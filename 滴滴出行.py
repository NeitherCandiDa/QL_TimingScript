# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         滴滴出行.py
# @author           Echo
# @EditTime         2024/11/27
import asyncio
import datetime
import json
import os

import httpx

from fn_print import fn_print
from get_env import get_env

MONTH_SIGNAL = False  # 月月领券

os.environ["DD_TOKENS"] = (
    "vGSy4Bj6JeK_nhaF9ZLs1qzRbv86UYv80UiRXgAenI0kzD2OAjEMQOG7vNoa2YmTSdxuv3fYheGnCRKIasTdUaB9evp2hhLkRRdFGEaYMBJhqqrCyEQu1ryk1HR1n80JW129u-vcC8HPL8IfAcI_ka3W0r33kq2bCUeiChux87g974eN0JdwmlROq7UPdSawVlpqJaWaES5f8jr3dwAAAP__"
)
dd_tokens = get_env("DD_TOKENS", "&")


class DiDi:
    LAT = "30.707130422009786"  # 纬度
    LNG = "104.09652654810503"  # 经度
    CITY_ID = 17  # 城市id

    def __init__(self, token, city_id=CITY_ID, lat=LAT, lng=LNG):
        self.blance = None
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
            self.blance = get_info_data['data']['balance']
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
                status = coupon.get("status")   # 0: 未领取 1: 已使用 2: 未使用
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
                status = coupon.get("status")   # 0: 未领取 1: 已使用 2: 未使用
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
                        fn_print(f"用户【“{self.user_phone}】, ===开始膨胀{coupon.get('remark')}{coupon.get('coupon_title')}===")
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
                            fn_print(f"用户【“{self.user_phone}】, ===领取行程意外险失败, {receive_travel_insurance_data}===")
                    else:
                        fn_print(f"===领取行程意外险请求异常, {receive_travel_insurance_response.text}===")


    async def run(self):
        await self.get_user_info()
        task = [
            # self.sign_in(),
            self.get_carve_up_action_id(),
            self.apply_carve_up_action(),
            self.complete_carve_up_action(),
        ]
        await asyncio.gather(*task)
        # await self.get_welfare_payments()


async def main():
    task = []
    for token in dd_tokens:
        dd = DiDi(token)
        task.append(dd.run())
    await asyncio.gather(*task)


if __name__ == '__main__':
    asyncio.run(main())
