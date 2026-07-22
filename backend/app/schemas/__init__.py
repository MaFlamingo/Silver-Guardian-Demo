"""
银发守护 — API Schema 定义
"""
from pydantic import BaseModel, Field
from typing import Optional


# ============================================================
# 请求体
# ============================================================
class ChatRequest(BaseModel):
    """文本对话请求"""
    message: str = Field(..., description="用户输入文本", min_length=1, max_length=2000)
    user_id: str = Field(default="default", description="用户标识")
    user_name: str = Field(default="张叔", description="用户称呼")
    user_age: int = Field(default=70, ge=1, le=150)
    image_url: Optional[str] = Field(default=None, description="图片URL（拍照识药等场景）")


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
    urgency: str = Field(default="high", description="紧急程度: low/medium/high")
    user_id: str = Field(default="default")


# ============================================================
# 响应体
# ============================================================
class ChatResponse(BaseModel):
    """对话响应"""
    reply: str = Field(..., description="AI 回复文本")
    intent: str = Field(default="unknown", description="识别的意图")
    action: str = Field(default="chat", description="执行的动作")
    tts_text: Optional[str] = Field(default=None, description="适合 TTS 播报的文本")
    need_confirm: bool = Field(default=False, description="是否需要用户确认")
    medicine_info: Optional[dict] = Field(default=None, description="药品识别信息")
    urgency: Optional[str] = Field(default=None, description="紧急程度")
    data: Optional[dict] = Field(default=None, description="附加数据")


class ReminderResponse(BaseModel):
    """提醒响应"""
    success: bool
    reminder_id: Optional[str] = None
    message: str


class MedicineInfoResponse(BaseModel):
    """药品信息响应"""
    found: bool
    info: Optional[dict] = None
    message: str


class ToolListResponse(BaseModel):
    """工具列表响应"""
    tools: list[dict]


class HealthStatus(BaseModel):
    """服务健康状态"""
    status: str = "ok"
    llm_provider: str
    rag_ready: bool
