"""
银发守护 v2 — API Schema 定义
===============================
原 Silver-Guardian schemas + 新增日记/心情/知识库 schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


# ============================================================
# 请求体
# ============================================================
class ChatRequest(BaseModel):
    """文本对话请求"""
    message: str = Field(..., min_length=1, max_length=2000)
    user_id: str = Field(default="default")
    user_name: str = Field(default="张叔")
    user_age: int = Field(default=70, ge=1, le=150)
    image_url: Optional[str] = Field(default=None)


class ReminderRequest(BaseModel):
    """设置提醒请求"""
    content: str = Field(..., description="提醒内容")
    time: str = Field(..., description="提醒时间")
    user_id: str = Field(default="default")


class MedicineQueryRequest(BaseModel):
    """药品查询请求"""
    medicine_name: str = Field(..., description="药品名称")


class EmergencyNotifyRequest(BaseModel):
    """紧急通知请求"""
    message: str = Field(..., description="通知内容")
    urgency: str = Field(default="high")
    user_id: str = Field(default="default")


# 🆕 日记/心情请求
class DiaryWriteRequest(BaseModel):
    """写日记请求"""
    content: str = Field(..., min_length=1, max_length=10000)
    user_id: str = Field(default="default")
    dt: Optional[date] = Field(default=None)
    mood: Optional[str] = Field(default=None)


class DiaryReadRequest(BaseModel):
    """读日记请求"""
    user_id: str = Field(default="default")
    dt: Optional[date] = Field(default=None)


class MoodRecordRequest(BaseModel):
    """记录心情请求"""
    mood: str = Field(..., description="心情标签")
    note: str = Field(default="", max_length=2000)
    user_id: str = Field(default="default")
    acoustic_mood: Optional[str] = Field(default=None)
    acoustic_conf: Optional[float] = Field(default=None)


class MoodHistoryRequest(BaseModel):
    """心情历史请求"""
    user_id: str = Field(default="default")
    days: int = Field(default=7, ge=1, le=365)


class PersonalKBSearchRequest(BaseModel):
    """个人知识库搜索"""
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


# ============================================================
# 响应体
# ============================================================
class ChatResponse(BaseModel):
    """对话响应"""
    reply: str = Field(...)
    intent: str = Field(default="unknown")
    action: str = Field(default="chat")
    tts_text: Optional[str] = Field(default=None)
    need_confirm: bool = Field(default=False)
    medicine_info: Optional[dict] = Field(default=None)
    urgency: Optional[str] = Field(default=None)
    data: Optional[dict] = Field(default=None)


class ReminderResponse(BaseModel):
    success: bool
    reminder_id: Optional[str] = None
    message: str


class MedicineInfoResponse(BaseModel):
    found: bool
    info: Optional[dict] = None
    message: str


class ToolListResponse(BaseModel):
    tools: list[dict]


class HealthStatus(BaseModel):
    """服务健康状态（v2 扩展）"""
    status: str = "ok"
    llm_provider: str
    health_rag_ready: bool
    personal_kb_ready: bool
    personal_kb_blocks: int = 0
    version: str = "2.0.0"
