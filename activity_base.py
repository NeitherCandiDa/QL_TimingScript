# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         activity_base.py
# @author           Echo
# @EditTime         2025/6/27
import time
import json
import re
import log

ACTIVITY_CONFIG = {

    "is_luckyDraw": True,  # 是否开启抽奖（所有活动的抽奖）
    "special_conf": ['积分乐园', 'OPPO Find X9 系列新品上市', 'S15 巅峰对决', '一起啦！超级搭'],  # 特殊任务配置

    "oppo_app": {
        "APP签到": {
            "bp_url": "/bp/b371ce270f7509f0",
            "raffle_name": "APP签到",
            "is_luckyDraw": False
        },
        "积分乐园": {
            "bp_url": "/bp/b371ce270f7509f0",
            "raffle_name": "积分乐园",
            "is_luckyDraw": False
        },
    },
    "oppo_applet": {
        "一起啦！超级搭": {
            "bp_url": "/bp/4da7ede61dc045cd",
            "raffle_name": "一起啦！超级搭"
        },
        "S15 巅峰对决": {
            "bp_url": "/bp/d24e2750503fbacf",
            "raffle_name": "S15 巅峰对决"
        },
        # "新品预约": {
        #     "bp_url": "/bp/0bff5d7a0cfc6953",
        #     "raffle_name": "OPPO Find X9 系列新品上市",
        #     "is_luckyDraw": True  # 是否开启抽奖（单独控制某个活动是否抽奖）
        # },
        "签到赢好礼": {
            "bp_url": {
                "url": "https://msec.opposhop.cn/configs/web/advert/300003",
                "activity_area": "福利专区",
                "activity_name": "签到"
            },
            "raffle_name": "签到赢好礼",
            "is_luckyDraw": False
        },
        "专享福利": {
            "bp_url": {
                "url": "https://msec.opposhop.cn/configs/web/advert/300003",
                "activity_area": "福利专区",
                "activity_name": "窄渠道"
            },
            "raffle_name": "小程序专享福利",
            "is_luckyDraw": False
        },
    },
    "oppo_service": {
        "bp_url": "/oppo-api/signIn/v1/signInActivityInfo?method=GET&region=CN&isoLanguageCode=zh-CN&sourceRoute=3",
        "raffle_name": "OPPO服务小程序抽奖"
    }
}


