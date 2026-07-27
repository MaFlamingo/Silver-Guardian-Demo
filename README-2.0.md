# 银发守护 Silver Guardian v2.0 🛡️

> **Agent + MCP + 双 RAG 引擎** · 适老化智能生活助手  
> 让老年人用「说话 + 拍照」完成数字生活的所有事  
> **v2.0**：合并 llm-wiki 个人知识库与日记心情系统  

---

## 一、这是什么

**银发守护** 是一个面向老年人的多智能体（Multi-Agent）智能助手系统，核心理念是**"说话就能办事，拍照就能看懂"**。老年用户不需要学习复杂的 App 操作，只需像跟人聊天一样说出需求（"今天要下雨吗？""这盒药怎么吃？""帮我记一下明天去医院"），系统背后的 5 个 AI Agent 会自动分工协作，完成天气查询、药品识别、提醒设置、紧急通知，甚至帮忙写日记和感知情绪。

v2.0 合并了开源个人知识库系统 **llm-wiki**，将它的日记、心情分析、语音声学识别和 BM25 语义检索引擎完整纳入，使银发守护从一个"办事工具"升级为"会记日记、懂你心情的 AI 陪伴"。

### 解决的核心痛点

| 痛点 | 银发守护的解法 |
|------|---------------|
| 老年人不会用 App | 语音输入，说一句话即可 |
| 看不懂药品说明书 | 拍照识别 + 大白话解释 |
| 记忆力衰退 | 自动提醒吃药、复诊 |
| 突发健康事件 | 自动判断紧急程度 → 通知家属 |
| 缺少情感陪伴 | 日记记录 + 心情趋势 + 语音情绪感知 |
| 个人信息碎片化 | 个人知识库统一检索（日记、笔记、健康记录） |

### 技术栈一览

| 层级 | 技术 | 说明 |
|------|------|------|
| **后端框架** | FastAPI + Uvicorn | 异步高性能 REST + WebSocket |
| **Agent 编排** | 自研 Orchestrator | 意图识别 → 分发 → 结果整合 |
| **LLM** | Agnes / 通义千问 / DeepSeek / OpenAI | 一行配置切换 |
| **MCP 工具** | 自研 Tool Registry | 天气、药品、提醒、紧急通知 |
| **健康知识库** | ChromaDB + fastembed | 向量语义检索（药品+健康科普） |
| **个人知识库** | BM25 引擎（纯 Python） | 零依赖语义检索，索引 Obsidian 笔记 |
| **语音分析** | wave + struct + math（纯标准库） | 声学特征提取，无第三方依赖 |
| **前端** | Next.js + Tailwind CSS | 大字体高对比度适老化设计 |

---

## 二、功能介绍

### 2.1 六大 Agent，各司其职

```
你说话 →
  Orchestrator 意图识别
    ├─ 🏠 生活助手 Agent     →  "今天上海天气怎么样？"
    ├─ 🏥 健康顾问 Agent     →  "阿莫西林怎么吃？"
    ├─ 🚨 紧急响应 Agent     →  "我头晕站不稳……"
    ├─ 📔 日记心情 Agent 🆕  →  "今天好开心，帮我记下来"
    ├─ 👋 问候闲聊 Agent     →  "小银你好！"
    └─ ❓ 兜底处理 Agent     →  不明确的请求，友好引导
```

### 2.2 功能详情

#### 🏠 生活助手

| 能力 | 触发方式 | 实现 |
|------|----------|------|
| 天气查询 | "今天天气怎么样" / "要不要带伞" | MCP Weather Tool |
| 提醒设置 | "下午3点提醒我吃药" | MCP Reminder Tool |
| 备忘记录 | "帮我记一下明天要买的东西" | Agent 处理 |
| 通讯 | "帮我打给女儿" | 确认后执行 |

#### 🏥 健康顾问

| 能力 | 触发方式 | 实现 |
|------|----------|------|
| 药品查询 | "阿莫西林怎么吃" | HealthKB (ChromaDB 向量检索) |
| 拍照识药 | 上传药盒照片 | 多模态 LLM + RAG |
| 饮食建议 | "血糖高能吃什么" | RAG 健康知识库 |
| 急救常识 | "胸口痛怎么办" | 内置急救知识 |

#### 🚨 紧急响应

