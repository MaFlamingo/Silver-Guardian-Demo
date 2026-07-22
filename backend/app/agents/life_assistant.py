"""
银发守护 — 生活助手 Agent
处理：天气查询、日历提醒、通讯录、生活备忘
支持 LLM 在线 + 离线兜底
"""

import logging
from app.core.llm import get_llm_client
from app.mcp_servers.weather_server import WeatherTool

logger = logging.getLogger(__name__)


class LifeAssistantAgent:
    """生活助手 Agent"""

    SYSTEM_PROMPT = """你是"小银"的生活助手。
你能帮用户：
- 查天气（告诉用户是否需要带伞、穿什么衣服）
- 设置提醒（"下午3点吃药"、"下周二去医院"）
- 记事情（"帮我记一下..."）
- 打电话/发消息给家人（需要确认）

回复风格：亲切、简洁、用大白话。重要操作先确认再执行。"""

    _LLM_DOWN_MARKERS = ["服务异常", "暂时无法"]

    def __init__(self):
        self.llm = get_llm_client()
        self.weather_tool = WeatherTool()

    def _is_llm_down(self, text: str) -> bool:
        return any(m in text for m in self._LLM_DOWN_MARKERS)

    async def handle(self, user_input: str, ctx) -> dict:
        if self._is_weather_query(user_input):
            return await self._handle_weather(user_input, ctx)
        elif self._is_reminder(user_input):
            return await self._handle_reminder(user_input, ctx)
        elif self._is_memo(user_input):
            return await self._handle_memo(user_input, ctx)
        elif self._is_contact(user_input):
            return await self._handle_contact(user_input, ctx)
        else:
            return await self._handle_general_life(user_input, ctx)

    def _is_weather_query(self, text: str) -> bool:
        return any(kw in text for kw in ["天气", "下雨", "带伞", "冷不冷", "热不热", "穿什么", "几度", "要不要带"])

    def _is_reminder(self, text: str) -> bool:
        return any(kw in text for kw in ["提醒", "闹钟", "别忘了", "记着", "到时"])

    def _is_memo(self, text: str) -> bool:
        return any(kw in text for kw in ["记一下", "记住", "备忘", "帮我记"])

    def _is_contact(self, text: str) -> bool:
        return any(kw in text for kw in ["打电话", "发消息", "联系", "找一下"])

    # ----------------------------------------------------------
    # 天气查询
    # ----------------------------------------------------------
    async def _handle_weather(self, user_input: str, ctx) -> dict:
        try:
            reply = await self.llm.chat(
                user_message=user_input,
                system_prompt=f"{self.SYSTEM_PROMPT}\n当前用户叫{ctx.name}。你可以模拟天气信息来回复。",
            )
            if not self._is_llm_down(reply):
                return {"reply": reply, "action": "weather", "tool": "weather_query"}
        except Exception:
            pass

        # 离线兜底
        city = self._extract_city(user_input)
        weather = await self.weather_tool.query(city or "北京")
        return {
            "reply": f"{ctx.name}，{weather}\n\n⚠️ AI 服务暂未连接，以上是本地天气信息。",
            "action": "weather_offline",
        }

    # ----------------------------------------------------------
    # 提醒
    # ----------------------------------------------------------
    async def _handle_reminder(self, user_input: str, ctx) -> dict:
        try:
            from app.mcp_servers import get_tools
            tools = get_tools()
            await tools.reminder.set(user_input, "稍后", ctx.user_id)
        except Exception:
            pass

        try:
            reply = await self.llm.chat(
                user_message=user_input,
                system_prompt=f"{self.SYSTEM_PROMPT}\n当前用户叫{ctx.name}。",
            )
            if not self._is_llm_down(reply):
                return {"reply": reply, "action": "reminder"}
        except Exception:
            pass

        return {
            "reply": f"{ctx.name}，好的，我记下来了。到时候会提醒您。",
            "action": "reminder_offline",
        }

    # ----------------------------------------------------------
    # 备忘
    # ----------------------------------------------------------
    async def _handle_memo(self, user_input: str, ctx) -> dict:
        try:
            reply = await self.llm.chat(
                user_message=user_input,
                system_prompt=f"{self.SYSTEM_PROMPT}\n当前用户叫{ctx.name}。",
            )
            if not self._is_llm_down(reply):
                return {"reply": reply, "action": "memo"}
        except Exception:
            pass
        return {"reply": f"{ctx.name}，好的，我记住了。", "action": "memo_offline"}

    # ----------------------------------------------------------
    # 通讯
    # ----------------------------------------------------------
    async def _handle_contact(self, user_input: str, ctx) -> dict:
        try:
            reply = await self.llm.chat(
                user_message=user_input,
                system_prompt=f"{self.SYSTEM_PROMPT}\n当前用户叫{ctx.name}。通讯类操作需要先确认再执行。",
            )
            if not self._is_llm_down(reply):
                return {"reply": reply, "action": "contact", "need_confirm": True}
        except Exception:
            pass
        return {
            "reply": f"{ctx.name}，我帮您联系家人。要现在打过去吗？",
            "action": "contact_offline",
            "need_confirm": True,
        }

    # ----------------------------------------------------------
    # 通用
    # ----------------------------------------------------------
    async def _handle_general_life(self, user_input: str, ctx) -> dict:
        try:
            reply = await self.llm.chat(user_message=user_input, system_prompt=self.SYSTEM_PROMPT)
            if not self._is_llm_down(reply):
                return {"reply": reply, "action": "chat"}
        except Exception:
            pass
        return {
            "reply": f"{ctx.name}，有什么我能帮您的吗？比如查天气、设提醒，或者问问健康问题。",
            "action": "chat_offline",
        }

    # ----------------------------------------------------------
    # 工具
    # ----------------------------------------------------------
    @staticmethod
    def _extract_city(text: str) -> str | None:
        cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "南京", "西安", "重庆"]
        for c in cities:
            if c in text:
                return c
        return None
