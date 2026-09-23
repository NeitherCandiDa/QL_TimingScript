# -*- coding=UTF-8 -*-
# const $ = new Env('得物森林')
# cron "1 8,10,12,15,18,22 * * *"
"""
================================================================================
 得物「星愿森林」自动脚本  —— 配置说明（先读完再运行）
================================================================================

【需要配置的 7 项凭据】（全部来自你自己手机抓包，切勿共用/分享）
  x_auth_token : 约 600 字符，Bearer 开头
  duToken      : 约 244 字符
  cookieToken  : 约 244 字符（一般与 duToken 相同）
  cookie       : 约 995 字符（整条 Cookie 原样复制）
  dudeliveryid : 约 160 字符
  duproductid  : 约 64 字符
  sk           : 约 92 字符  ★必需：设备签名

【怎么获取】
  手机装抓包工具（Reqable / 小黄鸟等）→ 打开得物 App → 进入"星愿森林"→ 随便点几下
  → 找到任意一条 dcdn-app-huoshan.dewu.com/hacking-tree/... 的请求
  → 把请求头里上面 7 项原样复制出来

【怎么填】两种方式任选其一
  方式1（青龙面板 / 系统环境变量，推荐）：
      变量名              含义
      dw_x_auth_token     Bearer xxxx...     （多账号用 & 分割）
      dw_duToken          xxxx...
      dw_cookieToken      xxxx...
      dw_cookie           duToken=xxx; x-auth-token=xxx...
      dw_dudeliveryid     xxxx...
      dw_duproductid      xxxx...
      dw_sk               xxxx...            （★必需！设备签名，见下方说明）
  方式2（本地测试）：把值填进同目录的 dw_creds.json（已生成模板），脚本自动读取

  - 遇到 485「请校验验证码」= 服务端风控（非限流）：
      个别任务会被要求人机验证，属正常风控，脚本自动跳过该任务继续跑
  - 部分任务连续快速请求也会触发 485，脚本内已加大请求间隔

【已知问题】
  1、浇水充满气泡 存在bug —— 2026-09-22 已修（死循环，见下方重构记录）
  2、领取品牌特惠活动奖励存在bug
  3、获取助力码存在bug

【2026-09-22 新增功能】
  - 收藏商品任务（taskType=50，「收藏想要的【品牌】商品」，每个 40g）
    三步流程（从 H5 JS 逆向得出）：
      ① POST /api/v1/h5/favorite/fire/app/favorite/add/spu/v2   {spuId}
      ② POST /hacking-task/v1/task/commit   {taskId,taskType,spuId,btd,kocSource}
      ③ POST /hacking-tree/v1/task/receive  {classify,taskId}
    实现：favorite_spu() + do_favorite_task()，execute_task 按 taskType==50 分发
    注意：会真的把商品收藏到你的得物账号（任务要求如此），可事后在 App 取消收藏

【2026-09-22 第三轮：新增免费领水滴 + 接口可行性结论】
  + 新增 receive_free_droplet()：水滴福利每日免费领 droplet_benefit/receive_droplet
    实测 +50g/天（即App「水滴兑换」页的免费领水滴），已挂 run()。
  接口可行性结论（实测，非推测）：
  - 逛逛品牌页(taskType=500,GPS_AD广告任务)：脚本 pre_commit→commit(str)→receive 链已通，
    但 commit 不推进 curStep（广告任务需真实SDK曝光），能否领取取决于服务端是否判定完成。
  - 首次添加星愿森林小组件(reward=6000)：需真机在手机桌面添加widget，无法脚本自动化。
  - 下滑赚水滴 product/task/seek-receive：sign 是【独立签名】(错误码709000007)，
    非主 _dw_sign 算法，旧硬编码值已失效，需真实浏览行为动态生成→静态不可复现，无法自动化。
  - 打卡得好礼 task/sign/choose_time：需【先完成7天连续签到】才解锁(711020005)，
    且选时段有副作用(影响真实签到节奏)，不自动化；老签到 sign/list 由 sign_in() 每日推进。

【2026-09-22 关键修复 + 新功能（第二轮）】
  ★ 修复所有浏览/逛逛/去摇一摇类任务：task/commit 的 taskType 必须传【字符串】
    传 int 会返回 code=900「请求参数不合法」，传 str 才 200 成功。
    已在 submit_task_completion_status 内部统一强制 str(taskType)，一次修好全部分支。
    （实测：浏览15s +50g、去摇一摇 +50g、从桌面组件 +500g、逛逛品牌页 +40g 全部领到）
  ★ submit 失败不再静默返回 False，会打印服务端真实响应（便于定位）
  + 新增周末活动 execute_weekend_task()：每日 login 计入 50g（周末结算发放）
    机制：taskStatus 10=待领 20=已计入 0=进行中；pk/order/waterEx 需真实交易无法自动化
  + 新增收藏商品任务 do_favorite_task()：favorite/add/spu → task/commit → task/receive（每个40g）

【2026-09-22 重构与健壮性加固】
  - 域名常量 _DW_API_HOST：41 处 URL 收敛，换域名只改 1 行
  - 统一日志 self.log()：97 处调用，自动加「用户【昵称】，=== ===」前后缀
  - 节流配置区 _SLEEP_* / _MAX_*_LOOP：全局控速只改这一处
  - 安全取值 dig()：45 处链式 .get().get() 改为 dig()，服务端返回 null 不再崩溃
  - 修死循环：receive_discover_droplet 原 while True 完全无出口（会无限狂发请求）
  - 修死循环：waterting_droplet_extra 非 200 时不退出（原「浇水充满气泡 bug」根因）

【2026-09-22 修复记录】
  - 修复 400：去掉 sks/shumreiId/duid/deviceTrait 等头（保留 SK）
  - 修复 485：加回 SK 设备签名（POST 接口必需，否则要求验证码）
  - 修复刷屏：气泡水滴「明日可领」不再无限循环
  - 修复死循环：接口非 200 时正确 return（原会空转 50 轮）
  - 修复限流：并发改串行、请求间隔加大（0.2s→2.5s）
  - 新增签名：内置 sign 自动计算（md5(排序参数+salt)），无需手动处理
  - 域名迁移：app.dewu.com → dcdn-app-huoshan.dewu.com（Host 头不变）
================================================================================
"""
import asyncio
import random
import re
import time
from datetime import datetime

import httpx
from urllib.parse import urlparse, parse_qs
import log  # 项目统一日志模块：打印+收集+视觉分级
from get_env import get_env
from sendNotify import send_notification_message_collection
# ============ 星愿森林接口签名（2026-09-22 逆向求得）============
# 规则: sign = md5( 按key排序拼接的 "key+value" + SALT )
# 参与参数: URL query 参数 + POST body(JSON) 参数，合并后按 key 排序
# 依据: http-config.json 的 apiEncrypt 清单 + dewu_record.txt 还原的 L 函数
import hashlib as _hashlib

# ============ 接口域名（2026-09 迁移到 CDN；换域名只改这一行）============
# 说明：星愿森林接口实际走 CDN 域名，Host 头仍是 app.dewu.com（见 headers）
_DW_API_HOST = "https://dcdn-app-huoshan.dewu.com"

_DW_SIGN_SALT = "048a9c4943398714b356a696503d2d36"


def _dw_sign(params):
    """计算接口 sign"""
    kv = "".join(str(k) + str(params[k]) for k in sorted(params.keys())) if params else ""
    return _hashlib.md5((kv + _DW_SIGN_SALT).encode("utf-8")).hexdigest()



def dig(obj, *keys, default=None):
    """安全链式取值，任一层为 None/缺失都不会抛 NoneType 异常。

    用法： dig(data, "data", "dailyExtra", "totalDroplet", default=0)
    替代： data.get("data").get("dailyExtra").get("totalDroplet")  ← data 为 None 时崩溃
    """
    cur = obj
    for k in keys:
        if cur is None:
            return default
        if isinstance(cur, dict):
            cur = cur.get(k)
        elif isinstance(cur, (list, tuple)) and isinstance(k, int):
            cur = cur[k] if -len(cur) <= k < len(cur) else None
        else:
            return default
    return default if cur is None else cur

