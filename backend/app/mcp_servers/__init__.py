"""
银发守护 — MCP 工具层
=================================
统一 MCP 工具注册和调用入口。
每个 MCP Server 负责一组功能，通过标准接口提供能力。
"""

from app.mcp_servers.weather_server import WeatherTool
from app.mcp_servers.medicine_server import MedicineTool
from app.mcp_servers.reminder_server import ReminderTool
from app.mcp_servers.emergency_server import EmergencyTool


class MCPToolRegistry:
    """MCP 工具注册中心"""

    def __init__(self):
        self.weather = WeatherTool()
        self.medicine = MedicineTool()
        self.reminder = ReminderTool()
        self.emergency = EmergencyTool()

    def list_tools(self) -> list[dict]:
        """列出所有可用工具"""
        return [
            {
                "name": "get_weather",
                "description": "查询指定城市的天气",
                "parameters": {"city": "城市名", "date": "日期(可选)"},
            },
            {
                "name": "set_reminder",
                "description": "设置用药/生活提醒",
                "parameters": {"content": "提醒内容", "time": "提醒时间"},
            },
            {
                "name": "query_medicine",
                "description": "查询药品用法用量和禁忌",
                "parameters": {"medicine_name": "药品名称"},
            },
            {
                "name": "notify_family",
                "description": "通知紧急联系人",
                "parameters": {"message": "通知内容", "urgency": "紧急程度"},
            },
        ]


# 全局单例
_tool_registry: MCPToolRegistry = None


def get_tools() -> MCPToolRegistry:
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = MCPToolRegistry()
    return _tool_registry
