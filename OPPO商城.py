# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         OPPO商城.py
# @author           Echo
# @EditTime         2025/4/24
# const $ = new Env('OPPO商城');
# cron: 0 0 12 * * *
"""
OPPO商城app版：
    开启抓包进入'OPPO商城'app，进入我的 - 签到任务
    变量oppo_cookie，抓包https://hd.opposhop.cn请求头中的 Cookie，整个Cookie都放进来 
    oppo_cookie变量格式： Cookie#user_agent#oppo_level   ，多个账号用@隔开
    user_agent，请求头的User-Agent
    oppo_level， 用户等级。值只能定义为 普卡、银卡会员、金钻会员

OPPO商城小程序版：
    开启抓包进入'OPPO商城小程序'，进入签到任务
    变量oppo_applet_cookie，抓包https://hd.opposhop.cn请求头中的 Cookie，整个Cookie都放进来 
    oppo_applet_cookie变量格式： Cookie   ，多个账号用@隔开

OPPO商城服务版：
    开启抓包进入'OPPO服务小程序'，抓包cookie
    变量oppo_service_cookie，将整个cookie放进来
    oppo_service_cookie变量格式： Cookie值   ，多个账号用@隔开
"""
import random
from urllib.parse import urlparse, parse_qs

import httpx
import json
import re
import time

from datetime import datetime
from fn_print import fn_print
from get_env import get_env
from sendNotify import send_notification_message_collection
from activity_base import BaseActivity, ACTIVITY_CONFIG

oppo_cookies = get_env("oppo_cookie", "@")
oppo_applet_cookies = get_env("oppo_applet_cookie", "@")
oppo_service_cookies = get_env("oppo_service_cookie", "@")
is_luckyDraw = True  # 是否开启抽奖


