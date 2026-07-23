"""
银发守护 Silver Guardian v2.0 — 全局配置
合并 my-wiki 知识库 + 语音心情分析
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

AGNES_API_KEY = os.getenv("AGNES_API_KEY", "")
AGNES_API_BASE = os.getenv("AGNES_API_BASE", "https://api.agnes.ai/v1")

QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
QWEN_API_BASE = os.getenv("QWEN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")

# ============================================================
# RAG / 向量数据库 — 双引擎
# ============================================================
CHROMA_PERSIST_DIR = str(DATA_DIR / "chroma")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
HF_ENDPOINT = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")

# 🆕 个人知识库（来自 my-wiki）
PERSONAL_KB_DIR = str(PROJECT_ROOT.parent / "brain")
OLLAMA_URL = os.getenv("MYWIKI_OLLAMA_URL", "http://localhost:11434")
MYWIKI_RAG_MODE = os.getenv("MYWIKI_RAG_MODE", "bm25")  # bm25 / ollama

# ============================================================
# 语音配置
# ============================================================
TTS_SPEED = float(os.getenv("TTS_SPEED", "0.8"))
TTS_VOLUME = float(os.getenv("TTS_VOLUME", "1.2"))
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "edge")

# 🆕 语音心情分析
VOICE_LANG = os.getenv("VOICE_LANG", "zh-CN")
VOICE_MAX_SECONDS = int(os.getenv("VOICE_MAX_SECONDS", "12"))

# ============================================================
# 日记 / 心情配置
# ============================================================
DIARY_DATA_DIR = str(DATA_DIR / "diary")
MOOD_DATA_DIR = str(DATA_DIR / "mood")
REPO_DATA_DIR = str(PROJECT_ROOT.parent / "brain")

# ============================================================
# 服务配置
# ============================================================
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
