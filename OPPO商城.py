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
    
    在activity_base.py配置中控制是否抽奖，全局控制与单独控制
    若某个活动中无is_luckyDraw，则遵循全局的配置
"""
import random
import time
from datetime import datetime
from urllib.parse import urlparse, parse_qs

import httpx

from activity_base import BaseActivity, ACTIVITY_CONFIG
from fn_print import fn_print
from get_env import get_env
from sendNotify import send_notification_message_collection

oppo_cookies = get_env("oppo_cookie", "@")
oppo_applet_cookies = get_env("oppo_applet_cookie", "@")
oppo_service_cookies = get_env("oppo_service_cookie", "@")


class OppoAppActivity(BaseActivity):
    def __init__(self, cookie, task_config):
        self.user_name = None
        cookie_parts = cookie.split("#")
        if len(cookie_parts) != 3:
            fn_print("❌Cookie格式错误，应为：Cookie#user_agent#oppo_level")
            return
        self.cookie = cookie_parts[0]
        self.user_agent = cookie_parts[1]
        self.level = self.validate_level(cookie_parts[2])
        if not self.level:
            return
        headers = {
            'User-Agent': self.user_agent,
            'Accept-Encoding': 'gzip, deflate',
            'Accept': "application/json, text/plain, */*",
            'Content-Type': 'application/json',
            'Cookie': self.cookie
        }
        self.client = httpx.Client(base_url="https://hd.opposhop.cn", verify=False, headers=headers, timeout=60)
        super().__init__(cookie, self.client, task_config)

    def validate_level(self, level):
        valid_levels = ["普卡", "银卡会员", "金钻会员"]
        if level not in valid_levels:
            fn_print(f"❌环境变量oppo_level定义的会员等级无效，只能定义为：{valid_levels}")
            return None
        return level

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

    def handle_task(self):
        task_list = self.get_task_list()
        for task in task_list:
            task_type = task.get('taskType')
            task_name = task.get('taskName')
            if task_type == 3:  # 浏览商品
                goods_num = int(task.get('attachConfigOne', {}).get('goodsNum', 0))
                if goods_num > 0:
                    self.browse_products(goods_num)
                    time.sleep(1.5)
                self.complete_task(task_name, task.get('taskId'), task.get('activityId'), task_type)
                time.sleep(1.5)
                self.receive_reward(task_name, task.get('taskId'), task.get('activityId'))
            else:
                super().handle_task()
                break  # 防止重复处理


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
        super().__init__(g_applet_cookie, self.client, task_config)


def batch_run_and_collect(cls, cookies, configs=None):
    if configs:
        for task_key_, task_config_ in configs.items():
            for i, cookie_ in enumerate(cookies, 1):
                fn_print(f"=======开始执行{cls.__name__}任务：{task_key_} (账户{i}/{len(cookies)})=======")
                obj = cls(cookie_, task_config_)
                obj.run()
                fn_print(f"=======账户{i}执行完毕=======\n")
    else:
        for i, cookie_ in enumerate(cookies, 1):
            fn_print(f"=======开始执行{cls.__name__} (账户{i}/{len(cookies)})=======")
            obj = cls(cookie_)
            obj.run()
            fn_print(f"=======账户{i}执行完毕=======\n")


if __name__ == '__main__':
    if oppo_cookies:
        from activity_base import ACTIVITY_CONFIG
        batch_run_and_collect(OppoAppActivity, oppo_cookies, ACTIVITY_CONFIG.get("oppo_app", {}))
    else:
        fn_print("‼️未配置OPPO商城APP的Cookie，跳过OPPO商城APP签到‼️")

    if oppo_applet_cookies:
        batch_run_and_collect(OppoAppletActivity, oppo_applet_cookies, ACTIVITY_CONFIG.get("oppo_applet", {}))
    else:
        fn_print("‼️未配置OPPO商城小程序的Cookie，跳过OPPO商城小程序签到‼️")

    if oppo_service_cookies:
        from oppo_service import OppoServiceActivity
        batch_run_and_collect(OppoServiceActivity, oppo_service_cookies)
    else:
        fn_print("‼️未配置OPPO服务的Cookie，跳过OPPO服务签到‼️")
    send_notification_message_collection(f"OPPO商城&OPPO服务签到通知 - {datetime.now().strftime('%Y/%m/%d')}")
