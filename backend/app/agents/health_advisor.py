"""
银发守护 — 健康顾问 Agent
处理：用药咨询、健康问答、拍照识药、饮食建议
"""

from __future__ import annotations

import logging
from app.core.llm import get_llm_client
from app.mcp_servers.medicine_server import MedicineTool, _KNOWN_MEDICINES

logger = logging.getLogger(__name__)


class HealthAdvisorAgent:
    """健康顾问 Agent — 支持 LLM 在线 + 本地知识库离线双模式"""

    SYSTEM_PROMPT = """你是"小银"的健康顾问，也是一位有经验的健康助手。
你能帮用户：
- 看药品照片，告诉用户这是什么药、怎么吃、注意什么
- 回答健康问题（饮食、运动、常见症状）
- 检查用药禁忌

重要原则：
- 用大白话解释，不要用医学术语
- 最后总是加一句"最好再问问医生"
- 不说绝对的话（"一定"、"保证"），用"建议"、"可能"
- 不诊断疾病，只提供参考信息"""

    MEDICINE_PHOTO_PROMPT = """用户拍了一张药品照片。请识别以下信息并以 JSON 格式返回：
{
  "medicine_name": "药品名称",
  "usage": "用法用量（大白话）",
  "warnings": ["禁忌事项1", "禁忌事项2"],
  "explanation": "给老人的大白话解释"
}

如果图片不是药品，返回 {"error": "not_medicine", "explanation": "..."}
如果无法识别，返回 {"error": "unrecognizable", "explanation": "..."}"""

    _LLM_DOWN_MARKERS = ["服务异常", "暂时无法", "服务暂不可用"]

    def __init__(self):
        self.llm = get_llm_client()
        self.medicine_tool = MedicineTool()

    @staticmethod
    def _is_llm_down(text: str) -> bool:
        return any(m in text for m in HealthAdvisorAgent._LLM_DOWN_MARKERS)

    # ----------------------------------------------------------
    # 主入口
    # ----------------------------------------------------------
    async def handle(self, user_input: str, ctx, image_url: str = None) -> dict:
        if image_url:
            return await self._handle_medicine_photo(user_input, ctx, image_url)
        if self._is_medicine_query(user_input):
            return await self._handle_medicine_query(user_input, ctx)
        return await self._handle_health_qa(user_input, ctx)

    def _is_medicine_query(self, text: str) -> bool:
        keywords = ["药", "吃药", "用量", "禁忌", "副作用", "能不能一起吃"]
        if any(kw in text for kw in keywords):
            return True
        # 也匹配已知药名（如"阿莫西林怎么吃"）
        return any(name in text for name in _KNOWN_MEDICINES)

    # ----------------------------------------------------------
    # 拍照识药（LLM vision + 离线兜底）
    # ----------------------------------------------------------
    async def _handle_medicine_photo(self, user_input: str, ctx, image_url: str) -> dict:
        vision_reply = None
        med_name = None

        # Step 1: 尝试 LLM 多模态识别
        try:
            vision_reply = await self.llm.chat_with_image(
                user_message="请识别图片中的药品，给出名称、用法用量、禁忌事项",
                image_url=image_url,
                system_prompt="你是药品识别助手。仔细识别图片中的药品信息。",
                temperature=0.2,
            )
        except Exception as e:
            logger.warning(f"[HealthAgent] LLM vision 异常: {e}")

        # Step 2: LLM 在线 → 正常流程
        if vision_reply and not self._is_llm_down(vision_reply):
            try:
                structured = await self.llm.chat_json(
                    user_message=f"药品识别结果：{vision_reply}\n请提取 JSON",
                    system_prompt=self.MEDICINE_PHOTO_PROMPT,
                    temperature=0.2,
                )
                med_name = structured.get("medicine_name", "")
            except Exception:
                pass

            reply = await self.llm.chat(
                user_message=f"药品识别结果：{vision_reply}\n请用大白话给老人({ctx.name})解释，记得加一句'最好再问问医生'。",
                system_prompt=self.SYSTEM_PROMPT,
            )

            # 本地库增强
            if med_name:
                local = await self.medicine_tool.query(med_name)
                if local["found"] and not self._is_llm_down(reply):
                    reply += f"\n\n📋 本地药品库确认：\n{local['message']}"

            return {
                "reply": reply,
                "action": "medicine_photo",
                "medicine_info": {"vision_raw": vision_reply, "extracted_name": med_name},
            }

        # Step 3: LLM 不可用 → 离线引导
        return self._offline_photo_fallback(ctx, med_name)

    def _offline_photo_fallback(self, ctx, med_name: str | None) -> dict:
        known = list(_KNOWN_MEDICINES.keys())
        drug_list = "、".join(known)

        if med_name:
            local = self.medicine_tool.query_sync(med_name) if hasattr(self.medicine_tool, "query_sync") else None
            if local and local.get("found"):
                return {
                    "reply": f"{ctx.name}，我看了一下，这应该是「{med_name}」。\n\n{local['message']}\n\n⚠️ 当前 AI 服务暂未连接，以上信息来自本地药品库。最好再问问医生。",
                    "action": "medicine_photo_offline",
                    "medicine_info": local.get("info"),
                }

        return {
            "reply": (
                f"{ctx.name}，我暂时看不清这张照片（AI 服务还没连上）。\n\n"
                f"不过没关系！您可以打字告诉我药名，我认识这些常见药：\n"
                f"📋 {drug_list}\n\n"
                f"直接敲药名就能查用法和禁忌。"
            ),
            "action": "medicine_photo_offline",
            "medicine_info": {"available_drugs": known},
        }

    # ----------------------------------------------------------
    # 用药咨询（LLM + 本地库兜底）
    # ----------------------------------------------------------
    async def _handle_medicine_query(self, user_input: str, ctx) -> dict:
        med_name = self._extract_medicine_name(user_input)
        local_info = None
        if med_name:
            local = await self.medicine_tool.query(med_name)
            if local["found"]:
                local_info = local["message"]

        try:
            reply = await self.llm.chat(
                user_message=f"用户({ctx.name})问：{user_input}\n本地参考：{local_info or '无'}",
                system_prompt=self.SYSTEM_PROMPT,
            )
            if not self._is_llm_down(reply):
                return {"reply": reply, "action": "medicine_qa"}
        except Exception:
            pass

        if local_info:
            return {
                "reply": f"{ctx.name}，我帮您查了一下：\n\n{local_info}\n\n⚠️ AI 服务暂未连接，以上信息来自本地药品库。最好再问问医生。",
                "action": "medicine_qa_offline",
            }
        return {
            "reply": f"{ctx.name}，我暂时查不到这个药的信息。您可以试试直接告诉我药名（比如'阿莫西林'），或者问医生。",
            "action": "medicine_qa_offline",
        }

    # ----------------------------------------------------------
    # 健康问答（LLM + RAG 兜底）
    # ----------------------------------------------------------
    async def _handle_health_qa(self, user_input: str, ctx) -> dict:
        try:
            reply = await self.llm.chat(
                user_message=f"用户({ctx.name}，{ctx.age}岁)问：{user_input}",
                system_prompt=self.SYSTEM_PROMPT,
            )
            if not self._is_llm_down(reply):
                return {"reply": reply, "action": "health_qa"}
        except Exception:
            pass

        try:
            from app.rag import get_rag
            rag = await get_rag()
            docs = await rag.search(user_input, top_k=2)
            if docs:
                knowledge = "\n\n".join(docs)
                return {
                    "reply": f"{ctx.name}，我在知识库里找到一些参考信息：\n\n{knowledge[:500]}\n\n⚠️ AI 服务暂未连接，以上来自本地知识库，仅供参考。最好再问问医生。",
                    "action": "health_qa_offline",
                }
        except Exception:
            pass

        return {
            "reply": f"{ctx.name}，我暂时回答不了这个问题（AI 服务还没连上）。不过别担心，您可以问问身边家人，或者直接去看医生最放心。",
            "action": "health_qa_offline",
        }

    # ----------------------------------------------------------
    # 工具
    # ----------------------------------------------------------
    @staticmethod
    def _extract_medicine_name(text: str) -> str | None:
        known = _KNOWN_MEDICINES
        for name in known:
            if name in text:
                return name
        return None
