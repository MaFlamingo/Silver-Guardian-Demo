"""
银发守护 — 后端主入口
=================================
FastAPI 应用 + Agent 编排 + MCP 工具 + RAG 知识库
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
    logger.info("🛡️  银发守护启动中...")
    logger.info(f"   LLM Provider: {__import__('app.core.config', fromlist=['']).LLM_PROVIDER}")

    # 初始化 RAG
    try:
        rag = await get_rag()
        logger.info("   RAG 知识库: 就绪 ✅")
    except Exception as e:
        logger.warning(f"   RAG 知识库: 初始化失败 ({e})，降级运行")

    yield

    logger.info("银发守护已关闭")


# ----------------------------------------------------------
# 创建应用
# ----------------------------------------------------------
app = FastAPI(
    title="银发守护 Silver Guardian",
    description="基于 Agent + MCP + RAG 的适老化智能生活助手",
    version="1.0.0",
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
        "name": "银发守护 Silver Guardian",
        "version": "1.0.0",
        "description": "适老化智能生活助手",
        "docs": "/docs",
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
