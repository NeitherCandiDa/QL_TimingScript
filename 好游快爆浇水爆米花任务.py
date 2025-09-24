"""
变量Hykb_cookie
cron: 0 0 0,12 * * *
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
from get_env import get_env
from sendNotify import send_notification_message_collection
from typing import Dict, List, Tuple, Optional

# 统一配置常量（不封装 http 客户端，仅集中常量与枚举）
from hykb_config import API_CONFIG, API_ENDPOINTS, ERROR_CODES, TASK_DELAYS

Hykb_cookie = get_env("Hykb_cookie", "@")


class HaoYouKuaiBao:
    def __init__(self, cookie: str):
        """
        好游快爆核心执行器。

        - 负责会话初始化、任务解析与任务执行。
        - 不封装 http 客户端，仅复用 httpx.Client，统一常量与参数构建。
        """
        self.appointment_game_task_list: List[Dict[str, str]] = []
        self.moreManorToDo_tasks: List[Dict[str, str]] = []
        self.share_task_list: List[Dict[str, str]] = []
        self.small_game_task_list: List[Dict[str, str]] = []
        self.cookie: str = cookie
        self.headers: Dict[str, str] = API_CONFIG["headers"]
        self.client = httpx.Client(
            base_url=API_CONFIG["base_url"],
            verify=False,
            headers=self.headers
        )
        __user_info = self.__user_info()
        self.user_name: str = __user_info.get("user") if __user_info else ""
        # cookie 统一约定：第 5 段为 device
        self.device: str = cookie.split("|")[4] if "|" in cookie else ""

    # -------------------------
    # 基础辅助方法
    # -------------------------
    @staticmethod
    def _rand() -> str:
        """生成与原脚本一致的 0.x 随机参数。"""
        return f"0.{random.randint(100000000000000000, 899999999999999999)}"

    def _encode_cookie(self) -> str:
        return urllib.parse.quote(self.cookie)

    def _post(self, url: str, content: str) -> Dict:
        """统一 POST 请求，保持原参数风格。"""
        return self.client.post(url=url, content=content).json()

    def _get_text(self, url: str) -> str:
        return self.client.get(url).text

    def __user_info(self) -> Optional[Dict[str, str]]:
        """
        获取用户的信息
        :return: 
        """
        try:
            u_response = self._post(
                url=API_ENDPOINTS["login"],
                content=f"ac=login&r={self._rand()}&scookie={self._encode_cookie()}"
            )
            if u_response.get("key") == ERROR_CODES["SUCCESS"] and u_response.get("loginStatus") == "100":
                return {
                    "user": u_response["config"]["name"],
                    "uid": u_response["config"]["uid"],
                    "device_id": u_response["config"]["deviceid"]
                }
            else:
                print("好游快爆-获取用户信息出现错误：{}".format(u_response))
        except Exception as e:
            print("好游快爆-获取用户信息出现错误：{}".format(e))

    async def login(self) -> Dict:
        """
        登录
        :return: 
        """
        try:
            l_response = self._post(
                url=API_ENDPOINTS["login"],
                content=f"ac=login&r={self._rand()}&scookie={self._encode_cookie()}&device={self.device}"
            )
            return l_response
        except Exception as e:
            fn_print("好游快爆-登录出现错误：{}".format(e))

    # 浇水
    async def watering(self) -> Tuple[int, int]:
        """
        浇水
        :return: 
        """
        try:
            w_response = self._post(
                url=API_ENDPOINTS["watering"],
                content=f"ac=Sign&verison=1.5.7.005&OpenAutoSign=&r={self._rand()}&scookie={self._encode_cookie()}&device={self.device}"
            )
            if w_response.get("key") == ERROR_CODES["SUCCESS"]:
                fn_print("={}=, 浇水成功💧💧💧".format(self.user_name))
                return 1, w_response["add_baomihua"]
            elif w_response.get("key") == ERROR_CODES["ALREADY_DONE"]:
                fn_print("={}=, 今日已浇水".format(self.user_name))
                return 0, 0
            else:
                fn_print(f"={self.user_name}=, ❌浇水出现错误：{w_response}")
                return -1, 0
        except Exception as e:
            fn_print(f"={self.user_name}=, ❌浇水异常：{e}")
            return -1, 0

    # 收获
    async def harvest(self) -> None:
        """
        收获
        :return: 
        """
        try:
            h_response = self._post(
                url=API_ENDPOINTS["plant"],
                content=f"ac=Harvest&r={self._rand()}&scookie={self._encode_cookie()}&device={self.device}"
            )
            if h_response.get("key") == ERROR_CODES["SUCCESS"]:
                fn_print("={}=, 收获成功🌽🌽🌽".format(self.user_name))
            elif h_response.get("key") == ERROR_CODES["NO_SEEDS"]:
                fn_print(f"={self.user_name}=, {h_response['info']}")
            else:
                fn_print(f"={self.user_name}=, ❌收获失败：{h_response}")
        except Exception as e:
            fn_print(f"={self.user_name}=, ❌收获异常：{e}")

    # 播种
    async def plant(self) -> int:
        """
        播种
        :return: 
        """
        try:
            p_response = self._post(
                url=API_ENDPOINTS["plant"],
                content=f"ac=Plant&corn_id=1&r={self._rand()}&scookie={self._encode_cookie()}&device={self.device}"
            )
            if p_response.get("key") == ERROR_CODES["SUCCESS"]:
                fn_print("={}=, 播种成功🌾🌾🌾".format(self.user_name))
                return 1
            else:
                if p_response.get('seed') == '0':
                    fn_print("={}=, 种子已用完".format(self.user_name))
                    return -1
                else:
                    fn_print(f"={self.user_name}=, ❌播种失败：{p_response}")
                    return 0
        except Exception as e:
            fn_print(f"={self.user_name}=, ❌播种异常：{e}")

    # 获取种子商品
    async def get_goods(self) -> Optional[Tuple[str, str]]:
        """
        获取种子商品
        :return: 
        """
        try:
            s_response = self._post(
                url=API_ENDPOINTS["get_goods"],
                content=f"pid=1660&r={self._rand()}&scookie={self._encode_cookie()}&device={self.device}"
            )
            if s_response['code'] == 200:
                return s_response['data']['store_id'], s_response['data']['product_name']
        except Exception as e:
            fn_print("好游快爆-获取商品id出现错误：{}".format(e))

    # 购买种子
    async def buy_seeds(self) -> bool:
        """
        购买种子
        :return: 
        """
        # 获取种子商品id
        goods = await self.get_goods()
        if not goods:
            fn_print(f"={self.user_name}=, ❌获取商品信息失败，无法购买种子")
            return False
        goods_id, goods_name = goods
        cbs_response = self._post(
            url=API_ENDPOINTS["buy_seeds"],
            content=f"ac=checkExchange&gid={goods_id}&t={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}&r={self._rand()}&scookie={self._encode_cookie()}&device={self.device}"
        )
        if cbs_response['key'] != "200" and cbs_response['msg'] != "验证通过":
            fn_print(f"={self.user_name}=, ❌购买种子出现错误：{cbs_response}")
            return False
        else:
            # 购买种子
            bs_response = self._post(
                url=API_ENDPOINTS["buy_seeds"],
                content=f"ac=exchange&t={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}&r={self._rand()}&goodsid={goods_id}&scookie={self._encode_cookie()}&device={self.device}"
            )
            if bs_response['key'] == 200:
                fn_print(f"={self.user_name}=, 购买种子成功，还剩下🍿爆米花{bs_response['bmh']}个")
                return True
            else:
                fn_print(f"={self.user_name}=, ❌购买种子失败：{bs_response}")
                return False

    # 获取今日必做推荐任务id
    async def get_recommend_task_ids(self) -> None:
        """
        获取今日必做推荐任务id
        :return: 
        """
        html = self._get_text("/n/hykb/cornfarm/index.php?imm=0")
        soup = BeautifulSoup(html, 'html.parser')
        task_list = soup.select(".taskDailyUl > li")
        for task_item in task_list:
            task_type = task_item.attrs.get("data-mode")
            tasks_infos = task_item.select_one("dl")
            id_param = tasks_infos.select_one("dd")["class"][0]
            title_param = tasks_infos.select_one("dt").get_text()
            reward_param = tasks_infos.select_one("dd").get_text()
            if task_type == "1":
                self.share_task_list.append(
                    {
                        "bmh_task_id": re.search(r"daily_dd_(.+)", id_param).group(1),
                        "bmh_task_title": title_param,
                        "reward_num": re.search(r"可得+(.+)", reward_param).group(1)
                    }
                )
            elif task_type == "15":
                self.small_game_task_list.append(
                    {
                        "bmh_task_id": re.search(r"daily_dd_(.+)", id_param).group(1),
                        "bmh_task_title": title_param,
                        "reward_num": re.search(r"可得+(.+)", reward_param).group(1)
                    }
                )
            elif task_type == "9":
                self.appointment_game_task_list.append(
                    {
                        "bmh_task_id": re.search(r"daily_dd_(.+)", id_param).group(1),
                        "bmh_task_title": title_param,
                        "reward_num": re.search(r"可得+(.+)", reward_param).group(1)
                    }
                )

    async def get_moreManorToDo_task_ids(self) -> None:
        """
        获取更多庄园必做任务id
        :return: 
        """
        html = self._get_text("/n/hykb/cornfarm/index.php?imm=0")
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

    async def appointment_game_task(self, recommend_task: Dict[str, str]) -> None:
        """
        预约游戏任务
        :param recommend_task: 
        :return: 
        """
        try:
            daily_game_detail_response = self._post(
                url=API_ENDPOINTS["daily_task"],
                content=f"ac=DailyGameDetail&id={recommend_task['bmh_task_id']}&r={self._rand()}&scookie={self._encode_cookie()}&device={self.device}"
            )
            if daily_game_detail_response.get("key") == ERROR_CODES["SUCCESS"]:
                fn_print(f"={self.user_name}=, 预约游戏任务成功，任务名称：{recommend_task['bmh_task_title']}")
        except Exception as e:
            fn_print(f"={self.user_name}=, 预约游戏任务调度任务异常：", e)

    async def receive_yuyue_game_rewards(self, recommend_task: Dict[str, str]) -> None:
        """
        领取预约游戏任务奖励
        :param recommend_task: 
        :return: 
        """
        try:
            daily_yuyue_ling_response = self._post(
                url=API_ENDPOINTS["daily_task"],
                content=f"ac=DailyYuyueLing&id={recommend_task['bmh_task_id']}&smdeviceid=BIb2%2B05P0FzEEGiSf%2Fg59Gok28Sb6y1tyhmR8RlC2X0FUtOGCbu3ONvgIEoA2hae0BrOCLXtqoWe1TgeVHU0L7A%3D%3D&verison=1.5.7.507&r={self._rand()}&scookie={self._encode_cookie()}&device={self.device}"
            )
            if daily_yuyue_ling_response.get("key") == ERROR_CODES["SUCCESS"]:
                fn_print(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- 可以领奖了🎉🎉🎉")
            else:
                fn_print(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- 奖励领取失败❌, {daily_yuyue_ling_response}")
        except Exception as e:
            fn_print(f"={self.user_name}=, 领取预约游戏任务奖励异常：", e)

    async def do_tasks_by_share(self, recommend_task: Dict[str, str]) -> bool:
        """
        分享类型任务
        :param recommend_task: 
        :return: 
        """
        try:
            daily_share_response = self._post(
                url=API_ENDPOINTS["daily_task"],
                content=f"ac=DailyShare&id={recommend_task['bmh_task_id']}&onlyc=0&r={self._rand()}&scookie={self._encode_cookie()}&device={self.device}"
            )
            if daily_share_response.get("key") != ERROR_CODES["TASK_READY"]:
                return False
            # 回调任务
            daily_share_callback_response = self._post(
                url=API_ENDPOINTS["daily_task"],
                content=f"ac=DailyShareCallback&id={recommend_task['bmh_task_id']}&mode=qq&source=ds&r={self._rand()}&scookie={self._encode_cookie()}&device={self.device}"
            )
            if daily_share_callback_response.get("key") == ERROR_CODES["SUCCESS"] and daily_share_callback_response.get("info") == "可以领奖":
                fn_print(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- 可以领奖了🎉🎉🎉")
                return True
            elif daily_share_callback_response.get("key") == ERROR_CODES["TASK_READY"]:
                fn_print(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- 已经领过奖励了🎁")
                return False
            else:
                fn_print(
                    f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- \n{daily_share_callback_response}\n不可以领奖🫷🫸")
                return False
        except Exception as e:
            fn_print(f"={self.user_name}=, 调度任务异常：", e)

    async def do_small_game_task(self, recommend_task: Dict[str, str]) -> bool:
        """
        免安装、即点即玩的小游戏任务
        :param recommend_task: 
        :return: 
        """
        try:
            daily_small_game_response = self._post(
                url=API_ENDPOINTS["daily_task"],
                content=f"ac=DailySmallGame&id={recommend_task['bmh_task_id']}&r={self._rand()}&scookie={self._encode_cookie()}&device={self.device}"
            )
            if daily_small_game_response.get("key") == ERROR_CODES["SUCCESS"]:
                fn_print(f"={self.user_name}=, 小游戏任务🎮🎮🎮-{recommend_task['bmh_task_title']}- 可以领奖了🎉🎉🎉")
                return True
            else:
                fn_print(
                    f"={self.user_name}=, 小游戏任务🎮🎮🎮-{recommend_task['bmh_task_title']}- ❌游玩小游戏任务失败：{daily_small_game_response}")
                return False
        except Exception as e:
            fn_print(f"={self.user_name}=, 小游戏任务调度任务异常：", e)

    async def receive_small_game_reward(self, recommend_task: Dict[str, str]) -> None:
        """
        领取免安装、即点即玩的小游戏任务奖励
        :param recommend_task: 
        :return: 
        """
        try:
            recevie_small_game_reward_response = self._post(
                url=API_ENDPOINTS["daily_task"],
                content=f"ac=DailySmallGameLing&id={recommend_task['bmh_task_id']}&VersionCode=342&smdeviceid=BIb2%2B05P0FzEEGiSf%2Fg59Gok28Sb6y1tyhmR8RlC2X0FUtOGCbu3ONvgIEoA2hae0BrOCLXtqoWe1TgeVHU0L7A%3D%3D&verison=1.5.7.507&r={self._rand()}&scookie={self._encode_cookie()}&device={self.device}"
            )
            if recevie_small_game_reward_response.get("key") == ERROR_CODES["SUCCESS"]:
                fn_print(f"={self.user_name}=, 小游戏任务🎮🎮🎮-{recommend_task['bmh_task_title']}- ✅领取任务奖励成功！")
            elif recevie_small_game_reward_response.get("key") == ERROR_CODES["TASK_DONE"]:
                fn_print(f"={self.user_name}=, 小游戏任务🎮🎮🎮-{recommend_task['bmh_task_title']}- 已经领过奖励了！")
            elif recevie_small_game_reward_response.get("key") == ERROR_CODES["NEED_HARVEST"]:  # 表示成熟度已经满了，先收割再播种，再领取小游戏任务奖励
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

    async def receive_share_task_reward(self, recommend_task: Dict[str, str]) -> None:
        """
        领取分享类型的任务奖励
        :param recommend_task: 
        :return: 
        """
        try:
            recevie_daily_reward_response = self._post(
                url=API_ENDPOINTS["daily_task"],
                content=f"ac=DailyShareLing&smdeviceid=BTeK4FWZx3plsETCF1uY6S1h2uEajvI1AicKa4Lqz3U7Tt5wKKDZZqVmVr7WpkcEuSQKyiDA3d64bErE%2FsaJp3Q%3D%3D&verison=1.5.7.507&id={recommend_task['bmh_task_id']}&r={self._rand()}&scookie={self.cookie}&device={self.device}"
            )
            if recevie_daily_reward_response.get("key") == ERROR_CODES["SUCCESS"]:
                fn_print(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- ✅领取任务奖励成功！")
            elif recevie_daily_reward_response.get("key") == ERROR_CODES["TASK_DONE"]:
                fn_print(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- 今天已经领取过了！")
            else:
                fn_print(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- 领取任务奖励失败！")
        except Exception as e:
            fn_print(f"={self.user_name}=, 领取任务奖励异常：", e)

    async def process_share_task(self, recommend_task: Dict[str, str]) -> None:
        """
        处理分享类的任务
        :param recommend_task: 分享类的任务信息
        :return: 
        """
        await self.do_tasks_by_share(recommend_task)  # 调度任务
        await self.receive_share_task_reward(recommend_task)  # 领取任务奖励 

    async def process_yuyue_game_task(self, recommend_task: Dict[str, str]) -> None:
        await self.appointment_game_task(recommend_task)
        await self.receive_yuyue_game_rewards(recommend_task)

    async def process_small_game_task(self, recommend_task: Dict[str, str]) -> None:
        """
        处理免安装、即点即玩的小游戏任务
        :param recommend_task: 
        :return: 
        """
        await self.do_small_game_task(recommend_task)
        await asyncio.sleep(TASK_DELAYS["small_game"])  # 默认 5 分钟
        await self.receive_small_game_reward(recommend_task)

    async def run_task(self) -> None:
        """
        执行任务
        :return: 
        """
        await self.get_recommend_task_ids()

        await asyncio.gather(
            *[self.process_share_task(task) for task in self.share_task_list], # 分享类型的任务
            *[self.process_small_game_task(task) for task in self.small_game_task_list],    # 免安装、即点即玩的小游戏任务
            *[self.process_yuyue_game_task(task) for task in self.appointment_game_task_list]   # 预约游戏任务
        )

    async def run(self) -> None:
        data = await self.login()
        if data.get('key') == ERROR_CODES["SUCCESS"]:
            fn_print("=" * 10 + f"【{self.user_name}】登录成功" + "=" * 10)
            # 优先判断成熟度是否已满
            if data['config']['csd_jdt'] == "100%":
                # 收获
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
