# -*- coding=UTF-8 -*-
# @Project      QL_TimingScript
# @fileName     好游快爆.py
# @desc         好游快爆「翻滚吧爆米花」玉米庄园 H5 自动任务
#               2026-09 协议重写版：补齐 page_token / token_sign 签名链、服务器时间校准、
#               页面令牌过期重取、领奖接口 smdeviceid；全程串行 + 随机节流模拟真机操作
#
# 用法：
#     python 好游快爆.py            # 正常执行任务
#     python 好游快爆.py --probe    # 只登录并打印任务清单/资产，不执行任何任务（换凭据后先用它验证）
#
# 环境变量（键名大小写兼容）：
#     Hykb_cookie / HYKB_COOKIE   活动 cookie（scookie），多账号用 @ 分隔
#     HYKB_SMDEVICEID             数美设备号（领取类接口必带；多账号用 @ 分隔，与 cookie 顺序对应）
#     HYKB_DEVICE                 设备识别码，默认取 cookie 第 5 段
#     HYKB_UA                     抓包原样 UA（含 Androidkb/<机型>，服务端会校验机型）
#     HYKB_WEB_COOKIE             网页登录态（Pauth/Uauth/accesstoken/nickname），预约任务专用；
#                                 多账号用 @ 分隔、与 cookie 顺序对应。获取方式见 hykb_config.WEB_YUYUE
"""
旧脚本为什么会失效（本次重写的依据）：
    旧脚本只带 scookie + device 就发请求，而活动后来给所有 ajax 接口加了 token 校验链：
    page_token + token_time + random_str + token_sign(md5 前 10 位)，
    且必须先 GET index.php 取服务端随机下发的 pageToken / pageRandomStr / 服务器时间。
    缺这一层，服务端一律返回 loginStatus=103（no_login），与 cookie 本身是否有效无关。
"""

import argparse
import hashlib
import json
import os
import random
import re
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning

import log
from get_env import get_env
from hykb_config import (
    API_CONFIG,
    API_ENDPOINTS,
    AUTO_MODES,
    BLACKLIST_LEVELS,
    CLIENT_VERSION,
    DEFAULT_UA,
    ERROR_CODES,
    RESPONSE_MESSAGES,
    RISK_KWS,
    SKIP_KWS,
    TASK_MODES,
    TASK_SWITCHES,
    THROTTLE,
    VERSION_CODE,
    WEB_YUYUE,
)
from sendNotify import send_notification_message_collection

warnings.filterwarnings('ignore', category=InsecureRequestWarning)

# 页面令牌有效期（服务端 MAX_PAGE_STAY_MS = 23 小时），留 10 分钟余量
PAGE_TOKEN_TTL_MS = 23 * 3600 * 1000 - 10 * 60 * 1000

# 玉米成熟度已满 / 需要先收获 —— 领奖接口会返回这两个码，处理后可重试一次
MATURITY_CODES = ("2004", "2005")


class RiskStop(Exception):
    """命中风控信号 —— 立即停止该账号，绝不硬重试"""


def now_ms() -> int:
    return int(time.time() * 1000)


def rand_param() -> str:
    """模拟 WebView 里 Math.random() 的字符串形式：0.xxxxxxxxxxxxxxxxxx"""
    return f"0.{random.randint(100000000000000000, 899999999999999999)}"


def risk_hit(text: str) -> bool:
    return any(k in text for k in RISK_KWS)


def is_skip(text: str) -> bool:
    return any(k in text for k in SKIP_KWS)


# ───────────────────────── 每日答题题库 ─────────────────────────
# 题目与正确答案都不在客户端（H5 只回传用户点的选项文本），答错还会消耗当日次数，
# 所以脚本只在题库命中时才作答；未命中的题目写进这个文件等人工补答案。
DATI_BANK_FILE = Path(__file__).with_name("hykb_dati_bank.json")