class _SignClient:
    """包装 httpx.AsyncClient：自动附加 sign 参数（GET 用 query，POST 合并 body）"""
    
    def __init__(self, client):
        self._c = client
    
    async def get(self, url=None, params=None, **kw):
        p = dict(params or {})
        p["sign"] = _dw_sign(p)
        return await self._c.get(url, params=p, **kw)
    
    async def post(self, url=None, params=None, json=None, data=None, **kw):
        q = dict(params or {})
        body = json if isinstance(json, dict) else (data if isinstance(data, dict) else {})
        merged = dict(q);
        merged.update(body)
        q["sign"] = _dw_sign(merged)
        return await self._c.post(url, params=q, json=json, data=data, **kw)
    
    def __getattr__(self, name):
        return getattr(self._c, name)


# ---------- 凭据加载（环境变量优先 → 同目录 dw_creds.json 兜底）----------
import os as _os, json as _json

_CRED_FIELDS = {
    "x_auth_token": "dw_x_auth_token",
    "duToken": "dw_duToken",
    "cookieToken": "dw_cookieToken",
    "cookie": "dw_cookie",
    "dudeliveryid": "dw_dudeliveryid",
    "duproductid": "dw_duproductid",
    "sk": "dw_sk",
}


def _split_multi(v):
    return [x.strip() for x in str(v).split("&") if x.strip()] if v else []


def _load_creds():
    """返回 {字段: [各账号的值]}，环境变量优先，其次 dw_creds.json"""
    out = {k: [] for k in _CRED_FIELDS}
    # 1) 环境变量
    for field, env in _CRED_FIELDS.items():
        vals = _split_multi(_os.environ.get(env, ""))
        if vals:
            out[field] = vals
    if out["x_auth_token"]:
        return out
    # 2) dw_creds.json（本地调试）
    try:
        p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "dw_creds.json")
        if _os.path.exists(p):
            data = _json.load(open(p, encoding="utf-8"))
            for acc in data.get("accounts", []):
                for field in _CRED_FIELDS:
                    out[field].append(str(acc.get(field, "") or ""))
    except Exception as e:
        print(f"[凭据] 读取 dw_creds.json 失败: {e}")
    return out


_CREDS = _load_creds()
dw_x_auth_tokens = _CREDS["x_auth_token"]
dw_duTokens = _CREDS["duToken"]
dw_cookieTokens = _CREDS["cookieToken"]
dw_Cookies = _CREDS["cookie"]
dw_dudeliveryids = _CREDS["dudeliveryid"]
dw_duproductids = _CREDS["duproductid"]
dw_sks = _CREDS["sk"]

if not dw_x_auth_tokens:
    print("=" * 70)
    print("[配置缺失] 未找到任何凭据！请按文件顶部说明配置：")
    print("  方式1：设置环境变量 dw_x_auth_token / dw_duToken / dw_cookieToken /")
    print("         dw_cookie / dw_dudeliveryid / dw_duproductid")
    print("  方式2：填写同目录 dw_creds.json 的 accounts 数组")
    print("=" * 70)
share_code_list = []
HELP_SIGNAL = True  # 是否助力

# 得物对高频请求会返回 485「请校验验证码」，间隔太小易触发。
_SLEEP_TASK = 2.5  # 领任务奖励（POST）间隔——最易触发 485，间隔最大
_SLEEP_NORMAL = 1.5  # 普通操作（浇水、领气泡）间隔
_SLEEP_SHORT = 1.0  # 轻量查询间隔
_SLEEP_POLL = 16  # 需等待倒计时的任务轮询间隔
_MAX_BUBBLE_LOOP = 50  # 气泡水滴领取最大轮询次数（防死循环）
_MAX_WATER_LOOP = 20  # 浇水最大次数（防死循环）


