"""
银发守护 v2 — RAG 双引擎知识库
=================================
整合两种 RAG 引擎：
  1. 个人知识库 (PersonalKB) — 来自 my-wiki，BM25 + 可选 Ollama embedding
     索引 brain/ 下的所有 .md 笔记（日记、概念、项目等）
  2. 健康知识库 (HealthKB)  — 原有 ChromaDB 向量检索，药品+健康科普
"""
import os
import logging
from pathlib import Path
from typing import Optional

from app.core.config import (
    CHROMA_PERSIST_DIR, EMBEDDING_MODEL, HF_ENDPOINT,
    PERSONAL_KB_DIR, MYWIKI_RAG_MODE, OLLAMA_URL,
)

logger = logging.getLogger(__name__)

os.environ.setdefault("HF_ENDPOINT", HF_ENDPOINT)


# ═══════════════════════════════════════════════════════════════
# 懒加载 Embedding 模型
# ═══════════════════════════════════════════════════════════════
_embedding_model = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        try:
            from fastembed import TextEmbedding
            _embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL)
            logger.info(f"[RAG] Embedding 模型加载完成: {EMBEDDING_MODEL}")
        except Exception as e:
            logger.warning(f"[RAG] Embedding 模型加载失败 ({e})，将使用关键词匹配降级")
            _embedding_model = False
    return _embedding_model if _embedding_model is not False else None


# ═══════════════════════════════════════════════════════════════
# 药品知识库（种子数据）
# ═══════════════════════════════════════════════════════════════
MEDICINE_KNOWLEDGE = [
    {
        "title": "阿莫西林用药指南",
        "content": "阿莫西林是青霉素类抗生素，用于治疗细菌感染。用法：每次0.5g，每日3次，饭后服用。青霉素过敏者绝对禁用。服药期间不能饮酒。必须按疗程吃完，不能症状好转就停药。",
    },
    {
        "title": "硝苯地平（降压药）注意事项",
        "content": "硝苯地平是钙通道阻滞剂类降压药。用法：每次10mg，每日2-3次。服用期间绝对不能吃柚子或喝柚子汁，会引发严重低血压。不能突然停药，需要逐渐减量。服药后可能头晕，应先坐下休息。",
    },
    {
        "title": "二甲双胍（降糖药）服用须知",
        "content": "二甲双胍是2型糖尿病一线用药。用法：每次0.5g，每日2-3次，饭中或饭后服用。定期检查肾功能很重要。做增强CT检查前需要暂停服药。常见副作用是胃肠道不适，随餐服用可减轻。",
    },
    {
        "title": "阿司匹林抗血小板用法",
        "content": "阿司匹林小剂量用于预防心脑血管疾病。用法：每次100mg，每日1次，饭后服用。有胃溃疡或胃出血史者禁用。不能和其他非甾体抗炎药（如布洛芬）同时服用。手术前需停药至少7天。",
    },
    {
        "title": "布洛芬止痛注意事项",
        "content": "布洛芬是非甾体抗炎止痛药。用法：每次0.2-0.4g，每日不超过2.4g。饭后服用减少胃刺激。有胃病史者慎用。不能和阿司匹林同时服用。不要长期服用超过一周，如疼痛持续应就医。",
    },
    {
        "title": "高血压饮食建议",
        "content": "高血压患者饮食应低盐（每天不超过6g盐）、低脂、高钾。多吃新鲜蔬菜水果，如芹菜、菠菜、香蕉。少吃腌制食品和加工肉制品。戒烟限酒，保持情绪稳定。适量运动如散步、太极。",
    },
    {
        "title": "糖尿病饮食原则",
        "content": "糖尿病人应控制主食量，每餐主食不超过2两（生重）。优先选择粗粮如燕麦、糙米。少吃甜食和含糖饮料。多吃绿叶蔬菜。水果在两餐之间吃，一次不超过拳头大小。定时定量进餐。",
    },
    {
        "title": "老年人跌倒预防",
        "content": "预防老年人跌倒的关键：家里保持光线充足，地面不滑，不堆放杂物。浴室铺防滑垫，马桶旁装扶手。鞋子要防滑合脚。起床时要慢，先坐一会再站。视力听力有问题及时矫正。",
    },
    {
        "title": "急救常识：突发胸痛怎么办",
        "content": "突发胸痛时：立即停止活动，坐下或半卧。如果怀疑心肌梗死，立即拨打120。如有医生开的硝酸甘油，按医嘱舌下含服。不要自己开车去医院。保持冷静，解开领口和腰带。",
    },
    {
        "title": "急救常识：老人摔倒处理",
        "content": "发现老人摔倒：先不要急着扶起来。检查是否有意识，有无骨折（尤其髋部）。如果怀疑骨折，不要移动，立即拨打120。如果没有骨折，让老人慢慢翻身侧卧，再扶着坐起。",
    },
]


