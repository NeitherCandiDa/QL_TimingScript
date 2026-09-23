"""
变量Hykb_cookie
cron: 0 0 0,12 * * *
const $ = new Env('好游快爆');
"""
import random
import re
import time
import urllib.parse
import warnings
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import log
from get_env import get_env
from hykb_config import API_CONFIG, API_ENDPOINTS, ERROR_CODES, TASK_DELAYS
from sendNotify import send_notification_message_collection
from urllib3.exceptions import InsecureRequestWarning

warnings.filterwarnings('ignore', category=InsecureRequestWarning)

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
        self.client = requests.Session()
        self.client.headers.update(self.headers)
        self.client.verify = False
        __user_info = self.__user_info()
        self.user_name: str = __user_info.get("user") if __user_info else ""
        self.seed = int(__user_info.get("seed") if __user_info else 0)
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

    def _post(self, url: str, data: Any) -> Dict:
        """统一 POST 请求"""
        return self.client.post(url=url, data=data).json()

    def _get_text(self, url: str) -> str:
        return self.client.get(url).text

    def check_and_handle_corn_maturity(self) -> bool:
        """
        检查并处理玉米成熟度，如果达到100%则自动收割和播种
        :return: 是否进行了收割操作
        """
        try:
            # 重新登录获取最新状态
            data = self.login()
            if data.get('key') == ERROR_CODES["SUCCESS"]:
                # 检查成熟度是否达到100%
                if data['config']['csd_jdt'] == "100%":
                    log.log(f"={self.user_name}=, 🌽检测到玉米成熟度100%，开始收割...")
                    # 收割
                    self.harvest()
                    # 重新登录获取最新状态
                    data = self.login()
                    # 检查是否需要播种
                    if data['config']['grew'] == '-1':
                        plant_status = self.plant()
                        if plant_status == -1:
                            log.log(f"={self.user_name}=, 播种失败，没有种子，尝试购买种子...")
                            # 购买种子
                            if self.buy_seeds():
                                self.plant()
                        elif plant_status == 1:
                            log.log(f"={self.user_name}=, 播种成功🌾🌾🌾")
                        else:
                            log.log(f"={self.user_name}=, 播种失败")
                    return True
            return False
        except Exception as e:
            log.log(f"={self.user_name}=, ❌检查玉米成熟度异常：{e}")
            return False

    def __user_info(self) -> Optional[Dict[str, str]]:
        """
        获取用户的信息
        :return: 
        """
        try:
            payload = {
                "ac": "login",
                "r": self._rand(),
                "scookie": self.cookie
            }
            u_response = self._post(
                url=API_ENDPOINTS["login"],
                data=payload
            )
            if u_response.get("key") == ERROR_CODES["SUCCESS"] and u_response.get("loginStatus") == "100":
                return {
                    "user": u_response["config"]["name"],
                    "uid": u_response["config"]["uid"],
                    "device_id": u_response["config"]["deviceid"],
                    "seed": u_response["config"]["seed"]
                }
            else:
                print("好游快爆-获取用户信息出现错误：{}".format(u_response))
        except Exception as e:
            print("好游快爆-获取用户信息出现错误：{}".format(e))

    def login(self) -> Dict:
        """
        登录
        :return: 
        """
        try:
            payload = {
                "ac": "login",
                "r": self._rand(),
                "scookie": self.cookie,
                "device": self.device
            }
            l_response = self._post(url=API_ENDPOINTS["login"], data=payload)
            return l_response
        except Exception as e:
            log.log("好游快爆-登录出现错误：{}".format(e))

    # 浇水
    def watering(self) -> Tuple[int, int]:
        """
        浇水
        :return: 
        """
        try:
            payload = {
                "ac": "Sign",
                "verison": "1.5.7.005",
                "OpenAutoSign": "",
                "r": self._rand(),
                "scookie": self.cookie,
                "device": self.device
            }
            w_response = self._post(
                url=API_ENDPOINTS["watering"],
                data=payload
            )
            if w_response.get("key") == ERROR_CODES["SUCCESS"]:
                log.log("={}=, 浇水成功💧💧💧".format(self.user_name))
                return 1, w_response["add_baomihua"]
            elif w_response.get("key") == ERROR_CODES["ALREADY_DONE"]:
                log.log("={}=, 今日已浇水".format(self.user_name))
                return 0, 0
            else:
                log.log(f"={self.user_name}=, ❌浇水出现错误：{w_response}")
                return -1, 0
        except Exception as e:
            log.log(f"={self.user_name}=, ❌浇水异常：{e}")
            return -1, 0

    # 收获
    def harvest(self) -> None:
        """
        收获
        :return: 
        """
        try:
            payload = {
                "ac": "Harvest",
                "r": self._rand(),
                "scookie": self.cookie,
                "device": self.device
            }
            h_response = self._post(
                url=API_ENDPOINTS["plant"],
                data=payload
            )
            if h_response.get("key") == ERROR_CODES["SUCCESS"]:
                log.log("={}=, 收获成功🌽🌽🌽".format(self.user_name))
            elif h_response.get("key") == ERROR_CODES["NO_SEEDS"]:
                log.log(f"={self.user_name}=, {h_response['info']}")
            else:
                log.log(f"={self.user_name}=, ❌收获失败：{h_response}")
        except Exception as e:
            log.log(f"={self.user_name}=, ❌收获异常：{e}")

    # 播种
    def plant(self) -> int:
        """
        播种
        :return: 
        """
        try:
            payload = {
                "ac": "Plant",
                "corn_id": "1",
                "r": self._rand(),
                "scookie": self.cookie,
                "device": self.device
            }
            p_response = self._post(
                url=API_ENDPOINTS["plant"],
                data=payload
            )
            if p_response.get("key") == ERROR_CODES["SUCCESS"]:
                log.log("={}=, 播种成功🌾🌾🌾".format(self.user_name))
                return 1
            else:
                if self.seed == 0:
                    log.log("={}=, 种子已用完".format(self.user_name))
                    return -1
                else:
                    log.log(f"={self.user_name}=, ❌播种失败：{p_response}")
                    return 0
        except Exception as e:
            log.log(f"={self.user_name}=, ❌播种异常：{e}")

    # 获取种子商品
    def get_goods(self) -> Optional[str]:
        """
        获取种子商品
        :return: 
        """
        try:
            html = self._get_text(
                url=API_ENDPOINTS["get_goods"]
            )
            soup = BeautifulSoup(html, "html.parser")
            link_element = soup.find('a', class_='corn1SeedBtn2')
            if link_element:
                href = link_element['href']
                html2 = self._get_text(
                    url=href
                )
                soup2 = BeautifulSoup(html2, "html.parser")
                # <script type='text/javascript'>window.location='https://shop.3839.com/?id=8220';</script>
                script_element = soup2.find('script', type='text/javascript')
                if script_element and script_element.string:
                    id_match = re.search(r'id=(\d+)', script_element.string)
                    if id_match:
                        id = id_match.group(1)
                        return id
                    log.log("❌未找到种子商品pid")
            else:
                log.log("❌未检索到种子商品的链接")
        except Exception as e:
            log.log("好游快爆-获取商品id出现错误：{}".format(e))

    def checkOrder(self, id):
        """ 验证订单 """
        try:
            payload = {
                'id': id,
                'smdeviceid': "BiF6S9YYiuHxjr8schCE08Xnm3HULzxag2XoCKERi/JrQjjguf2JoXTiuQSAZ220WC11SZF/izpv55ghVZtwn+w==",
                'version': "1.5.7.906",
                'r': self._rand(),
                'client': "1",
                'scookie': self.cookie,
                'device': self.device
            }
            response = self._post(
                url=API_ENDPOINTS["checkOrder"],
                data=payload
            )
            if response.get("code") != 200:
                return False
            return True
        except Exception as e:
            log.log("好游快爆-验证订单出现错误：{}".format(e))
            return False

    # 购买种子
    def buy_seeds(self) -> bool:
        """
        购买种子
        :return:
        """
        # 获取种子商品id
        goods_id = self.get_goods()
        if not goods_id:
            log.log(f"={self.user_name}=, ❌获取商品信息失败，无法购买种子")
            return False
        if not self.checkOrder(goods_id):
            log.log(f"={self.user_name}=, ⚠️订单校验未通过，无法购买种子！")
            return False
        payload = {
            "id": goods_id,
            "smdeviceid": "BGqqKPzBFBOmh5XVCbHmtfwN36lNBM7OPXnLpmlz%2F8%2BfXP2dNAnMG8vZjG5lMM%2FRW4%2FLE1P2UT9TJlCfx8yOvOg%3D%3D",
            "version": "1.5.7.807",
            "r": self._rand(),
            "client": 1,
            "scookie": self.cookie,
        }
        response = self._post(
            url=API_ENDPOINTS["buy_seeds"],
            data=payload
        )
        # 统一处理 key（支持字符串和整数两种格式）
        response_key = response.get("key")
        if str(response_key) == "200":
            log.log(f"={self.user_name}=, 购买种子成功")
            return True
        else:
            log.log(f"={self.user_name}=, ❌购买种子失败：{response}")
            return False

    def get_manors_task_info(self) -> None:
        """
        获取庄园任务信息（今日必做&更多庄园必做）
        :return: 
        """
        recommend_task_list = self.get_task_info(".taskDailyUl > li")
        more_manors_task_list = self.get_task_info(".taskYcxUl > li")
        task_list = recommend_task_list + more_manors_task_list
        for task_item in task_list:
            task_type = task_item.attrs.get("data-mode")
            if task_type not in ["1", "9", "15"]:
                continue
            tasks_infos = task_item.select_one("dl")
            onclick_value = tasks_infos.get("onclick")
            if not onclick_value:
                continue
            match = re.search(r"ShowLue\((\d+),", onclick_value)
            if not match:
                continue
            task_id = match.group(1)
            title_param = tasks_infos.select_one("dt").get_text()
            reward_param = tasks_infos.select_one("dd").get_text()
            if task_type == "1":
                self.share_task_list.append(
                    {
                        "bmh_task_id": task_id,
                        "bmh_task_title": title_param,
                        "reward_num": re.search(r"可得+(.+)", reward_param).group(1)
                    }
                )
            elif task_type == "15":
                self.small_game_task_list.append(
                    {
                        "bmh_task_id": task_id,
                        "bmh_task_title": title_param,
                        "reward_num": re.search(r"可得+(.+)", reward_param).group(1)
                    }
                )
            elif task_type == "9":
                self.appointment_game_task_list.append(
                    {
                        "bmh_task_id": task_id,
                        "bmh_task_title": title_param,
                        "reward_num": re.search(r"可得+(.+)", reward_param).group(1)
                    }
                )

    def get_task_info(self, selector):
        """ 获取任务信息 """
        try:
            html = self._get_text("https://huodong3.3839.com/n/hykb/cornfarm/index.php?imm=0")
            soup = BeautifulSoup(html, 'html.parser')
            task_list = soup.select(selector)
            return task_list
        except Exception as e:
            log.log(f"获取任务信息失败：{e}")

    def get_moreManorToDo_task_ids(self) -> None:
        """
        获取更多庄园必做任务id
        :return: 
        """
        html = self._get_text("https://huodong3.3839.com/n/hykb/cornfarm/index.php?imm=0")
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

    def appointment_game_task(self, recommend_task: Dict[str, str]) -> None:
        """
        预约游戏任务
        :param recommend_task: 
        :return: 
        """
        try:
            payload = {
                'ac': "DailyGameDetail",
                'id': recommend_task['bmh_task_id'],
                'r': self._rand(),
                'scookie': self.cookie,
                'device': self.device
            }
            daily_game_detail_response = self._post(
                url=API_ENDPOINTS["daily_task"],
                data=payload
            )
            if daily_game_detail_response.get("key") == ERROR_CODES["SUCCESS"]:
                log.log(f"={self.user_name}=, 预约游戏任务成功，任务名称：{recommend_task['bmh_task_title']}")
        except Exception as e:
            log.log(f"={self.user_name}=, 预约游戏任务调度任务异常：", e)

    def receive_yuyue_game_rewards(self, recommend_task: Dict[str, str]) -> None:
        """
        领取预约游戏任务奖励
        :param recommend_task: 
        :return: 
        """
        payload = {
            'ac': "DailyYuyueLing",
            'id': recommend_task['bmh_task_id'],
            'smdeviceid': "BIb2%2B05P0FzEEGiSf%2Fg59Gok28Sb6y1tyhmR8RlC2X0FUtOGCbu3ONvgIEoA2hae0BrOCLXtqoWe1TgeVHU0L7A%3D%3D",
            'verison': "1.5.7.905",
            'r': self._rand(),
            'scookie': self.cookie,
            'device': self.device
        }
        try:
            daily_yuyue_ling_response = self._post(
                url=API_ENDPOINTS["daily_task"],
                data=payload
            )
            if daily_yuyue_ling_response.get("key") == ERROR_CODES["SUCCESS"]:
                log.log(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- 可以领奖了🎉🎉🎉")
            elif daily_yuyue_ling_response.get("key") == ERROR_CODES["CORN_MATURITY_100"]:
                log.log(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- 玉米成熟度100%，正在处理...")
                # 检查并处理玉米成熟度
                if self.check_and_handle_corn_maturity():
                    # 重新尝试领取奖励
                    daily_yuyue_ling_response = self._post(
                        url=API_ENDPOINTS["daily_task"],
                        data=payload
                    )
                    if daily_yuyue_ling_response.get("key") == ERROR_CODES["SUCCESS"]:
                        log.log(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- ✅领取任务奖励成功！")
                    else:
                        log.log(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- 处理后仍无法领取奖励：{daily_yuyue_ling_response}")
            else:
                log.log(
                    f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- {daily_yuyue_ling_response.get('info', '奖励领取失败❌')}")
        except Exception as e:
            log.log(f"={self.user_name}=, 领取预约游戏任务奖励异常：", e)

    def do_tasks_by_share(self, recommend_task: Dict[str, str]) -> bool:
        """
        分享类型任务
        :param recommend_task: 
        :return: 
        """
        try:
            payload1 = {
                'ac': "DailyShare",
                'id': recommend_task['bmh_task_id'],
                'onlyc': "0",
                'r': self._rand(),
                'scookie': self.cookie,
                'device': self.device
            }
            daily_share_response = self._post(
                url=API_ENDPOINTS["daily_task"],
                data=payload1
            )
            if daily_share_response.get("key") != ERROR_CODES["TASK_READY"]:
                return False
            # 回调任务
            payload2 = {
                'ac': "DailyShareCallback",
                'id': recommend_task['bmh_task_id'],
                'mode': "qq",
                'source': "ds",
                'r': self._rand(),
                'scookie': self.cookie,
                'device': self.device
            }
            daily_share_callback_response = self._post(
                url=API_ENDPOINTS["daily_task"],
                data=payload2
            )
            if daily_share_callback_response.get("key") == ERROR_CODES["SUCCESS"] and daily_share_callback_response.get(
                    "info") == "可以领奖":
                log.log(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- 可以领奖了🎉🎉🎉")
                return True
            elif daily_share_callback_response.get("key") == ERROR_CODES["TASK_READY"]:
                log.log(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- 已经领过奖励了")
                return False
            else:
                log.log(
                    f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- \n{daily_share_callback_response}\n不可以领奖")
                return False
        except Exception as e:
            log.log(f"={self.user_name}=, 调度任务异常：", e)

    def do_small_game_task(self, recommend_task: Dict[str, str]) -> bool:
        """
        免安装、即点即玩的小游戏任务
        :param recommend_task: 
        :return: 
        """
        try:
            payload = {
                'ac': "DailySmallGame",
                'id': recommend_task['bmh_task_id'],
                'r': self._rand(),
                'scookie': self.cookie,
                'device': self.device
            }
            daily_small_game_response = self._post(
                url=API_ENDPOINTS["daily_task"],
                data=payload
            )
            if daily_small_game_response.get("key") == ERROR_CODES["SUCCESS"]:
                log.log(f"={self.user_name}=, 小游戏任务🎮🎮🎮-{recommend_task['bmh_task_title']}- 可以领奖了🎉🎉🎉")
                return True
            else:
                log.log(
                    f"={self.user_name}=, 小游戏任务🎮🎮🎮-{recommend_task['bmh_task_title']}- {daily_small_game_response.get('info', '❌游玩小游戏任务失败')}")
                return False
        except Exception as e:
            log.log(f"={self.user_name}=, 小游戏任务调度任务异常：", e)

    def receive_small_game_reward(self, recommend_task: Dict[str, str]) -> None:
        """
        领取免安装、即点即玩的小游戏任务奖励
        :param recommend_task: 
        :return: 
        """
        try:
            payload = {
                'ac': "DailySmallGameLing",
                'id': recommend_task['bmh_task_id'],
                'VersionCode': "342",
                'smdeviceid': "BIb2%2B05P0FzEEGiSf%2Fg59Gok28Sb6y1tyhmR8RlC2X0FUtOGCbu3ONvgIEoA2hae0BrOCLXtqoWe1TgeVHU0L7A%3D%3D",
                'verison': "1.5.7.507",
                'r': self._rand(),
                'scookie': self.cookie,
                'device': self.device
            }
            recevie_small_game_reward_response = self._post(
                url=API_ENDPOINTS["daily_task"],
                data=payload
            )
            if recevie_small_game_reward_response.get("key") == ERROR_CODES["SUCCESS"]:
                log.log(f"={self.user_name}=, 小游戏任务🎮🎮🎮-{recommend_task['bmh_task_title']}- ✅领取任务奖励成功！")
            elif recevie_small_game_reward_response.get("key") == ERROR_CODES["TASK_DONE"]:
                log.log(f"={self.user_name}=, 小游戏任务🎮🎮🎮-{recommend_task['bmh_task_title']}- 已经领过奖励了！")
            elif recevie_small_game_reward_response.get("key") == ERROR_CODES[
                "NEED_HARVEST"]:  # 表示成熟度已经满了，先收割再播种，再领取小游戏任务奖励
                log.log(f"={self.user_name}=, 小游戏任务🎮🎮🎮-{recommend_task['bmh_task_title']}- 玉米成熟度100%，正在处理...")
                # 检查并处理玉米成熟度
                if self.check_and_handle_corn_maturity():
                    # 重新尝试领取奖励
                    recevie_small_game_reward_response = self._post(
                        url=API_ENDPOINTS["daily_task"],
                        data=payload
                    )
                    if recevie_small_game_reward_response.get("key") == ERROR_CODES["SUCCESS"]:
                        log.log(f"={self.user_name}=, 小游戏任务🎮🎮🎮-{recommend_task['bmh_task_title']}- ✅领取任务奖励成功！")
                    else:
                        log.log(f"={self.user_name}=, 小游戏任务🎮🎮🎮-{recommend_task['bmh_task_title']}- 处理后仍无法领取奖励：{recevie_small_game_reward_response}")
            else:
                log.log(
                    f"={self.user_name}=, 小游戏任务🎮🎮🎮-{recommend_task['bmh_task_title']}- ❌领取任务奖励失败：{recevie_small_game_reward_response}")
        except Exception as e:
            log.log(f"={self.user_name}=, 小游戏任务领取奖励异常：", e)

    def receive_share_task_reward(self, recommend_task: Dict[str, str]) -> None:
        """
        领取分享类型的任务奖励
        :param recommend_task: 
        :return: 
        """
        try:
            payload = {
                'ac': "DailyShareLing",
                'id': recommend_task['bmh_task_id'],
                'smdeviceid': "BTeK4FWZx3plsETCF1uY6S1h2uEajvI1AicKa4Lqz3U7Tt5wKKDZZqVmVr7WpkcEuSQKyiDA3d64bErE%2FsaJp3Q%3D%3D",
                'verison': "1.5.7.507",
                'r': self._rand(),
                'scookie': self.cookie,
                'device': self.device
            }
            recevie_daily_reward_response = self._post(
                url=API_ENDPOINTS["daily_task"],
                data=payload
            )
            if recevie_daily_reward_response.get("key") == ERROR_CODES["SUCCESS"]:
                log.log(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- ✅领取任务奖励成功！")
            elif recevie_daily_reward_response.get("key") == ERROR_CODES["TASK_DONE"]:
                log.log(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- 今天已经领取过了！")
            elif recevie_daily_reward_response.get("key") == ERROR_CODES["CORN_MATURITY_100"]:
                log.log(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- 玉米成熟度100%，正在处理...")
                # 检查并处理玉米成熟度
                if self.check_and_handle_corn_maturity():
                    # 重新尝试领取奖励
                    recevie_daily_reward_response = self._post(
                        url=API_ENDPOINTS["daily_task"],
                        data=payload
                    )
                    if recevie_daily_reward_response.get("key") == ERROR_CODES["SUCCESS"]:
                        log.log(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- ✅领取任务奖励成功！")
                    else:
                        log.log(f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- 处理后仍无法领取奖励：{recevie_daily_reward_response}")
            else:
                log.log(
                    f"={self.user_name}=, 任务-{recommend_task['bmh_task_title']}- 领取任务奖励失败！-> {recevie_daily_reward_response.get('msg', recevie_daily_reward_response)}")
        except Exception as e:
            log.log(f"={self.user_name}=, 领取任务奖励异常：", e)

    def process_share_task(self, recommend_task: Dict[str, str]) -> None:
        """
        处理分享类的任务
        :param recommend_task: 分享类的任务信息
        :return: 
        """
        self.do_tasks_by_share(recommend_task)  # 调度任务
        self.receive_share_task_reward(recommend_task)  # 领取任务奖励 

    def process_yuyue_game_task(self, recommend_task: Dict[str, str]) -> None:
        self.appointment_game_task(recommend_task)
        self.receive_yuyue_game_rewards(recommend_task)

    def process_small_game_task(self, recommend_task: Dict[str, str]) -> None:
        """
        处理免安装、即点即玩的小游戏任务（单个任务，已废弃）
        现在使用批量处理方式 process_small_game_tasks_batch()
        :param recommend_task: 
        :return: 
        """
        self.do_small_game_task(recommend_task)
        time.sleep(TASK_DELAYS["small_game"])  # 默认 5 分钟
        self.receive_small_game_reward(recommend_task)

    def process_small_game_tasks_batch(self) -> None:
        """
        批量处理小游戏任务 - 优化版本
        先启动所有小游戏任务，然后统一等待5分钟，最后统一领取奖励
        :return: 
        """
        if not self.small_game_task_list:
            return

        log.log(f"={self.user_name}=, 开始处理 {len(self.small_game_task_list)} 个小游戏任务")

        # 启动所有小游戏任务
        for task in self.small_game_task_list:
            self.do_small_game_task(task)

        # 统一等待5分钟（而不是每个任务都等5分钟）
        log.log(f"={self.user_name}=, 小游戏任务已启动，等待6分钟后领取奖励...")
        time.sleep(TASK_DELAYS["small_game"])

        # 领取所有小游戏任务奖励
        for task in self.small_game_task_list:
            self.receive_small_game_reward(task)

    def run_task(self) -> None:
        """
        执行任务
        :return: 
        """
        self.get_manors_task_info()

        # 1. 先处理分享类型的任务（快速完成）
        for task in self.share_task_list:
            self.process_share_task(task)

        # 2. 批量处理小游戏任务（优化：统一等待6分钟）
        self.process_small_game_tasks_batch()

        # 3. 最后处理预约游戏任务
        for task in self.appointment_game_task_list:
            # for task in self.appointment_game_task_list:
            #     print(task)
            self.process_yuyue_game_task(task)

    def run(self) -> None:
        data = self.login()
        if data.get('key') == ERROR_CODES["SUCCESS"]:
            log.log("=" * 10 + f"【{self.user_name}】登录成功" + "=" * 10)
            # 优先判断成熟度是否已满
            if data['config']['csd_jdt'] == "100%":
                # 收获
                self.harvest()
                data = self.login()
            # 判断是否已播种
            if data['config']['grew'] == '-1':
                plant_status = self.plant()
                if plant_status == -1:
                    log.log("={}=, 播种失败，没有种子".format(self.user_name))
                    # 购买种子
                    self.buy_seeds()
                    self.plant()
                elif plant_status == 1:
                    ...
                else:
                    log.log("={}=, 播种失败".format(self.user_name))
            self.watering()
            log.log("=" * 10 + f"【{self.user_name}】开始执行庄园任务" + "=" * 10)
            self.run_task()
        else:
            log.log(f"={self.user_name}=, ❌登录失败：{data}")


def main():
    """主函数：顺序执行所有用户的脚本"""
    for cookie_ in Hykb_cookie:
        hykb = HaoYouKuaiBao(cookie_)
        hykb.run()
        hykb.client.close()


if __name__ == '__main__':
    main()
    send_notification_message_collection("好游快爆活动奖励领取通知 - {}".format(datetime.now().strftime("%Y/%m/%d")))
