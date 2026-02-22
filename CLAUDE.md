# E_shop_ai_agent 项目开发规范

## Bot 启动规范

### ⚠️ 严禁通过 Claude Code Bash 工具后台启动 Bot

**错误做法（会造成多实例）：**
```bash
python 启动PM-Agent.py >> bot/bot.log 2>&1 &
```

**正确做法：**
- 在系统独立终端/命令提示符窗口运行：
  ```
  python D:\E_shop_ai_agent\启动PM-Agent.py
  ```
- 保持窗口开着，Ctrl+C 退出

### 多实例大坑
- 每次 `&` 后台启动都会残留一个进程
- 旧进程不会自动退出，去重缓存相互独立
- 结果：同一条飞书消息被多个 bot 实例各回复一遍

### 启动前检查存量进程
```bash
ps aux | grep -E "pm_agent_bot|polling_bot" | grep -v grep
```
如有残留，用 PID 逐一终止：
```bash
python -c "import psutil; psutil.Process(PID).kill()"
```

### 项目已有防护
- `启动PM-Agent.py` 已加 PID 锁文件（`bot/.bot.pid`）
- 需要 `pip install psutil`（已安装）
- 第二个实例启动时会打印错误并退出

## 文件结构
- `bot/polling_bot.py` — 主 bot（HTTP 轮询）
- `bot/claude_handler.py` — Claude API 调用 + agent loop
- `bot/agent_tools.py` — 5 个工具实现
- `bot/config.py` — 读取 `.env` 环境变量
- `bot/feishu_sender.py` — 飞书消息发送封装
- `bot/.env` — 密钥（不提交 GitHub）

## Bot 工具能力
| 工具 | 功能 |
|------|------|
| `read_knowledge_base` | 读职能痛点矩阵，可按模块筛选 |
| `add_pain_point` | 写入新痛点卡片到知识库 |
| `git_push` | commit + push 到 GitHub |
| `send_notification` | 向飞书群发通知 |
| `web_search` | DuckDuckGo 搜索 |