class OppoAppActivity(BaseActivity):
    def __init__(self, cookie, task_config):
        self.user_name = None
        self.cookie = cookie.split("#")[0]
        self.user_agent = cookie.split("#")[1]
        self.level = self.validate_level(cookie.split("#")[2])
        self.oppo_list = re.split(r'[\n&]', cookie) if cookie else []
        self.sign_in_days_map = {}
        headers = {
            'User-Agent': self.user_agent,
            'Accept-Encoding': 'gzip, deflate',
            'Accept': "application/json, text/plain, */*",
            'Content-Type': 'application/json',
            'Cookie': self.cookie
        }
        self.client = httpx.Client(base_url="https://hd.opposhop.cn", verify=False, headers=headers, timeout=60)
        super().__init__(self.client, task_config)
        self.sign_in_map = {}

    def validate_level(self, level):
        valid_levels = ["普卡", "银卡会员", "金钻会员"]
        if level not in valid_levels:
            fn_print(f"❌环境变量oppo_level定义的会员等级无效，只能定义为：{valid_levels}")
            return None
        return level

    def get_sign_in_detail(self):
        """ 获取累计签到天数信息 """
        response = self.client.get(
            url=f"/api/cn/oapi/marketing/cumulativeSignIn/getSignInDetail?activityId={self.sign_in_map.get(self.level)}"
        )
        response.raise_for_status()
        data = response.json()
        sign_in_days_map = {}
        if data.get('code') == 200 and data.get('data').get('cumulativeAwards'):
            cumulative_awards: list = data.get('data').get('cumulativeAwards')
            for cumulative_award in cumulative_awards:
                sign_in_days_map[cumulative_award['awardId']] = (cumulative_award['signDayNum'],
                                                                 cumulative_award['status'])
            return sign_in_days_map
        else:
            fn_print("获取累计签到天数信息失败❌")
            return None

    def get_activity_info(self):
        bp_url = self.config['bp_url']
        # 判断是否需要先动态获取url
        if isinstance(bp_url, dict):
            url = self.get_activity_url(bp_url['url'], bp_url['activity_area'], bp_url['activity_name'])
            if not url:
                fn_print("任务配置存在问题，未获取到活动入口url，跳过该任务")
                return
        else:
            url = bp_url
        try:
            response = self.client.get(url=url)
            response.raise_for_status()
            html = response.text
            # 使用正则表达式提取活动ID
            pattern = r'window\.__DSL__\s*=\s*({.*?});'
            match = re.search(pattern, html, re.DOTALL)
            if not match:
                fn_print(f"未找到{self.config['raffle_name']}活动的DSL数据， 请检查活动是否结束!")
                return
            dsl_json = json.loads(match.group(1))
            task_cmps = dsl_json.get("cmps")
            signin_fields = [cmp for cmp in task_cmps if "SignIn" in cmp]
            task_field = next((cmp for cmp in task_cmps if "Task" in cmp), None)
            if not task_field:
                fn_print("⚠️未找到任务组件")
                return

            try:
                self.activity_id = dsl_json['byId'][task_field]['attr']['taskActivityInfo']['activityId']
            except KeyError:
                fn_print("⚠️任务ID解析失败")
                return
            for sign_in_field in signin_fields:
                try:
                    activity_name = dsl_json['byId'][sign_in_field]['attr']['activityInfo']['activityName']
                    if self.level in activity_name:
                        self.sign_in_map.update({
                            self.level: dsl_json['byId'][sign_in_field]['attr']['activityInfo']['activityId']
                        })
                        break
                    else:
                        self.sign_in_activity_id = dsl_json['byId'][sign_in_field]['attr']['activityInfo']['activityId']
                except KeyError:
                    fn_print(f"⚠️签到组件 {sign_in_field} 解析失败")
                    continue
            self.jimuld_id = dsl_json['activityId']
        except Exception as e:
            fn_print(f"获取{self.config['raffle_name']}活动ID时出错: {e}")

    def get_user_info(self):
        response = self.client.get(
            url="/api/cn/oapi/users/web/member/check?unpaid=0"
        )
        response.raise_for_status()
        data = response.json()
        if data['code'] == 200:
            self.user_name = "OPPO会员: " + data['data']['name']

    def sign_in(self):
        sign_in_data = self.client.get(
            url=f"/api/cn/oapi/marketing/cumulativeSignIn/getSignInDetail?activityId={self.sign_in_map.get(self.level)}").json()
        sign_in_status: bool = sign_in_data.get('data').get('todaySignIn')
        if sign_in_status:
            fn_print(f"今天已经签到过啦，明天再来吧~")
            return
        try:
            response = self.client.post(
                url="https://hd.opposhop.cn/api/cn/oapi/marketing/cumulativeSignIn/signIn",
                json={
                    "activityId": self.sign_in_map.get(self.level)
                }
            )
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 200:
                fn_print(f"✅签到成功！获得积分： {data.get('data').get('awardValue')}")
            elif data.get('code') == 5008:
                fn_print(data.get('message'))
            else:
                fn_print(f"❌签到失败！{data.get('message')}")
        except Exception as e:
            fn_print(f"❌签到时出错: {e}")

    def get_sku_ids(self):
        config_response = self.client.get(url="https://msec.opposhop.cn/configs/web/advert/220031")
        config_response.raise_for_status()
        if config_response.status_code != 200:
            fn_print(f"❌获取商品信息失败！{config_response.text}")
            return []
        config_data = config_response.json()
        sku_ids = set()
        for module in config_data.get('data', []):
            for detail in module.get('details', []):

                link = detail.get('link', '')
                if 'skuId=' in link:
                    parsed_url = urlparse(link)
                    query_params = parse_qs(parsed_url.query)
                    sku_id = query_params.get("skuId", [None])[0]
                    if sku_id:
                        sku_ids.add(int(sku_id))

                hot_zone = detail.get("hotZone", {})
                for subscribe in hot_zone.get("hotZoneSubscribe", []):
                    sku_id = subscribe.get("skuId")
                    if sku_id:
                        sku_ids.add(int(sku_id))

                goods_form = detail.get('goodsForm', {})
                sku_id = goods_form.get('skuId')
                if sku_id:
                    sku_ids.add(int(sku_id))
        return list(sku_ids)

    def browse_products(self, goods_num):
        sku_ids = self.get_sku_ids()
        random.shuffle(sku_ids)
        for sku_id in sku_ids[:goods_num]:
            try:
                response = self.client.get(
                    url=f"https://msec.opposhop.cn/cms-business/goods/detail?interfaceVersion=v2&pageCode=skuDetail&modelCode=OnePlus%20PJZ110&skuId={sku_id}"
                )
                response.raise_for_status()
                data = response.json()
                if data.get('code') != 200 and data.get('message'):
                    fn_print(f"❌浏览商品失败！{data.get('message')}")
            except Exception as e:
                fn_print(f"❌浏览商品时出错: {e}")

    def get_sign_days(self):
        """ 获取签到天数 """
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/cumulativeSignIn/getSignInDetail?activityId={self.sign_in_map.get(self.level)}"
            )
            response.raise_for_status()
            data = response.json()
            if data.get('data'):
                sign_in_day_num = data.get('data').get('signInDayNum')
                fn_print(f"已连续签到{sign_in_day_num}天")
                return sign_in_day_num
            else:
                fn_print(f"获取签到天数失败！-> {data}")
                return None
        except Exception as e:
            fn_print(f"获取签到天数时出错: {e}")
            return None

    def receive_sign_in_award(self, award_id):
        """ 领取签到奖励 """
        try:
            response = self.client.post(
                url=f"/api/cn/oapi/marketing/cumulativeSignIn/drawCumulativeAward",
                json={
                    "activityId": self.sign_in_map.get(self.level),
                    "awardId": award_id
                }
            )
            response.raise_for_status()
            data = response.json()
            if data.get('data'):
                days, status = self.sign_in_days_map.get(award_id)
                award_value = data.get('data').get('awardValue')
                if len(award_value.strip()) > 0:
                    fn_print(f"领取累计{days}天签到奖励成功！获得积分： {award_value}")
                else:
                    fn_print(f"领取累计{days}天签到奖励成功！获得： {award_value}")
            else:
                fn_print(f"领取连续签到奖励失败！-> {data.get('message')}")
        except Exception as e:
            fn_print(f"领取连续签到奖励时出错: {e}")

    def handle_sign_in_awards(self):
        """ 处理领取累计签到奖励 """
        sign_in_day_num = self.get_sign_days()
        sign_in_days_map = self.get_sign_in_detail()
        if sign_in_day_num is None or sign_in_days_map is None:
            return
        # 领取所有可领取的累计签到奖励
        for award_id, (sign_day_num, status) in sign_in_days_map.items():
            if status == 2:  # 2代表可领取
                self.receive_sign_in_award(award_id)

        # 如果今天的签到天数正好有奖励，且未领取，则领取
        for award_id, (sign_day_num, status) in sign_in_days_map.items():
            if sign_day_num == sign_in_day_num and status == 2:
                self.receive_sign_in_award(award_id)
                break

    def run(self):
        if self.level is None:
            return

        self.get_activity_info()  # 统一入口
        self.sign_in()
        self.handle_sign_in_awards()
        self.handle_task()
        draw_count = self.get_draw_count()
        for _ in range(draw_count):
            self.draw_lottery()
            time.sleep(1.5)


