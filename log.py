# -*- coding=UTF-8 -*-
# @Project      QL_TimingScript
# @fileName     log.py
# @desc         项目统一日志模块：打印 + 收集(供推送汇总) + 视觉分级
#               合并自原 fn_print.py(打印收集) 与 dw_log.py(视觉分级)，二者已删除
#               对外统一入口：log(...) 打印并收集；classify()/decorate() 做分级
# @EditTime     2026/09/23

# 收集全部输出，供 sendNotify 汇总推送
all_print_list = []


def log(*args, sep=' ', end='\n', **kwargs):
    """打印一行并收集到 all_print_list。

    与内置 print 签名一致，可直接作为 print 的替代；额外把成行文本
    追加进 all_print_list，供 sendNotify 汇总推送。
    """
    global all_print_list
    output = ""
    for index, arg in enumerate(args):
        if index == len(args) - 1:
            output += str(arg)
            continue
        output += str(arg) + sep
    output = output + end
    all_print_list.append(output)
    print(*args, sep=sep, end=end, **kwargs)


# ────────────────────────────────────────────────────────────
# 视觉分级：一眼区分「已领过/已完成」与「真实错误」
#   ✅成功  ⏭️已领过/已完成(幂等,正常)  ⚠️风控/条件不满足(可重试)  ❌真实错误(需排查)
# ────────────────────────────────────────────────────────────

# 幂等/已完成（正常，跳过标记）——不是错误，无需关注
SKIP_KWS = [
    "711020001", "已领取过", "已经领取", "已领取", "今日已", "今天已",
    "已经签到", "已经完成", "已水滴投资", "暂无可领", "还没有可以领取",
    "今日已领取", "已经积攒",
]
# 条件不满足/风控（可重试，警告标记）——今天不一定能做，非脚本故障
WARN_KWS = [
    "485", "请校验验证码", "水滴不够", "711070002", "请先完成", "711020005",
    "水滴不足", "未达到", "系统升级", "前方拥挤", "稍安勿躁",
    "711020004", "请刷新任务列表",  # 广告/浏览任务未真正完成(接口层做不了),非脚本bug
    "请先登录",  # 收藏接口间歇风控:同批其他登录态接口正常=凭据有效,重试/下次可好,非真错
]

MARK_OK   = "\u2705"          # ✅ 真实成功
MARK_SKIP = "\u23ed\ufe0f"    # ⏭️ 已领过/已完成（幂等）
MARK_WARN = "\u26a0\ufe0f"    # ⚠️ 风控/条件不满足（可重试）
MARK_ERR  = "\u274c"          # ❌ 真实错误（需排查）


def classify(msg: str) -> str:
    """返回 ok / skip / warn / err / info"""
    s = str(msg)
    # 成功优先：明确带成功标记
    if ("\u6210\u529f" in s) or (MARK_OK in s):   # 成功 / ✅
        # 但「成功」信封里若含幂等码仍算 skip（如 code200+data None 的"已完成"）
        if any(k in s for k in ("已领取过", "已经完成", "已经领取")):
            return "skip"
        return "ok"
    if any(k in s for k in SKIP_KWS):
        return "skip"
    if any(k in s for k in WARN_KWS):
        return "warn"
    # 明确错误信号
    if ("\u5931\u8d25" in s) or ("\u5f02\u5e38" in s) or ("\u9519\u8bef" in s) \
       or ("\u4e0d\u5408\u6cd5" in s) or (MARK_ERR in s):   # 失败/异常/错误/不合法/❌
        return "err"
    return "info"


def decorate(msg: str) -> str:
    """给消息加分级前缀标记；把误用的 ❌ 换成更准确的 ⏭️/⚠️。"""
    kind = classify(msg)
    s = str(msg)
    if kind == "skip":
        # 幂等：去掉刺眼的 ❌，换成跳过标记
        s = s.replace(MARK_ERR, "").rstrip("\u274c ")
        return f"{MARK_SKIP} [已完成] {s}"
    if kind == "warn":
        s = s.replace(MARK_ERR, "")
        return f"{MARK_WARN} [待条件] {s}"
    if kind == "err":
        # 去掉原文内嵌的 ❌，避免与前缀标记重复出现两个 ❌
        s = s.replace(MARK_ERR, "").strip()
        return f"{MARK_ERR} [执行错误] {s}"
    if kind == "ok":
        return s  # 成功保留原有 ✅✅
    return s
