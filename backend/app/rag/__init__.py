"""
银发守护 — RAG 知识库系统
=================================
基于 ChromaDB 的本地向量检索，支持药品知识库和健康科普库。

设计原则：
  - 懒加载：Embedding 模型在首次使用时下载，不在 import 时阻塞
  - 降级策略：ChromaDB 不可用时降级为关键词匹配
"""

import os
import logging
from pathlib import Path
from typing import Optional

from app.core.config import CHROMA_PERSIST_DIR, EMBEDDING_MODEL, HF_ENDPOINT

logger = logging.getLogger(__name__)

os.environ.setdefault("HF_ENDPOINT", HF_ENDPOINT)

# 懒加载的 Embedding 模型
_embedding_model = None


def _get_embedding_model():
    """懒加载 Embedding 模型（使用 fastembed，避免 sentence-transformers 版本冲突）"""
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


# ============================================================
# 药品知识库（内置文本，同时作为 ChromaDB 的种子数据）
# ============================================================
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


class RAGSystem:
    """RAG 检索增强生成系统"""

    def __init__(self, collection_name: str = "silver_guardian_kb"):
        self.collection_name = collection_name
        self._collection = None
        self._initialized = False

    # ----------------------------------------------------------
    # 初始化
    # ----------------------------------------------------------
    async def initialize(self):
        """初始化向量数据库和知识库"""
        if self._initialized:
            return

        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            # 创建 ChromaDB 客户端（本地持久化）
            Path(CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
            self._chroma_client = chromadb.PersistentClient(
                path=CHROMA_PERSIST_DIR,
                settings=ChromaSettings(anonymized_telemetry=False),
            )

            # 获取或创建 collection
            try:
                self._collection = self._chroma_client.get_collection(self.collection_name)
                count = self._collection.count()
                logger.info(f"[RAG] 已有知识库: {count} 条记录")
            except Exception:
                self._collection = self._chroma_client.create_collection(self.collection_name)
                count = 0

            # 如果是空的，导入种子数据
            if count == 0:
                await self._import_seed_data()
                logger.info(f"[RAG] 种子数据已导入")

            self._initialized = True
        except Exception as e:
            logger.warning(f"[RAG] ChromaDB 初始化失败 ({e})，将使用关键词匹配降级")
            self._initialized = True  # 标记为已初始化，后续降级处理

    async def _import_seed_data(self):
        """导入种子知识到向量库"""
        model = _get_embedding_model()
        if model is None or self._collection is None:
            return

        ids = [f"doc_{i}" for i in range(len(MEDICINE_KNOWLEDGE))]
        documents = [doc["content"] for doc in MEDICINE_KNOWLEDGE]
        metadatas = [{"title": doc["title"]} for doc in MEDICINE_KNOWLEDGE]

        # 批量生成 embedding
        embeddings = list(model.embed(documents))

        self._collection.add(
            ids=ids,
            embeddings=[emb.tolist() for emb in embeddings],
            documents=documents,
            metadatas=metadatas,
        )

    # ----------------------------------------------------------
    # 检索
    # ----------------------------------------------------------
    async def search(self, query: str, top_k: int = 3) -> list[str]:
        """检索相关文档

        Args:
            query: 用户问题
            top_k: 返回的文档数

        Returns:
            相关文档内容列表
        """
        # 尝试向量检索
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
                        logger.debug(f"[RAG] 向量检索返回 {len(documents)} 条结果")
                        return documents
        except Exception as e:
            logger.warning(f"[RAG] 向量检索失败: {e}")

        # 降级：关键词匹配
        return self._keyword_search(query, top_k)

    def _keyword_search(self, query: str, top_k: int = 3) -> list[str]:
        """关键词匹配降级检索"""
        scored = []
        for doc in MEDICINE_KNOWLEDGE:
            content = doc["content"] + doc["title"]
            # 简单计分：匹配到的关键词数量
            score = sum(1 for word in query if word in content)
            if score > 0:
                scored.append((score, doc["content"]))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]

    async def augment_prompt(self, query: str) -> str:
        """生成增强后的提示词（RAG 上下文化）"""
        docs = await self.search(query)
        if not docs:
            return ""

        context = "\n\n---\n\n".join(docs)
        return f"""以下是相关的健康/药品知识，请参考这些信息回答问题（用大白话）：

{context}

注意：以上知识仅供参考，回答时记得加一句"最好再问问医生"。
"""


# 全局单例
_rag_instance: Optional[RAGSystem] = None


async def get_rag() -> RAGSystem:
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGSystem()
        await _rag_instance.initialize()
    return _rag_instance