触发关键词（头晕 / 站不稳 / 摔倒 / 好痛等）→ 自动评估紧急程度 → 通知紧急联系人。所有回复附带**二次确认**防止误操作。

#### 📔 日记心情 🆕（来自 llm-wiki）

| 能力 | 说明 |
|------|------|
| **写日记** | 语音/文字输入 → 自动存档，带日期和心情标签 |
| **读日记** | 查看某一天的日记，按日期检索 |
| **日记列表** | 按时间倒序展示所有日记 |
| **记心情** | 6 种情绪标签：开心 / 平静 / 低落 / 兴奋 / 焦虑 / 感激 |
| **心情趋势** | 最近 7 天情绪分布统计 + 可视化 |
| **文本情绪分析** | 关键词匹配自动识别文字中的情绪 |
| **语音心情分析** | 🎙️ 从录音中提取 5 维声学特征，辅助判断真实情绪 |

#### 🎙️ 语音心情分析引擎（来自 llm-wiki）

纯 Python 标准库实现（wave + struct + math），**零额外依赖**。从 PCM WAV 录音中提取：

| 声学特征 | 含义 | 与情绪的关联 |
|----------|------|-------------|
| **energy_rms** | 音量/力度 | 高 → 兴奋/激动，低 → 低落/疲惫 |
| **energy_std** | 音量波动 | 大 → 情绪不稳定，小 → 平静 |
| **pitch_zcr** | 过零率（近似音高） | 高 → 紧张/兴奋，低 → 低落/倦怠 |
| **pitch_std** | 语调变化幅度 | 大 → 情绪起伏丰富，小 → 单调冷淡 |
| **speech_rate** | 语速估计 | 快 → 焦虑/兴奋，慢 → 低落/沉思 |

最终与文本情绪**融合判定**，给出综合心情评分。

#### 📚 双 RAG 知识库

| 引擎 | 技术 | 用途 | 来源 |
|------|------|------|------|
| **HealthKB** | ChromaDB + dense embedding | 药品用法、健康科普 | Silver-Guardian 种子数据 |
| **PersonalKB** 🆕 | BM25 稀疏检索（纯 Python） | 个人笔记语义搜索 | llm-wiki brain/ |

BM25 引擎特点：
- 中文采用**字符级 bigram**分词（无需词典）
- 英文按词切分
- 支持 Obsidian 笔记格式（自动跳过 YAML frontmatter）
- 零依赖，开箱即用
- 可选 Ollama embedding 升级为向量模式

---

## 三、项目结构

