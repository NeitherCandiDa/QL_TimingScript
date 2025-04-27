# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         OPPO商城.py
# @author           Echo
# @EditTime         2025/4/24
# const $ = new Env('OPPO商城');
# cron: 0 0 12 * * *
"""
开启抓包进入‘OPPO商城’app，进入我的 - 签到任务
三个变量： 
oppo_cookie，抓包https://hd.opposhop.cn请求头中的 Cookie，整个Cookie都放进来。多个账号用@隔开
oppo_user_agent，请求头的User-Agent
oppo_level， 用户等级。值只能定义为 普通、银卡会员、金钻会员
"""

import httpx
import json
import re
import time

from datetime import datetime
from fn_print import fn_print
from get_env import get_env
from sendNotify import send_notification_message_collection

oppo_cookies = get_env("oppo_cookie", "@")
USERAGENT = get_env("oppo_user_agent", "#")
LEVEL = get_env("oppo_level", "#")


class Oppo:
    def __init__(self, cookie, user_agent):
        self.user_name = None
        self.cookie = cookie
        self.user_agent = user_agent
        self.oppo_list = re.split(r'[\n&]', cookie) if cookie else []
        self.level = self.validate_level(LEVEL[0])
        self.sign_in_days_map = {
            1327: 3,  # 3天签到领取
            1328: 5,  # 5天签到领取
            1329: 10,  # 10天签到领取
            1330: 15  # 15天签到领取
        }
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
        res = httpx.get(url="https://msec.opposhop.cn/configs/web/advert/230008").json()
        for item in res['data']:
            if item['title'] == '个人中心签到入口':
                details = item.get('details')
                for detail in details:
                    if detail['title'] == '任务中心入口':
                        task_link = detail.get('link')
                        break
                break
        try:
            response = self.client.get(
                url=task_link
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
            if data.get('data'):
                task_list = data['data']['taskDTOList']
                for task in task_list:
                    # 排除黑卡和购物
                    if task.get('taskType') == 6:
                        continue
                    fn_print(f"开始执行【{task.get('taskName')}】任务")
                    self.complete_task(task.get('taskName'), task.get('taskId'), task.get('activityId'))
                    time.sleep(1.5)
                    self.receive_reward(task.get('taskName'), task.get('taskId'), task.get('activityId'))
                    time.sleep(1.5)
            else:
                fn_print(f"获取任务列表失败！-> {data.get('message')}")
        except Exception as e:
            fn_print(f"获取活动ID列表时出错: {e}")
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
        valid_levels = ["普通", "银卡会员", "金钻会员"]
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


def run(self: Oppo):
    if self.level is None:
        return
        
    self.is_login()
    self.get_user_info()
    self.get_task_activity_info()
    self.sign_in()
    sign_in_days = self.get_sign_days()
    self.get_task_list_ids()
    for award_id, days in self.sign_in_days_map.items():
        if sign_in_days >= days:
            self.receive_sign_in_award(award_id=award_id)
        else:
            fn_print(f"**{self.user_name}**，未达到累计{days}天签到要求，跳过领取奖励")


if __name__ == '__main__':
    invalid_level = False
    for cookie in oppo_cookies:
        oppo = Oppo(cookie, USERAGENT[0])
        if oppo.level is None:
            invalid_level = True
        else:
            run(oppo)
    send_notification_message_collection(f"OPPO商城签到通知 - {datetime.now().strftime('%Y/%m/%d')}")
