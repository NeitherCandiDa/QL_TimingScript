# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         Z-API.py
# @author           Leon
# @EditTime         2026/3/12
# const $ = new Env('Z-API中转站');
# cron: 0 0 12 * * *
from checkin_core import run_checkin

if __name__ == "__main__":
    run_checkin(
        env_name="zapi_cookies",
        base_url="https://zapi.aicc0.com",
        origin="https://zapi.aicc0.com",
        referer="https://zapi.aicc0.com/console/personal",
        notify_title="Z-API",
    )
