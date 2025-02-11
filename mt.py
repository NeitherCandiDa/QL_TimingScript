# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         mt.py
# @author           Echo
# @EditTime         2025/1/13
import asyncio
import random
import time
from datetime import datetime
from typing import Text, Union
import httpx
from fn_print import fn_print
from get_env import get_env
from sendNotify import send_notification_message_collection

# 获取环境变量或默认值
mt_tokens = get_env("mt_token", "@")
is_expansion = False    # 是否膨胀
invitation_code = None  # 邀请码

# sjpz = os.getenv('sjpz') if env.is_node() else env.getdata('sjpz') or 'false'
# status = env.getval("fhxzstatus") or "1"
# status = status if int(status) > 1 else ""  # 账号扩展字符
# meituanyq = os.getenv('meituanyq') if env.is_node() else env.getdata('meituanyq') or ''
# all_message = ''
# current_time = int(time.time())
# mt_token = ''
# accept_tag_code = None
# query_tag_code = None
# num = random.randint(10, 99)
# slcks = ''
# user_id = None
# uuid = None
# invite_code = None


class MeiTuan:
    def __init__(self, mt_token: Text):
        """        
        :param mt_token: token
        """
        self.client = httpx.AsyncClient(verify=False)
        self.mt_token = mt_token.split("#")[0]
        self.is_expansion = is_expansion
        self.invitation_code = invitation_code
        self.randomNum = random.randint(10, 99)
        self.user_id = None
        self.uuid = self.random_string(64)

    @staticmethod
    def random_string(length):
        chars = 'abcdef0123456789'
        return "".join(random.choice(chars) for _ in range(length))

    async def get_share_card(self):
        """
        获取分享卡片信息
        :return: 
        """
        url = "https://promotion-waimai.meituan.com/invite/getsharecard?sourceId=1"
        headers = {
            "Host": "promotion-waimai.meituan.com",
            "Cookie": f"mt_c_token={self.mt_token}; thirdlogin_token={self.mt_token};token={self.mt_token};",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.3(0x1800032c) NetType/WIFI Language/zh_CN"
        }
        try:
            response = await self.client.get(
                url,
                headers=headers
            )
            if response.status_code == 200:
                response_json = response.json()
                if response_json.get("code") == 0:
                    invite_code = response_json['data']['invitationUrl'].split('inviteCode=')[1].split('&')[0]
                    fn_print(f"美团邀请链接：{invite_code}")
                    self.invitation_code = invite_code
            else:
                fn_print("获取分享卡片信息失败")
        except Exception as e:
            fn_print(f"获取分享卡片信息异常：{e}")

    async def receive_coupon(self):
        """
        领取优惠券
        :return: 
        """
        invite_code = self.invitation_code if self.invitation_code else "'NnOIp-QOs8SiYF1dcSlL5r8phPrCf6qkH7evMyjIoureqol0OXXaopfjjblE0yPgN86y4RcZwmbDNeilsjadKKx8C_xcAtb9biugMRpa1nHJplwNd25nXQxgtWHn9006X_TBXSsJXEvvpgsevw4IOO1GodOJn4IOG_sQpdLKzqo'"
        url = f"https://promotion-waimai.meituan.com/invite/fetchcoupon?version=8.0.14&ctype=wxapp&fpPlatform=13&app=13&initialLng=113387518&initialLat=22931265&inviteCode={invite_code}&isMini=1&token={self.mt_token}"
        headers = {
            "Host": "promotion-waimai.meituan.com",
            "User-Agent": "MeituanGroup/11.9.208",
            "Referer": "https://servicewechat.com/wx2c348cf579062e56/568/page"
        }
        try:
            response = await self.client.get(
                url,
                headers=headers
            )
            if response.status_code == 200:
                response_json = response.json()
                fn_print(f"\n【下午茶红包】🧧\n{response_json.get('msg')}")
            else:
                fn_print("领取优惠券失败")
        except Exception as e:
            fn_print(f"领取优惠券异常：{e}")

    async def sign_in(self):
        """
        签到赚米粒
        :return: 
        """
        url = "https://wx.waimai.meituan.com/weapp/v1/wlwc/signintask/signin"
        try:
            response = await self.client.post(
                url,
                data={
                    "wm_dtype": "iPhone 11",
                    "wm_logintoken": self.mt_token,
                    "user_id": self.user_id,
                    "uuid": self.uuid
                }
            )
            if response.status_code == 200:
                response_json = response.json()
                fn_print(f"\n【签到结果】🍩\n{response_json.get('msg')}")
            else:
                fn_print("签到失败")
        except Exception as e:
            fn_print(f"签到异常：{e}")

    async def get_user_info(self):
        """
        获取用户信息
        :return: 
        """
        url = f"https://web.meituan.com/web/user/points?token={self.mt_token}&userId={self.user_id}"
        try:
            response = await self.client.get(url)
            if response.status_code == 200:
                response_json = response.json()
                fn_print(f"用户全信息：{response_json}")
                if response_json.get("code") == 0:
                    fn_print(f"\n【当前金币🪙】:{response_json.get('data').get('count')}")
            else:
                fn_print("获取用户信息失败")
        except Exception as e:
            fn_print(f"获取用户信息异常：{e}")

    async def run(self):
        fn_print("============开始执行签到============")
        await self.get_share_card()
        await self.receive_coupon()
        await self.sign_in()
        await self.get_user_info()


async def main():
    tasks = []
    for mt_token in mt_tokens:
        meituan = MeiTuan(mt_token)
        tasks.append(meituan.run())
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())
    send_notification_message_collection(f"美团赚米粒签到通知 - {datetime.now().strftime('%Y/%m/%d')}")
