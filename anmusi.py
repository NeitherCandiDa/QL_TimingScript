# -*- coding=UTF-8 -*-
# @Project          sfsy.py
# @fileName         anmusi.py
# @author           Echo
# @EditTime         2025/5/6
# cron: 0 10 * * *
# const $ = new Env('安慕希');
"""
开启抓包，进入小程序
抓取请求头中的access-token，填入环境变量amx_token中，多个token用&分隔
"""
from datetime import datetime

import httpx

from fn_print import fn_print
from get_env import get_env
from sendNotify import send_notification_message_collection

amx_tokens = get_env("amx_token", '&')


class Anmusi:
    def __init__(self, amx_token):
        self.nick_name = None
        self.amx_token = amx_token
        self.client = httpx.Client(
            base_url="https://msmarket.msx.digitalyili.com",
            verify=False, timeout=60,
            headers={
                "access-token": self.amx_token,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090c33)XWEB/11581",
                "Content-Type": "application/json"
            }
        )

    def get_user_info(self):
        try:
            response = self.client.get("/gateway/api/auth/account/user/info")
            response.raise_for_status()
            user_info = response.json()
            if user_info.get('status'):
                self.nick_name = user_info.get("data").get("nickName")
            else:
                fn_print(f"获取用户信息失败！{user_info.get('error').get("msg")}")
        except Exception as e:
            fn_print("获取用户信息异常❌\n", e)

    def get_sign_in_status(self):
        try:
            response = self.client.get("/gateway/api/member/sign/status")
            response.raise_for_status()
            sign_in_status = response.json()
            if not sign_in_status.get('status'):
                fn_print(f"获取签到状态失败！{sign_in_status.get('data').get("error")}")
                return
            if sign_in_status.get("data").get("signed"):
                fn_print(f"**用户: {self.nick_name}**, 今日已签到！")
                return
            self.sign_in()
        except Exception as e:
            fn_print("获取签到状态异常❌\n", e)

    def sign_in(self):
        try:
            response = self.client.post("/gateway/api/member/daily/sign")
            response.raise_for_status()
            sign_in_status = response.json()
            if sign_in_status.get("status"):
                fn_print(f"**用户: {self.nick_name}**, 签到成功！✅")
            else:
                fn_print(f"签到失败！{sign_in_status.get('data').get("error")}")
        except Exception as e:
            fn_print("签到异常❌\n", e)

    def get_points(self):
        try:
            response = self.client.get("/gateway/api/member/point")
            response.raise_for_status()
            points_info = response.json()
            if points_info.get("status"):
                points = points_info.get("data")
                fn_print(f"**用户: {self.nick_name}**, 当前积分: {points}")
            else:
                fn_print(f"获取积分失败！{points_info.get('data').get("error")}")
        except Exception as e:
            fn_print("获取积分异常❌\n", e)

    def run(self):
        self.get_user_info()
        self.get_sign_in_status()
        self.get_points()


if __name__ == "__main__":
    for amx_token in amx_tokens:
        anmusi = Anmusi(amx_token)
        anmusi.run()
    send_notification_message_collection(f"安慕希签到通知 - {datetime.now().strftime('%Y-%m-%d')}")
