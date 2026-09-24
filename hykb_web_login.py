# -*- coding=UTF-8 -*-
# @Project      QL_TimingScript
# @fileName     hykb_web_login.py
# @desc         好游快爆「网页版预约」登录态获取工具（本地运行，扫码登录一次有效期约 1 年）
#
# 用途：
#     好游快爆.py 的预约任务（mode=9）走网页版正规接口
#     POST https://www.3839.com/app/hykb_web/ajax_yuyue.php  action=orderNoPhone
#     该接口需要网页登录态（Pauth / Uauth / accesstoken / nickname 四个 cookie）。
#     本脚本负责拿到这四个 cookie —— 本机跑一次，用快爆 App「扫一扫」确认即可。
#
# 用法（在能打开浏览器的电脑上运行，手机和电脑需在同一网络或都能上公网）：
#     python hykb_web_login.py
#     浏览器打开 http://127.0.0.1:8899/  → 用快爆 App 扫页面上的二维码 → 手机上点「确认登录」
#     页面显示「登录成功」后，终端会打印一行可直接粘贴进环境变量 HYKB_WEB_COOKIE 的 cookie 串
#
# 说明：
#     二维码失效会自动换新（页面每 4 秒自刷新），不用赶时间；
#     登录态是账号级凭据，只在本机生成、只写到你自己的配置里，不要外传。
import io
import json
import pathlib
import socketserver
import threading
import time
import http.server

import qrcode
import requests

PORT = 8899
API = "https://www.3839.com/user/index.php"

state = {"qr": None, "png": None, "status": "初始化", "done": False, "uid": None}
lock = threading.Lock()

S = requests.Session()
S.trust_env = False
S.headers.update({
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"),
    "Referer": "https://www.3839.com/user/index.php?ac=login&appId=web",
    "X-Requested-With": "XMLHttpRequest",
})


def new_qr():
    """取新二维码（返回给展示页；登录态始终绑在本进程的 requests.Session 上）"""
    resp = S.post(f"{API}?ac=QRcodeCreate&appId=web", data={"r": str(time.time())}, timeout=20)
    data = resp.json()
    if data.get("code") != 100:
        raise RuntimeError(f"QRcodeCreate 失败：{data}")
    qr = data["result"]["qrcode"]
    buf = io.BytesIO()
    img = qrcode.make(qr)
    img = img.get_image().resize((300, 300)) if hasattr(img, "get_image") else img.resize((300, 300))
    img.save(buf, format="PNG")
    with lock:
        state.update({"qr": qr, "png": buf.getvalue(), "status": "等待扫码", "done": False})
    print("[*] 二维码已生成（有效期约 1 分钟，页面会自动换新）", flush=True)
    return qr


def poll_loop():
    """轮询扫码状态；确认后调 QRcodeAuthCallBack 换取登录 cookie"""
    while True:
        with lock:
            qr, done = state["qr"], state["done"]
        if done:
            time.sleep(3)
            continue
        try:
            resp = S.post(f"{API}?ac=QRcodePolling&appId=web",
                          data={"qrcode": qr, "r": str(time.time())}, timeout=15)
            data = resp.json()
        except Exception as exc:
            print(f"[!] 轮询异常：{type(exc).__name__}", flush=True)
            time.sleep(3)
            continue

        code = data.get("code")
        result = data.get("result") or {}
        if code == 100 and isinstance(result, dict) and "uid" in result:
            payload = {f"result[{k}]": ("" if v is None else str(v)) for k, v in result.items()}
            payload.update({"show_idcard": "0", "r": str(time.time())})
            S.post(f"{API}?ac=QRcodeAuthCallBack", data=payload, timeout=20)
            cookie = "; ".join(f"{k}={v}" for k, v in S.cookies.get_dict().items() if k != "show_idcard")
            with lock:
                state.update({"status": f"登录成功 uid={result.get('uid')}", "done": True, "uid": result.get("uid")})
            print(f"\n[✓] 登录成功：uid={result.get('uid')} nickname={result.get('nickname')}", flush=True)
            print("[✓] 把下面这一整行（等号后面全部内容）填到环境变量 HYKB_WEB_COOKIE：\n", flush=True)
            print("HYKB_WEB_COOKIE=" + cookie, flush=True)
            print("\n（本地调试也可以把等号后面的内容写进同目录 hykb_web_cookie.txt）", flush=True)
            time.sleep(3)
        elif code == 102:
            print("[*] 二维码过期，自动换新", flush=True)
            new_qr()
        elif isinstance(result, dict) and result.get("status") == 1:
            with lock:
                state["status"] = "已扫码，请在手机上确认"
        time.sleep(1.5)


PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>好游快爆 · 扫码登录</title>
<style>body{font-family:system-ui,"Microsoft YaHei";background:#111;color:#eee;text-align:center;padding:24px}
img{background:#fff;padding:10px;border-radius:8px}h2{font-weight:600}</style></head>
<body><h2>好游快爆 · 扫码登录</h2><img id="q" src="/qr.png" width="300" height="300">
<h2 id="st">加载中…</h2>
<p style="color:#888;font-size:13px">用快爆 App「扫一扫」扫这个码，然后在手机上点「确认登录」<br>二维码失效会自动换新</p>
<script>setInterval(()=>{document.getElementById('q').src='/qr.png?t='+Date.now();
 fetch('/status').then(r=>r.text()).then(t=>document.getElementById('st').textContent=t);},4000);
 fetch('/status').then(r=>r.text()).then(t=>{document.getElementById('st').textContent=t;});</script>
</body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path.startswith("/qr.png"):
            with lock:
                png = state["png"]
            if not png:
                self.send_response(503); self.end_headers(); return
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(png)))
            self.end_headers(); self.wfile.write(png)
        elif self.path.startswith("/status"):
            with lock:
                body = state["status"].encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body)
        else:
            body = PAGE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body)


if __name__ == "__main__":
    new_qr()
    threading.Thread(target=poll_loop, daemon=True).start()
    socketserver.TCPServer.allow_reuse_address = True
    print(f"[*] 请用浏览器打开 http://127.0.0.1:{PORT}/ ，用快爆 App 扫码并确认", flush=True)
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as srv:
        srv.serve_forever()
