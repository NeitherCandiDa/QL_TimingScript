# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         hello_signIn.py
# @author           Echo
# @EditTime         2024/9/23
# cron: 0 10 * * *
# const $ = new Env('哈啰出行);
"""
开启抓包进入app
进入签到页面，抓https://api.hellobike.com/api?user.taurus.pointInfo,请求体中的token
填入环境变量hl_token中，多个token用@分隔
"""
import asyncio
from datetime import datetime

import httpx

import log
from get_env import get_env
from sendNotify import send_notification_message_collection

hl_tokens = get_env("hl_token", "@")


class HelloSignIn:

    def __init__(self, token):
        self.token = token
        self.client = httpx.AsyncClient(base_url="https://api.hellobike.com", verify=False)

    async def sign_in(self):
        """签到"""
        response = await self.client.post(
            url=f'/api?common.welfare.signAndRecommend',
            json={
                "from": "h5",
                "systemCode": 62,
                "platform": 4,
                "version": "6.72.1",
                "action": "common.welfare.signAndRecommend",
                "token": self.token
            }
        )
        return self._process_response(response, "签到")

    async def point_info(self):
        """查询账户所有金币"""
        response = await self.client.post(
            url=f"/api?user.taurus.pointInfo",
            json={
                "from": "h5",
                "systemCode": 62,
                "platform": 4,
                "version": "6.72.1",
                "action": "user.taurus.pointInfo",
                "token": self.token,
                "pointType": 1
            }
        )
        return self._process_response(response, "查询金币")

    def _process_response(self, response, action_type):
        try:
            data = response.json()
            if data.get("code") == 0:
                if action_type == "签到":
                    if data["data"]["didSignToday"]:
                        log.log(f"账户今日已签到， 金币🪙+{data['data']['bountyCountToday']}")
                        return 
                    log.log("今日未签到, 检查token是否已过期")
                    return 
                elif action_type == "查询金币":
                    log.log(f"账户可用金币🪙：{data['data']['points']}, 可抵扣{data['data']['amount']}元")
                    return 
            log.log(f"无法{action_type}, 检查token是否已过期")
            return 
        except Exception as e:
            log.log(f"{action_type}失败: {str(e)}")
            return 

    async def run(self):
        await self.sign_in()
        await self.point_info()        


if __name__ == '__main__':
    for token in hl_tokens:
        asyncio.run(HelloSignIn(token).run())
    send_notification_message_collection(f"哈啰出行-签到通知 - {datetime.now().strftime('%Y/%m/%d')}")
