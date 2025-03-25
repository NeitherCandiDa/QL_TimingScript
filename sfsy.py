# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         sfsy.py
# @author           Echo
# @EditTime         2025/3/19
# cron: 0 10,15,18 * * *
# const $ = new Env("顺丰速运");
"""
开启抓包，小程序-我的-积分
抓 https://mcs-mimp-web.sf-express.com/mcs-mimp/share/weChat/activityRedirect?source=xxxxxxxxxxxx
将整个url地址填入变量sfsy_url

    本脚本收集来自https://github.com/arvinsblog/deepsea
"""
import asyncio
import hashlib
import json
import random
import time
from datetime import datetime

import httpx
from fn_print import fn_print
from get_env import get_env
from sendNotify import send_notification_message_collection

sfsy_tokens = get_env("sfsy_url", "\n")

inviteId = [
    '7B0443273B2249CB9CDB7B48B94DEC13', '809FAF1E02D045D7A0DB185E5C91CFB1', '',
    '', '']


class Sfsy:
    def __init__(self, url_info: str, index):
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.user = None
        self.send_uid = None
        self.anniversary_black = False
        self.member_day_black = False
        self.member_day_red_packet_drew_today = False
        self.member_day_red_packet_map = {}
        self.answer = False
        self.max_level = 8
        self.packet_threshold = 1 << (self.max_level - 1)
        self.client = httpx.AsyncClient(
            verify=False,
            timeout=60
        )
        url_info_list = url_info.split("@")
        url_info_list_len = len(url_info_list)
        self.url = url_info_list[0]
        last_url_info = url_info_list[url_info_list_len - 1]
        if url_info_list_len > 0 and "UID_" in last_url_info:
            self.send_uid = last_url_info
        self.index = index + 1
        self.headers = {
            'Host': 'mcs-mimp-web.sf-express.com',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090551) XWEB/6945 Flue',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'accept-language': 'zh-CN,zh',
            'platform': 'MINI_PROGRAM',
        }
        self.get_sign()

    async def generate_device_id(self, characters='abcdef0123456789'):
        template = 'xxxxxxxx-xxxx-xxxx'
        return ''.join(
            random.choice(characters) if c == 'x' else
            random.choice(characters).upper() if c == 'X' else
            c
            for c in template
        )

    async def login(self):
        await self.client.get(self.url, headers=self.headers)
        self.user_id = self.client.cookies.get("_login_user_id_", "")
        self.phone = self.client.cookies.get("_login_mobile_", "")
        self.mobile = self.phone[:3] + "*" * 4 + self.phone[7:]
        if self.phone != "":
            fn_print(f"用户【{self.phone}】 -  登录成功！✔️")
            return True
        else:
            fn_print(f"用户【{self.phone}】 -  登录失败！❌")
            return False

    def get_sign(self):
        timestamp = str(int(round(time.time() * 1000)))
        token = 'wwesldfs29aniversaryvdld29'
        sysCode = 'MCS-MIMP-CORE'
        data = f'token={token}&timestamp={timestamp}&sysCode={sysCode}'
        signature = hashlib.md5(data.encode()).hexdigest()
        data = {
            'sysCode': sysCode,
            'timestamp': timestamp,
            'signature': signature
        }
        self.headers.update(data)
        return data

    async def sign_in(self):
        """
        签到
        :return: 
        """
        fn_print(">>> 开始签到...")
        response = await self.client.post(
            url='https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~integralTaskSignPlusService~automaticSignFetchPackage',
            headers=self.headers,
            json={
                "comeFrom": "vioin",
                "channelFrom": "WEIXIN"
            }
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                days = data.get("obj", {}).get("ountDay", 0)
                if data.get("obj") and data.get("obj").get("integralTaskSignPackageVOList"):
                    reward_name = data["obj"]["integralTaskSignPackageVOList"][0]["packetName"]
                    fn_print(f">>> 用户【{self.phone}】 -  签到成功！✔️ - 获得【{reward_name}】， 本周累计签到{days}天")
                else:
                    fn_print(f">>> 用户【{self.phone}】 -  今日已签到！✖️ - 本周累计签到{days + 1}天")
            else:
                fn_print(f">>> 用户【{self.phone}】 -  签到失败！❌ - {data.get('errorMessage')}")
        else:
            fn_print(">>> 用户【{self.phone}】 -  签到异常！‼️")

    async def super_welfare_benefit_sign_in(self):
        """
        超值福利签到
        :return: 
        """
        fn_print(">>> 超值福利签到...")
        try:
            response = await self.client.post(
                url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberActLengthy~redPacketActivityService~superWelfare~receiveRedPacket",
                headers=self.headers,
                json={'channel': 'czflqflqdlhbxcx'}
            )
            data = response.json()
            if data.get("success"):
                gift_list = data.get("obj", {}).get("giftList", [])
                if gift_list is None:
                    gift_list = []
                if data.get("obj", {}).get("extraGiftList", []):
                    extra_gift_list = data.get("obj", {}).get("extraGiftList", [])
                    if extra_gift_list is not None:
                        gift_list.extend(extra_gift_list)
                gift_name = ",".join([gift["giftName"] for gift in gift_list])
                receive_status = data.get("obj", {}).get("receiveStatus")
                status_msg = "领取成功" if receive_status == 1 else "已经领取过"
                fn_print(f">>> 用户【{self.phone}】 -  超值福利签到成功！✔️ - {status_msg} - 【{gift_name}】")
            else:
                error_message = data.get('errorMessage') or json.dumps(data) or '无返回'
                fn_print(f">>> 用户【{self.phone}】 -  超值福利签到失败！❌ - {error_message}")
        except Exception as e:
            fn_print(f">>> 用户【{self.phone}】 -  签到异常！‼️ - {e}")

    async def get_task_list(self, flag=False):
        """
        获取任务列表
        :param flag: 
        :return: 
        """
        if not flag: fn_print(">>> 获取任务列表...")
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~integralTaskStrategyService~queryPointTaskAndSignFromES",
            headers=self.headers,
            json={
                'channelType': '1',
                'deviceId': await self.generate_device_id()
            }
        )
        data = response.json()
        if data.get("success") and data.get("obj") != []:
            total_point = data.get("obj").get("totalPoint")
            if flag:
                fn_print(f">>> 用户【{self.phone}】 -  当前积分：{total_point}")
            return data["obj"]["taskTitleLevels"]

    async def do_task(self):
        """
        完成任务
        :return:
        """
        fn_print(f">>> 用户【{self.phone}】 -  前往完成【{self.title}】任务...")
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonRoutePost/memberEs/taskRecord/finishTask",
            headers=self.headers,
            json={'taskCode': self.task_code}
        )
        data = response.json()
        if data.get("success"):
            fn_print(f">>> 用户【{self.phone}】 -  任务【{self.title}】完成成功！✅")
        else:
            fn_print(f">>> 用户【{self.phone}】 -  任务【{self.title}】完成失败！❌ - {data.get('errorMessage')}")

    async def receive_task(self):
        """
        领取任务奖励
        :return:
        """
        fn_print(f">>> 用户【{self.phone}】 -  前往领取{self.title}任务奖励...")
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~integralTaskStrategyService~fetchIntegral",
            headers=self.headers,
            json={
                "strategyId": self.strategy_id,
                "taskId": self.task_id,
                "taskCode": self.task_code,
                "deviceId": await self.generate_device_id()
            }
        )
        data = response.json()
        if data.get("success"):
            fn_print(f">>> 用户【{self.phone}】 -  任务【{self.title}】奖励领取成功！✅")
        else:
            fn_print(f">>> 用户【{self.phone}】 -  任务【{self.title}】奖励领取失败！❌ - {data.get('errorMessage')}")

    async def processe_tasks(self):
        tasks = await self.get_task_list()
        for task in tasks:
            self.task_id = task["taskId"]
            self.task_code = task["taskCode"]
            self.strategy_id = task["strategyId"]
            self.title = task["title"]
            status = task["status"]
            skip_keys = ['用行业模板寄件下单', '去新增一个收件偏好', '参与积分活动']
            if status == 3:
                fn_print(f">>> 用户【{self.phone}】 -  任务【{self.title}】 - 已完成！✅")
                continue
            if self.title in skip_keys:
                fn_print(f">>> 用户【{self.phone}】 -  任务【{self.title}】 - 已跳过！♻️")
                continue
            else:
                await self.do_task()
                await asyncio.sleep(3)
            await self.receive_task()

    async def do_honey_task(self):
        """
        做蜂蜜任务
        :return: 
        """
        fn_print(">>> 开始做蜂蜜任务...")
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberEs~taskRecord~finishTask",
            headers=self.headers,
            json={
                "taskCode": self.task_code
            }
        )
        data = response.json()
        if data.get("success"):
            fn_print(f">>> 用户【{self.phone}】 -  蜂蜜任务【{self.task_type}】完成成功！✅")
        else:
            fn_print(f">>> 用户【{self.phone}】 -  蜂蜜任务【{self.task_type}】完成失败！❌ - {data.get('errorMessage')}")

    async def receive_honey_task(self):
        """
        领取蜂蜜任务奖励
        :return:
        """
        fn_print(f">>> 用户【{self.phone}】 -  前往收取蜂蜜任务奖励...")
        self.headers.update(
            {
                "syscode": "MCS-MIMP-CORE",
                "channel": "wxwdsj",
                "accept": "application/json, text/plain, */*",
                "content-type": "application/json;charset=UTF-8",
                "platform": "MINI_PROGRAM"
            }
        )
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~receiveHoney",
            headers=self.headers,
            json={"taskType": self.task_type}
        )
        data = response.json()
        if data.get("success"):
            fn_print(f">>> 用户【{self.phone}】 -  收取蜂蜜任务【{self.task_type}】奖励成功！✅")
        else:
            fn_print(f">>> 用户【{self.phone}】 -  收取蜂蜜任务【{self.task_type}】奖励失败！❌ - {data.get('errorMessage')}")

    async def get_honey_task_list_and_start(self):
        """
        获取蜂蜜任务列表
        :return:
        """
        fn_print(">>> 获取采蜜换大礼包任务列表...")
        self.headers.update(
            {"channel": "wxwdsj"}
        )
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~taskDetail",
            headers=self.headers,
            json={}
        )
        data = response.json()
        if data.get("success"):
            for i in data["obj"]["list"]:
                self.task_type = i["taskType"]
                status = i["status"]
                if status == 3:
                    fn_print(f">>> 用户【{self.phone}】 -  任务【{self.task_type}】 - 已完成！✅")
                    if self.task_type == "BEES_GAME_TASK_TYPE":
                        self.bee_need_help = False
                    continue
                if "taskCode" in i:
                    self.task_code = i["taskCode"]
                    if self.task_type == "DAILY_VIP_TASK_TYPE":
                        await self.get_coupom_list()
                    else:
                        await self.do_honey_task()
                if self.task_type == "BEES_GAME_TASK_TYPE":
                    await self.honey_damaoxian()
                await asyncio.sleep(2)

    async def honey_damaoxian(self):
        """
        蜂蜜大冒险
        :return: 
        """
        fn_print(">>> 执行大冒险任务...")
        game_num = 5
        for i in range(1, game_num):
            if game_num < 0: break
            fn_print(f">> 第{i}次大冒险...")
            response = await self.client.post(
                url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeGameService~gameReport",
                headers=self.headers,
                json={
                    "gatherHoney": 20,
                }
            )
            data = response.json()
            if data.get("success"):
                game_num = data["obj"]["gameNum"]
                fn_print(f"> 大冒险成功！剩余次数：{game_num}")
                await asyncio.sleep(2)
                game_num -= 1
            elif data.get("errorMessage") == "容量不足":
                fn_print(f"> 大冒险失败！容量不足，需要扩容")
                await self.honey_expand()
            else:
                fn_print(f"> 大冒险失败！❌ - {data.get('errorMessage')}")

    async def honey_expand(self):
        """
        扩容
        :return: 
        """
        fn_print(">>> 开始扩容...")
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~expand",
            headers=self.headers,
            json={}
        )
        data = response.json()
        if data.get("success"):
            fn_print(f">>> 用户【{self.phone}】 -  成功扩容【{data.get('obj')}】！✅")
        else:
            fn_print(f">>> 用户【{self.phone}】 -  扩容失败！❌ - {data.get('errorMessage')}")

    async def get_coupom(self):
        """
        领取生活权益优惠券
        :return: 
        """
        fn_print(">>> 开始领取生活权益优惠券...")
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberGoods~pointMallService~createOrder",
            headers=self.headers,
            json={
                "from": "Point_Mall",
                "orderSource": "POINT_MALL_EXCHANGE",
                "goodsNo": self.goodsNo,
                "quantity": 1,
                "taskCode": self.task_code
            }
        )
        data = response.json()
        if data.get("success"):
            fn_print(f">>> 用户【{self.phone}】 -  领取生活权益优惠券成功！✅")
        else:
            fn_print(f">>> 用户【{self.phone}】 -  领取生活权益优惠券失败！❌ - {data.get('errorMessage')}")

    async def get_coupom_list(self):
        """
        获取生活权益优惠券列表
        :return:
        """
        fn_print(">>> 获取生活权益优惠券列表...")
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberGoods~mallGoodsLifeService~list",
            headers=self.headers,
            json={
                "memGrade": 1,
                "categoryCode": "SHTQ",
                "showCode": "SHTQWNTJ"
            }
        )
        data = response.json()
        if data.get("success"):
            goods_list = data["obj"][0]["goodsList"]
            for goods in goods_list:
                exchange_times_limit = goods["exchangeTimesLimit"]
                if exchange_times_limit >= 7:
                    self.goodsNo = goods["goodsNo"]
                    fn_print(f">> 当前选择券号： {self.goodsNo}")
                    await self.get_coupom()
                    break
        else:
            fn_print(f">>> 用户【{self.phone}】 -  获取生活权益优惠券列表失败！❌ - {data.get('errorMessage')}")

    async def honey_index_data(self, flag=False):
        if not flag: fn_print(">>> 执行采蜜换大礼包...")
        random_invite = random.choice([invite for invite in inviteId if invite != self.user_id])
        self.headers.update(
            {
                "channel": "wxwdsj"
            }
        )
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~indexData",
            headers=self.headers,
            json={
                "inviteUserId": random_invite
            }
        )
        data = response.json()
        if data.get("success"):
            usableHoney = data.get('obj').get('usableHoney')
            if flag:
                fn_print(f">>> 用户【{self.phone}】 -  当前蜂蜜：{usableHoney}")
                return
            task_detail = data.get('obj').get('taskDetail')
            activity_end_time = data.get("obj").get('activityEndTime', '')
            activity_end_time = datetime.strptime(activity_end_time, "%Y-%m-%d %H:%M:%S")
            current_time = datetime.now()
            if current_time.date() == activity_end_time.date():
                fn_print(f"本期活动今日结束❗请及时兑换")
            else:
                fn_print(f"本期活动结束时间 【{activity_end_time}】")
            if task_detail != []:
                for task in task_detail:
                    self.task_type = task["type"]
                    await self.receive_honey_task()
                    await asyncio.sleep(2)

    async def ear_end_2023_task_list(self):
        fn_print(">>> 执行周年庆任务...")
        self.headers.update(
            {
                "channel": "32annixcx",
                "platform": "MINI_PROGRAM",
                "syscode": "MCS-MIMP-CORE"
            }
        )
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~activityTaskService~taskList",
            headers=self.headers,
            json={
                "activityCode": "ANNIVERSARY_2025",
                "channelType": "MINI_PROGRAM"
            }
        )
        data = response.json()
        if data.get("success"):
            task_list = data.get("obj")
            for task in task_list:
                self.title = task["taskName"]
                self.task_type = task["taskType"]
                status = task["status"]
                if status == 3:
                    fn_print(f">>> 用户【{self.phone}】 -  任务【{self.title}】 - 已完成！✅")
                    continue
                if self.task_type == "INTEGRAL_EXCHANGE":
                    await self.ear_end_2023_exchange_card()
                elif self.task_type == "PLAY_ACTIVITY_GAME":
                    await self.dragonboat_2024_index()
                    await self.dragonboat_2024_game_init()
                elif self.task_type == "CLICK_MY_SETTING":
                    self.task_code = task["taskCode"]
                    await self.add_deliver_prefer()
                if "taskCode" in task:
                    self.task_code = task["taskCode"]
                    await self.do_task()
                    await asyncio.sleep(3)
                    await self.ear_end_2023_receive_task()
                else:
                    fn_print(f">>> 用户【{self.phone}】 -  暂不支持【{self.title}】任务❗")
        await self.ear_end_2023_get_award()

    async def add_deliver_prefer(self):
        fn_print(f">>> 开始【{self.title}】任务...")
        response = await self.client.post(
            url="https://ucmp.sf-express.com/cx-wechat-member/member/deliveryPreference/addDeliverPrefer",
            headers=self.headers,
            json={
                "country": "中国",
                "countryCode": "A000086000",
                "province": "四川省",
                "provinceCode": "A510000000",
                "city": "成都市",
                "cityCode": "A510100000",
                "county": "成华区",
                "countyCode": "A510108000",
                "address": "兴元华盛一期",
                "latitude": "30.712051069985897",
                "longitude": "104.1025074699607",
                "memberId": "",
                "locationCode": "028",
                "deptCode": "028VP",
                "aoiId": "62556EACB8E91B9DE0530EF4520A0CFC",
                "aoiType": "120302",
                "appliedAoiId": "62556EACB8E91B9DE0530EF4520A0CFC",
                "zoneCode": "CN",
                "postCode": "",
                "workdayPrefer": {
                    "noDeliverDays": [],
                    "remark": "",
                    "startDeliverTime": "",
                    "content": [
                        {
                            "timeRange": "00:00-24:00",
                            "tag": "8",
                            "storeInfo": None,
                            "location": {
                                "tag": "1",
                                "userSelect": ""
                            },
                            "deliverFlag": "True"
                        }
                    ]
                },
                "weekdendPrefer": {
                    "noDeliverDays": [],
                    "remark": "",
                    "startDeliverTime": "",
                    "content": [
                        {
                            "timeRange": "00:00-24:00",
                            "tag": "8",
                            "storeInfo": None,
                            "location": {
                                "tag": "1",
                                "userSelect": ""
                            },
                            "deliverFlag": "True"
                        }
                    ]
                },
                "takeWay": "00",
                "empCode": "",
                "channelCode": "wxapp",
                "taskId": self.task_id,
                "extJson": "{\"noDeliverDetail\":[]}"
            }
        )
        data = response.json()
        if data.get("success"):
            fn_print(f">>> 用户【{self.phone}】 -  新增一个收件偏好成功！✅")
        else:
            fn_print(f">>> 用户【{self.phone}】 -  任务【{self.title}】失败！❌ - {data.get('errorMessage')}")

    async def ear_end_2023_exchange_card(self):
        fn_print(f">>> 开始积分兑换年卡任务...")
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonNoLoginPost/~memberNonactivity~yearEnd2023TaskService~integralExchange",
            headers=self.headers,
            json={
                "exchangeNum": 2,
                "activityCode": "YEAR_END_2023",
                "channelType": "MINI_PROGRAM"
            }
        )
        data = response.json()
        if data.get("success"):
            received_account_list = data["obj"]["receivedAccountList"]
            for card in received_account_list:
                fn_print(f">>> 用户【{self.phone}】 -  兑换年卡成功！✅ - 获得【{card['urrency']}】卡【{card['amount']}】张！")
        else:
            fn_print(f">>> 用户【{self.phone}】 -  任务【{self.title}】失败！❌ - {data.get('errorMessage')}")

    async def ear_end_2023_get_award(self):
        fn_print(f">>> 开始抽取卡片...")
        for index in range(10):
            for i in range(0, 3):
                response = await self.client.post(
                    url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~anniversary2025ClaimService~claim",
                    headers=self.headers,
                    json={"cardType": i}
                )
                data = response.json()
                if data.get("success"):
                    received_account_list = data["obj"]["receivedAccountList"]
                    for card in received_account_list:
                        fn_print(
                            f">>> 用户【{self.phone}】 -  抽取卡片成功！✅ - 获得【{card['currency']}】卡【{card['amount']}】张！")
                elif data.get("errorMessage") == "用户账户余额不足":
                    fn_print(f">>> 用户【{self.phone}】 -  用户账户余额不足！❌")
                    break
                elif data.get("errorMessage") == "用户信息失效，请退出重新进入":
                    fn_print(f">>> 用户【{self.phone}】 -  用户信息失效，请退出重新进入❌")
                    break
                else:
                    fn_print(f">>> 用户【{self.phone}】 -  抽取卡片失败！❌ - {data.get('errorMessage')}")
                    break
                await asyncio.sleep(3)

    async def ear_end_2023_query(self):
        fn_print(f">>> 开始查询卡片数量...")
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~anniversary2025ClaimService~claimStatus",
            headers=self.headers,
            json={}
        )
        data = response.json()
        if data.get("success"):
            obj = data.get("obj", None)
            if obj is None: return False
            current_account_list = obj.get("currentAccountList", [])
            if not current_account_list:
                fn_print(">> 当前无卡片！")
            else:
                for card in current_account_list:
                    currency = card.get("currency")
                    total_amount = card.get("totalAmount")
                    balance = card.get("balance")
                    if currency == "DAI_BI":
                        currency_name = "坐以待币🪙"
                    elif currency == 'CHENG_GONG':
                        currency_name = '成功人士⌚'
                    elif currency == 'GAN_FAN':
                        currency_name = '干饭圣体🍚'
                    elif currency == 'DING_ZHU':
                        currency_name = '都顶得住🦾'
                    elif currency == 'ZHI_SHUI':
                        currency_name = '心如止水🏄'
                    else:
                        currency_name = currency
                    fn_print(f">>> 用户【{self.phone}】 -  卡片【{currency_name}】 - 数量：{balance}")
            total_fortune_times = obj.get("totalFortuneTimes", 0)
            fn_print(f">>> 用户【{self.phone}】 -  总卡片数量：{total_fortune_times}")
            return True
        else:
            fn_print(f">>> 用户【{self.phone}】 -  查询卡片数量失败！❌ - {data.get('errorMessage')}")
            return False

    async def ear_end_2023_receive_task(self):
        fn_print(f">>> 开始领取【{self.title}】任务奖励...")
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonNoLoginPost/~memberNonactivity~yearEnd2023TaskService~fetchMixTaskReward",
            headers=self.headers,
            json={
                "activityCode": "YEAR_END_2023",
                "channelType": "MINI_PROGRAM",
                "taskType": self.task_type
            }
        )
        data = response.json()
        if data.get("success"):
            fn_print(f">>> 用户【{self.phone}】 -  领取【{self.title}】任务奖励成功！✅")
        else:
            fn_print(f">>> 用户【{self.phone}】 -  领取【{self.title}】任务奖励失败！❌ - {data.get('errorMessage')}")

    async def anniversary_2024_weekly_gift_status(self):
        fn_print(f">>> 开始周年庆任务...")
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~anniversary2024IndexService~weeklyGiftStatus",
            headers=self.headers,
            json={}
        )
        data = response.json()
        if data.get("success"):
            weekly_gift_list = data.get("obj", {}).get("weeklyGiftList", [])
            for weekly_gift in weekly_gift_list:
                if not weekly_gift.get("received"):
                    receive_start_time = datetime.strptime(weekly_gift['receiveStartTime'], '%Y-%m-%d %H:%M:%S')
                    receive_end_time = datetime.strptime(weekly_gift['receiveEndTime'], '%Y-%m-%d %H:%M:%S')
                    current_time = datetime.now()
                    if receive_start_time <= current_time <= receive_end_time:
                        await self.anniversary_2024_receive_weekly_gift()
        else:
            error_message = data.get('errorMessage') or json.dumps(response) or '无返回'
            fn_print(f">>> 用户【{self.phone}】 -  查询每周领券失败！❌ - {error_message}")
            if "系统繁忙" in error_message or "用户手机号校验未通过" in error_message:
                self.anniversary_black = True

    async def anniversary_2024_receive_weekly_gift(self):
        fn_print(f">>> 开始领取每周领券...")
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~anniversary2024IndexService~receiveWeeklyGift",
            headers=self.headers
        )
        data = response.json()
        if data.get("success"):
            product_names = [product['productName'] for product in data.get('obj', [])]
            fn_print(f">>> 用户【{self.phone}】 -  领取每周领券【{product_names}】成功！✅")
        else:
            error_message = data.get('errorMessage') or json.dumps(response) or '无返回'
            fn_print(f">>> 用户【{self.phone}】 -  领取每周领券失败！❌ - {error_message}")
            if "系统繁忙" in error_message or "用户手机号校验未通过" in error_message:
                self.anniversary_black = True

    async def anniversary_2024_task_list(self):
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~activityTaskService~taskList",
            headers=self.headers,
            json={
                "activityCode": "ANNIVERSARY_2024",
                "channelType": "MINI_PROGRAM"
            }
        )
        data = response.json()
        if data.get("success"):
            task_list = data.get("obj", [])
            for task in filter(lambda x: x['status'] == 1, task_list):
                if self.anniversary_black:
                    return
                for _ in range(task['canReceiveTokenNum']):
                    await self.anniversary_2024_fetch_task_reward(task)
            for task in filter(lambda x: x['status'] == 2, task_list):
                if self.anniversary_black:
                    return
                if task['taskType'] in ['PLAY_ACTIVITY_GAME', 'PLAY_HAPPY_ELIMINATION', 'PARTAKE_SUBJECT_GAME']:
                    pass
                elif task['taskType'] == 'FOLLOW_SFZHUNONG_VEDIO_ID':
                    pass
                elif task['taskType'] in ['BROWSE_VIP_CENTER', 'GUESS_GAME_TIP', 'CREATE_SFID', 'CLICK_MY_SETTING',
                                          'CLICK_TEMPLATE', 'REAL_NAME', 'SEND_SUCCESS_RECALL', 'OPEN_SVIP',
                                          'OPEN_FAST_CARD', 'FIRST_CHARGE_NEW_EXPRESS_CARD', 'CHARGE_NEW_EXPRESS_CARD',
                                          'INTEGRAL_EXCHANGE']:
                    pass
                else:
                    for _ in range(task['restFinishTime']):
                        if self.anniversary_black:
                            break
                        await self.anniversary_2024_finish_task(task)

    async def anniversary_2024_finish_task(self, task):
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonRoutePost/memberEs/taskRecord/finishTask",
            headers=self.headers,
            json={'taskCode': task['taskCode']}
        )
        data = response.json()
        if data.get("success"):
            fn_print(f">>> 用户【{self.phone}】 -  完成任务【{task['taskName']}】成功！✅")
            await self.anniversary_2024_fetch_mix_task_reward(task)
        else:
            error_message = data.get('errorMessage') or json.dumps(response) or '无返回'
            fn_print(f">>> 用户【{self.phone}】 -  完成任务【{task['taskName']}】失败！❌ - {error_message}")

    async def anniversary_2024_fetch_mix_task_reward(self, task):
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~anniversary2024TaskService~fetchMixTaskReward",
            headers=self.headers,
            json={
                'taskType': task['taskType'],
                'activityCode': 'ANNIVERSARY_2024',
                'channelType': 'MINI_PROGRAM'
            }
        )
        data = response.json()
        if data.get("success"):
            reward_info = data.get('obj', {}).get('account', {})
            received_list = [f"[{item['currency']}]X{item['amount']}" for item in
                             reward_info.get('receivedAccountList', [])]
            turned_award = reward_info.get('turnedAward', {})
            if turned_award.get("productName"):
                received_list.append(f"[优惠券]{turned_award['productName']}")
            fn_print(f">> 领取任务【{task['taskName']}】奖励成功！✅ - 获得：{received_list}")
        else:
            error_message = data.get('errorMessage') or json.dumps(response) or '无返回'
            fn_print(f">> 领取任务【{task['taskName']}】奖励失败！❌ - {error_message}")
            if '用户手机号校验未通过' in error_message:
                self.anniversary_black = True

    async def anniversary_2024_unbox(self):
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~anniversary2024CardService~unbox",
            headers=self.headers,
            json={}
        )
        data = response.json()
        if data.get("success"):
            account_info = data.get("obj", {}).get("account", {})
            unbox_list = [f"[{item['currency']}]X{item['amount']}" for item in
                          account_info.get('receivedAccountList', [])]
            fn_print(">> 拆盒子📦： %s" % ', '.join(unbox_list) or '空气')
        else:
            error_message = data.get('errorMessage') or json.dumps(response) or '无返回'
            fn_print(f">> 拆盒子失败！❌ - {error_message}")
            if '用户手机号校验未通过' in error_message:
                self.anniversary_black = True

    async def anniversary_2024_game_list(self):
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~anniversary2024GameParkService~list",
            headers=self.headers,
            json={}
        )
        data = response.json()
        if data.get("success"):
            topic_pk_info = data['obj'].get('topicPKInfo', {})
            search_word_info = data['obj'].get('searchWordInfo', {})
            happy_elimination_info = data['obj'].get('happyEliminationInfo', {})

            if not topic_pk_info.get("isPassFlag"):
                fn_print("> 开始话题PK赛")
                await self.anniversary_2024_topic_pk_topic_list()
            if not search_word_info.get("isPassFlag") or not search_word_info.get("isFinishDailyFlag"):
                fn_print("> 开始找字游戏")
                for i in range(1, 11):
                    wait_time = random.randint(1000, 3000) / 1000.0
                    await asyncio.sleep(wait_time)
                    if not await self.anniversary_2024_happy_elimination_win(i):
                        break
        else:
            error_message = data.get('errorMessage') or json.dumps(response) or '无返回'
            fn_print(f">> 查询游戏状态失败！❌ - {error_message}")
            if '用户手机号校验未通过' in error_message:
                self.anniversary_black = True

    async def anniversary_2024_search_word_win(self, index):
        flag = True
        try:
            response = await self.client.post(
                url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~anniversary2024SearchWordService~win",
                headers=self.headers,
                json={
                    "index": index
                }
            )
            data = response.json()
            if data.get("success"):
                currency_list = data.get('obj', {}).get('currencyDTOList', [])
                rewards = ', '.join([f"[{c.get('currency')}]X{c.get('amount')}" for c in currency_list])
                fn_print(
                    f">>> 用户【{self.phone}】 -  找字游戏第{index}关胜利！✅ - {rewards if rewards else '未获得奖励'}")
            else:
                error_message = data.get('errorMessage') or json.dumps(response) or '无返回'
                fn_print(f">>> 用户【{self.phone}】 -  找字游戏第{index}关失败！❌ - {error_message}")
                if '系统繁忙' in error_message:
                    flag = False
        except Exception as e:
            fn_print(f">>> 用户【{self.phone}】 -  找字游戏异常‼️ - {e}")
            flag = False
        finally:
            return flag

    async def anniversary_2024_happy_elimination_win(self, index):
        flag = True
        try:
            response = await self.client.post(
                url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~anniversary2024HappyEliminationService~win",
                headers=self.headers,
                json={
                    "index": index
                }
            )
            data = response.json()
            if data.get("success"):
                is_award = data['obj'].get('isAward')
                currency_dto_list = data['obj'].get('currencyDTOList', [])
                rewards = ', '.join([f"[{c.get('currency')}]X{c.get('amount')}" for c in currency_dto_list])
                fn_print(f">>> 用户【{self.phone}】 -  第{index}关胜利！✅ - {rewards if rewards else '未获得奖励'}")
            else:
                error_message = data.get('errorMessage') or json.dumps(response) or '无返回'
                fn_print(f">>> 用户【{self.phone}】 -  第{index}关失败！❌ - {error_message}")
                if '系统繁忙' in error_message:
                    flag = False
        except Exception as e:
            fn_print(f">>> 用户【{self.phone}】 -  第{index}关异常‼️ - {e}")
            flag = False
        finally:
            return flag

    async def anniversary_2024_topic_pk_choose_side(self, index):
        flag = True
        self.headers.update(
            {
                "channel": "31annizyw"
            }
        )
        try:
            response = await self.client.post(
                url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~anniversary2024TopicPkService~chooseSide",
                headers=self.headers,
                json={
                    "index": index,
                    "choose": 0
                }
            )
            data = response.json()
            if data.get("success"):
                currency_dto_list = data['obj'].get('currencyDTOList', [])
                rewards = ', '.join([f"[{c.get('currency')}]X{c.get('amount')}" for c in currency_dto_list])
                fn_print(
                    f">>> 用户【{self.phone}】 -  话题PK赛选择话题{index}成功！✅ - {rewards if rewards else '未获得奖励'}")
            else:
                error_message = data.get('errorMessage') or json.dumps(response) or '无返回'
                fn_print(f">>> 用户【{self.phone}】 -  话题PK赛选择话题{index}失败！❌ - {error_message}")
                if '系统繁忙' in error_message:
                    flag = False
        except Exception as e:
            fn_print(f">>> 用户【{self.phone}】 -  话题PK赛选择话题{index}异常‼️ - {e}")
            flag = False
        finally:
            return flag

    async def anniversary_2024_topic_pk_topic_list(self):
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~anniversary2024TopicPkService~topicList",
            headers=self.headers,
            json={}
        )
        data = response.json()
        if data.get("success"):
            topics = data['obj'].get('topics', [])
            for topic in topics:
                if not topic.get('choose'):
                    index = topic.get('index', 1)
                    wait_time = random.randint(2000, 4000) / 1000.0
                    await asyncio.sleep(wait_time)
                    if not self.anniversary_2024_topic_pk_choose_side(index):
                        break
        else:
            error_message = data.get('errorMessage') or json.dumps(response) or '无返回'
            fn_print(f">> 查询话题PK赛记录失败！❌ - {error_message}")

    async def anniversary_2024_query_account_status_refresh(self):
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~anniversary2024CardService~queryAccountStatus",
            headers=self.headers,
            json={}
        )
        data = response.json()
        if not data.get("success"):
            error_message = data.get('errorMessage') or json.dumps(response) or '无返回'
            fn_print(f">> 查询账户状态失败！❌ - {error_message}")

    async def anniversary_2024_title_list(self):
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~anniversary2024GuessService~titleList",
            headers=self.headers,
            json={}
        )
        data = response.json()
        if data.get("success"):
            guess_title_info_list = data.get('obj', {}).get('guessTitleInfoList', [])
            today_titles = [title for title in guess_title_info_list if title['gameDate'] == self.today]
            for title_info in today_titles:
                if title_info['answerStatus']:
                    fn_print(f">> 今日已回答过竞猜")
                else:
                    answer = self.answer
                    if answer:
                        await self.anniversary_2024_answer(title_info)
                        print(f"进行了答题： {answer}")
        else:
            error_message = data.get('errorMessage') or json.dumps(response) or '无返回'
            fn_print(f">> 查询每日口令竞猜失败！❌ - {error_message}")

    async def anniversary_2024_title_list_award(self):
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~anniversary2024GuessService~titleList",
            headers=self.headers
        )
        data = response.json()
        if data.get("success"):
            guess_title_info_list = data.get('obj', {}).get('guessTitleInfoList', [])
            today_awards = [title for title in guess_title_info_list if title['gameDate'] == self.today]

            for award_info in today_awards:
                if award_info['answerStatus']:
                    awards = award_info.get('awardList', []) + award_info.get('puzzleList', [])
                    awards_description = ', '.join([f"{award['productName']}" for award in awards])
                    print(f'>> 口令竞猜奖励: {awards_description}' if awards_description else '今日无奖励')
                else:
                    print('>> 今日还没回答竞猜')
        else:
            error_message = data.get('errorMessage') or json.dumps(response) or '无返回'
            print(f">> 查询每日口令竞猜失败！❌ - {error_message}")

    async def anniversary_2024_answer(self, answer_info):
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~anniversary2024GuessService~answer",
            headers=self.headers,
            json={
                'period': answer_info['period'],
                'answerInfo': answer_info
            }
        )
        data = response.json()
        if data.get("success"):
            print(f">> 口令竞猜回答成功！")
            await self.anniversary_2024_title_list_award()
        else:
            error_message = data.get('errorMessage') or json.dumps(response) or '无返回'
            print(f">> 口令竞猜回答失败！❌ - {error_message}")

    async def anniversary_2024_query_account_status(self):
        response = await self.client.post(
            url='https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~anniversary2024CardService~queryAccountStatus',
            headers=self.headers
        )
        result = response.json()

        # 统一错误处理
        async def handle_error(message_prefix):
            error_message = result.get('errorMessage') or json.dumps(result) or '无返回'
            fn_print(f'{message_prefix}: {error_message}')

        if not result.get('success'):
            await handle_error('查询账户状态失败')
            return

        account_data = result.get('obj', {})
        account_currencies = account_data.get('accountCurrencyList', [])

        # 处理拆盒机会
        unbox_chance = next((c for c in account_currencies if c.get('currency') == 'UNBOX_CHANCE'), None)
        unbox_balance = unbox_chance.get('balance', 0) if unbox_chance else 0
        if unbox_balance > 0:
            fn_print(f'可以拆{unbox_balance}次盒子')
            # 如需实际拆盒，取消下方注释
            # for _ in range(unbox_balance):
            #     self.anniversary2024_unbox()

        # 初始化卡片数据容器
        self.cards = {f'CARD_{i}': 0 for i in range(1, 10)}
        self.cards['COMMON_CARD'] = 0
        card_collections = []

        # 处理卡片数据
        for currency in account_currencies:
            curr_type = currency.get('currency')
            balance = int(currency.get('balance', 0))

            if curr_type in self.cards:
                self.cards[curr_type] = balance
                card_collections.append(f'[{curr_type}]X{balance}')
            elif curr_type == 'UNBOX_CHANCE':
                continue  # 已单独处理

        # 输出收集结果
        if card_collections:
            fn_print(f'已收集拼图: {", ".join(card_collections)}')
        else:
            fn_print('当前尚未收集到任何拼图')

    async def do_draw(self, cards):
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~anniversary2024CardService~collectDrawAward",
            headers=self.headers,
            json={
                "accountList": cards
            }
        )
        data = response.json()
        if data.get("success"):
            obj = data.get("obj", {})
            product_name = obj.get("productName", "")
            fn_print(f">>> 用户【{self.phone}】 -  抽奖成功！✅ - 获得【{product_name}】")
            return True
        else:
            error_message = data.get('errorMessage') or json.dumps(response) or '无返回'
            fn_print(f">>> 用户【{self.phone}】 -  抽奖失败！❌ - {error_message}")
            return False

    async def convert_common_card(self, cards, target_card):
        if cards['COMMON_CARD'] > 0:
            cards['COMMON_CARD'] -= 1
            cards[target_card] += 1
            return True
        return False

    async def can_draw(self, cards, n):
        distinct_cards = sum(1 for card, amount in cards.items() if card != 'COMMON_CARD' and amount > 0)
        return distinct_cards >= n

    async def draw(self, cards, n):
        drawn_cards = []
        for card, amount in sorted(cards.items(), key=lambda item: item[1]):
            if card != 'COMMON_CARD' and amount > 0:
                cards[card] -= 1
                drawn_cards.append(card)
                if len(drawn_cards) == n:
                    break
        if len(drawn_cards) == n:
            "没有足够的卡进行抽奖"
        if await self.do_draw(drawn_cards):
            return drawn_cards  # 返回本次抽奖使用的卡
        else:
            return None

    async def simulate_lottery(self, cards):
        while await self.can_draw(cards, 9):
            used_cards = await self.draw(cards, 9)
            fn_print(f">>> 用户【{self.phone}】，进行了一次9卡抽奖，消耗卡片: ", used_cards)
        while await self.can_draw(cards, 7) or await self.convert_common_card(cards, 'CARD_1'):
            if not await self.can_draw(cards, 7):
                continue
            used_cards = await self.draw(cards, 7)
            fn_print(f">>> 用户【{self.phone}】，进行了一次7卡抽奖，消耗卡片: ", used_cards)
        while await self.can_draw(cards, 5) or await self.convert_common_card(cards, 'CARD_1'):
            if not await self.can_draw(cards, 5):
                continue
            used_cards = await self.draw(cards, 5)
            fn_print(f">>> 用户【{self.phone}】，进行了一次5卡抽奖，消耗卡片: ", used_cards)
        while await self.can_draw(cards, 3) or await self.convert_common_card(cards, 'CARD_1'):
            if not await self.can_draw(cards, 3):
                continue
            used_cards = await self.draw(cards, 3)
            fn_print(f">>> 用户【{self.phone}】，进行了一次3卡抽奖，消耗卡片: ", used_cards)

    async def anniversary_2024_task(self):
        await self.anniversary_2024_weekly_gift_status()
        if self.anniversary_black:
            return
        await self.anniversary_2024_query_account_status()
        target_time = datetime(2024, 4, 3, 14, 0)
        if datetime.now() >= target_time:
            fn_print("周年庆活动即将结束，开始自动抽奖")
            await self.simulate_lottery(self.cards)
        else:
            fn_print("未到自动抽奖时间")

    async def member_day_index(self):
        fn_print(">>> 会员日活动...")
        try:
            invite_user_id = random.choice([invite for invite in inviteId if invite != self.user_id])
            response = await self.client.post(
                url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~memberDayIndexService~index",
                headers=self.headers,
                json={
                    "inviteUserId": invite_user_id
                }
            )
            data = response.json()
            if data.get("success"):
                lottery_num = data.get('obj', {}).get('lotteryNum', 0)
                can_receive_invite_award = data.get('obj', {}).get('canReceiveInviteAward', False)
                if can_receive_invite_award:
                    await self.member_day_receive_invite_award(invite_user_id)
                await self.member_day_red_packet_status()
                fn_print(f">> 会员日可以抽奖{lottery_num}次")
                for _ in range(lottery_num):
                    await self.member_day_lottery()
                if self.member_day_black:
                    return
                await self.member_day_task_list()
                if self.member_day_black:
                    return
                await self.member_day_red_packet_status()
            else:
                error_message = data.get('errorMessage', '无返回')
                fn_print(f">> 查询会员日失败！❌ - {error_message}")
                if "没有资格参与活动" in error_message:
                    self.member_day_black = True
                    fn_print(f"会员日任务风控‼️")
        except Exception as e:
            fn_print(f">> 查询会员日异常！❌ - {e}")

    async def member_day_receive_invite_award(self, invite_user_id):
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~memberDayIndexService~receiveInviteAward",
            headers=self.headers,
            json={
                "inviteUserId": invite_user_id
            }
        )
        data = response.json()
        if data.get("success"):
            product_name = data.get('obj', {}).get('productName', '空气')
            fn_print(f">> 会员日奖励： {product_name}")
        else:
            error_message = data.get('errorMessage', '无返回')
            fn_print(f">> 领取会员日奖励失败！❌ - {error_message}")
            if "没有资格参与活动" in error_message:
                self.member_day_black = True
                fn_print(f"会员日任务风控‼️")

    async def member_day_lottery(self):
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~memberDayLotteryService~lottery",
            headers=self.headers,
            json={}
        )
        data = response.json()
        if data.get("success"):
            product_name = data.get('obj', {}).get('productName', '空气')
            fn_print(f">> 会员日抽奖成功！✅ - {product_name}")
        else:
            error_message = data.get('errorMessage', '无返回')
            fn_print(f">> 会员日抽奖失败！❌ - {error_message}")
            if "没有资格参与活动" in error_message:
                self.member_day_black = True
                fn_print(f"会员日任务风控‼️")

    async def member_day_task_list(self):
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~activityTaskService~taskList",
            headers=self.headers,
            json={
                'activityCode': 'MEMBER_DAY',
                'channelType': 'MINI_PROGRAM'
            }
        )
        data = response.json()
        if data.get("success"):
            task_list = data.get('obj', {})
            for task in task_list:
                if task['status'] == 1:
                    if self.member_day_black:
                        return
                    await self.member_day_fetch_mix_task_reward(task)
            for task in task_list:
                if task['status'] == 2:
                    if self.member_day_black:
                        return
                    if task['taskType'] in ['SEND_SUCCESS', 'INVITEFRIENDS_PARTAKE_ACTIVITY', 'OPEN_SVIP',
                                            'OPEN_NEW_EXPRESS_CARD', 'OPEN_FAMILY_CARD', 'CHARGE_NEW_EXPRESS_CARD',
                                            'INTEGRAL_EXCHANGE']:
                        pass
                    else:
                        for _ in range(task['restFinishTime']):
                            if self.member_day_black:
                                return
                            await self.member_day_finish_task(task)
        else:
            error_message = data.get('errorMessage', '无返回')
            fn_print(f">> 查询会员日任务列表失败！❌ - {error_message}")
            if "没有资格参与活动" in error_message:
                self.member_day_black = True
                fn_print(f"会员日任务风控‼️")

    async def member_day_finish_task(self, task):
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberEs~taskRecord~finishTask",
            headers=self.headers,
            json={
                'taskCode': task['taskCode']
            }
        )
        data = response.json()
        if data.get("success"):
            fn_print(f">>> 用户【{self.phone}】，会员日任务【{task['taskName']}】完成！✅")
            await self.member_day_fetch_mix_task_reward(task)
        else:
            error_message = data.get('errorMessage', '无返回')
            fn_print(f">>> 用户【{self.phone}】，会员日任务【{task['taskName']}】失败！❌ - {error_message}")
            if "没有资格参与活动" in error_message:
                self.member_day_black = True
                fn_print(f"会员日任务风控‼️")

    async def member_day_fetch_mix_task_reward(self, task):
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~activityTaskService~fetchMixTaskReward",
            headers=self.headers,
            json={
                'taskType': task['taskType'],
                'activityCode': 'MEMBER_DAY',
                'channelType': 'MINI_PROGRAM'
            }
        )
        data = response.json()
        if data.get("success"):
            fn_print(f">>> 用户【{self.phone}】，会员日任务【{task['taskName']}】领取奖励成功！✅")
        else:
            error_message = data.get('errorMessage', '无返回')
            fn_print(f">>> 用户【{self.phone}】，会员日任务【{task['taskName']}】领取奖励失败！❌ - {error_message}")
            if "没有资格参与活动" in error_message:
                self.member_day_black = True
                fn_print(f"会员日任务风控‼️")

    async def member_day_receive_red_packet(self, hour):
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~memberDayTaskService~receiveRedPacket",
            headers=self.headers,
            json={
                "receiveHour": hour
            }
        )
        data = response.json()
        if data.get("success"):
            fn_print(f">> 会员日领取{hour}点红包成功！✅")
        else:
            error_message = data.get('errorMessage', '无返回')
            fn_print(f">> 会员日领取{hour}点红包失败！❌ - {error_message}")
            if "没有资格参与活动" in error_message:
                self.member_day_black = True
                fn_print(f"会员日任务风控‼️")

    async def member_day_red_packet_status(self):
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~memberDayPacketService~redPacketStatus",
            headers=self.headers,
            json={}
        )
        data = response.json()
        if data.get("success"):
            packet_list: list = data.get("obj", {}).get("packetList", [])
            for packet in packet_list:
                self.member_day_red_packet_map[packet['level']] = packet['count']
            for level in range(1, self.max_level):
                count = self.member_day_red_packet_map.get(level, 0)
                while count >= 2:
                    await self.member_day_red_packet_merge(level)
                    count -= 2
            packet_summary = []
            remaining_needed = 0
            for level, count in self.member_day_red_packet_map.items():
                packet_summary.append(f"{level}级红包：{count}个")
                if count == 0:
                    continue
                packet_summary.append(f"[{level}级X{count}]")
                int_level = int(level)
                if int_level < self.max_level:
                    remaining_needed += 1 << (int_level - 1)
            fn_print(f"会员日合成列表： " + ", ".join(packet_summary))
            if self.member_day_red_packet_map.get(self.max_level):
                fn_print(f"会员日已拥有[{self.max_level}级]X{self.member_day_red_packet_map.get(self.max_level)}")
                await self.member_day_packet_draw(self.max_level)
            else:
                remaining = self.packet_threshold - remaining_needed
                fn_print(f"会员日距离[{self.max_level}级]红包还差： [1级]红包{remaining}")
        else:
            error_message = data.get('errorMessage', '无返回')
            fn_print(f">> 查询会员日红包状态失败！❌ - {error_message}")
            if "没有资格参与活动" in error_message:
                self.member_day_black = True
                fn_print(f"会员日任务风控‼️")

    async def member_day_red_packet_merge(self, level):
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~memberDayPacketService~redPacketMerge",
            headers=self.headers,
            json={
                "level": level,
                "num": 2
            }
        )
        data = response.json()
        if data.get("success"):
            fn_print(f"会员日合成: [{level}级]红包X2 -> [{level + 1}级]红包")
            self.member_day_red_packet_map[level] -= 2
            if not self.member_day_red_packet_map.get(level + 1):
                self.member_day_red_packet_map[level + 1] = 0
            self.member_day_red_packet_map[level + 1] += 1
        else:
            error_message = data.get('errorMessage', '无返回')
            fn_print(f">> 会员日合成两个[{level}级]红包失败！❌ - {error_message}")
            if "没有资格参与活动" in error_message:
                self.member_day_black = True
                fn_print(f"会员日任务风控‼️")

    async def member_day_red_packet_draw(self, level):
        response = await self.client.post(
            url="https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~memberDayPacketService~redPacketDraw",
            headers=self.headers,
            json={
                "level": str(level)
            }
        )
        data = response.json()
        if data.get("success"):
            coupon_names = [item['couponName'] for item in data.get('obj', [])] or []
            fn_print(f"会员日提取[{level}级]红包: {', '.join(coupon_names) or '空气'}")
        else:
            error_message = data.get('errorMessage') if data else '无返回'
            fn_print(f">> 会员日提取[{level}级]红包失败！❌ - {error_message}")
            if "没有资格参与活动" in error_message:
                self.member_day_black = True
                fn_print(f"会员日任务风控‼️")

    async def midautumn_2024_index(self):
        fn_print(">>> 查询活动状态...")
        invite_user_id = random.choice([invite for invite in inviteId if invite != self.user_id])
        self.headers.update(
            {
                "channel": "newExpressWX",
                "referer": f'https://mcs-mimp-web.sf-express.com/origin/a/mimp-activity/midAutumn2024?mobile={self.mobile}&userId={self.user_id}&path=/origin/a/mimp-activity/midAutumn2024&supportShare=&inviteUserId={invite_user_id}&from=newExpressWX'
            }
        )
        response = await self.client.post(
            url='https://mcs-mimp-web.sf-express.com/mcs-mimp/commonNoLoginPost/~memberNonactivity~midAutumn2024IndexService~index',
            headers=self.headers,
            json={}
        )
        data = response.json()
        if data.get("success"):
            obj = data.get("obj", {})
            ac_end_time = obj.get("acEndTime", "")
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            comparison_time = datetime.strptime(ac_end_time, "%Y-%m-%d %H:%M:%S")
            is_less_than = datetime.now() < comparison_time
            if is_less_than:
                fn_print("活动进行中...")
                return True
            else:
                fn_print("活动已结束...")
                return False
        else:
            error_message = data.get('errorMessage', '无返回')
            fn_print(f">> 查询活动状态失败！❌ - {error_message}")
            if "没有资格参与活动" in error_message:
                self.midautumn_2024_black = True
                fn_print(f"活动任务风控‼️")
            return False

    async def midautumn_2024_game_index_info(self):
        fn_print(">>> 开始游戏...")
        response = await self.client.post(
            url='https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~midAutumn2024GameService~indexInfo',
            headers=self.headers,
            json={}
        )
        data = response.json()
        if data.get("success"):
            obj = data.get("obj", {})
            maxPassLevel = obj.get('maxPassLevel', '')
            ifPassAllLevel = obj.get('ifPassAllLevel', '')
            if maxPassLevel != 30:
                await self.midautumn_2024_win(maxPassLevel)
            else:
                await self.midautumn_2024_win(0)
        else:
            error_message = data.get('errorMessage', '无返回')
            fn_print(f">> 查询中秋游戏信息！❌ - {error_message}")
            if "没有资格参与活动" in error_message:
                self.midautumn_2024_black = True
                fn_print(f"活动任务风控‼️")
            return False

    async def midautumn_2024_game_init(self):
        fn_print(">>> 开始游戏...")
        response = await self.client.post(
            url='https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~midAutumn2024GameService~init',
            headers=self.headers,
            json={}
        )
        data = response.json()
        if data.get("success"):
            obj = data.get("obj", {})
            currentIndex = obj.get('currentIndex', '')
            ifPassAllLevel = obj.get('ifPassAllLevel', '')
            if currentIndex != 30:
                await self.midautumn_2024_win(currentIndex)
            else:
                await self.midautumn_2024_win(0)
        else:
            error_message = data.get('errorMessage', '无返回')
            fn_print(f">> 中秋游戏失败！❌ - {error_message}")
            if "没有资格参与活动" in error_message:
                self.midautumn_2024_black = True
                fn_print(f"活动任务风控‼️")
            return False

    async def midautumn_2024_weekly_gift_status(self):
        fn_print(">>> 查询每周礼包领取状态...")
        response = await self.client.post(
            url='https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~midAutumn2024IndexService~weeklyGiftStatus',
            headers=self.headers,
            json={}
        )
        data = response.json()
        if data.get("success"):
            obj = data.get("obj", [{}])
            for gift in obj:
                received = gift['received']
                receiveStartTime = gift['receiveStartTime']
                receiveEndTime = gift['receiveEndTime']
                fn_print(f">> 领取时间: {receiveStartTime} - {receiveEndTime}")
                if received:
                    fn_print(f">> 该礼包已领取")
                    continue
                receive_start_time = datetime.strptime(receiveStartTime, "%Y-%m-%d %H:%M:%S")
                receive_end_time = datetime.strptime(receiveEndTime, "%Y-%m-%d %H:%M:%S")
                is_within_range = receive_start_time <= datetime.now() <= receive_end_time
                if is_within_range:
                    print(f'>> 开始领取礼包：')
                    await self.midautumn_2024_receive_weekly_gift()
        else:
            error_message = data.get('errorMessage', '无返回')
            fn_print(f">> 查询每周礼包领取状态失败！❌ - {error_message}")
            if "没有资格参与活动" in error_message:
                self.midautumn_2024_black = True
                fn_print(f"活动任务风控‼️")

    async def midautumn_2024_receive_weekly_gift(self):
        fn_print(">>> 开始领取每周礼包...")
        invite_user_id = random.choice([invite for invite in inviteId if invite != self.user_id])
        response = await self.client.post(
            url='https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~midAutumn2024IndexService~receiveWeeklyGift',
            headers=self.headers,
            json={
                'inviteUserId': invite_user_id
            }
        )
        data = response.json()
        if data.get("success"):
            obj = data.get("obj", [{}])
            if obj == [{}]:
                fn_print(f">> 礼包领取失败！❌")
                return False
            for gift in obj:
                productName = gift['productName']
                amount = gift['amount']
                fn_print(f">> 领取成功！✅ - {productName} X {amount}")
        else:
            error_message = data.get('errorMessage', '无返回')
            fn_print(f">> 领取每周礼包失败！❌ - {error_message}")
            if "没有资格参与活动" in error_message:
                self.midautumn_2024_black = True
                fn_print(f"活动任务风控‼️")

    async def midautumn_2024_task_list(self):
        fn_print(">>> 查询推币任务列表...")
        response = await self.client.post(
            url='https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~activityTaskService~taskList',
            headers=self.headers,
            json={
                'activityCode': 'MID_AUTUMN_2024',
                'channelType': 'MINI_PROGRAM'
            }
        )
        data = response.json()
        if data.get("success"):
            obj = data.get("obj", [{}])
            for task in obj:
                task_type = task['taskType']
                self.task_name = task['taskName']
                status = task['status']
                if status == 3:
                    fn_print(f">> 任务【{self.task_name}】已完成！✅")
                    continue
                self.task_code = task.get('taskCode', None)
                if self.task_code:
                    await self.midautumn_2024_finish_task()
                if task_type == 'PLAY_ACTIVITY_GAME':
                    await self.midautumn_2024_game_init()
        else:
            error_message = data.get('errorMessage', '无返回')
            fn_print(f">> 查询推币任务列表失败！❌ - {error_message}")
            if "没有资格参与活动" in error_message:
                self.midautumn_2024_black = True
                fn_print(f"活动任务风控‼️")

    async def midautumn_2024_coin_status(self, flag=False):
        fn_print(f">>> 查询金币信息...")
        response = await self.client.post(
            url='https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~midAutumn2024CoinService~coinStatus',
            headers=self.headers,
            json={}
        )
        data = response.json()
        if data.get("success"):
            obj = data.get("obj", None)
            if obj is None: return False
            accountCurrencyList = obj.get('accountCurrencyList', [])
            pushedTimesToday = obj.get('pushedTimesToday', '')
            pushedTimesTotal = obj.get('pushedTimesTotal', '')
            PUSH_TIMES_balance = 0
            self.COIN_balance = 0
            WELFARE_CARD_balance = 0
            for li in accountCurrencyList:
                if li['currency'] == 'PUSH_TIMES':
                    PUSH_TIMES_balance = li['balance']
                if li['currency'] == 'COIN':
                    self.COIN_balance = li['balance']
                if li['currency'] == 'WELFARE_CARD':
                    WELFARE_CARD_balance = li['balance']

            PUSH_TIMES = PUSH_TIMES_balance
            if flag:
                if PUSH_TIMES_balance > 0:
                    for i in range(PUSH_TIMES_balance):
                        fn_print(f'>> 开始第【{PUSH_TIMES_balance + 1}】次推币')
                        await self.midautumn_2024_push_coin()
                        PUSH_TIMES -= 1
                        pushedTimesToday += 1
                        pushedTimesTotal += 1
                fn_print(f'> 剩余推币次数：【{PUSH_TIMES}】')
                fn_print(f'> 当前金币：【{self.COIN_balance}】')
                fn_print(f'> 今日推币：【{pushedTimesToday}】次')
                fn_print(f'> 总推币：【{pushedTimesTotal}】次')
            else:
                fn_print(f'> 剩余推币次数：【{PUSH_TIMES_balance}】')
                fn_print(f'> 当前金币：【{self.COIN_balance}】')
                fn_print(f'> 今日推币：【{pushedTimesToday}】次')
                fn_print(f'> 总推币：【{pushedTimesTotal}】次')
            await self.midautumn_2024_give_push_times()
        else:
            error_message = data.get('errorMessage', '无返回')
            fn_print(f">> 查询金币信息失败！❌ - {error_message}")
            if "没有资格参与活动" in error_message:
                self.midautumn_2024_black = True
                fn_print(f"活动任务风控‼️")

    async def midautumn_2024_push_coin(self):
        response = await self.client.post(
            url='https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~midAutumn2024CoinService~pushCoin',
            headers=self.headers,
            json={}
        )
        data = response.json()
        if data.get("success"):
            obj = data.get("obj", [{}])
            draw_award = obj.get('drawAward', "")
            self.COIN_balance += draw_award
            fn_print(f">> 推币成功！✅ - 获得【{draw_award}】金币🪙")
        else:
            error_message = data.get('errorMessage', '无返回')
            fn_print(f">> 推币失败！❌ - {error_message}")
            if "没有资格参与活动" in error_message:
                self.midautumn_2024_black = True
                fn_print(f"活动任务风控‼️")

    async def midautumn_2024_give_push_times(self):
        fn_print(">>> 领取赠送推币次数...")
        response = await self.client.post(
            url='https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~midAutumn2024CoinService~givePushTimes',
            headers=self.headers,
            json={}
        )
        data = response.json()
        if data.get("success"):
            obj = data.get("obj", 0)
            fn_print(f">> 领取成功！✅ - 获得【{obj}】推币次数")
        else:
            error_message = data.get('errorMessage', '无返回')
            fn_print(f">> 领取赠送推币次数失败！❌ - {error_message}")
            if "没有资格参与活动" in error_message:
                self.midautumn_2024_black = True
                fn_print(f"活动任务风控‼️")

    async def midautumn_2024_finish_task(self):
        fn_print(f">>> 开始完成任务【{self.task_name}】...")
        response = await self.client.post(
            url='https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberEs~taskRecord~finishTask',
            headers=self.headers,
            json={
                'taskCode': self.task_code
            }
        )
        data = response.json()
        if data.get("success"):
            obj = data.get("obj", False)
            fn_print(f">>> 任务【{self.task_name}】完成成功！✅")
        else:
            error_message = data.get('errorMessage', '无返回')
            fn_print(f">>> 任务【{self.task_name}】完成失败！❌ - {error_message}")
            if "没有资格参与活动" in error_message:
                self.midautumn_2024_black = True
                fn_print(f"活动任务风控‼️")

    async def midautumn_2024_win(self, level):
        fn_print(f">>> 开始闯关...")
        for i in range(level, 31):
            fn_print(f'开始第【{i}】关')
            response = await self.client.post(
                url='https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~midAutumn2024GameService~win',
                headers=self.headers,
                json={
                    'levelIndex': i
                }
            )
            data = response.json()
            if data.get("success"):
                obj = data.get("obj", [{}])
                current_award_list = obj.get('currentAwardList', [])
                if current_award_list != []:
                    for award in current_award_list:
                        currency = award.get('currency', '')
                        amount = award.get('amount', '')
                        fn_print(f'>> 获得【{currency}】X【{amount}】')
                else:
                    fn_print(">> 本关无奖励")
            else:
                error_message = data.get('errorMessage', '无返回')
                fn_print(f">> 闯关失败！❌ - {error_message}")
                if "没有资格参与活动" in error_message:
                    self.midautumn_2024_black = True
                    fn_print(f"活动任务风控‼️")

    async def run(self):
        if not await self.login(): return False
        await self.sign_in()
        await self.super_welfare_benefit_sign_in()
        await self.processe_tasks()
        await self.honey_index_data()
        await self.get_honey_task_list_and_start()
        await self.honey_index_data()
        target_time = datetime(2025, 4, 8, 19, 0)
        if datetime.now() < target_time:
            await self.ear_end_2023_task_list()
            await self.ear_end_2023_query()
        else:
            fn_print("周年庆活动已结束！")
        current_date = datetime.now().day
        if 26 <= current_date <= 28:
            await self.member_day_index()
        else:
            fn_print("未到指定时间， 不执行会员日任务！")
        if await self.midautumn_2024_index():
            await self.midautumn_2024_weekly_gift_status()
            await self.midautumn_2024_coin_status()
            await self.midautumn_2024_task_list()
            await self.midautumn_2024_coin_status(True)
        return True


async def main():
    tasks = []
    for index, url_info in enumerate(sfsy_tokens):
        sfsy = Sfsy(url_info, index)
        tasks.append(sfsy.run())
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())
    send_notification_message_collection(f"顺丰速运签到通知 - {datetime.now().strftime('%Y/%m/%d')}")
