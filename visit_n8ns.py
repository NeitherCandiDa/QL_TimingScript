# const $ = new Env('定时请求n8n');
# cron: 0 0 */2 * * *
import httpx


def requestWeb(url):
    try:
        response = httpx.get(url)
        print(response)
        print(response.text)
        if response.status_code == 200:
            print("Success")
        else:
            print("Error")
    except Exception as e:
        return str(f"访问失败: {e}")


if __name__ == '__main__':
    n8nUlrs = [
        "https://liulong0608-qinglong.hf.space/",
        "https://liulong0608-baota.hf.space/",
        "https://xwq3367-qinglong.hf.space/"
    ]
    for url in n8nUlrs:
        requestWeb(url)
