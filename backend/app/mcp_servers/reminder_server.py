"""
MCP 工具 — 提醒服务
管理用药提醒和生活提醒
"""

import logging
import json
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# 提醒数据文件（简单 JSON 持久化）
_REMINDERS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "reminders.json"


class ReminderTool:
    """提醒管理工具"""

    async def set(self, content: str, time: str, user_id: str = "default") -> dict:
        """设置提醒

        Args:
            content: 提醒内容
            time: 提醒时间描述
            user_id: 用户标识
        """
        reminder = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "content": content,
            "time": time,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "done": False,
        }

        reminders = self._load()
        if user_id not in reminders:
            reminders[user_id] = []
        reminders[user_id].append(reminder)
        self._save(reminders)

        logger.info(f"[ReminderTool] 已设置提醒: {content} @ {time}")
        return {"success": True, "reminder": reminder, "message": f"好的，我记住了：{time} {content}"}

    async def list(self, user_id: str = "default") -> list:
        """列出用户的所有提醒"""
        reminders = self._load()
        user_reminders = reminders.get(user_id, [])
        # 只返回未完成的
        return [r for r in user_reminders if not r.get("done")]

    async def done(self, reminder_id: str, user_id: str = "default") -> bool:
        """标记提醒已完成"""
        reminders = self._load()
        for r in reminders.get(user_id, []):
            if r["id"] == reminder_id:
                r["done"] = True
                self._save(reminders)
                return True
        return False

    def _load(self) -> dict:
        try:
            if _REMINDERS_FILE.exists():
                return json.loads(_REMINDERS_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"[ReminderTool] 加载失败: {e}")
        return {}

    def _save(self, data: dict):
        try:
            _REMINDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
            _REMINDERS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"[ReminderTool] 保存失败: {e}")
