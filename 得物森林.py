# -*- coding=UTF-8 -*-
# const $ = new Env('得物森林')
# cron "1 8,10,12,15,18,22 * * *"
"""
dw_x_auth_token：Bearer xxxxxxxxxxxx   (）
"""
import os
import asyncio
import random
import re
import time
import httpx
from urllib.parse import urlparse, parse_qs
from fn_print import fn_print
from get_env import get_env

os.environ["dw_x_auth_token"] = (
    "***REMOVED***"
)
os.environ["dw_sk"] = (
    "***REMOVED***"
)
dw_x_auth_tokens = get_env("dw_x_auth_token", "&")
dw_sks = get_env("dw_sk", "&")

share_code_list = []
HELP_SIGNAL = True


class DeWu:
    WATERTING_G: int = 40  # 每次浇水克数
    REMAINING_G: int = 1800  # 最后浇水剩余不超过的克数

    def __init__(self, x_auth_token, index, sk, waterting_g=WATERTING_G, remaining_g=REMAINING_G):
        self.client = httpx.AsyncClient(verify=False)
        self.index = index
        self.waterting_g = waterting_g
        self.remaining_g = remaining_g
        self.headers = {'appVersion': "5.55.0",
                        'User-Agent': "Mozilla/5.0 (Linux; Android 15; PJZ110 Build/AP3A.240617.008; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/129.0.6668.70 Mobile Safari/537.36/duapp/5.55.0(android;15)",
                        'x-auth-token': x_auth_token,
                        'uuid': '0000000000000000',
                        'SK': sk, }
        self.user_name = None
        self.tree_id = 0  # 树的id
        self.tasks_completed_number = 0  # 任务完成数
        self.cumulative_task_list = []  # 累计计任务列表
        self.tasks_dict_list = []  # 任务字典列表
        self.is_team_tree = False  # 是否是团队树

    @staticmethod
    def get_url_key_value(url, key):
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        _dict = {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}
        key_value = _dict.get(key)
        return key_value

    async def get_user_info(self):
        """
        获取用户信息
        :return: 
        """
        user_info_response = await self.client.get(url="https://app.dewu.com/hacking-tree/v1/team/info",
                                                   headers=self.headers)
        if user_info_response.status_code == 200:
            user_info_data = user_info_response.json()
            if user_info_data['code'] == 200:
                self.user_name = user_info_data.get("data").get("member")[0].get("name")
            else:
                fn_print(f"===获取用户信息失败❌, {user_info_data.get('msg')}===")
        else:
            fn_print(f"===获取用户信息请求异常❌, {user_info_response.status_code}===")

    async def tree_info(self):
        url = "https://app.dewu.com/hacking-tree/v1/user/target/info"
        tree_info_response = await self.client.get(url=url, headers=self.headers)
        if tree_info_response.status_code == 200:
            tree_info_data = tree_info_response.json()
            if tree_info_data['code'] == 200:
                name = tree_info_data.get("data").get("name")
                level = tree_info_data.get("data").get("level")
                fn_print(f"用户【{self.user_name}】，===目标奖品🥇：{name}, 当前小树等级：{level}===")
                return name, level
            fn_print(f"用户【{self.user_name}】，===获取许愿树信息失败❌, {tree_info_data.get('msg')}===")
        else:
            fn_print(f"用户【{self.user_name}】，===获取许愿树信息请求异常❌, {tree_info_response.status_code}===")

    async def determine_whether_is_team_tree(self):
        """
        获取是否是团队树
        :return: 
        """
        team_tree_response = await self.client.get(
            url="https://app.dewu.com/hacking-tree/v1/team/info",
            headers=self.headers
        )
        if team_tree_response.status_code == 200:
            team_tree_data = team_tree_response.json()
            if team_tree_data.get("data").get("show") and team_tree_data.get("data").get("teamTreeId"):
                self.is_team_tree = True
        else:
            fn_print(f"用户【{self.user_name}】，===获取是否团队树请求异常❌, {team_tree_response.status_code}===")

    async def sign_in(self):
        """
        签到
        :return: 
        """
        sign_in_response = await self.client.post(
            url="https://app.dewu.com/hacking-game-center/v1/sign/sign",
            headers=self.headers
        )
        if sign_in_response.status_code == 200:
            sign_in_data = sign_in_response.json()
            if sign_in_data.get("code") == 200:
                fn_print(f"用户【{self.user_name}】，===签到成功✅✅===")
            else:
                fn_print(f"用户【{self.user_name}】，===签到失败❌, {sign_in_data.get('msg')}===")
        else:
            fn_print(f"用户【{self.user_name}】，===签到发生异常❌, {sign_in_response.status_code}===")

    async def droplet_sign_in(self):
        """
        水滴签到
        :return: 
        """
        droplet_sign_in_response = await self.client.post(
            url="https://app.dewu.com/hacking-tree/v1/sign/sign_in",
            headers=self.headers
        )
        if droplet_sign_in_response.status_code == 200:
            droplet_sign_in_data = droplet_sign_in_response.json()
            if droplet_sign_in_data.get("code") == 200:
                fn_print(
                    f"用户【{self.user_name}】，===水滴签到成功✅✅, 获得{droplet_sign_in_data.get('data').get('Num')}g水滴💧💧💧===")
            else:
                fn_print(f"用户【{self.user_name}】，===水滴签到失败❌, {droplet_sign_in_data.get('msg')}===")
        else:
            fn_print(f"用户【{self.user_name}】，===水滴签到发生异常❌, {droplet_sign_in_response.status_code}===")

    async def receive_droplet_extra(self):
        """
        领取气泡水滴
        :return: 
        """
        flag = -1
        countdown_time = 0
        recevie_signal = False
        for _ in range(50):
            droplet_extra_response = await self.client.get(
                url="https://app.dewu.com/hacking-tree/v1/droplet-extra/info",
                headers=self.headers
            )
            if droplet_extra_response.status_code == 200:
                droplet_extra_data = droplet_extra_response.json()
                if droplet_extra_data.get("code") != 200:
                    fn_print(f"用户【{self.user_name}】，===获取气泡水滴信息失败❌, {droplet_extra_data}===")
                    return
                data = droplet_extra_data.get("data")
                receivable = data.get("receivable")
                if receivable:
                    if data.get("dailyExtra"):
                        water_droplet_num = data.get("dailyExtra").get("totalDroplet")
                    else:
                        water_droplet_num = data.get("onlineExtra").get("totalDroplet")
                    if flag == water_droplet_num or recevie_signal:
                        fn_print(f"用户【{self.user_name}】，===当前可领取气泡水滴{water_droplet_num}g水滴💧===")
                        receive_droplet_extra_response = await self.client.post(
                            url="https://app.dewu.com/hacking-tree/v1/droplet-extra/receive",
                            headers=self.headers
                        )
                        if receive_droplet_extra_response.status_code == 200:
                            receive_droplet_extra_data = receive_droplet_extra_response.json()
                            if receive_droplet_extra_data.get("code") != 200:
                                countdown_time += 60
                                if countdown_time > 60:
                                    fn_print(
                                        f"用户【{self.user_name}】，===领取气泡水滴失败❌, {receive_droplet_extra_data}===")
                                    return
                                fn_print(f"用户【{self.user_name}】，===等待{countdown_time}秒后领取===")
                                await asyncio.sleep(countdown_time)
                                continue
                            fn_print(
                                f"用户【{self.user_name}】，===领取气泡水滴成功✅✅, 获得{receive_droplet_extra_data.get('data').get('totalDroplet')}g水滴💧===")
                            countdown_time = 0  # 重置时间
                            continue
                        else:
                            fn_print(
                                f"用户【{self.user_name}】，===领取气泡水滴发生异常❌, {receive_droplet_extra_response.status_code}===")
                        flag = water_droplet_num
                        recevie_signal = True
                    flag = water_droplet_num
                    fn_print(f"用户【{self.user_name}】，===当前气泡水滴{water_droplet_num}g, 未满，开始浇水===")
                    if not await self.waterting():
                        recevie_signal = True
                    await asyncio.sleep(0.5)
                    continue
                water_droplet_num = droplet_extra_data.get("data").get("dailyExtra").get("totalDroplet")
                fn_print(
                    f"用户【{self.user_name}】，==={droplet_extra_data.get('data').get('dailyExtra').get('popTitle')}, "
                    f"已经积攒{water_droplet_num}g水滴！===")
            else:
                fn_print(
                    f"用户【{self.user_name}】，===获取气泡水滴信息发生异常❌, {droplet_extra_response.status_code}===")

    async def waterting_droplet_extra(self):
        """
        浇水充满气泡水滴
        :return: 
        """
        while True:
            water_response = await self.client.get(
                url="https://app.dewu.com/hacking-tree/v1/droplet-extra/info",
                headers=self.headers
            )
            if water_response.status_code == 200:
                water_data = water_response.json()
                count = water_data.get("data").get("dailyExtra", {}).get("times", 0)
                if not count:
                    fn_print(
                        f"用户【{self.user_name}】，===气泡水滴已充满，明日可领取{water_data.get('data').get('dailyExtra').get('totalDroplet')}g===")
                    return
                for _ in range(count):
                    if not await self.waterting():
                        return
                    await asyncio.sleep(0.5)
            else:
                fn_print(f"用户【{self.user_name}】，===获取气泡水滴信息发生异常❌, {water_response.status_code}===")

    async def receive_bucket_droplet(self):
        """
        领取木桶水滴,200秒满一次,每天领取3次
        :return: 
        """
        receive_bucket_droplet_response = await self.client.post(
            url="https://app.dewu.com/hacking-tree/v1/droplet/get_generate_droplet",
            headers=self.headers
        )
        if receive_bucket_droplet_response.status_code == 200:
            receive_bucket_droplet_data = receive_bucket_droplet_response.json()
            if receive_bucket_droplet_data.get("code") != 200:
                fn_print(
                    f"用户【{self.user_name}】，===领取木桶水滴失败❌, {receive_bucket_droplet_data}===")
                return
            fn_print(
                f"用户【{self.user_name}】，===领取木桶水滴成功✅✅, 获得{receive_bucket_droplet_data.get('data').get('droplet')}g水滴💧===")
        else:
            fn_print(
                f"用户【{self.user_name}】，===领取木桶水滴发生异常❌, {receive_bucket_droplet_response.status_code}===")

    async def judging_bucket_droplet(self):
        """
        判断木桶水滴是否可以领取
        :return: 
        """
        judging_bucket_droplet_response = await self.client.get(
            url="https://app.dewu.com/hacking-tree/v1/droplet/generate_info",
            headers=self.headers
        )
        if judging_bucket_droplet_response.status_code == 200:
            judging_bucket_droplet_data = judging_bucket_droplet_response.json()
            if judging_bucket_droplet_data.get("data").get("currentDroplet") == 100:
                fn_print(
                    f"用户【{self.user_name}】，===今天已领取木桶水滴{judging_bucket_droplet_data.get('data').get('getTimes')}次===")
                await self.receive_bucket_droplet()
                return True
            return False
        else:
            fn_print(
                f"用户【{self.user_name}】，===判断木桶水滴发生异常❌, {judging_bucket_droplet_response.status_code}===")

    async def get_shared_code(self):
        """
        获取助力码
        :return: 
        """
        get_shared_code_response = await self.client.post(
            url="https://app.dewu.com/hacking-tree/v1/keyword/gen",
            headers=self.headers
        )
        if get_shared_code_response.status_code == 200:
            get_shared_code_data = get_shared_code_response.json()
            if get_shared_code_data.get("code") != 200:
                fn_print(
                    f"用户【{self.user_name}】，===获取助力码失败❌, {get_shared_code_data}===")
                return
            share_code = get_shared_code_data.get("data").get("keywordDesc").replace("\n", "")
            fn_print(f"用户【{self.user_name}】，===获取助力码 {share_code} 成功✅✅===")
        else:
            fn_print(
                f"用户【{self.user_name}】，===获取助力码发生异常❌, {get_shared_code_response.status_code}===")

    async def get_droplet_number(self):
        """
        获取水滴数
        :return: 
        """
        headers = self.headers
        headers.update(
            {
                'channel': 'opp',
                'uuid': '0000000000000000',
                'isProxy': "0",
                'emu': "0",
                'isRoot': "0",
                'deviceTrait': "PJZ110",
                'ua': "duapp/5.55.0(android;15)",
                'Origin': "https://cdn-m.dewu.com",
                'X-Requested-With': "com.shizhuang.duapp",
                'Sec-Fetch-Site': "same-site",
                'Sec-Fetch-Mode': "cors",
                'Sec-Fetch-Dest': "empty",
                'Referer': "https://cdn-m.dewu.com/",
                'Accept-Language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            }
        )
        get_droplet_number_response = await self.client.post(
            url="https://app.dewu.com/hacking-tree/v1/user/init",
            headers=headers,
            json={"keyword": ""}
        )
        if get_droplet_number_response.status_code == 200:
            get_droplet_number_data = get_droplet_number_response.json()
            data = get_droplet_number_data.get("data")
            if data:
                droplet_number = data.get("droplet")
                return droplet_number
            else:
                fn_print(f"用户【{self.user_name}】，===获取水滴数失败❌, {get_droplet_number_data}===")
        else:
            fn_print(f"用户【{self.user_name}】，===获取水滴数发生异常❌, {get_droplet_number_response.status_code}===")

    async def receive_cumulative_tasks_reward(self, condition):
        """
        领取累计任务奖励
        :return: 
        """
        recevie_cumulative_tasks_reward_response = await self.client.post(
            url="https://app.dewu.com/hacking-tree/v1/task/extra",
            headers=self.headers,
            json={"condition": condition}
        )
        if recevie_cumulative_tasks_reward_response.status_code == 200:
            recevie_cumulative_tasks_reward_data = recevie_cumulative_tasks_reward_response.json()
            if recevie_cumulative_tasks_reward_data.get("code") != 200:
                fn_print(
                    f"用户【{self.user_name}】，===领取累计任务奖励失败❌, {recevie_cumulative_tasks_reward_data}===")
                return
            fn_print(
                f"用户【{self.user_name}】，===领取累计任务奖励成功✅✅, 获得{recevie_cumulative_tasks_reward_data.get('data').get('num')}g水滴💧===")
        else:
            fn_print(
                f"用户【{self.user_name}】，===领取累计任务奖励发生异常❌, {recevie_cumulative_tasks_reward_response.status_code}===")

    async def receive_task_reward(self, classify, task_id, task_type):
        """
        领取任务奖励
        :param classify: 
        :param task_id: 
        :param task_type: 
        :return: 
        """
        await asyncio.sleep(0.2)
        url = "https://app.dewu.com/hacking-tree/v1/task/receive"
        if task_type in [251]:
            json = {'classify': classify, 'taskId': task_id, 'completeFlag': 1}
        else:
            json = {'classify': classify, 'taskId': task_id}
        recevie_task_reward_response = await self.client.post(
            url=url,
            headers=self.headers,
            json=json
        )
        if recevie_task_reward_response.status_code == 200:
            recevie_task_reward_data = recevie_task_reward_response.json()
            if recevie_task_reward_data.get("code") != 200:
                fn_print(
                    f"用户【{self.user_name}】，===领取任务奖励失败❌, {recevie_task_reward_data}===")
                return
            fn_print(
                f"用户【{self.user_name}】，===领取任务奖励成功✅✅, 获得{recevie_task_reward_data.get('data').get('num')}g水滴💧===")
        else:
            fn_print(
                f"用户【{self.user_name}】，===领取任务奖励发生异常❌, {recevie_task_reward_response.status_code}===")

    async def receive_watering_reward(self):
        """
        领取浇水奖励
        :return: 
        """
        recevie_watering_reward_response = await self.client.post(
            url="https://app.dewu.com/hacking-tree/v1/tree/get_watering_reward",
            headers=self.headers,
            json={"promote": ""}
        )
        if recevie_watering_reward_response.status_code == 200:
            recevie_watering_reward_data = recevie_watering_reward_response.json()
            if recevie_watering_reward_data.get("code") != 200:
                fn_print(
                    f"用户【{self.user_name}】，===领取浇水奖励失败❌, {recevie_watering_reward_data}===")
                return
            fn_print(
                f"用户【{self.user_name}】，===领取浇水奖励成功✅✅, 获得{recevie_watering_reward_data.get('data').get('currentWateringReward').get('rewardNum')}g水滴💧===")
        else:
            fn_print(
                f"用户【{self.user_name}】，===领取浇水奖励发生异常❌, {recevie_watering_reward_response.status_code}===")

    async def receive_level_reward(self):
        """
        领取等级奖励
        :return: 
        """
        for _ in range(20):
            recevie_level_reward_response = await self.client.post(
                url="https://app.dewu.com/hacking-tree/v1/tree/get_level_reward",
                headers=self.headers,
                json={"promote": ""}
            )
            if recevie_level_reward_response.status_code == 200:
                recevie_level_reward_data = recevie_level_reward_response.json()
                if recevie_level_reward_data.get("code") != 200 or recevie_level_reward_data.get("data") is None:
                    fn_print(
                        f"用户【{self.user_name}】，===领取等级奖励失败❌, {recevie_level_reward_data.get('msg')}===")
                    return
                level = recevie_level_reward_data.get("data").get("levelReward").get("showLevel") - 1
                reward_num = recevie_level_reward_data.get("data").get("currentLevelReward").get("rewardNum")
                fn_print(
                    f"用户【{self.user_name}】，===领取{level}级奖励成功✅✅, 获得{reward_num}g水滴💧===")
                if not recevie_level_reward_data.get("data").get("levelReward").get("isComplete"):
                    return
                await asyncio.sleep(1)
            else:
                fn_print(
                    f"用户【{self.user_name}】，===领取等级奖励发生异常❌, {recevie_level_reward_response.status_code}===")

    async def execute_receive_watering_reward(self):
        """
        多次执行浇水，领取浇水奖励
        :return: 
        """
        for _ in range(20):
            execute_receive_watering_reward_response = await self.client.get(
                url="https://app.dewu.com/hacking-tree/v1/tree/get_tree_info",
                headers=self.headers
            )
            if execute_receive_watering_reward_response.status_code == 200:
                execute_receive_watering_reward_data = execute_receive_watering_reward_response.json()
                if execute_receive_watering_reward_data.get("code") != 200:
                    fn_print(f"用户【{self.user_name}】，===获取种树进度失败❌, {execute_receive_watering_reward_data}===")
                    return
                count = execute_receive_watering_reward_data.get("data").get("nextWateringTimes")
                if execute_receive_watering_reward_data.get("data").get("wateringReward") is None or count <= 0:
                    return
                for _ in range(count):
                    if not await self.waterting():
                        return
                    await asyncio.sleep(0.5)
            else:
                fn_print(
                    f"用户【{self.user_name}】，===获取种树进度发生异常❌, {execute_receive_watering_reward_response.status_code}===")

    async def waterting_until_less_than(self):
        """
        浇水直到小于指定克数
        :return: 
        """
        droplet_number = await self.get_droplet_number()
        if droplet_number > self.waterting_g:
            count = int((droplet_number - self.remaining_g) / self.waterting_g)
            for _ in range(count + 1):
                if not await self.waterting():
                    return
                await asyncio.sleep(0.5)

    async def submit_task_completion_status(self, json):
        submit_task_completion_status_response = await self.client.post(
            url="https://app.dewu.com/hacking-task/v1/task/commit",
            headers=self.headers,
            json=json
        )
        if submit_task_completion_status_response.status_code == 200:
            submit_task_completion_status_data = submit_task_completion_status_response.json()
            if submit_task_completion_status_data.get("code") == 200:
                return True
            return False
        else:
            fn_print(
                f"用户【{self.user_name}】，===提交任务完成状态发生异常❌, {submit_task_completion_status_response.status_code}===")
            return False

    async def get_task_list(self):
        """
        获取任务列表
        :return: 
        """
        get_task_list_response = await self.client.get(
            url="https://app.dewu.com/hacking-tree/v1/task/list",
            headers=self.headers
        )
        if get_task_list_response.status_code == 200:
            get_task_list_data = get_task_list_response.json()
            if get_task_list_data.get("code") == 200:
                self.tasks_completed_number = get_task_list_data.get("data").get("userStep")  # 已完成任务数量
                self.cumulative_task_list = get_task_list_data.get('data').get('extraAwardList')  # 累计任务列表            
                self.tasks_dict_list = get_task_list_data.get('data').get('taskList')  # 任务列表
                return True
        else:
            fn_print(f"用户【{self.user_name}】，===获取任务列表发生异常❌, {get_task_list_response.status_code}===")
            return False

    async def task_obtain(self, task_id, task_type):
        """
        水滴大放送任务
        :param task_id: 
        :param task_type: 
        :return: 
        """
        task_obtain_response = await self.client.post(
            url="https://app.dewu.com/hacking-task/v1/task/obtain",
            headers=self.headers,
            json={"taskId": task_id, "taskType": task_type}
        )
        if task_obtain_response.status_code == 200:
            task_obtain_data = task_obtain_response.json()
            if task_obtain_data.get("code") == 200 and task_obtain_data.get("status") == 200:
                return True
            return False
        else:
            fn_print(f"用户【{self.user_name}】，===水滴大放送任务步骤发生异常❌, {task_obtain_response.status_code}===")

    async def task_commit_pre(self, json):
        """
        浏览任务
        :param json: 
        :return: 
        """
        task_commit_pre_response = await self.client.post(
            url="https://app.dewu.com/hacking-task/v1/task/pre_commit",
            headers=self.headers,
            json=json
        )
        if task_commit_pre_response.status_code == 200:
            task_commit_pre_data = task_commit_pre_response.json()
            if task_commit_pre_data.get("code") == 200 and task_commit_pre_data.get("status") == 200:
                return True
            return False
        else:
            fn_print(f"用户【{self.user_name}】，===浏览任务发生异常❌, {task_commit_pre_response.status_code}===")

    async def execute_task(self):
        """
        执行任务
        :return: 
        """
        await self.get_task_list()
        for task_dict in self.tasks_dict_list:
            if task_dict.get("isReceiveReward"):
                continue
            if task_dict.get("rewardCount") >= 3000:
                continue
            classify = task_dict.get('classify')
            task_id = task_dict.get('taskId')
            task_type = task_dict.get('taskType')
            task_name = task_dict.get('taskName')
            btd = self.get_url_key_value(task_dict.get('jumpUrl'), 'btd')
            btd = int(btd) if btd else btd
            spu_id = self.get_url_key_value(task_dict.get('jumpUrl'), 'spuId')
            spu_id = int(spu_id) if spu_id else spu_id
            if task_dict.get("isComplete"):
                if task_name == "领40g水滴值" and not task_dict.get("receivable"):
                    continue
                fn_print(f"用户【{self.user_name}】，===开始执行任务【{task_name}】===")
                await self.receive_task_reward(classify, task_id, task_type)
                continue
            fn_print(f"用户【{self.user_name}】，===开始执行任务【{task_name}】===")
            if task_name == "完成一次签到":
                await self.sign_in()
                json = {
                    "taskId": task_dict.get("taskId"),
                    "taskType": str(task_dict.get("taskType")),
                }
                if await self.submit_task_completion_status(json):
                    await self.receive_task_reward(classify, task_id, task_type)
                    continue
            if task_name == "领40g水滴值":
                await self.receive_task_reward(classify, task_id, task_type)
                continue
            if task_name == "收集一次水滴生产":
                if await self.judging_bucket_droplet():
                    await self.receive_task_reward(classify, task_id, task_type)
                else:
                    fn_print(f"用户【{self.user_name}】，===当前木桶水滴未达到100g，下次来完成任务吧！===")
                continue
            if task_name == "浏览【我】的右上角星愿森林入口":
                report_action_response = await self.client.post(
                    url="https://app.dewu.com/hacking-tree/v1/user/report_action",
                    headers=self.headers,
                    json={"action": task_id}
                )
                if report_action_response.status_code == 200:
                    report_action_data = report_action_response.json()
                    if report_action_data.get("code"):
                        await self.receive_task_reward(classify, task_id, task_type)
                    continue
                if any(re.match(pattern, task_name) for pattern in
                       ["参与1次上上签活动", "从桌面组件访问许愿树", "参与1次拆盲盒", "去.*"]):
                    await self.submit_task_completion_status(
                        {
                            "taskId": task_id,
                            "taskType": str(task_type)
                        }
                    )
                    await self.receive_task_reward(classify, task_id, task_type)
                    continue

                if any(re.match(pattern, task_name) for pattern in [".*订阅.*", ".*逛一逛.*", "逛逛.*活动"]):
                    await self.submit_task_completion_status(
                        {
                            "taskId": task_id,
                            "taskType": str(task_type),
                            "btd": btd
                        }
                    )
                    await self.receive_task_reward(classify, task_id, task_type)
                    continue
                if any(re.match(pattern, task_name) for pattern in [".*逛逛.*", "浏览.*s"]):
                    if await self.task_commit_pre(
                            {
                                "taskId": task_id,
                                "taskType": str(task_type),
                                "btd": btd
                            }
                    ):
                        await asyncio.sleep(16)
                        await self.submit_task_completion_status(
                            {
                                "taskId": task_id,
                                "taskType": str(task_type),
                                "activityType": None,
                                "activityId": None,
                                "taskSetId": None,
                                "venueCode": None,
                                "venueUnitStyle": None,
                                "taskScene": None,
                                "btd": btd
                            }
                        )
                        await self.receive_task_reward(classify, task_id, task_type)
                        continue
                if any(re.match(pattern, task_name) for pattern in [".*晒图.*"]):
                    if await self.task_commit_pre(
                            {
                                "taskId": task_id,
                                "taskType": str(task_type)
                            }
                    ):
                        await asyncio.sleep(16)
                        await self.submit_task_completion_status(
                            {
                                "taskId": task_id,
                                "taskType": str(task_type),
                                "activityType": None,
                                "activityId": None,
                                "taskSetId": None,
                                "venueCode": None,
                                "venueUnitStyle": None,
                                "taskScene": None
                            }
                        )
                        await self.receive_task_reward(classify, task_id, task_type)
                        continue
                if task_name == "完成五次浇灌":
                    count = task_dict.get("total") - task_dict.get("curStep")
                    if await self.get_droplet_number() < (self.waterting_g * count):
                        fn_print(f"用户【{self.user_name}】，===当前水滴不足以完成任务，下次来完成任务吧！===")
                        continue
                    for _ in range(count):
                        await asyncio.sleep(0.5)
                        if not await self.waterting():
                            break
                    else:
                        if await self.submit_task_completion_status(
                                {
                                    "taskId": task_dict.get("taskId"),
                                    "taskType": str(task_dict.get("taskType"))
                                }
                        ):
                            await self.receive_task_reward(classify, task_id, task_type)
                            continue
                if any(re.match(pattern, task_name) for pattern in [".*专场", ".*水滴大放送"]):
                    if await self.task_obtain(task_id, task_type):
                        if await self.task_commit_pre(
                                {
                                    "taskId": task_id,
                                    "taskType": 16
                                }
                        ):
                            await asyncio.sleep(16)
                            await self.submit_task_completion_status(
                                {
                                    "taskId": task_id,
                                    "taskType": str(task_type)
                                }
                            )
                            await self.receive_task_reward(classify, task_id, task_type)
                            continue
                fn_print(f"该任务暂时无法处理，请提交日志给作者！{task_dict}")

    async def execute_cumulative_task(self):
        """
        执行累计任务
        :return: 
        """
        await self.get_task_list()
        for task in self.cumulative_task_list:
            if task.get("status") == 1:
                fn_print(f"用户【{self.user_name}】，===开始领取累计任务数达{task.get('condition')}个的奖励===")
                await self.receive_cumulative_tasks_reward(task.get("condition"))
                await asyncio.sleep(1)

    async def droplet_invest(self):
        """
        水滴投资
        :return: 
        """
        droplet_invest_response = await self.client.get(
            url="https://app.dewu.com/hacking-tree/v1/invest/info",
            headers=self.headers
        )
        if droplet_invest_response.status_code == 200:
            droplet_invest_data = droplet_invest_response.json()
            if not droplet_invest_data.get("data").get("isToday"):
                await self.receive_droplet_invest()
            else:
                fn_print(f"用户【{self.user_name}】，===今日已领取过水滴投资奖励了===")
            await asyncio.sleep(2)
            droplet_invest_response = await self.client.get(
                url="https://app.dewu.com/hacking-tree/v1/invest/info",
                headers=self.headers
            )
            droplet_invest_data = droplet_invest_response.json()
            if droplet_invest_data.get("data").get("triggered"):
                invest_commit_response = await self.client.post(
                    url="https://app.dewu.com/hacking-tree/v1/invest/commit",
                    headers=self.headers
                )
                invest_commit_data = invest_commit_response.json()
                if invest_commit_data.get("code") == 200 and invest_commit_data.get("status") == 200:
                    fn_print(f"用户【{self.user_name}】，===水滴投资成功✅✅, 水滴-100g===")
                    return
                if invest_commit_data.get("msg") == "水滴不够了":
                    fn_print(f"用户【{self.user_name}】，===水滴投资失败❌, 水滴不够了。{invest_commit_data.get('msg')}===")
                    return
                fn_print(f"用户【{self.user_name}】，===水滴投资有问题❌, {invest_commit_data}===")
                return
            else:
                fn_print(f"用户【{self.user_name}】，===今日已水滴投资过了===")
        else:
            fn_print(f"用户【{self.user_name}】，===水滴投资发生异常❌, {droplet_invest_response.status_code}===")

    async def receive_droplet_invest(self):
        """
        领取水滴投资奖励
        :return: 
        """
        receive_droplet_invest_response = await self.client.post(
            url="https://app.dewu.com/hacking-tree/v1/invest/receive",
            headers=self.headers
        )
        if receive_droplet_invest_response.status_code == 200:
            receive_droplet_invest_data = receive_droplet_invest_response.json()
            profit = receive_droplet_invest_data.get("data").get("profit")
            fn_print(f"用户【{self.user_name}】，===领取水滴投资奖励成功✅✅，收益-{profit}g水滴💧===")
        else:
            fn_print(
                f"用户【{self.user_name}】，===领取水滴投资奖励请求发生异常❌, {receive_droplet_invest_response.status_code}===")

    async def get_share_code(self):
        """
        获取助力码
        :return: 
        """
        get_share_code_response = await self.client.get(
            url="https://app.dewu.com/hacking-tree/v1/keyword/gen",
            headers=self.headers
        )
        if get_share_code_response.status_code == 200:
            get_share_code_data = get_share_code_response.json()
            if get_share_code_data.get("status") == 200:
                keyword = get_share_code_data.get("data").get("keyword")
                keyword = re.findall("œ(.*?)œ ", keyword)
                if keyword:
                    fn_print(f"用户【{self.user_name}】，===获取助力码成功✅✅, {keyword[0]}===")
                    return keyword[0]
            else:
                fn_print(f"用户【{self.user_name}】，===获取助力码失败❌, {get_share_code_data}===")
        else:
            fn_print(f"用户【{self.user_name}】，===获取助力码发生异常❌, {get_share_code_response.status_code}===")

    async def help_user(self):
        """
        助力
        :return: 
        """
        if not HELP_SIGNAL:  # 未开启助力
            return
        url = "https://app.dewu.com/hacking-tree/v1/user/init"
        if self.index == 0:
            for share_code in share_code_list:
                help_user_response = await self.client.post(
                    url=url,
                    headers=self.headers,
                    json={"keyword": share_code}
                )
                if help_user_response.status_code == 200:
                    help_user_data = help_user_response.json()
                    data = help_user_data.get("data")
                    if not data:
                        continue
                    invite_res = data.get("inviteRes")
                    if any(re.match(pattern, invite_res) for pattern in ["助力成功", "助力失败", "今日已助力过了"]):
                        fn_print(f"用户【{self.user_name}】，===开始助力{share_code}===", end=" ")
                        fn_print(invite_res)
                        return
                    await asyncio.sleep(random.randint(20, 30) / 10)
                else:
                    fn_print(f"用户【{self.user_name}】，===助力发生异常❌, {help_user_response.status_code}===")
        for share_code in share_code_list:
            fn_print(f"用户【{self.user_name}】，===开始助力{share_code}===", end=" ")
            help_user_response = await self.client.post(
                url=url,
                headers=self.headers,
                json={"keyword": share_code}
            )
            if help_user_response.status_code == 200:
                help_user_data = help_user_response.json()
                data = help_user_data.get("data")
                if not data:
                    fn_print(f"用户【{self.user_name}】，===助力失败❌, {help_user_data}===")
                invite_res = data.get("inviteRes")
                fn_print(invite_res)
                if any(re.match(pattern, invite_res) for pattern in ["助力成功", "助力失败", "今日已助力过了"]):
                    return
                await asyncio.sleep(random.randint(20, 30) / 10)
            else:
                fn_print(f"用户【{self.user_name}】，===助力发生异常❌, {help_user_response.status_code}===")
        return

    async def receive_help_reward(self):
        """
        领取助力奖励
        :return: 
        """
        receive_help_reward_list_response = await self.client.get(
            url="https://app.dewu.com/hacking-tree/v1/invite/list",
            headers=self.headers
        )
        if receive_help_reward_list_response.status_code == 200:
            receive_help_reward_list_data = receive_help_reward_list_response.json()
            if receive_help_reward_list_data.get("status") == 200:
                reward_list = receive_help_reward_list_data.get("data").get("list")
                if not reward_list:
                    return
                for reward in reward_list:
                    if reward.get("status") != 0:
                        continue
                    invitee_user_id = reward.get("inviteeUserId")
                    receive_help_reward_response = await self.client.post(
                        url="https://app.dewu.com/hacking-tree/v1/invite/reward",
                        headers=self.headers,
                        json={
                            "inviteeUserId": invitee_user_id
                        }
                    )
                    receive_help_reward_data = receive_help_reward_response.json()
                    if receive_help_reward_data.get("status") == 200:
                        droplet = receive_help_reward_data.get("data").get("droplet")
                        fn_print(f"用户【{self.user_name}】，===领取助力奖励成功✅✅，获得{droplet}g水滴💧===")
                        continue
                    fn_print(f"用户【{self.user_name}】，===领取助力奖励失败❌, {receive_help_reward_data}===")
                return
            fn_print(f"用户【{self.user_name}】，===领取助力奖励失败❌, {receive_help_reward_list_data}===")
        else:
            fn_print(
                f"用户【{self.user_name}】，===领取助力奖励发生异常❌, {receive_help_reward_list_response.status_code}===")

    async def receive_hybrid_online_reward(self):
        """
        领取合种上线奖励
        :return: 
        """
        team_reward_list_response = await self.client.get(
            url=f"https://app.dewu.com/hacking-tree/v1/team/sign/list?teamTreeId={self.tree_id}",
            headers=self.headers
        )
        if team_reward_list_response.status_code == 200:
            team_reward_list_data = team_reward_list_response.json()
            if team_reward_list_data.get("data") is None:
                return
            reward_list = team_reward_list_data.get("data", {}).get("list")
            if not reward_list:
                return
            for rewaed in reward_list:
                if rewaed.get("isComplete") and not rewaed.get("isReceive"):
                    receive_hybrid_online_reward_response = await self.client.post(
                        url="https://app.dewu.com/hacking-tree/v1/team/sign/receive",
                        headers=self.headers,
                        json={
                            "teamTreeId": self.tree_id,
                            "day": rewaed.get("day")
                        }
                    )
                    receive_hybrid_online_reward_data = receive_hybrid_online_reward_response.json()
                    if receive_hybrid_online_reward_data.get("data").get("isOk"):
                        fn_print(f"用户【{self.user_name}】，===领取合种上线奖励成功✅✅, 获得{rewaed.get('num')}g水滴💧===")
                        continue
                    fn_print(f"用户【{self.user_name}】，===领取合种上线奖励失败❌, {receive_hybrid_online_reward_data}===")
        return

    async def receive_air_drop(self):
        """
        领取空中水滴
        :return: 
        """
        for _ in range(2):
            receive_air_drop_response = await self.client.post(
                url="https://app.dewu.com/hacking-tree/v1/droplet/air_drop_receive",
                headers=self.headers,
                json={
                    "clickCount": 20,
                    "time": int(time.time())
                }
            )
            if receive_air_drop_response.status_code == 200:
                receive_air_drop_data = receive_air_drop_response.json()
                data = receive_air_drop_data.get("data")
                if data is not None and data.get("isOk"):
                    fn_print(f"用户【{self.user_name}】，===领取空中水滴成功✅✅，获得{data.get('droplet')}g水滴💧===")
                    await asyncio.sleep(1)
                    continue
                break

    async def click_product(self):
        products = [
            {"spuId": 3030863, "timestamp": 1690790735382, "sign": "2889b16b3077c5719288d105a14ffa1e"},
            {"spuId": 4673547, "timestamp": 1690790691956, "sign": "cc3cc95253d29a03fc6e79bfe2200143"},
            {"spuId": 1502607, "timestamp": 1690791565022, "sign": "04951eac012785ccb2600703a92c037b"},
            {"spuId": 2960612, "timestamp": 1690791593097, "sign": "fb667d45bc3950a7beb6e3fa0fc05089"},
            {"spuId": 3143593, "timestamp": 1690791613243, "sign": "82b9fda61be79f7b8833087508d6abe2"},
            {"spuId": 3067054, "timestamp": 1690791639606, "sign": "2808f3c7cf2ededea17d3f70a2dc565d"},
            {"spuId": 4448037, "timestamp": 1690791663078, "sign": "335bc519ee9183c086beb009adf93738"},
            {"spuId": 3237561, "timestamp": 1690791692553, "sign": "5c113b9203a510b7068b3cd0f6b7c25e"},
            {"spuId": 3938180, "timestamp": 1690792014889, "sign": "3841c0272443dcbbab0bcb21c94c6262"}
        ]
        for product in products:
            product_response = await self.client.post(
                url="https://app.dewu.com/hacking-tree/v1/product/spu",
                headers=self.headers,
                json=product
            )
            if product_response.status_code == 200:
                product_data = product_response.json()
                if product_data.get("data") is None:
                    fn_print(f"用户【{self.user_name}】，===今天已经完成过这个任务了❌, {product_data}===")
                    return
                if product_data.get("data").get("isReceived"):
                    fn_print(f"用户【{self.user_name}】，===获得{product_data.get('data').get('dropLetReward')}g水滴💧")
                    return
                await asyncio.sleep(1)
            else:
                fn_print(f"用户【{self.user_name}】，===点击商品任务请求异常❌, {product_response.status_code}===")

    async def receive_discover_droplet(self):
        """
        领取发现水滴
        :return: 
        """
        while True:
            receive_discover_droplet_response = await self.client.post(
                url="https://app.dewu.com/hacking-tree/v1/product/task/seek-receive",
                headers=self.headers,
                json={
                    "sign": "9888433e6d10b514e5b5be4305d123f0",
                    "timestamp": int(time.time() * 1000)
                }
            )
            if receive_discover_droplet_response.status_code == 200:
                receive_discover_droplet_data = receive_discover_droplet_response.json()
                fn_print(receive_discover_droplet_data)

    async def receive_brand_specials(self):
        """
        领取品牌特惠奖励
        :return: 
        """
        receive_brand_specials_response = await self.client.get(
            url="https://app.dewu.com/hacking-ad/v1/activity/list?bizId=tree",
            headers=self.headers
        )
        if receive_brand_specials_response.status_code == 200:
            receive_brand_specials_data = receive_brand_specials_response.json()
            if receive_brand_specials_data.get("data") is None:
                fn_print(f"用户【{self.user_name}】，===当前没有可以完成的品牌特惠任务===")
                return
            if receive_brand_specials_data.get("data").get("list") is None:
                fn_print(f"用户【{self.user_name}】，===当前没有可以完成的品牌特惠任务===")
                return
            ad_list = receive_brand_specials_data.get("data").get("list")
            for ad in ad_list:
                if ad.get("isReceived"):
                    continue
                aid = ad.get("id")
                receive_brand_specials_response = await self.client.post(
                    url="https://app.dewu.com/hacking-ad/v1/activity/receive",
                    headers=self.headers,
                    json={"bizId": "tree", "aid": aid}
                )
                receive_brand_specials_data = receive_brand_specials_response.json()
                fn_print(
                    f"用户【{self.user_name}】，===领取品牌特惠奖励成功✅✅, {receive_brand_specials_data.get('data').get('award')}g水滴💧===")
                await asyncio.sleep(1)
        else:
            fn_print(
                f"用户【{self.user_name}】，===领取品牌特惠奖励请求异常❌, {receive_brand_specials_response.status_code}===")

    async def get_tree_planting_progress(self):
        """
        获取许愿树的进度
        :return: 
        """
        get_tree_planting_progress_response = await self.client.get(
            url="https://app.dewu.com/hacking-tree/v1/tree/get_tree_info",
            headers=self.headers
        )
        if get_tree_planting_progress_response.status_code == 200:
            get_tree_planting_progress_data = get_tree_planting_progress_response.json()
            if get_tree_planting_progress_data.get("code") != 200:
                fn_print(f"用户【{self.user_name}】，===获取许愿树进度失败❌, {get_tree_planting_progress_data}===")
                return
            self.tree_id = get_tree_planting_progress_data.get("data").get("treeId")
            level = get_tree_planting_progress_data.get("data").get("level")
            current_level_need_watering_droplet = get_tree_planting_progress_data.get("data").get(
                "currentLevelNeedWateringDroplet")
            user_watering_droplet = get_tree_planting_progress_data.get('data').get('userWateringDroplet')
            fn_print(
                f"用户【{self.user_name}】，===当前许愿树等级：{level}级{user_watering_droplet}/{current_level_need_watering_droplet}===")
        else:
            fn_print(
                f"用户【{self.user_name}】，===获取许愿树进度请求异常❌, {get_tree_planting_progress_response.status_code}===")

    async def waterting(self):
        """
        浇水
        :return: 
        """
        if self.is_team_tree:
            return await self.team_waterting()
        waterting_response = await self.client.post(
            url="https://app.dewu.com/hacking-tree/v1/tree/watering",
            headers=self.headers
        )
        if waterting_response.status_code == 200:
            waterting_data = waterting_response.json()
            if waterting_data.get("code") != 200:
                fn_print(f"用户【{self.user_name}】，===浇水失败❌, {waterting_data}===")
                return False
            fn_print(f"用户【{self.user_name}】，===浇水成功✅✅===")
            if waterting_data.get("data").get("nextWateringTimes") == 0:
                fn_print(f"用户【{self.user_name}】，===开始领取浇水奖励===")
                await asyncio.sleep(1)
                await self.receive_watering_reward()
            return True
        else:
            fn_print(f"用户【{self.user_name}】，===浇水发生异常❌, {waterting_response.status_code}===")
            return False

    async def team_waterting(self):
        waterting_response = await self.client.post(
            url="https://app.dewu.com/hacking-tree/v1/team/tree/watering",
            headers=self.headers,
            json={
                "teamTreeId": self.tree_id
            }
        )
        if waterting_response.status_code == 200:
            team_waterting_data = waterting_response.json()
            if team_waterting_data.get("code") != 200:
                fn_print(f"用户【{self.user_name}】，===浇水失败❌, {team_waterting_data}===")
                return False
            fn_print(f"用户【{self.user_name}】，===浇水成功✅✅，成功浇水{self.waterting_g}g===")
            if team_waterting_data.get("data").get("nextWateringTimes") == 0:
                fn_print(f"用户【{self.user_name}】，===开始领取浇水奖励===")
                await asyncio.sleep(1)
                await self.receive_watering_reward()
            return True
        else:
            fn_print(f"用户【{self.user_name}】，===浇水发生异常❌, {waterting_response.status_code}===")

    async def run(self):
        await self.get_user_info()
        name, level = await self.tree_info()
        droplet_number = await self.get_droplet_number()
        if not (name and level and droplet_number):
            fn_print("请求数据异常！")
            return
        fn_print(f"用户【{self.user_name}】，===当前水滴数：{droplet_number}===")
        await self.determine_whether_is_team_tree()
        await self.get_tree_planting_progress()
        task_list = [
            self.droplet_sign_in(),
            self.receive_droplet_extra(),
            self.execute_task(),
            self.execute_cumulative_task(),
            self.judging_bucket_droplet(),
            self.execute_receive_watering_reward(),
            # self.waterting_droplet_extra(),
            self.receive_hybrid_online_reward(),
            self.receive_air_drop(),
            self.droplet_invest(),
            self.click_product(),
            self.receive_brand_specials(),
            self.help_user(),
            self.receive_help_reward(),
            self.receive_level_reward(),
            self.waterting_until_less_than()
        ]
        await asyncio.gather(*task_list)


async def main():
    task = []
    for index, (dw_x_auth_token, sk) in enumerate(zip(dw_x_auth_tokens, dw_sks)):
        dw = DeWu(dw_x_auth_token, index, sk)
        task.append(dw.run())
    await asyncio.gather(*task)


if __name__ == '__main__':
    asyncio.run(main())
