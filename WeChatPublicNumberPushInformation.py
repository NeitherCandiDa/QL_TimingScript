# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         WeChatPublicNumberPushInformation.py
# @author           Echo
# @EditTime         2024/9/14
# cron: 0 0 7 * * *
# const $ = new Env('微信公众号推送信息');
import datetime
import os
import random
import re
import time
import httpx
from typing import Text, Optional, List, Dict

import log
from sendNotify import send_notification_message_collection

"""
公众号推送模版：
📆今天是: {{today.DATA}}

👩‍❤️‍💋‍👨今天是我们恋爱的第{{ld.DATA}}天
☁️今天的天气状况: {{w.DATA}}
🌡️当前气温: {{c_temp.DATA}}℃
❄️最低气温: {{min_temp.DATA}}℃
☀️最高气温: {{max_temp.DATA}}℃
🎂距离{{u.DATA}}生日还有: {{b.DATA}}天
📝距离考研还剩: {{exa_day.DATA}}天

❤️‍爱情指数: {{l_i.DATA}}
💼工作指数: {{w_i.DATA}}
🪙财运指数: {{f_i.DATA}}
🌟星座运势: {{sign1.DATA}}{{sign2.DATA}}{{sign3.DATA}}{{sign4.DATA}}{{sign5.DATA}}

🌈今日彩虹屁: {{copy1.DATA}}{{copy2.DATA}}{{copy3.DATA}}{{copy4.DATA}}{{copy5.DATA}}
"""

"""
设置配置常量
"""
CONFIG = {
    "API_KEY": "",           # 天聚数行密钥
    "APP_ID": "",            # 微信公众号appid
    "APP_SECRET": "",        # 微信公众号appsecret
    "TEMPLATE_ID": "",       # 模板ID
    "CITY_NAME": "",         # 城市
    "AREA": "",              # 区县
    "EXAMINATION_DATE": "",  # 考研日期（xx-xx）
    "USER": "",              # 对象称呼
    "BIRTHDAY": "",          # 对象生日（xx-xx)
    "STAR_SIGN": "",         # 对象星座（xx座）
    "LOVE_DATE": ""          # 恋爱开始日期（xxxx-xx-xx）
}

# 从环境变量中获取配置，如果环境变量不存在则使用默认值
for key in CONFIG:
    CONFIG[key] = os.environ.get(key, CONFIG[key])

# 特殊处理 WECHAT_USER_IDS，因为它需要被分割
WECHAT_USER_IDS = re.split("@|&", os.environ.get("WECHAT_USER_IDS", "")) if "WECHAT_USER_IDS" in os.environ else []

# 使用全局变量
globals().update(CONFIG)


def time_diff(time1: Text, time2: Text, format) -> int:
    """
    计算两个时间差
    :param time1: 时间1
    :param time2: 时间2
    :param format: 时间格式
    :return: 时间差
    """
    import datetime
    time1 = datetime.datetime.strptime(time1, format)
    time2 = datetime.datetime.strptime(time2, format)
    if time2 > time1:
        return (time2 - time1).days
    else:
        log.log("时间1大于时间2, 请检查")


def calculate_birthday(birthday: Text) -> int:
    """
    计算生日
    :param birthday: 出生日期
    :return: 生日
    """
    from datetime import date
    today = date.today()

    # 解析生日字符串
    birthday_month, birthday_day = map(int, birthday.split('-'))

    # 计算今年的生日日期
    this_year_birthday = date(today.year, birthday_month, birthday_day)

    # 如果今年的生日已经过了，就计算明年的生日
    if this_year_birthday < today:
        next_birthday = date(today.year + 1, birthday_month, birthday_day)
    else:
        next_birthday = this_year_birthday

    # 计算天数差
    days_left = (next_birthday - today).days
    return days_left


def claculate_love_date(love_date: Text) -> int:
    """
    计算恋爱日
    :param love_date: 
    :return: 
    """
    from datetime import date, datetime

    anniversary_date = datetime.strptime(love_date, "%Y-%m-%d").date()
    today = date.today()
    days_passed = (today - anniversary_date).days
    return days_passed


