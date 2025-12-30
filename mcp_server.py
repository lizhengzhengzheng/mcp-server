# mcp-server/mcp_server.py
from fastmcp import FastMCP
from typing import Dict, Any
from datetime import datetime

# 创建MCP服务器实例
mcp = FastMCP("Production-Tools-Suite", version="1.0.0")


# ========== 1. 天气查询工具 (模拟真实API) ==========
@mcp.tool()
async def get_weather(city: str) -> Dict[str, Any]:
    """
    获取指定城市的当前天气信息。

    Args:
        city: 城市名称，如"北京"、"上海"。

    Returns:
        包含天气信息的字典。
    """
    # 模拟真实API调用 - 生产环境替换为真实天气API
    weather_data = {
        "北京": {"temperature": "22°C", "condition": "晴", "humidity": "40%"},
        "上海": {"temperature": "25°C", "condition": "多云", "humidity": "65%"},
        "广州": {"temperature": "28°C", "condition": "阵雨", "humidity": "80%"},
    }

    if city in weather_data:
        return {
            "city": city,
            **weather_data[city],
            "timestamp": datetime.now().isoformat(),
            "source": "weather-api"
        }
    else:
        # 默认返回
        return {
            "city": city,
            "temperature": "24°C",
            "condition": "未知",
            "humidity": "50%",
            "note": "模拟数据",
            "timestamp": datetime.now().isoformat()
        }


# ========== 2. 科学计算器工具 ==========
@mcp.tool()
async def calculator(expression: str) -> Dict[str, Any]:
    """
    执行安全的数学表达式计算。

    Args:
        expression: 数学表达式，如"2+3*4"、"sin(30)"。

    Returns:
        包含计算结果的字典。
    """
    import ast
    import math
    import operator

    # 安全的操作符字典
    SAFE_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }

    # 安全的函数字典
    SAFE_FUNCTIONS = {
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'sqrt': math.sqrt,
        'log': math.log,
        'log10': math.log10,
        'exp': math.exp,
    }

    class SafeEval(ast.NodeVisitor):
        def visit(self, node):
            if isinstance(node, ast.Expression):
                return self.visit(node.body)
            elif isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.BinOp):
                left = self.visit(node.left)
                right = self.visit(node.right)
                return SAFE_OPERATORS[type(node.op)](left, right)
            elif isinstance(node, ast.UnaryOp):
                operand = self.visit(node.operand)
                return SAFE_OPERATORS[type(node.op)](operand)
            elif isinstance(node, ast.Call):
                if node.func.id in SAFE_FUNCTIONS:
                    args = [self.visit(arg) for arg in node.args]
                    return SAFE_FUNCTIONS[node.func.id](*args)
                else:
                    raise ValueError(f"不支持的函数: {node.func.id}")
            else:
                raise ValueError(f"不支持的表达式类型: {type(node)}")

    try:
        # 清理表达式
        cleaned_expr = ''.join(c for c in expression if c.isdigit() or c in '+-*/.() ' or c.isalpha())
        tree = ast.parse(cleaned_expr, mode='eval')
        result = SafeEval().visit(tree)

        return {
            "expression": expression,
            "result": float(result) if isinstance(result, (int, float)) else str(result),
            "type": "calculation"
        }
    except Exception as e:
        return {
            "expression": expression,
            "error": f"计算失败: {str(e)}",
            "type": "error"
        }


# ========== 3. 单位转换工具 ==========
@mcp.tool()
async def unit_converter(value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
    """
    在不同的物理单位之间进行转换。

    Args:
        value: 要转换的数值
        from_unit: 原始单位，如"km", "kg", "C"
        to_unit: 目标单位，如"mile", "lb", "F"

    Returns:
        包含转换结果的字典。
    """
    # 转换因子定义
    CONVERSIONS = {
        ("km", "mile"): 0.621371,
        ("mile", "km"): 1.60934,
        ("kg", "lb"): 2.20462,
        ("lb", "kg"): 0.453592,
        ("m", "ft"): 3.28084,
        ("ft", "m"): 0.3048,
        ("C", "F"): lambda c: c * 9 / 5 + 32,
        ("F", "C"): lambda f: (f - 32) * 5 / 9,
    }

    key = (from_unit.lower(), to_unit.lower())

    if key in CONVERSIONS:
        conversion = CONVERSIONS[key]
        if callable(conversion):
            result = conversion(value)
        else:
            result = value * conversion

        return {
            "original": {"value": value, "unit": from_unit},
            "converted": {"value": round(result, 6), "unit": to_unit},
            "conversion_factor": conversion if not callable(conversion) else "function"
        }
    else:
        return {
            "error": f"不支持的单位转换: {from_unit} → {to_unit}",
            "supported_conversions": list(CONVERSIONS.keys())
        }


# ========== 4. 时间日期工具 ==========
@mcp.tool()
async def time_tool(timezone: str = "Asia/Shanghai", operation: str = "current") -> Dict[str, Any]:
    """
    获取时间信息或执行时间操作。

    Args:
        timezone: 时区，默认为"Asia/Shanghai"
        operation: 操作类型，"current"(当前时间) 或 "timestamp"(时间戳)
    """
    from datetime import datetime
    import pytz

    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)

        if operation == "current":
            return {
                "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp": int(now.timestamp()),
                "timezone": timezone,
                "day_of_week": now.strftime("%A"),
                "iso_format": now.isoformat()
            }
        elif operation == "timestamp":
            return {
                "timestamp": int(now.timestamp()),
                "timezone": timezone
            }
        else:
            return {
                "error": f"不支持的操作: {operation}",
                "supported_operations": ["current", "timestamp"]
            }
    except Exception as e:
        return {
            "error": f"时区错误: {str(e)}",
            "supported_timezones": ["Asia/Shanghai", "America/New_York", "Europe/London", "UTC"]
        }


# ========== 5. 文本处理工具 ==========
@mcp.tool()
async def text_analyzer(text: str, operation: str = "stats") -> Dict[str, Any]:
    """
    分析文本的统计信息。

    Args:
        text: 要分析的文本
        operation: 分析类型，"stats"(统计) 或 "summary"(摘要)
    """
    if operation == "stats":
        words = text.split()
        chars = len(text)
        sentences = text.count('.') + text.count('!') + text.count('?')

        return {
            "character_count": chars,
            "word_count": len(words),
            "sentence_count": sentences,
            "average_word_length": round(sum(len(w) for w in words) / len(words), 2) if words else 0,
            "language": "中文" if any('\u4e00' <= c <= '\u9fff' for c in text) else "英文"
        }
    elif operation == "summary":
        # 简单摘要生成
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        summary = '. '.join(sentences[:3]) + '.' if sentences else text[:100]

        return {
            "summary": summary,
            "original_length": len(text),
            "summary_length": len(summary),
            "compression_ratio": round(len(summary) / len(text) * 100, 2) if text else 0
        }


if __name__ == "__main__":
    # 以SSE模式启动，支持远程调用
    print("🚀 启动生产级MCP服务器...")
    print("🔧 可用工具:")
    print("  - get_weather: 查询天气")
    print("  - calculator: 科学计算器")
    print("  - unit_converter: 单位转换")
    print("  - time_tool: 时间日期工具")
    print("  - text_analyzer: 文本分析")
    print(f"\n📡 服务地址: http://localhost:8001")

    mcp.run(transport="sse", host="0.0.0.0", port=8001)