"""
好游快爆配置文件
集中管理所有常量、配置和基础设置
"""

# API 配置
API_CONFIG = {
    "base_url": "https://huodong3.3839.com",
    "shop_url": "https://shop.3839.com",
    "headers": {
        'User-Agent': "Mozilla/5.0 (Linux; Android 15; PJZ110 Build/AP3A.240617.008; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/134.0.6998.135 Mobile Safari/537.36Androidkb/1.5.7.905(android;PJZ110;15;1440x2952;WiFi);@4399_sykb_android_activity@",
        'Accept': "application/json, text/javascript, */*; q=0.01",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'sec-ch-ua-platform': "\"Android\"",
        'X-Requested-With': "XMLHttpRequest",
        'sec-ch-ua': "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Android WebView\";v=\"134\"",
        'sec-ch-ua-mobile': "?1",
        'Origin': "https://huodong3.3839.com",
        'Sec-Fetch-Site': "same-origin",
        'Sec-Fetch-Mode': "cors",
        'Sec-Fetch-Dest': "empty",
        'Referer': "https://huodong3.3839.com/n/hykb/cornfarm/index.php?imm=0",
        'Accept-Language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    }
}

# API 接口路径
API_ENDPOINTS = {
    "login": "https://huodong3.3839.com/n/hykb/cornfarm/ajax.php",
    "watering": "https://huodong3.3839.com/n/hykb/cornfarm/ajax_sign.php",
    "plant": "https://huodong3.3839.com/n/hykb/cornfarm/ajax_plant.php",
    "daily_task": "https://huodong3.3839.com/n/hykb/cornfarm/ajax_daily.php",
    "get_goods": "https://huodong3.3839.com/n/hykb/cornfarm/index.php?imm=0",
    "buy_seeds": "https://shop.3839.com/index.php?c=OrderVirtual&a=createOrder"
}

# 任务类型配置
TASK_TYPES = {
    "SHARE": "分享任务",
    "SHARE_INFO": "分享资讯任务",
    "SMALL_GAME": "小游戏任务",
    "APPOINTMENT": "预约游戏任务",
    "RECOMMEND_DAILY": "每日必做推荐任务"
}

# 错误码映射
ERROR_CODES = {
    "SUCCESS": "ok",
    "ALREADY_DONE": "1001",
    "PLANTING FAILURE": 501,
    "NO_SEEDS": "503",
    "TASK_DONE": "2001",
    "TASK_READY": "2002",
    "CORN_MATURITY_100": "2004",  # 玉米成熟度已经达到100%
    "NEED_HARVEST": "2005"
}

# 随机数参数配置
RANDOM_CONFIG = {
    "min_length": 18,
    "max_length": 18,
    "prefix": "0."
}

# 请求重试配置
RETRY_CONFIG = {
    "max_attempts": 3,
    "delay": 1,
    "backoff": 2
}

# 任务执行间隔
TASK_DELAYS = {
    "small_game": 360,  # 6分钟
    "request_delay": 1  # 1秒
}

# 响应消息模板
RESPONSE_MESSAGES = {
    "login_success": "【{}】登录成功",
    "watering_success": "💧💧💧浇水成功",
    "watering_already": "今日已浇水",
    "harvest_success": "🌽🌽🌽收获成功",
    "plant_success": "🌾🌾🌾播种成功",
    "no_seeds": "种子已用完",
    "buy_seeds_success": "购买种子成功，还剩下🍿爆米花{}个",
    "task_ready": "任务-{}-可以领奖了🎉🎉🎉",
    "task_done": "任务-{}-已经领过奖励了🎁",
    "task_failed": "任务-{}-❌失败"
}
