# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         AiPm.py
# @author           Leon
# @EditTime         2026/3/12
# const $ = new Env('AIPM中转站');
# cron: 0 0 12 * * *
from checkin_core import run_checkin

if __name__ == "__main__":
    run_checkin(
        env_name="aipm_cookies",
        base_url="https://emtf.aipm9527.online",
        origin="https://emtf.aipm9527.online",
        referer="https://emtf.aipm9527.online/console/personal",
        notify_title="AIPM",
    )
