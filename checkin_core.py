# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         checkin_core.py
# @author           Leon
# @EditTime         2026/3/12
# 通用签到核心模块 - 支持多站点签到
import httpx
from fn_print import fn_print
from get_env import get_env
from datetime import datetime
from sendNotify import send_notification_message_collection


class CheckInClient:
    """通用签到客户端"""

    def __init__(self, account, base_url, origin, referer):
        """
        初始化签到客户端

        Args:
            account: 账户信息，格式为 "cookie#user_id"
            base_url: API基础URL
            origin: Origin请求头
            referer: Referer请求头
        """
        cookie, user_id = self._parse_account(account)
        self.user_name = ""
        self.quota = None
        self.base_url = base_url

        if not user_id:
            fn_print("未配置用户ID！")
            self.client = None
            return
        if not cookie:
            fn_print("未获取到cookie！")
            self.client = None
            return

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-store",
            "Content-Length": "0",
            "Origin": origin,
            "Referer": referer,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Cookie": cookie,
            "New-API-User": user_id,
        }
        self.client = httpx.Client(base_url=base_url, headers=headers, verify=False)

    @staticmethod
    def _parse_account(account):
        """解析账户信息"""
        parts = account.split("#", 1)
        cookie = parts[0] if parts else ""
        user_id = parts[1] if len(parts) > 1 else ""
        return cookie, user_id

    def check_in(self):
        """执行签到"""
        if self.client is None:
            return
        try:
            response = self.client.post("/api/user/checkin")
            if response.status_code == 200:
                data = self._parse_json(response, "签到")
                if data is None:
                    return
                if data.get("success"):
                    fn_print(
                        f"{self.user_name} - {data.get('data').get('checkin_date')} - {data.get('message')}🎉，获得💲{data.get('quota_awarded') / 500000}"
                    )
                else:
                    fn_print(f"{self.user_name} - " + data.get("message"))
            else:
                fn_print(f"{self.user_name} - 签到异常！{response.text}")
        except httpx.RequestError as e:
            fn_print(f"{self.user_name} - ❌签到请求失败，{e}")
        except Exception as e:
            fn_print(f"{self.user_name} - ❌签到出现错误，{e}")
        finally:
            self.get_user_info()
            user_name = self.user_name or "未知用户"
            quota = self.quota or "未知"
            fn_print(f"用户：{user_name} | 当前余额：💲{quota}")
            self.client.close()

    def get_user_info(self):
        """获取用户信息"""
        if self.client is None:
            return
        try:
            response = self.client.get("/api/user/self")
            if response.status_code == 200:
                data = self._parse_json(response, "获取用户信息")
                if data is None:
                    return
                if data.get("success"):
                    self.user_name = data.get("data").get("username")
                    quota_value = data.get("data", {}).get("quota")
                    if isinstance(quota_value, (int, float)):
                        dollars = quota_value / 500000
                        self.quota = f"{dollars:.2f}"
                    else:
                        self.quota = None
                else:
                    fn_print(data)
        except httpx.RequestError as e:
            fn_print(f"❌获取用户信息请求失败，{e}")
        except Exception as e:
            fn_print(f"❌获取用户信息出现错误，{e}")

    @staticmethod
    def _parse_json(response, scene):
        """解析JSON响应"""
        try:
            return response.json()
        except ValueError as e:
            fn_print(f"❌{scene}解析失败，{e}")
            return None


def run_checkin(env_name, base_url, origin, referer, notify_title):
    """
    执行签到任务

    Args:
        env_name: 环境变量名称
        base_url: API基础URL
        origin: Origin请求头
        referer: Referer请求头
        notify_title: 通知标题
    """
    accounts = get_env(env_name, "@")
    for acc in accounts:
        CheckInClient(acc, base_url, origin, referer).check_in()
    send_notification_message_collection(
        f"{notify_title}签到通知 - " + datetime.now().strftime("%Y/%m/%d")
    )


# 站点配置
SITES = {
    "aipm": {
        "env_name": "aipm_cookies",
        "base_url": "https://emtf.aipm9527.online",
        "origin": "https://emtf.aipm9527.online",
        "referer": "https://emtf.aipm9527.online/console/personal",
        "notify_title": "AIPM",
    },
    "zapi": {
        "env_name": "zapi_cookies",
        "base_url": "https://zapi.aicc0.com",
        "origin": "https://zapi.aicc0.com",
        "referer": "https://zapi.aicc0.com/console/personal",
        "notify_title": "Z-API",
    },
}


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        site_key = sys.argv[1].lower()
        if site_key in SITES:
            config = SITES[site_key]
            run_checkin(
                config["env_name"],
                config["base_url"],
                config["origin"],
                config["referer"],
                config["notify_title"],
            )
        else:
            fn_print(f"未知站点: {site_key}，可用站点: {list(SITES.keys())}")
    else:
        fn_print("用法: python checkin_core.py <site_key>")
        fn_print(f"可用站点: {list(SITES.keys())}")
