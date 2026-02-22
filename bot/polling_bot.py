"""
polling_bot.py — HTTP 轮询模式
每 5 秒拉一次群消息，检测新的 @机器人 消息并回复。
不依赖 WebSocket 事件订阅，直接调用 REST API。
"""
import json
import logging
import time
import requests
from collections import deque

from config import (
    FEISHU_APP_ID, FEISHU_APP_SECRET,
    BOT_OPEN_ID, TARGET_CHAT_ID, DEDUP_CACHE_SIZE,
)
from claude_handler import run_agent
from feishu_sender import reply_message, send_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

POLL_INTERVAL = 5          # 秒
PAGE_SIZE = 10             # 每次拉多少条
_seen_ids: deque = deque(maxlen=DEDUP_CACHE_SIZE)


def get_token() -> str:
    resp = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"获取 token 失败: {data}")
    return data["tenant_access_token"]


def fetch_messages(token: str) -> list:
    """拉取目标群最新消息（按时间倒序）。"""
    resp = requests.get(
        "https://open.feishu.cn/open-apis/im/v1/messages",
        params={
            "container_id_type": "chat",
            "container_id": TARGET_CHAT_ID,
            "sort_type": "ByCreateTimeDesc",
            "page_size": PAGE_SIZE,
        },
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"拉取消息失败: {data}")
    return data.get("data", {}).get("items", [])


def is_bot_mentioned(msg: dict) -> bool:
    """检查消息是否 @了机器人。"""
    if not BOT_OPEN_ID:
        return True  # BOT_OPEN_ID 未设置时响应所有消息
    mentions = msg.get("mentions", [])
    return any(m.get("id") == BOT_OPEN_ID for m in mentions)


def extract_text(msg: dict) -> str:
    """从消息 body 提取纯文本，去掉 @mention 标记。"""
    try:
        content = json.loads(msg["body"]["content"])
        text = content.get("text", "")
        # 去掉 @_user_N 占位符
        import re
        text = re.sub(r"@_user_\d+\s*", "", text).strip()
        return text
    except Exception:
        return ""


def process_message(msg: dict) -> None:
    message_id = msg["message_id"]
    if message_id in _seen_ids:
        return
    _seen_ids.append(message_id)

    if msg.get("msg_type") != "text":
        return
    if not is_bot_mentioned(msg):
        return

    text = extract_text(msg)
    if not text:
        return

    logger.info("处理消息 id=%s text=%r", message_id, text)
    try:
        reply = run_agent(text)
        reply_message(message_id, reply)
        logger.info("已回复: %r", reply[:80])
    except Exception:
        logger.exception("回复失败")


def main() -> None:
    logger.info("启动轮询 Bot — APP_ID=%s TARGET=%s", FEISHU_APP_ID, TARGET_CHAT_ID)
    logger.info("BOT_OPEN_ID=%s  轮询间隔=%ds", BOT_OPEN_ID or "（全部响应）", POLL_INTERVAL)

    token = ""
    token_expire = 0

    # 启动时先拉一次，把现有消息都标记为已处理（避免回复历史消息）
    logger.info("初始化：加载历史消息 ID...")
    try:
        token = get_token()
        token_expire = time.time() + 7000
        msgs = fetch_messages(token)
        for m in msgs:
            _seen_ids.append(m["message_id"])
        logger.info("已跳过 %d 条历史消息，开始监听新消息", len(msgs))
    except Exception:
        logger.exception("初始化失败")

    logger.info("轮询中，Ctrl+C 退出...")
    while True:
        try:
            # token 快过期时刷新（7200s 有效期，提前 200s 刷新）
            if time.time() >= token_expire:
                token = get_token()
                token_expire = time.time() + 7000
                logger.debug("Token 已刷新")

            msgs = fetch_messages(token)
            for msg in reversed(msgs):   # 按时间正序处理
                process_message(msg)

        except Exception:
            logger.exception("轮询出错，5s 后重试")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
