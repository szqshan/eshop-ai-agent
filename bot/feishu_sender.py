"""
飞书消息发送封装。
send_message  : 向群发新消息（备用）
reply_message : 回复指定消息（带引用，推荐）
"""
import json
import lark_oapi as lark
from lark_oapi.api.im.v1 import (
    CreateMessageRequest, CreateMessageRequestBody,
    ReplyMessageRequest, ReplyMessageRequestBody,
)
from config import FEISHU_APP_ID, FEISHU_APP_SECRET


def _get_client() -> lark.Client:
    return (
        lark.Client.builder()
        .app_id(FEISHU_APP_ID)
        .app_secret(FEISHU_APP_SECRET)
        .build()
    )


def reply_message(message_id: str, text: str, reply_in_thread: bool = False) -> None:
    """回复指定消息（引用回复），message_id 来自事件的 msg.message_id。"""
    client = _get_client()
    body = (
        ReplyMessageRequestBody.builder()
        .msg_type("text")
        .content(json.dumps({"text": text}))
        .reply_in_thread(reply_in_thread)
        .build()
    )
    request = (
        ReplyMessageRequest.builder()
        .message_id(message_id)
        .request_body(body)
        .build()
    )
    resp = client.im.v1.message.reply(request)
    if not resp.success():
        raise RuntimeError(
            f"飞书回复消息失败: code={resp.code}, msg={resp.msg}"
        )


def send_message(chat_id: str, text: str) -> None:
    """向指定群发送新的纯文本消息（备用，当 message_id 不可用时）。"""
    client = _get_client()
    body = (
        CreateMessageRequestBody.builder()
        .receive_id(chat_id)
        .msg_type("text")
        .content(json.dumps({"text": text}))
        .build()
    )
    request = (
        CreateMessageRequest.builder()
        .receive_id_type("chat_id")
        .request_body(body)
        .build()
    )
    resp = client.im.v1.message.create(request)
    if not resp.success():
        raise RuntimeError(
            f"飞书发送消息失败: code={resp.code}, msg={resp.msg}"
        )
