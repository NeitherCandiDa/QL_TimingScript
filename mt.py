# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         mt.py
# @author           Echo
# @EditTime         2025/1/13
import random
import time
from typing import *
import httpx
import os


# 获取环境变量或默认值
sjpz = os.getenv('sjpz') if env.is_node() else env.getdata('sjpz') or 'false'
status = env.getval("fhxzstatus") or "1"
status = status if int(status) > 1 else ""  # 账号扩展字符
meituanyq = os.getenv('meituanyq') if env.is_node() else env.getdata('meituanyq') or ''
all_message = ''
current_time = int(time.time())
mt_token = ''
accept_tag_code = None
query_tag_code = None
num = random.randint(10, 99)
slcks = ''
user_id = None
uuid = None
invite_code = None



