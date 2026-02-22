"""
agent_tools.py — 5 个工具的 schema 定义 + 实现函数

工具列表：
  read_knowledge_base  读取职能痛点矩阵
  add_pain_point       写入新痛点卡片
  git_push             commit & push 到 GitHub
  send_notification    向飞书群发通知
  web_search           DuckDuckGo 搜索
"""
import os
import subprocess

# 路径常量（由文件自身位置推算，不硬编码）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_FILE = os.path.join(PROJECT_ROOT, "电商知识库", "痛点_问题_需求", "职能痛点矩阵.md")
KB_MEMBER_DIR = os.path.join(PROJECT_ROOT, "电商知识库", "痛点_问题_需求", "成员痛点")

SECTION_MAP = {
    "选品":   "## 一、选品 & 市场调研",
    "Listing": "## 二、Listing / 内容生产",
    "广告":   "## 三、广告投放 & 引流",
    "客服":   "## 四、客服 & 评论管理",
    "库存":   "## 五、库存 & 供应链",
    "财务":   "## 六、财务 & 利润核算",
    "数据分析": "## 七、数据分析 & 经营决策",
    "合规":   "## 八、合规 & 账号安全",
}

# ─── Tool Schemas ────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "read_knowledge_base",
        "description": (
            "读取电商知识库内容。支持三种模式：\n"
            "1. section 留空：返回职能痛点矩阵概览\n"
            "2. section='成员统计'：扫描成员痛点目录，返回每人提交了几条痛点\n"
            "3. section='成员:木易'：读取指定成员的完整痛点文件\n"
            "4. section='选品'等职能名称：读取职能痛点矩阵对应章节"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "description": "职能模块（选品/Listing/广告/客服/库存/财务/数据分析/合规），不填返回全文前3000字",
                }
            },
            "required": [],
        },
    },
    {
        "name": "add_pain_point",
        "description": "向知识库写入一条新的痛点卡片。写完后建议调用 git_push。",
        "input_schema": {
            "type": "object",
            "properties": {
                "section":          {"type": "string", "description": "职能模块：选品/Listing/广告/客服/库存/财务/数据分析/合规"},
                "title":            {"type": "string", "description": "痛点标题（一句话）"},
                "scenario":         {"type": "string", "description": "场景：什么情况下遇到"},
                "current_approach": {"type": "string", "description": "当前做法（可选）"},
                "problem":          {"type": "string", "description": "问题所在"},
                "loss":             {"type": "string", "description": "损失量化：时间或金钱（可选）"},
                "expected":         {"type": "string", "description": "期望结果"},
                "platform":         {"type": "string", "description": "平台：亚马逊/TK/Temu/独立站/通用"},
                "submitter":        {"type": "string", "description": "提交人昵称"},
            },
            "required": ["section", "title", "scenario", "problem", "expected", "platform", "submitter"],
        },
    },
    {
        "name": "git_push",
        "description": "将知识库改动 commit 并推送到 GitHub。add_pain_point 之后调用。",
        "input_schema": {
            "type": "object",
            "properties": {
                "commit_message": {
                    "type": "string",
                    "description": "提交说明，如「feat: 添加广告痛点-by 小明」",
                }
            },
            "required": ["commit_message"],
        },
    },
    {
        "name": "send_notification",
        "description": "向飞书「电商AI-agent特战队」群发送通知消息。",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "消息内容"}
            },
            "required": ["text"],
        },
    },
    {
        "name": "web_search",
        "description": "搜索互联网，获取跨境电商政策、工具推荐、最新行业动态等信息。",
        "input_schema": {
            "type": "object",
            "properties": {
                "query":       {"type": "string", "description": "搜索关键词"},
                "max_results": {"type": "integer", "description": "返回条数，默认3，最多5"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "send_file",
        "description": (
            "将知识库中的文件发送到飞书「电商AI-agent特战队」群。"
            "可发送成员痛点文件（如「木易」「龙君」「张涛」等）或职能痛点矩阵。"
            "file_path 为相对于知识库根目录的路径，"
            "例如：「痛点_问题_需求/成员痛点/木易.md」或「痛点_问题_需求/职能痛点矩阵.md」。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": (
                        "相对于「电商知识库/」的文件路径。"
                        "成员痛点示例：痛点_问题_需求/成员痛点/木易.md；"
                        "矩阵示例：痛点_问题_需求/职能痛点矩阵.md"
                    ),
                }
            },
            "required": ["file_path"],
        },
    },
]

