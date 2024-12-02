"""
变量Hykb_cookie
corn: 0 0 0,12 * * *
const $ = new Env('好游快爆');
"""
import asyncio
import os
import random
import re
import urllib.parse
import httpx

from datetime import datetime

from bs4 import BeautifulSoup

from fn_print import fn_print
from sendNotify import send_notification_message_collection

if 'Hykb_cookie' in os.environ:
    Hykb_cookie = re.split("@", os.environ.get("Hykb_cookie"))
else:
    Hykb_cookie = []
    print("未查找到Hykb_cookie变量.")


class HaoYouKuaiBao:
    def __init__(self, cookie):
        self.appointment_game_task_list = []
        self.moreManorToDo_tasks = []
        self.recommend_task_list = []
        self.small_game_task_list = []
        self.cookie = cookie
        self.headers = {
            "Origin": "https://huodong3.i3839.com",
            "Referer": "https://huodong3.3839.com/n/hykb/cornfarm/index.php?imm=0",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        }
        self.client = httpx.Client(
            base_url="https://huodong3.3839.com",
            verify=False,
            headers=self.headers
        )
        __user_info = self.__user_info()
        self.user_name = __user_info.get("user")
        self.device = cookie.split("|")[4]

    def __user_info(self):
        """
        获取用户的信息
        :return: 
        """
        try:
            u_response = self.client.post(
                url="/n/hykb/cornfarm/ajax.php",
                content=f"ac=login&r=0.{random.randint(100000000000000000, 899999999999999999)}&scookie={urllib.parse.quote(self.cookie)}"
            ).json()
            if u_response["key"] == "ok" and u_response["loginStatus"] == "100":
                return {
                    "user": u_response["config"]["name"],
                    "uid": u_response["config"]["uid"],
                    "device_id": u_response["config"]["deviceid"]
                }
            else:
                print("好游快爆-获取用户信息出现错误：{}".format(u_response))
        except Exception as e:
            print("好游快爆-获取用户信息出现错误：{}".format(e))

    async def login(self):
        """
        登录
        :return: 
        """
        try:
            l_response = self.client.post(
                url="/n/hykb/cornfarm/ajax.php",
                content=f"ac=login&r=0.{random.randint(100000000000000000, 899999999999999999)}&scookie={urllib.parse.quote(self.cookie)}&device={self.device}"
            ).json()
            # fn_print("="*10 + f"【{self.user_name}】登录成功" + "="*10)
            return l_response
        except Exception as e:
            fn_print("好游快爆-登录出现错误：{}".format(e))

    # 浇水
    async def watering(self):
        """
        浇水
        :return: 
        """
        try:
            w_response = self.client.post(
                url="/n/hykb/cornfarm/ajax_sign.php",
                content=f"ac=Sign&verison=1.5.7.005&OpenAutoSign=&r=0.{random.randint(100000000000000000, 899999999999999999)}&scookie={urllib.parse.quote(self.cookie)}&device={self.device}"
            ).json()
            if w_response["key"] == "ok":
                fn_print("={}=, 浇水成功💧💧💧".format(self.user_name))
                return 1, w_response["add_baomihua"]
            elif w_response["key"] == "1001":
                fn_print("={}=, 今日已浇水".format(self.user_name))
                return 0, 0
            else:
                fn_print(f"={self.user_name}=, ❌浇水出现错误：{w_response}")
                return -1, 0
        except Exception as e:
            fn_print(f"={self.user_name}=, ❌浇水异常：{e}")
            return -1, 0

    # 收获
    async def harvest(self):
        """
        收获
        :return: 
        """
        try:
            h_response = self.client.post(
                url="/n/hykb/cornfarm/ajax_plant.php",
                content=f"ac=Harvest&r=0.{random.randint(100000000000000000, 899999999999999999)}&scookie={urllib.parse.quote(self.cookie)}&device={self.device}"
            ).json()
            if h_response["key"] == "ok":
                fn_print("={}=, 收获成功🌽🌽🌽".format(self.user_name))
            elif h_response["key"] == "503":
                fn_print(f"={self.user_name}=, {h_response['info']}")
            else:
                fn_print(f"={self.user_name}=, ❌收获失败：{h_response}")
        except Exception as e:
            fn_print(f"={self.user_name}=, ❌收获异常：{e}")

    # 播种
    async def plant(self):
        """
        播种
        :return: 
        """
        try:
            p_response = self.client.post(
                url="/n/hykb/cornfarm/ajax_plant.php",
                content=f"ac=Plant&r=0.{random.randint(100000000000000000, 899999999999999999)}&scookie={urllib.parse.quote(self.cookie)}&device={self.device}"
            ).json()
            if p_response["key"] == "ok":
                fn_print("={}=, 播种成功🌾🌾🌾".format(self.user_name))
                return 1
            else:
                if p_response['seed'] == '0':
                    fn_print("={}=, 种子已用完".format(self.user_name))
                    return -1
                else:
                    fn_print(f"={self.user_name}=, ❌播种失败：{p_response}")
                    return 0
        except Exception as e:
            fn_print(f"={self.user_name}=, ❌播种异常：{e}")

    # 获取种子商品
    async def get_goods(self):
        """
        获取种子商品
        :return: 
        """
        try:
            s_response = self.client.post(
                url="https://shop.3839.com/index.php?c=Index&a=initCard",
                content=f"pid=1660&r=0.{random.randint(100000000000000000, 899999999999999999)}&scookie={urllib.parse.quote(self.cookie)}&device={self.device}"
            ).json()
            if s_response['code'] == 200:
                return s_response['data']['store_id'], s_response['data']['product_name']
        except Exception as e:
            fn_print("好游快爆-获取商品id出现错误：{}".format(e))

    # 购买种子
    async def buy_seeds(self):
        """
        购买种子
        :return: 
        """
        # 获取种子商品id
        goods_id, goods_name = await self.get_goods()
        cbs_response = self.client.post(
            url="/n/hykb/bmhstore2/inc/virtual/ajaxVirtual.php",
            content=f"ac=checkExchange&gid={goods_id}&t={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}&r=0.{random.randint(100000000000000000, 899999999999999999)}&scookie={urllib.parse.quote(self.cookie)}&device={self.device}"
        ).json()
        if cbs_response['key'] != "200" and cbs_response['msg'] != "验证通过":
            fn_print(f"={self.user_name}=, ❌购买种子出现错误：{cbs_response}")
            return False
        else:
            # 购买种子
            bs_response = self.client.post(
                url="/n/hykb/bmhstore2/inc/virtual/ajaxVirtual.php",
                content=f"ac=exchange&t={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}&r=0.{random.randint(100000000000000000, 899999999999999999)}&goodsid={goods_id}&scookie={urllib.parse.quote(self.cookie)}&device={self.device}"
            ).json()
            if bs_response['key'] == 200:
                fn_print(f"={self.user_name}=, 购买种子成功，还剩下🍿爆米花{bs_response['bmh']}个")
                return True
            else:
                fn_print(f"={self.user_name}=, ❌购买种子失败：{bs_response}")
                return False

    # 获取今日必做推荐任务id
    async def get_recommend_task_ids(self):
        """
        获取今日必做推荐任务id
        :return: 
        """
        response = self.client.get("/n/hykb/cornfarm/index.php?imm=0")
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        task_list = soup.select(".taskDailyUl > li")
        for task_item in task_list:
            tasks_infos = task_item.select_one("dl")
            id_param = tasks_infos.select_one("dd")["class"][0]
            title_param = tasks_infos.select_one("dt").get_text()
            reward_param = tasks_infos.select_one("dd").get_text()
            if "分享福利" in title_param or "分享资讯" in title_param:
                self.recommend_task_list.append(
                    {
                        "bmh_task_id": re.search(r"daily_dd_(.+)", id_param).group(1),
                        "bmh_task_title": re.search(r"分享福利：(.*)", title_param).group(
                            1) if "分享福利" in title_param else re.search(r"分享资讯：(.*)", title_param).group(1),
                        "reward_num": re.search(r"可得+(.+)", reward_param).group(1)
                    }
                )
            elif "免安装、即点即玩" in task_item.select("div.task-info")[0].get_text():
                self.small_game_task_list.append(
                    {
                        "bmh_task_id": re.search(r"daily_dd_(.+)", id_param).group(1),
                        "bmh_task_title": title_param,
                        "reward_num": re.search(r"可得+(.+)", reward_param).group(1)
                    }
                )
            elif "预约" in task_item.select("div.task-info")[0].get_text():
                self.appointment_game_task_list.append(
                    {
                        "bmh_task_id": re.search(r"daily_dd_(.+)", id_param).group(1),
                        "bmh_task_title": title_param,
                        "reward_num": re.search(r"可得+(.+)", reward_param).group(1)
                    }
                )

    async def get_moreManorToDo_task_ids(self):
        """
        获取更多庄园必做任务id
        :return: 
        """
        m_response = self.client.get("/n/hykb/cornfarm/index.php?imm=0")
        html = m_response.text
        soup = BeautifulSoup(html, 'html.parser')
        task_list = soup.select(".taskYcxUl > li")
        for task_item in task_list:
            task_info = task_item.select_one("dl")
            id_param = task_info["onclick"]
            title_param = task_info.select_one("dt").get_text()
            reward_param = task_info.select_one("dd").get_text()
            self.moreManorToDo_tasks.append(
                {
                    "bmh_task_id": re.search(r"ShowLue\((.+),'ycx'\); return false;", id_param).group(1),
                    "bmh_task_title": title_param,
                    "reward_num": re.search(r"可得+(.+)", reward_param).group(1)
                }
            )

    async def appointment_game_task(self, recommend_task):
        """
        预约游戏任务
        :param recommend_task: 
        :return: 
        """
        try:
            daily_game_detail_response = self.client.post(
                url="/n/hykb/cornfarm/ajax_daily.php",
                content=f"ac=DailyGameDetail&id={recommend_task['bmh_task_id']}&r=0.{random.randint(100000000000000, 8999999999999999)}&scookie={urllib.parse.quote(self.cookie)}&device={self.device}"
            ).json()
            if daily_game_detail_response["key"] == "ok":
                fn_print(f"={self.user_name}=, 预约游戏任务成功，任务名称：{recommend_task['bmh_task_title']}")
        except Exception as e:
            fn_print(f"={self.user_name}=, 预约游戏任务调度任务异常：", e)

    async def receive_yuyue_game_rewards(self, recommend_task):
        """
        领取预约游戏任务奖励
        :param recommend_task: 
        :return: 
        """
        try:
            daily_yuyue_ling_response = self.client.post(
                url="/n/hykb/cornfarm/ajax_daily.php",
                content=f"ac=DailyYuyueLing&id={recommend_task['bmh_task_id']}&smdeviceid=BIb2%2B05P0FzEEGiSf%2Fg59Gok28Sb6y1tyhmR8RlC2X0FUtOGCbu3ONvgIEoA2hae0BrOCLXtqoWe1TgeVHU0L7A%3D%3D&verison=1.5.7.507&r=0.{random.randint(100000000000000, 8999999999999999)}&scookie={urllib.parse.quote(self.cookie)}&device={self.device}"
            ).json()
            if daily_yuyue_ling_response["key"] == "ok":
                fn_print(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- 可以领奖了🎉🎉🎉")
            else:
                fn_print(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- 奖励领取失败❌, {daily_yuyue_ling_response}")
        except Exception as e:
            fn_print(f"={self.user_name}=, 领取预约游戏任务奖励异常：", e)

    async def do_tasks_every_day(self, recommend_task):
        """
        每日必做推荐任务
        :param recommend_task: 
        :return: 
        """
        try:
            daily_share_response = self.client.post(
                url="/n/hykb/cornfarm/ajax_daily.php",
                content=f"ac=DailyShare&id={recommend_task['bmh_task_id']}&onlyc=0&r=0.{random.randint(100000000000000, 8999999999999999)}&scookie={urllib.parse.quote(self.cookie)}&device={self.device}"
            ).json()
            if daily_share_response["key"] != "2002":
                return False
            # 回调任务
            daily_share_callback_response = self.client.post(
                url="/n/hykb/cornfarm/ajax_daily.php",
                content=f"ac=DailyShareCallback&id={recommend_task['bmh_task_id']}&mode=qq&source=ds&r=0.{random.randint(100000000000000, 8999999999999999)}"
                        f"&scookie={urllib.parse.quote(self.cookie)}&device={self.device}"
            ).json()
            if daily_share_callback_response["key"] == "ok" and daily_share_callback_response["info"] == "可以领奖":
                fn_print(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- 可以领奖了🎉🎉🎉")
                return True
            elif daily_share_callback_response["key"] == "2002":
                fn_print(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- 已经领过奖励了🎁")
                return False
            else:
                fn_print(
                    f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- \n{daily_share_callback_response}\n不可以领奖🫷🫸")
                return False
        except Exception as e:
            fn_print(f"={self.user_name}=, 调度任务异常：", e)

    async def do_small_game_task(self, recommend_task):
        """
        免安装、即点即玩的小游戏任务
        :param recommend_task: 
        :return: 
        """
        try:
            daily_small_game_response = self.client.post(
                url="/n/hykb/cornfarm/ajax_daily.php",
                content=f"ac=DailySmallGame&id={recommend_task['bmh_task_id']}&r=0.{random.randint(100000000000000, 8999999999999999)}&scookie={urllib.parse.quote(self.cookie)}&device={self.device}"
            ).json()
            if daily_small_game_response["key"] == "ok":
                fn_print(f"={self.user_name}=, 小游戏任务🎮🎮🎮-{recommend_task['bmh_task_title']}- 可以领奖了🎉🎉🎉")
                return True
            else:
                fn_print(
                    f"={self.user_name}=, 小游戏任务🎮🎮🎮-{recommend_task['bmh_task_title']}- ❌游玩小游戏任务失败：{daily_small_game_response}")
                return False
        except Exception as e:
            fn_print(f"={self.user_name}=, 小游戏任务调度任务异常：", e)

    async def receive_small_game_reward(self, recommend_task):
        """
        领取免安装、即点即玩的小游戏任务奖励
        :param recommend_task: 
        :return: 
        """
        try:
            recevie_small_game_reward_response = self.client.post(
                url="/n/hykb/cornfarm/ajax_daily.php",
                content=f"ac=DailySmallGameLing&id={recommend_task['bmh_task_id']}&VersionCode=342&smdeviceid=BIb2%2B05P0FzEEGiSf%2Fg59Gok28Sb6y1tyhmR8RlC2X0FUtOGCbu3ONvgIEoA2hae0BrOCLXtqoWe1TgeVHU0L7A%3D%3D&verison=1.5.7.507&r=0.{random.randint(100000000000000, 8999999999999999)}&scookie={urllib.parse.quote(self.cookie)}&device={self.device}"
            ).json()
            if recevie_small_game_reward_response["key"] == "ok":
                fn_print(f"={self.user_name}=, 小游戏任务🎮🎮🎮-{recommend_task['bmh_task_title']}- ✅领取任务奖励成功！")
            elif recevie_small_game_reward_response["key"] == "2001":
                fn_print(f"={self.user_name}=, 小游戏任务🎮🎮🎮-{recommend_task['bmh_task_title']}- 已经领过奖励了！")
            elif recevie_small_game_reward_response["key"] == "2005":  # 表示成熟度已经满了，先收割再播种（如果没有种子就先去购买种子），再领取小游戏任务奖励
                # 收割
                await self.harvest()
                # 播种
                plant_status = await self.plant()
                if plant_status == -1:  # 没有种子
                    fn_print("={}=, 播种失败，没有种子".format(self.user_name))
                    # 购买种子
                    await self.buy_seeds()
                    await self.plant()
                elif plant_status == 1:
                    ...
                else:
                    fn_print("={}=, 播种失败".format(self.user_name))
                # 领取小游戏任务奖励
                await self.receive_small_game_reward(recommend_task)
            else:
                fn_print(
                    f"={self.user_name}=, 小游戏任务🎮🎮🎮-{recommend_task['bmh_task_title']}- ❌领取任务奖励失败：{recevie_small_game_reward_response}")
        except Exception as e:
            fn_print(f"={self.user_name}=, 小游戏任务领取奖励异常：", e)

    async def receive_commendDaily_reward(self, recommend_task):
        """
        领取每日必做推荐任务奖励
        :param recommend_task: 
        :return: 
        """
        try:
            recevie_daily_reward_response = self.client.post(
                url="/n/hykb/cornfarm/ajax_daily.php",
                content=f"ac=DailyShareLing&smdeviceid=BTeK4FWZx3plsETCF1uY6S1h2uEajvI1AicKa4Lqz3U7Tt5wKKDZZqVmVr7WpkcEuSQKyiDA3d64bErE%2FsaJp3Q%3D%3D&verison=1.5.7.507&id={recommend_task['bmh_task_id']}&r=0.{random.randint(100000000000000, 8999999999999999)}&scookie={self.cookie}"
                        f"&device={self.device}"
            ).json()
            if recevie_daily_reward_response["key"] == "ok":
                fn_print(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- ✅领取任务奖励成功！")
            elif recevie_daily_reward_response["key"] == "2001":
                fn_print(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- 今天已经领取过了！")
            else:
                fn_print(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- 领取任务奖励失败！")
        except Exception as e:
            fn_print(f"={self.user_name}=, 领取任务奖励异常：", e)

    async def process_doItRecommendDaily_task(self, recommend_task):
        """
        处理每日必做推荐任务
        :param recommend_task: 每日必做推荐任务信息
        :return: 
        """
        await self.do_tasks_every_day(recommend_task)  # 调度任务
        await self.receive_commendDaily_reward(recommend_task)  # 领取任务奖励 

    async def process_yuyue_game_task(self, recommend_task):
        await self.appointment_game_task(recommend_task)
        await self.receive_yuyue_game_rewards(recommend_task)

    async def process_small_game_task(self, recommend_task):
        """
        处理免安装、即点即玩的小游戏任务
        :param recommend_task: 
        :return: 
        """
        await self.do_small_game_task(recommend_task)
        await asyncio.sleep(60 * 5)
        await self.receive_small_game_reward(recommend_task)

    async def run_task(self):
        """
        执行任务
        :return: 
        """
        await self.get_recommend_task_ids()

        await asyncio.gather(
            *[self.process_doItRecommendDaily_task(task) for task in self.recommend_task_list],
            *[self.process_small_game_task(task) for task in self.small_game_task_list],
            *[self.process_yuyue_game_task(task) for task in self.appointment_game_task_list]
        )

    async def run(self):
        data = await self.login()
        if data['key'] == 'ok':
            fn_print("=" * 10 + f"【{self.user_name}】登录成功" + "=" * 10)
            # 优先判断成熟度是否已满
            if data['config']['csd_jdt'] == "100%":
                await self.harvest()
                data = await self.login()
            # 判断是否已播种
            if data['config']['grew'] == '-1':
                plant_status = await self.plant()
                if plant_status == -1:
                    fn_print("={}=, 播种失败，没有种子".format(self.user_name))
                    # 购买种子
                    await self.buy_seeds()
                    await self.plant()
                elif plant_status == 1:
                    ...
                else:
                    fn_print("={}=, 播种失败".format(self.user_name))
            await self.watering()
            fn_print("=" * 10 + f"【{self.user_name}】开始执行每日必做推荐任务" + "=" * 10)
            await self.run_task()
        else:
            fn_print(f"={self.user_name}=, ❌登录失败：{data}")


async def main():
    tasks = []
    for cookie_ in Hykb_cookie:
        hykb = HaoYouKuaiBao(cookie_)
        tasks.append(hykb.run())
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())
    send_notification_message_collection("好游快爆活动奖励领取通知 - {}".format(datetime.now().strftime("%Y/%m/%d")))
