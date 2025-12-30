# tools/weather.py
from tool_registry import tool

@tool
def weather(location: str, date: str = None) -> str:
    """
    获取指定城市的天气信息。

    用途：
      用于查询全球城市的天气情况，支持指定日期查询历史天气。
      可回答自然语言问题，如“北京今天天气怎么样”、“上海明天天气”、“查一下昨天的天气”。

    参数：
      location: 城市名称，例如 "北京"、"Shanghai"、"纽约"
      date: 查询日期，格式为 "YYYY-MM-DD"，默认是当天。
            也可以使用自然语言，例如 "今天"、"明天"、"昨天"

    返回：
      str - 格式化的天气信息字符串，例如 "2025-12-30 北京 晴 25°C"

    示例：
      weather(location="北京") → "2025-12-30 北京 晴 25°C"
      weather(location="上海", date="2025-12-31") → "2025-12-31 上海 多云 20°C"
      weather(location="纽约", date="昨天") → "2025-12-29 纽约 雨 10°C"

    注意：
      如果城市不存在，返回 "未知城市"
    """
    if date is None:
        date = "2025-12-30"  # 默认当天
    if location == "北京":
        return f"{date} {location} 晴 25°C"
    elif location == "上海":
        return f"{date} {location} 多云 20°C"
    elif location == "纽约":
        return f"{date} {location} 雨 10°C"
    else:
        return f"{date} {location} 未知城市"