class DeWu:
    WATERTING_G: int = 40  # 每次浇水克数
    REMAINING_G: int = 1800  # 最后浇水剩余不超过的克数
    
    def __init__(self, x_auth_token, index, sk, duToken="", cookieToken="", cookie="",
                 dudeliveryid="", duproductid="", waterting_g=WATERTING_G, remaining_g=REMAINING_G):
        self.client = httpx.AsyncClient(verify=False, timeout=60)
        self.client = _SignClient(self.client)  # [签名] 自动附加 sign (2026-09-22)
        self._duToken = duToken
        self._cookieToken = cookieToken
        self._cookie = cookie
        self._dudeliveryid = dudeliveryid
        self._duproductid = duproductid
        self._sk = sk  # [风控] 设备签名，POST 类接口(领任务奖励)必需，缺失会触发 485 验证码
        self.index = index
        self.waterting_g = waterting_g
        self.remaining_g = remaining_g
        # self.headers = {'appVersion': "5.55.0",
        #                 'User-Agent': "Mozilla/5.0 (Linux; Android 15; PJZ110 Build/AP3A.240617.008; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/129.0.6668.70 Mobile Safari/537.36/duapp/5.55.0(android;15)",
        #                 'x-auth-token': x_auth_token,
        #                 'uuid': '0000000000000000',
        self.headers = {
            'Host': "app.dewu.com",
            'User-Agent': "Mozilla/5.0 (Linux; U; Android 16; zh-CN; PJZ110 Build/BP2A.250605.015) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/100.0.4896.58 UWS/5.18.12.0 Mobile Safari/537.36/duapp/6.1.0(android;16)",
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip",
            'ua': "duapp/6.1.0(android;16)",
            'appid': "h5",
            'SK': self._sk,  # [风控] 必需：设备签名(SZStone)，POST类接口(领奖)缺它会485验证码；sks/shumreiId/duid 不可同时带(会400)
            # 'shumeiId': "<已移除：如需使用请自行抓包填写>",  # [已禁用] 风控头→400校验失败(11001) 2026-09-22
            # 'deviceTrait': "<已移除：如需使用请自行抓包填写>",  # [已禁用] 风控头→400校验失败(11001) 2026-09-22
            'x-auth-token': x_auth_token,  # 改用构造参数(全局变量已变列表)
            'networktype': "wifi",
            # 'device_model': "<已移除：如需使用请自行抓包填写>",  # [已禁用] 风控头→400校验失败(11001) 2026-09-22
            'channel': "opp",
            'duToken': self._duToken,
            'appVersion': "6.1.0",
            'emu': "0",
            'countryCode': "CN",
            'cookieToken': self._cookieToken,
            # 注: 下面 a / traceparent 是抓包时的静态值（实测不影响功能）；
            #     如追求完全模拟真机，可自行抓包替换，二者非账号凭据、无需共用
            'traceparent': "00-f5dafcc46ab239d1085c8423b64bcee7-14469d84e4cbebc6-01",
            'dudeliveryid': self._dudeliveryid,
            'duproductid': self._duproductid,
            'isRoot': "0",
            # 'sks': "<已移除：如需使用请自行抓包填写>",  # [已禁用] 风控头→400校验失败(11001) 2026-09-22
            'imei': "",
            # 'duid': "<已移除：如需使用请自行抓包填写>",  # [已禁用] 风控头→400校验失败(11001) 2026-09-22
            'platform': "h5",
            'a': "D9BEC67287063A252394A15D3B572BF35A56964FA63EA870",
            'isProxy': "0",
            'Origin': "https://cdn-m.dewu.com",
            'X-Requested-With': "com.shizhuang.duapp",
            'Sec-Fetch-Site': "same-site",
            'Sec-Fetch-Mode': "cors",
            'Sec-Fetch-Dest': "empty",
            'Referer': "https://cdn-m.dewu.com/",
            'Accept-Language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            'Cookie': self._cookie
        }
        self.user_name = None
        self.tree_id = 0  # 树的id
        self._log_stats = {"ok": 0, "skip": 0, "warn": 0, "err": 0, "info": 0}  # 日志分级计数 (2026-09-23)
        self._gained = 0  # 本次真实到账水滴合计g (2026-09-23)
        self.tasks_completed_number = 0  # 任务完成数
        self.cumulative_task_list = []  # 累计计任务列表
        self.tasks_dict_list = []  # 任务字典列表
        self.is_team_tree = False  # 是否是团队树
    
    def log(self, msg, closed=True, end=None):
        """统一日志：自动加 用户【昵称】，=== === 包装 + 视觉分级前缀

        分级标记（一眼区分性质，2026-09-22）：
          ✅ 真实成功    ⏭️ [已完成] 幂等/已领过(正常)
          ⚠️ [待条件] 风控/条件不满足(可重试)    ❌ [执行错误] 真实错误(需排查)

        :param msg:    日志正文（不含前后缀）
        :param closed: True 时结尾补 ===；False 时不补（用于后面还要接着打印的场景）
        :param end:    透传给 log.log 的 end 参数（如 " " 表示同行接续）
        """
        msg = log.decorate(msg)
        # 分级计数 + 到账水滴累计 (2026-09-23)
        try:
            kind = log.classify(str(msg))
            self._log_stats[kind] = self._log_stats.get(kind, 0) + 1
            if kind == "ok":
                m = re.search(r"获得(\d+)g", str(msg))
                if m:
                    self._gained += int(m.group(1))
        except Exception:
            pass
        text = f"用户【{self.user_name}】，==={msg}" + ("===" if closed else "")
        if end is not None:
            log.log(text, end=end)
        else:
            log.log(text)

    def log_summary(self):
        """本次运行末尾汇总：一眼判断有无真实故障 (2026-09-23)"""
        s = self._log_stats
        line = (f"本次汇总 ▶ 到账+{self._gained}g💧 ｜ "
                f"✅成功{s['ok']} ⏭️已完成{s['skip']} ⚠️待条件{s['warn']} ❌错误{s['err']}")
        # 汇总行本身不再进分级计数，直接原样打印
        text = f"用户【{self.user_name}】，==={line}==="
        log.log(text)
        if s["err"] == 0:
            log.log(f"用户【{self.user_name}】，===✅ 本次无执行错误，全部正常===")
        else:
            log.log(f"用户【{self.user_name}】，===❌ 本次有 {s['err']} 条执行错误，请翻查上方 ❌[执行错误] 行===")
    
    @staticmethod
    def get_url_key_value(url, key):
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        _dict = {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}
        key_value = _dict.get(key)
        return key_value
    
    async def get_user_info(self):
        """
        获取用户信息
        :return: 
        """
        user_info_response = await self.client.get(url=_DW_API_HOST + "/hacking-tree/v1/team/info",
                                                   headers=self.headers)
        if user_info_response.status_code == 200:
            user_info_data = user_info_response.json()
            if user_info_data['code'] == 200:
                self.user_name = dig(user_info_data, "data", "member")[0].get("name")
            else:
                log.log(f"===获取用户信息失败❌, {user_info_data.get('msg')}===")
        else:
            log.log(f"===获取用户信息请求异常❌, {user_info_response.status_code}===")
    
    async def tree_info(self):
        url = _DW_API_HOST + "/hacking-tree/v1/user/target/info"
        tree_info_response = await self.client.get(url=url, headers=self.headers)
        if tree_info_response.status_code == 200:
            tree_info_data = tree_info_response.json()
            if tree_info_data['code'] == 200:
                name = dig(tree_info_data, "data", "name")
                level = dig(tree_info_data, "data", "level")
                self.log(f"目标奖品🥇：{name}, 当前小树等级：{level}")
                return name, level
            self.log(f"获取许愿树信息失败❌, {tree_info_data.get('msg')}")
        else:
            self.log(f"获取许愿树信息请求异常❌, {tree_info_response.status_code}")
    
    async def determine_whether_is_team_tree(self):
        """
        获取是否是团队树
        :return: 
        """
        team_tree_response = await self.client.get(
            url=_DW_API_HOST + "/hacking-tree/v1/team/info",
            headers=self.headers
        )
        if team_tree_response.status_code == 200:
            team_tree_data = team_tree_response.json()
            if dig(team_tree_data, "data", "show") and dig(team_tree_data, "data", "teamTreeId"):
                self.is_team_tree = True
        else:
            self.log(f"获取是否团队树请求异常❌, {team_tree_response.status_code}")
    
    async def sign_in(self):
        """
        签到
        :return: 
        """
        sign_in_response = await self.client.post(
            url=_DW_API_HOST + "/hacking-game-center/v1/sign/sign",
            headers=self.headers
        )
        if sign_in_response.status_code == 200:
            sign_in_data = sign_in_response.json()
            if sign_in_data.get("code") == 200:
                self.log(f"签到成功✅✅")
            else:
                self.log(f"签到失败❌, {sign_in_data.get('msg')}")
        else:
            self.log(f"签到发生异常❌, {sign_in_response.status_code}")
    
    async def droplet_sign_in(self):
        """
        水滴签到
        :return: 
        """
        droplet_sign_in_response = await self.client.post(
            url=_DW_API_HOST + "/hacking-tree/v1/sign/sign_in",
            headers=self.headers
        )
        if droplet_sign_in_response.status_code == 200:
            droplet_sign_in_data = droplet_sign_in_response.json()
            if droplet_sign_in_data.get("code") == 200:
                self.log(f"水滴签到成功✅✅, 获得{dig(droplet_sign_in_data, 'data', 'Num')}g水滴💧💧💧")
            else:
                self.log(f"水滴签到失败❌, {droplet_sign_in_data.get('msg')}")
        else:
            self.log(f"水滴签到发生异常❌, {droplet_sign_in_response.status_code}")
    
    async def receive_droplet_extra(self):
        """
        领取气泡水滴
        :return: 
        """
        flag = -1
        countdown_time = 0
        recevie_signal = False
        for _ in range(_MAX_BUBBLE_LOOP):
            droplet_extra_response = await self.client.get(
                url=_DW_API_HOST + "/hacking-tree/v1/droplet-extra/info",
                headers=self.headers
            )
            if droplet_extra_response.status_code == 200:
                droplet_extra_data = droplet_extra_response.json()
                if droplet_extra_data.get("code") != 200:
                    self.log(f"获取气泡水滴信息失败❌, {droplet_extra_data}")
                    return
                data = droplet_extra_data.get("data")
                receivable = data.get("receivable")
                if receivable:
                    if data.get("dailyExtra"):
                        water_droplet_num = data.get("dailyExtra").get("totalDroplet")
                    else:
                        water_droplet_num = data.get("onlineExtra").get("totalDroplet")
                    if flag == water_droplet_num or recevie_signal:
                        self.log(f"当前可领取气泡水滴{water_droplet_num}g水滴💧")
                        receive_droplet_extra_response = await self.client.post(
                            url=_DW_API_HOST + "/hacking-tree/v1/droplet-extra/receive",
                            headers=self.headers
                        )
                        if receive_droplet_extra_response.status_code == 200:
                            receive_droplet_extra_data = receive_droplet_extra_response.json()
                            if receive_droplet_extra_data.get("code") != 200:
                                countdown_time += 60
                                if countdown_time > 60:
                                    self.log(f"领取气泡水滴失败❌, {receive_droplet_extra_data}")
                                    return
                                self.log(f"等待{countdown_time}秒后领取")
                                await asyncio.sleep(countdown_time)
                                continue
                            self.log(
                                f"领取气泡水滴成功✅✅, 获得{dig(receive_droplet_extra_data, 'data', 'totalDroplet')}g水滴💧")
                            countdown_time = 0  # 重置时间
                            continue
                        else:
                            self.log(f"领取气泡水滴发生异常❌, {receive_droplet_extra_response.status_code}")
                            return  # [保护] 同上 (2026-09-22)
                        flag = water_droplet_num
                        recevie_signal = True
                    flag = water_droplet_num
                    self.log(f"当前气泡水滴{water_droplet_num}g, 未满，开始浇水")
                    if not await self.waterting():
                        recevie_signal = True
                    await asyncio.sleep(1.5)  # [限流改造] 0.5→1.5
                    continue
                water_droplet_num = dig(droplet_extra_data, "data", "dailyExtra", "totalDroplet")
                self.log(
                    f"{dig(droplet_extra_data, 'data', 'dailyExtra', 'popTitle')}, 已经积攒{water_droplet_num}g水滴！")
                return  # [修复] 今日不可领取时直接结束，避免 while 循环刷屏 (2026-09-22)
            else:
                self.log(f"获取气泡水滴信息发生异常❌, {droplet_extra_response.status_code}")
                return  # [保护] 非200不再空转50轮狂发请求 (2026-09-22)
    
    async def waterting_droplet_extra(self):
        """
        浇水充满气泡水滴
        :return: 
        """
        while True:
            water_response = await self.client.get(
                url=_DW_API_HOST + "/hacking-tree/v1/droplet-extra/info",
                headers=self.headers
            )
            if water_response.status_code == 200:
                water_data = water_response.json()
                count = dig(water_data, "data", "dailyExtra", "times", default=0)
                if not count:
                    self.log(
                        f"气泡水滴已充满，明日可领取{dig(water_data, 'data', 'dailyExtra', 'totalDroplet')}g")
                    return
                for _ in range(count):
                    if not await self.waterting():
                        return
                    await asyncio.sleep(0.5)
            else:
                self.log(f"获取气泡水滴信息发生异常❌, {water_response.status_code}")
                return  # [修复] 非200不再无限空转 (2026-09-22)
    
    async def receive_bucket_droplet(self):
        """
        领取木桶水滴,200秒满一次,每天领取3次
        :return: 
        """
        receive_bucket_droplet_response = await self.client.post(
            url=_DW_API_HOST + "/hacking-tree/v1/droplet/get_generate_droplet",
            headers=self.headers
        )
        if receive_bucket_droplet_response.status_code == 200:
            receive_bucket_droplet_data = receive_bucket_droplet_response.json()
            if receive_bucket_droplet_data.get("code") != 200:
                self.log(f"领取木桶水滴失败❌, {receive_bucket_droplet_data}")
                return
            self.log(f"领取木桶水滴成功✅✅, 获得{dig(receive_bucket_droplet_data, 'data', 'droplet')}g水滴💧")
        else:
            self.log(f"领取木桶水滴发生异常❌, {receive_bucket_droplet_response.status_code}")
    
    async def judging_bucket_droplet(self):
        """
        判断木桶水滴是否可以领取
        :return: 
        """
        judging_bucket_droplet_response = await self.client.get(
            url=_DW_API_HOST + "/hacking-tree/v1/droplet/generate_info",
            headers=self.headers
        )
        if judging_bucket_droplet_response.status_code == 200:
            judging_bucket_droplet_data = judging_bucket_droplet_response.json()
            if dig(judging_bucket_droplet_data, "data", "currentDroplet") == 100:
                self.log(f"今天已领取木桶水滴{dig(judging_bucket_droplet_data, 'data', 'getTimes')}次")
                await self.receive_bucket_droplet()
                return True
            return False
        else:
            self.log(f"判断木桶水滴发生异常❌, {judging_bucket_droplet_response.status_code}")
    
    async def get_shared_code(self):
        """
        获取助力码
        :return: 
        """
        get_shared_code_response = await self.client.post(
            url=_DW_API_HOST + "/hacking-tree/v1/keyword/gen",
            headers=self.headers
        )
        if get_shared_code_response.status_code == 200:
            get_shared_code_data = get_shared_code_response.json()
            if get_shared_code_data.get("code") != 200:
                self.log(f"获取助力码失败❌, {get_shared_code_data}")
                return
            share_code = dig(get_shared_code_data, "data", "keywordDesc").replace("\n", "")
            self.log(f"获取助力码 {share_code} 成功✅✅")
        else:
            self.log(f"获取助力码发生异常❌, {get_shared_code_response.status_code}")
    
    async def get_droplet_number(self):
        """
        获取水滴数
        :return: 
        """
        headers = self.headers
        headers.update(
            {
                'channel': 'opp',
                'uuid': '0000000000000000',
                'isProxy': "0",
                'emu': "0",
                'isRoot': "0",
                # 'deviceTrait': "<已移除：如需使用请自行抓包填写>",  # [已禁用] 风控头→400 2026-09-22
                'ua': "duapp/5.55.0(android;15)",
                'Origin': "https://cdn-m.dewu.com",
                'X-Requested-With': "com.shizhuang.duapp",
                'Sec-Fetch-Site': "same-site",
                'Sec-Fetch-Mode': "cors",
                'Sec-Fetch-Dest': "empty",
                'Referer': "https://cdn-m.dewu.com/",
                'Accept-Language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            }
        )
        get_droplet_number_response = await self.client.post(
            url=_DW_API_HOST + "/hacking-tree/v1/user/init",
            headers=headers,
            json={"keyword": ""}
        )
        if get_droplet_number_response.status_code == 200:
            get_droplet_number_data = get_droplet_number_response.json()
            data = get_droplet_number_data.get("data")
            if data:
                droplet_number = data.get("droplet")
                return droplet_number
            else:
                self.log(f"获取水滴数失败❌, {get_droplet_number_data}")
        else:
            self.log(f"获取水滴数发生异常❌, {get_droplet_number_response.status_code}")
    
    async def receive_cumulative_tasks_reward(self, condition):
        """
        领取累计任务奖励
        :return: 
        """
        recevie_cumulative_tasks_reward_response = await self.client.post(
            url=_DW_API_HOST + "/hacking-tree/v1/task/extra",
            headers=self.headers,
            json={"condition": condition}
        )
        if recevie_cumulative_tasks_reward_response.status_code == 200:
            recevie_cumulative_tasks_reward_data = recevie_cumulative_tasks_reward_response.json()
            if recevie_cumulative_tasks_reward_data.get("code") != 200:
                self.log(f"领取累计任务奖励失败❌, {recevie_cumulative_tasks_reward_data}")
                return
            self.log(f"领取累计任务奖励成功✅✅, 获得{dig(recevie_cumulative_tasks_reward_data, 'data', 'num')}g水滴💧")
        else:
            self.log(f"领取累计任务奖励发生异常❌, {recevie_cumulative_tasks_reward_response.status_code}")
    
    async def receive_task_reward(self, classify, task_id, task_type):
        """
        领取任务奖励
        :param classify: 
        :param task_id: 
        :param task_type: 
        :return: 
        """
        await asyncio.sleep(_SLEEP_TASK)  # [节流] 领奖间隔，防 485
        url = _DW_API_HOST + "/hacking-tree/v1/task/receive"
        if task_type in [251]:
            json = {'classify': classify, 'taskId': task_id, 'completeFlag': 1}
        else:
            json = {'classify': classify, 'taskId': task_id}
        recevie_task_reward_response = await self.client.post(
            url=url,
            headers=self.headers,
            json=json
        )
        if recevie_task_reward_response.status_code == 200:
            recevie_task_reward_data = recevie_task_reward_response.json()
            if recevie_task_reward_data.get("code") != 200:
                self.log(f"领取任务奖励失败❌, {recevie_task_reward_data}")
                return
            self.log(f"领取任务奖励成功✅✅, 获得{dig(recevie_task_reward_data, 'data', 'num')}g水滴💧")
        else:
            self.log(f"领取任务奖励发生异常❌, {recevie_task_reward_response.status_code}")
    
    async def receive_watering_reward(self):
        """
        领取浇水奖励
        :return: 
        """
        recevie_watering_reward_response = await self.client.post(
            url=_DW_API_HOST + "/hacking-tree/v1/tree/get_watering_reward",
            headers=self.headers,
            json={"promote": ""}
        )
        if recevie_watering_reward_response.status_code == 200:
            recevie_watering_reward_data = recevie_watering_reward_response.json()
            if recevie_watering_reward_data.get("code") != 200:
                self.log(f"领取浇水奖励失败❌, {recevie_watering_reward_data}")
                return
            self.log(
                f"领取浇水奖励成功✅✅, 获得{dig(recevie_watering_reward_data, 'data', 'currentWateringReward', 'rewardNum')}g水滴💧")
        else:
            self.log(f"领取浇水奖励发生异常❌, {recevie_watering_reward_response.status_code}")
    
    async def execute_weekend_task(self):
        """周末活动任务（2026-09-22 新增）
        机制（逆向实测）：任务完成累计到 accumulateVal，周末结算发放。
        - taskStatus=10 已完成待领 → obtain + receive 计入累计
        - taskStatus=20 已计入（如 login 今日已 +50）
        - taskStatus=0  进行中（watering 靠正常浇水推进 curStep，满额后可领）
        可自动化：login（每日登录）+ 任何 status==10 的已完成任务
        无法自动化：pk/order/waterEx（需真实 PK/下单/兑换）
        """
        info_resp = await self.client.get(
            url=_DW_API_HOST + "/hacking-tree/v1/weekend/info",
            headers=self.headers
        )
        if info_resp.status_code != 200:
            return
        info_data = info_resp.json()
        if info_data.get("code") != 200:
            return
        week_data = dig(info_data, "data", "weekData", default={}) or {}
        task_list = week_data.get("taskList") or []
        if not task_list:
            return
        acc = week_data.get("accumulateVal", 0)
        self.log(f"周末活动累计水滴：{acc}g（周末结算发放，剩余{week_data.get('remainDays','?')}天）")

        for wt in task_list:
            wtt = wt.get("taskType")
            status = wt.get("taskStatus")
            title = wt.get("title", wtt)
            # status==10 已完成待领，或 login（每日可计入）
            if status == 10 or (wtt == "login" and status not in (20, 30)):
                await asyncio.sleep(_SLEEP_NORMAL)
                ob = await self.client.post(
                    url=_DW_API_HOST + "/hacking-tree/v1/weekend/task_obtain",
                    headers=self.headers, json={"taskType": wtt}
                )
                if ob.status_code == 200 and ob.json().get("code") == 200:
                    await asyncio.sleep(_SLEEP_NORMAL)
                    rc = await self.client.post(
                        url=_DW_API_HOST + "/hacking-tree/v1/weekend/task_receive",
                        headers=self.headers, json={"taskType": wtt}
                    )
                    rc_data = rc.json() if rc.status_code == 200 else {}
                    if rc_data.get("code") == 200:
                        self.log(f"周末任务【{title}】完成✅，+{wt.get('reward')}g 计入累计")
                    # 711000001=已计入/暂无可领，静默跳过
        # 尝试领取累计奖励（get_reward 无参，满档位才会真发）
        await asyncio.sleep(_SLEEP_NORMAL)
        gr = await self.client.post(
            url=_DW_API_HOST + "/hacking-tree/v1/weekend/get_reward",
            headers=self.headers, json={}
        )
        gr_data = gr.json() if gr.status_code == 200 else {}
        if gr_data.get("code") == 200:
            self.log(f"领取周末累计奖励成功✅✅, {gr_data.get('data')}")

    async def receive_level_reward(self):
        """
        领取等级奖励
        :return: 
        """
        for _ in range(_MAX_WATER_LOOP):
            recevie_level_reward_response = await self.client.post(
                url=_DW_API_HOST + "/hacking-tree/v1/tree/get_level_reward",
                headers=self.headers,
                json={"promote": ""}
            )
            if recevie_level_reward_response.status_code == 200:
                recevie_level_reward_data = recevie_level_reward_response.json()
                if recevie_level_reward_data.get("code") != 200 or recevie_level_reward_data.get("data") is None:
                    self.log(f"领取等级奖励失败❌, {recevie_level_reward_data.get('msg')}")
                    return
                level = dig(recevie_level_reward_data, "data", "levelReward", "showLevel") - 1
                reward_num = dig(recevie_level_reward_data, "data", "currentLevelReward", "rewardNum")
                self.log(f"领取{level}级奖励成功✅✅, 获得{reward_num}g水滴💧")
                if not dig(recevie_level_reward_data, "data", "levelReward", "isComplete"):
                    return
                await asyncio.sleep(1)
            else:
                self.log(f"领取等级奖励发生异常❌, {recevie_level_reward_response.status_code}")
    
    async def execute_receive_watering_reward(self):
        """
        多次执行浇水，领取浇水奖励
        :return: 
        """
        for _ in range(_MAX_WATER_LOOP):
            execute_receive_watering_reward_response = await self.client.get(
                url=_DW_API_HOST + "/hacking-tree/v1/tree/get_tree_info",
                headers=self.headers
            )
            if execute_receive_watering_reward_response.status_code == 200:
                execute_receive_watering_reward_data = execute_receive_watering_reward_response.json()
                if execute_receive_watering_reward_data.get("code") != 200:
                    self.log(f"获取种树进度失败❌, {execute_receive_watering_reward_data}")
                    return
                count = dig(execute_receive_watering_reward_data, "data", "nextWateringTimes")
                if dig(execute_receive_watering_reward_data, "data", "wateringReward") is None or count <= 0:
                    return
                for _ in range(count):
                    if not await self.waterting():
                        return
                    await asyncio.sleep(0.5)
            else:
                self.log(f"获取种树进度发生异常❌, {execute_receive_watering_reward_response.status_code}")
    
    async def waterting_until_less_than(self):
        """
        浇水直到小于指定克数
        :return: 
        """
        droplet_number = await self.get_droplet_number()
        if droplet_number > self.waterting_g:
            count = int((droplet_number - self.remaining_g) / self.waterting_g)
            for _ in range(count + 1):
                if not await self.waterting():
                    return
                await asyncio.sleep(0.5)
    
    async def submit_task_completion_status(self, json):
        # [修复 2026-09-22] 得物后端要求 taskType 为字符串，传 int 会返回 900「请求参数不合法」
        if isinstance(json, dict) and "taskType" in json and json["taskType"] is not None:
            json = dict(json)
            json["taskType"] = str(json["taskType"])
        submit_task_completion_status_response = await self.client.post(
            url=_DW_API_HOST + "/hacking-task/v1/task/commit",
            headers=self.headers,
            json=json
        )
        if submit_task_completion_status_response.status_code == 200:
            submit_task_completion_status_data = submit_task_completion_status_response.json()
            if submit_task_completion_status_data.get("code") == 200:
                return True
            # [修复] 原来静默返回 False，看不到真因；现在打印服务端响应
            self.log(f"提交任务完成状态未通过❌, {submit_task_completion_status_data}")
            return False
        else:
            self.log(f"提交任务完成状态发生异常❌, {submit_task_completion_status_response.status_code}")
            return False
    
    async def get_task_list(self):
        """
        获取任务列表
        :return: 
        """
        get_task_list_response = await self.client.get(
            url=_DW_API_HOST + "/hacking-tree/v1/task/list",
            headers=self.headers
        )
        if get_task_list_response.status_code == 200:
            get_task_list_data = get_task_list_response.json()
            if get_task_list_data.get("code") == 200:
                self.tasks_completed_number = dig(get_task_list_data, "data", "userStep")  # 已完成任务数量
                self.cumulative_task_list = dig(get_task_list_data, 'data', 'extraAwardList')  # 累计任务列表            
                self.tasks_dict_list = dig(get_task_list_data, 'data', 'taskList')  # 任务列表
                return True
        else:
            self.log(f"获取任务列表发生异常❌, {get_task_list_response.status_code}")
            return False
    
    async def task_obtain(self, task_id, task_type):
        """
        水滴大放送任务
        :param task_id: 
        :param task_type: 
        :return: 
        """
        task_obtain_response = await self.client.post(
            url=_DW_API_HOST + "/hacking-task/v1/task/obtain",
            headers=self.headers,
            json={"taskId": task_id, "taskType": task_type}
        )
        if task_obtain_response.status_code == 200:
            task_obtain_data = task_obtain_response.json()
            if task_obtain_data.get("code") == 200 and task_obtain_data.get("status") == 200:
                return True
            return False
        else:
            self.log(f"水滴大放送任务步骤发生异常❌, {task_obtain_response.status_code}")
    
    async def task_commit_pre(self, json):
        """
        浏览任务
        :param json: 
        :return: 
        """
        task_commit_pre_response = await self.client.post(
            url=_DW_API_HOST + "/hacking-task/v1/task/pre_commit",
            headers=self.headers,
            json=json
        )
        if task_commit_pre_response.status_code == 200:
            task_commit_pre_data = task_commit_pre_response.json()
            if task_commit_pre_data.get("code") == 200 and task_commit_pre_data.get("status") == 200:
                return True
            return False
        else:
            self.log(f"浏览任务发生异常❌, {task_commit_pre_response.status_code}")
    
    async def execute_task(self):
        """
        执行任务
        :return: 
        """
        await self.get_task_list()
        for task_dict in self.tasks_dict_list:
            if task_dict.get("isReceiveReward"):  # 为True，这个任务奖励已经领取过了
                continue
            if task_dict.get("rewardCount") >= 3000:  # 奖励的水滴大于3000，需要下单，跳过
                continue
            classify = task_dict.get('classify')
            task_id = task_dict.get('taskId')
            task_type = task_dict.get('taskType')
            task_name = task_dict.get('taskName')
            btd = self.get_url_key_value(task_dict.get('jumpUrl'), 'btd')
            btd = int(btd) if btd else 0
            spu_id = self.get_url_key_value(task_dict.get('jumpUrl'), 'spuId')
            spu_id = int(spu_id) if spu_id else 0
            if task_dict.get("isComplete"):
                if task_name == "领40g水滴值" and not task_dict.get("receivable"):
                    continue
                self.log(f"开始执行任务【{task_name}】")
                await self.receive_task_reward(classify, task_id, task_type)
                continue
            self.log(f"开始执行任务【{task_name}】")
            if task_name == "完成一次签到":
                await self.sign_in()
                json = {
                    "taskId": task_dict.get("taskId"),
                    "taskType": str(task_dict.get("taskType")),
                }
                if await self.submit_task_completion_status(json):
                    await self.receive_task_reward(classify, task_id, task_type)
                    continue
            if task_name == "领40g水滴值":
                await self.receive_task_reward(classify, task_id, task_type)
                continue
            if task_name == "收集一次水滴生产":
                if await self.judging_bucket_droplet():
                    await self.receive_task_reward(classify, task_id, task_type)
                else:
                    self.log(f"当前木桶水滴未达到100g，下次来完成任务吧！")
                continue
            if task_name == "浏览【我】的右上角星愿森林入口":
                report_action_response = await self.client.post(
                    url=_DW_API_HOST + "/hacking-tree/v1/user/report_action",
                    headers=self.headers,
                    json={"action": task_id}
                )
                if report_action_response.status_code == 200:
                    report_action_data = report_action_response.json()
                    if report_action_data.get("code"):
                        await self.receive_task_reward(classify, task_id, task_type)
                    continue
            if any(re.match(pattern, task_name) for pattern in
                   ["参与1次上上签活动", "从桌面组件访问许愿树", "参与1次拆盲盒", "去.*"]):
                await self.submit_task_completion_status(
                    {
                        "taskId": task_id,
                        "taskType": int(task_type)
                    }
                )
                await self.receive_task_reward(classify, task_id, task_type)
                continue
            
            if any(re.match(pattern, task_name) for pattern in [".*订阅.*", ".*逛一逛.*", "逛逛.*活动"]):
                await self.submit_task_completion_status(
                    {
                        "taskId": task_id,
                        "taskType": int(task_type),
                        "btd": btd
                    }
                )
                await self.receive_task_reward(classify, task_id, task_type)
                continue
            if any(re.match(pattern, task_name) for pattern in [".*逛逛.*", "浏览.*s"]):
                if await self.task_commit_pre(
                        {
                            "taskId": task_id,
                            "taskType": int(task_type),
                            "btd": btd
                        }
                ):
                    await asyncio.sleep(16)
                    await self.submit_task_completion_status(
                        {
                            "taskId": task_id,
                            "taskType": int(task_type),
                            "activityType": None,
                            "activityId": None,
                            "taskSetId": None,
                            "venueCode": None,
                            "venueUnitStyle": None,
                            "taskScene": None,
                            "btd": btd
                        }
                    )
                    await self.receive_task_reward(classify, task_id, task_type)
                    continue
            if any(re.match(pattern, task_name) for pattern in [".*晒图.*"]):
                if await self.task_commit_pre(
                        {
                            "taskId": task_id,
                            "taskType": int(task_type)
                        }
                ):
                    await asyncio.sleep(16)
                    await self.submit_task_completion_status(
                        {
                            "taskId": task_id,
                            "taskType": int(task_type),
                            "activityType": None,
                            "activityId": None,
                            "taskSetId": None,
                            "venueCode": None,
                            "venueUnitStyle": None,
                            "taskScene": None
                        }
                    )
                    await self.receive_task_reward(classify, task_id, task_type)
                    continue
            if task_name == "完成五次浇灌":
                count = task_dict.get("total") - task_dict.get("curStep")
                if await self.get_droplet_number() < (self.waterting_g * count):
                    self.log(f"当前水滴不足以完成任务，下次来完成任务吧！")
                    continue
                for _ in range(count):
                    await asyncio.sleep(0.5)
                    if not await self.waterting():
                        break
                else:
                    if await self.submit_task_completion_status(
                            {
                                "taskId": task_dict.get("taskId"),
                                "taskType": str(task_dict.get("taskType"))
                            }
                    ):
                        await self.receive_task_reward(classify, task_id, task_type)
                        continue
            if any(re.match(pattern, task_name) for pattern in [".*专场", ".*水滴大放送"]):
                if await self.task_obtain(task_id, task_type):
                    if await self.task_commit_pre(
                            {
                                "taskId": task_id,
                                "taskType": 16
                            }
                    ):
                        await asyncio.sleep(16)
                        await self.submit_task_completion_status(
                            {
                                "taskId": task_id,
                                "taskType": int(task_type)
                            }
                        )
                        await self.receive_task_reward(classify, task_id, task_type)
                        continue
            # ---- 收藏商品任务 (taskType=50)，2026-09-22 新增 ----
            # 识别依据：taskType==50 且 jumpUrl 带 spuId（形如「收藏想要的【品牌】商品」）
            if task_type == 50 and spu_id:
                await self.do_favorite_task(classify, task_id, task_type, spu_id, btd,
                                            already_complete=bool(task_dict.get("isComplete")))
                continue
            log.log(f"该任务暂时无法处理，请提交日志给作者！{task_dict}")
    
    async def execute_cumulative_task(self):
        """
        执行累计任务
        :return: 
        """
        await self.get_task_list()
        for task in self.cumulative_task_list:
            if task.get("status") == 1:
                self.log(f"开始领取累计任务数达{task.get('condition')}个的奖励")
                await self.receive_cumulative_tasks_reward(task.get("condition"))
                await asyncio.sleep(1)
    
    async def receive_free_droplet(self):
        """水滴福利每日免费领水滴（2026-09-22 新增）
        接口：droplet_benefit/receive_droplet（空 body），每日一次，实测 +50g。
        今日已领返回 isOk=false，静默跳过。
        """
        resp = await self.client.post(
            url=_DW_API_HOST + "/hacking-tree/v1/droplet_benefit/receive_droplet",
            headers=self.headers,
            json={}
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 200 and dig(data, "data", "isOk"):
                self.log(f"领取水滴福利成功✅✅, 当前水滴{dig(data, 'data', 'userDroplet', default='?')}g💧")
            else:
                self.log("水滴福利今日已领取或暂无可领")
        else:
            self.log(f"领取水滴福利发生异常❌, {resp.status_code}")

    async def droplet_invest(self):
        """
        水滴投资
        :return: 
        """
        droplet_invest_response = await self.client.get(
            url=_DW_API_HOST + "/hacking-tree/v1/invest/info",
            headers=self.headers
        )
        if droplet_invest_response.status_code == 200:
            droplet_invest_data = droplet_invest_response.json()
            if not dig(droplet_invest_data, "data", "isToday"):
                await self.receive_droplet_invest()
            else:
                self.log(f"今日已领取过水滴投资奖励了")
            await asyncio.sleep(2)
            droplet_invest_response = await self.client.get(
                url=_DW_API_HOST + "/hacking-tree/v1/invest/info",
                headers=self.headers
            )
            droplet_invest_data = droplet_invest_response.json()
            if dig(droplet_invest_data, "data", "triggered"):
                invest_commit_response = await self.client.post(
                    url=_DW_API_HOST + "/hacking-tree/v1/invest/commit",
                    headers=self.headers
                )
                invest_commit_data = invest_commit_response.json()
                if invest_commit_data.get("code") == 200 and invest_commit_data.get("status") == 200:
                    self.log(f"水滴投资成功✅✅, 水滴-100g")
                    return
                if invest_commit_data.get("msg") == "水滴不够了":
                    self.log(f"水滴投资失败❌, 水滴不够了。{invest_commit_data.get('msg')}")
                    return
                self.log(f"水滴投资有问题❌, {invest_commit_data}")
                return
            else:
                self.log(f"今日已水滴投资过了")
        else:
            self.log(f"水滴投资发生异常❌, {droplet_invest_response.status_code}")
    
    async def receive_droplet_invest(self):
        """
        领取水滴投资奖励
        :return: 
        """
        receive_droplet_invest_response = await self.client.post(
            url=_DW_API_HOST + "/hacking-tree/v1/invest/receive",
            headers=self.headers
        )
        if receive_droplet_invest_response.status_code == 200:
            receive_droplet_invest_data = receive_droplet_invest_response.json()
            profit = dig(receive_droplet_invest_data, "data", "profit")
            self.log(f"领取水滴投资奖励成功✅✅，收益-{profit}g水滴💧")
        else:
            self.log(f"领取水滴投资奖励请求发生异常❌, {receive_droplet_invest_response.status_code}")
    
    async def get_share_code(self):
        """
        获取助力码
        :return: 
        """
        get_share_code_response = await self.client.get(
            url=_DW_API_HOST + "/hacking-tree/v1/keyword/gen",
            headers=self.headers
        )
        if get_share_code_response.status_code == 200:
            get_share_code_data = get_share_code_response.json()
            if get_share_code_data.get("status") == 200:
                keyword = dig(get_share_code_data, "data", "keyword")
                keyword = re.findall("œ(.*?)œ ", keyword)
                if keyword:
                    self.log(f"获取助力码成功✅✅, {keyword[0]}")
                    return keyword[0]
            else:
                self.log(f"获取助力码失败❌, {get_share_code_data}")
        else:
            self.log(f"获取助力码发生异常❌, {get_share_code_response.status_code}")
    
    async def help_user(self):
        """
        助力
        :return: 
        """
        if not HELP_SIGNAL:  # 未开启助力
            return
        url = _DW_API_HOST + "/hacking-tree/v1/user/init"
        if self.index == 0:
            for share_code in share_code_list:
                help_user_response = await self.client.post(
                    url=url,
                    headers=self.headers,
                    json={"keyword": share_code}
                )
                if help_user_response.status_code == 200:
                    help_user_data = help_user_response.json()
                    data = help_user_data.get("data")
                    if not data:
                        continue
                    invite_res = data.get("inviteRes")
                    if any(re.match(pattern, invite_res) for pattern in ["助力成功", "助力失败", "今日已助力过了"]):
                        self.log(f"开始助力{share_code}", end=" ")
                        log.log(invite_res)
                        return
                    await asyncio.sleep(random.randint(20, 30) / 10)
                else:
                    self.log(f"助力发生异常❌, {help_user_response.status_code}")
        for share_code in share_code_list:
            self.log(f"开始助力{share_code}", end=" ")
            help_user_response = await self.client.post(
                url=url,
                headers=self.headers,
                json={"keyword": share_code}
            )
            if help_user_response.status_code == 200:
                help_user_data = help_user_response.json()
                data = help_user_data.get("data")
                if not data:
                    self.log(f"助力失败❌, {help_user_data}")
                invite_res = data.get("inviteRes")
                log.log(invite_res)
                if any(re.match(pattern, invite_res) for pattern in ["助力成功", "助力失败", "今日已助力过了"]):
                    return
                await asyncio.sleep(random.randint(20, 30) / 10)
            else:
                self.log(f"助力发生异常❌, {help_user_response.status_code}")
        return
    
    async def receive_help_reward(self):
        """
        领取助力奖励
        :return: 
        """
        receive_help_reward_list_response = await self.client.get(
            url=_DW_API_HOST + "/hacking-tree/v1/invite/list",
            headers=self.headers
        )
        if receive_help_reward_list_response.status_code == 200:
            receive_help_reward_list_data = receive_help_reward_list_response.json()
            if receive_help_reward_list_data.get("status") == 200:
                reward_list = dig(receive_help_reward_list_data, "data", "list")
                if not reward_list:
                    return
                for reward in reward_list:
                    if reward.get("status") != 0:
                        continue
                    invitee_user_id = reward.get("inviteeUserId")
                    receive_help_reward_response = await self.client.post(
                        url=_DW_API_HOST + "/hacking-tree/v1/invite/reward",
                        headers=self.headers,
                        json={
                            "inviteeUserId": invitee_user_id
                        }
                    )
                    receive_help_reward_data = receive_help_reward_response.json()
                    if receive_help_reward_data.get("status") == 200:
                        droplet = dig(receive_help_reward_data, "data", "droplet")
                        self.log(f"领取助力奖励成功✅✅，获得{droplet}g水滴💧")
                        continue
                    self.log(f"领取助力奖励失败❌, {receive_help_reward_data}")
                return
            self.log(f"领取助力奖励失败❌, {receive_help_reward_list_data}")
        else:
            self.log(f"领取助力奖励发生异常❌, {receive_help_reward_list_response.status_code}")
    
    async def receive_hybrid_online_reward(self):
        """
        领取合种上线奖励
        :return: 
        """
        team_reward_list_response = await self.client.get(
            url=_DW_API_HOST + f"/hacking-tree/v1/team/sign/list?teamTreeId={self.tree_id}",
            headers=self.headers
        )
        if team_reward_list_response.status_code == 200:
            team_reward_list_data = team_reward_list_response.json()
            if team_reward_list_data.get("data") is None:
                return
            reward_list = dig(team_reward_list_data, "data", "list")
            if not reward_list:
                return
            for rewaed in reward_list:
                if rewaed.get("isComplete") and not rewaed.get("isReceive"):
                    receive_hybrid_online_reward_response = await self.client.post(
                        url=_DW_API_HOST + "/hacking-tree/v1/team/sign/receive",
                        headers=self.headers,
                        json={
                            "teamTreeId": self.tree_id,
                            "day": rewaed.get("day")
                        }
                    )
                    receive_hybrid_online_reward_data = receive_hybrid_online_reward_response.json()
                    if dig(receive_hybrid_online_reward_data, "data", "isOk"):
                        self.log(f"领取合种上线奖励成功✅✅, 获得{rewaed.get('num')}g水滴💧")
                        continue
                    self.log(f"领取合种上线奖励失败❌, {receive_hybrid_online_reward_data}")
        return
    
    async def receive_air_drop(self):
        """
        领取空中水滴
        :return: 
        """
        for _ in range(2):
            receive_air_drop_response = await self.client.post(
                url=_DW_API_HOST + "/hacking-tree/v1/droplet/air_drop_receive",
                headers=self.headers,
                json={
                    "clickCount": 20,
                    "time": int(time.time())
                }
            )
            if receive_air_drop_response.status_code == 200:
                receive_air_drop_data = receive_air_drop_response.json()
                data = receive_air_drop_data.get("data")
                if data is not None and data.get("isOk"):
                    self.log(f"领取空中水滴成功✅✅，获得{data.get('droplet')}g水滴💧")
                    await asyncio.sleep(1)
                    continue
                break
    
    async def favorite_spu(self, spu_id):
        """收藏商品（taskType=50 收藏任务的第一步）

        接口来源：H5 JS dw-growth-share-0.js 逆向（services.goodFavorite）
        :param spu_id: 商品 spuId（从任务 jumpUrl 里解析）
        :return: True 收藏成功
        """
        if not spu_id:
            return False
        # code 700「请先登录」/401 多为密集请求后的临时登录态抖动，等待后重试一次
        for attempt in range(2):
            resp = await self.client.post(
                url=_DW_API_HOST + "/api/v1/h5/favorite/fire/app/favorite/add/spu/v2",
                headers=self.headers,
                json={"spuId": spu_id}
            )
            try:
                code = resp.json().get("code")
            except Exception:
                code = None
            if resp.status_code == 200 and code == 200:
                return True
            if code in (700, 401) and attempt == 0:
                await asyncio.sleep(3)  # 等登录态恢复后重试
                continue
            self.log(f"收藏商品失败❌, {resp.status_code} {resp.text[:80]}")
            return False
        return False

    async def do_favorite_task(self, classify, task_id, task_type, spu_id, btd, already_complete=False):
        """执行收藏商品任务（taskType=50）完整三步流程

        流程（H5 JS 逆向）：收藏商品 → 提交任务完成 → 领取奖励
        """
        # ① 收藏商品（已完成的任务跳过收藏，直接走领奖，避免重复收藏）
        if not already_complete:
            if not await self.favorite_spu(spu_id):
                return
            await asyncio.sleep(_SLEEP_NORMAL)
        # ② 提交任务完成状态（走 hacking-task/v1/task/commit）
        commit_resp = await self.client.post(
            url=_DW_API_HOST + "/hacking-task/v1/task/commit",
            headers=self.headers,
            json={
                "taskId": task_id,
                "taskType": str(task_type),
                "spuId": spu_id,
                "btd": btd,
                "kocSource": ""
            }
        )
        if commit_resp.status_code != 200 or commit_resp.json().get("code") != 200:
            self.log(f"收藏任务提交失败❌, {commit_resp.text[:100]}")
            return
        # ③ 领取奖励
        await self.receive_task_reward(classify, task_id, task_type)

    async def click_product(self):
        products = [
            {"spuId": 3030863, "timestamp": 1690790735382, "sign": "2889b16b3077c5719288d105a14ffa1e"},
            {"spuId": 4673547, "timestamp": 1690790691956, "sign": "cc3cc95253d29a03fc6e79bfe2200143"},
            {"spuId": 1502607, "timestamp": 1690791565022, "sign": "04951eac012785ccb2600703a92c037b"},
            {"spuId": 2960612, "timestamp": 1690791593097, "sign": "fb667d45bc3950a7beb6e3fa0fc05089"},
            {"spuId": 3143593, "timestamp": 1690791613243, "sign": "82b9fda61be79f7b8833087508d6abe2"},
            {"spuId": 3067054, "timestamp": 1690791639606, "sign": "2808f3c7cf2ededea17d3f70a2dc565d"},
            {"spuId": 4448037, "timestamp": 1690791663078, "sign": "335bc519ee9183c086beb009adf93738"},
            {"spuId": 3237561, "timestamp": 1690791692553, "sign": "5c113b9203a510b7068b3cd0f6b7c25e"},
            {"spuId": 3938180, "timestamp": 1690792014889, "sign": "3841c0272443dcbbab0bcb21c94c6262"}
        ]
        for product in products:
            product_response = await self.client.post(
                url=_DW_API_HOST + "/hacking-tree/v1/product/spu",
                headers=self.headers,
                json=product
            )
            if product_response.status_code == 200:
                product_data = product_response.json()
                if product_data.get("data") is None:
                    self.log(f"今天已经完成过这个任务了❌, {product_data}")
                    return
                if dig(product_data, "data", "isReceived"):
                    self.log(f"获得{dig(product_data, 'data', 'dropLetReward')}g水滴💧", closed=False)
                    return
                await asyncio.sleep(1)
            else:
                self.log(f"点击商品任务请求异常❌, {product_response.status_code}")
    
    async def receive_discover_droplet(self):
        """
        领取发现水滴
        :return: 
        """
        while True:
            receive_discover_droplet_response = await self.client.post(
                url=_DW_API_HOST + "/hacking-tree/v1/product/task/seek-receive",
                headers=self.headers,
                json={
                    "sign": "9888433e6d10b514e5b5be4305d123f0",
                    "timestamp": int(time.time() * 1000)
                }
            )
            if receive_discover_droplet_response.status_code == 200:
                receive_discover_droplet_data = receive_discover_droplet_response.json()
                log.log(receive_discover_droplet_data)
                # [修复] 原 while True 无任何出口会无限狂发请求 (2026-09-22)
                if receive_discover_droplet_data.get("code") != 200:
                    return
                if not (receive_discover_droplet_data.get("data") or {}).get("isOk"):
                    return
                await asyncio.sleep(_SLEEP_SHORT)
            else:
                self.log(f"领取发现水滴异常❌, {receive_discover_droplet_response.status_code}")
                return
    
    async def receive_brand_specials(self):
        """
        领取品牌特惠奖励
        :return: 
        """
        receive_brand_specials_response = await self.client.get(
            url=_DW_API_HOST + "/hacking-ad/v1/activity/compound/list?bizId=tree",
            headers=self.headers
        )
        if receive_brand_specials_response.status_code == 200:
            receive_brand_specials_data = receive_brand_specials_response.json()
            if receive_brand_specials_data.get("data") is None:
                self.log(f"当前没有可以完成的品牌特惠任务")
                return
            if dig(receive_brand_specials_data, "data", "list") is None:
                self.log(f"当前没有可以完成的品牌特惠任务")
                return
            ad_list = dig(receive_brand_specials_data, "data", "list")
            for ad in ad_list:
                if ad.get("isReceived"):
                    continue
                aid = ad.get("task").get("taskId")
                receive_brand_specials_response = await self.client.post(
                    url=_DW_API_HOST + "/hacking-ad/v1/activity/receive",
                    headers=self.headers,
                    json={"bizId": "tree", "aid": aid}
                )
                receive_brand_specials_data = receive_brand_specials_response.json()
                self.log(f"领取品牌特惠奖励成功✅✅, {dig(receive_brand_specials_data, 'data', 'award')}g水滴💧")
                await asyncio.sleep(1)
        else:
            self.log(f"领取品牌特惠奖励请求异常❌, {receive_brand_specials_response.status_code}")
    
    async def get_tree_planting_progress(self):
        """
        获取许愿树的进度
        :return: 
        """
        get_tree_planting_progress_response = await self.client.get(
            url=_DW_API_HOST + "/hacking-tree/v1/tree/get_tree_info",
            headers=self.headers
        )
        if get_tree_planting_progress_response.status_code == 200:
            get_tree_planting_progress_data = get_tree_planting_progress_response.json()
            if get_tree_planting_progress_data.get("code") != 200:
                self.log(f"获取许愿树进度失败❌, {get_tree_planting_progress_data}")
                return
            self.tree_id = dig(get_tree_planting_progress_data, "data", "treeId")
            level = dig(get_tree_planting_progress_data, "data", "level")
            current_level_need_watering_droplet = dig(get_tree_planting_progress_data, "data", "currentLevelNeedWateringDroplet")
            user_watering_droplet = dig(get_tree_planting_progress_data, 'data', 'userWateringDroplet')
            self.log(f"当前许愿树等级：{level}级{user_watering_droplet}/{current_level_need_watering_droplet}")
        else:
            self.log(f"获取许愿树进度请求异常❌, {get_tree_planting_progress_response.status_code}")
    
    async def waterting(self):
        """
        浇水
        :return: 
        """
        if self.is_team_tree:
            return await self.team_waterting()
        waterting_response = await self.client.post(
            url=_DW_API_HOST + "/hacking-tree/v1/tree/watering",
            headers=self.headers
        )
        if waterting_response.status_code == 200:
            waterting_data = waterting_response.json()
            if waterting_data.get("code") != 200:
                self.log(f"浇水失败❌, {waterting_data}")
                return False
            self.log(f"浇水成功✅✅")
            if dig(waterting_data, "data", "nextWateringTimes") == 0:
                self.log(f"开始领取浇水奖励")
                await asyncio.sleep(1)
                await self.receive_watering_reward()
            return True
        else:
            self.log(f"浇水发生异常❌, {waterting_response.status_code}")
            return False
    
    async def team_waterting(self):
        waterting_response = await self.client.post(
            url=_DW_API_HOST + "/hacking-tree/v1/team/tree/watering",
            headers=self.headers,
            json={
                "teamTreeId": self.tree_id
            }
        )
        if waterting_response.status_code == 200:
            team_waterting_data = waterting_response.json()
            if team_waterting_data.get("code") != 200:
                self.log(f"浇水失败❌, {team_waterting_data}")
                return False
            self.log(f"浇水成功✅✅，成功浇水{self.waterting_g}g")
            if dig(team_waterting_data, "data", "nextWateringTimes") == 0:
                self.log(f"开始领取浇水奖励")
                await asyncio.sleep(1)
                await self.receive_watering_reward()
            return True
        else:
            self.log(f"浇水发生异常❌, {waterting_response.status_code}")
    
    async def run(self):
        await self.get_user_info()
        name, level = await self.tree_info()
        droplet_number = await self.get_droplet_number()
        if not (name and level and droplet_number >= 0):
            log.log("请求数据异常！")
            return
        self.log(f"当前水滴数：{droplet_number}")
        await self.determine_whether_is_team_tree()
        await self.get_tree_planting_progress()
        # if HELP_SIGNAL:
        #     self.log(f"开始获取助力码")
        #     share_code_list.append(await self.get_share_code())
        task_list = [
            self.droplet_sign_in(),
            self.receive_droplet_extra(),
            self.execute_task(),
            self.execute_cumulative_task(),
            self.judging_bucket_droplet(),
            self.execute_receive_watering_reward(),
            # self.waterting_droplet_extra(),
            self.receive_hybrid_online_reward(),
            self.receive_air_drop(),
            self.receive_free_droplet(),
            self.droplet_invest(),
            self.click_product(),
            # self.receive_brand_specials(),
            # self.help_user(),
            self.receive_help_reward(),
            self.execute_weekend_task(),
            self.receive_level_reward(),
            self.waterting_until_less_than()
        ]
        for _t in task_list:  # [限流改造] 串行执行，避免并发触发485限流 (2026-09-22)
            await _t
        await self.get_tree_planting_progress()
        self.log_summary()  # 末尾分级汇总 (2026-09-23)


async def main():
    task = []
    _n = len(dw_x_auth_tokens)
    for index in range(_n):
        dw = DeWu(
            dw_x_auth_tokens[index], index,
            dw_sks[index] if index < len(dw_sks) else "",
            duToken=dw_duTokens[index] if index < len(dw_duTokens) else "",
            cookieToken=dw_cookieTokens[index] if index < len(dw_cookieTokens) else "",
            cookie=dw_Cookies[index] if index < len(dw_Cookies) else "",
            dudeliveryid=dw_dudeliveryids[index] if index < len(dw_dudeliveryids) else "",
            duproductid=dw_duproductids[index] if index < len(dw_duproductids) else "",
        )
        task.append(dw.run())
    await asyncio.gather(*task)


if __name__ == '__main__':
    asyncio.run(main())
    send_notification_message_collection("得物森林通知 - {}".format(datetime.now().strftime("%Y/%m/%d")))
