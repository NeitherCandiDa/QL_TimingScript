# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         浓五的酒馆.py
# @author           Echo
# @EditTime         2025/3/15
# const $ = new Env('浓五的酒馆');
"""
开启抓包进入‘浓五的酒馆’小程序，抓取authorization，不要带Bearer
变量格式： nwjg_token，多个账号用@隔开
"""
import httpx

from fn_print import fn_print
from get_env import get_env

nwjg_tokens = get_env("nwjg_token", "@")


class Nwjg:
    def __init__(self, token):
        self.user = None
        self.client = httpx.Client(
            verify=False,
            timeout=60
        )
        self.token = token
        self.headers = {
            'xweb_xhr': '1',
            'content-type': 'application/json',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'accept-language': 'zh-CN,zh;q=0.9',
            'Authorization': f'Bearer {self.token}'
        }

    def sign(self):
        self.get_integral()
        try:
            response = self.client.get(
                url="https://stdcrm.dtmiller.com/scrm-promotion-service/promotion/sign/today",
                headers=self.headers,
                params={
                    "promotionId": "PI67c25977540856000aac6ac0"
                }
            )
            if response.status_code == 200:
                response_data = response.json()
                if response_data['code'] == 0:
                    fn_print(f"用户【{self.user}】 -  签到成功！获得{response_data['data']['prize']['goodsName']} - "
                             f"签到天数： {response_data['data']['signDays']}")
                else:
                    fn_print(f"用户【{self.user}】 -  签到失败: {response_data['msg']}")
            else:
                fn_print(f"用户【{self.user}】 -  签到失败: {response.text}")
        except Exception as e:
            fn_print(f"用户【{self.user}】 -  签到发生异常: {e}")

    def get_integral(self):
        try:
            response = self.client.get(
                url="https://stdcrm.dtmiller.com/scrm-promotion-service/mini/wly/user/info",
                headers=self.headers
            ).json()
            # print(json.dumps(response, indent=4, ensure_ascii=False))
            if response['code'] == 0:
                self.user = response['data']['member']['mobile']
                fn_print(f"用户【{self.user}】 - 当前积分{response['data']['member']['points']}")
            else:
                fn_print(f"查询积分失败: {response['msg']}")
        except Exception as e:
            fn_print(f"查询积分发生异常: {e}")


if __name__ == '__main__':
    for token in nwjg_tokens:
        nwjg = Nwjg(token)
        nwjg.sign()
