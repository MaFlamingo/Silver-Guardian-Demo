"""
MCP 工具 — 药品信息查询
接入：RAG 药品知识库
"""

import logging

logger = logging.getLogger(__name__)


# 内置常见药品知识库（作为 RAG 的补充）
_KNOWN_MEDICINES = {
    "阿莫西林": {
        "name": "阿莫西林",
        "type": "抗生素",
        "usage": "每次0.5g，每日3次，饭后服用",
        "warnings": ["青霉素过敏者禁用", "不能和酒精一起服用", "吃够疗程，不要自己停药"],
    },
    "硝苯地平": {
        "name": "硝苯地平（心痛定）",
        "type": "降压药",
        "usage": "每次10mg，每日2-3次，饭后服用",
        "warnings": ["不要突然停药", "不要吃柚子/喝柚子汁", "头晕时先坐下休息"],
    },
    "二甲双胍": {
        "name": "二甲双胍",
        "type": "降糖药",
        "usage": "每次0.5g，每日2-3次，饭中或饭后服用",
        "warnings": ["定期检查肾功能", "做增强CT前要停药", "不要空腹吃"],
    },
    "阿司匹林": {
        "name": "阿司匹林",
        "type": "抗血小板",
        "usage": "每次100mg，每日1次，饭后服用",
        "warnings": ["胃病患者慎用", "不要和其他止痛药一起吃", "手术前要停药"],
    },
    "布洛芬": {
        "name": "布洛芬",
        "type": "止痛药",
        "usage": "每次0.2-0.4g，每日不超过2.4g，饭后服用",
        "warnings": ["不能和阿司匹林一起吃", "胃不好要少吃", "不要长期吃"],
    },
}


class MedicineTool:
    """药品信息查询工具"""

    async def query(self, medicine_name: str) -> dict:
        """查询药品信息

        Args:
            medicine_name: 药品名称

        Returns:
            {"found": bool, "info": dict|None, "message": str}
        """
        # 精确匹配
        if medicine_name in _KNOWN_MEDICINES:
            info = _KNOWN_MEDICINES[medicine_name]
            return {"found": True, "info": info, "message": self._format_response(info)}

        # 模糊匹配
        for key, info in _KNOWN_MEDICINES.items():
            if medicine_name in key or key in medicine_name:
                return {"found": True, "info": info, "message": self._format_response(info)}

        return {
            "found": False,
            "info": None,
            "message": f"暂时没有找到「{medicine_name}」的信息。建议您查看药品说明书，或者问一下医生。",
        }

    @staticmethod
    def _format_response(info: dict) -> str:
        """格式化为大白话"""
        parts = [
            f"📋 {info['name']}（{info['type']}）",
            f"💊 用法：{info['usage']}",
            "⚠️ 注意：",
        ]
        for w in info["warnings"]:
            parts.append(f"  • {w}")
        return "\n".join(parts)