# ─── Tool Implementations ─────────────────────────────────────────────────────

def _read_knowledge_base(section: str = "") -> str:
    # 模式2：成员统计 - 扫描成员痛点目录
    if section == "成员统计":
        if not os.path.exists(KB_MEMBER_DIR):
            return "成员痛点目录不存在"
        lines = ["## 成员痛点统计\n"]
        total_points = 0
        member_count = 0
        for fname in sorted(os.listdir(KB_MEMBER_DIR)):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(KB_MEMBER_DIR, fname)
            with open(fpath, encoding="utf-8") as f:
                cnt = f.read().count("## 痛点 ")
            name = fname.replace(".md", "")
            lines.append(f"- {name}：{cnt} 条")
            total_points += cnt
            member_count += 1
        lines.append(f"\n**合计：{member_count} 人，{total_points} 条痛点**")
        return "\n".join(lines)

    # 模式3：成员:木易 - 读取指定成员文件
    if section.startswith("成员:"):
        name = section[3:].strip()
        member_file = os.path.join(KB_MEMBER_DIR, f"{name}.md")
        if not os.path.exists(member_file):
            available = [f.replace(".md", "") for f in os.listdir(KB_MEMBER_DIR) if f.endswith(".md")]
            return f"未找到成员「{name}」，现有成员：{available}"
        with open(member_file, encoding="utf-8") as f:
            return f.read()

    # 模式1：section 留空 - 返回职能痛点矩阵概览
    if not section:
        try:
            with open(KB_FILE, encoding="utf-8") as f:
                return f.read()[:3000]
        except FileNotFoundError:
            return f"知识库文件不存在：{KB_FILE}"

    # 模式4：职能名称 - 读取职能痛点矩阵对应章节
    try:
        with open(KB_FILE, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return f"知识库文件不存在：{KB_FILE}"

    heading = SECTION_MAP.get(section)
    if not heading:
        return f"未找到职能模块「{section}」，可选：{list(SECTION_MAP.keys())}"

    start = content.find(heading)
    if start == -1:
        return f"知识库中未找到章节标题「{heading}」"

    next_section = content.find("\n## ", start + 1)
    chunk = content[start:next_section] if next_section != -1 else content[start:]
    return chunk[:3000]


def _add_pain_point(
    section: str,
    title: str,
    scenario: str,
    problem: str,
    expected: str,
    platform: str,
    submitter: str,
    current_approach: str = "",
    loss: str = "",
) -> str:
    """写入新痛点卡片到提交人的专属 MD 文件（成员痛点/{提交人}.md）。"""
    if section not in SECTION_MAP:
        return f"未找到职能模块「{section}」，可选：{list(SECTION_MAP.keys())}"

    os.makedirs(KB_MEMBER_DIR, exist_ok=True)
    member_file = os.path.join(KB_MEMBER_DIR, f"{submitter}.md")

    # 若文件不存在则初始化
    if not os.path.exists(member_file):
        header = f"# {submitter}的痛点卡片\n\n> 提交人：{submitter}\n\n---\n\n"
        with open(member_file, encoding="utf-8", mode="w") as f:
            f.write(header)

    with open(member_file, encoding="utf-8") as f:
        content = f.read()

    # 计算当前痛点编号
    pain_count = content.count("## 痛点 ") + 1

    # 构建痛点卡片
    lines = [f"## 痛点 {pain_count}", "", f"**{title}**"]
    lines.append(f"- 场景：{scenario}")
    if current_approach:
        lines.append(f"- 当前做法：{current_approach}")
    lines.append(f"- 问题所在：{problem}")
    if loss:
        lines.append(f"- 损失量化：{loss}")
    lines.append(f"- 期望结果：{expected}")
    lines.append(f"- 平台：[{platform}]")
    lines.append(f"- 职能：{section}")
    lines.append("")
    lines.append("---")
    lines.append("")
    card = "\n".join(lines)

    with open(member_file, encoding="utf-8", mode="a") as f:
        f.write(card)

    return f"痛点卡片「{title}」已写入 {submitter}.md（第 {pain_count} 条）。"


def _git_push(commit_message: str) -> str:
    kb_rel = os.path.join("电商知识库")
    steps = [
        ["git", "-C", PROJECT_ROOT, "add", kb_rel],
        ["git", "-C", PROJECT_ROOT, "commit", "-m", commit_message],
        ["git", "-C", PROJECT_ROOT, "push", "origin", "master"],
    ]
    for cmd in steps:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if result.returncode != 0:
            # commit 返回码 1 可能表示"nothing to commit"，不当错误处理
            if "nothing to commit" in result.stdout + result.stderr:
                return "没有新改动可提交（知识库内容未变化）。"
            return (
                f"命令失败：{' '.join(cmd)}\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )
    return f"已成功推送到 GitHub，commit: {commit_message}"


def _send_notification(text: str) -> str:
    from config import TARGET_CHAT_ID
    from feishu_sender import send_message
    send_message(TARGET_CHAT_ID, text)
    return "通知已发送到飞书群。"


def _send_file(file_path: str) -> str:
    """上传本地文件到飞书并发送到群。file_path 相对于 电商知识库/ 目录。"""
    import json
    import requests
    from config import FEISHU_APP_ID, FEISHU_APP_SECRET, TARGET_CHAT_ID

    full_path = os.path.join(PROJECT_ROOT, "电商知识库", file_path)
    if not os.path.exists(full_path):
        # 尝试模糊匹配成员痛点文件
        member_dir = KB_MEMBER_DIR
        candidates = [f for f in os.listdir(member_dir) if file_path.replace(".md", "") in f]
        if candidates:
            full_path = os.path.join(member_dir, candidates[0])
        else:
            return f"文件不存在：{full_path}"

    filename = os.path.basename(full_path)
    file_size = os.path.getsize(full_path)

    # 1. 获取 tenant_access_token
    token_resp = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET},
        timeout=10,
    )
    token_resp.raise_for_status()
    token = token_resp.json()["tenant_access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. 上传文件
    with open(full_path, "rb") as f:
        upload_resp = requests.post(
            "https://open.feishu.cn/open-apis/im/v1/files",
            headers=headers,
            data={"file_type": "stream", "file_name": filename, "size": str(file_size)},
            files={"file": (filename, f, "application/octet-stream")},
            timeout=30,
        )
    upload_resp.raise_for_status()
    upload_data = upload_resp.json()
    if upload_data.get("code") != 0:
        return f"文件上传失败：{upload_data}"
    file_key = upload_data["data"]["file_key"]

    # 3. 发送文件消息到群
    send_resp = requests.post(
        "https://open.feishu.cn/open-apis/im/v1/messages",
        headers={**headers, "Content-Type": "application/json"},
        params={"receive_id_type": "chat_id"},
        json={
            "receive_id": TARGET_CHAT_ID,
            "msg_type": "file",
            "content": json.dumps({"file_key": file_key}),
        },
        timeout=15,
    )
    send_resp.raise_for_status()
    send_data = send_resp.json()
    if send_data.get("code") != 0:
        return f"文件发送失败：{send_data}"

    return f"文件「{filename}」已发送到飞书群。"


def _web_search(query: str, max_results: int = 3) -> str:
    max_results = min(max(1, max_results), 5)
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return "duckduckgo-search 未安装，请运行：pip install duckduckgo-search>=6.0.0"

    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append(f"**{r.get('title', '')}**\n{r.get('href', '')}\n{r.get('body', '')}")

    if not results:
        return f"搜索「{query}」无结果。"
    return "\n\n".join(results)


# ─── Unified Dispatcher ───────────────────────────────────────────────────────

def execute_tool(name: str, inputs: dict) -> str:
    """统一调度入口，捕获异常返回字符串错误信息。"""
    try:
        if name == "read_knowledge_base":
            return _read_knowledge_base(**inputs)
        elif name == "add_pain_point":
            return _add_pain_point(**inputs)
        elif name == "git_push":
            return _git_push(**inputs)
        elif name == "send_notification":
            return _send_notification(**inputs)
        elif name == "send_file":
            return _send_file(**inputs)
        elif name == "web_search":
            return _web_search(**inputs)
        else:
            return f"未知工具：{name}"
    except Exception as e:
        return f"工具 {name} 执行出错：{e}"
