# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         hello_signIn.py
# @author           Echo
# @EditTime         2024/9/23
# cron: 0 0 10 * * *
# const $ = new Env('哈啰出行);
import asyncio
import os
import re
from datetime import datetime

import httpx

from sendNotify import aysnc_send_notification_message


class HelloSignIn:
    BASE_URL = "https://api.hellobike.com/api"

    def __init__(self, token):
        self.token = token
        self.client = httpx.AsyncClient(verify=False)

    async def sign_in(self):
        """签到"""
        response = await self.client.post(
            url=f'{self.BASE_URL}?common.welfare.signAndRecommend',
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
            url=f"{self.BASE_URL}?user.taurus.pointInfo",
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
                        return f"账户今日已签到， 金币🪙+{data['data']['bountyCountToday']}"
                    return "今日未签到, 检查token是否已过期"
                elif action_type == "查询金币":
                    return f"账户可用金币🪙：{data['data']['points']}, 可抵扣{data['data']['amount']}元"
            return f"无法{action_type}, 检查token是否已过期"
        except Exception as e:
            return f"{action_type}失败: {str(e)}"

    async def run(self):
        sign_result = await self.sign_in()
        point_result = await self.point_info()
        message = f"{sign_result}\n{point_result}"
        print(message)
        await aysnc_send_notification_message(f"哈啰出行-签到通知 - {datetime.now().strftime('%Y/%m/%d')}", message)
        await self.client.aclose()


async def main():
    if 'hl_token' in os.environ:
        tokens = re.split("@|&", os.environ.get("hl_token"))
        print(f"查找到{len(tokens)}个账号")
        tasks = [HelloSignIn(token).run() for token in tokens]
        await asyncio.gather(*tasks)
    else:
        print("未查找到hl_token变量.")


if __name__ == '__main__':
    asyncio.run(main())