def load_dati_bank() -> Dict[str, str]:
    """读取本地答题库（结构 {"answers": {"题目": "正确选项文本"}}）"""
    try:
        raw = json.loads(DATI_BANK_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except Exception as e:
        log.log(f"⚠️答题库 {DATI_BANK_FILE.name} 读取失败：{e}")
        return {}
    answers = raw.get("answers") if isinstance(raw, dict) else None
    if not isinstance(answers, dict):
        return {}
    return {str(k).strip(): str(v).strip() for k, v in answers.items() if str(v).strip()}


def remember_dati_question(title: str, options: List[str]) -> None:
    """把没见过的题目与选项落盘，供人工补答案（answers 里填正确选项文本即可自动作答）"""
    if not title:
        return
    try:
        raw = json.loads(DATI_BANK_FILE.read_text(encoding="utf-8"))
    except Exception:
        raw = {}
    if not isinstance(raw, dict):
        raw = {}
    raw.setdefault("answers", {})
    unknown = raw.setdefault("unknown", {})
    if title in raw["answers"] or title in unknown:
        return
    unknown[title] = options
    try:
        DATI_BANK_FILE.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        log.log(f"⚠️答题库写入失败：{e}")


def load_web_cookie() -> str:
    """网页登录态：优先环境变量（青龙），其次脚本同目录的本地文件（本地调试）"""
    for name in WEB_YUYUE["env_names"]:
        try:
            vals = [v for v in get_env(name, "@") if v]
        except Exception:
            vals = []
        if vals:
            return vals[0].strip().strip("'\"")
    path = Path(__file__).with_name(WEB_YUYUE["cookie_file"])
    if path.exists():
        return path.read_text(encoding="utf-8", errors="ignore").strip().strip("'\"")
    return ""


class WebYuyue:
    """网页版预约：走 www.3839.com 游戏详情页「立即预约 → 无手机号预约」的正规前端接口

    为什么不走 App：预约动作在 App 侧是 api.3839app.com/kuaibao/android/api.php?a=add&c=gameappointment，
    报文 params_encryption=1（libne.so 里的 native AES）+ svid/SECRET-DEVICE 设备头 + native 签名 t，
    活动凭据直连只会拿到 token error；H5 活动域也没有预约能力（153 个 ac 里只有查询/领奖）。
    而网页版有官方预约入口，纯 HTTP（cookie 登录态），不依赖任何设备 —— 这正是青龙要的形态。

    接口（POST，form-urlencoded）：
        POST {site}/app/hykb_web/ajax_yuyue.php
            action=checkStatus   → {"key":"ok","yuyued":false}     查询预约状态
            action=checkLogin    → {"key":"ok","msg":"登录校验通过"} 强登录校验
            action=orderNoPhone  → {"key":"ok","msg":"预约成功"}     无手机号预约（gid + game_type）
    登录态：Pauth / Uauth / accesstoken / nickname 四个 cookie，快爆 App 扫码登录一次有效期约 1 年
    （登录页 → 扫码 → App 确认 → QRcodeAuthCallBack 下发 cookie）。
    """

    def __init__(self, cookie: str = "", cfg: Optional[Dict[str, Any]] = None):
        self.cfg: Dict[str, Any] = dict(WEB_YUYUE)
        if cfg:
            self.cfg.update(cfg)
        self.cookie = (cookie or "").strip().strip("'\"").strip()
        self.reason = "" if self.cookie else "未配置网页登录态（HYKB_WEB_COOKIE）"
        self.client = requests.Session()
        self.client.verify = False
        self.client.headers.update({
            "User-Agent": self.cfg["ua"],
            "Referer": self.cfg["site"] + "/",
            "Origin": self.cfg["site"],
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        })
        if self.cookie:
            self.client.headers["Cookie"] = self.cookie

    @property
    def available(self) -> bool:
        return bool(self.cookie)

    def _post(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """带节流+重试的 POST（沿用 THROTTLE，保持人类节奏）"""
        url = self.cfg["site"] + self.cfg["endpoint"]
        for attempt in range(THROTTLE["max_retry"] + 1):
            time.sleep(random.uniform(THROTTLE["min_interval"], THROTTLE["max_interval"]))
            try:
                resp = self.client.post(url, data=data, timeout=API_CONFIG["timeout"])
                payload = resp.json()
            except Exception as e:
                if attempt >= THROTTLE["max_retry"]:
                    log.log(f"   ⚠️网页预约请求失败：{e}")
                    return None
                time.sleep(2 + attempt * 2)
                continue
            if isinstance(payload, dict):
                return payload
            return None
        return None

    def login_ok(self) -> bool:
        """强登录校验：预约弹窗的前置条件，失败即登录态过期"""
        data = self._post({"action": "checkLogin", "gid": "", "game_type": self.cfg["game_type"]})
        if data and data.get("key") == "ok":
            return True
        self.reason = (data or {}).get("msg") or "网页登录态失效"
        return False

    def is_reserved(self, gameid: str) -> Optional[bool]:
        """查询该游戏是否已预约；None 表示查询失败"""
        data = self._post({"action": "checkStatus", "gid": str(gameid), "game_type": self.cfg["game_type"]})
        if not data or data.get("key") != "ok":
            return None
        return bool(data.get("yuyued"))

    def reserve(self, gameid: str) -> bool:
        """无手机号预约（幂等：已预约再调也只返回成功）；真伪仍由玉米庄园 dailyInit 复核"""
        data = self._post({
            "action": "orderNoPhone",
            "gid": str(gameid),
            "game_type": self.cfg["game_type"],
            "relation_steam_id": self.cfg["relation_steam_id"],
        })
        if not data:
            return False
        if data.get("key") == "ok":
            log.log(f"   ✅网页预约成功：gameid={gameid}（{data.get('msg') or '预约成功'}）")
            return True
        log.log(f"   ❌网页预约失败：gameid={gameid} → {data.get('msg') or data}")
        return False


class HaoYouKuaiBao:
    """好游快爆玉米庄园任务执行器（单账号）"""

    def __init__(self, scookie: str, smdeviceid: str = "", device: str = "",
                 ua: str = "", probe: bool = False, web_cookie: str = ""):
        self.scookie = (scookie or "").strip().strip("'\"").strip()
        self.smdeviceid = (smdeviceid or "").strip().strip("'\"").strip()
        # cookie 约定：第 5 段即设备识别码（App 的 getUniqueDeviceIdNew 结果）
        parts = self.scookie.split("|")
        self.device = (device or "").strip() or (parts[4] if len(parts) > 4 else "")
        self.probe = probe

        headers = dict(API_CONFIG["headers"])
        headers["User-Agent"] = (ua or "").strip() or DEFAULT_UA
        self.client = requests.Session()
        self.client.headers.update(headers)
        self.client.verify = False

        # 页面令牌与时钟校准
        self.page_token: str = ""
        self.random_str: str = ""
        self.enter_time: int = 0
        self.time_diff: int = 0
        self.server_time_info: Dict[str, int] = {}
        self.page_html: str = ""

        # 服务端下发的会话令牌
        self.token_name: str = "token"
        self.token_value: str = "default"
        self.user_name: str = ""
        self.user_level: int = 0

        self.stats: Dict[str, Any] = {"ok": 0, "skip": 0, "fail": 0, "baomihua": 0}

        # 每日任务上下文：dailyInit 下发的「已预约游戏」清单 / 本地答题库
        self.reserved_gameids: set = set()
        self.dati_bank: Dict[str, str] = load_dati_bank()

        # 网页版预约客户端（预约任务用；登录态缺失时自动跳过，不影响其它任务）
        self.yuyue = WebYuyue(web_cookie or load_web_cookie())

    # ───────────────────────── 基础层 ─────────────────────────

    def _pace(self) -> None:
        """请求节奏：真机不会 0.1 秒一个请求"""
        time.sleep(random.uniform(THROTTLE["min_interval"], THROTTLE["max_interval"]))

    def _server_now(self) -> int:
        return now_ms() + self.time_diff

    def _bootstrap(self) -> bool:
        """打开活动页：取 pageToken / pageRandomStr / 服务器时间（每次运行必须做）"""
        try:
            resp = self.client.get(API_ENDPOINTS["page"], timeout=API_CONFIG["timeout"])
        except Exception as e:
            log.log(f"❌打开活动页失败：{e}")
            return False
        if resp.status_code != 200:
            log.log(f"❌活动页返回 HTTP {resp.status_code}")
            return False

        html = resp.text
        self.page_html = html
        m_token = re.search(r"var\s+pageToken\s*=\s*['\"]([^'\"]+)['\"]", html)
        m_rand = re.search(r"var\s+pageRandomStr\s*=\s*['\"]([^'\"]+)['\"]", html)
        m_time = re.search(r"setACTServerTime\(\s*(\d{10,16})\s*\)", html)
        if not (m_token and m_rand and m_time):
            log.log("❌活动页未取到 pageToken/pageRandomStr/服务器时间（页面结构可能又变了）")
            return False

        self.page_token = m_token.group(1)
        self.random_str = m_rand.group(1)
        local = now_ms()
        self.enter_time = int(m_time.group(1))
        self.time_diff = self.enter_time - local
        self.server_time_info = {"enter_set_time": local, "time_diff": self.time_diff}
        log.log(f"🕒时间校准完成（服务器与本地相差 {self.time_diff} ms）")
        return True

    def _token_expired(self) -> bool:
        return self.enter_time > 0 and (self._server_now() - self.enter_time) >= PAGE_TOKEN_TTL_MS

    def _sign(self, param: Dict[str, Any]) -> Dict[str, Any]:
        """AddTokenInfo：每个请求必须注入的令牌与签名（对应页面里的 AddTokenInfo 函数）"""
        param[self.token_name] = self.token_value
        param["token_version"] = "v2"
        param["page_token"] = self.page_token
        param["enter_time"] = self.enter_time
        param["token_time"] = self._server_now()
        param["token_time2"] = now_ms()
        param["serverTimeInfo[enter_set_time]"] = self.server_time_info.get("enter_set_time", now_ms())
        param["serverTimeInfo[time_diff]"] = self.server_time_info.get("time_diff", 0)
        param["random_str"] = self.random_str
        sign_src = f"{self.page_token}|{self.random_str}|{param['token_time']}|visitV2"
        param["token_sign"] = hashlib.md5(sign_src.encode("utf-8")).hexdigest()[:10]
        param["scookie"] = self.scookie
        param["device"] = self.device
        return param

    def _check_risk(self, msg: Dict[str, Any], label: str) -> None:
        text = str(msg)
        if risk_hit(text):
            raise RiskStop(f"{label} 命中风控信号：{text[:160]}")
        level = msg.get("userlevel") or (msg.get("config") or {}).get("userlevel")
        if level is not None:
            try:
                if int(level) in BLACKLIST_LEVELS:
                    raise RiskStop(f"账号被标记为黑名单等级 {level}（{label}），停止全部动作")
            except (TypeError, ValueError):
                pass

    def post(self, endpoint: str, param: Dict[str, Any], label: str = "") -> Optional[Dict[str, Any]]:
        """统一发请求：节流 + 令牌注入 + 重试 + 风控识别"""
        if self._token_expired():
            log.log("♻️页面令牌已过期（超过 23 小时），重新打开活动页换取新令牌")
            if not self._bootstrap():
                return None

        url = API_ENDPOINTS[endpoint]
        body = self._sign(dict(param))
        for attempt in range(THROTTLE["max_retry"] + 1):
            self._pace()
            try:
                resp = self.client.post(url, data=body, timeout=API_CONFIG["timeout"])
                msg = resp.json()
            except Exception as e:
                if attempt >= THROTTLE["max_retry"]:
                    log.log(f"❌{label}请求异常：{e}")
                    self.stats["fail"] += 1
                    return None
                time.sleep(THROTTLE["retry_backoff"] * (attempt + 1) + random.uniform(0, 1.5))
                body = self._sign(dict(param))   # 重试必须重新签名（token_time 要新鲜）
                continue

            if not isinstance(msg, dict):
                log.log(f"❌{label}返回非 JSON：{str(msg)[:160]}")
                self.stats["fail"] += 1
                return None

            self._check_risk(msg, label)
            if str(msg.get("loginStatus")) == ERROR_CODES["NO_LOGIN"]:
                raise RiskStop("凭据失效（loginStatus=103 / no_login），请重新抓包更新 HYKB_COOKIE")
            return msg
        return None

    # ───────────────────────── 业务层 ─────────────────────────

    def login(self) -> Optional[Dict[str, Any]]:
        msg = self.post("main", {"ac": "login", "r": rand_param()}, "登录")
        if not msg:
            return None
        cfg = msg.get("config") or {}
        if str(msg.get("loginStatus")) != "100" or not cfg:
            log.log(f"❌登录失败：{str(msg)[:200]}")
            return None
        self.token_name = cfg.get("token_name") or self.token_name
        self.token_value = cfg.get("token_value") or self.token_value
        self.user_name = cfg.get("name") or "未知用户"
        try:
            self.user_level = int(cfg.get("userlevel") or msg.get("userlevel") or 0)
        except (TypeError, ValueError):
            self.user_level = 0
        log.log(RESPONSE_MESSAGES["login_success"].format(self.user_name))
        return cfg

    def sign(self) -> None:
        """签到（浇水）—— 每日爆米花主要来源"""
        msg = self.post("sign", {
            "ac": "Sign",
            "smdeviceid": self.smdeviceid,
            "verison": CLIENT_VERSION,
            "OpenAutoSign": "close",
            "r": rand_param(),
        }, "浇水签到")
        if not msg:
            return
        if str(msg.get("key")) == ERROR_CODES["SUCCESS"]:
            add = msg.get("add_baomihua") or msg.get("baomihua") or "?"
            log.log(RESPONSE_MESSAGES["sign_success"].format(add))
            self._count_baomihua(msg)
            self.stats["ok"] += 1
        elif is_skip(str(msg)):
            log.log(RESPONSE_MESSAGES["sign_already"])
            self.stats["skip"] += 1
        else:
            log.log(f"⚠️浇水签到未成功：{str(msg)[:180]}")
            self.stats["fail"] += 1

    def manor(self, cfg: Dict[str, Any]) -> None:
        """庄园：成熟则收获，空地则播种"""
        maturity = str(cfg.get("csd_jdt", ""))
        grew = str(cfg.get("grew", ""))
        if maturity == "100%" or grew == "100":
            msg = self.post("plant", {"ac": "HarvestAndPlant", "r": rand_param()}, "收获并播种")
            if msg and str(msg.get("key")) == ERROR_CODES["SUCCESS"]:
                log.log(f"🌽收获并播种成功（{self._reward_text(msg)}）")
                self._count_baomihua(msg)
                self.stats["ok"] += 1
            elif msg:
                log.log(f"⚠️收获未成功：{str(msg)[:160]}")
            return

        if grew in ("-1", "0", ""):
            bag = self.post("bag", {"ac": "BagInit", "r": rand_param()}, "背包")
            corn_id = self._pick_seed(bag)
            if corn_id is None:
                log.log("⏭️没有可用种子，跳过播种（种子来自每日任务奖励）")
                self.stats["skip"] += 1
                return
            msg = self.post("plant", {"ac": "Plant", "corn_id": corn_id, "r": rand_param()}, "播种")
            if msg and str(msg.get("key")) == ERROR_CODES["SUCCESS"]:
                log.log(RESPONSE_MESSAGES["plant_success"])
                self.stats["ok"] += 1
            elif msg:
                log.log(f"⚠️播种未成功：{str(msg)[:160]}")
        else:
            log.log("⏭️庄园作物未成熟，今日无需收获")

    @staticmethod
    def _pick_seed(bag: Optional[Dict[str, Any]]) -> Optional[int]:
        """从背包里挑一个还有剩余的种子 id"""
        if not isinstance(bag, dict):
            return None
        for item in (bag.get("cornDetails") or bag.get("corn") or []):
            if not isinstance(item, dict):
                continue
            try:
                if int(item.get("num") or item.get("count") or 0) > 0:
                    return int(item.get("id") or item.get("corn_id"))
            except (TypeError, ValueError):
                continue
        return None

    @staticmethod
    def _reward_text(msg: Dict[str, Any]) -> str:
        """领奖响应里的奖励文案：签到用 add_baomihua，每日任务用 reward_bmh_num"""
        parts: List[str] = []
        gain = 0
        for key in ("reward_bmh_num", "add_baomihua"):
            try:
                gain = int(msg.get(key) or 0)
            except (TypeError, ValueError):
                gain = 0
            if gain:
                break
        if gain:
            parts.append(f"爆米花 +{gain}")
        for key, name in (("reward_csd_num", "成熟度"), ("add_csd", "成熟度"),
                          ("reward_score_num", "经验"), ("add_score", "经验")):
            try:
                value = int(msg.get(key) or 0)
            except (TypeError, ValueError):
                value = 0
            if value:
                parts.append(f"{name} +{value}")
        for key in ("baomihua", "dialog_baomihua"):
            if msg.get(key) is not None:
                parts.append(f"余额 {msg[key]}")
                break
        return "，".join(parts) or "已到账"

    def _count_baomihua(self, msg: Dict[str, Any]) -> None:
        for key in ("reward_bmh_num", "add_baomihua"):
            try:
                gain = int(msg.get(key) or 0)
            except (TypeError, ValueError):
                continue
            if gain:
                self.stats["baomihua"] += gain
                return

    def season(self) -> None:
        """赛季：先取等级奖励状态，再逐个领取（线上服务端已不支持批量领取：
        调用 batchReceiveLevelPrize 返回 1001「不支持批量操作」）"""
        init = self.post("season", {"ac": "seasonManualInit", "r": rand_param()}, "赛季初始化")
        if not init:
            return
        prize_map = init.get("user_prize_data") or {}
        # prize_id 以页面内嵌的 onclick="Season.receiveLevelPrize(prize_id, level)" 为准
        page_prize_ids = {int(level): int(prize) for prize, level in
                          re.findall(r"receiveLevelPrize\(\s*(\d+)\s*,\s*(\d+)\s*\)", self.page_html)}
        claimable = sorted(int(lv) for lv, st in prize_map.items()
                           if str(st).lower() in ("completed", "1"))
        if not claimable:
            log.log(f"⏭️赛季暂无可领奖励（经验 {init.get('user_score', '?')}，"
                    f"下一档 Lv{init.get('user_next_span_level', '?')}，状态={prize_map or '空'}）")
            self.stats["skip"] += 1
            return
        for level in claimable:
            got = self.post("season", {"ac": "receiveLevelPrize",
                                       "prize_id": page_prize_ids.get(level, level),
                                       "level": level, "r": rand_param()}, f"赛季Lv{level}奖励")
            if got and str(got.get("key")) == ERROR_CODES["SUCCESS"]:
                log.log(f"🎉赛季Lv{level}奖励已领取（{self._reward_text(got)}）")
                self._count_baomihua(got)
                self.stats["ok"] += 1
            elif got and is_skip(str(got)):
                log.log(f"⏭️赛季Lv{level}已领取过")
                self.stats["skip"] += 1
            else:
                log.log(f"⚠️赛季Lv{level}未领取：{str(got)[:140]}")
                self.stats["fail"] += 1

    # ───────────────────────── 每日任务 ─────────────────────────

    @staticmethod
    def parse_page_tasks(html: str) -> List[Dict[str, Any]]:
        """解析 index.php 里服务端直出的任务清单（data-id / data-mode / data-status）"""
        tasks: List[Dict[str, Any]] = []
        soup = BeautifulSoup(html, "html.parser")
        for li in soup.select("li.daily_li"):
            tid = li.get("data-id")
            if not tid:
                continue
            try:
                mode = int(li.get("data-mode") or 0)
                status = int(li.get("data-status") or -1)
            except ValueError:
                mode, status = 0, -1
            title_el = li.select_one("dt")
            tasks.append({
                "id": int(tid),
                "mode": mode,
                "status": status,
                "gameid": li.get("data-gameid") or "0",
                "title": (title_el.get_text(" ", strip=True) if title_el else "")[:60],
            })
        return tasks

    def _claim(self, action: str, task_id: int, label: str) -> bool:
        """统一走领奖接口（*Ling）；成熟度满时先收获再领，最多补一次"""
        param: Dict[str, Any] = {
            "ac": action,
            "id": task_id,
            "smdeviceid": self.smdeviceid,
            "verison": CLIENT_VERSION,
            "r": rand_param(),
        }
        msg = self.post("daily", param, label)
        if not msg:
            return False
        key = str(msg.get("key"))
        if key in MATURITY_CODES:
            log.log(f"🌽{label}：玉米成熟度已满，先收获再领奖")
            self.manor({"csd_jdt": "100%", "grew": "100"})
            msg = self.post("daily", dict(param, r=rand_param()), label + "-重试")
            if not msg:
                return False
            key = str(msg.get("key"))
        if key == ERROR_CODES["SUCCESS"]:
            log.log(f"✅{label}领取成功（{self._reward_text(msg)}）")
            self._count_baomihua(msg)
            self.stats["ok"] += 1
            return True
        if is_skip(str(msg)):
            log.log(f"⏭️{label}今日已领取")
            self.stats["skip"] += 1
            return True
        log.log(f"⚠️{label}未领取：{str(msg)[:150]}")
        self.stats["fail"] += 1
        return False

    def task_share(self, task: Dict[str, Any]) -> None:
        """分享类任务：发起分享 → 分享回调 → 领奖（mode/source 取真机抓包值）"""
        label = f"分享任务[{task['id']}]"
        tid = task["id"]
        self.post("daily", {"ac": "DailyShare", "id": tid, "onlyc": "0", "r": rand_param()}, label + "-发起")
        self.post("daily", {"ac": "DailyShareCallback", "id": tid, "mode": "qq", "source": "ds",
                            "r": rand_param()}, label + "-回调")
        self._claim("DailyShareLing", tid, label)

    def task_dati(self, task: Dict[str, Any]) -> None:
        """每日答题：题目与正确答案都不在客户端（H5 只把用户点的选项文本回传），
        且答错会消耗当日答题次数 → 只在本地题库命中时才作答，
        未命中的题目记录下来交人工在 App 内作答（绝不猜答案）。"""
        label = f"每日答题[{task['id']}]"
        tid = task["id"]
        q = self.post("daily", {"ac": "DailyDati", "id": tid, "r": rand_param()}, label + "-取题")
        if not q:
            return
        options = [str(q.get(f"option{i}")) for i in range(1, 5) if q.get(f"option{i}")]
        if str(q.get("key")) != "2004" or not options:
            if is_skip(str(q)) or str(q.get("key")) == "2001":
                log.log(f"⏭️{label}今日已答/已无答题次数：{str(q)[:110]}")
                self.stats["skip"] += 1
            else:
                log.log(f"⚠️{label}取题失败：{str(q)[:130]}")
                self.stats["fail"] += 1
            return

        title = str(q.get("title") or "").strip()
        answer = self.dati_bank.get(title)
        if answer and answer in options:
            ans = self.post("daily", {"ac": "DailyDatiAnswer", "id": tid, "option": answer,
                                      "r": rand_param()}, label + "-作答")
            if ans and str(ans.get("key")) == ERROR_CODES["SUCCESS"]:
                log.log(f"✅{label}作答正确（题库命中）")
                self._claim("DailyDatiLing", tid, label)
                return
            log.log(f"⚠️{label}作答未通过：{str(ans)[:120]}")
            self.stats["fail"] += 1
            return

        remember_dati_question(title, options)
        log.log(f"❓{label}未知题目（题库未命中），不猜答案、不消耗次数：{title}"
                f"｜选项：{' / '.join(options)}")
        log.log(f"📝已写入 {DATI_BANK_FILE.name} 的 answers，填好正确选项后下次自动作答")
        self.stats["skip"] += 1

    def task_interactive(self, task: Dict[str, Any]) -> None:
        """好友互动：先帮 3 位好友处理事件（事件=好友家待帮收的玉米），再领奖。
        事件由真实好友产生，没有事件时服务端必拒 —— 直接跳过，不做无效请求。"""
        label = f"好友互动[{task['id']}]"
        init = self.post("interactive", {"ac": "iafInit", "r": rand_param()}, label + "-好友事件")
        uids: List[str] = []
        if init:
            ev = init.get("eventUids") or {}
            if isinstance(ev, dict):
                uids = [str(u) for u in (ev.get("uids") or []) if str(u).isdigit()]
        if len(uids) < 3:
            log.log(f"⏭️{label}好友事件不足（{len(uids)}/3），今日跳过"
                    f"（该任务需真实好友家出现待帮收玉米）")
            self.stats["skip"] += 1
            return
        for fuid in uids[:3]:
            self.post("friendhome", {"ac": "HelpReap", "fuid": fuid, "r": rand_param()},
                      label + f"-帮好友{fuid}")
            time.sleep(random.uniform(*THROTTLE["task_gap"]))
        self._claim("DailyInteractiveLing", task["id"], label)

    def yuyue_auto_reserve(self, tasks: List[Dict[str, Any]]) -> None:
        """预约任务全自动：走网页版正规接口（无手机号预约），再用 dailyInit 复核（服务端状态为权威）

        链路：dailyInit 给出「已预约游戏」清单 → 找出每日任务里未预约的预约类任务（mode=9）
        → POST ajax_yuyue.php?action=orderNoPhone → 重新拉 dailyInit 确认生效 → 之后按 task_yuyue 领奖。
        全程纯 HTTP，不依赖任何设备；登录态过期时只提示、不重试轰炸（避免风控）。
        """
        if not TASK_SWITCHES.get("daily_yuyue_auto", True):
            return
        pending = [t for t in tasks
                   if t["mode"] == 9
                   and str(t.get("gameid") or "0") not in ("", "0")
                   and str(t["gameid"]) not in self.reserved_gameids]
        if not pending:
            return

        pend_txt = "、".join(f"{t.get('title') or t['gameid']}({t['gameid']})" for t in pending)
        yuyue: Optional[WebYuyue] = getattr(self, "yuyue", None)
        if yuyue is None or not yuyue.available:
            log.log(f"⚠️预约任务跳过：{getattr(yuyue, 'reason', '未初始化')}"
                    f"；待预约 {len(pending)} 个：{pend_txt}"
                    "（需在环境变量 HYKB_WEB_COOKIE 配置网页登录态，获取方式见 hykb_config.WEB_YUYUE）")
            return
        if not yuyue.login_ok():
            log.log(f"⚠️预约任务跳过：网页登录态已失效（{yuyue.reason}）"
                    f"；待预约 {len(pending)} 个：{pend_txt}"
                    " —— 本机运行 python hykb_web_login.py 用快爆 App 扫码重新登录，"
                    "把输出的 cookie 串填回 HYKB_WEB_COOKIE")
            return

        pending = pending[: int(yuyue.cfg["max_per_run"])]
        log.log(f"🌐预约全自动（网页版接口）：{len(pending)} 个游戏待预约")
        for task in pending:
            gid = str(task["gameid"])
            log.log(f"   ➡️预约《{task['title'] or gid}》gameid={gid}")
            state = yuyue.is_reserved(gid)
            if state is True:
                log.log("   ℹ️网页侧显示已预约，跳过下单")
            else:
                yuyue.reserve(gid)

        # 复核：服务端 user_yuyue_gameids 才是权威判据
        init = self.post("daily", {"ac": "dailyInit", "VersionCode": VERSION_CODE, "r": rand_param()},
                         "预约结果复核")
        if not init:
            return
        new_set = {str(g) for g in (init.get("user_yuyue_gameids") or []) if str(g)}
        added = sorted(new_set - self.reserved_gameids)
        if added:
            log.log(f"✅预约生效 {len(added)} 个：{', '.join(added)}")
        self.reserved_gameids = new_set
        still = [str(t["gameid"]) for t in pending if str(t["gameid"]) not in new_set]
        if still:
            log.log(f"⚠️仍未预约成功：{', '.join(still)}"
                    "（可能该游戏已停止预约 / 网页登录态权限不足，稍后重试即可）")

    def task_yuyue(self, task: Dict[str, Any]) -> None:
        """预约类任务：预约动作已由上一步的网页版接口完成（WebYuyue），
        这里只对「服务端确认已预约」的游戏领奖，避免无效失败请求。"""
        label = f"预约任务[{task['id']}]"
        gameid = str(task.get("gameid") or "")
        if gameid and gameid in self.reserved_gameids:
            self._claim("DailyYuyueLing", task["id"], label)
        else:
            log.log(f"⏭️{label}未预约（gameid={gameid or '?'}）：请在 App 内预约该游戏后才能领奖")
            self.stats["skip"] += 1

    def daily(self) -> None:
        """每日任务主流程"""
        init = self.post("daily", {"ac": "dailyInit", "VersionCode": VERSION_CODE, "r": rand_param()},
                         "每日任务初始化")
        done_by_server: set = set()
        if init:
            # 已预约游戏清单：预约动作只能由 App 端发起，这里决定哪些预约任务可直接领奖
            self.reserved_gameids = {str(g) for g in (init.get("user_yuyue_gameids") or []) if str(g)}
            # 任务的真实状态来自 dailyInit（success=2 已领取）；页面 data-status 恒为 -1，不可用
            done_by_server = {str(t.get("rwid")) for t in (init.get("user_daily_Task") or [])
                              if str(t.get("success")) == "2"}
        tasks = self.parse_page_tasks(self.page_html)
        if not tasks:
            log.log("⚠️页面未解析到每日任务条目，跳过每日任务")
            return

        # 预约任务全自动：走网页版正规接口（无手机号预约）→ 纯 HTTP，无设备依赖
        self.yuyue_auto_reserve(tasks)

        todo: List[Dict[str, Any]] = []
        for task in tasks:
            if task["mode"] not in AUTO_MODES or not self._mode_enabled(task["mode"]):
                continue
            if task["status"] == 100 or str(task["id"]) in done_by_server:   # 已领取（以服务端状态为准）
                continue
            todo.append(task)

        limit = TASK_SWITCHES.get("daily_max") or 0
        if limit and len(todo) > limit:
            todo = todo[:limit]

        if not todo:
            log.log("⏭️没有可自动完成的每日任务（其余任务需在真机上手动完成）")
            return

        log.log(f"📋本次处理 {len(todo)} 个任务："
                + "、".join(f"{TASK_MODES.get(t['mode'], t['mode'])}#{t['id']}" for t in todo))

        for index, task in enumerate(todo, 1):
            mode = task["mode"]
            try:
                if mode == 1:
                    self.task_share(task)
                elif mode == 2:
                    self.task_dati(task)
                elif mode == 7:
                    self.task_interactive(task)
                elif mode == 9:
                    self.task_yuyue(task)
            except RiskStop:
                raise
            except Exception as e:
                log.log(f"❌任务[{task['id']}]执行异常：{e}")
                self.stats["fail"] += 1
            if index < len(todo):
                time.sleep(random.uniform(*THROTTLE["task_gap"]))

    @staticmethod
    def _mode_enabled(mode: int) -> bool:
        return {
            1: TASK_SWITCHES.get("daily_share", True),
            2: TASK_SWITCHES.get("daily_dati", True),
            7: TASK_SWITCHES.get("daily_interactive", True),
            9: TASK_SWITCHES.get("daily_yuyue", True),
        }.get(mode, False)

    def ycx(self) -> None:
        """一次性任务：老账号基本已领完，这里只做初始化让服务端刷新任务状态"""
        msg = self.post("ycx", {"ac": "ycxInit", "VersionCode": VERSION_CODE, "r": rand_param()},
                        "一次性任务初始化")
        if msg and str(msg.get("key")) == ERROR_CODES["SUCCESS"]:
            log.log("ℹ️一次性任务状态已刷新")
        elif msg:
            log.log(f"ℹ️一次性任务无可领项：{str(msg)[:120]}")

    # ───────────────────────── 编排 ─────────────────────────

    def run(self) -> None:
        log.log("=" * 12 + " 好游快爆 · 翻滚吧爆米花 " + "=" * 12)
        if not self.scookie:
            log.log("❌未配置 cookie，跳过")
            return
        if not self.smdeviceid:
            log.log("⚠️未配置 HYKB_SMDEVICEID：签到/领奖类接口可能被服务端拒绝")
        if not self._bootstrap():
            return

        try:
            cfg = self.login()
            if not cfg:
                return

            if self.probe:
                self._probe_report(cfg)
                return

            if TASK_SWITCHES.get("sign", True):
                self.sign()
                time.sleep(random.uniform(*THROTTLE["group_gap"]))

            if TASK_SWITCHES.get("manor", True):
                self.manor(cfg)
                time.sleep(random.uniform(*THROTTLE["group_gap"]))

            if TASK_SWITCHES.get("season", True):
                self.season()
                time.sleep(random.uniform(*THROTTLE["group_gap"]))

            self.daily()

            if TASK_SWITCHES.get("ycx", True):
                time.sleep(random.uniform(*THROTTLE["group_gap"]))
                self.ycx()

            s = self.stats
            log.log(f"📊【{self.user_name}】完成：成功 {s['ok']} / 已领过 {s['skip']} / 失败 {s['fail']}"
                    + (f" / 爆米花 +{s['baomihua']}" if s["baomihua"] else ""))

        except RiskStop as e:
            log.log(f"🛑【{self.user_name or '当前账号'}】{e}")
            log.log("🛑已按防风控策略停止本账号后续动作（不要连续重试，隔天再跑更安全）")
        finally:
            self.client.close()

    def _probe_report(self, cfg: Dict[str, Any]) -> None:
        """--probe：只读体检，不发任何任务请求"""
        tasks = self.parse_page_tasks(self.page_html)
        log.log(f"🔎体检模式：{self.user_name}（uid={cfg.get('uid', '?')}）")
        for key in ("baomihua", "seed", "muck", "corn", "csd_jdt", "grew", "deviceid",
                    "next_seed_id", "blacklist", "DeviceBindUserStatus"):
            if key in cfg:
                log.log(f"    {key} = {cfg[key]}")
        log.log(f"    cookie 设备号 = {self.device[:6]}…（cookie 第 5 段）")
        log.log(f"    数美设备号 = {'已配置' if self.smdeviceid else '未配置'}")
        log.log(f"    页面任务 {len(tasks)} 条：")
        for task in tasks:
            flag = "可自动" if task["mode"] in AUTO_MODES else "需真机"
            log.log(f"      [{flag}] id={task['id']} mode={task['mode']}"
                    f"({TASK_MODES.get(task['mode'], '?')}) status={task['status']} {task['title']}")


def load_accounts() -> List[Dict[str, str]]:
    """读取环境变量；cookie 与数美设备号按顺序一一对应"""
    cookies = [c for c in (get_env("HYKB_COOKIE", "@") or get_env("Hykb_cookie", "@")) if c]
    if not cookies:
        log.log("❌未找到 Hykb_cookie / HYKB_COOKIE 变量")
        return []
    smids = [s for s in get_env("HYKB_SMDEVICEID", "@") if s]
    web_cookies = [w for w in get_env("HYKB_WEB_COOKIE", "@") if w]
    devices = [d for d in get_env("HYKB_DEVICE", "@") if d]
    uas = [u for u in get_env("HYKB_UA", "@") if u]

    def pick(seq: List[str], index: int) -> str:
        if not seq:
            return ""
        return seq[index] if index < len(seq) else seq[0]

    return [{
        "cookie": cookie,
        "smdeviceid": pick(smids, i),
        "device": pick(devices, i),
        "ua": pick(uas, i),
        "web_cookie": pick(web_cookies, i),
    } for i, cookie in enumerate(cookies)]


def main() -> None:
    parser = argparse.ArgumentParser(description="好游快爆 翻滚吧爆米花 自动任务")
    parser.add_argument("--probe", action="store_true", help="只登录并打印任务清单，不执行任务")
    args = parser.parse_args()

    accounts = load_accounts()
    if not accounts:
        return
    log.log(f"🔐共读取到 {len(accounts)} 个账号")
    for index, account in enumerate(accounts):
        if index:
            time.sleep(random.uniform(20, 45))   # 账号之间也留出人类节奏
        bot = HaoYouKuaiBao(
            scookie=account["cookie"],
            smdeviceid=account["smdeviceid"],
            device=account["device"],
            ua=account["ua"],
            probe=args.probe,
            web_cookie=account["web_cookie"],
        )
        bot.run()


if __name__ == '__main__':
    main()
    send_notification_message_collection("好游快爆活动奖励领取通知 - {}".format(datetime.now().strftime("%Y/%m/%d")))
