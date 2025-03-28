# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         pzSignIn.py
# @author           Echo
# @EditTime         2024/9/13
# const $ = new Env('品赞代理签到');
# cron: 0 0 9 * * 1
import os
import re
from datetime import datetime

import httpx

from fn_print import fn_print
from get_env import get_env
from sendNotify import send_notification_message_collection

pz_account = get_env("pz_account", "@")


class PzSignIn:
    def __init__(self, account):
        self.client = httpx.Client(base_url="https://service.ipzan.com", verify=False)
        self.get_token(account)

    def get_token(self, account):
        try:
            response = self.client.post(
                '/users-login',
                json={
                    "account": account,
                    "source": "ipzan-home-one"
                }
            )
            response_json = response.json()
        except Exception as e:
            fn_print(e)
            fn_print(response.text)
        token = response_json["data"]['token']
        if token is not None:
            fn_print("=" * 30 + f"登录成功，开始执行签到" + "=" * 30)
            self.client.headers["Authorization"] = "Bearer " + token
        else:
            fn_print("登录失败")
            exit()

    def get_balance(self):
        """
        获取品赞余额
        :return: 
        """
        response = self.client.get(
            "/home/userWallet-find"
        ).json()
        return str(response["data"]["balance"])

    def sign_in(self):
        """
        品赞签到
        :return: 
        """
        response = self.client.get(
            "/home/userWallet-receive"
        ).json()
        if response["status"] == 200 and response['data'] == '领取成功':
            fn_print("签到成功")
            fn_print("=" * 100)
            balance = self.get_balance()
            fn_print("当前账户余额： " + balance)
        elif response["code"] == -1:
            balance = self.get_balance()
            fn_print(response["message"])
            fn_print(f"签到失败，{response['message']}\n当前账户余额：{balance}")
        else:
            fn_print("签到失败！")
            fn_print(response) 


if __name__ == '__main__':
    for i in pz_account:
        pz = PzSignIn(i)
        pz.sign_in()
        del pz
    send_notification_message_collection("品赞代理签到通知 - " + datetime.now().strftime("%Y/%m/%d"))