```
silver-guardian-v2/                     # ← 项目根目录
│
├── .gitignore                          # Git 忽略规则
├── README.md                           # 本文件
│
├── backend/                            # ── 后端 (Python FastAPI) ──
│   ├── main.py                         # 启动入口（uvicorn）
│   ├── requirements.txt                # Python 依赖
│   ├── .env.example                    # 环境变量模板
│   │
│   ├── app/
│   │   ├── agents/                     # ★ Agent 层（5 个 Agent）
│   │   │   ├── __init__.py             # 统一导出
│   │   │   ├── orchestrator.py         # 主控编排器（意图识别 + 分发）
│   │   │   ├── life_assistant.py       # 生活助手：天气/提醒/备忘
│   │   │   ├── health_advisor.py       # 健康顾问：药品/饮食/急救
│   │   │   ├── emergency_responder.py  # 紧急响应：判断+通知
│   │   │   └── diary_agent.py          # 🆕 日记心情：CRUD + 趋势
│   │   │
│   │   ├── core/                       # 核心基础设施
│   │   │   ├── config.py               # 全局配置（LLM/RAG/语音）
│   │   │   ├── llm.py                  # LLM API 封装（多 Provider）
│   │   │   └── theme.py                # 🆕 UI 主题系统
│   │   │
│   │   ├── rag/                        # ★ 双 RAG 引擎
│   │   │   ├── __init__.py             # UnifiedRAG 统一入口
│   │   │   ├── personal_kb.py          # 🆕 llm-wiki BM25 引擎
│   │   │   └── tag_extractor.py        # 🆕 标签提取
│   │   │
│   │   ├── voice/                      # 🆕 语音心情分析
│   │   │   ├── __init__.py             # 声学+文本情绪+融合判定
│   │   │   └── mood_analyzer.py        # 原始 voice_mood.py 备份
│   │   │
│   │   ├── mcp_servers/                # MCP 工具层（4 个服务）
│   │   │   ├── __init__.py             # Tool Registry
│   │   │   ├── weather_server.py       # 天气查询
│   │   │   ├── medicine_server.py      # 药品信息
│   │   │   ├── reminder_server.py      # 提醒服务
│   │   │   └── emergency_server.py     # 紧急通知
│   │   │
│   │   ├── api/
│   │   │   └── routes.py               # 16 条 REST + WebSocket 路由
│   │   │
│   │   └── schemas/
│   │       └── __init__.py             # Pydantic 数据模型（7 个 schema）
│   │
│   └── data/                           # 持久化数据
│       ├── chroma/                     # ChromaDB 向量存储
│       ├── diary/                      # 🆕 日记 JSON 文件
│       ├── mood/                       # 🆕 心情 JSONL 日志
│       └── reminders/                  # 提醒数据
│
├── frontend/                           # ── 前端 (Next.js + Tailwind) ──
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── src/
│       ├── app/
│       │   ├── layout.tsx              # 根布局（适老化大字体）
│       │   ├── page.tsx                # 主对话页面
│       │   ├── globals.css             # 全局样式
│       │   ├── diary/
│       │   │   └── page.tsx            # 🆕 日记页面
│       │   └── mood/
│       │       └── page.tsx            # 🆕 心情页面
│       ├── components/
│       │   ├── VoiceInterface.tsx      # 语音交互组件
│       │   └── ImageRecognition.tsx    # 拍照识别组件
│       └── services/
│           └── api.ts                  # 后端 API 调用封装
│
└── brain/                              # 🆕 个人知识库（Obsidian 笔记）
    ├── concepts/                       # 技术概念笔记
    │   ├── gbrain.md.md                #   分布式训练
    │   ├── llm_wiki.md                 #   LLM 知识库
    │   └── rag_vs_wiki.md              #   RAG vs Wiki 对比
    ├── daily/                          # 日记（56 篇）
    │   ├── 2026-05-22.md ~ 07-05.md    #   日常记录
    │   └── rss/                        #   RSS 抓取存档（24 篇）
    ├── projects/                       # 项目笔记
    │   ├── psvr2-panel.md
    │   ├── stock-crewai.md
    │   └── sanguosha-mobile-updates.md
    ├── people/                         # 人物笔记
    ├── health/                         # 健康知识（可扩展）
    ├── index.md
    ├── readme.md
    └── weekly_review.md
```

### API 路由一览（16 条）

| 方法 | 路径 | 说明 | 来源 |
|------|------|------|------|
| `GET` | `/` | 根路由，返回项目信息 | — |
| `GET` | `/api/v1/health` | 健康检查（双 RAG 状态） | SG |
| `POST` | `/api/v1/chat` | 主对话入口（6 种意图） | SG |
| `POST` | `/api/v1/diary/write` | 🆕 写日记 | llm-wiki |
| `POST` | `/api/v1/diary/read` | 🆕 读日记 | llm-wiki |
| `GET` | `/api/v1/diary/list/{user_id}` | 🆕 日记列表 | llm-wiki |
| `DELETE` | `/api/v1/diary/{user_id}` | 🆕 删除日记 | llm-wiki |
| `POST` | `/api/v1/mood/record` | 🆕 记录心情 | llm-wiki |
| `POST` | `/api/v1/mood/history` | 🆕 心情趋势 | llm-wiki |
| `POST` | `/api/v1/mood/analyze-text` | 🆕 文本情绪分析 | llm-wiki |
| `POST` | `/api/v1/kb/search` | 🆕 个人知识库搜索 | llm-wiki |
| `GET` | `/api/v1/kb/summary` | 🆕 知识库概览 | llm-wiki |
| `GET` | `/api/v1/tools` | MCP 工具列表 | SG |
| `POST` | `/api/v1/reminder` | 设置提醒 | SG |
| `GET` | `/api/v1/reminder/{user_id}` | 获取提醒 | SG |
| `POST` | `/api/v1/medicine/query` | 药品查询 | SG |
| `WS` | `/api/v1/ws/chat/{user_id}` | WebSocket 实时对话 | SG |

