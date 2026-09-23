# -*- coding=UTF-8 -*-
# @Project          sfsy.py
# @fileName         ctrip.py
# @author           Echo
# @EditTime         2025/5/15
# const $ = new Env('携程旅行');
import json

import httpx

import log
from get_env import get_env

ctrip_cookies = get_env("ctrip_cookie", '@')
print(len(ctrip_cookies))


class Ctrip:
    def __init__(self, cookie):
        self.cookie = cookie
        self.client = httpx.Client(
            headers={
                'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090c33)XWEB/11581",
                'Content-Type': "application/json",
                'cookieorigin': "https://m.ctrip.com",
                'origin': "https://m.ctrip.com",
                'sec-fetch-site': "same-origin",
                'sec-fetch-mode': "cors",
                'sec-fetch-dest': "empty",
                'referer': "https://m.ctrip.com/activitysetupapp/mkt/index/membersignin2021?isHideNavBar=YES&pushcode=miniprogram&mpopenid=28f0ed5e-7f2d-499d-89d2-d7cadca53a4c&ismkt=true&fromminiapp=weixin&allianceid=262684&sid=711465&sourceid=55552689&_cwxobj=%7B%22cid%22%3A%2252271128496542159715%22%2C%22appid%22%3A%22wx0e6ed4f51db9d078%22%2C%22mpopenid%22%3A%2228f0ed5e-7f2d-499d-89d2-d7cadca53a4c%22%2C%22mpunionid%22%3A%22oHkqHt6QTnYDTk5IOXWKrmWUcCeI%22%2C%22allianceid%22%3A%22262684%22%2C%22sid%22%3A%22711465%22%2C%22ouid%22%3A%22%22%2C%22sourceid%22%3A%2255552689%22%2C%22exmktID%22%3A%22%7B%5C%22openid%5C%22%3A%5C%2228f0ed5e-7f2d-499d-89d2-d7cadca53a4c%5C%22%2C%5C%22unionid%5C%22%3A%5C%22oHkqHt6QTnYDTk5IOXWKrmWUcCeI%5C%22%2C%5C%22channelUpdateTime%5C%22%3A%5C%221747296117326%5C%22%2C%5C%22serverFrom%5C%22%3A%5C%22WAP%2FWECHATAPP%5C%22%2C%5C%22innersid%5C%22%3A%5C%22%5C%22%2C%5C%22innerouid%5C%22%3A%5C%22%5C%22%2C%5C%22pushcode%5C%22%3A%5C%22%5C%22%2C%5C%22txCpsId%5C%22%3A%5C%22%5C%22%2C%5C%22search_keywords%5C%22%3A%5C%22%5C%22%2C%5C%22search_type%5C%22%3A%5C%22%5C%22%2C%5C%22amsPid%5C%22%3A%5C%22%5C%22%2C%5C%22gdt_vid%5C%22%3A%5C%22%5C%22%2C%5C%22xhs_click_id%5C%22%3A%5C%22%5C%22%7D%22%2C%22scene%22%3A1131%2C%22personalRecommendSwitch%22%3Atrue%2C%22localRecommendSwitch%22%3Atrue%2C%22marketSwitch%22%3Atrue%2C%22pLen%22%3A2%7D",
                'accept-language': "zh-CN,zh;q=0.9",
                'Cookie': self.cookie,
            },
            verify=False,
            timeout=60
        )

    # def get_user_info(self):
    #     try:
    #         response = self.client.post(
    #             
    #         )

    def sign_in(self):
        try:
            response = self.client.post(
                url="https://m.ctrip.com/restapi/soa2/22769/signToday",
                json={}
            )
            response.raise_for_status()
            sign_in_status = response.json()
            if sign_in_status.get("code") == 0 and sign_in_status.get("message") == "SUCCESS":
                log.log(f"**用户: {1}**, 签到成功！✅获取{sign_in_status.get('baseIntegratedPoint')}积分！")
            else:
                log.log(sign_in_status.get("message"))
        except Exception as e:
            log.log("签到异常❌\n", e)

    def get_task_list(self):
        try:
            response = self.client.post(
                url="https://m.ctrip.com/restapi/soa2/22598/userTaskList",
                json={
                    "channelCode": "2H3294O46M",
                    "extMap": {
                        "mktTaskSort": ""
                    },
                    "oAuthHead": {},
                    "version": "4",
                    "osType": "android",
                    "appVersion": "",
                    "subOsType": "",
                    "_locale": "zh-CN",
                    "head": {
                        "ctok": "",
                        "cver": "1.0",
                        "lang": "01",
                        "sid": "8888",
                        "syscode": "09",
                        "auth": "",
                        "xsid": "",
                        "extension": []
                    }
                }
            )
            response.raise_for_status()
            task_list = response.json()
            todo_task_list = task_list.get('todoTaskList')
            for task in todo_task_list:
                task_id = task.get('id')
                self.todo_task(task_id)
                if "关注" in task.get('eventName'):
                    task_name = task.get('displayName')
                    log.log(f"***开始处理 {task_name} 任务...***")
                    focus_id = task.get('h5Url').split('clientAuth=')[1].split('&')[0]
                    if self.handle_focus_task(focus_id):
                        self.obtain_task_award(task_id)
        except Exception as e:
            log.log("获取任务列表异常❌\n", e)

    def todo_task(self, task_id):
        """ 领取任务 """
        try:
            response = self.client.post(
                url="https://m.ctrip.com/restapi/soa2/22598/todoTask",
                json={
                    "allianceid": "4897",
                    "sid": "130026",
                    "ouid": "",
                    "sourceid": "",
                    "pushcode": "h5main",
                    "innersid": "",
                    "innerouid": "",
                    "channelCode": "2H3294O46M",
                    "taskId": task_id,
                    "status": 0,
                    "done": 0,
                    "oAuthHead": {},
                    "platform": "H5",
                    "version": "4",
                    "osType": "android",
                    "appVersion": "",
                    "subOsType": "",
                    "_locale": "zh-CN",
                    "head": {
                        "ctok": "",
                        "cver": "1.0",
                        "lang": "01",
                        "sid": "8888",
                        "syscode": "09",
                        "auth": "",
                        "xsid": "",
                        "extension": []
                    }
                }
            )
            response.raise_for_status()
            task_list = response.json()

        except Exception as e:
            log.log("获取任务列表异常❌\n", e)

    def handle_focus_task(self, focus_id):
        try:
            response = self.client.post(
                url="https://m.ctrip.com/restapi/soa2/16225/json/attention",
                json={
                    "starCtripUid": focus_id,
                    "head": {
                        "ctok": "",
                        "cver": "1.0",
                        "lang": "01",
                        "sid": "8888",
                        "syscode": "09",
                        "auth": "",
                        "xsid": "",
                        "extension": []
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            if data.get('ResponseStatus').get('Ack') == 'Success':
                log.log("任务完成！")
                return True
            else:
                log.log("任务失败！")
                return False
        except Exception as e:
            log.log("处理关注任务异常❌\n", e)
            return False

    def obtain_task_award(self, task_id):
        try:
            response = self.client.post(
                url="https://m.ctrip.com/restapi/soa2/22598/awardTask",
                json={
                    "channelCode": "2H3294O46M",
                    "taskId": task_id,
                    "platform": "H5",
                    "oAuthHead": {},
                    "version": "4",
                    "osType": "android",
                    "appVersion": "",
                    "subOsType": "",
                    "ouid": "",
                    "sourceid": "",
                    "pushcode": "h5main",
                    "innersid": "",
                    "innerouid": "",
                    "head": {
                        "ctok": "",
                        "cver": "1.0",
                        "lang": "01",
                        "sid": "8888",
                        "syscode": "09",
                        "auth": "",
                        "xsid": "",
                        "extension": []
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            if data.get('ResponseStatus').get('Ack') == 'Success':
                if data.get('code') == 200:
                    log.log("奖励领取成功！")
                elif data.get('code') == 40015:
                    log.log(f"{data.get('message')}")
                else:
                    log.log(f"奖励领取失败！{data}")
            else:
                log.log("奖励领取失败！")
        except Exception as e:
            log.log("领取奖励异常❌\n", e)


if __name__ == '__main__':
    for ctrip_cookie in ctrip_cookies:
        ctrip = Ctrip(ctrip_cookie)
        ctrip.sign_in()
        ctrip.get_task_list()
