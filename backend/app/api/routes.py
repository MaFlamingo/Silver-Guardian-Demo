"""
银发守护 — API 路由
=================================
RESTful API + WebSocket 实时对话
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agents.orchestrator import AgentOrchestrator, UserContext
from app.mcp_servers import get_tools
from app.rag import get_rag
from app.schemas import (
    ChatRequest, ChatResponse,
    ReminderRequest, ReminderResponse,
    MedicineQueryRequest, MedicineInfoResponse,
    ToolListResponse, HealthStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["银发守护"])

# 全局实例
_orchestrator = AgentOrchestrator()


# ============================================================
# 健康检查
# ============================================================
@router.get("/health", response_model=HealthStatus)
async def health_check():
    """服务健康检查"""
    rag_ready = False
    try:
        rag = await get_rag()
        rag_ready = rag._initialized
    except Exception:
        pass

    from app.core.config import LLM_PROVIDER
    return HealthStatus(
        status="ok",
        llm_provider=LLM_PROVIDER,
        rag_ready=rag_ready,
    )


# ============================================================
# 主对话接口
# ============================================================
@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """文本对话（支持多模态图片）"""
    ctx = UserContext(
        user_id=req.user_id,
        name=req.user_name,
        age=req.user_age,
    )

    result = await _orchestrator.process_message(
        user_input=req.message,
        context=ctx,
        image_url=req.image_url,
    )

    return ChatResponse(**result)


# ============================================================
# MCP 工具接口
# ============================================================
@router.get("/tools", response_model=ToolListResponse)
async def list_tools():
    """列出所有可用 MCP 工具"""
    tools = get_tools()
    return ToolListResponse(tools=tools.list_tools())


@router.post("/reminder", response_model=ReminderResponse)
async def set_reminder(req: ReminderRequest):
    """设置提醒"""
    tools = get_tools()
    result = await tools.reminder.set(req.content, req.time, req.user_id)
    return ReminderResponse(
        success=result["success"],
        reminder_id=result["reminder"]["id"],
        message=result["message"],
    )


@router.get("/reminder/{user_id}")
async def get_reminders(user_id: str = "default"):
    """获取用户提醒列表"""
    tools = get_tools()
    reminders = await tools.reminder.list(user_id)
    return {"user_id": user_id, "reminders": reminders, "count": len(reminders)}


@router.post("/medicine/query", response_model=MedicineInfoResponse)
async def query_medicine(req: MedicineQueryRequest):
    """查询药品信息"""
    tools = get_tools()
    result = await tools.medicine.query(req.medicine_name)
    return MedicineInfoResponse(**result)


# ============================================================
# WebSocket 实时对话
# ============================================================
@router.websocket("/ws/chat/{user_id}")
async def ws_chat(websocket: WebSocket, user_id: str):
    """WebSocket 实时对话"""
    await websocket.accept()
    logger.info(f"[WS] 用户连接: {user_id}")

    ctx = UserContext(user_id=user_id)

    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()
            message = data.get("message", "")
            image_url = data.get("image_url", None)

            if not message and not image_url:
                await websocket.send_json({"error": "消息不能为空"})
                continue

            # 更新用户上下文
            ctx.name = data.get("user_name", ctx.name)
            ctx.age = data.get("user_age", ctx.age)

            # 处理消息
            result = await _orchestrator.process_message(
                user_input=message,
                context=ctx,
                image_url=image_url,
            )

            # 发送回复
            await websocket.send_json({
                "reply": result.get("reply", ""),
                "intent": result.get("intent", "unknown"),
                "action": result.get("action", "chat"),
                "tts_text": result.get("tts_text", result.get("reply", "")),
                "need_confirm": result.get("need_confirm", False),
                "medicine_info": result.get("medicine_info"),
                "urgency": result.get("urgency"),
            })

    except WebSocketDisconnect:
        logger.info(f"[WS] 用户断开: {user_id}")
    except Exception as e:
        logger.error(f"[WS] 错误: {e}")
        try:
            await websocket.send_json({"error": f"服务异常：{str(e)}"})
        except Exception:
            pass
