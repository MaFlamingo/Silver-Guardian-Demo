"""
MCP 工具 — 天气查询
接入：和风天气 API（免费）
"""

import logging
import httpx

logger = logging.getLogger(__name__)


class WeatherTool:
    """天气查询工具"""

    # 模拟数据（未配置 API 时使用）
    _MOCK_WEATHER = {
        "北京": "多云转晴，15~25℃，东北风3级，适宜出行",
        "上海": "小雨，18~22℃，建议带伞",
        "广州": "晴，22~30℃，注意防晒",
        "深圳": "多云，23~28℃，体感舒适",
        "杭州": "阴转小雨，16~24℃，记得带伞",
        "成都": "阴天，18~26℃，空气质量良好",
    }

    async def query(self, city: str, date: str = "今天") -> str:
        """查询天气

        Args:
            city: 城市名
            date: 日期（今天/明天/后天）

        Returns:
            天气描述文本
        """
        # 优先尝试真实 API（如果有 Key）
        api_key = ""  # 可在配置中扩展
        if api_key:
            return await self._query_real(city, date, api_key)

        # 降级到模拟数据
        return self._query_mock(city, date)

    async def _query_real(self, city: str, date: str, api_key: str) -> str:
        """调用和风天气 API"""
        try:
            # 先查城市 ID
            async with httpx.AsyncClient() as client:
                geo_resp = await client.get(
                    "https://geoapi.qweather.com/v2/city/lookup",
                    params={"location": city, "key": api_key},
                    timeout=10,
                )
                geo_data = geo_resp.json()
                if geo_data.get("code") != "200" or not geo_data.get("location"):
                    return self._query_mock(city, date)

                city_id = geo_data["location"][0]["id"]

                # 查天气
                weather_resp = await client.get(
                    "https://devapi.qweather.com/v7/weather/3d",
                    params={"location": city_id, "key": api_key},
                    timeout=10,
                )
                weather_data = weather_resp.json()

                # 格式化返回
                days = weather_data.get("daily", [])
                idx = {"今天": 0, "明天": 1, "后天": 2}.get(date, 0)
                if idx < len(days):
                    d = days[idx]
                    return f"{city} {date}：{d.get('textDay', '未知')}，{d.get('tempMin', '?')}~{d.get('tempMax', '?')}℃"

        except Exception as e:
            logger.warning(f"[WeatherTool] API 调用失败: {e}")
        return self._query_mock(city, date)

    def _query_mock(self, city: str, date: str) -> str:
        """模拟天气数据"""
        weather = self._MOCK_WEATHER.get(city)
        if weather:
            return f"{city} {date}：{weather}"
        return f"{city} {date}：天气信息暂不可用，建议您看下窗外 😊"
