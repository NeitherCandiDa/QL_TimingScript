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


class AiPm:
    def __init__(self, cookie):
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
            'Accept': "application/json, text/plain, */*",
            'Accept-Language': "zh-CN,zh;q=0.9",
            'Cache-Control': "no-store",
            'Content-Length': "0",
            'New-API-User': "255",
            'Origin': "https://emtf.aipm9527.online",
            'Referer': "https://emtf.aipm9527.online/console/personal",
            'Sec-Fetch-Dest': "empty",
            'Sec-Fetch-Mode': "cors",
            'Sec-Fetch-Site': "same-origin",
            'sec-ch-ua': "\"Not:A-Brand\";v=\"99\", \"Google Chrome\";v=\"145\", \"Chromium\";v=\"145\"",
            'sec-ch-ua-mobile': "?0",
            'sec-ch-ua-platform': "\"Windows\""
        }
        if cookie is None or cookie == '':
            fn_print("未获取到cookie！")
            exit(0)
        headers["Cookie"] = cookie
        self.client = httpx.Client(
            base_url="https://emtf.aipm9527.online",
            headers=headers,
            verify=False
        )
    
    def check_in(self):
        """ 签到 """
        try:
            response = self.client.post(
                "/api/user/checkin"
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    fn_print(f"{data.get('data').get('checkin_date')} - {data.get('message')}🎉")
                else:
                    fn_print(data.get("message"))
            else:
                fn_print(f"签到异常！{response.text}")
        except Exception as e:
            fn_print(f"❌签到出现错误，{e}")


if __name__ == '__main__':
    for cookie in AIPM_COOKIES:
        AiPm(cookie).check_in()
    send_notification_message_collection("AIPM签到通知 - " + datetime.now().strftime("%Y/%m/%d"))
