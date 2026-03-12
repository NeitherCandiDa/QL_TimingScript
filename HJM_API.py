# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         HJM_API.py
# @author           Leon
# @EditTime         2026/3/12
from checkin_core import run_checkin

if __name__ == '__main__':
    run_checkin(
        env_name="hjm_cookies",
        base_url="https://api.gemai.cc",
        origin="https://api.gemai.cc",
        referer="https://api.gemai.cc/console/personal",
        notify_title="哈基米API",
    )