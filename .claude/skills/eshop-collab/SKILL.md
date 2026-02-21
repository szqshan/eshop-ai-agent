---
name: eshop-collab
description: 跨境电商 AI Agent 共创协作技能。当用户说「发消息给群」「更新知识库」「填写痛点」「提交 GitHub」「通知群成员」「查看进度」「我要写痛点」「讨论电商AI」时触发。服务于「电商-AI-agent特战队」30名成员，帮助大家用 Claude 高效协作，共同开发跨境电商 AI Agent 产品。
---

## 项目速查

- **GitHub 仓库**: https://github.com/szqshan/eshop-ai-agent
- **核心文件**: `电商知识库/痛点_问题_需求/职能痛点矩阵.md`
- **飞书群**: 电商AI-agent特战队（chat_id: `oc_ea4a789a0305af2d0fb8c99bea026afd`）
- **飞书 MCP**: `pm-agent`
- **当前阶段**: 第一步——痛点收集

## 初始化（首次使用必做）

用户第一次使用时，先确认仓库位置：

```bash
# 找到本机仓库根目录
git rev-parse --show-toplevel
```

把输出路径记为 `REPO_ROOT`，后续所有 git 命令都用这个路径。
如果报错说明还没克隆，引导用户先执行：
```bash
git clone https://github.com/szqshan/eshop-ai-agent.git
cd eshop-ai-agent
```

## 工作流一：填写痛点卡片（核心工作流）

用户说「我要写痛点」「帮我填痛点」时，**依次引导提问**：

1. 「你主要做哪个平台？（亚马逊 / TikTok / Temu / 独立站）」
2. 「遇到了什么问题，一句话描述？」
3. 「现在怎么解决或忍受这个问题的？」
4. 「大概每周或每月损失多少时间或金钱？（估算即可）」
5. 「你希望的理想状态是什么？」
6. 「你的昵称是？」

收集完后生成标准卡片，写入 `电商知识库/痛点_问题_需求/职能痛点矩阵.md` 对应模块：

```
**[痛点标题]**
- 场景：什么情况下遇到？
- 当前做法：现在怎么解决或忍受的？
- 问题所在：具体卡在哪里？
- 损失量化：每周/月损失多少时间或金钱？
- 期望结果：理想状态是什么样？
- 平台：[亚马逊] / [TK] / [Temu] / [独立站] / [通用]
- 提交人：（昵称）
```

**职能模块对应**：
- 选品/找货/竞品 → 「一、选品 & 市场调研」
- 写 Listing/内容/图片/视频 → 「二、Listing / 内容生产」
- 广告/投流/引流 → 「三、广告投放 & 引流」
- 客服/评论/售后 → 「四、客服 & 评论管理」
- 库存/备货/物流 → 「五、库存 & 供应链」
- 利润/财务/核算 → 「六、财务 & 利润核算」
- 数据/报表/分析 → 「七、数据分析 & 经营决策」
- 封号/合规/风控 → 「八、合规 & 账号安全」

## 工作流二：提交 GitHub

填完痛点后，或用户说「提交 GitHub」「同步文档」时执行：

```bash
REPO=$(git rev-parse --show-toplevel)
git -C "$REPO" pull origin master
# （Edit 工具写入文件后）
git -C "$REPO" add 电商知识库/
git -C "$REPO" commit -m "feat: 补充[模块名]痛点 - [提交人昵称]"
git -C "$REPO" push origin master
```

提交成功后询问：「要通知群里吗？」

## 工作流三：发飞书群消息

用户说「通知群里」「给群发消息」时：

```
工具：mcp__pm-agent__im_v1_message_create
chat_id：oc_ea4a789a0305af2d0fb8c99bea026afd
msg_type：text
```

消息风格：简洁、有行动号召，结尾带 GitHub 链接。

## 工作流四：读取群最新消息

用户说「看看群里说什么」「读取群消息」时：

```
工具：mcp__pm-agent__im_v1_message_list
container_id：oc_ea4a789a0305af2d0fb8c99bea026afd
container_id_type：chat
page_size：10          ← 默认只读10条，避免上下文爆炸
sort_type：ByCreateTimeDesc
```

读取后摘要输出，不要把原始 JSON 全部展示给用户。
如需更多，用 `start_time` 按时间段过滤，不要无限加大 page_size。

## 工作流五：讨论电商 AI Agent 方向

用户说「我们应该做什么 Agent」「讨论方向」时，加载方法论：

```
参考：references/methodology.md
```

引导用户按四维评分筛选方向，不接受没有量化的方案。

## 核心原则

1. 痛点必须有损失量化，不接受「太麻烦了」
2. 方向选择用评分公式：严重程度 × 频次 × AI可行性 × 市场规模
3. 写代码前必须有 Agent 定义文档
4. MVP = 跑通核心流程，不追求完美
5. 每次 git pull 再编辑，避免冲突
