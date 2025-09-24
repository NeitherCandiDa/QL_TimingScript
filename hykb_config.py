"""
好游快爆配置文件
集中管理所有常量、配置和基础设置
"""

# API 配置
API_CONFIG = {
    "base_url": "https://huodong3.3839.com",
    "shop_url": "https://shop.3839.com",
    "headers": {
        "Origin": "https://huodong3.i3839.com",
        "Referer": "https://huodong3.3839.com/n/hykb/cornfarm/index.php?imm=0",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
    }
}

# API 接口路径
API_ENDPOINTS = {
    "login": "/n/hykb/cornfarm/ajax.php",
    "watering": "/n/hykb/cornfarm/ajax_sign.php",
    "plant": "/n/hykb/cornfarm/ajax_plant.php",
    "daily_task": "/n/hykb/cornfarm/ajax_daily.php",
    "get_goods": "https://shop.3839.com/index.php?c=Index&a=initCard",
    "buy_seeds": "/n/hykb/bmhstore2/inc/virtual/ajaxVirtual.php"
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
    "small_game": 300,  # 5分钟
    "request_delay": 1   # 1秒
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