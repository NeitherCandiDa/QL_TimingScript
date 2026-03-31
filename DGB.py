# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         AiPm.py
# @author           Leon
# @EditTime         2026/3/12
# const $ = new Env('DGB中转站');
# cron: 0 0 12 * * *
from checkin_core import run_checkin

if __name__ == "__main__":
    run_checkin(
        env_name="dgb_cookies",
        base_url="https://freeapi.dgbmc.top",
        origin="https://freeapi.dgbmc.top",
        referer="https://freeapi.dgbmc.top/console/personal",
        notify_title="DGB",
    )
