# 银发守护 Silver Guardian v2.0 🛡️

> **Agent + MCP + 双 RAG 引擎** 的适老化智能生活助手  
> 让老年人用「说话 + 拍照」就能完成数字生活中的所有事  
> **v2.0 合并 my-wiki 知识库 + 日记心情系统**

---

## 🆕 v2.0 新特性

| 功能 | 来源 | 说明 |
|------|------|------|
| **个人知识库** | my-wiki | BM25 语义检索，索引 brain/ 笔记 |
| **日记心情 Agent** | my-wiki | 日记 CRUD + 文本情绪分析 |
| **语音心情分析** | my-wiki | 声学特征（能量/音高/语速）辅助心情判定 |
| **心情趋势分析** | my-wiki | 周/月度心情分布统计与可视化 |
| **双 RAG 引擎** | 两者合并 | HealthKB (ChromaDB) + PersonalKB (BM25) |

---

## 项目结构

```
silver-guardian-v2/
├── backend/                          # 后端服务 (FastAPI)
│   ├── app/
│   │   ├── agents/                   # Agent 编排
│   │   │   ├── orchestrator.py       # ★ 主控编排器（6 种意图）
│   │   │   ├── life_assistant.py     # 生活助手 Agent
│   │   │   ├── health_advisor.py     # 健康顾问 Agent
│   │   │   ├── emergency_responder.py # 紧急响应 Agent
│   │   │   └── diary_agent.py        # 🆕 日记心情 Agent
│   │   ├── core/
│   │   │   ├── llm.py              # LLM API 独立封装层
│   │   │   ├── config.py           # 全局配置
│   │   │   └── theme.py            # 🆕 UI 主题系统
│   │   ├── rag/                      # 双 RAG 引擎
│   │   │   ├── __init__.py          # UnifiedRAG: HealthKB + PersonalKB
│   │   │   ├── personal_kb.py       # 🆕 my-wiki BM25 引擎
│   │   │   └── tag_extractor.py     # 🆕 标签提取
│   │   ├── voice/                    # 🆕 语音心情分析
│   │   │   └── __init__.py          # 声学分析 + 文本情绪 + 融合判定
│   │   ├── mcp_servers/             # MCP 工具层
│   │   │   ├── weather_server.py    # 天气查询
│   │   │   ├── medicine_server.py   # 药品信息
│   │   │   ├── reminder_server.py   # 提醒服务
│   │   │   └── emergency_server.py  # 紧急通知
│   │   ├── api/routes.py            # REST + WebSocket API
│   │   └── schemas/                 # Pydantic 数据模型
│   ├── data/                        # 持久化数据
│   │   ├── chroma/                  # 向量数据库
│   │   ├── diary/                   # 🆕 日记存储
│   │   ├── mood/                    # 🆕 心情记录
│   │   └── reminders/               # 提醒数据
│   ├── main.py                      # 启动入口
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                        # 前端 (Next.js + Tailwind)
│   └── src/
│       ├── app/
│       │   ├── page.tsx             # 主页面
│       │   ├── diary/               # 🆕 日记页面
│       │   └── mood/                # 🆕 心情页面
│       └── components/
│           ├── VoiceInterface.tsx   # 语音交互
│           ├── DiaryEditor.tsx      # 🆕 日记编辑器
│           └── MoodChart.tsx        # 🆕 心情趋势图
│
├── brain/                           # 🆕 个人知识库（Obsidian 笔记）
│   ├── concepts/                    # 概念笔记
│   ├── daily/                       # 日记 + RSS
│   ├── projects/                    # 项目笔记
│   └── health/                      # 健康知识
│
├── .gitignore
└── README.md
```

---

## 快速启动

### 1. 后端启动

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置 API Key
cp .env.example .env
# 编辑 .env，填入 LLM API Key

# 启动
python main.py
```

后端运行在 **http://localhost:8000**  
API 文档: **http://localhost:8000/docs**

### 2. 前端启动

```bash
cd frontend
npm install
npm run dev
```

前端运行在 **http://localhost:3000**

---

## 架构设计

```
语音/拍照/文字输入 → FastAPI → Agent Orchestrator
                                  ├── 意图识别 (6 种)
                                  ├── 生活助手 Agent → MCP 工具
                                  ├── 健康顾问 Agent → HealthKB (ChromaDB)
                                  ├── 紧急响应 Agent → 通知家属
                                  └── 日记心情 Agent → 日记 CRUD + 心情记录
                                       │
                         ┌─────────────┼─────────────┐
                         ▼             ▼             ▼
                    LLM (Agnes)   RAG 双引擎     语音分析
                                  ┌─ HealthKB      ┌─ 声学特征
                                  └─ PersonalKB    └─ 文本情绪
```

---

## 核心功能

| 功能 | 说明 | 技术 |
|------|------|------|
| 语音办事 | 说一句话，Agent 自动处理 | ASR + Agent + MCP |
| 拍照识物 | 拍药盒/通知 → 大白话解释 | 多模态 LLM + RAG |
| 用药管理 | 记录用药、定时提醒、禁忌检查 | Agent + HealthKB |
| 紧急求助 | 判断紧急程度 → 通知家属 | Agent 决策链 |
| 🆕 日记记录 | 语音/文字写日记，自动存档 | DiaryAgent |
| 🆕 心情分析 | 文本+声学双重分析情绪 | 声学特征 + 关键词 |
| 🆕 知识库检索 | BM25 语义搜索个人笔记 | PersonalKB |
| 🆕 心情趋势 | 周/月度情绪变化统计 | 数据分析 |

---

## LLM 切换

修改 `.env` 中一行即可：

```env
# 使用 Agnes AI（默认）
LLM_PROVIDER=agnes

# 或切换为 DeepSeek
# LLM_PROVIDER=deepseek
# DEEPSEEK_API_KEY=sk-xxx
```

---

## 适老化设计

- **大字体**：最小 20px，正文 24px，标题 32px+
- **慢语速**：TTS 0.8x，音量 1.2x
- **亲切称呼**：「张叔」「李阿姨」
- **确认机制**：重要操作二次确认
- **容错设计**：听不清时友好提示
- **紧急兜底**：异常自动通知家人

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v2.0 | 2026-07 | 合并 my-wiki：个人知识库 + 日记心情 + 语音分析 |
| v1.0 | 2026-07 | 初版：4 Agent + ChromaDB 健康知识库 |