def claculate_exam_countdown(exam_date: Text) -> int:
    """
    计算考试倒计时
    :param exam_date: 考试时间
    :return: 
    """
    from datetime import date, datetime
    today = date.today()
    exam_date = datetime.strptime(exam_date, "%m-%d").date()
    exam_date = exam_date.replace(year=today.year)
    # if exam_date < today:
    #     exam_date = exam_date.replace(year=today.year + 1)
    days_left = (exam_date - today).days
    return days_left


class TianApi:
    def __init__(self):
        self.api_key = API_KEY
        self.client = httpx.Client(base_url="https://apis.tianapi.com")

    def get_rainbowFart(self):
        """
        获取彩虹屁
        :return: 
        """
        response = self.client.get(
            url=f"/caihongpi/index?key={self.api_key}"
        ).json()
        if response.get("msg") == "success":
            return response["result"]["content"]

    def get_horoscope(self, star_sign: Text, date: Optional[Text] = None) -> List:
        """
        获取星座运势
        :param star_sign: 星座名（必填）
        :param date: 出生日期（可选）
        :return: 
        """
        if date is None:
            url = f"/star/index?key={self.api_key}&astro={star_sign}"
        else:
            url = f"/star/index?key={self.api_key}&astro={star_sign}&date={date}"
        response = self.client.get(
            url=url
        ).json()
        return response["result"]["list"]

    def get_weather_infos(self, city: Text) -> Dict:
        """
        获取天气
        :param city: 城市（城市天气ID、行政代码、城市名称、IP地址）
        :return: 
        """
        response = self.client.get(
            url=f"/tianqi/index?key={self.api_key}&city={city}&type=1"
        ).json()
        return response["result"]


