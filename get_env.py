# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         get_env.py
# @author           Echo
# @EditTime         2024/11/26
import os
import re

from dotenv import load_dotenv, find_dotenv

import log


def get_env(env_var, separator):
    if env_var in os.environ:
        raw = os.environ.get(env_var)
    else:
        load_dotenv(find_dotenv())
        raw = os.environ.get(env_var) if env_var in os.environ else None
    if raw is None:
        log.log(f"未找到{env_var}变量.")
        return []
    # 面板粘贴的值常带首尾换行/空格，原样进请求头会被 httpx 判为非法头值直接抛异常。
    # 只剥每段自身的空白，不能 strip 整个串——有的脚本用换行本身做多账号分隔符。
    return [s.strip() for s in re.split(separator, raw)]