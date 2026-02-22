"""
启动 PM-Agent Bot
运行方式：
  python 启动PM-Agent.py          # 轮询模式（推荐，稳定）
  python 启动PM-Agent.py ws       # WebSocket 模式（需飞书事件订阅正常）
"""
import sys
import os
import atexit

bot_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot")
sys.path.insert(0, bot_dir)
os.chdir(bot_dir)

# ── 防多实例：PID 锁文件 ──────────────────────────────────────────────
LOCK_FILE = os.path.join(bot_dir, ".bot.pid")

def _check_lock():
    if os.path.exists(LOCK_FILE):
        try:
            old_pid = int(open(LOCK_FILE).read().strip())
            import psutil
            if psutil.pid_exists(old_pid):
                print(f"[ERROR] Bot 已在运行 (PID {old_pid})，请先关闭再启动。")
                sys.exit(1)
        except Exception:
            pass  # PID 文件残留但进程已不存在，继续启动
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    atexit.register(lambda: os.path.exists(LOCK_FILE) and os.remove(LOCK_FILE))

try:
    import psutil
    _check_lock()
except ImportError:
    pass  # psutil 未安装时跳过锁检查

mode = sys.argv[1] if len(sys.argv) > 1 else "poll"

if mode == "ws":
    import pm_agent_bot
    pm_agent_bot.main()
else:
    import polling_bot
    polling_bot.main()
