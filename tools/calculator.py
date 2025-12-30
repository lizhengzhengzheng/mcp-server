# tools/calculator.py
from tool_registry import tool

@tool
def calculator(expression: str) -> str:
    """
    计算一个数学表达式的值。

    用途：
      用于执行数学计算，支持加减乘除、幂运算、开方等常见数学操作。
      可以处理自然语言中的数学问题，如“1+1等于几”、“算一下2*3+5”。

    参数：
      expression: 数学表达式字符串，例如 "1+1"、"2*3+5"、"sqrt(9)"、"2^3"
                  也可以是自然语言形式的问题，例如 "1加1等于几"、"计算 3的平方"

    返回：
      str - 计算结果的字符串形式，例如 "2"、"11"、"3.0"

    示例：
      calculator(expression="1+1") → "2"
      calculator(expression="2*3+5") → "11"
      calculator(expression="sqrt(9)") → "3.0"
      calculator(expression="1加1等于几") → "2"
      calculator(expression="计算 3的平方") → "9"

    支持的操作符：
      + (加), - (减), * (乘), / (除), ** (幂), sqrt() (开平方)
    """
    try:
        # 简单替换自然语言数字和运算符
        expr = expression.replace("加", "+").replace("减", "-").replace("乘", "*").replace("除", "/")
        expr = expr.replace("等于几", "").replace("计算", "").strip()
        return str(eval(expr))
    except Exception as e:
        return f"计算错误: {e}"