class WeChatPushMessage:
    def __init__(self):
        self.client = httpx.Client()
        self.tian_api = TianApi()

    @staticmethod
    def get_color():
        # 获取随机颜色
        get_colors = lambda n: list(map(lambda i: "#" + "%06x" % random.randint(0, 0xFFFFFF), range(n)))
        color_list = get_colors(100)
        return random.choice(color_list)

    @staticmethod
    def split_str(str_: Text, length: int = 20):
        chunks = [str_[i:i + length] for i in range(0, len(str_), length)]
        result = {}
        for i, chunk in enumerate(chunks, 1):
            var_name = f"content_{i}"
            result[var_name] = chunk
        return result

    def __get_access_token(self) -> Text:
        appid = APP_ID
        appsecret = APP_SECRET
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={appsecret}"
        try:
            response = self.client.get(url).json()
            return response["access_token"]
        except KeyError:
            raise KeyError("获取access_token失败！检查appid和appsecret是否正确.")

    def push_message(self, user):
        # city = config.get("cityName") + config.get("area")
        week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
        time_ = time.strftime('%Y年%m月%d日 %H:%M:%S（' + week_list[datetime.date.today().isoweekday() % 7] + '）',
                              time.localtime((int(time.mktime(time.gmtime())) + 28800)))  # 获取当前时间
        birthday = calculate_birthday(BIRTHDAY)  # 计算生日
        love_date = claculate_love_date(LOVE_DATE)  # 计算恋爱日
        exam_date = claculate_exam_countdown(EXAMINATION_DATE)  # 计算考研剩余时间
        weather_info = self.tian_api.get_weather_infos(AREA)
        weather_condition = weather_info.get("weather")  # 天气状况
        max_temperature = weather_info.get("highest")  # 最高温度
        current_temperature = weather_info.get("real")  # 实时温度
        min_temperature = weather_info.get("lowest")  # 最低温度

        star_sign = STAR_SIGN  # 星座
        star_sign_info = self.tian_api.get_horoscope(star_sign)
        composite_index = star_sign_info[0]["content"]  # 综合指数
        love_index = star_sign_info[1]["content"]  # 恋爱指数
        work_index = star_sign_info[2]["content"]  # 工作指数
        fortune_index = star_sign_info[3]["content"]  # 财运指数
        health_index = star_sign_info[4]["content"]  # 健康指数
        speed_sign = star_sign_info[7]["content"]  # 速配星座

        url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={self.__get_access_token()}"
        messages = {

            "touser": user,
            "template_id": TEMPLATE_ID,
            "url": "heartSpin.html",
            "topcolor": "#FF0000",
            "data": {
                "today": {"value": time_, "color": self.get_color()},  # 当前时间
                "ld": {"value": love_date, "color": "#EC2417"},  # 恋爱日
                # "city": {"value": city, "color": self.get_color()},    # 城市
                "w": {"value": weather_condition, "color": self.get_color()},  # 天气状况
                "c_temp": {"value": current_temperature, "color": self.get_color()},  # 实时温度
                "min_temp": {"value": min_temperature, "color": self.get_color()},  # 最低温度
                "max_temp": {"value": max_temperature, "color": self.get_color()},  # 最高温度
                "u": {"value": USER, "color": self.get_color()},  # 用户
                "b": {"value": birthday, "color": self.get_color()},  # 生日
                "exa_day": {"value": exam_date, "color": self.get_color()},  # 考研剩余时间
                # "c_i": {"value": composite_index, "color": self.get_color()},    # 综合指数
                "l_i": {"value": love_index, "color": self.get_color()},  # 恋爱指数
                "w_i": {"value": work_index, "color": self.get_color()},  # 工作指数
                "f_i": {"value": fortune_index, "color": self.get_color()}  # 财运指数
                # "h_i": {"value": health_index, "color": self.get_color()},  # 健康指数
                # "s_s": {"value": speed_sign, "color": self.get_color()},  # 速配星座
            }
        }
        # tips_info = weather_info.get("tips")  # 出行建议
        # split_tips = self.split_str(tips_info)
        # tips_fields = ["tips1", "tips2", "tips3", "tips4", "tips5"]
        # for i, field in enumerate(tips_fields, 1):
        #     if f"content_{i}" in split_tips:
        #         messages["data"][field] = {"value": split_tips[f"content_{i}"], "color": self.get_color()}

        today_summarize_info = star_sign_info[8]["content"]  # 今日运势
        split_today_summarize_info = self.split_str(today_summarize_info)
        today_summarize_fields = ["sign1", "sign2", "sign3", "sign4", "sign5"]
        for i, field in enumerate(today_summarize_fields, 1):
            if f"content_{i}" in split_today_summarize_info:
                messages["data"][field] = {"value": split_today_summarize_info[f"content_{i}"],
                                           "color": self.get_color()}

        rainbow_fart_info = self.tian_api.get_rainbowFart()
        if "XXX" in rainbow_fart_info:
            rainbow_fart_info = rainbow_fart_info.replace("XXX", USER)
        split_rainbow_fart_info = self.split_str(rainbow_fart_info)
        rainbow_fart_fields = ["copy1", "copy2", "copy3", "copy4", "copy5"]
        for i, field in enumerate(rainbow_fart_fields, 1):
            if f"content_{i}" in split_rainbow_fart_info:
                messages["data"][field] = {"value": split_rainbow_fart_info[f"content_{i}"], "color": self.get_color()}
        try:
            response = self.client.post(url, json=messages).json()
            if response.get("errcode") == 0 and response.get("errmsg") == "ok":
                log.log(f"⏰向【{USER}】早安信息已成功推送啦！")
            else:
                log.log(f"❌向【{USER}】早安信息推送失败")
                log.log(f"错误信息： {response}")
        except KeyError:
            log.log("推送失败，请检查参数是否正确")
            raise KeyError("推送失败，请检查参数是否正确")


if __name__ == '__main__':
    for user in WECHAT_USER_IDS:
        wpm = WeChatPushMessage()
        wpm.push_message(user)
        del wpm
    send_notification_message_collection(f"🗨️微信公众号通知 - {datetime.datetime.now().strftime('%Y/%m/%d')}")
