"""
raw_ws_debug.py — 原始 WebSocket 诊断脚本
绕过 lark-oapi SDK，直接打印飞书推送的所有原始帧。

运行后在飞书群里发消息，看这里有没有任何输出（除 ping/pong 之外）。
"""
import asyncio
import json
import requests
import websockets
import sys

APP_ID = "cli_a9102436a5f85cc2"
APP_SECRET = "SuRj2cAvFbkeOPLKPw9MPggYWqHP7ZTj"


def get_ws_url():
    resp = requests.post(
        "https://open.feishu.cn/callback/ws/endpoint",
        headers={"locale": "zh"},
        json={"AppID": APP_ID, "AppSecret": APP_SECRET},
    )
    data = resp.json()
    print(f"[HTTP] status={resp.status_code} body={json.dumps(data, ensure_ascii=False)}")
    url = data["data"]["URL"]
    return url


async def listen(url):
    print(f"[WS] connecting: {url[:80]}...")
    async with websockets.connect(url) as ws:
        print("[WS] connected, waiting for all frames...")
        async for raw in ws:
            if isinstance(raw, bytes):
                try:
                    text = raw.decode("utf-8", errors="replace")
                except Exception:
                    text = repr(raw)
            else:
                text = raw
            print(f"[FRAME] len={len(raw)} data={text[:500]}")
            sys.stdout.flush()


async def main():
    url = get_ws_url()
    await listen(url)


if __name__ == "__main__":
    asyncio.run(main())
