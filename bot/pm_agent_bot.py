"""
pm_agent_bot.py — WebSocket 长连接版本
ws_client.start() 在主线程运行，worker 在 daemon 线程，Ctrl+C 干净退出。
"""
import json
import logging
import queue
import re
import threading
from collections import deque

import lark_oapi as lark
from lark_oapi.api.im.v1 import P2ImMessageReceiveV1

from config import (
    BOT_OPEN_ID, DEDUP_CACHE_SIZE,
    FEISHU_APP_ID, FEISHU_APP_SECRET,
    FEISHU_ENCRYPT_KEY, FEISHU_VERIFICATION_TOKEN,
    TARGET_CHAT_ID,
)
from claude_handler import ask_claude
from feishu_sender import reply_message, send_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

_queue: queue.Queue = queue.Queue()
_seen_ids: deque = deque(maxlen=DEDUP_CACHE_SIZE)


def on_message_receive(data: P2ImMessageReceiveV1) -> None:
    try:
        msg = data.event.message
        sender = data.event.sender
        sender_open_id = (
            sender.sender_id.open_id
            if sender and sender.sender_id else "unknown"
        )
        logger.info("收到消息 message_id=%s chat_id=%s sender=%s",
                    msg.message_id, msg.chat_id, sender_open_id)

        if msg.message_id in _seen_ids:
            return
        _seen_ids.append(msg.message_id)

        if msg.chat_id != TARGET_CHAT_ID:
            return

        try:
            text = json.loads(msg.content).get("text", "").strip()
        except (json.JSONDecodeError, AttributeError):
            return

        if BOT_OPEN_ID:
            mentions = getattr(msg, "mentions", None) or []
            if not any(
                getattr(getattr(m, "id", None), "open_id", None) == BOT_OPEN_ID
                for m in mentions
            ):
                return

        clean = re.sub(r"@\S+", "", text).strip()
        if not clean:
            return

        logger.info("入队: %r", clean)
        _queue.put_nowait({
            "chat_id": msg.chat_id,
            "message_id": msg.message_id,
            "text": clean,
        })

    except Exception:
        logger.exception("on_message_receive 异常")


def worker() -> None:
    logger.info("Worker 启动")
    while True:
        item = _queue.get()
        try:
            reply = ask_claude(item["text"])
            message_id = item.get("message_id")
            if message_id:
                reply_message(message_id, reply)
            else:
                send_message(item["chat_id"], reply)
            logger.info("已回复: %r", reply[:80])
        except Exception:
            logger.exception("处理消息失败")
        finally:
            _queue.task_done()


def main() -> None:
    logger.info("启动 pm-agent Bot (WebSocket 模式)")
    logger.info("APP_ID: %s", FEISHU_APP_ID)
    logger.info("TARGET_CHAT_ID: %s", TARGET_CHAT_ID)

    threading.Thread(target=worker, daemon=True, name="worker").start()

    event_handler = (
        lark.EventDispatcherHandler.builder(
            FEISHU_VERIFICATION_TOKEN, FEISHU_ENCRYPT_KEY
        )
        .register_p2_im_message_receive_v1(on_message_receive)
        .build()
    )

    ws_client = lark.ws.Client(
        FEISHU_APP_ID,
        FEISHU_APP_SECRET,
        event_handler=event_handler,
        log_level=lark.LogLevel.DEBUG,
    )

    logger.info("WebSocket 连接中，Ctrl+C 退出...")
    try:
        ws_client.start()  # 主线程阻塞，SDK 在主线程 event loop 中运行
    except KeyboardInterrupt:
        logger.info("已停止")


if __name__ == "__main__":
    main()
