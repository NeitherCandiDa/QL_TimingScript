# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         get_env.py
# @author           Echo
# @EditTime         2024/11/26
import os
import re

from dotenv import load_dotenv, find_dotenv

from fn_print import fn_print


def get_env(env_var, separator):
    if env_var in os.environ:
        return re.split(separator, os.environ.get(env_var))
    else:
        load_dotenv(find_dotenv())
        if env_var in os.environ:
            return re.split(separator, os.environ.get(env_var))
        else:
            fn_print(f"未找到{env_var}变量.")
            return []
