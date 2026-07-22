# 银发守护 — Agent 编排层
# 主控 Orchestrator：意图识别 → 任务分发 → 结果整合 → 回复生成

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from app.core.llm import get_llm_client, LLMClient
from app.agents.life_assistant import LifeAssistantAgent
from app.agents.health_advisor import HealthAdvisorAgent
from app.agents.emergency_responder import EmergencyResponderAgent

logger = logging.getLogger(__name__)


class Intent(str, Enum):
    """意图分类"""
    LIFE = "life"               # 生活助手：天气、日历、通讯、备忘
    HEALTH = "health"           # 健康顾问：用药、饮食、问答
    MEDICINE_PHOTO = "medicine_photo"  # 拍照识药
    EMERGENCY = "emergency"     # 紧急求助
    GREETING = "greeting"       # 寒暄/闲聊
    UNKNOWN = "unknown"         # 不明确


@dataclass
class UserContext:
    """用户上下文"""
    user_id: str
    name: str = "张叔"  # 默认称呼
    age: int = 70
    medical_history: list[str] = field(default_factory=list)
    medications: list[str] = field(default_factory=list)
    emergency_contact: str = ""
    emergency_phone: str = ""


class AgentOrchestrator:
    """Agent 主控编排器

    流程：
      1. 意图识别 → 判断用户想要什么
      2. 任务分发 → 交给对应的子 Agent
      3. 结果整合 → 适老化包装输出
    """

    # --- 适老化系统提示词 ---
    SYSTEM_PROMPT = """你是"小银"，一位专为老年人设计的AI生活助手。
你的说话风格：
- 称呼用户为"张叔"或"李阿姨"（根据上下文），语气亲切自然
- 用大白话解释，不用专业术语
- 字字清晰，句子简短，每句话一个意思
- 重要信息会重复一遍确认
- 听不清时会友好地让用户再说一遍
- 涉及健康问题时，总是建议"最好再问问医生"作为兜底"""

    INTENT_PROMPT = """分析用户输入，判断意图类型。只返回一个 JSON：
{
  "intent": "life|health|medicine_photo|emergency|greeting",
  "reason": "简短说明"
}

意图说明：
- life: 天气、日历提醒、通讯、备忘等生活事务
- health: 用药咨询、饮食健康、症状问答等
- medicine_photo: 用户拍了药盒/药品照片需要识别
- emergency: 头晕、摔倒、剧痛等紧急健康事件
- greeting: 普通的打招呼、闲聊"""

    def __init__(self):
        self.llm: LLMClient = get_llm_client()
        self.life_agent = LifeAssistantAgent()
        self.health_agent = HealthAdvisorAgent()
        self.emergency_agent = EmergencyResponderAgent()

    # ----------------------------------------------------------
    # 主入口：处理用户消息
    # ----------------------------------------------------------
    async def process_message(
        self,
        user_input: str,
        context: Optional[UserContext] = None,
        image_url: Optional[str] = None,
    ) -> dict:
        """处理一条用户消息，返回结构化响应"""
        ctx = context or UserContext(user_id="default")

        # Step 1: 意图识别
        intent = await self._classify_intent(user_input, image_url)
        logger.info(f"[Orchestrator] user={ctx.user_id} intent={intent.value}")

        # Step 2: 根据意图分发
        if intent == Intent.EMERGENCY:
            result = await self.emergency_agent.handle(user_input, ctx)
        elif intent in (Intent.HEALTH, Intent.MEDICINE_PHOTO):
            result = await self.health_agent.handle(user_input, ctx, image_url)
        elif intent == Intent.LIFE:
            result = await self.life_agent.handle(user_input, ctx)
        elif intent == Intent.GREETING:
            result = await self._handle_greeting(user_input, ctx)
        else:
            result = await self._handle_unknown(user_input, ctx)

        # Step 3: 适老化包装
        result["intent"] = intent.value
        result.setdefault("need_confirm", False)
        result.setdefault("tts_text", result.get("reply", ""))

        return result

    # ----------------------------------------------------------
    # 意图分类
    # ----------------------------------------------------------
    async def _classify_intent(self, user_input: str, image_url: Optional[str] = None) -> Intent:
        """意图分类：规则优先 → LLM 增强 → 规则兜底"""
        if image_url:
            return Intent.MEDICINE_PHOTO

        # 规则先行：紧急
        emergency_keywords = ["头晕", "站不稳", "摔倒", "好痛", "不行了", "不舒服", "救命", "120", "救护车"]
        if any(kw in user_input for kw in emergency_keywords):
            return Intent.EMERGENCY

        # 规则先行：生活类
        life_keywords = ["天气", "下雨", "带伞", "提醒", "备忘", "记一下", "打电话", "几点", "日历", "闹钟", "要不要带", "穿什么"]
        if any(kw in user_input for kw in life_keywords):
            return Intent.LIFE

        # 规则先行：健康类（药名 + 健康关键词）
        health_keywords = ["药", "吃药", "血压", "血糖", "头痛", "感冒", "咳嗽", "拉肚子",
                           "怎么吃", "用量", "禁忌", "副作用", "能不能吃", "饮食",
                           "阿莫西林", "硝苯地平", "二甲双胍", "阿司匹林", "布洛芬"]
        if any(kw in user_input for kw in health_keywords):
            return Intent.HEALTH

        # 规则先行：问候
        greeting_keywords = ["你好", "小银", "谢谢", "再见", "晚安", "早上好"]
        if any(kw in user_input for kw in greeting_keywords):
            return Intent.GREETING

        # LLM 增强分类
        try:
            result = await self.llm.chat_json(
                user_message=f"用户输入：{user_input}",
                system_prompt=self.INTENT_PROMPT,
                temperature=0.1,
            )
            intent_str = result.get("intent", "unknown")
            if result.get("parse_error"):
                return self._rule_fallback_intent(user_input)
            return Intent(intent_str) if intent_str in Intent._value2member_map_ else self._rule_fallback_intent(user_input)
        except Exception:
            return self._rule_fallback_intent(user_input)

    @staticmethod
    def _rule_fallback_intent(user_input: str) -> Intent:
        """当 LLM 不可用时，用规则兜底"""
        health = ["药", "吃药", "血压", "血糖", "病", "痛", "感冒", "咳嗽", "怎么吃", "饮食",
                  "阿莫西林", "硝苯地平", "二甲双胍", "阿司匹林", "布洛芬"]
        life = ["天气", "下雨", "带伞", "提醒", "备忘", "记一下", "打电话", "日历", "闹钟", "几点", "要不要带", "穿什么"]
        greeting = ["你好", "小银", "谢谢", "再见", "晚安", "早"]

        if any(kw in user_input for kw in health):
            return Intent.HEALTH
        if any(kw in user_input for kw in life):
            return Intent.LIFE
        if any(kw in user_input for kw in greeting):
            return Intent.GREETING
        # 兜底：非空输入交给健康 Agent 处理
        if user_input.strip():
            return Intent.HEALTH
        return Intent.UNKNOWN

    # ----------------------------------------------------------
    # 问候 & 兜底
    # ----------------------------------------------------------
    _LLM_DOWN_MARKERS = ["服务异常", "暂时无法"]

    async def _handle_greeting(self, user_input: str, ctx: UserContext) -> dict:
        try:
            reply = await self.llm.chat(
                user_message=user_input,
                system_prompt=f"{self.SYSTEM_PROMPT}\n当前用户叫{ctx.name}。",
                temperature=0.8,
            )
            if not any(m in reply for m in self._LLM_DOWN_MARKERS):
                return {"reply": reply, "action": "chat"}
        except Exception:
            pass
        return {
            "reply": f"{ctx.name}您好！我是小银，您的智能助手。有什么需要帮忙的吗？",
            "action": "chat_offline",
        }

    async def _handle_unknown(self, user_input: str, ctx: UserContext) -> dict:
        try:
            reply = await self.llm.chat(
                user_message=user_input,
                system_prompt=f"{self.SYSTEM_PROMPT}\n当前用户叫{ctx.name}。",
                temperature=0.7,
            )
            if not any(m in reply for m in self._LLM_DOWN_MARKERS):
                return {"reply": reply, "action": "clarify"}
        except Exception:
            pass
        return {
            "reply": f"{ctx.name}，您可以说天气、问健康、查药品，或者直接拍照给我看。",
            "action": "clarify_offline",
        }