class OppoAppletActivity(BaseActivity):
    def __init__(self, g_applet_cookie, task_config):
        self.user_name = None
        self.g_applet_cookie = g_applet_cookie
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090c33)XWEB/11581",
            'Accept-Encoding': 'gzip, deflate',
            'Accept': "application/json, text/plain, */*",
            'Content-Type': 'application/json',
            'Cookie': self.g_applet_cookie
        }
        import httpx
        self.client = httpx.Client(base_url="https://hd.opposhop.cn", verify=False, headers=headers, timeout=60)
        super().__init__(self.client, task_config)



if __name__ == '__main__':
    if oppo_cookies:
        for task_key, task_config in ACTIVITY_CONFIG.get("oppo_app", {}).items():
            for cookie in oppo_cookies:
                fn_print(f"=======开始执行APP任务=======")
                oppo_app = OppoAppActivity(cookie, task_config)
                oppo_app.run()
    else:
        fn_print("‼️未配置OPPO商城APP的Cookie，跳过OPPO商城APP签到‼️")

    if oppo_applet_cookies:
        for task_key, task_config in ACTIVITY_CONFIG.get('oppo_applet', {}).items():
            for cookie in oppo_applet_cookies:
                fn_print(f"=======开始执行小程序任务：{task_key} =======")
                oppo_applet = OppoAppletActivity(cookie, task_config)
                oppo_applet.run()
    else:
        fn_print("‼️未配置OPPO商城小程序的Cookie，跳过OPPO商城小程序签到‼️")

    if oppo_service_cookies:
        from oppo_service import OppoServiceActivity
        for cookie in oppo_service_cookies:
            oppo_service = OppoServiceActivity(cookie)
            oppo_service.run()
    else:
        fn_print("‼️未配置OPPO服务的Cookie，跳过OPPO服务签到‼️")
    send_notification_message_collection(f"OPPO商城&OPPO服务签到通知 - {datetime.now().strftime('%Y/%m/%d')}")
