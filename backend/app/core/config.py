"""
银发守护 — 全局配置
"""
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"


# ============================================================
# LLM Provider 配置
# ============================================================
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "agnes")

# Agnes AI（默认）
AGNES_API_KEY = os.getenv("AGNES_API_KEY", "")
AGNES_API_BASE = os.getenv("AGNES_API_BASE", "https://api.agnes.ai/v1")

# 阿里云通义千问（备选）
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
QWEN_API_BASE = os.getenv("QWEN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# OpenAI（备选）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

# DeepSeek（备选）
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")

# ============================================================
# RAG / 向量数据库
# ============================================================
CHROMA_PERSIST_DIR = str(DATA_DIR / "chroma")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
HF_ENDPOINT = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")

# ============================================================
# 语音配置
# ============================================================
TTS_SPEED = float(os.getenv("TTS_SPEED", "0.8"))      # 适老化：慢语速
TTS_VOLUME = float(os.getenv("TTS_VOLUME", "1.2"))     # 大音量
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "edge")       # edge / aliyun

# ============================================================
# 服务配置
# ============================================================
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
