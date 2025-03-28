# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         tclx.py
# @author           Echo
# @EditTime         2025/3/14
# cron: 0 0 9 * * *
# const $ = new Env('同程旅游');
"""
开启抓包，进入app 进入‘领福利’界面，点击签到，查看https://app.17u.cn/welfarecenter/index/signIndex请求头
提取变量： apptoken、device
变量格式： phone#apptoken#device，多个账号用@隔开
"""
import asyncio
import time
from datetime import datetime

import httpx

from fn_print import fn_print
from get_env import get_env
from sendNotify import send_notification_message_collection

tc_cookies = get_env("tc_cookie", "@")


class Tclx:
    def __init__(self, cookie):
        self.client = httpx.AsyncClient(base_url="https://app.17u.cn/welfarecenter",
                                        verify=False,
                                        timeout=60)
        self.phone = cookie.split("#")[0]
        self.apptoken = cookie.split("#")[1]
        self.device = cookie.split("#")[2]
        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'phone': self.phone,
            'channel': '1',
            'apptoken': self.apptoken,
            'sec-fetch-site': 'same-site',
            'accept-language': 'zh-CN,zh-Hans;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'sec-fetch-mode': 'cors',
            'origin': 'https://m.17u.cn',
            'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 TcTravel/11.0.0 tctype/wk',
            'referer': 'https://m.17u.cn/',
            # 'content-length': str(len(payload_str.encode('utf-8'))),
            'device': self.device,
            'sec-fetch-dest': 'empty'
        }

    @staticmethod
    async def get_today_date():
        return datetime.now().strftime('%Y-%m-%d')

    async def sign_in(self):
        try:
            response = await self.client.post(
                url="/index/signIndex",
                headers=self.headers,
                json={}
            )
            data = response.json()
            if data['code'] != 2200:
                fn_print(f"用户【{self.phone}】 - token失效了，请更新")
                return None
            else:
                today_sign = data['data']['todaySign']
                mileage = data['data']['mileageBalance']['mileage']
                fn_print(f"用户【{self.phone}】 - 今日{'已' if today_sign else '未'}签到，当前剩余里程{mileage}！")
                return today_sign
        except Exception as e:
            fn_print(f"用户【{self.phone}】 - 签到请求异常！{e}")
            fn_print(response.text)
            return None

    async def do_sign_in(self):
        today_date = await self.get_today_date()
        try:
            response = await self.client.post(
                url="/index/sign",
                headers=self.headers,
                json={"type": 1, "day": today_date}
            )
            data = response.json()
            if data['code'] != 2200:
                fn_print(f"用户【{self.phone}】 - 签到失败了，尝试获取任务列表")
                return False
            else:
                fn_print(f"用户【{self.phone}】 - 签到成功！开始获取任务列表")
                return True
        except Exception as e:
            fn_print(f"用户【{self.phone}】 - 执行签到请求异常！{e}")
            fn_print(response.text)
            return False

    async def get_task_list(self):
        try:
            response = await self.client.post(
                url="/task/taskList?version=11.0.7",
                headers=self.headers,
                json={}
            )
            data = response.json()
            if data['code'] != 2200:
                fn_print(f"用户【{self.phone}】 - 获取任务列表失败了")
                return None
            else:
                tasks = []
                for task in data['data']:
                    if task['state'] == 1 and task['browserTime'] != 0:
                        tasks.append(
                            {
                                'taskCode': task['taskCode'],
                                'title': task['title'],
                                'browserTime': task['browserTime']
                            }
                        )
                return tasks
        except Exception as e:
            fn_print(f"用户【{self.phone}】 - 获取任务列表请求异常！{e}")
            fn_print(response.text)
            return None

    async def perform_tasks(self, task_code):
        try:
            response = await self.client.post(
                url="/task/start",
                headers=self.headers,
                json={"taskCode": task_code}
            )
            data = response.json()
            if data['code'] != 2200:
                fn_print(f"用户【{self.phone}】 - 执行任务【{task_code}】失败了，跳过当前任务")
                return None
            else:
                task_id = data['data']
                return task_id
        except Exception as e:
            fn_print(f"用户【{self.phone}】 - 执行任务【{task_code}】请求异常！{e}")
            fn_print(response.text)
            return None

    async def finsh_task(self, task_id):
        max_retry = 3  # 最大重试次数
        retry_delay = 2  # 重试间隔时间（秒）
        for attempt in range(max_retry):
            try:
                response = await self.client.post(
                    url="/task/finish",
                    headers=self.headers,
                    json={"id": task_id}
                )
                data = response.json()
                if data['code'] == 2200:
                    fn_print(f"用户【{self.phone}】 - 完成任务【{task_id}】成功！开始领取奖励")
                    return True
                if attempt < max_retry - 1:
                    fn_print(f"用户【{self.phone}】 - 完成任务【{task_id}】失败了，尝试重新提交（第{attempt + 1}次重试。。）")
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                fn_print(f"用户【{self.phone}】 - 完成任务【{task_id}】最终失败，跳过当前任务")
                return False
            except Exception as e:
                error_msg = f"用户【{self.phone}】 - 完成任务【{task_id}】请求异常！{e}"
                if 'response' in locals():
                    error_msg += f"\n{response.text}"
                fn_print(error_msg)
                if attempt == max_retry - 1:
                    return False
                await asyncio.sleep(retry_delay * (attempt + 1))

    async def receive_reward(self, task_id):
        try:
            response = await self.client.post(
                url="/task/receive",
                headers=self.headers,
                json={"id": task_id}
            )
            data = response.json()
            if data['code'] != 2200:
                fn_print(f"用户【{self.phone}】 - 领取签到奖励失败了， 请尝试手动领取")
            else:
                fn_print(f"用户【{self.phone}】 - 领取签到奖励成功！开始下一个任务")
        except Exception as e:
            fn_print(f"用户【{self.phone}】 - 领取签到奖励请求异常！{e}")
            fn_print(response.text)

    async def get_mileage_info(self):
        try:
            response = await self.client.post(
                url="/index/signIndex",
                headers=self.headers,
                json={}
            )
            data = response.json()
            if data['code'] != 2200:
                fn_print(f"用户【{self.phone}】 - 获取积分信息失败了")
                return None
            else:
                cycle_sign_num = data['data']['cycleSighNum']
                continuous_history = data['data']['continuousHistory']
                mileage = data['data']['mileageBalance']['mileage']
                today_mileage = data['data']['mileageBalance']['todayMileage']
                fn_print(
                    f"用户【{self.phone}】 - 本月签到{cycle_sign_num}天，连续签到{continuous_history}天，今日共获取{today_mileage}里程，当前剩余里程{mileage}")
        except Exception as e:
            fn_print(f"用户【{self.phone}】 - 获取积分信息请求异常！{e}")
            fn_print(response.text)
            return None

    async def run(self):
        today_sign = await self.sign_in()
        if today_sign is None:
            return
        if today_sign:
            fn_print(f"用户【{self.phone}】 - 今日已签到，开始获取任务列表")
        else:
            if await self.do_sign_in():
                fn_print(f"用户【{self.phone}】 - 签到成功，开始获取任务列表")
        tasks = await self.get_task_list()
        if tasks:
            for task in tasks:
                task_code = task['taskCode']
                title = task['title']
                browser_time = task['browserTime']
                fn_print(f"用户【{self.phone}】 - 开始做任务【{title}】，需要浏览{browser_time}秒")
                task_id = await self.perform_tasks(task_code)
                if task_id:
                    await asyncio.sleep(browser_time)
                    if await self.finsh_task(task_id):
                        await self.receive_reward(task_id)
        await self.get_mileage_info()


async def main():
    tasks = []
    for cookie in tc_cookies:
        tclx = Tclx(cookie)
        tasks.append(tclx.run())
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())
    send_notification_message_collection(f"同程旅行签到通知 - {datetime.now().strftime('%Y/%m/%d')}")
