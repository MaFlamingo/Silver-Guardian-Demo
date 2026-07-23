"""
银发守护 Silver Guardian v2.0 — 后端主入口
=============================================
整合 my-wiki 知识库 + 语音心情分析的适老化智能生活助手

FastAPI 应用 + Agent 编排 + MCP 工具 + 双 RAG 引擎

启动: python main.py
文档: http://localhost:8000/docs
"""
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# 确保项目根目录在 sys.path 中
sys.path.insert(0, str(Path(__file__).resolve().parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("silver-guardian")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import HOST, PORT, DEBUG, CORS_ORIGINS
from app.rag import get_rag


# ----------------------------------------------------------
# 应用生命周期
# ----------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭"""
    logger.info("🛡️  银发守护 Silver Guardian v2.0 启动中...")
    logger.info(f"   LLM Provider: {__import__('app.core.config', fromlist=['']).LLM_PROVIDER}")

    # 初始化双 RAG 引擎
    try:
        rag = await get_rag()
        health_ok = rag.personal._initialized if hasattr(rag, 'personal') else False
        personal_ok = rag.personal._initialized if hasattr(rag, 'personal') else False
        logger.info(f"   Health KB: {'就绪' if health_ok else '降级'} ✅")
        logger.info(f"   Personal KB: {'就绪 ' + str(len(rag.personal.blocks)) + ' 块' if personal_ok else '降级'} ✅")
    except Exception as e:
        logger.warning(f"   RAG 初始化失败 ({e})，降级运行")

    yield

    logger.info("银发守护已关闭")


# ----------------------------------------------------------
# 创建应用
# ----------------------------------------------------------
app = FastAPI(
    title="银发守护 Silver Guardian v2.0",
    description="""基于 Agent + MCP + 双 RAG 引擎 的适老化智能生活助手

## 核心功能
- **生活助手**: 天气查询、提醒设置、生活备忘
- **健康顾问**: 药品查询、饮食建议、急救常识
- **日记心情** 🆕: 日记 CRUD、心情记录与趋势分析
- **个人知识库** 🆕: my-wiki 语义检索 (BM25)
- **紧急响应**: 自动判断紧急程度并通知家属
- **语音交互**: 支持语音输入 + 声学心情分析

## v2.0 新特性
- 合并 my-wiki 个人知识库系统
- 新增日记 + 心情 Agent
- 语音声学特征分析辅助心情判定
- BM25 语义检索引擎（零依赖，开箱即用）
""",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
from app.api.routes import router
app.include_router(router)


# ----------------------------------------------------------
# 根路由
# ----------------------------------------------------------
@app.get("/")
async def root():
    return {
        "name": "银发守护 Silver Guardian v2.0",
        "version": "2.0.0",
        "description": "Agent + MCP + 双 RAG 适老化智能生活助手",
        "docs": "/docs",
        "features": [
            "生活助手 (天气/提醒/备忘)",
            "健康顾问 (药品/饮食/急救)",
            "日记心情 🆕 (CRUD + 趋势分析)",
            "个人知识库 🆕 (BM25 语义检索)",
            "紧急响应 (自动通知家属)",
        ],
    }


# ----------------------------------------------------------
# 启动入口
# ----------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="info",
    )
