"""
银发守护 v2 — API 路由
=========================
RESTful API + WebSocket 实时对话
新增：日记 CRUD、心情记录/分析、个人知识库检索
"""
import logging
from datetime import date
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException

from app.agents.orchestrator import AgentOrchestrator, UserContext
from app.agents.diary_agent import DiaryAgent
from app.mcp_servers import get_tools
from app.rag import get_rag
from app.voice import analyze_text_mood, fuse_mood
from app.schemas import (
    ChatRequest, ChatResponse,
    ReminderRequest, ReminderResponse,
    MedicineQueryRequest, MedicineInfoResponse,
    ToolListResponse, HealthStatus,
    DiaryWriteRequest, DiaryReadRequest,
    MoodRecordRequest, MoodHistoryRequest,
    PersonalKBSearchRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["银发守护 v2"])

# 全局实例
_orchestrator = AgentOrchestrator()
_diary_agent = DiaryAgent()

# ============================================================
# 健康检查
# ============================================================
@router.get("/health", response_model=HealthStatus)
async def health_check():
    """服务健康检查"""
    rag_ready = False
    kb_ready = False
    kb_blocks = 0
    try:
        rag = await get_rag()
        rag_ready = rag._initialized
        kb_ready = rag.personal._initialized
        kb_blocks = len(rag.personal.blocks)
    except Exception:
        pass

    from app.core.config import LLM_PROVIDER
    return HealthStatus(
        status="ok",
        llm_provider=LLM_PROVIDER,
        health_rag_ready=rag_ready,
        personal_kb_ready=kb_ready,
        personal_kb_blocks=kb_blocks,
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
# 🆕 日记接口
# ============================================================
@router.post("/diary/write")
async def diary_write(req: DiaryWriteRequest):
    """写日记"""
    result = _diary_agent.write_diary(req.user_id, req.content, req.dt, req.mood)
    return result


@router.post("/diary/read")
async def diary_read(req: DiaryReadRequest):
    """读日记"""
    return _diary_agent.read_diary(req.user_id, req.dt)


@router.get("/diary/list/{user_id}")
async def diary_list(user_id: str = "default"):
    """日记列表"""
    entries = _diary_agent.list_diaries(user_id)
    return {"user_id": user_id, "entries": entries, "count": len(entries)}


@router.delete("/diary/{user_id}")
async def diary_delete(user_id: str, dt: str = None):
    """删除日记"""
    d = date.fromisoformat(dt) if dt else None
    return _diary_agent.delete_diary(user_id, d)


# ============================================================
# 🆕 心情接口
# ============================================================
@router.post("/mood/record")
async def mood_record(req: MoodRecordRequest):
    """记录心情"""
    return _diary_agent.record_mood(
        req.user_id, req.mood, req.note,
        req.acoustic_mood, req.acoustic_conf,
    )


@router.post("/mood/history")
async def mood_history(req: MoodHistoryRequest):
    """心情历史与趋势"""
    return _diary_agent.get_mood_history(req.user_id, req.days)


@router.post("/mood/analyze-text")
async def mood_analyze_text(req: dict):
    """分析文本情绪"""
    text = req.get("text", "")
    if not text:
        raise HTTPException(400, "文本不能为空")
    return analyze_text_mood(text)


# ============================================================
# 🆕 个人知识库接口
# ============================================================
@router.post("/kb/search")
async def kb_search(req: PersonalKBSearchRequest):
    """个人知识库语义检索"""
    rag = await get_rag()
    results = rag.search_personal(req.query, req.top_k)
    return {
        "query": req.query,
        "results": results,
        "count": len(results),
    }


@router.get("/kb/summary")
async def kb_summary():
    """知识库概览"""
    rag = await get_rag()
    return rag.personal_summary()


# ============================================================
# MCP 工具接口
# ============================================================
@router.get("/tools", response_model=ToolListResponse)
async def list_tools():
    tools = get_tools()
    return ToolListResponse(tools=tools.list_tools())


@router.post("/reminder", response_model=ReminderResponse)
async def set_reminder(req: ReminderRequest):
    tools = get_tools()
    result = await tools.reminder.set(req.content, req.time, req.user_id)
    return ReminderResponse(
        success=result["success"],
        reminder_id=result["reminder"]["id"],
        message=result["message"],
    )


@router.get("/reminder/{user_id}")
async def get_reminders(user_id: str = "default"):
    tools = get_tools()
    reminders = await tools.reminder.list(user_id)
    return {"user_id": user_id, "reminders": reminders, "count": len(reminders)}


@router.post("/medicine/query", response_model=MedicineInfoResponse)
async def query_medicine(req: MedicineQueryRequest):
    tools = get_tools()
    result = await tools.medicine.query(req.medicine_name)
    return MedicineInfoResponse(**result)


# ============================================================
# WebSocket 实时对话
# ============================================================
@router.websocket("/ws/chat/{user_id}")
async def ws_chat(websocket: WebSocket, user_id: str):
    await websocket.accept()
    logger.info(f"[WS] 用户连接: {user_id}")
    ctx = UserContext(user_id=user_id)

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            image_url = data.get("image_url", None)

            if not message and not image_url:
                await websocket.send_json({"error": "消息不能为空"})
                continue

            ctx.name = data.get("user_name", ctx.name)
            ctx.age = data.get("user_age", ctx.age)

            result = await _orchestrator.process_message(
                user_input=message,
                context=ctx,
                image_url=image_url,
            )

            await websocket.send_json({
                "reply": result.get("reply", ""),
                "intent": result.get("intent", "unknown"),
                "action": result.get("action", "chat"),
                "tts_text": result.get("tts_text", result.get("reply", "")),
                "need_confirm": result.get("need_confirm", False),
                "medicine_info": result.get("medicine_info"),
                "urgency": result.get("urgency"),
                "data": result.get("data"),
            })

    except WebSocketDisconnect:
        logger.info(f"[WS] 用户断开: {user_id}")
    except Exception as e:
        logger.error(f"[WS] 错误: {e}")
        try:
            await websocket.send_json({"error": f"服务异常：{str(e)}"})
        except Exception:
            pass
