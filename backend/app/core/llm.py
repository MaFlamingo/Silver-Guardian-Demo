"""
银发守护 — LLM 大模型 API 独立封装层
=========================================
支持多 Provider 切换：Agnes / Qwen / OpenAI
当前默认使用 Agnes AI (OpenAI 兼容协议)

设计原则：
单一职责：只负责 LLM 调用，不包含业务逻辑
统一接口：上层代码调用方式完全一致，切换 Provider 只需改配置
容错降级：JSON 解析失败自动 fallback，不会因模型输出格式问题崩溃
"""
import json
import logging
from typing import Optional, AsyncGenerator
from openai import AsyncOpenAI
import app.core.config as settings
logger = logging.getLogger(__name__)

# ============================================================
# 模型 ID 映射：统一模型名 → 各 Provider 的实际 model ID
# ============================================================
_MODEL_MAP: dict[str, dict[str, str]] = {
    "agnes": {
        "chat": "agnes-chat",
        "vision": "agnes-vision",
    },
    "qwen": {
        "chat": "qwen-plus",
        "vision": "qwen-vl-plus",
    },
    "openai": {
        "chat": "gpt-4o-mini",
        "vision": "gpt-4o",
    },
    "deepseek": {
        "chat": "deepseek-chat",
        "vision": "deepseek-chat",  # DeepSeek 暂不支持视觉
    },
}


class LLMClient:
    """大模型 API 客户端（独立封装，OpenAI 兼容协议）

    使用方式:
        client = LLMClient()
        reply = await client.chat("你好")
        reply = await client.chat_json("提取姓名和年龄", messages=[...])
        reply = await client.chat_with_image("这是什么药？", image_url="...")
    """

    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or settings.LLM_PROVIDER
        self._client: Optional[AsyncOpenAI] = None

    # ----------------------------------------------------------
    # 内部 — 懒加载客户端
    # ----------------------------------------------------------
    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self._get_api_key(),
                base_url=self._get_base_url(),
                timeout=60.0,
            )
        return self._client

    def _get_api_key(self) -> str:
        keys = {
            "agnes": settings.AGNES_API_KEY,
            "qwen": settings.QWEN_API_KEY,
            "openai": settings.OPENAI_API_KEY,
            "deepseek": settings.DEEPSEEK_API_KEY,
        }
        key = keys.get(self.provider, "")
        if not key:
            logger.warning(f"LLM Provider '{self.provider}' 未配置 API Key")
        return key

    def _get_base_url(self) -> str:
        urls = {
            "agnes": settings.AGNES_API_BASE,
            "qwen": settings.QWEN_API_BASE,
            "openai": settings.OPENAI_API_BASE,
            "deepseek": settings.DEEPSEEK_API_BASE,
        }
        return urls.get(self.provider, settings.AGNES_API_BASE)

    def _get_model(self, model_type: str = "chat") -> str:
        """获取当前 Provider 的模型 ID"""
        provider_models = _MODEL_MAP.get(self.provider, {})
        return provider_models.get(model_type, provider_models.get("chat", "gpt-3.5-turbo"))

    # ----------------------------------------------------------
    # 公开 API — 文本对话
    # ----------------------------------------------------------
    async def chat(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """纯文本对话，返回字符串"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        try:
            client = self._get_client()
            response = await client.chat.completions.create(
                model=self._get_model("chat"),
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content or ""
            logger.debug(f"[LLM chat] {self.provider}: {content[:100]}...")
            return content.strip()
        except Exception as e:
            logger.error(f"[LLM chat] 调用失败 ({self.provider}): {e}")
            return f"抱歉，我暂时无法回答。({self.provider} 服务异常)"

    # ----------------------------------------------------------
    # 公开 API — JSON 结构化输出
    # ----------------------------------------------------------
    async def chat_json(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> dict:
        """对话并返回 JSON 结构化数据（带 fallback）"""
        json_instruction = "\n请严格返回 JSON 格式，不要包含 markdown 代码块标记。"
        effective_system = (system_prompt or "") + json_instruction

        raw = await self.chat(
            user_message=effective_system,
            system_prompt=effective_system,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return self._safe_parse_json(raw)

    # ----------------------------------------------------------
    # 公开 API — 多模态（图片理解）
    # ----------------------------------------------------------
    async def chat_with_image(
        self,
        user_message: str,
        image_url: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        """带图片的多模态对话"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": user_message},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        })

        try:
            client = self._get_client()
            response = await client.chat.completions.create(
                model=self._get_model("vision"),
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content or ""
            logger.debug(f"[LLM vision] {self.provider}: {content[:100]}...")
            return content.strip()
        except Exception as e:
            logger.error(f"[LLM vision] 调用失败 ({self.provider}): {e}")
            return f"抱歉，我暂时无法识别这张图片。({self.provider} 服务异常)"

    # ----------------------------------------------------------
    # 公开 API — 流式对话
    # ----------------------------------------------------------
    async def chat_stream(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """流式文本对话"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        try:
            client = self._get_client()
            stream = await client.chat.completions.create(
                model=self._get_model("chat"),
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content
        except Exception as e:
            logger.error(f"[LLM stream] 调用失败 ({self.provider}): {e}")
            yield f"抱歉，服务异常：{e}"

    # ----------------------------------------------------------
    # 内部工具方法
    # ----------------------------------------------------------
    @staticmethod
    def _safe_parse_json(text: str) -> dict:
        """安全解析 JSON，自动剔除 markdown 代码块标记"""
        cleaned = text.strip()
        # 去掉可能的 markdown 代码块标记
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # 尝试用正则提取 JSON 对象
            import re
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            logger.warning(f"[LLM JSON] 解析失败，raw text: {text[:200]}")
            return {"raw": text, "parse_error": True}


# ============================================================
# 全局单例
# ============================================================
_llm_instance: Optional[LLMClient] = None


def get_llm_client(provider: Optional[str] = None) -> LLMClient:
    """获取 LLM 客户端单例"""
    global _llm_instance
    if _llm_instance is None or provider:
        _llm_instance = LLMClient(provider=provider)
    return _llm_instance
