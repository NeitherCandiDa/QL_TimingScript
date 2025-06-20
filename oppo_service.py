# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         oppo_service.py
# @author           Echo
# @EditTime         2025/6/20
import httpx

from fn_print import fn_print


class OppoService:
    def __init__(self, cookie):
        self.cookie = cookie
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090c33)XWEB/13639",
            "Connection": "keep-alive",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json;charset=UTF-8",
            "xweb_xhr": "1",
            "Page-Path": "pages/self-index/index",
            "Cookie": cookie,
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }
        self.client = httpx.Client(base_url="https://service-cms.oppo.com", headers=self.headers, verify=False)

    def get_activity_info(self):
        try:
            response = self.client.get(
                url="/oppo-api/signIn/v1/signInActivityInfo?method=GET&region=CN&isoLanguageCode=zh-CN&sourceRoute=3"
            )
            response.raise_for_status()
            data = response.json()
            if data["code"] == "1":
                activityId = data.get("data").get("activityId")
                taskId = data.get("data").get("taskId")
                is_sign_in = data.get("data").get("isSignIn")
                return activityId, taskId, is_sign_in
            else:
                fn_print(f"‼️获取活动信息失败: {data.get('msg')}")
                return None, None, None
        except Exception as e:
            fn_print(f"❌获取活动信息异常: {e}")
            return None, None, None

    def sign_in(self, activityId, taskId):
        try:
            response = self.client.post(
                url="/oppo-api/signIn/v1/sign",
                json={
                    "activityId": activityId,
                    "taskId": taskId,
                    "region": "CN",
                    "isoLanguageCode": "zh-CN",
                    "sourceRoute": "3"
                }
            )
            response.raise_for_status()
            data = response.json()
            if data["code"] == "1":
                fn_print(
                    f"🎉打卡成功! 连续再学习打卡{data.get('data').get('remainingSignInDays')}天可获得【{data.get('data').get('signInActivityPrizeInfo').get('couponPkgName')}】")
            else:
                fn_print(f"‼️{data.get('msg')}")
        except Exception as e:
            fn_print(f"❌打卡异常: {e}")

    def oppoService_run(self):
        activityId, taskId, is_sign_in = self.get_activity_info()
        if is_sign_in:
            fn_print("⚠️请勿重复签到！")
            return
        if not activityId and not taskId:
            fn_print("⚠️未获取到活动信息！")
            return
        self.sign_in(activityId, taskId)
