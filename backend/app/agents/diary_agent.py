"""
银发守护 v2 — 日记心情 Agent
=================================
来自 my-wiki 的日记/心情功能，封装为 Agent 模块。
提供：日记 CRUD、心情记录与趋势分析、知识库联动。
"""
import os
import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from app.core.config import DIARY_DATA_DIR, MOOD_DATA_DIR

logger = logging.getLogger(__name__)


class DiaryAgent:
    """日记心情 Agent

    负责：
      - 日记的创建、查询、更新、删除
      - 心情记录与文本情绪分析
      - 心情趋势统计
      - 语音心情融合分析
    """

    SYSTEM_PROMPT = """你是"小银"的心灵陪伴助手。
你能帮用户：
- 写日记、回顾日记（今天做了什么、有什么想法）
- 记录心情（开心、低落、焦虑、平静...）
- 看心情变化趋势（最近一周的情绪怎么样）
- 语音心情分析（从说话的语气判断心情）

回复风格：温柔亲切，多用大白话，像朋友聊天。
用户心情不好时要给予安慰和鼓励，心情好时一起开心。"""

    def __init__(self):
        Path(DIARY_DATA_DIR).mkdir(parents=True, exist_ok=True)
        Path(MOOD_DATA_DIR).mkdir(parents=True, exist_ok=True)

    # ============================================================
    # 日记 CRUD
    # ============================================================
    def _diary_path(self, user_id: str, dt: Optional[date] = None) -> str:
        dt = dt or date.today()
        return str(Path(DIARY_DATA_DIR) / user_id / f"{dt.isoformat()}.json")

    def write_diary(self, user_id: str, content: str,
                    dt: Optional[date] = None, mood: Optional[str] = None) -> dict:
        """写日记"""
        path = self._diary_path(user_id, dt)
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        entry = {
            "date": (dt or date.today()).isoformat(),
            "content": content,
            "mood": mood,
            "created_at": datetime.now().isoformat(),
        }

        existing = {}
        if os.path.exists(path):
            try:
                existing = json.loads(Path(path).read_text("utf-8"))
                if isinstance(existing, dict):
                    existing.update(entry)
                    entry = existing
                else:
                    entry = {"entries": existing + [entry]}
            except Exception:
                pass

        Path(path).write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"[Diary] 用户 {user_id} 日记已保存: {entry['date']}")
        return {"success": True, "date": entry["date"], "preview": content[:100]}

    def read_diary(self, user_id: str, dt: Optional[date] = None) -> dict:
        """读日记"""
        path = self._diary_path(user_id, dt)
        if not os.path.exists(path):
            return {"success": False, "message": "这一天还没有写日记哦～"}
        try:
            data = json.loads(Path(path).read_text("utf-8"))
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "message": f"读取失败: {e}"}

    def list_diaries(self, user_id: str, limit: int = 30) -> list:
        """列出日记列表"""
        user_dir = Path(DIARY_DATA_DIR) / user_id
        if not user_dir.exists():
            return []
        files = sorted(user_dir.glob("*.json"), reverse=True)[:limit]
        entries = []
        for f in files:
            try:
                data = json.loads(f.read_text("utf-8"))
                entries.append({
                    "date": data.get("date", f.stem),
                    "mood": data.get("mood"),
                    "preview": data.get("content", "")[:80],
                })
            except Exception:
                entries.append({"date": f.stem, "mood": None, "preview": "(读取失败)"})
        return entries

    def delete_diary(self, user_id: str, dt: Optional[date] = None) -> dict:
        """删除日记"""
        path = self._diary_path(user_id, dt)
        if not os.path.exists(path):
            return {"success": False, "message": "这一天没有日记可以删除"}
        os.remove(path)
        return {"success": True, "message": f"已删除 {dt.isoformat() if dt else date.today().isoformat()} 的日记"}

    # ============================================================
    # 心情记录与分析
    # ============================================================
    def _mood_path(self, user_id: str) -> str:
        return str(Path(MOOD_DATA_DIR) / user_id / "mood_log.jsonl")

    def record_mood(self, user_id: str, mood: str, note: str = "",
                    acoustic_mood: Optional[str] = None,
                    acoustic_conf: Optional[float] = None) -> dict:
        """记录一条心情"""
        path = self._mood_path(user_id)
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        entry = {
            "timestamp": datetime.now().isoformat(),
            "date": date.today().isoformat(),
            "mood": mood,
            "note": note,
        }
        if acoustic_mood:
            entry["acoustic_mood"] = acoustic_mood
            entry["acoustic_confidence"] = acoustic_conf

        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        logger.info(f"[Mood] 用户 {user_id} 心情: {mood}")
        return {"success": True, "mood": mood, "timestamp": entry["timestamp"]}

    def get_mood_history(self, user_id: str, days: int = 7) -> dict:
        """获取最近 N 天心情历史"""
        path = self._mood_path(user_id)
        if not os.path.exists(path):
            return {"success": True, "records": [], "trend": "暂无数据"}

        records = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line.strip())
                    if r:
                        records.append(r)
                except Exception:
                    continue

        # 过滤最近 N 天
        from datetime import timedelta
        cutoff = (datetime.now() - timedelta(days=days)).date().isoformat()
        recent = [r for r in records if r.get("date", "") >= cutoff]

        # 心情趋势统计
        mood_count = {}
        for r in recent:
            m = r.get("mood", "未知")
            mood_count[m] = mood_count.get(m, 0) + 1

        # 趋势简述
        if mood_count:
            dominant = max(mood_count.items(), key=lambda x: x[1])
            trend = f"最近{days}天以「{dominant[0]}」为主（共{dominant[1]}次）"
        else:
            trend = f"最近{days}天暂无心情记录"

        return {
            "success": True,
            "records": recent,
            "mood_distribution": mood_count,
            "trend": trend,
            "total": len(recent),
        }

    # ============================================================
    # Agent 统一处理入口
    # ============================================================
    async def handle(self, user_input: str, ctx, action: str = "auto") -> dict:
        """处理日记/心情相关请求"""
        if action == "auto":
            action = self._detect_action(user_input)

        if action == "write_diary":
            return self._handle_write(user_input, ctx)
        elif action == "read_diary":
            return self._handle_read(ctx)
        elif action == "record_mood":
            return self._handle_mood(user_input, ctx)
        elif action == "mood_trend":
            return self._handle_trend(ctx)
        else:
            return self._handle_general(ctx)

    def _detect_action(self, text: str) -> str:
        if any(kw in text for kw in ["写日记", "记日记", "日记写下", "记录今天", "今天发生"]):
            return "write_diary"
        if any(kw in text for kw in ["看日记", "读日记", "日记回顾", "那天", "那天发生了什么"]):
            return "read_diary"
        if any(kw in text for kw in ["心情怎么样", "最近心情", "情绪趋势", "心情变化", "心情趋势"]):
            return "mood_trend"
        if any(kw in text for kw in ["心情", "开心", "难过", "焦虑", "低落", "不高兴", "烦躁",
                                       "好开心", "好难过", "心情不好", "心情好"]):
            return "record_mood"
        return "general"

    def _handle_write(self, user_input: str, ctx) -> dict:
        from app.rag import get_rag
        result = self.write_diary(ctx.user_id, user_input)
        return {
            "reply": f"{ctx.name}，日记已经帮您记好了。今天{date.today().isoformat()}的点点滴滴，我都收着。",
            "action": "diary_write",
            "data": result,
        }

    def _handle_read(self, ctx) -> dict:
        result = self.read_diary(ctx.user_id, date.today())
        if result["success"]:
            data = result["data"]
            content = data.get("content", "") if isinstance(data, dict) else str(data)
            return {
                "reply": f"{ctx.name}，您今天的日记：\n\n{content[:500]}",
                "action": "diary_read",
                "data": result,
            }
        return {"reply": result["message"], "action": "diary_read_empty"}

    def _handle_mood(self, user_input: str, ctx) -> dict:
        from app.voice import analyze_text_mood
        mood_result = analyze_text_mood(user_input)
        self.record_mood(ctx.user_id, mood_result["mood"], user_input)

        replies = {
            "开心": f"看到{ctx.name}开心，小银也跟着高兴！😊 继续保持好心情哦～",
            "低落": f"{ctx.name}，不开心的日子总会过去的。想跟小银聊聊天吗？说出来心里会舒服很多。",
            "焦虑": f"{ctx.name}别太紧张，深呼吸，慢慢来。需要我帮您理一理现在最担心的事吗？",
            "兴奋": f"哇，{ctx.name}今天特别兴奋啊！有什么好消息跟小银分享吗？",
            "平静": f"嗯，{ctx.name}，平平淡淡的日子其实很安心。记得照顾好自己～",
            "感激": f"听到{ctx.name}这么说，小银觉得很温暖。很高兴能陪在您身边。",
        }
        reply = replies.get(mood_result["mood"], f"{ctx.name}，我感受到您的心情了。无论什么心情都是正常的，小银一直在这里。")

        return {
            "reply": reply,
            "action": "mood_record",
            "data": {"mood": mood_result["mood"], "confidence": mood_result["confidence"]},
        }

    def _handle_trend(self, ctx) -> dict:
        result = self.get_mood_history(ctx.user_id)
        entries = self.list_diaries(ctx.user_id, 7)

        summary_lines = [f"**{result['trend']}**"]
        if result["mood_distribution"]:
            for mood, count in sorted(result["mood_distribution"].items(), key=lambda x: x[1], reverse=True):
                summary_lines.append(f"• {mood}: {count} 次")
        summary = "\n".join(summary_lines)

        return {
            "reply": f"{ctx.name}，这是您最近7天的心情概览：\n\n{summary}\n\n{'最近有写日记呢，真棒！' if entries else '有空也可以写写日记哦，把每天的点点滴滴记录下来。'}",
            "action": "mood_trend",
            "data": {"trend": result["trend"], "distribution": result["mood_distribution"], "recent_entries": entries},
        }

    def _handle_general(self, ctx) -> dict:
        return {
            "reply": f"{ctx.name}，您想写日记、记心情，还是看看最近的心情趋势呢？小银都可以帮您！",
            "action": "diary_general",
        }
