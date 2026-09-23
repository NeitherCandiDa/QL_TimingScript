# # -*- coding=UTF-8 -*-
# # @Project          QL_TimingScript
# # @fileName         ali_cloud_disk.py
# # @author           Echo
# # @EditTime         2025/3/7
import httpx

import log
from get_env import get_env
from 携程测试 import payload

refresh_tokens = get_env("alicloud_token", "@")


class AliYunDisk:
    def __init__(self, refresh_token):
        self.client = httpx.Client(verify=False, timeout=60)
        self.refresh_token = refresh_token
        self.user = None
        self.sign_count = None
        self.token = self.get_token(refresh_token)

    def get_token(self, refresh_token):
        response = self.client.post(
            url="https://auth.aliyundrive.com/v2/account/token",
            headers={
                "accept": "application/json, text/plain, */*",            
                "accept-language": "zh-CN,zh;q=0.9",
                "cache-control": "no-cache",            
                "content-type": "application/json;charset=UTF-8",            
                "origin": "https://www.aliyundrive.com",
                "pragma": "no-cache",            
                "referer": "https://www.aliyundrive.com/",            
                "sec-fetch-dest": "empty",            
                "sec-fetch-mode": "cors",            
                "sec-fetch-site": "same-site",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            },
            json={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
        )
        if response.status_code == 200:
            token = {}
            user_datas = response.json()
            token["access_token"] = user_datas.get("access_token", "")
            token["refresh_token"] = user_datas.get("refresh_token", "")
            token["expire_time"] = user_datas.get("expire_time", "")
            log.log(f"获取到新的access_token: {token.get('access_token')[:10]}, 新的refresh_token: {token.get('refresh_token')}, 过期时间: {token.get('expire_time')}")
            self.user = user_datas.get("user_name")
            return token.get("access_token")
        else:
            log.log("❌获取token失败！")
            raise

    def sign_in(self):
        not_sign_day_list = []
        response = self.client.post(
            url="https://aliyundrive.com/v1/activity/sign_in_list",
            json={'isReward': False},
            params={'_rx-s': 'mobile'},
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + self.token,
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            }
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code", "") == "AccessTokenInvalid":
            log.log("请检查token是否正确")
        elif data.get("code", "") is None:
            result = data.get("result", {})
            sign_in_infos_list = result.get("signInInfos", [])
            sign_in_count = result.get("signInCount", 0)

            if len(sign_in_infos_list) > 0:
                for index, sign_in_info in enumerate(sign_in_infos_list, 1):
                    status = sign_in_info.get("status", "")
                    day = sign_in_info.get("day", "")
                    is_reward = sign_in_info.get("isReward", False)
                    if status == "":
                        log.log(sign_in_info)
                        log.log("签到信息获取异常！")
                    elif status == "miss":
                        not_sign_day_list.append(day)
                    elif status == "normal":
                        reward = {}
                        # 签到但未领取奖励
                        if not is_reward:
                            reward = self.receive_reward(day)
                        else:
                            reward = sign_in_info.get("reward", {})
                        # 获取签到奖励信息
                        if reward:
                            name = reward.get("name", "")
                            description = reward.get("description", "")
                        else:
                            name = "无奖励"
                            description = ""
                        today_info = "" if day == sign_in_count else "✅"
                        log.log(f"{today_info}打卡第{day}天，获得{name}，{description}")
                        not_sign_day_list.append(day)
                log.log(f"🔥打开进度： {sign_in_count}/{len(sign_in_infos_list)}")        
            else:
                log.log("签到信息获取失败！")
        else:
            log.log(f"==账号: {self.user}==，❌签到失败！")
            log.log(response.text)

    def receive_reward(self, day):
        try:
            response = self.client.post(
                url="https://member.aliyundrive.com/v1/activity/sign_in_reward?_rx-s=mobile",
                headers={
                    'User-Agent': "AliApp(AYSD/6.9.1) com.alicloud.databox/45974708 Channel/36176927979800@rimet_android_6.9.1 language/zh-CN /Android Mobile/OnePlus PJZ110",
                    'Content-Type': "application/json",
                    'x-device-id': "6a799f2e292b4201b37a0ffa4a883ce292b7d469d06bb96caefd45f5eea4705d",
                    'referer': "https://alipan.com/",
                    'x-canary': "client=Android,app=adrive,version=v6.9.1",
                    'x-timestamp': "1749655777",
                    'x-nonce': "debac8a2-4ecf-4d7c-afab-646aa14f8d12",
                    'x-signature-v2': "35629b53d3b35de27b0f50a048313dc448f4ed0a",
                    'authorization': self.token,
                    'x-sign': "azRr1P002xAALpm2uxNYjW5BpoOL%2Fpm%2BmhvNKOvsek6d6bmlo9oqduK%2FWZfsU%2BdvV9N%2FAObZH85qvF3CyYfd%2BUuJTy6Zrpm%2Bma6Zvp",
                    'x-mini-wua': "aBARVoDftRy0p%2F7ScAui6kP7bCiB5ldHWY%2B3KG0wicrQKOAd3tuf8Zv9AKyC8oT2rC2COz3Z5RTnUqwnb3KTjn8N9DJWkexug8Zzvu%2Fqp4pFC26NZe9VeeSx7bu%2FcwxcesUJAgf5i%2FUrRMRLp7PeUBp6YaOGG%2FfbVXardG5tDotfsD7c%2F7n73KYQPjhSvnzRvVWY%3D",
                    'x-umt': "RXIBs6ZLPIewHAKXXtftHObea%2Bf2eGcP",
                    'x-sgext': "JBJmJW%2BigywDApquCDNfrSVXFVUcUQZXFFcTUAZVE0UGVxJSHFAQUxJTFEUVVhVWFVYVVhVWFVYVVhVWBlcGVgZWFUUVVhVWBlYGVwZXBlcGVwZXBlcGVgZXBlcGVgZWBlYGVgZWBlYGVgZFQEUVRRVFElFEXhVWBlYVVhVWBlYGVEEHBlYGRRZFHUUWRRZFXyVMDQZWBkYFRhVGBUYV",
                    'x-bx-version': "6.6.240404",
                    'x-host': "198.18.0.19",
                },
                json={"signInDay": str(day)}
            )
            response.raise_for_status()
            award_datas = response.json()
            if response.status_code == 200:
                award_name = award_datas.get("result").get("name")  # 奖励名称
                award_description = award_datas.get("result").get("description")  # 奖励描述
                rewardMessage = f" {award_name} - {award_description}"
                log.log(f"==账号: {self.user}==，✅领取奖励成功！{rewardMessage}")
                return {'name': award_name, 'description': award_description}
            else:
                log.log(f"==账号: {self.user}==，❌领取奖励失败！{award_datas.get("message")}")
        except Exception as error:
            log.log(f"==账号: {self.user}==，❌领取奖励异常！{error}")
        return {"name": "", "description": ""}


if __name__ == '__main__':
    for refresh_token in refresh_tokens:
        aliyun = AliYunDisk(refresh_token)
        aliyun.sign_in()