class BaseActivity:
    def __init__(self, cookie, client, config):
        self.client = client
        self.config = config
        self.activity_id = None
        self.raffle_id = None
        self.jimuld_id = None
        self.sign_in_activity_id = None
        self.reservation_activity_id = None
        self.user_name = None
        self.level = None  # 默认没有等级，子类可以设置

    def get_activity_url(self, url, k, v):
        try:
            response = self.client.get(url=url)
            response.raise_for_status()
            data = response.json()
            if data.get("code") != 200:
                log.log(f"获取活动信息失败！{data.get('message')}")
                return None
            datas = data.get("data")
            for d in datas:
                if k in d.get("title"):
                    for detail in d.get("details"):
                        if v in detail.get("title"):
                            return detail.get("link")
            return None
        except Exception as e:
            log.log(f"获取活动信息失败！{e}")
            return None

    def get_activity_info(self):
        """通用活动ID提取逻辑，特殊情况子类重写"""
        bp_url = self.config['bp_url']
        # 判断是否需要先动态获取url
        if isinstance(bp_url, dict):
            url = self.get_activity_url(bp_url['url'], bp_url['activity_area'], bp_url['activity_name'])
            if not url:
                log.log("任务配置存在问题，未获取到活动入口url，跳过该任务")
                return
        else:
            url = bp_url
        try:
            response = self.client.get(url)
            response.raise_for_status()
            html = response.text
            # 特殊任务处理
            # 需要动态解析 creditsAddActionId/creditsDeductActionId
            if self.config.get('raffle_name') in ACTIVITY_CONFIG.get("special_conf"):
                app_pattern = r'window\.__APP__\s*=\s*({.*?});'
                app_match = re.search(app_pattern, html, re.DOTALL)
                if app_match:
                    app_json = json.loads(app_match.group(1))
                    # 动态注入到 config['draw_extra_params']
                    if 'draw_extra_params' not in self.config:
                        self.config['draw_extra_params'] = {}
                    self.config['draw_extra_params']['business'] = app_json.get('business')
                    self.config['draw_extra_params']['creditsAddActionId'] = app_json.get('scoreId', {}).get(
                        'creditsAddActionId')
                    self.config['draw_extra_params']['creditsDeductActionId'] = app_json.get('scoreId', {}).get(
                        'creditsDeductActionId')

            pattern = r'window\.__DSL__\s*=\s*({.*?});'
            match = re.search(pattern, html, re.DOTALL)
            if not match:
                log.log(f"未找到{self.config['raffle_name']}活动的DSL数据， 请检查活动是否结束!")
                return
            dsl_json = json.loads(match.group(1))
            task_cmps = dsl_json.get("cmps", [])
            task_field = next((cmp for cmp in task_cmps if "Task" in cmp), None)
            raffle_field = next((cmp for cmp in task_cmps if "Raffle" in cmp), None)
            sign_in_fields = [cmp for cmp in task_cmps if "SignIn" in cmp]
            sign_in_field = self._get_sign_in_field(sign_in_fields)
            reservation_field = next((cmp for cmp in task_cmps if "Appointment" in cmp), None)

            # 获取各种 ID
            self._extract_activity_ids(dsl_json, task_field, raffle_field, sign_in_field, reservation_field)
        except Exception as e:
            log.log(f"获取{self.config['raffle_name']}活动ID时出错: {e}")

    def _extract_activity_ids(self, dsl_json, task_field, raffle_field, sign_in_field, reservation_field):
        """
        提取各种活动ID
        """
        if task_field:
            try:
                self.activity_id = dsl_json['byId'][task_field]['attr']['taskActivityInfo']['activityId']
            except KeyError:
                log.log("⚠️任务ID解析失败")
        if raffle_field:
            try:
                self.raffle_id = dsl_json['byId'][raffle_field]['attr']['activityInformation']['raffleId']
            except KeyError:
                log.log("⚠️抽奖ID解析失败")
        if sign_in_field:
            try:
                self.sign_in_activity_id = dsl_json['byId'][sign_in_field]['attr']['activityInfo']['activityId']
            except KeyError:
                log.log("⚠️签到ID解析失败")
        if reservation_field:
            try:
                self.reservation_activity_id = \
                    dsl_json['byId'][reservation_field]['attr']['reserveGoodsAppointment'][
                        'goodsReserveActivityInfo'][
                        'activityId']
            except KeyError:
                log.log("⚠️预约ID解析失败")
        self.jimuld_id = dsl_json['activityId']

    def _get_sign_in_field(self, sign_in_fields):
        """
        获取签到字段，子类可以重写此方法来实现自定义逻辑
        """
        if len(sign_in_fields) == 1:
            return sign_in_fields[0]
        elif len(sign_in_fields) == 0:
            return None
        elif len(sign_in_fields) == 3 and self.level:
            # 有等级信息时，根据等级选择对应的签到字段
            if self.level == "普卡":
                return sign_in_fields[0]
            elif self.level == "银卡会员":
                return sign_in_fields[1]
            elif self.level == "金钻会员":
                return sign_in_fields[2]
            else:
                log.log("⚠️未找到用户的会员等级, 无法执行签到")
                return None
        else:
            # 默认选择第一个
            return sign_in_fields[0] if sign_in_fields else None

    def get_task_list(self):
        """获取任务列表"""
        if not self.activity_id:
            log.log("⚠️未获取到活动ID，无法获取任务列表")
            return []
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/task/queryTaskList?activityId={self.activity_id}&source=c"
            )
            response.raise_for_status()
            data = response.json()
            task_list_info = data.get('data', {}).get('taskDTOList', [])
            return task_list_info
        except Exception as e:
            log.log(f"获取任务列表时出错: {e}")
            return []

    def sign_in(self):
        """签到"""
        if not self.sign_in_activity_id:
            return
        try:
            paylaod = {
                "activityId": self.sign_in_activity_id
            }
            if self.config.get('draw_extra_params'):
                paylaod['business'] = self.config.get("draw_extra_params").get('business')
                paylaod['creditsAddActionId'] = self.config.get("draw_extra_params").get('creditsAddActionId')
            response = self.client.post(
                url="/api/cn/oapi/marketing/cumulativeSignIn/signIn",
                json=paylaod
            )
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 200:
                log.log(f"✅签到成功！获得积分： {data.get('data').get('awardValue')}")
            else:
                log.log(f"❌签到失败！{data.get('message')}")
        except Exception as e:
            log.log(f"签到时出错: {e}")

    def get_sign_in_detail(self):
        """ 获取签到天数和累计签到奖励 """
        if not self.sign_in_activity_id:
            return None, None
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/cumulativeSignIn/getSignInDetail?activityId={self.sign_in_activity_id}"
            )
            response.raise_for_status()
            data = response.json()
            accumulated_sign_in_reward_map = {}
            sign_in_day_num = data.get('data').get('signInDayNum')
            if data.get('code') == 200 and data.get('data').get('cumulativeAwards'):
                cumulative_awards = data.get('data').get('cumulativeAwards')
                for award in cumulative_awards:
                    accumulated_sign_in_reward_map[award.get('awardId')] = award.get('signDayNum')
            return sign_in_day_num, accumulated_sign_in_reward_map
        except Exception as e:
            log.log(f"获取签到天数及签到奖励时出错: {e}")
            return None

    def receive_sign_in_award(self, sign_in_activity_id, award_id, sign_in_reward_map):
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
                log.log(f"累计签到{days}天的奖励领取成功！获得： {award_value}")
        except Exception as e:
            log.log(f"领取累计签到奖励时出错: {e}")

    def handle_sign_in_award(self):
        """ 处理累计签到奖励 """
        sign_in_day_num, accumulated_sign_in_reward_map = self.get_sign_in_detail()
        if sign_in_day_num is None:
            return
        if sign_in_day_num not in accumulated_sign_in_reward_map.values():
            return
        award_id = [k for k, v in accumulated_sign_in_reward_map.items() if v == sign_in_day_num][0]
        self.receive_sign_in_award(
            self.sign_in_activity_id, award_id, accumulated_sign_in_reward_map
        )

    def handle_task(self):
        """处理任务"""
        task_list = self.get_task_list()
        for task in task_list:
            task_name = task.get('taskName')
            task_id = task.get('taskId')
            activity_id = task.get('activityId')
            task_type = task.get('taskType')
            if task_type in [6, 14, 15, 17]:  # 黑卡任务和学生认证
                continue
            if task_type in [0, 1, 2, 4]:
                self.complete_task(task_name, task_id, activity_id, task_type)
                time.sleep(2)
                self.receive_reward(task_name, task_id, activity_id)
            else:
                log.log(f"【{task_name}】任务暂不支持，‘{task_type}’类型任务不支持‼️")

    def complete_task(self, task_name, task_id, activity_id, task_type):
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/taskReport/signInOrShareTask?taskId={task_id}&activityId={activity_id}&taskType={task_type}"
            )
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 200:
                log.log(f"✅小程序任务【{task_name}】完成！")
            else:
                log.log(f"❌小程序任务【{task_name}】失败！-> {data.get('message')}")
        except Exception as e:
            log.log(f"完成小程序任务时出错: {e}")

    def receive_reward(self, task_name, task_id, activity_id):
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/task/receiveAward?taskId={task_id}&activityId={activity_id}"
            )
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 200:
                log.log(f"✅小程序任务【{task_name}】奖励领取成功！")
            else:
                log.log(f"❌小程序任务【{task_name}】-> {data.get('message')}")
        except Exception as e:
            log.log(f"领取小程序任务奖励时出错: {e}")

    def get_draw_count(self):
        """获取抽奖次数"""
        if not self.raffle_id:
            log.log("⚠️未获取到抽奖ID，无法获取抽奖次数")
            return 0
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/raffle/queryRaffleCount?activityId={self.raffle_id}"
            )
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 200:
                log.log(f"剩余抽奖次数：{data.get('data').get('count')}")
                return data.get('data').get('count')
            else:
                log.log(f"获取剩余抽奖次数失败！-> {data.get('message')}")
                return 0
        except Exception as e:
            log.log(f"获取抽奖次数时出错: {e}")
            return 0

    def draw_lottery(self, **kwargs):
        """抽奖"""
        from urllib.parse import quote, urlencode
        params = {
            "activityId": self.raffle_id,
            "jimuId": self.jimuld_id,
            "jimuName": quote(self.config.get("raffle_name"))
        }
        if kwargs:
            params.update(kwargs)
        try:
            response = self.client.get(
                url=f"/api/cn/oapi/marketing/raffle/clickRaffle?{urlencode(params)}"
            )
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 200:
                log.log(f"\t\t>>> 抽奖结果: {data.get('data').get('raffleWinnerVO').get('exhibitAwardName')}")
            else:
                log.log(f"\t\t>>> 抽奖失败！-> {data.get('message')}")
        except Exception as e:
            log.log(f"\t\t>>> 抽奖时出错: {e}")

    def is_login(self):
        """检测Cookie是否有效，通用实现"""
        try:
            response = self.client.get(url="/api/cn/oapi/marketing/task/isLogin")
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 403:
                log.log("Cookie已过期或无效，请重新获取")
                return False
        except Exception as e:
            log.log(f"检测Cookie时出错: {e}")
            return False
        return True

    def get_user_info(self):
        """获取用户信息，通用实现"""
        try:
            response = self.client.get(
                url="/api/cn/oapi/users/web/member/check?unpaid=0"
            )
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 200:
                self.user_name = data['data']['name']
        except Exception as e:
            log.log(f"获取用户信息时出错: {e}")

    def get_user_total_points(self):
        """ 获取用户总积分 """
        try:
            response = self.client.get(
                url=f"https://msec.opposhop.cn/users/web/member/infoDetail"
            )
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 200 and data.get('data'):
                log.log(
                    f"**OPPO会员: {data.get('data').get('userName')}**，当前总积分: {data.get('data').get('userCredit')}")
        except Exception as e:
            log.log(f"获取用户总积分时出错: {e}")

    def should_draw_lottery(self):
        """判断是否应该进行抽奖"""
        # 单独活动配置优先级高于全局配置
        if 'is_luckyDraw' in self.config:
            return self.config['is_luckyDraw']
        # 如果单独活动没有配置，则使用全局配置
        return ACTIVITY_CONFIG.get('is_luckyDraw', True)

    def reservation_new_products(self, activityId):
        """ 预约新商品 """
        if not self.reservation_activity_id:
            return
        try:
            response = self.client.post(
                url=f"/api/cn/oapi/marketing/reserve/materials/reserveMaterials",
                json={
                    "activityId": activityId,
                    "reserveType": 2,
                    "reserveChannel": "积木页",
                    "reserveComp": "预约组件",
                    "reserveMaterialScene": 2
                }
            )
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 200:
                log.log(data.get('data').get('actions')[0].get('actionInfo'))
        except Exception as e:
            log.log(f"预约新商品时出错: {e}")

    def run(self):
        # 首先检查登录状态和获取用户信息
        if not self.is_login():
            return
        self.get_user_info()
        if self.user_name:
            log.log(f"🔹 当前账户：{self.user_name}")
        self.get_activity_info()
        self.sign_in()
        self.reservation_new_products(self.reservation_activity_id)
        if hasattr(self, 'handle_sign_in_award'):
            self.handle_sign_in_award()
        self.handle_task()

        # 根据配置决定是否进行抽奖
        if self.should_draw_lottery():
            draw_count = self.get_draw_count()
            if draw_count > 0:
                log.log(f"🎲 开始抽奖，共{draw_count}次")
                for i in range(draw_count):
                    log.log(f"第{i + 1}次抽奖：", end="")
                    if self.config.get('draw_extra_params'):
                        self.draw_lottery(**self.config['draw_extra_params'])
                    else:
                        self.draw_lottery()
                    time.sleep(1.5)
            else:
                log.log("🎲 当前没有可用的抽奖次数")
        else:
            log.log("🚫 抽奖功能已关闭，跳过抽奖")

        # 显示账户总积分
        self.get_user_total_points()
