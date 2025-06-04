# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         OPPO商城.py
# @author           Echo
# @EditTime         2025/4/24
# const $ = new Env('OPPO商城');
# cron: 0 0 12 * * *
"""
OPPO商城app版：
    开启抓包进入‘OPPO商城’app，进入我的 - 签到任务
    变量oppo_cookie，抓包https://hd.opposhop.cn请求头中的 Cookie，整个Cookie都放进来 
    oppo_cookie变量格式： Cookie#user_agent#oppo_level   ，多个账号用@隔开
    user_agent，请求头的User-Agent
    oppo_level， 用户等级。值只能定义为 普卡、银卡会员、金钻会员

OPPO商城小程序版：
    开启抓包进入‘OPPO商城小程序’，进入签到任务
    变量oppo_applet_cookie，抓包https://hd.opposhop.cn请求头中的 Cookie，整个Cookie都放进来 
    oppo_applet_cookie变量格式： Cookie   ，多个账号用@隔开
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

oppo_cookies = get_env("oppo_cookie", "@")
oppo_applet_cookies = get_env("oppo_applet_cookie", "@")
is_luckyDraw = True  # 是否开启抽奖


class Oppo:
    def __init__(self, cookie):
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
        self.activity_id = None
        self.sign_in_map = {}

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
                sign_in_days_map[cumulative_award['awardId']] = cumulative_award['signDayNum']
            return sign_in_days_map
        else:
            fn_print("获取累计签到天数信息失败❌")
            return None

    def is_login(self):
        """ 检测Cookie是否有效 """
        try:
            response = self.client.get(url="/api/cn/oapi/marketing/task/isLogin")
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 403:
                fn_print("Cookie已过期或无效，请重新获取")
                return
        except Exception as e:
            fn_print(f"检测Cookie时出错: {e}")
            return

    def get_task_activity_info(self):
        try:
            response = self.client.get(
                url="/bp/b371ce270f7509f0"
            )
            response.raise_for_status()
            html = response.text
            # 使用正则表达式提取活动ID
            pattern = r'window\.__DSL__\s*=\s*({.*?});'
            match = re.search(pattern, html, re.DOTALL)
            if match:
                dsl_json = json.loads(match.group(1))
                task_cmps = dsl_json.get("cmps")
                signin_fields = []
                for cmp in task_cmps:
                    if "SignIn" in cmp:
                        signin_fields.append(cmp)
                    if "Task" in cmp:
                        task_field = cmp
                        break
                self.activity_id = dsl_json['byId'][task_field]['attr']['taskActivityInfo']['activityId']
                for signin_field in signin_fields:
                    if self.level in dsl_json['byId'][signin_field]['attr']['activityInfo']['activityName']:
                        self.sign_in_map.update({
                            self.level: dsl_json['byId'][signin_field]['attr']['activityInfo']['activityId']})
            else:
                fn_print("未找到活动ID")
        except Exception as e:
            fn_print(f"获取活动ID时出错: {e}")
        return None

    def get_task_list_ids(self):
        """ 获取任务列表 """
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/task/queryTaskList?activityId={self.activity_id}&source=c"
            )
            response.raise_for_status()
            data = response.json()
            if not data.get('data'):
                fn_print(f"获取任务列表失败！-> {data.get('message')}")
                return None
            task_list = data['data']['taskDTOList']
            for task in task_list:
                task_type = task.get('taskType')
                task_name = task.get('taskName')
                if task_type == 6:  # 黑卡任务
                    continue
                fn_print(f"开始处理【{task_name}】任务")
                if task_type == 3:
                    goods_num = int(task.get('attachConfigOne', {}).get('goodsNum', 0))
                    if goods_num > 0:
                        self.browse_products(goods_num)
                        time.sleep(1.5)
                # 执行任务
                self.complete_task(task_name, task.get('taskId'), task.get('activityId'))
                time.sleep(1.5)
                # 领取奖励
                self.receive_reward(task_name, task.get('taskId'), task.get('activityId'))
                time.sleep(1.5)
        except Exception as e:
            fn_print(f"获取任务列表时出错: {e}")
        return None

    def complete_task(self, task_name, task_id, activity_id):
        """
        完成任务
        :param task_name: 任务名称
        :param task_id: 任务ID
        :param activity_id: 活动ID
        :return: 
        """
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/taskReport/signInOrShareTask?taskId={task_id}&activityId={activity_id}&taskType=1"
            )
            response.raise_for_status()
            data = response.json()
            if data.get('data'):
                fn_print(f"**{self.user_name}**，任务【{task_name}】完成！")
            else:
                fn_print(f"**{self.user_name}**，任务【{task_name}】失败！-> {data.get('message')}")
        except Exception as e:
            fn_print(f"完成任务时出错: {e}")

    def receive_reward(self, task_name, task_id, activity_id):
        """
        领取奖励
        :param task_name: 任务名称
        :param task_id: 任务ID
        :param activity_id: 活动ID
        :return:
        """
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/task/receiveAward?taskId={task_id}&activityId={activity_id}"
            )
            response.raise_for_status()
            data = response.json()
            if data.get('data'):
                fn_print(
                    f"**{self.user_name}**，任务【{task_name}】奖励领取成功！积分+{data.get('data').get('awardValue')}")
            else:
                fn_print(f"**{self.user_name}**，任务【{task_name}】-> {data.get('message')}")
        except Exception as e:
            fn_print(f"领取奖励时出错: {e}")

    def validate_level(self, level):
        """
        验证会员等级是否有效，如果无效则返回None
        :param level: 用户输入的会员等级
        :return: 有效的会员等级或None
        """
        valid_levels = ["普卡", "银卡会员", "金钻会员"]
        if level not in valid_levels:
            fn_print(f"❌环境变量oppo_level定义的会员等级无效，只能定义为：{valid_levels}")
            return None
        return level

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
            fn_print(f"**{self.user_name}**，今天已经签到过啦，明天再来吧~")
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
                fn_print(f"**{self.user_name}**，已连续签到{sign_in_day_num}天")
                return sign_in_day_num
            else:
                fn_print(f"**{self.user_name}**，获取签到天数失败！-> {data}")
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
                days = self.sign_in_days_map.get(award_id)
                award_value = data.get('data').get('awardValue')
                if len(award_value.strip()) > 0:
                    fn_print(f"**{self.user_name}**，领取累计{days}天签到奖励成功！获得积分： {award_value}")
                else:
                    fn_print(f"**{self.user_name}**，领取累计{days}天签到奖励成功！获得： {award_value}")
            else:
                fn_print(f"**{self.user_name}**，领取连续签到奖励失败！-> {data.get('message')}")
        except Exception as e:
            fn_print(f"领取连续签到奖励时出错: {e}")

    def handle_sign_in_awards(self):
        """ 处理领取累计签到奖励 """
        sign_in_day_num = self.get_sign_days()
        sign_in_days_map = self.get_sign_in_detail()
        if sign_in_day_num is None or sign_in_days_map is None:
            return
        if sign_in_day_num not in sign_in_days_map.values():
            return
        award_id = [k for k, v in sign_in_days_map.items() if v == sign_in_day_num][0]
        self.receive_sign_in_award(award_id)


class OppoApplet:
    def __init__(self, g_applet_cookie):
        self.g_applet_618mainVenue_jimuld_id = None
        self.g_applet_618mainVenue_raffle_id = None
        self.g_applet_full_time_jimuld_id = None
        self.g_applet_full_time_sign_in_activity_id = None
        self.g_applet_full_time_raffle_id = None
        self.g_applet_full_time_activity_id = None
        self.g_applet_ocean_jimuld_id = None
        self.g_applet_ocean_sign_in_activity_id = None
        self.g_applet_ocean_raffle_id = None
        self.g_applet_ocean_activity_id = None
        self.g_applet_reserva_shop_streamCode = None
        self.g_aapplet_reserva_shop_sku_id = None
        self.g_applet_reserva_shop_jimuld_id = None
        self.g_applet_reserva_shop_raffle_id = None
        self.g_applet_reserva_shop_activity_id = None
        self.g_applet_Sun_enterprise_jimuld_id = None
        self.g_applet_Sun_enterprise_raffle_id = None
        self.g_applet_Sun_enterprise_activity_id = None
        self.g_applet_CrayonShinChan_sign_in_activity_id = None
        self.g_applet_CrayonShinChan_jimuld_id = None
        self.g_applet_CrayonShinChan_raffle_id = None
        self.g_applet_CrayonShinChan_activity_id = None
        self.g_applet_champions_league_jimuld_id = None
        self.g_applet_champions_league_raffle_id = None
        self.g_applet_champions_league_sign_in_activity_id = None
        self.g_applet_champions_league_activity_id = None
        self.g_applet_618membership_subsidy_jimuld_id = None
        self.g_applet_618membership_subsidy_raffle_id = None
        self.g_applet_618membership_subsidy_activity_id = None
        self.g_applet_narrow_channel_jimuld_id = None
        self.g_applet_narrow_channel_raffle_id = None
        self.g_applet_narrow_channel_activity_id = None
        self.user_name = None
        self.g_applet_cookie = g_applet_cookie
        self.g_applet_activity_id = None
        self.g_applet_sign_in_activity_id = None
        self.g_applet_jimuld_id = None
        self.g_applet_raffle_id = None
        self.sign_in_day_num = None
        self.g_applet_accumulated_sign_in_reward_map = {}
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090c33)XWEB/11581",
            'Accept-Encoding': 'gzip, deflate',
            'Accept': "application/json, text/plain, */*",
            'Content-Type': 'application/json',
            'Cookie': self.g_applet_cookie
        }
        self.client = httpx.Client(base_url="https://hd.opposhop.cn", verify=False, headers=headers, timeout=60)

    def is_login(self):
        """ 检测Cookie是否有效 """
        try:
            response = self.client.get(url="/api/cn/oapi/marketing/task/isLogin")
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 403:
                fn_print("Cookie已过期或无效，请重新获取")
                return
        except Exception as e:
            fn_print(f"检测Cookie时出错: {e}")
            return

    def get_user_info(self):
        response = self.client.get(
            url="/api/cn/oapi/users/web/member/check?unpaid=0"
        )
        response.raise_for_status()
        data = response.json()
        if data['code'] == 200:
            self.user_name = "OPPO会员: " + data['data']['name']

    def get_activity_url(self, url, keyword1, keyword2):
        try:
            response = self.client.get(url=url)
            response.raise_for_status()
            data = response.json()
            if data.get('code') != 200:
                fn_print(f"获取活动信息失败！{data.get('message')}")
                return None
            datas = data.get('data')
            for data in datas:
                if keyword1 in data.get("title"):
                    for detail in data.get('details'):
                        if keyword2 in detail.get('title'):
                            return detail.get('link')
            return None
        except Exception as e:
            fn_print(f"获取活动信息时出错: {e}")
            return None

    def g_applet_get_task_activity_info(self):
        url = self.get_activity_url("https://msec.opposhop.cn/configs/web/advert/300003", "福利专区", "签到")
        if url is None:
            fn_print("获取活动信息异常，任务停止！")
            exit()
        try:
            response = self.client.get(
                url=url
            )
            response.raise_for_status()
            html = response.text
            # 使用正则表达式提取活动ID
            pattern = r'window\.__DSL__\s*=\s*({.*?});'
            match = re.search(pattern, html, re.DOTALL)
            if match:
                dsl_json = json.loads(match.group(1))
                task_cmps = dsl_json.get("cmps")
                for cmp in task_cmps:
                    if "SignIn" in cmp:
                        signin_field = cmp
                        continue
                    if "Raffle" in cmp:
                        raffle_field = cmp
                        continue
                    if "Task" in cmp:
                        task_field = cmp
                        continue
                self.g_applet_activity_id = dsl_json['byId'][task_field]['attr']['taskActivityInfo']['activityId']
                self.g_applet_sign_in_activity_id = dsl_json['byId'][signin_field]['attr']['activityInfo']['activityId']
                self.g_applet_jimuld_id = dsl_json['activityId']
                self.g_applet_raffle_id = dsl_json['byId'][raffle_field]['attr']['activityInformation']['raffleId']

        except Exception as e:
            fn_print(f"获取小程序活动ID时出错: {e}")

    def g_applet_get_task_list(self):
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/task/queryTaskList?activityId={self.g_applet_activity_id}&source=c"
            )
            response.raise_for_status()
            data = response.json()
            task_list_info = []
            if not data.get('data').get('taskDTOList'):
                fn_print(f"获取小程序任务列表失败！-> {data.get('message')}")
                return task_list_info
            for task in data.get('data').get('taskDTOList'):
                task_list_info.append(
                    {
                        "task_name": task.get('taskName'),
                        "task_id": task.get('taskId'),
                        "activity_id": task.get('activityId'),
                        "task_type": task.get('taskType'),
                        "browseTime": task.get('attachConfigOne').get('browseTime') if task.get(
                            'attachConfigOne') else None,
                    }
                )
            return task_list_info
        except Exception as e:
            fn_print(f"领取连续签到奖励时出错: {e}")
            return []

    def g_applet_sign_in(self):
        try:
            response = self.client.post(
                url=f"/api/cn/oapi/marketing/cumulativeSignIn/signIn",
                json={
                    "activityId": self.g_applet_sign_in_activity_id
                }
            )
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 200:
                fn_print(f"✅小程序签到成功！获得积分： {data.get('data').get('awardValue')}")
            elif data.get('code') == 5008:
                fn_print(data.get('message'))
            else:
                fn_print(f"❌小程序签到失败！{data.get('message')}")
        except Exception as e:
            fn_print(f"❌小程序签到时出错: {e}")

    def g_applet_todo_task_by_browse_page(self, task_name, task_id, activity_id, task_type):
        """ 完成浏览页面任务 """
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/taskReport/signInOrShareTask?taskId={task_id}&activityId={activity_id}&taskType={task_type}"
            )
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 200 and data.get('message') == '操作成功':
                fn_print(f"✅小程序任务【{task_name}】完成！")
            else:
                fn_print(f"❌小程序任务【{task_name}】失败！-> {data.get('message')}")
        except Exception as e:
            fn_print(f"完成小程序任务时出错: {e}")

    def g_applet_receive_reward(self, task_name, task_id, activity_id):
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/task/receiveAward?taskId={task_id}&activityId={activity_id}"
            )
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 200:
                fn_print(f"✅小程序任务【{task_name}】奖励领取成功！")
            else:
                fn_print(f"❌小程序任务【{task_name}】-> {data.get('message')}")
        except Exception as e:
            fn_print(f"领取小程序任务奖励时出错: {e}")

    def g_applet_handle_task(self):
        task_list = self.g_applet_get_task_list()
        for task in task_list:
            task_name = task.get('task_name')
            task_id = task.get('task_id')
            activity_id = task.get('activity_id')
            task_type = task.get('task_type')
            browse_time = task.get('browseTime')
            if task_type == 1:
                self.g_applet_todo_task_by_browse_page(task_name, task_id, activity_id, task_type)
                time.sleep(browse_time + 1)
                self.g_applet_receive_reward(task_name, task_id, activity_id)
            else:
                fn_print(f"小程序签到-暂不支持{task_type}类型任务，请向作者反馈‼️")
                continue

    def g_applet_get_draw_count(self, raffle_id):
        """ 获取剩余抽奖次数 """
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/raffle/queryRaffleCount?activityId={raffle_id}"
            )
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 200:
                draw_count = data.get('data').get('count')
                fn_print(f"剩余抽奖次数：{draw_count}")
                return draw_count
            else:
                fn_print(f"获取剩余抽奖次数失败！-> {data.get('message')}")
                return 0
        except Exception as e:
            fn_print(f"获取剩余抽奖次数时出错: {e}")
            return 0

    def g_applet_draw_raffle(self, activity_id, jimu_id, jimuName):
        """ 抽奖 """
        from urllib.parse import quote
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/raffle/clickRaffle?activityId={activity_id}&jimuId={jimu_id}&jimuName={quote(jimuName)}"
            )
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 200:
                fn_print(f"\t\t>>> 抽奖结果: {data.get('data').get('raffleWinnerVO').get('exhibitAwardName')}")
            else:
                fn_print(f"\t\t>>> 抽奖失败！-> {data.get('message')}")
        except Exception as e:
            fn_print(f"\t\t>>> 抽奖时出错: {e}")

    def g_applet_get_sign_in_detail(self):
        """ 获取签到天数和累计签到奖励 """
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/cumulativeSignIn/getSignInDetail?activityId={self.g_applet_sign_in_activity_id}"
            )
            response.raise_for_status()
            data = response.json()
            g_applet_accumulated_sign_in_reward_map = {}
            sign_in_day_num = data.get('data').get('signInDayNum')
            if data.get('code') == 200 and data.get('data').get('cumulativeAwards'):
                cumulative_awards = data.get('data').get('cumulativeAwards')
                for award in cumulative_awards:
                    g_applet_accumulated_sign_in_reward_map[award.get('awardId')] = award.get('signDayNum')
            return sign_in_day_num, g_applet_accumulated_sign_in_reward_map
        except Exception as e:
            fn_print(f"获取签到天数及签到奖励时出错: {e}")
            return None

    def g_applet_receive_sign_in_award(self, sign_in_activity_id, award_id, sign_in_reward_map):
        """ 领取累计签到奖励 """
        try:
            response = self.client.post(
                url="/api/cn/oapi/marketing/cumulativeSignIn/drawCumulativeAward",
                json={
                    "activityId": sign_in_activity_id,
                    "awardId": award_id
                }
            )
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 200:
                days = sign_in_reward_map.get(award_id)
                award_value = data.get('data').get('awardValue')
                fn_print(f"累计签到{days}天的奖励领取成功！获得： {award_value}")
        except Exception as e:
            fn_print(f"领取累计签到奖励时出错: {e}")

    def g_applet_handle_sign_in_award(self):
        """ 处理累计签到奖励 """
        sign_in_day_num, g_applet_accumulated_sign_in_reward_map = self.g_applet_get_sign_in_detail()
        if sign_in_day_num is None:
            return
        if sign_in_day_num not in g_applet_accumulated_sign_in_reward_map.values():
            return
        award_id = [k for k, v in g_applet_accumulated_sign_in_reward_map.items() if v == sign_in_day_num][0]
        self.g_applet_receive_sign_in_award(self.g_applet_sign_in_activity_id, award_id,
                                            g_applet_accumulated_sign_in_reward_map)

    def g_applet_get_narrow_channel_task_activity_info(self):
        """ 获取窄渠道活动信息 """
        url = self.get_activity_url("https://msec.opposhop.cn/configs/web/advert/300003", "福利专区", "窄渠道")
        if url is None:
            fn_print("获取活动信息异常，任务停止！")
            exit()
        try:
            response = self.client.get(
                url=url
            )
            response.raise_for_status()
            html = response.text
            # 使用正则表达式提取活动ID
            pattern = r'window\.__DSL__\s*=\s*({.*?});'
            match = re.search(pattern, html, re.DOTALL)
            if match:
                dsl_json = json.loads(match.group(1))
                task_cmps = dsl_json.get("cmps")
                for cmp in task_cmps:
                    if "Task" in cmp:
                        task_field = cmp
                        continue
                    if "Raffle" in cmp:
                        raffle_field = cmp
                        continue
                self.g_applet_narrow_channel_activity_id = dsl_json['byId'][task_field]['attr']['taskActivityInfo'][
                    'activityId']
                self.g_applet_narrow_channel_raffle_id = dsl_json['byId'][raffle_field]['attr']['activityInformation'][
                    'raffleId']
                self.g_applet_narrow_channel_jimuld_id = dsl_json['activityId']
        except Exception as e:
            fn_print(f"获取窄渠道活动ID时出错: {e}")

    def g_applet_get_narrow_channel_task_list(self):
        """ 获取窄渠道活动任务列表 """
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/task/queryTaskList?activityId={self.g_applet_narrow_channel_activity_id}&source=c"
            )
            response.raise_for_status()
            data = response.json()
            task_list_info = []
            if not data.get('data').get('taskDTOList'):
                fn_print(f"获取窄渠道活动任务列表失败！-> {data.get('message')}")
                return task_list_info
            for task in data.get('data').get('taskDTOList'):
                task_list_info.append(
                    {
                        "task_name": task.get('taskName'),
                        "task_id": task.get('taskId'),
                        "activity_id": task.get('activityId'),
                        "task_type": task.get('taskType'),
                        "browseTime": task.get('attachConfigOne').get('browseTime') if task.get(
                            'attachConfigOne') else None,
                    }
                )
            return task_list_info
        except Exception as e:
            fn_print(f"获取窄渠道活动任务列表时出错: {e}")
            return []

    def g_applet_handle_narrow_channel_task(self):
        task_list = self.g_applet_get_narrow_channel_task_list()
        for task in task_list:
            task_name = task.get('task_name')
            task_id = task.get('task_id')
            activity_id = task.get('activity_id')
            task_type = task.get('task_type')
            browse_time = task.get('browseTime')
            if task_type == 1:
                self.g_applet_todo_task_by_browse_page(task_name, task_id, activity_id, task_type)
                time.sleep(browse_time + 1)
                self.g_applet_receive_reward(task_name, task_id, activity_id)
            else:
                fn_print(f"小程序专享福利-暂不支持{task_type}类型任务，请向作者反馈‼️")
                continue

    def g_applet_618membership_subsidy_get_task_activity_info(self):
        """ 获取618会员补贴活动信息 """
        url = self.get_activity_url("https://msec.opposhop.cn/configs/web/advert/300003", "首页定帧", "积分膨胀")
        if url is None:
            fn_print("获取活动信息异常，任务停止！")
            exit()
        try:
            response = self.client.get(
                url=url
            )
            response.raise_for_status()
            html = response.text
            # 使用正则表达式提取活动ID
            pattern = r'window\.__DSL__\s*=\s*({.*?});'
            match = re.search(pattern, html, re.DOTALL)
            if match:
                dsl_json = json.loads(match.group(1))
                task_cmps = dsl_json.get("cmps")
                for cmp in task_cmps:
                    if "Task" in cmp:
                        task_field = cmp
                        continue
                    if "Raffle" in cmp:
                        raffle_field = cmp
                        continue
                self.g_applet_618membership_subsidy_activity_id = \
                    dsl_json['byId'][task_field]['attr']['taskActivityInfo']['activityId']
                self.g_applet_618membership_subsidy_raffle_id = \
                    dsl_json['byId'][raffle_field]['attr']['activityInformation']['raffleId']
                self.g_applet_618membership_subsidy_jimuld_id = dsl_json['activityId']
        except Exception as e:
            fn_print(f"获取618会员补贴活动ID时出错: {e}")

    def g_applet_618membership_subsidy_get_task_list(self):
        """ 获取618会员补贴活动任务列表 """
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/task/queryTaskList?activityId={self.g_applet_618membership_subsidy_activity_id}&source=c"
            )
            response.raise_for_status()
            data = response.json()
            task_list_info = []
            if not data.get('data').get('taskDTOList'):
                fn_print(f"获取618会员补贴活动任务列表失败！-> {data.get('message')}")
                return task_list_info
            for task in data.get('data').get('taskDTOList'):
                if task.get('taskType') == 6:
                    continue
                task_list_info.append(
                    {
                        "task_name": task.get('taskName'),
                        "task_id": task.get('taskId'),
                        "activity_id": task.get('activityId'),
                        "task_type": task.get('taskType'),
                        "browseTime": task.get('attachConfigOne').get('browseTime') if task.get(
                            'attachConfigOne') else None,
                    }
                )
            return task_list_info
        except Exception as e:
            fn_print(f"获取618会员补贴活动任务列表时出错: {e}")
            return []

    def g_applet_618membership_subsidy_handle_task(self):
        task_list = self.g_applet_618membership_subsidy_get_task_list()
        for task in task_list:
            task_name = task.get('task_name')
            task_id = task.get('task_id')
            activity_id = task.get('activity_id')
            task_type = task.get('task_type')
            browse_time = task.get('browseTime')
            if task_type == 1:
                self.g_applet_todo_task_by_browse_page(task_name, task_id, activity_id, task_type)
                time.sleep(browse_time + 1)
                self.g_applet_receive_reward(task_name, task_id, activity_id)
            elif task_type == 2:
                self.g_applet_todo_task_by_browse_page(task_name, task_id, activity_id, task_type)
                self.g_applet_receive_reward(task_name, task_id, activity_id)
            else:
                fn_print(f"618会员补贴-暂不支持{task_type}类型任务，请向作者反馈‼️")
                continue

    def g_applet_champions_league_get_task_activity_info(self):
        """ 欧冠联赛活动信息 """
        try:
            response = self.client.get(
                url=f"/bp/e3c49b889f357f17"
            )
            response.raise_for_status()
            html = response.text
            # 使用正则表达式提取活动ID
            pattern = r'window\.__DSL__\s*=\s*({.*?});'
            match = re.search(pattern, html, re.DOTALL)
            if not match:
                fn_print(f"❌未找到欧冠联赛活动的DSL数据，请检查页面是否更新！")
                return
            dsl_json = json.loads(match.group(1))
            task_cmps = dsl_json.get("cmps", [])
            task_field = raffle_field = signin_field = None
            for cmp in task_cmps:
                if "Task" in cmp:
                    task_field = cmp
                elif "Raffle" in cmp:
                    raffle_field = cmp
                elif "SignIn" in cmp:
                    signin_field = cmp
            if task_field:
                try:
                    self.g_applet_champions_league_activity_id = \
                        dsl_json['byId'][task_field]['attr']['taskActivityInfo']['activityId']
                except KeyError:
                    fn_print("⚠️任务ID解析失败")
            if raffle_field:
                try:
                    self.g_applet_champions_league_raffle_id = \
                        dsl_json['byId'][raffle_field]['attr']['activityInformation']['raffleId']
                except KeyError:
                    fn_print("⚠️抽奖ID解析失败")
            if signin_field:
                try:
                    self.g_applet_champions_league_sign_in_activity_id = \
                        dsl_json['byId'][signin_field]['attr']['activityInfo']['activityId']
                except KeyError:
                    fn_print("⚠️签到ID解析失败")
            self.g_applet_champions_league_jimuld_id = dsl_json['activityId']
        except Exception as e:
            fn_print(f"获取欧冠联赛活动ID时出错: {e}")

    def g_applet_champions_league_get_task_list(self):
        """ 获取欧冠联赛活动任务列表 """
        if not self.g_applet_champions_league_activity_id:
            fn_print("⚠️未获取到欧冠联赛活动ID")
            return []
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/task/queryTaskList?activityId={self.g_applet_champions_league_activity_id}&source=c"
            )
            response.raise_for_status()
            data = response.json()
            task_list_info = []
            if not data.get('data').get('taskDTOList'):
                fn_print(f"获取欧冠联赛活动任务列表失败！-> {data.get('message')}")
                return task_list_info
            for task in data.get('data').get('taskDTOList'):
                task_list_info.append(
                    {
                        "task_name": task.get('taskName'),
                        "task_id": task.get('taskId'),
                        "activity_id": task.get('activityId'),
                        "task_type": task.get('taskType'),
                        "browseTime": task.get('attachConfigOne').get('browseTime') if task.get(
                            'attachConfigOne') else None
                    }
                )
            return task_list_info
        except Exception as e:
            fn_print(f"获取欧冠联赛活动任务列表时出错: {e}")
            return []

    def g_applet_champions_league_handle_task(self):
        task_list = self.g_applet_champions_league_get_task_list()
        for task in task_list:
            task_name = task.get('task_name')
            task_id = task.get('task_id')
            activity_id = task.get('activity_id')
            task_type = task.get('task_type')
            browse_time = task.get('browseTime')
            if task_type == 1:
                self.g_applet_todo_task_by_browse_page(task_name, task_id, activity_id, task_type)
                time.sleep(browse_time + 1)
                self.g_applet_receive_reward(task_name, task_id, activity_id)
            elif task_type == 2:
                self.g_applet_todo_task_by_browse_page(task_name, task_id, activity_id, task_type)
                self.g_applet_receive_reward(task_name, task_id, activity_id)
            else:
                fn_print(f"欧冠联赛-暂不支持{task_type}类型任务，请向作者反馈‼️")
                continue

    def g_applet_champions_league_sign_in(self):
        """ 欧冠联赛签到 """
        if not self.g_applet_champions_league_sign_in_activity_id:
            fn_print("⏭️未找到欧冠联赛活动签到活动ID，跳过签到")
            return
        try:
            response = self.client.post(
                url=f"/api/cn/oapi/marketing/cumulativeSignIn/signIn",
                json={
                    "activityId": self.g_applet_champions_league_sign_in_activity_id
                }
            )
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 200:
                fn_print(f"✅欧冠联赛签到成功！获得积分： {data.get('data').get('awardValue')}")
            elif data.get('code') == 5008:
                fn_print(data.get('message'))
            else:
                fn_print(f"❌欧冠联赛签到失败！{data.get('message')}")
        except Exception as e:
            fn_print(f"欧冠联赛签到时出错: {e}")

    def g_applet_champions_league_get_sign_in_detail(self):
        """ 获取欧冠联赛签到天数和累计签到奖励 """
        if not self.g_applet_champions_league_sign_in_activity_id:
            fn_print("⏭️未找到欧冠联赛活动签到活动ID，跳过获取签到天数和奖励")
            return None, None
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/cumulativeSignIn/getSignInDetail?activityId={self.g_applet_champions_league_sign_in_activity_id}"
            )
            response.raise_for_status()
            data = response.json()
            g_applet_accumulated_sign_in_reward_map = {}
            sign_in_day_num = data.get('data').get('signInDayNum')
            if data.get('code') == 200 and data.get('data').get('cumulativeAwards'):
                cumulative_awards = data.get('data').get('cumulativeAwards')
                for award in cumulative_awards:
                    g_applet_accumulated_sign_in_reward_map[award.get('awardId')] = award.get('signDayNum')
            return sign_in_day_num, g_applet_accumulated_sign_in_reward_map
        except Exception as e:
            fn_print(f"获取欧冠联赛签到天数及签到奖励时出错: {e}")
            return None, None

    def g_applet_champions_league_handle_sign_in_award(self):
        """ 处理累计签到奖励 """
        sign_in_day_num, g_applet_accumulated_sign_in_reward_map = self.g_applet_champions_league_get_sign_in_detail()
        if sign_in_day_num is None:
            return
        if sign_in_day_num not in g_applet_accumulated_sign_in_reward_map.values():
            return
        award_id = [k for k, v in g_applet_accumulated_sign_in_reward_map.items() if v == sign_in_day_num][0]
        self.g_applet_receive_sign_in_award(self.g_applet_champions_league_sign_in_activity_id, award_id,
                                            g_applet_accumulated_sign_in_reward_map)

    def g_applet_CrayonShinChan_get_task_activity_info(self):
        """ 蜡笔小新活动信息 """
        try:
            response = self.client.get(
                url=f"/bp/2d83f8d2e8e0ef11"
            )
            response.raise_for_status()
            html = response.text
            # 使用正则表达式提取活动ID
            pattern = r'window\.__DSL__\s*=\s*({.*?});'
            match = re.search(pattern, html, re.DOTALL)
            if not match:
                fn_print("❌未找到蜡笔小新活动的DSL数据，请检查页面结构是否发生变化。")
                return
            dsl_json = json.loads(match.group(1))
            task_cmps = dsl_json.get("cmps", [])
            # 初始化所有字段为None
            task_field = raffle_field = signin_field = None
            for cmp in task_cmps:
                if "Task" in cmp:
                    task_field = cmp
                elif "Raffle" in cmp:
                    raffle_field = cmp
                elif "SignIn" in cmp:
                    signin_field = cmp
            if task_field:
                try:
                    self.g_applet_CrayonShinChan_activity_id = dsl_json['byId'][task_field]['attr']['taskActivityInfo'][
                        'activityId']
                except KeyError:
                    fn_print("⚠️任务ID解析失败")
            if raffle_field:
                try:
                    self.g_applet_CrayonShinChan_raffle_id = \
                        dsl_json['byId'][raffle_field]['attr']['activityInformation']['raffleId']
                except KeyError:
                    fn_print("⚠️抽奖ID解析失败")

            if signin_field:
                try:
                    self.g_applet_CrayonShinChan_sign_in_activity_id = \
                        dsl_json['byId'][signin_field]['attr']['activityInfo']['activityId']
                except KeyError:
                    fn_print("⚠️签到ID解析失败")
            else:
                fn_print("ℹ️未找到签到组件信息")
            self.g_applet_CrayonShinChan_jimuld_id = dsl_json['activityId']
        except Exception as e:
            fn_print(f"获取蜡笔小新活动ID时出错: {e}")

    def g_applet_CrayonShinChan_get_task_list(self):
        """ 获取蜡笔小新活动任务列表 """
        if not self.g_applet_CrayonShinChan_activity_id:
            fn_print("❌蜡笔小新活动ID未设置，请先获取活动ID。")
            return []
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/task/queryTaskList?activityId={self.g_applet_CrayonShinChan_activity_id}&source=c"
            )
            response.raise_for_status()
            data = response.json()
            task_list_info = []
            if not data.get('data').get('taskDTOList'):
                fn_print(f"获取蜡笔小新活动任务列表失败！-> {data.get('message')}")
                return task_list_info
            for task in data.get('data').get('taskDTOList'):
                task_list_info.append(
                    {
                        "task_name": task.get('taskName'),
                        "task_id": task.get('taskId'),
                        "activity_id": task.get('activityId'),
                        "task_type": task.get('taskType'),
                        "browseTime": task.get('attachConfigOne').get('browseTime') if task.get(
                            'attachConfigOne') else None
                    }
                )
            return task_list_info
        except Exception as e:
            fn_print(f"获取蜡笔小新活动任务列表时出错: {e}")
            return []

    def g_applet_CrayonShinChan_handle_task(self):
        task_list = self.g_applet_CrayonShinChan_get_task_list()
        for task in task_list:
            task_name = task.get('task_name')
            task_id = task.get('task_id')
            activity_id = task.get('activity_id')
            task_type = task.get('task_type')
            browse_time = task.get('browseTime')
            if task_type == 1:
                self.g_applet_todo_task_by_browse_page(task_name, task_id, activity_id, task_type)
                time.sleep(browse_time + 1)
                self.g_applet_receive_reward(task_name, task_id, activity_id)
            elif task_type == 2:
                self.g_applet_todo_task_by_browse_page(task_name, task_id, activity_id, task_type)
                self.g_applet_receive_reward(task_name, task_id, activity_id)
            elif task_type == 6:
                continue
            else:
                fn_print(f"蜡笔小新-暂不支持{task_type}类型任务，请向作者反馈‼️")
                continue

    def g_applet_CrayonShinChan_sign_in(self):
        """ 蜡笔小新签到 """
        if not self.g_applet_CrayonShinChan_sign_in_activity_id:
            fn_print("⏭️未找到蜡笔小新签到活动ID，跳过签到")
            return
        try:
            response = self.client.post(
                url="/api/cn/oapi/marketing/cumulativeSignIn/signIn",
                json={
                    "activityId": self.g_applet_CrayonShinChan_sign_in_activity_id
                }
            )
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 200:
                fn_print(f"✅蜡笔小新签到成功！获得积分： {data.get('data').get('awardValue')}")
            elif data.get('code') == 5008:
                fn_print(data.get('message'))
            else:
                fn_print(f"❌蜡笔小新签到失败！{data.get('message')}")
        except Exception as e:
            fn_print(f"蜡笔小新签到时出错: {e}")

    def g_applet_CrayonShinChan_get_sign_in_detail(self):
        """ 获取蜡笔小新签到天数和累计签到奖励 """
        if not self.g_applet_CrayonShinChan_sign_in_activity_id:
            fn_print("⏭️未找到蜡笔小新签到活动ID，跳过获取签到信息")
            return None, None
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/cumulativeSignIn/getSignInDetail?activityId={self.g_applet_CrayonShinChan_sign_in_activity_id}"
            )
            response.raise_for_status()
            data = response.json()
            g_applet_CrayonShinChan_sign_in_reward_map = {}
            sign_in_day_num = data.get('data').get('signInDayNum')
            if data.get('code') == 200 and data.get('data').get('cumulativeAwards'):
                cumulative_awards = data.get('data').get('cumulativeAwards')
                for award in cumulative_awards:
                    g_applet_CrayonShinChan_sign_in_reward_map[award.get('awardId')] = award.get('signDayNum')
            return sign_in_day_num, g_applet_CrayonShinChan_sign_in_reward_map
        except Exception as e:
            fn_print(f"获取蜡笔小新签到天数及签到奖励时出错: {e}")
            return None

    def g_applet_CrayonShinChan_handle_sign_in_award(self):
        """ 处理蜡笔小新累计签到奖励 """
        sign_in_day_num, g_applet_CrayonShinChan_sign_in_reward_map = self.g_applet_CrayonShinChan_get_sign_in_detail()
        if sign_in_day_num is None:
            return
        if sign_in_day_num not in g_applet_CrayonShinChan_sign_in_reward_map.values():
            return
        award_id = [k for k, v in g_applet_CrayonShinChan_sign_in_reward_map.items() if v == sign_in_day_num][0]
        self.g_applet_receive_sign_in_award(self.g_applet_CrayonShinChan_sign_in_activity_id, award_id,
                                            g_applet_CrayonShinChan_sign_in_reward_map)

    def g_applet_Sun_enterprise_get_task_activity_info(self):
        """ 莎莎企业活动信息 """
        try:
            response = self.client.get(
                url=f"/bp/457871c72cb6ccd9"
            )
            response.raise_for_status()
            html = response.text
            # 使用正则表达式提取活动ID
            pattern = r'window\.__DSL__\s*=\s*({.*?});'
            match = re.search(pattern, html, re.DOTALL)
            if match:
                dsl_json = json.loads(match.group(1))
                task_cmps = dsl_json.get("cmps")
                for cmp in task_cmps:
                    if "Task" in cmp:
                        task_field = cmp
                        continue
                    if "Raffle" in cmp:
                        raffle_field = cmp
                        continue
                self.g_applet_Sun_enterprise_activity_id = dsl_json['byId'][task_field]['attr']['taskActivityInfo'][
                    'activityId']
                self.g_applet_Sun_enterprise_raffle_id = dsl_json['byId'][raffle_field]['attr']['activityInformation'][
                    'raffleId']
                self.g_applet_Sun_enterprise_jimuld_id = dsl_json['activityId']
        except Exception as e:
            fn_print(f"获取莎莎企业活动ID时出错: {e}")

    def g_applet_Sun_enterprise_get_task_list(self):
        """ 获取莎莎企业活动任务列表 """
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/task/queryTaskList?activityId={self.g_applet_Sun_enterprise_activity_id}&source=c"
            )
            response.raise_for_status()
            data = response.json()
            task_list_info = []
            if not data.get('data').get('taskDTOList'):
                fn_print(f"获取莎莎企业活动任务列表失败！-> {data.get('message')}")
                return task_list_info
            for task in data.get('data').get('taskDTOList'):
                task_list_info.append(
                    {
                        "task_name": task.get('taskName'),
                        "task_id": task.get('taskId'),
                        "activity_id": task.get('activityId'),
                        "task_type": task.get('taskType'),
                        "browseTime": task.get('attachConfigOne').get('browseTime') if task.get(
                            'attachConfigOne') else None
                    }
                )
            return task_list_info
        except Exception as e:
            fn_print(f"获取莎莎企业活动任务列表时出错: {e}")
            return []

    def g_applet_Sun_enterprise_handle_task(self):
        task_list = self.g_applet_Sun_enterprise_get_task_list()
        for task in task_list:
            task_name = task.get('task_name')
            task_id = task.get('task_id')
            activity_id = task.get('activity_id')
            task_type = task.get('task_type')
            browse_time = task.get('browseTime')
            if task_type == 1:
                self.g_applet_todo_task_by_browse_page(task_name, task_id, activity_id, task_type)
                time.sleep(browse_time + 1)
                self.g_applet_receive_reward(task_name, task_id, activity_id)
            elif task_type == 2:
                self.g_applet_todo_task_by_browse_page(task_name, task_id, activity_id, task_type)
                self.g_applet_receive_reward(task_name, task_id, activity_id)
            elif task_type == 6:
                continue
            else:
                fn_print(f"莎莎企业-暂不支持{task_type}类型任务，请向作者反馈‼️")
                continue

    def g_applet_reserva_shop_get_task_activity_info(self):
        """ 预约新品活动信息 """
        try:
            response = self.client.get(
                url="/bp/f568925e03316c4d"
            )
            response.raise_for_status()
            html = response.text
            # 使用正则表达式提取活动ID
            pattern = r'window\.__DSL__\s*=\s*({.*?});'
            match = re.search(pattern, html, re.DOTALL)
            if match:
                dsl_json = json.loads(match.group(1))
                task_cmps = dsl_json.get("cmps")
                for cmp in task_cmps:
                    if "Task" in cmp:
                        task_field = cmp
                        continue
                    if "Raffle" in cmp:
                        raffle_field = cmp
                        continue
                    if "Appointment" in cmp:
                        appointment_field = cmp
                        continue
                self.g_applet_reserva_shop_activity_id = dsl_json['byId'][task_field]['attr']['taskActivityInfo'][
                    'activityId']
                self.g_applet_reserva_shop_raffle_id = dsl_json['byId'][raffle_field]['attr']['activityInformation'][
                    'raffleId']
                self.g_applet_reserva_shop_jimuld_id = dsl_json['activityId']
                self.g_aapplet_reserva_shop_sku_id = \
                    dsl_json['byId'][appointment_field]['attr']['selectAppointmentGoods']['cardInfo']['skuId'][
                        'labelValue']
                self.g_applet_reserva_shop_streamCode = \
                    dsl_json['byId'][appointment_field]['attr']['liveReminder']['info']['liveId']

        except Exception as e:
            fn_print(f"获取预约新品活动ID时出错: {e}")

    def g_applet_reserva_shop_get_task_list(self):
        """ 获取预约新品活动任务列表 """
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/task/queryTaskList?activityId={self.g_applet_reserva_shop_activity_id}&source=c"
            )
            response.raise_for_status()
            data = response.json()
            task_list_info = []
            if not data.get('data').get('taskDTOList'):
                fn_print(f"获取预约新品活动任务列表失败！-> {data.get('message')}")
                return task_list_info
            for task in data.get('data').get('taskDTOList'):
                task_list_info.append(
                    {
                        "task_name": task.get('taskName'),
                        "task_id": task.get('taskId'),
                        "activity_id": task.get('activityId'),
                        "task_type": task.get('taskType'),
                        "browseTime": task.get('attachConfigOne').get('browseTime') if task.get(
                            'attachConfigOne') else None
                    }
                )
            return task_list_info
        except Exception as e:
            fn_print(f"获取预约新品活动任务列表时出错: {e}")
            return []

    def g_applet_reserva_shop_handle_task(self):
        task_list = self.g_applet_reserva_shop_get_task_list()
        for task in task_list:
            task_name = task.get('task_name')
            task_id = task.get('task_id')
            activity_id = task.get('activity_id')
            task_type = task.get('task_type')
            browse_time = task.get('browseTime')
            if task_type == 1:
                self.g_applet_todo_task_by_browse_page(task_name, task_id, activity_id, task_type)
                time.sleep(browse_time + 1)
                self.g_applet_receive_reward(task_name, task_id, activity_id)
            elif task_type == 6:
                continue
            else:
                fn_print(f"预约新品-暂不支持{task_type}类型任务，请向作者反馈‼️")
                continue

    def g_applet_reserva_shop_products(self, sku_id: int, jimuld_id: int, streamCode: str):
        """ 预约新商品 """
        try:
            response = self.client.post(
                url=f"/api/cn/oapi/marketing/reserve/materials/reserveMaterials",
                json={
                    "reserveMaterialsList": [
                        sku_id
                    ],
                    "reserveType": 2,
                    "jimuActivityId": jimuld_id,
                    "streamCode": streamCode
                }
            )
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 200:
                fn_print(f"✅预约新商品成功！")
            else:
                fn_print(f"❌预约新商品失败！{data.get('message')}")
        except Exception as e:
            fn_print(f"预约新商品时出错: {e}")

    def g_applet_ocean_get_task_activity_info(self):
        """ 获取海洋「琦」遇活动信息 """
        try:
            response = self.client.get(
                url=f"/bp/3859e6f1cfe2a4ab"
            )
            response.raise_for_status()
            html = response.text
            # 使用正则表达式提取活动ID
            pattern = r'window\.__DSL__\s*=\s*({.*?});'
            match = re.search(pattern, html, re.DOTALL)
            if not match:
                fn_print("❌未找到海洋「琦」遇活动的DSL数据，请检查页面是否更新！")
                return
            dsl_json = json.loads(match.group(1))
            task_cmps = dsl_json.get("cmps", [])
            task_field = raffle_field = signin_field = None
            for cmp in task_cmps:
                if "Task" in cmp:
                    task_field = cmp
                elif "Raffle" in cmp:
                    raffle_field = cmp
                elif "SignIn" in cmp:
                    signin_field = cmp
            if task_field:
                try:
                    self.g_applet_ocean_activity_id = dsl_json['byId'][task_field]['attr']['taskActivityInfo'][
                        'activityId']
                except KeyError:
                    fn_print("⚠️任务ID解析失败")
            if raffle_field:
                try:
                    self.g_applet_ocean_raffle_id = \
                        dsl_json['byId'][raffle_field]['attr']['activityInformation']['raffleId']
                except KeyError:
                    fn_print("⚠️抽奖ID解析失败")
            if signin_field:
                try:
                    self.g_applet_ocean_sign_in_activity_id = \
                        dsl_json['byId'][signin_field]['attr']['activityInfo']['activityId']
                except KeyError:
                    fn_print("⚠️签到ID解析失败")
            self.g_applet_ocean_jimuld_id = dsl_json['activityId']
        except Exception as e:
            fn_print(f"获取海洋「琦」遇活动ID时出错: {e}")

    def g_applet_ocean_get_task_list(self):
        """ 获取海洋「琦」遇活动任务列表 """
        if not self.g_applet_ocean_activity_id:
            fn_print("⚠️未找到海洋「琦」遇活动ID，跳过获取任务列表")
            return []
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/task/queryTaskList?activityId={self.g_applet_ocean_activity_id}&source=c"
            )
            response.raise_for_status()
            data = response.json()
            task_list_info = []
            if not data.get('data').get('taskDTOList'):
                fn_print(f"获取海洋「琦」遇活动任务列表失败！-> {data.get('message')}")
                return task_list_info
            for task in data.get('data').get('taskDTOList'):
                task_list_info.append(
                    {
                        "task_name": task.get('taskName'),
                        "task_id": task.get('taskId'),
                        "activity_id": task.get('activityId'),
                        "task_type": task.get('taskType'),
                        "browseTime": task.get('attachConfigOne').get('browseTime') if task.get(
                            'attachConfigOne') else None
                    }
                )
            return task_list_info
        except Exception as e:
            fn_print(f"获取海洋「琦」遇活动任务列表时出错: {e}")
            return []

    def g_applet_ocean_handle_task(self):
        task_list = self.g_applet_ocean_get_task_list()
        for task in task_list:
            task_name = task.get('task_name')
            task_id = task.get('task_id')
            activity_id = task.get('activity_id')
            task_type = task.get('task_type')
            browse_time = task.get('browseTime')
            if task_type == 1:
                self.g_applet_todo_task_by_browse_page(task_name, task_id, activity_id, task_type)
                time.sleep(browse_time + 1)
                self.g_applet_receive_reward(task_name, task_id, activity_id)
            elif task_type == 2:
                self.g_applet_todo_task_by_browse_page(task_name, task_id, activity_id, task_type)
                self.g_applet_receive_reward(task_name, task_id, activity_id)
            elif task_type == 6:
                continue
            else:
                fn_print(f"海洋「琦」遇-暂不支持{task_type}类型任务，请向作者反馈‼️")
                continue

    def g_applet_full_time_get_task_activity_info(self):
        """ 获取618 · 全职「补」给活动信息 """
        try:
            response = self.client.get(
                url=f"/bp/3d6adf457b29db15"
            )
            response.raise_for_status()
            html = response.text
            # 使用正则表达式提取活动ID
            pattern = r'window\.__DSL__\s*=\s*({.*?});'
            match = re.search(pattern, html, re.DOTALL)
            if not match:
                fn_print("❌未找到618 · 全职「补」给活动的DSL数据，请检查页面是否更新！")
                return
            dsl_json = json.loads(match.group(1))
            task_cmps = dsl_json.get("cmps", [])
            task_field = signin_field = None
            raffle_fields = []
            for cmp in task_cmps:
                if "Task" in cmp:
                    task_field = cmp
                elif "Raffle" in cmp:
                    raffle_fields.append(cmp)
                elif "SignIn" in cmp:
                    signin_field = cmp
            if task_field:
                try:
                    self.g_applet_full_time_activity_id = dsl_json['byId'][task_field]['attr']['taskActivityInfo'][
                        'activityId']
                except KeyError:
                    fn_print("⚠️任务ID解析失败")
            if raffle_fields:
                try:
                    self.g_applet_full_time_raffle_id = \
                        dsl_json['byId'][raffle_fields[0]]['attr']['activityInformation']['raffleId']
                except KeyError:
                    fn_print("⚠️抽奖ID解析失败")
            if signin_field:
                try:
                    self.g_applet_full_time_sign_in_activity_id = \
                        dsl_json['byId'][signin_field]['attr']['activityInfo']['activityId']
                except KeyError:
                    fn_print("⚠️签到ID解析失败")
            self.g_applet_full_time_jimuld_id = dsl_json['activityId']
        except Exception as e:
            fn_print(f"获取618 · 全职「补」给活动ID时出错: {e}")

    def g_applet_full_time_get_task_list(self):
        """ 获取618 · 全职「补」给活动任务列表 """
        if not self.g_applet_full_time_activity_id:
            fn_print("⚠️未找到618 · 全职「补」给活动ID，跳过获取任务列表")
            return []
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/task/queryTaskList?activityId={self.g_applet_full_time_activity_id}&source=c"
            )
            response.raise_for_status()
            data = response.json()
            task_list_info = []
            if not data.get('data').get('taskDTOList'):
                fn_print(f"获取618 · 全职「补」给活动任务列表失败！-> {data.get('message')}")
                return task_list_info
            for task in data.get('data').get('taskDTOList'):
                task_list_info.append(
                    {
                        "task_name": task.get('taskName'),
                        "task_id": task.get('taskId'),
                        "activity_id": task.get('activityId'),
                        "task_type": task.get('taskType'),
                        "browseTime": task.get('attachConfigOne').get('browseTime') if task.get(
                            'attachConfigOne') else None
                    }
                )
            return task_list_info
        except Exception as e:
            fn_print(f"获取618 · 全职「补」给活动任务列表时出错: {e}")
            return []

    def g_applet_full_time_handle_task(self):
        task_list = self.g_applet_full_time_get_task_list()
        for task in task_list:
            task_name = task.get('task_name')
            task_id = task.get('task_id')
            activity_id = task.get('activity_id')
            task_type = task.get('task_type')
            browse_time = task.get('browseTime')
            if task_type == 1:
                self.g_applet_todo_task_by_browse_page(task_name, task_id, activity_id, task_type)
                time.sleep(browse_time + 1)
                self.g_applet_receive_reward(task_name, task_id, activity_id)
            elif task_type == 2:
                self.g_applet_todo_task_by_browse_page(task_name, task_id, activity_id, task_type)
                self.g_applet_receive_reward(task_name, task_id, activity_id)
            elif task_type == 6:
                continue
            else:
                fn_print(f"618 · 全职「补」给-暂不支持{task_type}类型任务，请向作者反馈‼️")
                continue

    def g_applet_618mainVenue_get_task_activity_info(self):
        """ 获取618主会场活动信息 """
        try:
            response = self.client.get(
                url="/bp/6df3b6a0d359165c"
            )
            response.raise_for_status()
            html = response.text
            # 使用正则表达式提取活动ID
            pattern = r'window\.__DSL__\s*=\s*({.*?});'
            match = re.search(pattern, html, re.DOTALL)
            if not match:
                fn_print("❌未找到618主会场活动的DSL数据，请检查页面是否更新！")
                return
            dsl_json = json.loads(match.group(1))
            task_cmps = dsl_json.get("cmps", [])
            raffle_field = None
            for cmp in task_cmps:
                if "Raffle" in cmp:
                    raffle_field = cmp
            if raffle_field:
                try:
                    self.g_applet_618mainVenue_raffle_id = \
                        dsl_json['byId'][raffle_field]['attr']['activityInformation']['raffleId']
                except KeyError:
                    fn_print("⚠️抽奖ID解析失败")
            self.g_applet_618mainVenue_jimuld_id = dsl_json['activityId']
        except Exception as e:
            fn_print(f"获取618主会场活动ID时出错: {e}")

    def get_user_total_points(self):
        """ 获取用户总积分 """
        try:
            response = self.client.get(
                url=f"https://msec.opposhop.cn/users/web/member/infoDetail"
            )
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 200 and data.get('data'):
                fn_print(
                    f"**OPPO会员: {data.get('data').get('userName')}**，当前总积分: {data.get('data').get('userCredit')}")
        except Exception as e:
            fn_print(f"获取用户总积分时出错: {e}")


def run(self: Oppo):
    if self.level is None:
        return

    self.is_login()
    self.get_user_info()
    self.get_task_activity_info()
    self.sign_in()
    self.get_task_list_ids()


def run_g_applet(self: OppoApplet):
    self.is_login()
    self.get_user_info()

    # 小程序签到任务
    fn_print("#######开始执行小程序签到任务#######")
    self.g_applet_get_task_activity_info()
    self.g_applet_sign_in()
    self.g_applet_handle_sign_in_award()
    self.g_applet_handle_task()
    draw_count = self.g_applet_get_draw_count(self.g_applet_raffle_id)
    for _ in range(draw_count):
        fn_print("\t>> 前往抽奖")
        self.g_applet_draw_raffle(self.g_applet_raffle_id, self.g_applet_jimuld_id, "签到赢好礼")
        time.sleep(1.5)

    # 小程序专享福利任务
    fn_print("#######开始执行小程序专享福利任务#######")
    self.g_applet_get_narrow_channel_task_activity_info()
    self.g_applet_handle_narrow_channel_task()
    narrow_channel_draw_count = self.g_applet_get_draw_count(self.g_applet_narrow_channel_raffle_id)
    for _ in range(narrow_channel_draw_count):
        fn_print("\t>> 前往抽奖")
        self.g_applet_draw_raffle(self.g_applet_narrow_channel_raffle_id, self.g_applet_narrow_channel_jimuld_id,
                                  "小程序专享福利")
        time.sleep(1.5)

    # 小程序618会员补贴抽奖
    fn_print("#######开始执行小程序618会员补贴抽奖#######")
    self.g_applet_618membership_subsidy_get_task_activity_info()
    self.g_applet_618membership_subsidy_handle_task()
    _618membership_subsidy_draw_count = self.g_applet_get_draw_count(self.g_applet_618membership_subsidy_raffle_id)
    for _ in range(_618membership_subsidy_draw_count):
        fn_print("\t>> 前往抽奖")
        self.g_applet_draw_raffle(self.g_applet_618membership_subsidy_raffle_id,
                                  self.g_applet_618membership_subsidy_jimuld_id, "OPPO 商城 618-会员「补」贴会场")
        time.sleep(3)

    # 小程序欧冠联赛
    fn_print("#######开始执行小程序欧冠联赛任务#######")
    self.g_applet_champions_league_get_task_activity_info()
    self.g_applet_champions_league_sign_in()
    self.g_applet_champions_league_handle_sign_in_award()
    self.g_applet_champions_league_handle_task()
    champions_league_draw_count = self.g_applet_get_draw_count(self.g_applet_champions_league_raffle_id)
    for _ in range(champions_league_draw_count):
        fn_print("\t>> 前往抽奖")
        self.g_applet_draw_raffle(self.g_applet_champions_league_raffle_id, self.g_applet_champions_league_jimuld_id,
                                  "欧冠联赛 巅峰对决")
        time.sleep(3)

    # 小程序蜡笔小新活动
    fn_print("#######开始执行小程序蜡笔小新活动任务#######")
    self.g_applet_CrayonShinChan_get_task_activity_info()
    self.g_applet_CrayonShinChan_sign_in()
    self.g_applet_CrayonShinChan_handle_sign_in_award()
    self.g_applet_CrayonShinChan_handle_task()
    if is_luckyDraw:
        CrayonShinChan_draw_count = self.g_applet_get_draw_count(self.g_applet_CrayonShinChan_raffle_id)
        for _ in range(CrayonShinChan_draw_count):
            fn_print("\t>> 前往抽奖")
            self.g_applet_draw_raffle(self.g_applet_CrayonShinChan_raffle_id, self.g_applet_CrayonShinChan_jimuld_id,
                                      "蜡笔小新 夏日奇旅")
            time.sleep(1.5)

    # 小程序莎莎企业活动
    fn_print("#######开始执行小程序莎莎企业活动任务#######")
    self.g_applet_Sun_enterprise_get_task_activity_info()
    self.g_applet_Sun_enterprise_handle_task()
    if is_luckyDraw:
        Sun_enterprise_draw_count = self.g_applet_get_draw_count(self.g_applet_Sun_enterprise_raffle_id)
        for _ in range(Sun_enterprise_draw_count):
            fn_print("\t>> 前往抽奖")
            self.g_applet_draw_raffle(self.g_applet_Sun_enterprise_raffle_id, self.g_applet_Sun_enterprise_jimuld_id,
                                      "莎莎企业 夏日奇旅")
            time.sleep(1.5)

    # 小程序预约新品活动
    # fn_print("#######开始执行小程序预约新品活动任务#######")
    # self.g_applet_reserva_shop_get_task_activity_info()
    # self.g_applet_reserva_shop_handle_task()
    # self.g_applet_reserva_shop_products(self.g_aapplet_reserva_shop_sku_id, self.g_applet_reserva_shop_jimuld_id,
    #                                     self.g_applet_reserva_shop_streamCode)
    # reserva_shop_draw_count = self.g_applet_get_draw_count(self.g_applet_reserva_shop_raffle_id)
    # for _ in range(reserva_shop_draw_count):
    #     fn_print("\t>> 前往抽奖")
    #     self.g_applet_draw_raffle(self.g_applet_reserva_shop_raffle_id, self.g_applet_reserva_shop_jimuld_id,
    #                               "一加 Ace 5 至尊系列新品上市")
    #     time.sleep(1.5)

    # 海洋「琦」遇活动

    fn_print("#######开始执行海洋「琦」遇活动任务#######")
    self.g_applet_ocean_get_task_activity_info()
    self.g_applet_ocean_handle_task()
    if is_luckyDraw:
        ocean_draw_count = self.g_applet_get_draw_count(self.g_applet_ocean_raffle_id)
        for _ in range(ocean_draw_count):
            fn_print("\t>> 前往抽奖")
            self.g_applet_draw_raffle(self.g_applet_ocean_raffle_id, self.g_applet_ocean_jimuld_id,
                                      "海洋「琦」遇 人鱼送礼")
            time.sleep(1.5)

    # 618 · 全职「补」给活动
    fn_print("#######开始执行618 · 全职「补」给活动任务#######")
    self.g_applet_full_time_get_task_activity_info()
    self.g_applet_full_time_handle_task()
    if is_luckyDraw:
        full_time_draw_count = self.g_applet_get_draw_count(self.g_applet_full_time_raffle_id)
        for _ in range(full_time_draw_count):
            fn_print("\t>> 前往抽奖")
            self.g_applet_draw_raffle(self.g_applet_full_time_raffle_id, self.g_applet_full_time_jimuld_id,
                                      "618 · 全职「补」给")
            time.sleep(2.5)

    # 618主会场活动
    fn_print("#######开始执行618主会场活动任务#######")
    self.g_applet_618mainVenue_get_task_activity_info()
    mainVenue_draw_count = self.g_applet_get_draw_count(self.g_applet_618mainVenue_raffle_id)
    for _ in range(mainVenue_draw_count):
        fn_print("\t>> 前往抽奖")
        self.g_applet_draw_raffle(self.g_applet_618mainVenue_raffle_id, self.g_applet_618mainVenue_jimuld_id,
                                  "OPPO 商城 618 主会场")

    self.get_user_total_points()


if __name__ == '__main__':
    if oppo_cookies:
        invalid_level = False
        for cookie in oppo_cookies:
            oppo = Oppo(cookie)
            if oppo.level is None:
                invalid_level = True
            else:
                run(oppo)
    else:
        fn_print("‼️未配置OPPO商城APP的Cookie，跳过OPPO商城签到‼️")

    if oppo_applet_cookies:
        fn_print("=======开始执行小程序任务=======")
        for cookie in oppo_applet_cookies:
            oppo_applet = OppoApplet(cookie)
            run_g_applet(oppo_applet)
    else:
        fn_print("‼️未配置小程序的Cookie，跳过小程序签到‼️")
    send_notification_message_collection(f"OPPO商城签到通知 - {datetime.now().strftime('%Y/%m/%d')}")
