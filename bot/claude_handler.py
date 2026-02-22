"""
调用 Claude API，返回 AI 回复。

ask_claude : 简单问答（无工具）
run_agent  : agent loop，支持工具调用
"""
import time
import anthropic
from config import ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL
from agent_tools import TOOLS, execute_tool

SYSTEM_PROMPT = """你是「电商-AI-agent特战队」的 AI 助理 pm-agent，运行在 claude-sonnet-4-6 模型上。
这是一个 30 人共创小组，目标是用 AI Agent 赋能 ToC 跨境电商卖家，帮助成员实现求职年薪 50 万或店铺增收 50 万纯利润。

**三步走方法论**
1. 痛点收集：整理跨境电商各职能（选品、运营、供应链、客服等）的真实痛点
2. Agent 定义：为每个痛点设计 AI 解决方案
3. Vibe Coding：用 Claude 快速实现 Agent

**痛点卡片格式**（鼓励成员按此格式提交）
```
职能：[选品/运营/供应链/物流/客服/财务/合规/团队管理]
痛点：[一句话描述]
具体场景：[什么情况下发生、影响多大]
期望解法：[你希望 AI 如何帮你]
```

**你的工具能力**
- `read_knowledge_base`：读取电商知识库（支持成员统计、指定成员痛点文件、职能章节）
- `add_pain_point`：写入成员痛点卡片到 GitHub 知识库
- `git_push`：将知识库改动推送到 GitHub
- `send_notification`：向本群发通知消息
- `send_file`：上传知识库文件到本群
- `web_search`：搜索互联网获取最新信息

**工具调用规则（必须严格遵守）**
1. 用户说"帮我记录痛点"或描述了一个痛点场景，**立即调用 `add_pain_point`**，不要反复追问细节。缺少的字段自行根据上下文推断填入合理值（如职能模块根据描述内容判断）。
2. 调用 `add_pain_point` 成功后，必须紧接着调用 `git_push`，commit_message 格式：`feat: 添加[职能]痛点-[标题]-by [提交人]`
3. 所有工具执行完毕后，必须调用 `send_notification` 向群里发一条执行汇报，格式：
   ```
   ✅ 操作完成汇报
   📝 写入痛点：[标题]（[职能]）
   📁 文件：成员痛点/[提交人].md（第N条）
   💾 GitHub 已推送：[commit_message]
   👤 提交人：[提交人]
   ```
4. 执行 `web_search` 后，直接把搜索结果整理成中文回复，不需要额外发群通知

**数据准确性规则（严禁幻觉）**
- 被问到"几个人提交了痛点""统计一下"时，**必须先调用 `read_knowledge_base(section="成员统计")`**，把工具返回的原始数据直接引用，禁止自己推算或估计数字
- 被问到某个成员的痛点时，**必须先调用 `read_knowledge_base(section="成员:xxx")`**，用工具返回的原文回答，不得凭记忆编造
- 永远不允许在没有调用工具的情况下给出具体的数字（如"3条"、"8条"等）

**回复风格**
- 使用中文
- 不超过 300 字
- 直接给出可操作的建议
- 对痛点类消息，帮助成员补全或优化卡片格式
- 对技术问题，给出简洁步骤
- 友好、专业，不废话
"""


_MODELS = ["claude-sonnet-4-6", "claude-haiku-4-5-20251001"]
_MAX_RETRIES = 3
_RETRY_DELAY = 5  # seconds


def ask_claude(user_message: str) -> str:
    """调用 Claude，返回回复文本。500/529 时自动重试并切换备用模型。"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY, base_url=ANTHROPIC_BASE_URL)
    last_error = None
    for model in _MODELS:
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                message = client.messages.create(
                    model=model,
                    max_tokens=600,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_message}],
                )
                return message.content[0].text
            except anthropic.InternalServerError as e:
                last_error = e
                if attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_DELAY * attempt)
                continue
            except anthropic.APIStatusError as e:
                last_error = e
                if e.status_code == 529 and attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_DELAY * attempt)
                    continue
                break
    raise RuntimeError(f"Claude API 全部重试失败: {last_error}")


MAX_AGENT_TURNS = 10


def _call_with_retry(client, model: str, messages: list) -> object:
    """单次 API 调用，500/529 自动重试最多3次。"""
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            return client.messages.create(
                model=model,
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )
        except anthropic.InternalServerError:
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY * attempt)
            else:
                raise
        except anthropic.APIStatusError as e:
            if e.status_code == 529 and attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY * attempt)
            else:
                raise


def run_agent(user_message: str) -> str:
    """带工具调用的 agent loop。支持多轮工具调用直至 end_turn，500/529 自动重试+降级。"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY, base_url=ANTHROPIC_BASE_URL)
    messages = [{"role": "user", "content": user_message}]

    for _ in range(MAX_AGENT_TURNS):
        last_error = None
        response = None
        for model in _MODELS:
            try:
                response = _call_with_retry(client, model, messages)
                break
            except Exception as e:
                last_error = e
                continue
        if response is None:
            raise RuntimeError(f"Claude API 全部重试失败: {last_error}")

        if response.stop_reason == "end_turn":
            texts = [b.text for b in response.content if hasattr(b, "text")]
            return "\n".join(texts) or "已完成"

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
                    })
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    return "处理完成"
