"""
MCP 工具 — 紧急通知服务
通知家属、拨打急救电话
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EmergencyTool:
    """紧急通知工具"""

    async def notify_family(self, message: str, urgency: str, contact_name: str = "", contact_phone: str = "") -> dict:
        """通知紧急联系人

        Args:
            message: 通知内容
            urgency: 紧急程度 (low/medium/high)
            contact_name: 联系人姓名
            contact_phone: 联系人电话
        """
        notification = {
            "timestamp": datetime.now().isoformat(),
            "urgency": urgency,
            "message": message,
            "contact_name": contact_name or "家属",
            "contact_phone": contact_phone,
            "status": "sent" if contact_phone else "simulated",
        }

        if contact_phone:
            # TODO: 接入短信 API（阿里云短信 / 腾讯云短信）
            logger.info(f"[EmergencyTool] 模拟发送通知到 {contact_name}({contact_phone}): {message}")
        else:
            logger.info(f"[EmergencyTool] 通知已记录（无联系电话）: {message}")

        return notification

    async def call_ambulance(self, location: str = "", reason: str = "") -> dict:
        """拨打急救电话（模拟）

        Returns:
            急救指引信息
        """
        guidance = {
            "action": "call_120",
            "location": location or "请查看定位",
            "reason": reason or "紧急医疗求助",
            "guidance": [
                "保持冷静",
                "说清楚地址",
                "说明患者情况",
                "保持电话畅通",
            ],
        }
        logger.info(f"[EmergencyTool] 急救指引已生成: {guidance}")
        return guidance
