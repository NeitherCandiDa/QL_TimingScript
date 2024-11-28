# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         滴滴出行.py
# @author           Echo
# @EditTime         2024/11/27
# const $ = new Env('滴滴出行')
# cron "0 8,14,17 * * *"
"""
DD_TOKENS： 滴滴出行进入福利页面抓token值
自行配经纬度和城市id
"""
import asyncio
import datetime

import httpx

from fn_print import fn_print
from get_env import get_env

MONTH_SIGNAL = False  # 月月领券

dd_tokens = get_env("DD_TOKENS", "&")


class DiDi:
    LAT = "30.707130422009786"  # 纬度
    LNG = "104.09652654810503"  # 经度
    CITY_ID = 17  # 城市id

    def __init__(self, token, city_id=CITY_ID, lat=LAT, lng=LNG):
        self.user_phone = None
        self.client = httpx.AsyncClient(verify=False)
        self.token = token
        self.city_id = city_id
        self.lat = lat
        self.lng = lng
        self.today = datetime.datetime.now().strftime("%Y-%m-%d")
        self.tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        self.activity_id_today = 0
        self.task_id_today = 0
        self.status_today = 0
        self.activity_id_tomorrow = 0
        self.status_tomorrow = 0
        self.count_tomorrow = 0

    async def get_user_info(self):
        """
        获取用户信息
        :return: 
        """
        get_user_info_response = await self.client.get(
            url=f"https://common.diditaxi.com.cn/passenger/getprofile?token={self.token}"
        )
        get_user_info_data = get_user_info_response.json()
        self.user_phone = get_user_info_data.get("phone")

    async def get_welfare_payments(self):
        """
        获取福利金
        :return: 
        """
        get_weibo_payments_response = await self.client.get(
            url="https://rewards.xiaojukeji.com/loyalty_credit/bonus/getWelfareUsage4Wallet",
            params={
                "token": self.token,
                "city_id": self.city_id
            }
        )
        if get_weibo_payments_response.status_code == 200:
            get_info_data = get_weibo_payments_response.json()
            return get_info_data['data']['balance']
        else:
            fn_print(f"===获取用户福利金请求异常, {get_weibo_payments_response.text}===")

    async def sign_in(self):
        """
        签到
        :return: 
        """
        sign_in_response = await self.client.post(
            url="https://ut.xiaojukeji.com/ut/welfare/api/action/dailySign",
            json={
                "token": self.token,
                "lat": self.lat,
                "lng": self.lng,
                "platform": "na",
                "env": '{}'
            }
        )
        if sign_in_response.status_code == 200:
            sign_in_data = sign_in_response.json()
            fn_print(sign_in_data)
            if sign_in_data["errno"] == 0:
                subsidy_amount = sign_in_data["data"]["subsidy_state"]["subsidy_amount"]
                fn_print(f"用户【{0}】, ===今日签到成功，获得{subsidy_amount}福利金🪙🪙🪙===")
                return
            elif sign_in_data["errno"] == 40009:
                fn_print(f"用户【{0}】, ===今日福利金已签到，无需重复签到！===")
                return
            else:
                fn_print(f"用户【{0}】, ===签到失败, {sign_in_data}===")
        else:
            fn_print(f"===签到请求异常, {sign_in_response}===")

    async def get_carve_up_action_id(self):
        """
        获取瓜分活动的ID
        :return: 
        """
        get_carve_up_action_id_response = await self.client.post(
            url="https://ut.xiaojukeji.com/ut/welfare/api/home/init/v2",
            json={
                "token": self.token,
                "lat": self.lat,
                "lng": self.lng,
                "platform": "na",
                "env": '{}'
            }
        )
        if get_carve_up_action_id_response.status_code == 200:
            get_carve_up_action_id_data = get_carve_up_action_id_response.json()
            if get_carve_up_action_id_data.get("errno") == 0:
                divide_data = get_carve_up_action_id_data["data"]["divide_data"]["divide"]
                today_data = divide_data.get(self.today)
                self.activity_id_today, self.task_id_today, self.status_today = today_data["activity_id"], today_data[
                    "task_id"], today_data["status"]
                tomorrow_data = divide_data.get(self.tomorrow)
                self.activity_id_tomorrow, self.status_tomorrow, self.count_tomorrow = tomorrow_data["activity_id"], \
                    tomorrow_data["status"], tomorrow_data["button"]["count"]
                return True
        else:
            fn_print(f"===获取瓜分活动ID请求异常, {get_carve_up_action_id_response.text}===")

    async def apply_carve_up_action(self):
        """
        报名明天的瓜分福利金
        :return: 
        """
        apply_carve_up_action_response = await self.client.post(
            url="https://ut.xiaojukeji.com/ut/welfare/api/action/joinDivide",
            json={
                "token": self.token,
                "lat": self.lat,
                "lng": self.lng,
                "platform": "na",
                "env": '{}',
                "activity_id": self.activity_id_tomorrow,
                "count": self.count_tomorrow,
                "type": "ut_bonus"
            }
        )
        if apply_carve_up_action_response.status_code == 200:
            apply_carve_up_action_data = apply_carve_up_action_response.json()
            if apply_carve_up_action_data.get("errno") == 0:
                if apply_carve_up_action_data.get("data", {}).get("result"):
                    fn_print(f"用户【{self.user_phone}】, ===报名明日瓜分福利金成功🎉===")
                    return
            elif apply_carve_up_action_data.get("errno") == 1003:
                fn_print(f"用户【{self.user_phone}】, ===今日瓜分福利金已报名，无需重复报名！===")
                return
            else:
                fn_print(f"用户【{self.user_phone}】, ===报名明日瓜分福利金失败, {apply_carve_up_action_data}===")
                return
        else:
            fn_print(f"===报名明日瓜分福利金请求异常, {apply_carve_up_action_response.text}===")

    async def complete_carve_up_action(self):
        """
        完成今天的瓜分福利金，14点前完成
        :return: 
        """
        complete_carve_up_action_response = await self.client.post(
            url="https://ut.xiaojukeji.com/ut/welfare/api/action/divideReward",
            json={
                "token": self.token,
                "lat": self.lat,
                "lng": self.lng,
                "platform": "na",
                "env": '{}',
                "activity_id": self.activity_id_today,
                "task_id": self.task_id_today
            }
        )
        if complete_carve_up_action_response.status_code == 200:
            complete_carve_up_action_data = complete_carve_up_action_response.json()
            if complete_carve_up_action_data.get("errno") == 0:
                if complete_carve_up_action_data.get("data", {}).get("result"):
                    fn_print(f"用户【{self.user_phone}】, ===完成今日打卡瓜分福利金成功🎉===")
                    return
            elif complete_carve_up_action_data.get("errno") == 1003:
                fn_print(f"用户【{self.user_phone}】, ===今日瓜分福利金已完成，无需重复完成！===")
                return
            else:
                fn_print(f"用户【{self.user_phone}】, ===完成今日瓜分福利金失败, {complete_carve_up_action_data}===")
                return
        else:
            fn_print(f"===完成今日瓜分福利金请求异常, {complete_carve_up_action_response.text}===")

    async def inquire_benefits_details(self):
        """
        查询权益详情
        :return: 
        """
        benefits_details_response = await self.client.get(
            url="https://member.xiaojukeji.com/dmember/h5/privilegeLists",
            params={
                "token": self.token,
                "city_id": self.city_id
            }
        )
        if benefits_details_response.status_code == 200:
            benefits_details_data = benefits_details_response.json()
            if benefits_details_data.get("errno") == 0:
                privileges_list = benefits_details_data.get('data', {}).get('privileges', [])  # 我的权益列表
                return privileges_list
        else:
            fn_print(f"===查询权益详情请求异常, {benefits_details_response.text}===")

    async def receive_level_gift_week(self):
        """
        领取周周领券活动的优惠券
        :return: 
        """
        privileges_list = await self.inquire_benefits_details()
        for privilege in privileges_list:
            if privilege.get('name') not in ['周周领券'] or privilege.get('level_gift') is None:
                continue
            coupons_list = privilege.get('level_gift', {}).get('coupons', [])
            for coupon in coupons_list:
                status = coupon.get("status")  # 0: 未领取 1: 已使用 2: 未使用
                if status != 0:
                    continue
                batch_id = coupon.get("batch_id")
                fn_print(f"用户【“{self.user_phone}】, ===开始领取{coupon.get('remark')}{coupon.get('coupon_title')}===")
                receive_level_gift_response = await self.client.get(
                    url=f"https://member.xiaojukeji.com/dmember/h5/receiveLevelGift?xbiz=&prod_key=wyc-vip-level&xpsid=&dchn=&xoid=&xenv=passenger&xspm_from=&xpsid_root=&xpsid_from=&xpsid_share=&token={self.token}&batch_id={batch_id}&env={{}}&gift_type=1&city_id={self.city_id}"
                )
                if receive_level_gift_response.status_code == 200:
                    receive_level_gift_data = receive_level_gift_response.json()
                    if receive_level_gift_data.get("errno") == 0:
                        fn_print(f"用户【“{self.user_phone}】, ===领取成功🎉===")
                        continue
                    else:
                        fn_print(f"用户【“{self.user_phone}】, ===领取失败, {receive_level_gift_data}===")
                else:
                    fn_print(f"===领取周周领券请求异常, {receive_level_gift_response.text}===")

    async def receive_level_gift_month(self):
        """
        领取月月领券活动的优惠券
        :return: 
        """
        if not MONTH_SIGNAL:
            fn_print(f"用户【“{self.user_phone}】, ===月月领券活动未开启===")
            return
        privileges_list = await self.inquire_benefits_details()
        for privilege in privileges_list:
            if privilege.get('name') not in ['月月领券'] or privilege.get('level_gift') is None:
                continue
            coupons_list = privilege.get('level_gift', {}).get('coupons', [])
            for coupon in coupons_list:
                status = coupon.get("status")  # 0: 未领取 1: 已使用 2: 未使用
                if status != 0:
                    continue
                batch_id = coupon.get("batch_id")
                fn_print(f"用户【“{self.user_phone}】, ===开始领取{coupon.get('remark')}{coupon.get('coupon_title')}===")
                receive_level_gift_response = await self.client.get(
                    url=f"https://member.xiaojukeji.com/dmember/h5/receiveLevelGift?xbiz=&prod_key=wyc-vip-level&xpsid=&dchn=&xoid=&xenv=passenger&xspm_from=&xpsid_root=&xpsid_from=&xpsid_share=&token={self.token}&batch_id={batch_id}&env={{}}&gift_type=1&city_id={self.city_id}"
                )
                if receive_level_gift_response.status_code == 200:
                    receive_level_gift_data = receive_level_gift_response.json()
                    if receive_level_gift_data.get("errno") == 0:
                        fn_print(f"用户【“{self.user_phone}】, ===领取成功🎉===")
                        continue
                    else:
                        fn_print(f"用户【“{self.user_phone}】, ===领取失败, {receive_level_gift_data}===")
                else:
                    fn_print(f"===领取月月领券请求异常, {receive_level_gift_response.text}===")

    async def swell_coupon(self):
        """
        膨胀周周领券活动的优惠券
        :return: 
        """
        privileges_list = await self.inquire_benefits_details()
        for privilege in privileges_list:
            if privilege.get("name") in ["周周领券", "月月领券"]:
                if privilege.get('level_gift') is None:
                    continue
                coupons_list = privilege.get('level_gift', {}).get('coupons', [])
                for coupon in coupons_list:
                    swell_status = coupon.get('swell_status')  # 0代表不能膨胀，1代表能膨胀,2代表已膨胀、
                    if swell_status == 1:
                        fn_print(
                            f"用户【“{self.user_phone}】, ===开始膨胀{coupon.get('remark')}{coupon.get('coupon_title')}===")
                    batch_id = coupon.get("batch_id")
                    coupon_id = coupon.get("coupon_id")
                    swell_coupon_response = await self.client.post(
                        url=f"https://member.xiaojukeji.com/dmember/h5/swell_coupon?city_id={self.city_id}",
                        json={
                            "token": self.token,
                            "batch_id": batch_id,
                            "coupon_id": coupon_id,
                            "city_id": self.city_id
                        }
                    )
                    if swell_coupon_response.status_code == 200:
                        swell_coupon_data = swell_coupon_response.json()
                        if swell_coupon_data.get("errno") == 0:
                            if swell_coupon_data.get("data", {}).get("is_swell"):
                                fn_print(f"用户【“{self.user_phone}】, ===膨胀成功🎉===")
                                continue
                            else:
                                fn_print(f"用户【“{self.user_phone}】, ===膨胀失败, {swell_coupon_data}===")
                        else:
                            fn_print(f"用户【“{self.user_phone}】, ===膨胀失败, {swell_coupon_data}===")
                    else:
                        fn_print(f"===膨胀周周领券请求异常, {swell_coupon_response.text}===")

    async def receive_travel_insurance(self):
        """
        领取行程意外险
        :return: 
        """
        privileges_list = await self.inquire_benefits_details()
        for privilege in privileges_list:
            if privilege.get('name') == "行程意外险":
                need_received = privilege.get('need_received')
                if need_received == 1:  # 0为未领取，1为已领取
                    fn_print(f"用户【“{self.user_phone}】, ===已经领取过了行程意外险===")
                    return
                elif need_received == 0:
                    fn_print(f"用户【“{self.user_phone}】, ===开始领取行程意外险===")
                    receive_travel_insurance_response = await self.client.post(
                        url="https://member.xiaojukeji.com/dmember/h5/bindPrivilege",
                        json={"token": self.token, "type": 3}
                    )
                    if receive_travel_insurance_response.status_code == 200:
                        receive_travel_insurance_data = receive_travel_insurance_response.json()
                        if receive_travel_insurance_data.get("errno") == 0:
                            fn_print(f"用户【“{self.user_phone}】, ===领取行程意外险成功🎉===")
                        else:
                            fn_print(
                                f"用户【“{self.user_phone}】, ===领取行程意外险失败, {receive_travel_insurance_data}===")
                    else:
                        fn_print(f"===领取行程意外险请求异常, {receive_travel_insurance_response.text}===")

    async def receive_memberday_discount_multi(self):
        """
        领取周三折上折权益
        :return: 
        """
        privileges_list = await self.inquire_benefits_details()
        for privilege in privileges_list:
            if privilege.get('name') == "周三折上折":
                need_received = privilege.get('need_received')
                if need_received == 1:  # 0为未领取，1为已领取
                    fn_print(f"用户【“{self.user_phone}】, ===已经领取过了周三折上折===")
                    return
                elif need_received == 0:
                    fn_print(f"用户【“{self.user_phone}】, ===开始领取周三折上折===")
                    receive_memberday_discount_multi_response = await self.client.post(
                        url="https://member.xiaojukeji.com/dmember/h5/receiveMemberDayDiscount",
                        json={"token": self.token, "privilege_type": 1}
                    )
                    if receive_memberday_discount_multi_response.status_code == 200:
                        receive_memberday_discount_multi_data = receive_memberday_discount_multi_response.json()
                        if receive_memberday_discount_multi_data.get("errno") == 0:
                            fn_print(f"用户【“{self.user_phone}】, ===领取周三折上折成功🎉===")
                            return
                        else:
                            fn_print(
                                f"用户【“{self.user_phone}】, ===领取周三折上折失败, {receive_memberday_discount_multi_data}===")
                    else:
                        fn_print(f"===领取周三折上折请求异常, {receive_memberday_discount_multi_response.text}===")

    async def receive_wyc_order_finish(self):
        """
        领取气泡奖励完单返福利金
        :return: 
        """
        get_bubble_response = await self.client.post(
            url="https://ut.xiaojukeji.com/ut/welfare/api/home/getBubble",
            json={
                "token": self.token,
                "lat": self.lat,
                "lng": self.lng,
                "platform": "na",
                "env": "{}"
            }
        )
        get_bubble_data = get_bubble_response.json()
        bubble_list = get_bubble_data.get('data', {}).get('bubble_list', [])
        for bubble in bubble_list:
            if bubble.get('pre_content') == "完单返":
                cycle_id = bubble.get('cycle_id')
                reward_count = bubble.get('reward_count')
                receive_wyc_order_finish_response = await self.client.post(
                    url="https://ut.xiaojukeji.com/ut/welfare/api/action/clickBubble",
                    json={
                        "token": self.token,
                        "lat": self.lat,
                        "lng": self.lng,
                        "platform": "na",
                        "env": "{}",
                        "cycle_id": cycle_id,
                        "bubble_type": "wyc_order_finish"
                    }
                )
                if receive_wyc_order_finish_response.status_code == 200:
                    receive_wyc_order_finish_data = receive_wyc_order_finish_response.json()
                    if receive_wyc_order_finish_data.get("errno") == 0:
                        fn_print(
                            f"用户【“{self.user_phone}】, ===领取气泡奖励完单返福利金成功🎉, 获得{reward_count}福利金！===")
                        return
                    else:
                        fn_print(
                            f"用户【“{self.user_phone}】, ===领取气泡奖励完单返福利金失败, {receive_wyc_order_finish_data}===")
                else:
                    fn_print(f"===领取气泡奖励完单返福利金请求异常, {receive_wyc_order_finish_response.text}===")

    async def claim_coupon_check_in(self):
        """
        领取天天神券签到
        :return: 
        """
        claim_coupon_check_in_response = await self.client.post(
            url="https://ut.xiaojukeji.com/ut/janitor/api/action/sign/do",
            headers={'Didi-Ticket': self.token}
        )
        if claim_coupon_check_in_response.status_code == 200:
            claim_coupon_check_in_data = claim_coupon_check_in_response.json()
            if claim_coupon_check_in_data.get("errno") == 0:
                current_progress = claim_coupon_check_in_data.get("data").get("current_progress")
                total_progress = claim_coupon_check_in_data.get("data").get("total_progress")
                fn_print(
                    f"用户【“{self.user_phone}】, ===领取天天神券签到成功🎉签到进度：{current_progress}/{total_progress}===")
                return
            else:
                fn_print(f"用户【“{self.user_phone}】, ===领取天天神券签到失败, {claim_coupon_check_in_data}===")
        else:
            fn_print(f"===领取天天神券签到请求异常, {claim_coupon_check_in_response.text}===")

    async def claim_coupon_lottery(self):
        """
        天天神券抽奖
        :return: 
        """
        get_draw_times_response = await self.client.post(
            url="https://api.didi.cn/webx/chapter/product/init",
            headers={'Didi-Ticket': self.token},
            json={
                "dchn": "dKlklLa",
                "args": {
                    "runtime_args":
                        {
                            "token": self.token,
                            "lat": self.lat,
                            "lng": self.lng,
                            "env": {},
                            "platform": "na",
                            "Didi-Ticket": self.token,
                        }
                }
            }
        )
        if get_draw_times_response.status_code == 200:
            get_draw_times_data = get_draw_times_response.json()
            lottery_chance = get_draw_times_data.get('data').get('conf').get('strategy_data').get('data').get(
                'lottery_chance')
            act_id = get_draw_times_data.get('data').get('conf').get('ext').get('act_conf').get('act_id')
            for _ in range(lottery_chance):
                lucky_draw_response = await self.client.post(
                    url="https://ut.xiaojukeji.com/ut/janitor/api/action/lottery/doLottery",
                    headers={'Didi-Ticket': self.token},
                    json={
                        "act_id": act_id
                    }
                )
                lucky_draw_data = lucky_draw_response.json()
                if lucky_draw_data.get("errno") == 0:
                    fn_print(
                        f"用户【“{self.user_phone}】, ===抽奖成功🎉, 获得{lucky_draw_data.get('data').get('prize_data')[0].get('name')}===")
                    await asyncio.sleep(5)
                    continue
                else:
                    fn_print(f"用户【“{self.user_phone}】, ===天天神券抽奖失败, {lucky_draw_data}===")
                    return
        else:
            fn_print(f"===天天神券获取抽奖次数请求异常, {get_draw_times_response.text}===")

    async def run_scratch(self):
        """
        运行刮刮乐
        :return: 
        """
        if await self.get_carve_up_action_id():
            fn_print(f"用户【“{self.user_phone}】, ===开始完成今日瓜分活动===")
            if self.status_today == 2:
                await self.complete_carve_up_action()
            elif self.status_today == 3:
                fn_print(f"用户【“{self.user_phone}】, ===今日瓜分活动已完成，无需重复完成！===")
            elif self.status_today == 4:
                fn_print(f"用户【“{self.user_phone}】, ===今日已领取瓜分活动奖励！===")
            else:
                fn_print(f"用户【“{self.user_phone}】, ===今日瓜分活动完成失败！肯昨日未报名！===")
            fn_print(f"用户【“{self.user_phone}】, ===开始报名明日瓜分活动===")
            if self.status_tomorrow == 1:
                await self.apply_carve_up_action()
            elif self.status_tomorrow == 2:
                fn_print(f"用户【“{self.user_phone}】, ===明日瓜分活动已报名，无需重复报名！===")
            else:
                fn_print(f"用户【“{self.user_phone}】, ===明日瓜分活动报名失败！===")

    async def today_pick(self):
        """
        每日精选
        :return: 
        """
        get_batch_config_response = await self.client.post(
            url="https://api.didi.cn/webx/chapter/page/batch/config",
            headers={'Didi-Ticket': self.token},
            json={
                "dchn": "PxJanq9",
                "args": [
                    {"dchn": "kkXgpzO",
                     "prod_key": "ut-limited-seckill",
                     "runtime_args":
                         {
                             "token": self.token,
                             "lat": self.lat,
                             "lng": self.lng,
                             "env": {},
                             "Didi-Ticket": self.token,
                         }
                     },
                    {"dchn": "gL3E8qZ",
                     "prod_key": "ut-support-coupon",
                     "runtime_args": {
                         "token": self.token,
                         "lat": self.lat,
                         "lng": self.lng,
                         "env": {},
                         "Didi-Ticket": self.token}
                     }
                ]
            }
        )
        if get_batch_config_response.status_code == 200:
            get_batch_config_data = get_batch_config_response.json()
            activity_list = get_batch_config_data.get("data").get("conf")
            for activity in activity_list:
                if activity.get("dchn") == "gL3E8qZ":
                    fn_print(f"用户【“{self.user_phone}】, ===开始领取每日精选===")
                    coupons_list = activity.get("strategy_data").get("data").get("daily_coupon").get("coupons")
                    coupons_status_name_dict = {
                        '1': '可领取',
                        '2': '已经领取',
                        '4': '已抢光',
                        '6': '待前置条件完成'
                    }
                    for coupon_index, coupon in enumerate(coupons_list):
                        coupons_name = coupon.get("name")
                        coupons_status = coupon.get("status")  # 1为可领取 2为已经领取 4为抽奖抢券
                        fn_print(f"==={coupon_index + 1}.券名：{coupons_name} "
                                 f"状态：{coupons_status_name_dict.get(str(coupons_status))}===")
                        if coupons_status == 1:
                            fn_print(f"===开始领取券：{coupons_name}===")
                            activity_id = coupon.get("activity_id")
                            if coupons_name == "打车5元券":
                                fn_print(f"用户【{self.user_phone}】, ===【打车5元券】为分享助力才能领券，不支持自动领券===")
                                continue
                            if activity_id == "10010":
                                fn_print(
                                    f"用户【{self.user_phone}】, ===该券为明天在目的地栏搜“领券”必得1张快车优惠券，不支持自动领取===")
                                continue
                            group_id = coupon.get("group_id")
                            coupon_conf_id = coupon.get("coupon_conf_id")
                            group_date = coupon.get("group_date")
                            bind_coupon_response = await self.client.post(
                                url="https://ut.xiaojukeji.com/ut/janitor/api/action/coupon/bind",
                                headers={'Didi-Ticket': self.token},
                                json={
                                    'group_date': group_date,
                                    "activity_id": activity_id,
                                    "group_id": group_id,
                                    "coupon_conf_id": coupon_conf_id
                                }
                            )
                            bind_coupon_data = bind_coupon_response.json()
                            if bind_coupon_data.get("errno") == 0:
                                fn_print(f"用户【{self.user_phone}】, ===领取成功🎉===")
                                await asyncio.sleep(0.5)
                                continue
                            else:
                                fn_print(f"用户【{self.user_phone}】, ===领取失败，{bind_coupon_data}===")
                                return
                if activity.get("dchn") == "kkXgpzO":
                    fn_print(f"用户【“{self.user_phone}】, ===开始领取限时抢===")
                    seckill_list = activity.get("strategy_data").get("data").get("seckill")  # 秒杀列表
                    seckill_status_name_dict = {
                        '1': '正在热抢',
                        '2': '即将开始',
                        '3': '已经开抢'
                    }
                    coupons_status_name_dict = {
                        '1': '可领取',
                        '2': '已经领取',
                        '4': '抽奖抢券',
                        '5': '未到时间'
                    }
                    for seckill in seckill_list:
                        seckill_name = seckill.get("start_at")
                        seckill_status = int(seckill.get("status"))  # 1为正在热抢 2为即将开始 3为已经开抢
                        fn_print(f"☆☆场次：{seckill_name} 状态：{seckill_status_name_dict[str(seckill_status)]}")
                        if seckill_status in [1, 3]:
                            coupons_list = seckill.get("coupons")
                            for coupon_index, coupon in enumerate(coupons_list):
                                coupons_name = coupon.get("name")
                                coupons_status = coupon.get("status")  # 1为可领取 2为已经领取 4为抽奖抢券
                                fn_print(f"==={coupon_index + 1}.券名：{coupons_name} "
                                         f"状态：{coupons_status_name_dict.get(str(coupons_status))}===")
                                if coupons_status == 1:
                                    fn_print(f"===开始领取券：{coupons_name}===")
                                    activity_id = coupon.get("activity_id")
                                    group_id = coupon.get("group_id")
                                    coupon_conf_id = coupon.get("coupon_conf_id")
                                    group_date = coupon.get("group_date")
                                    bind_coupon_response = await self.client.post(
                                        url="https://ut.xiaojukeji.com/ut/janitor/api/action/coupon/bind",
                                        headers={'Didi-Ticket': self.token},
                                        json={
                                            "activity_id": activity_id,
                                            "group_id": group_id,
                                            'group_date': group_date,
                                            "coupon_conf_id": coupon_conf_id
                                        }
                                    )
                                    bind_coupon_data = bind_coupon_response.json()
                                    if bind_coupon_data.get("errno") == 0:
                                        fn_print(f"用户【{self.user_phone}】, ===领取成功🎉===")
                                        await asyncio.sleep(0.5)
                                        continue
                                    else:
                                        fn_print(f"用户【{self.user_phone}】, ===领取失败，{bind_coupon_data}===")
                                        return
        else:
            fn_print(f"===每日精选请求异常， {get_batch_config_response.text}===")

    async def run(self):
        await self.get_user_info()
        fn_print(f"用户【{self.user_phone}】, ===当前福利金数量为：{await self.get_welfare_payments()}===")
        task = [
            self.today_pick(),
            self.sign_in(),
            self.run_scratch(),
            self.receive_level_gift_week(),
            self.receive_level_gift_month(),
            self.swell_coupon(),
            self.receive_travel_insurance(),
            self.receive_memberday_discount_multi(),
            self.receive_wyc_order_finish(),
            self.claim_coupon_check_in(),
            self.claim_coupon_lottery()
        ]
        await asyncio.gather(*task)
        fn_print(f"用户【{self.user_phone}】, ===当前福利金数量为：{await self.get_welfare_payments()}===")


async def main():
    task = []
    for token in dd_tokens:
        dd = DiDi(token)
        task.append(dd.run())
    await asyncio.gather(*task)


if __name__ == '__main__':
    asyncio.run(main())
