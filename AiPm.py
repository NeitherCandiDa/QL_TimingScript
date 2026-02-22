# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         AiPm.py
# @author           Leon
# @EditTime         2026/2/22
# const $ = new Env('AIPM中转站');
# cron: 0 0 12 * * *
import httpx
from fn_print import fn_print
from get_env import get_env
from datetime import datetime
from sendNotify import send_notification_message_collection

AIPM_COOKIES = get_env("aipm_cookies", "@")

BASE_URL = "https://emtf.aipm9527.online"
DEFAULT_HEADERS = {
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    'Accept': "application/json, text/plain, */*",
    'Accept-Language': "zh-CN,zh;q=0.9",
    'Cache-Control': "no-store",
    'Content-Length': "0",
    'Origin': "https://emtf.aipm9527.online",
    'Referer': "https://emtf.aipm9527.online/console/personal",
    'Sec-Fetch-Dest': "empty",
    'Sec-Fetch-Mode': "cors",
    'Sec-Fetch-Site': "same-origin",
    'sec-ch-ua': "\"Not:A-Brand\";v=\"99\", \"Google Chrome\";v=\"145\", \"Chromium\";v=\"145\"",
    'sec-ch-ua-mobile': "?0",
    'sec-ch-ua-platform': "\"Windows\""
}


class AiPm:
    def __init__(self, account):
        cookie, user_id = self._parse_account(account)
        if not user_id:
            fn_print("未配置用户ID！")
            self.client = None
            return
        if not cookie:
            fn_print("未获取到cookie！")
            self.client = None
            return
        headers = {
            **DEFAULT_HEADERS,
            "Cookie": cookie,
            "New-API-User": user_id
        }
        self.client = httpx.Client(
            base_url=BASE_URL,
            headers=headers,
            verify=False
        )

    @staticmethod
    def _parse_account(account):
        parts = account.split("#", 1)
        cookie = parts[0] if parts else ""
        user_id = parts[1] if len(parts) > 1 else ""
        return cookie, user_id

    def check_in(self):
        """ 签到 """
        if self.client is None:
            return
        try:
            response = self.client.post(
                "/api/user/checkin"
            )
            if response.status_code == 200:
                try:
                    data = response.json()
                except ValueError as e:
                    fn_print(f"❌签到解析失败，{e}")
                    return
                if data.get("success"):
                    fn_print(f"{data.get('data').get('checkin_date')} - {data.get('message')}🎉")
                else:
                    fn_print(data.get("message"))
            else:
                fn_print(f"签到异常！{response.text}")
        except httpx.RequestError as e:
            fn_print(f"❌签到请求失败，{e}")
        except Exception as e:
            fn_print(f"❌签到出现错误，{e}")
        finally:
            self.client.close()


if __name__ == '__main__':
    for acc in AIPM_COOKIES:
        AiPm(acc).check_in()
    send_notification_message_collection("AIPM签到通知 - " + datetime.now().strftime("%Y/%m/%d"))
