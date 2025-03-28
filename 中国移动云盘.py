# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         中国移动云盘.py
# @author           Echo
# @EditTime         2024/11/4
# cron: 0 0 8 * * *
# const $ = new Env('中国移动云盘');
"""
设置环境变量，ydyp_ck，格式 Basic XXXXXXXX#手机号#token
多个账号用@分割
"""
import asyncio
import json
import os
import random
import re
import time
import urllib.parse
from datetime import datetime

import httpx
import requests

from fn_print import fn_print
from get_env import get_env
from sendNotify import send_notification_message_collection

ua = "Mozilla/5.0 (Linux; Android 11; M2012K10C Build/RP1A.200720.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/90.0.4430.210 Mobile Safari/537.36 MCloudApp/10.0.1"

ydyp_ck = get_env("ydyp_ck", "@")

is_redeem = False  # 是否兑换
redeem_reward_description = ""  # 兑换的奖品描述，比如哔哩哔哩会员月卡、网易云音乐月卡、移动云盘钻石会员季卡


class MobileCloudDisk:
    def __init__(self, cookie):
        self.client = httpx.AsyncClient(verify=False, timeout=60)
        self.notebook_id = None
        self.note_token = None
        self.note_auth = None
        self.click_num = 15  # 定义抽奖次数和抽抽乐-享好礼戳一戳次数
        self.draw = 1  # 定义抽奖次数，首次免费
        self.timestamp = str(int(round(time.time() * 1000)))
        self.cookies = {'sensors_stay_time': self.timestamp}
        self.Authorization = cookie.split("#")[0]
        self.account = cookie.split("#")[1]
        self.auth_token = cookie.split("#")[2]
        self.encrypt_account = self.account[:3] + "*" * 4 + self.account[7:]
        # self.rmkey = cookie.split("#")[3]
        # self.Os_SSo_Sid = cookie.split("#")[4]
        self.fruit_url = 'https://happy.mail.10086.cn/jsp/cn/garden/'
        self.JwtHeaders = {
            'User-Agent': ua,
            'Accept': '*/*',
            'Host': 'caiyun.feixin.10086.cn:7071'
        }
        self.treetHeaders = {
            'Host': 'happy.mail.10086.cn',
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': ua,
            'Referer': 'https://happy.mail.10086.cn/jsp/cn/garden/wap/index.html?sourceid=1003'
        }

    async def refresh_token(self):
        responses = await self.client.post(
            url='https://orches.yun.139.com/orchestration/auth-rebuild/token/v1.0/querySpecToken',
            headers={
                'Authorization': self.Authorization,
                'User-Agent': ua,
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Host': 'orches.yun.139.com'
            },
            json={
                "account": self.account,
                "toSourceId": "001005"
            }
        )
        refresh_token_responses = responses.json()
        if refresh_token_responses["success"]:
            refresh_token = refresh_token_responses["data"]["token"]
            return refresh_token
        else:
            fn_print(refresh_token_responses)
            return None

    async def jwt(self):
        token = await self.refresh_token()
        if token is not None:
            jwt_url = f"https://caiyun.feixin.10086.cn:7071/portal/auth/tyrzLogin.action?ssoToken={token}"
            jwt_response = await self.client.post(
                url=jwt_url,
                headers=self.JwtHeaders
            )
            jwt_datas = jwt_response.json()
            if jwt_datas["code"] != 0:
                fn_print(jwt_datas["msg"])
                return False
            self.JwtHeaders["jwtToken"] = jwt_datas["result"]["token"]
            self.cookies["jwtToken"] = jwt_datas["result"]["token"]
            return True
        else:
            fn_print("cookie可能失效了")
            return False

    async def query_sign_in_status(self):
        """
        查询签到状态
        :return: 
        """
        sign_response_datas = await self.client.get(
            url="https://caiyun.feixin.10086.cn/market/signin/page/info?client=app",
            headers=self.JwtHeaders,
            cookies=self.cookies
        )
        if sign_response_datas.status_code == 200:
            sign_response_data = sign_response_datas.json()
            if sign_response_data["msg"] == "success":
                today_sign = sign_response_data["result"].get("todaySignIn", False)
                if today_sign:
                    fn_print(f"用户【{self.account}】，===今日已签到☑️===")
                else:
                    await self.sign_in()
        else:
            fn_print(f"签到查询状态异常：{sign_response_datas.status_code}")

    async def a_poke(self):
        """
        戳一戳
        :return: 
        """
        url = "https://caiyun.feixin.10086.cn/market/signin/task/click?key=task&id=319"
        successful_click = 0  # 获得次数
        try:
            for _ in range(self.click_num):
                responses = await self.client.get(
                    url=url,
                    headers=self.JwtHeaders,
                    cookies=self.cookies
                )
                time.sleep(0.5)
                if responses.status_code == 200:
                    responses_data = responses.json()
                    if "result" in responses_data:
                        fn_print(f"用户【{self.account}】，===戳一戳成功✅✅===, {responses_data['result']}")
                        successful_click += 1
                else:
                    fn_print(f"戳一戳发生异常：{responses.status_code}")
            if successful_click == 0:
                fn_print(f"用户【{self.account}】，===未获得 x {self.click_num}===")
        except Exception as e:
            fn_print(f"戳一戳执行异常：{e}")

    async def refresh_notetoken(self):
        """
        刷新noteToken
        :return: 
        """
        note_url = 'http://mnote.caiyun.feixin.10086.cn/noteServer/api/authTokenRefresh.do'
        note_payload = {
            "authToken": self.auth_token,
            "userPhone": self.account
        }
        note_headers = {
            'X-Tingyun-Id': 'p35OnrDoP8k;c=2;r=1122634489;u=43ee994e8c3a6057970124db00b2442c::8B3D3F05462B6E4C',
            'Charset': 'UTF-8',
            'Connection': 'Keep-Alive',
            'User-Agent': 'mobile',
            'APP_CP': 'android',
            'CP_VERSION': '3.2.0',
            'x-huawei-channelsrc': '10001400',
            'Host': 'mnote.caiyun.feixin.10086.cn',
            'Content-Type': 'application/json; charset=UTF-8',
            'Accept-Encoding': 'gzip'
        }
        try:
            response = await self.client.post(
                url=note_url,
                data=note_payload,
                headers=note_headers
            )
            if response.status_code == 200:
                response.raise_for_status()
        except Exception as e:
            fn_print('出错了:', e)
            return
        self.note_token = response.headers.get('NOTE_TOKEN')
        self.note_auth = response.headers.get('APP_AUTH')

    async def get_task_list(self, url, app_type):
        """
        获取任务列表
        :return: 
        """
        task_url = f'https://caiyun.feixin.10086.cn/market/signin/task/taskList?marketname={url}'
        task_response = await self.client.get(
            url=task_url,
            headers=self.JwtHeaders,
            cookies=self.cookies
        )
        if task_response.status_code == 200:
            task_list = {}
            task_response_data = task_response.json()
            await self.rm_sleep()
            if task_response_data["msg"] == "success":
                task_list = task_response_data.get("result", {})
            try:
                for task_type, tasks in task_list.items():
                    if task_type in ["new", "hidden", "hiddenabc"]:
                        continue
                    if app_type == "cloud_app":
                        if task_type == "month":
                            fn_print("\n🗓️云盘每月任务")
                            for month in tasks:
                                task_id = month.get("id")
                                if task_id in [110, 113, 417, 409]:
                                    continue
                                task_name = month.get("name", "")
                                task_status = month.get("state", "")

                                if task_status == "FINISH":
                                    fn_print(f"【{self.account}】，===任务【{task_name}】已完成✅✅===")
                                    continue
                                fn_print(f"【{self.account}】，===任务【{task_name}】待完成✒️✒️===")
                                await self.do_task(task_id, task_type="month", app_type="cloud_app")
                                await asyncio.sleep(2)
                        elif task_type == "day":
                            fn_print("\n🗓️云盘每日任务")
                            for day in tasks:
                                task_id = day.get("id")
                                if task_id == 404:
                                    continue
                                task_name = day.get("name", "")
                                task_status = day.get("state", "")
                                if task_status == "FINISH":
                                    fn_print(f"【{self.account}】，===任务【{task_name}】已完成✅✅===")
                                    continue
                                fn_print(f"【{self.account}】，===任务【{task_name}】待完成✒️✒️===")
                                await self.do_task(task_id, task_type="day", app_type="cloud_app")
                    elif app_type == "email_app":
                        if task_type == "month":
                            fn_print("\n🗓️139邮箱每月任务")
                            for month in tasks:
                                task_id = month.get("id")
                                task_name = month.get("name", "")
                                task_status = month.get("state", "")
                                if task_id in [1004, 1005, 1015, 1020]:
                                    continue
                                if task_status == "FINISH":
                                    fn_print(f"【{self.account}】，===任务【{task_name}】已完成✅✅===")
                                    continue
                                fn_print(f"【{self.account}】，===任务【{task_name}】待完成✒️✒️===")
                                await self.do_task(task_id, task_type="month", app_type="email_app")
                                await asyncio.sleep(2)
            except Exception as e:
                fn_print(f"任务列表获取异常，错误信息：{e}")

    async def do_task(self, task_id, task_type, app_type):
        """
        执行任务
        :param task_id: 
        :param task_type: 
        :param app_type: 
        :return: 
        """
        await self.rm_sleep()
        task_url = f'https://caiyun.feixin.10086.cn/market/signin/task/click?key=task&id={task_id}'
        await self.client.get(
            url=task_url,
            headers=self.JwtHeaders,
            cookies=self.cookies
        )
        if app_type == "cloud_app":
            if task_type == "day":
                if task_id == 106:
                    await self.upload_file()
                elif task_id == 107:
                    await self.refresh_notetoken()
                    await self.get_notebook_id()
            elif task_type == "month":
                pass
        elif app_type == "email_app":
            if task_type == "month":
                pass

    async def sign_in(self):
        """
        签到
        :return: 
        """
        sign_in_url = 'https://caiyun.feixin.10086.cn/market/manager/commonMarketconfig/getByMarketRuleName?marketName=sign_in_3'
        sign_in_response = await self.client.get(
            url=sign_in_url,
            headers=self.JwtHeaders,
            cookies=self.cookies
        )
        if sign_in_response.status_code == 200:
            sign_in_response_data = sign_in_response.json()
            if sign_in_response_data["msg"] == "success":
                fn_print(f"用户【{self.account}】，===签到成功✅✅===")
            else:
                fn_print(sign_in_response_data)
        else:
            fn_print(f"签到发生异常：{sign_in_response.status_code}")

    async def get_notebook_id(self):
        """
        获取笔记的默认id
        :return: 
        """
        note_url = 'http://mnote.caiyun.feixin.10086.cn/noteServer/api/syncNotebookV3.do'
        headers = {
            'X-Tingyun-Id': 'p35OnrDoP8k;c=2;r=1122634489;u=43ee994e8c3a6057970124db00b2442c::8B3D3F05462B6E4C',
            'Charset': 'UTF-8',
            'Connection': 'Keep-Alive',
            'User-Agent': 'mobile',
            'APP_CP': 'android',
            'CP_VERSION': '3.2.0',
            'x-huawei-channelsrc': '10001400',
            'APP_NUMBER': self.account,
            'APP_AUTH': self.note_auth,
            'NOTE_TOKEN': self.note_token,
            'Host': 'mnote.caiyun.feixin.10086.cn',
            'Content-Type': 'application/json; charset=UTF-8',
            'Accept': '*/*'
        }
        payload = {
            "addNotebooks": [],
            "delNotebooks": [],
            "notebookRefs": [],
            "updateNotebooks": []
        }
        note_response = await self.client.post(
            url=note_url,
            headers=headers,
            json=payload
        )
        if note_response.status_code == 200:
            note_response_data = note_response.json()
            self.notebook_id = note_response_data["notebooks"][0]["notebookId"]
            if self.notebook_id:
                await self.create_note(headers)
        else:
            fn_print(f"获取笔记id发生异常：{note_response.status_code}")

    async def wx_app_sign(self):
        """
        微信公众号签到
        :return: 
        """
        await self.rm_sleep()
        wx_sign_url = 'https://caiyun.feixin.10086.cn/market/playoffic/followSignInfo?isWx=true'
        wx_sign_response = await self.client.get(
            url=wx_sign_url,
            headers=self.JwtHeaders,
            cookies=self.cookies
        )
        if wx_sign_response.status_code == 200:
            wx_sign_response_data = wx_sign_response.json()
            if wx_sign_response_data["msg"] == "success":
                fn_print(f"用户【{self.account}】，===微信公众号签到成功✅✅===")
            if not wx_sign_response_data["result"].get("todaySignIn"):
                fn_print(f"用户【{self.account}】，===微信公众号签到失败，可能未绑定公众号❌===")
        else:
            fn_print(f"签到发生异常：{wx_sign_response.status_code}")

    async def shake(self):
        """
        抽抽乐-享好礼
        :return: 
        """
        successful_shake = 0
        try:
            for _ in range(self.click_num):
                responses = await self.client.post(
                    url="https://caiyun.feixin.10086.cn:7071/market/shake-server/shake/shakeIt?flag=1",
                    headers=self.JwtHeaders,
                    cookies=self.cookies
                )
                if responses.status_code == 200:
                    shake_response_data = responses.json()
                    await asyncio.sleep(1)
                    shake_prize_config = shake_response_data["result"].get("shakePrizeConfig")
                    if shake_prize_config:
                        fn_print(
                            f"用户【{self.account}】，===抽抽乐-享好礼抽奖成功✅✅===, 获得：{shake_prize_config['name']}🎉🎉")
                        successful_shake += 1
                    else:
                        fn_print(f"抽抽乐-享好礼抽奖未中奖")
                else:
                    fn_print(f"抽抽乐-享好礼抽奖发生异常：{responses.status_code}")
        except Exception as e:
            fn_print(f"抽抽乐-享好礼执行异常：{e}")
        if successful_shake == 0:
            fn_print(f"用户【{self.account}】，===未抽中 x {self.click_num}❌===")

    async def surplus_num(self):
        """
        查询剩余抽奖次数
        :return: 
        """
        await self.rm_sleep()
        draw_info_url = 'https://caiyun.feixin.10086.cn/market/playoffic/drawInfo'
        draw_url = "https://caiyun.feixin.10086.cn/market/playoffic/draw"

        draw_info_response = await self.client.get(
            url=draw_info_url,
            headers=self.JwtHeaders
        )
        if draw_info_response.status_code == 200:
            draw_info_data = draw_info_response.json()
            if draw_info_data.get('msg') == "success":
                remain_num = draw_info_data["result"].get("surplusNumber", 0)
                fn_print(f"剩余抽奖次数{remain_num}")
                if remain_num > 50 - self.draw:
                    for _ in range(self.draw):
                        await self.rm_sleep()
                        draw_responses = await self.client.get(
                            url=draw_url,
                            headers=self.JwtHeaders
                        )
                        if draw_responses.status_code == 200:
                            draw_data = draw_responses.json()
                            if draw_data.get("code") == 0:
                                prize_name = draw_data["result"].get("prizeName", "")
                                fn_print(f"用户【{self.account}】，===抽奖成功✅✅===, 获得：{prize_name}🎉🎉")
                            else:
                                fn_print(f"抽奖失败了❌：{draw_data}")
                        else:
                            fn_print(f"抽奖发生异常：{draw_responses.status_code}")
                else:
                    pass
            else:
                fn_print(f"查询剩余抽奖次数发生异常：{draw_info_data.get('msg')}")
        else:
            fn_print(f"查询剩余抽奖次数发生异常：{draw_info_response.status_code}")

    async def fruit_login(self):
        """
        果园
        :return: 
        """
        token = await self.refresh_token()
        if token is not None:
            fn_print(f"用户【{self.account}】，===果园专区Token刷新成功✅✅===")
            await self.rm_sleep()
            login_info_url = f'{self.fruit_url}login/caiyunsso.do?token={token}&account={self.account}&targetSourceId=001208&sourceid=1003&enableShare=1'
            headers = {
                'Host': 'happy.mail.10086.cn', 'Upgrade-Insecure-Requests': '1', 'User-Agent': ua,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Referer': 'https://caiyun.feixin.10086.cn:7071/',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
            }
            login_info_data = requests.request("""GET""", login_info_url, headers=headers, verify=False)
            treeCookie = login_info_data.request.headers['Cookie']
            self.treetHeaders['Cookie'] = treeCookie
            do_login_url = f'{self.fruit_url}login/userinfo.do'
            do_login_response = await self.client.get(
                url=do_login_url,
                headers=self.treetHeaders
            )
            if do_login_response.status_code == 200:
                do_login_data = do_login_response.json()
                if do_login_data.get('result', {}).get('islogin') != 1:
                    fn_print(f"用户【{self.account}】，===果园专区登录失败❌===")
                    return
                await self.fruit_task()
            else:
                fn_print(f"果园专区登录请求发生异常：{do_login_response.status_code}")
        else:
            fn_print(f"用户【{self.account}】，===果园专区Token刷新失败❌===")

    async def fruit_task(self):
        """
        果园专区任务
        :return: 
        """
        # 签到
        check_sign_responses = await self.client.get(
            url=f"{self.fruit_url}task/checkinInfo.do",
            headers=self.treetHeaders
        )
        if check_sign_responses.status_code == 200:
            check_sign_data = check_sign_responses.json()
            if check_sign_data.get("success"):
                today_checkin = check_sign_data.get("result", {}).get("todayCheckin", 0)
                if today_checkin == 1:
                    fn_print(f"用户【{self.account}】，===今日已签到☑️☑️===")
                else:
                    check_in_data = await self.client.get(
                        url=f"{self.fruit_url}task/checkin.do",
                        headers=self.treetHeaders
                    )
                    if check_in_data.status_code == 200:
                        check_in_data = check_in_data.json()
                        if check_in_data.get("result", {}).get("code", "") == 1:
                            fn_print(f"用户【{self.account}】，===签到成功✅✅===")
                            await self.rm_sleep()
                            water_response = await self.client.get(
                                url=f'{self.fruit_url}user/clickCartoon.do?cartoonType=widget',
                                headers=self.treetHeaders
                            )
                            if water_response.status_code == 200:
                                water_data = water_response.json()
                            else:
                                fn_print(f"领取水滴请求发生异常：{water_response.status_code}")
                            color_response = await self.client.get(
                                url=f'{self.fruit_url}user/clickCartoon.do?cartoonType=color',
                                headers=self.treetHeaders
                            )
                            if color_response.status_code == 200:
                                color_data = color_response.json()
                            else:
                                fn_print(f"领取每日雨滴请求发生异常：{color_response.status_code}")
                            given_water = water_data.get("result", {}).get("given", 0)
                            fn_print(f"用户【{self.account}】，===领取每日水滴💧💧：{given_water}===")
                            fn_print(f"用户【{self.account}】，===领取每日雨滴💧💧：{color_data.get('result').get('msg')}===")
                        else:
                            fn_print(f"用户【{self.account}】，===签到失败❌===")
                    else:
                        fn_print(f"签到请求发生异常：{check_in_data.status_code}")
            else:
                fn_print(f"用户【{self.account}】，===果园签到查询失败❌, {check_sign_data.get('msg')}===")
            # 获取任务列表
            task_list_responses = await self.client.get(
                url=f'{self.fruit_url}task/taskList.do?clientType=PE',
                headers=self.treetHeaders
            )
            if task_list_responses.status_code == 200:
                task_list_data = task_list_responses.json()
                task_list = task_list_data.get('result', [])
            else:
                fn_print(f"任务列表请求发生异常：{task_list_responses.status_code}")
            task_state_responses = await self.client.get(
                url=f'{self.fruit_url}task/taskState.do',
                headers=self.treetHeaders
            )
            if task_state_responses.status_code == 200:
                task_state_data = task_state_responses.json()
                task_state_result = task_state_data.get('result', [])
            else:
                fn_print(f"任务状态请求发生异常：{task_state_responses.status_code}")
            for task in task_list:
                task_id = task.get('taskId', "")
                task_name = task.get('taskName', "")
                water_num = task.get('waterNum', 0)
                if task_id == 2002 or task_id == 2003:
                    continue
                task_state = next(
                    (state.get('taskState', 0) for state in task_state_result if state.get('taskId') == task_id), 0)
                if task_state == 2:
                    fn_print(f"用户【{self.account}】，===任务【{task_name}】已完成✅✅===")
                else:
                    await self.do_fruit_task(task_name, task_id, water_num)
            await self.tree_info()
        else:
            fn_print(f"签到请求发生异常：{check_sign_responses.status_code}")

    async def do_fruit_task(self, task_name, task_id, water_num):
        """
        执行果园任务
        :param task_name: 
        :param task_id: 
        :param water_num: 
        :return: 
        """
        fn_print(f"用户【{self.account}】，===任务【{task_name}】开始执行🚀🚀===")
        do_task_url = f'{self.fruit_url}task/doTask.do?taskId={task_id}'
        do_task_response = await self.client.get(
            url=do_task_url,
            headers=self.treetHeaders
        )
        if do_task_response.status_code == 200:
            do_task_data = do_task_response.json()
            if do_task_data.get("success"):
                get_water_url = f'{self.fruit_url}task/givenWater.do?taskId={task_id}'
                get_water_response = await self.client.get(
                    url=get_water_url,
                    headers=self.treetHeaders
                )
                if get_water_response.status_code == 200:
                    get_water_data = get_water_response.json()
                    if get_water_data.get("success"):
                        fn_print(f"用户【{self.account}】，===已完成任务【{task_name}】✅✅，领取水滴: {water_num}===")
                    else:
                        fn_print(
                            f"用户【{self.account}】，===任务【{task_name}】领取水滴失败❌, {get_water_data.get('msg')}===")
                else:
                    fn_print(f"领取水滴请求发生异常：{get_water_response.status_code}")
            else:
                fn_print(f"用户【{self.account}】，===任务【{task_name}】执行失败❌, {do_task_data.get('msg')}===")
        else:
            fn_print(f"任务执行请求发生异常：{do_task_response.status_code}")

    async def tree_info(self):
        """
        查询果园信息
        :return: 
        """
        tree_info_url = f'{self.fruit_url}user/treeInfo.do'
        tree_info_responses = await self.client.get(
            url=tree_info_url,
            headers=self.treetHeaders
        )
        if tree_info_responses.status_code == 200:
            tree_info_data = tree_info_responses.json()
            if not tree_info_data.get("success"):
                fn_print(f"用户【{self.account}】，===获取果园任务列表失败❌, {tree_info_data.get('msg')}===")
            else:
                collect_water = tree_info_data.get("result", {}).get("collectWater", 0)
                tree_level = tree_info_data.get("result", {}).get("treeLevel", 0)
                fn_print(f"用户【{self.account}】，===当前小树等级：{tree_level}，剩余水滴：{collect_water}===")
                if tree_level in (2, 4, 6, 8):
                    # 开宝箱
                    openbox_url = f'{self.fruit_url}prize/openBox.do'
                    openbox_response = await self.client.get(
                        url=openbox_url,
                        headers=self.treetHeaders
                    )
                    if openbox_response.status_code == 200:
                        openbox_data = openbox_response.json()
                        fn_print(f"用户【{self.account}】，==={openbox_data.get('msg')}===")
                    else:
                        fn_print(f"开宝箱请求发生异常：{openbox_response.status_code}")
                watering_amout = collect_water // 20  # 计算需要浇水的次数
                watering_url = f'{self.fruit_url}user/watering.do?isFast=0'
                if watering_amout > 0:
                    for index in range(watering_amout):
                        watering_response = await self.client.get(
                            url=watering_url,
                            headers=self.treetHeaders
                        )
                        if watering_response.status_code == 200:
                            watering_data = watering_response.json()
                            if watering_data.get("success"):
                                fn_print(f"用户【{self.account}】，===已完成{index + 1}次浇水🌊🌊===")
                            else:
                                fn_print(f"用户【{self.account}】，===浇水失败❌, {watering_data.get('msg')}===")
                            await asyncio.sleep(3)
                        else:
                            fn_print(f"浇水请求发生异常：{watering_response.status_code}")
                else:
                    fn_print(f"用户【{self.account}】，===水滴不足，无法浇水❌===")
        else:
            fn_print(f"查询果园信息请求发生异常：{tree_info_responses.status_code}")

    async def cloud_game(self):
        """
        云朵大作战
        :return: 
        """
        game_info_url = 'https://caiyun.feixin.10086.cn/market/signin/hecheng1T/info?op=info'
        bigin_url = 'https://caiyun.feixin.10086.cn/market/signin/hecheng1T/beinvite'
        end_url = 'https://caiyun.feixin.10086.cn/market/signin/hecheng1T/finish?flag=true'
        game_info_response = await self.client.get(
            url=game_info_url,
            headers=self.JwtHeaders,
            cookies=self.cookies
        )
        if game_info_response.status_code == 200:
            game_info_data = game_info_response.json()
            if game_info_data and game_info_data.get("code", -1) == 0:
                curr_num = game_info_data.get("result", {}).get("info", {}).get("curr", 0)
                count = game_info_data.get("result", {}).get("history", {}).get("0", {}).get("count", '')
                rank = game_info_data.get("result", {}).get("history", {}).get("0", {}).get("rank", '')
                fn_print(f"今日剩余游戏次数：{curr_num}\n本月排名：{rank}\n合成次数：{count}")
                for _ in range(curr_num):
                    await self.client.get(
                        url=bigin_url,
                        headers=self.JwtHeaders,
                        cookies=self.cookies
                    )
                    fn_print("开始游戏， 等待10-15秒完成游戏")
                    await asyncio.sleep(random.randint(10, 15))
                    end_response = await self.client.get(
                        url=end_url,
                        headers=self.JwtHeaders,
                        cookies=self.cookies
                    )
                    if end_response.status_code == 200:
                        end_data = end_response.json()
                        if end_data and end_data.get("code", -1) == 0:
                            fn_print(f"用户【{self.account}】，===云朵大作战游戏成功✅✅===")
                        else:
                            fn_print(f"用户【{self.account}】，===云朵大作战游戏失败❌===")
                    else:
                        fn_print(f"用户【{self.account}】，===获取云朵大作战游戏信息失败❌===")
            else:
                fn_print(f"用户【{self.account}】，===获取云朵大作战游戏信息失败❌===")
        else:
            fn_print(f"云朵大作战请求发生异常：{game_info_response.status_code}")

    async def receive(self):
        """
        领取云朵
        :return: 
        """
        recevice_url = "https://caiyun.feixin.10086.cn/market/signin/page/receive"
        prize_url = f"https://caiyun.feixin.10086.cn/market/prizeApi/checkPrize/getUserPrizeLogPage?currPage=1&pageSize=15&_={self.timestamp}"
        receive_response = await self.client.get(
            url=recevice_url,
            headers=self.JwtHeaders,
            cookies=self.cookies
        )
        if receive_response.status_code == 200:
            receive_data = receive_response.json()
            await self.rm_sleep()
        else:
            fn_print(f"领取云朵请求发生异常：{receive_response.status_code}")
        prize_response = await self.client.get(
            url=prize_url,
            headers=self.JwtHeaders,
            cookies=self.cookies
        )
        if prize_response.status_code == 200:
            prize_data = prize_response.json()
            result = prize_data.get("result").get("result")
            rewards = ""
            for value in result:
                prize_name = value.get("prizeName")
                flag = value.get("flag")
                if flag == 1:
                    rewards += f"待领取奖品：{prize_name}\n"
            receive_amout = receive_data["result"].get("receive", "")
            total_amout = receive_data["result"].get("total", "")
            fn_print(f"\n用户【{self.account}】，===当前待领取{receive_amout}个云朵===")
            fn_print(f"用户【{self.account}】，===当前云朵数量：{total_amout}个===")
            fn_print(f"用户【{self.account}】，===云朵数量：{total_amout}个，{rewards}===")
        else:
            fn_print(f"领取奖品请求发生异常：{prize_response.status_code}")

    async def backup_cloud(self):
        """
        备份云朵
        :return: 
        """
        backup_url = 'https://caiyun.feixin.10086.cn/market/backupgift/info'
        backup_response = await self.client.get(
            url=backup_url,
            headers=self.JwtHeaders
        )
        if backup_response.status_code == 200:
            backup_data = backup_response.json()
            state = backup_data.get("result", {}).get("state", {})
            if state == -1:
                fn_print(f"用户【{self.account}】，===本月未备份，暂无连续备份奖励❌===")
            elif state == 0:
                fn_print(f"用户【{self.account}】，===领取本月连续备份奖励===")
                cur_url = 'https://caiyun.feixin.10086.cn/market/backupgift/receive'
                cur_response = await self.client.get(
                    url=cur_url,
                    headers=self.JwtHeaders
                )
                if cur_response.status_code == 200:
                    cur_data = cur_response.json()
                    if isinstance(cur_data.get('result'), int):
                        fn_print(f"异常：{cur_data.get('result')}")
                    fn_print(f"用户【{self.account}】，===获得云朵数量：{cur_data.get('result').get('result')}===")
                else:
                    fn_print(f"用户【{self.account}】，===获取云朵数量请求失败❌，{cur_response.status_code}===")
            elif state == 1:
                fn_print(f"用户【{self.account}】，===已领取本月连续备份奖励===")
            else:
                fn_print(f"用户【{self.account}】，===获取本月连续备份奖励状态异常❌，{backup_data}===")
        else:
            fn_print(f"用户【{self.account}】，===领取本月连续备份奖励请求失败❌，{backup_response.status_code}===")
        await self.rm_sleep()
        # 每月膨胀云朵
        expend_url = 'https://caiyun.feixin.10086.cn/market/signin/page/taskExpansion'
        expend_response = await self.client.get(
            url=expend_url,
            headers=self.JwtHeaders
        )
        if expend_response.status_code == 200:
            expend_data = expend_response.json()
        else:
            fn_print(f"用户【{self.account}】，===每月膨胀云朵请求失败❌，{expend_response.status_code}===")
        cur_month_backup = expend_data.get("result", {}).get("curMonthBackup", "")  # 本月备份
        pre_month_backup = expend_data.get("result", {}).get("preMonthBackup", "")  # 上月备份
        cur_month_backup_task_accept = expend_data.get("result", {}).get("curMonthBackupTaskAccept", "")  # 本月是否领取
        next_month_backup_task_record_count = expend_data.get("result", {}).get("nextMonthBackupTaskRecordCount",
                                                                                "")  # 下月备份云朵
        accept_date = expend_data.get("result", {}).get("aeptDate", "")  # 月份

        if cur_month_backup:
            fn_print(f"用户【{self.account}】，===本月已备份，下月可领取膨胀云朵: {next_month_backup_task_record_count}===")
        else:
            fn_print(f"用户【{self.account}】，===本月未备份，下月暂无膨胀云朵===")

        if pre_month_backup:
            if cur_month_backup_task_accept:
                fn_print(f"用户【{self.account}】，===上月已备份，膨胀云朵已领取===")
            else:
                receive_url = f'https://caiyun.feixin.10086.cn/market/signin/page/receiveTaskExpansion?acceptDate={accept_date}'
                receive_response = await self.client.get(
                    url=receive_url,
                    headers=self.JwtHeaders,
                    cookies=self.cookies
                )
                if receive_response.status_code == 200:
                    receive_data = receive_response.json()
                    if receive_data.get("code") != 0:
                        fn_print(f"用户【{self.account}】，===领取膨胀云朵失败❌，{receive_data.get('msg')}===")
                    else:
                        fn_print(
                            f"用户【{self.account}】，===领取膨胀云朵成功✅✅, {receive_data.get('result', {}).get('cloudCount'), ''}朵===")
                else:
                    fn_print(f"用户【{self.account}】，===领取膨胀云朵请求失败❌，{receive_response.status_code}===")
        else:
            fn_print(f"用户【{self.account}】，===上月未备份，本月暂无膨胀云朵===")

    async def open_send(self):
        """
        通知云朵
        :return: 
        """
        send_url = 'https://caiyun.feixin.10086.cn/market/msgPushOn/task/status'
        send_response = await self.client.get(
            url=send_url,
            headers=self.JwtHeaders
        )
        if send_response.status_code == 200:
            send_data = send_response.json()
            push_on = send_data.get("result", {}).get("pushOn", "")  # 0未开启，1开启，2未领取，3已领取
            first_task_status = send_data.get("result", {}).get("firstTaskStatus", "")
            second_task_status = send_data.get("result", {}).get("secondTaskStatus", "")
            on_duaration = send_data.get("result", {}).get("onDuration", "")  # 开启时间
            if push_on == 1:
                reward_url = 'https://caiyun.feixin.10086.cn/market/msgPushOn/task/obtain'
                if first_task_status == 3:
                    fn_print(f"用户【{self.account}】，===领取任务1奖励成功✅✅===")
                else:
                    reward_response = await self.client.post(
                        url=reward_url,
                        headers=self.JwtHeaders,
                        json={"type": 1}
                    )
                    if reward_response.status_code == 200:
                        reward_data = reward_response.json()
                        fn_print(f"用户【{self.account}】，===领取任务1奖励成功✅✅===")
                    else:
                        fn_print(f"用户【{self.account}】，===领取任务1奖励请求失败❌，{reward_response.status_code}===")
                if second_task_status == 2:
                    reward2_response = await self.client.post(
                        url=reward_url,
                        headers=self.JwtHeaders,
                        json={"type": 2}
                    )
                    if reward2_response.status_code == 200:
                        reward_data = reward2_response.json()
                        fn_print(f"用户【{self.account}】，===领取任务2奖励成功✅✅===")
                    else:
                        fn_print(f"用户【{self.account}】，===领取任务2奖励请求失败❌，{reward2_response.status_code}===")
                fn_print(f"用户【{self.account}】，===通知已开启天数: {on_duaration}, 满31天可领取奖励===")
            else:
                fn_print(f"用户【{self.account}】，===未开启通知权限===")
        else:
            fn_print(f"用户【{self.account}】，===开启通知云朵请求失败❌，{send_response.status_code}===")

    async def create_note(self, headers):
        """
        创建笔记
        :return: 
        """
        note_id = await self.random_genner_note_id(length=32)
        create_time = str(int(round(time.time() * 1000)))
        await asyncio.sleep(3)
        update_time = str(int(round(time.time() * 1000)))
        create_note_url = 'http://mnote.caiyun.feixin.10086.cn/noteServer/api/createNote.do'
        payload = {
            "archived": 0,
            "attachmentdir": note_id,
            "attachmentdirid": "",
            "attachments": [],
            "audioInfo": {
                "audioDuration": 0,
                "audioSize": 0,
                "audioStatus": 0
            },
            "contentid": "",
            "contents": [{
                "contentid": 0,
                "data": "<font size=\"3\">000000</font>",
                "noteId": note_id,
                "sortOrder": 0,
                "type": "RICHTEXT"
            }],
            "cp": "",
            "createtime": create_time,
            "description": "android",
            "expands": {
                "noteType": 0
            },
            "latlng": "",
            "location": "",
            "noteid": note_id,
            "notestatus": 0,
            "remindtime": "",
            "remindtype": 1,
            "revision": "1",
            "sharecount": "0",
            "sharestatus": "0",
            "system": "mobile",
            "tags": [{
                "id": self.notebook_id,
                "orderIndex": "0",
                "text": "默认笔记本"
            }],
            "title": "00000",
            "topmost": "0",
            "updatetime": update_time,
            "userphone": self.account,
            "version": "1.00",
            "visitTime": ""
        }
        create_note_response = await self.client.post(
            url=create_note_url,
            headers=headers,
            json=payload
        )
        if create_note_response.status_code == 200:
            fn_print(f"用户【{self.account}】，===创建笔记成功✅✅===")
        else:
            fn_print(f"创建笔记发生异常：{create_note_response.status_code}")

    async def upload_file(self):
        """
        上传文件
        :return: 
        """
        url = 'http://ose.caiyun.feixin.10086.cn/richlifeApp/devapp/IUploadAndDownload'
        headers = {
            'x-huawei-uploadSrc': '1', 'x-ClientOprType': '11', 'Connection': 'keep-alive', 'x-NetType': '6',
            'x-DeviceInfo': '6|127.0.0.1|1|10.0.1|Xiaomi|M2012K10C|CB63218727431865A48E691BFFDB49A1|02-00-00-00-00-00|android 11|1080X2272|zh||||032|',
            'x-huawei-channelSrc': '10000023', 'x-MM-Source': '032', 'x-SvcType': '1', 'APP_NUMBER': self.account,
            'Authorization': self.Authorization,
            'X-Tingyun-Id': 'p35OnrDoP8k;c=2;r=1955442920;u=43ee994e8c3a6057970124db00b2442c::8B3D3F05462B6E4C',
            'Host': 'ose.caiyun.feixin.10086.cn', 'User-Agent': 'okhttp/3.11.0',
            'Content-Type': 'application/xml; charset=UTF-8', 'Accept': '*/*'
        }
        payload = '''                                <pcUploadFileRequest>                                    <ownerMSISDN>{phone}</ownerMSISDN>                                    <fileCount>1</fileCount>                                    <totalSize>1</totalSize>                                    <uploadContentList length="1">                                        <uploadContentInfo>                                            <comlexFlag>0</comlexFlag>                                            <contentDesc><![CDATA[]]></contentDesc>                                            <contentName><![CDATA[000000.txt]]></contentName>                                            <contentSize>1</contentSize>                                            <contentTAGList></contentTAGList>                                            <digest>C4CA4238A0B923820DCC509A6F75849B</digest>                                            <exif/>                                            <fileEtag>0</fileEtag>                                            <fileVersion>0</fileVersion>                                            <updateContentID></updateContentID>                                        </uploadContentInfo>                                    </uploadContentList>                                    <newCatalogName></newCatalogName>                                    <parentCatalogID></parentCatalogID>                                    <operation>0</operation>                                    <path></path>                                    <manualRename>2</manualRename>                                    <autoCreatePath length="0"/>                                    <tagID></tagID>                                    <tagType></tagType>                                </pcUploadFileRequest>                            '''.format(
            phone=self.account)
        response = await self.client.post(
            url=url,
            headers=headers,
            content=payload
        )
        if response is None:
            return
        if response.status_code != 200:
            fn_print(f"上传文件发生异常：{response.status_code}")
        fn_print(f"用户【{self.account}】，===上传文件成功✅✅===")

    async def rm_sleep(self, min_delay=1, max_delay=1.5):
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)

    async def random_genner_note_id(self, length):
        characters = '19f3a063d67e4694ca63a4227ec9a94a19088404f9a28084e3e486b928039a299bf756ebc77aa4f6bfa250308ec6a8be8b63b5271a00350d136d117b8a72f39c5bd15cdfd350cba4271dc797f15412d9f269e666aea5039f5049d00739b320bb9e8585a008b52c1cbd86970cae9476446f3e41871de8d9f6112db94b05e5dc7ea0a942a9daf145ac8e487d3d5cba7cea145680efc64794d43dd15c5062b81e1cda7bf278b9bc4e1b8955846e6bc4b6a61c28f831f81b2270289e5a8a677c3141ddc9868129060c0c3b5ef507fbd46c004f6de346332ef7f05c0094215eae1217ee7c13c8dca6d174cfb49c716dd42903bb4b02d823b5f1ff93c3f88768251b56cc'
        note_id = ''.join(random.choice(characters) for _ in range(length))
        return note_id

    async def get_redeemable_reward_list(self):
        """
        获取可兑换奖励
        :return: 
        """
        url = "https://mrp.mcloud.139.com/market/signin/page/exchangeList?client=app&clientVersion=11.4.4"
        try:
            response = await self.client.get(
                url=url,
                headers=self.JwtHeaders,
                cookies=self.cookies
            )
            if response.status_code == 200:
                reward_data = response.json()
                # print(json.dumps(reward_data, indent=4, ensure_ascii=False))
                if reward_data.get("msg") == "success":
                    reward_type_datas: dict[dict[list[dict]]] = reward_data.get("result", {})
                    # print(json.dumps(reward_type_list, indent=4, ensure_ascii=False))
                    reward_type_list = list(reward_type_datas.keys())
                    # print(reward_type_list)
                    reward_list = []
                    for reward_type_key in reward_type_list:
                        for reward_data in reward_type_datas.get(reward_type_key):
                            # print(reward_data)
                            oid = reward_data.get("oid")
                            msg = f"{reward_data.get('prizeName')} - 兑换所需云朵: {reward_data.get('pOrder')} - 是否可兑换: {'是' if reward_data.get('dailyRemainderCount') != 0 else '否'}"
                            fn_print(msg)
                            reward_list.append({"oid": oid, "prizeName": reward_data.get("prizeName")})
                    return reward_list
            else:
                fn_print(f"获取可兑换奖励错误：{response.text}")
        except Exception as e:
            fn_print(f"获取可兑换奖励请求发生异常：{e}")

    async def redeem_reward(self, oid):
        """
        兑换奖励
        :param oid: 奖励的id
        :return:
        """
        url = f"https://mrp.mcloud.139.com/market/signin/page/exchange?prizeId={oid}&client=app&clientVersion=11.4.4&smsCode"
        try:
            response = await self.client.get(
                url=url,
                headers=self.JwtHeaders,
                cookies=self.cookies
            )
            if response.status_code == 200:
                reward_data = response.json()
                if reward_data.get("code") == 0:
                    fn_print(f"✅兑换奖励成功：{reward_data.get('msg')}")
                elif reward_data.get("code") == 2301:
                    fn_print(f"❌兑换奖励失败！{reward_data.get('msg')}")
                else:
                    fn_print(f"❌兑换奖励失败！{reward_data.get('msg')}")
            else:
                fn_print(f"❌兑换奖励请求错误：{response.text}")
        except Exception as e:
            fn_print(f"❌兑换奖励请求发生异常：{e}")

    async def run(self):
        if await self.jwt():
            fn_print("=========开始签到=========")
            await self.query_sign_in_status()
            fn_print("=========开始执行戳一戳=========")
            await self.a_poke()
            await self.get_task_list(url="sign_in_3", app_type="cloud_app")
            fn_print("=========开始执行☁️云朵大作战=========")
            await self.cloud_game()
            # fn_print("=========开始执行🌳果园任务=========")
            # await self.fruit_login()
            fn_print("=========开始执行📝公众号任务=========")
            await self.wx_app_sign()
            await self.shake()
            await self.surplus_num()
            fn_print("=========开始执行🔥热门任务=========")
            await self.backup_cloud()
            await self.open_send()
            fn_print("=========开始执行📮139邮箱任务=========")
            await self.get_task_list(url="newsign_139mail", app_type="email_app")
            await self.receive()
            reward_list = await self.get_redeemable_reward_list()
            if is_redeem and reward_list:
                fn_print("=========开始🎁兑换奖励=========")
                found = False
                for reward in reward_list:
                    if reward.get("prizeName") == redeem_reward_description:
                        oid = reward.get("oid")
                        if oid:
                            await self.redeem_reward(oid)
                            found = True
                            break
                if not found:
                    fn_print(f"❌未找到你想要兑换的奖品，请检查奖品名称是否正确")

        else:
            fn_print("token失效")


async def main():
    tasks = []
    for ck in ydyp_ck:
        mobileCloudDisk = MobileCloudDisk(ck)
        tasks.append(mobileCloudDisk.run())
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())
    send_notification_message_collection(f"中国移动云盘签到通知 - {datetime.now().strftime('%Y/%m/%d')}")
