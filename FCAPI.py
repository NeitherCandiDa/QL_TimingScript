# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         AiPm.py
# @author           Leon
# @EditTime         2026/3/12
# const $ = new Env('发财网API中转站');
# cron: 0 0 12 * * *
from checkin_core import run_checkin

if __name__ == "__main__":
    run_checkin(
        env_name="fc_cookies",
        base_url="https://ai.facai.cloudns.org",
        origin="https://ai.facai.cloudns.org",
        referer="https://ai.facai.cloudns.org/console/personal",
        notify_title="发财网API",
    )
