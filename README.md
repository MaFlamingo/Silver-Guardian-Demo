# 银发守护 Silver Guardian(Demo)

> 基于 **Agent + MCP + RAG** 的适老化智能生活助手  
> 让老年人用「说话 + 拍照」就能完成数字生活中的所有事

---

## 项目结构

```
银发守护/
├── backend/                    # 后端服务 (FastAPI + LangGraph)
│   ├── app/
│   │   ├── core/
│   │   │   ├── llm.py         # ★ LLM API 独立封装层 (Agnes/Qwen/OpenAI/DeepSeek)
│   │   │   └── config.py      # 全局配置
│   │   ├── agents/
│   │   │   ├── orchestrator.py      # Agent 主控编排器
│   │   │   ├── life_assistant.py    # 生活助手 Agent
│   │   │   ├── health_advisor.py    # 健康顾问 Agent
│   │   │   └── emergency_responder.py # 紧急响应 Agent
│   │   ├── mcp_servers/
│   │   │   ├── weather_server.py    # 天气查询 MCP
│   │   │   ├── medicine_server.py   # 药品信息 MCP
│   │   │   ├── reminder_server.py   # 提醒服务 MCP
│   │   │   └── emergency_server.py  # 紧急通知 MCP
│   │   ├── rag/                # RAG 知识库 (ChromaDB)
│   │   ├── api/routes.py       # REST + WebSocket API
│   │   └── schemas/            # Pydantic 数据模型
│   ├── data/                   # 持久化数据目录
│   ├── main.py                 # 启动入口
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                   # 前端应用 (Next.js + Tailwind CSS)
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx      # 根布局 (适老化样式)
│   │   │   ├── page.tsx        # 主页面
│   │   │   └── globals.css     # 全局样式 (大字体高对比度)
│   │   ├── components/
│   │   │   ├── VoiceInterface.tsx     # 语音交互组件
│   │   │   └── ImageRecognition.tsx   # 拍照识别组件
│   │   └── services/
│   │       └── api.ts          # API 调用 + WebSocket
│   ├── package.json
│   ├── tailwind.config.js
│   └── next.config.js
│
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
# 编辑 .env，填入 AGNES_API_KEY=你的密钥

# 启动
python main.py
```

后端运行在 **http://localhost:8000**  
API 文档: **http://localhost:8000/docs**

### 2. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端运行在 **http://localhost:3000**

---

## LLM API 封装说明

LLM 客户端在 `backend/app/core/llm.py` 中**独立封装**，支持多 Provider 切换：

```python
from app.core.llm import get_llm_client

client = get_llm_client()  # 自动读取 .env 中的 LLM_PROVIDER

# 文本对话
reply = await client.chat("你好")

# JSON 结构化输出
result = await client.chat_json("提取姓名和年龄", ...)

# 图片理解
desc = await client.chat_with_image("这是什么？", image_url="...")

# 流式对话
async for chunk in client.chat_stream("讲个故事"):
    print(chunk, end="")
```

切换 Provider 只需修改 `.env` 中一行：

```env
# 使用 Agnes AI (默认)
LLM_PROVIDER=agnes
AGNES_API_KEY=sk-xxx

# 切换为通义千问
# LLM_PROVIDER=qwen
# QWEN_API_KEY=sk-xxx

# 切换为 OpenAI
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-xxx
```

---

## 架构设计

```
语音/拍照输入 → FastAPI → Agent Orchestrator
                              ├── 意图识别
                              ├── 生活助手 Agent
                              ├── 健康顾问 Agent
                              └── 紧急响应 Agent
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
               MCP 工具层      RAG 知识库      LLM (Agnes)
               (天气/药品/     (ChromaDB)     (独立封装)
                提醒/通知)
```

---

## 核心功能

|  功能 | 说明  |  技术 |
|---|---|---|
| 语音办事 | 说一句话，Agent 自动处理 | ASR + Agent + MCP  |
| 拍照识物 | 拍药盒/通知 → 大白话解释 | 多模态 LLM + RAG  |
| 用药管理 | 记录用药、定时提醒、禁忌检查 | Agent + 药品知识库  |
| 紧急求助  | 判断紧急程度 → 通知家属 | Agent 决策链  |
| 亲情连线  | 语音控制拨号/发消息 | MCP 通讯录  |
| 健康问答  | 饮食运动咨询 | RAG 健康知识库  |

---

## 适老化设计

- **大字体**：最小 20px，正文 24px，标题 32px+
- **慢语速**：TTS 0.8x，音量 1.2x
- **亲切称呼**：「张 叔」「李阿姨」
- **确认机制**：重要操作二次确认
- **容错设计**：听不清时友好提示
- **紧急兜底**：异常自动通知家人

## 后续说明
1. 模型统一封装规范：需要添加一个专门识别图片和语音的大模型，并且每个大模型都分别封装
2. 平台适配：ai眼镜、微信小程序、手机app。
Agent 核心逻辑必须与前端展示完全解耦； frontend/adapters/ 中为不同终端提供统一的接入接口；
3. 适老化：语音识别要精通各地方方言。# Silver-Guardian-Demo