# ═══════════════════════════════════════════════════════════════
# HealthKB — 健康知识库 (ChromaDB)
# ═══════════════════════════════════════════════════════════════
class HealthKB:
    """健康知识库：基于 ChromaDB 的向量检索"""

    def __init__(self, collection_name: str = "silver_guardian_health"):
        self.collection_name = collection_name
        self._collection = None
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            Path(CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
            self._chroma_client = chromadb.PersistentClient(
                path=CHROMA_PERSIST_DIR,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            try:
                self._collection = self._chroma_client.get_collection(self.collection_name)
                count = self._collection.count()
                logger.info(f"[HealthKB] 已有知识库: {count} 条")
            except Exception:
                self._collection = self._chroma_client.create_collection(self.collection_name)
                count = 0
            if count == 0:
                await self._import_seed_data()
            self._initialized = True
        except Exception as e:
            logger.warning(f"[HealthKB] ChromaDB 初始化失败 ({e})，降级关键词匹配")
            self._initialized = True

    async def _import_seed_data(self):
        model = _get_embedding_model()
        if model is None or self._collection is None:
            return
        ids = [f"doc_{i}" for i in range(len(MEDICINE_KNOWLEDGE))]
        documents = [doc["content"] for doc in MEDICINE_KNOWLEDGE]
        metadatas = [{"title": doc["title"]} for doc in MEDICINE_KNOWLEDGE]
        embeddings = list(model.embed(documents))
        self._collection.add(
            ids=ids,
            embeddings=[emb.tolist() for emb in embeddings],
            documents=documents,
            metadatas=metadatas,
        )

    async def search(self, query: str, top_k: int = 3) -> list[str]:
        try:
            if self._collection is not None:
                model = _get_embedding_model()
                if model is not None:
                    query_embedding = list(model.embed([query]))[0]
                    results = self._collection.query(
                        query_embeddings=[query_embedding.tolist()],
                        n_results=min(top_k, 10),
                    )
                    documents = results.get("documents", [[]])[0]
                    if documents:
                        return documents
        except Exception as e:
            logger.warning(f"[HealthKB] 向量检索失败: {e}")
        return self._keyword_search(query, top_k)

    def _keyword_search(self, query: str, top_k: int = 3) -> list[str]:
        scored = []
        for doc in MEDICINE_KNOWLEDGE:
            content = doc["content"] + doc["title"]
            score = sum(1 for word in query if word in content)
            if score > 0:
                scored.append((score, doc["content"]))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]

    async def augment_prompt(self, query: str) -> str:
        docs = await self.search(query)
        if not docs:
            return ""
        context = "\n\n---\n\n".join(docs)
        return f"""以下是与健康/药品相关的知识，请参考这些信息回答问题（用大白话）：

{context}

注意：以上知识仅供参考，回答时记得加一句"最好再问问医生"。
"""


# ═══════════════════════════════════════════════════════════════
# PersonalKB — 个人知识库 (来自 my-wiki，BM25 引擎)
# ═══════════════════════════════════════════════════════════════
class PersonalKB:
    """个人知识库：索引 brain/ 中的 Obsidian 笔记"""

    CATEGORIES = ["concepts", "daily", "projects", "people", "health"]
    SKIP_DIRS = {".obsidian", ".git", "__pycache__", "node_modules", ".trash"}

    def __init__(self, kb_dir: str = None):
        self.root = Path(kb_dir) if kb_dir else Path(PERSONAL_KB_DIR)
        self.blocks = []
        self.df = {}
        self.N = 0
        self.avgdl = 0.0
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        self._index()
        self._initialized = True
        logger.info(f"[PersonalKB] 已索引 {len(self.blocks)} 个知识块，来自 {self.root}")

    def _tokenize(self, text: str):
        """中英混合分词：英文按词，中文按字符 bigram"""
        import re
        text = (text or "").lower()
        tokens = []
        for m in re.findall(r"[a-z0-9]+", text):
            if len(m) > 1:
                tokens.append(m)
        for seg in re.findall(r"[一-鿿]+", text):
            if len(seg) == 1:
                tokens.append("c:" + seg)
            else:
                for i in range(len(seg) - 1):
                    tokens.append("c:" + seg[i:i + 2])
        return tokens

    def _chunk_text(self, text: str, max_chars: int = 600):
        lines = text.splitlines()
        blocks, cur, cur_len = [], [], 0
        for ln in lines:
            cur.append(ln)
            cur_len += len(ln) + 1
            if cur_len >= max_chars and (ln.strip() == "" or ln.startswith("#")):
                joined = "\n".join(cur).strip()
                if joined:
                    blocks.append(joined)
                cur, cur_len = [], 0
        if cur:
            joined = "\n".join(cur).strip()
            if joined:
                blocks.append(joined)
        return [b for b in blocks if len(b) > 20]

    def _index(self):
        import re
        blocks = []
        for cat in self.CATEGORIES:
            root = self.root / cat
            if not root.exists():
                continue
            for f in root.rglob("*.md"):
                if any(part in self.SKIP_DIRS for part in f.parts):
                    continue
                rel = f.relative_to(self.root).as_posix() if self.root in f.parents else f.name
                try:
                    text = f.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                m = re.match(r"^---\s*\n.*?\n---\s*\n?", text, re.DOTALL)
                body = text[m.end():] if m else text
                title = f.stem.replace("_", " ")
                for b in self._chunk_text(body):
                    toks = self._tokenize(b)
                    tf = {}
                    for t in toks:
                        tf[t] = tf.get(t, 0) + 1
                    blocks.append({
                        "rel": rel,
                        "title": title,
                        "text": b,
                        "tf": tf,
                        "dl": len(toks),
                    })
        self.blocks = blocks
        self.N = len(blocks)
        df = {}
        for b in blocks:
            for t in b["tf"]:
                df[t] = df.get(t, 0) + 1
        self.df = df
        self.avgdl = (sum(b["dl"] for b in blocks) / self.N) if self.N else 0

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        import math
        q_tokens = self._tokenize(query)
        k1, b_param = 1.5, 0.75
        scored = []
        for blk in self.blocks:
            score = 0.0
            for qt in set(q_tokens):
                tf = blk["tf"].get(qt)
                if not tf:
                    continue
                df_t = self.df.get(qt, 0)
                idf = math.log((self.N - df_t + 0.5) / (df_t + 0.5) + 1)
                score += idf * (tf * (k1 + 1)) / (
                    tf + k1 * (1 - b_param + b_param * blk["dl"] / self.avgdl)
                )
            if score > 0:
                scored.append((score, blk))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{
            "file": blk["rel"],
            "title": blk["title"],
            "score": round(s, 4),
            "snippet": blk["text"][:200].replace("\n", " ") + ("..." if len(blk["text"]) > 200 else ""),
            "content": blk["text"],
        } for s, blk in scored[:top_k]]

    def get_all_entries_summary(self) -> dict:
        """获取知识库概览"""
        files = set(b["rel"] for b in self.blocks)
        return {
            "total_blocks": len(self.blocks),
            "total_files": len(files),
            "categories": self.CATEGORIES,
            "kb_root": str(self.root),
        }


# ═══════════════════════════════════════════════════════════════
# 统一 RAG 入口
# ═══════════════════════════════════════════════════════════════
class UnifiedRAG:
    """统一 RAG 入口：同时查健康知识库 + 个人知识库"""

    def __init__(self):
        self.health = HealthKB()
        self.personal = PersonalKB()
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        await self.health.initialize()
        await self.personal.initialize()
        self._initialized = True

    async def search_health(self, query: str, top_k: int = 3) -> list[str]:
        await self.initialize()
        return await self.health.search(query, top_k)

    def search_personal(self, query: str, top_k: int = 5) -> list[dict]:
        return self.personal.search(query, top_k)

    async def augment_prompt(self, query: str) -> str:
        """为 LLM 生成增强提示"""
        await self.initialize()
        return await self.health.augment_prompt(query)

    def personal_summary(self) -> dict:
        return self.personal.get_all_entries_summary()


# 全局单例
_rag_instance: Optional[UnifiedRAG] = None


async def get_rag() -> UnifiedRAG:
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = UnifiedRAG()
        await _rag_instance.initialize()
    return _rag_instance
