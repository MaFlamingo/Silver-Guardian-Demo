"""
银发守护 — 紧急响应 Agent
处理：紧急求助、异常检测、通知家属
"""

import logging
from app.core.llm import get_llm_client

logger = logging.getLogger(__name__)


class EmergencyResponderAgent:
    """紧急响应 Agent

    流程：
      1. 判断紧急程度：轻度不适 / 需要关注 / 紧急
      2. 轻度 → 安抚 + 建议
      3. 中度 → 询问是否需要通知家人
      4. 紧急 → 立即通知 + 引导
    """

    SYSTEM_PROMPT = """你是"小银"的紧急响应助手。当老人说身体不舒服时，你需要：
1. 先判断情况有多紧急（不紧急 / 有点严重 / 非常紧急）
2. 用冷静、清晰的语气引导老人，不要慌张
3. "非常紧急"时：直接说"我已经通知您儿子了"，然后引导老人保持安全姿势
4. "有点严重"时：先安抚，然后问是否需要联系家人
5. "不紧急"时：给出简单建议，提醒注意观察

判断标准：
- 非常紧急：头晕站不稳、摔倒、胸痛、呼吸困难、说不了话
- 有点严重：持续疼痛、发烧、吃错药、行动不便
- 不紧急：轻微不适、心情不好、想问问题"""

    URGENCY_PROMPT = """分析用户的描述，判断紧急程度。只返回 JSON：
{
  "urgency": "low|medium|high",
  "possible_cause": "可能的原因（简短）",
  "immediate_action": "建议立即采取的行动"
}"""

    def __init__(self):
        self.llm = get_llm_client()

    async def handle(self, user_input: str, ctx) -> dict:
        """处理紧急请求"""
        # Step 1: 判断紧急程度
        try:
            urgency_result = await self.llm.chat_json(
                user_message=f"用户说：{user_input}\n用户年龄：{ctx.age}岁\n病史：{', '.join(ctx.medical_history) if ctx.medical_history else '未知'}",
                system_prompt=self.URGENCY_PROMPT,
                temperature=0.1,
            )
        except Exception as e:
            logger.error(f"[Emergency] 判断紧急程度失败: {e}")
            urgency_result = {"urgency": "medium", "possible_cause": "未知", "immediate_action": "尽快联系家人或拨打120"}

        urgency = urgency_result.get("urgency", "medium")

        # Step 2: 根据紧急程度生成回复
        if urgency == "high":
            reply = await self._handle_high_urgency(user_input, ctx, urgency_result)
            return {
                "reply": reply,
                "action": "emergency_high",
                "urgency": "high",
                "notify_family": True,
                "need_confirm": False,
            }
        elif urgency == "medium":
            reply = await self._handle_medium_urgency(user_input, ctx, urgency_result)
            return {
                "reply": reply,
                "action": "emergency_medium",
                "urgency": "medium",
                "need_confirm": True,
            }
        else:
            reply = await self._handle_low_urgency(user_input, ctx, urgency_result)
            return {
                "reply": reply,
                "action": "emergency_low",
                "urgency": "low",
                "need_confirm": False,
            }

    async def _handle_high_urgency(self, user_input: str, ctx, urgency: dict) -> str:
        """高度紧急"""
        contact_info = f"紧急联系人：{ctx.emergency_contact} ({ctx.emergency_phone})" if ctx.emergency_phone else ""
        reply = await self.llm.chat(
            user_message=user_input,
            system_prompt=f"""{self.SYSTEM_PROMPT}
这是紧急情况！用户：{ctx.name}，{ctx.age}岁。
{contact_info}
直接告知用户：已经通知家人，引导用户保持安全姿势，询问是否要叫120。""",
            temperature=0.5,
        )
        return reply

    async def _handle_medium_urgency(self, user_input: str, ctx, urgency: dict) -> str:
        """中度紧急"""
        reply = await self.llm.chat(
            user_message=user_input,
            system_prompt=f"""{self.SYSTEM_PROMPT}
情况有点严重但不致命。先安抚用户{ctx.name}，然后询问是否需要帮ta联系家人或叫120。
给出可能的建议：{urgency.get('immediate_action', '休息观察')}""",
            temperature=0.6,
        )
        return reply

    async def _handle_low_urgency(self, user_input: str, ctx, urgency: dict) -> str:
        """不紧急"""
        reply = await self.llm.chat(
            user_message=user_input,
            system_prompt=f"""{self.SYSTEM_PROMPT}
情况不紧急。给用户{ctx.name}一些简单的建议，提醒注意观察。
可以建议：{urgency.get('immediate_action', '休息一下')}""",
            temperature=0.7,
        )
        return reply