---

## 四、运行

### 环境要求

- Python ≥ 3.10
- Node.js ≥ 18
- （可选）Ollama — 用于 PersonalKB 向量升级

### 4.1 后端启动

```bash
cd backend

# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，至少填入 LLM API Key：
#   LLM_PROVIDER=agnes
#   AGNES_API_KEY=sk-xxxxxxxx

# 3. 启动服务
python main.py
```

启动后访问：
- **API 文档**：http://localhost:8000/docs （Swagger UI，可直接在页面试用所有接口）
- **根路由**：http://localhost:8000/

### 4.2 前端启动

```bash
cd frontend

# 1. 安装依赖
npm install

# 2. 启动开发服务器
npm run dev
```

访问 http://localhost:3000 ：
- `/` — 主对话页面（语音 + 拍照）
- `/diary` — 日记页面
- `/mood` — 心情记录与趋势

### 4.3 切换 LLM

只需改 `.env` 中两行：

```env
# DeepSeek
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-xxxxxxxx

# 或通义千问
# LLM_PROVIDER=qwen
# QWEN_API_KEY=sk-xxxxxxxx
```

### 4.4 可选：开启 PersonalKB 向量模式

如果本机运行了 Ollama：

```bash
ollama pull nomic-embed-text
```

然后在 `.env` 中设置：

```env
MYWIKI_RAG_MODE=ollama
MYWIKI_OLLAMA_URL=http://localhost:11434
```

个人知识库将自动从 BM25 切换到向量语义检索，检索精度更高。

---

## 五、后续升级

### 5.1 短期（下一步可做）

| 优先级 | 方向 | 说明 |
|--------|------|------|
| 🔴 高 | **接入真实 TTS / ASR** | 目前语音心情分析是离线模式，需要接入 STT 引擎（如 Whisper）实现端到端语音→文字→心情 |
| 🔴 高 | **用户身份系统** | 当前 user_id 是简单字符串，需要接入 JWT / OAuth 支持多用户独立数据隔离 |
| 🟡 中 | **微信小程序适配** | 根据 README 提及的后续方向，需要 `frontend/adapters/` 多端适配层 |
| 🟡 中 | **多模态识别增强** | 拍照识药目前依赖 LLM 的多模态能力，可用专用模型（如 CLIP）预处理 |
| 🟢 低 | **个人知识库导入** | 支持用户上传 PDF / Markdown 文件自动摄入 PersonalKB |

### 5.2 中期（架构演进）

| 方向 | 说明 |
|------|------|
| **多端适配层** | `frontend/adapters/` 统一接口，支持 AI 眼镜、微信小程序、手机 App 同步接入，Agent 核心逻辑与前端完全解耦 |
| **方言语音识别** | 适老化关键需求：接入粤语、四川话、闽南语等主流方言 STT 引擎 |
| **家属端** | 独立的家属 App / 小程序页面，查看老人健康数据、心情趋势、紧急通知 |
| **RAG 双路融合** | 查询时同时检索 HealthKB + PersonalKB，用 RRF（倒数排名融合）合并排序 |
| **Agent 记忆系统** | 跨会话记忆：记住老人的偏好、常用联系人、常吃药名 |

### 5.3 长期（愿景）

| 方向 | 说明 |
|------|------|
| **社区健康知识共建** | PersonalKB 模型升级为联邦学习，社区老人可以贡献匿名健康数据（经同意）来丰富 HealthKB |
| **可穿戴设备集成** | 对接智能手表 / 健康手环，实时采集心率、血氧生理数据，预警前置 |
| **多语言 + 多文化** | 支持少数民族语言，适老化称呼体系适配不同文化背景 |
| **开源社区运营** | 发布 pip 包 / npm 包，标准化 Agent 接口，吸引社区贡献新的 Agent 和 MCP 工具 |
| **AI 眼镜原生支持** | Agent 输出适配 AR 眼镜信息密度，语音 → 浮窗提示 |

---

### 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v2.0 | 2026-07-23 | 🆕 添加 llm-wiki：PersonalKB + DiaryAgent + Voice Mood |
| v1.0 | 2026-07 | 初版：4 Agent + ChromaDB + Next.js 前端 |

---

*银发守护 — 让科技的温度触及每一位老人* 💝
