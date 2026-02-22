"""
统一读取环境变量，提供全局常量。
"""
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)

FEISHU_APP_ID = os.environ["FEISHU_APP_ID"]
FEISHU_APP_SECRET = os.environ["FEISHU_APP_SECRET"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
ANTHROPIC_BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
FEISHU_ENCRYPT_KEY = os.environ.get("FEISHU_ENCRYPT_KEY", "")
FEISHU_VERIFICATION_TOKEN = os.environ.get("FEISHU_VERIFICATION_TOKEN", "")
BOT_OPEN_ID = os.environ.get("BOT_OPEN_ID", "")  # 首次运行可为空，从日志中获取
TARGET_CHAT_ID = os.environ["TARGET_CHAT_ID"]

# 消息去重缓存大小
DEDUP_CACHE_SIZE = 100
