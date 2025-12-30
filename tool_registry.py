import inspect
import importlib
import os
from typing import Dict, Callable, Any


class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Callable] = {}

    def tool(self, func: Callable) -> Callable:
        self.tools[func.__name__] = func
        return func

    def _parse_docstring(self, docstring: str) -> dict:
        """手动解析纯文本文档字符串，提取参数说明（增加容错处理）"""
        if not docstring:
            return {"description": "", "params_desc": {}}

        # 分离主描述和参数部分
        lines = docstring.strip().split('\n')
        main_desc_lines = []
        params_desc = {}
        in_params_section = False
        current_param = None

        # 先提取主描述（参数部分之前的内容）
        for line in lines:
            stripped_line = line.strip()
            # 匹配参数部分的开头（兼容中文/英文冒号）
            if stripped_line.startswith(("参数：", "参数:", "Params：", "Params:")):
                in_params_section = True
                continue
            if not in_params_section:
                if stripped_line:  # 跳过空行
                    main_desc_lines.append(stripped_line)
            else:
                # 处理参数部分，遇到其他关键部分则停止
                if stripped_line.startswith(("返回：", "返回:", "示例：", "示例:",
                                             "支持的操作符：", "注意：", "Note：")):
                    break
                # 跳过空行
                if not stripped_line:
                    continue
                # 兼容中文/英文冒号分割
                if "：" in stripped_line:
                    sep = "："
                elif ":" in stripped_line:
                    sep = ":"
                else:
                    # 没有冒号，判断是参数描述的换行还是无效行
                    if current_param and stripped_line:
                        # 追加到当前参数的描述
                        params_desc[current_param] = params_desc.get(current_param, "") + " " + stripped_line
                    continue  # 无冒号且无当前参数，跳过

                # 分割参数名和描述（增加容错）
                parts = stripped_line.split(sep, 1)
                if len(parts) < 2:
                    continue  # 无法分割，跳过该行
                param_name, desc = parts
                param_name = param_name.strip()
                desc = desc.strip()

                # 过滤无效参数名（比如空字符串、纯空格）
                if param_name and desc:
                    params_desc[param_name] = desc
                    current_param = param_name
                elif param_name:
                    # 只有参数名没有描述
                    params_desc[param_name] = ""
                    current_param = param_name

        # 拼接主描述（保留换行格式）
        full_description = "\n\n".join(main_desc_lines)

        return {"description": full_description, "params_desc": params_desc}

    def list_tools(self) -> Dict[str, Any]:
        tool_list = []
        for name, func in self.tools.items():
            doc_info = self._parse_docstring(func.__doc__)
            sig = inspect.signature(func)
            params = []
            for param in sig.parameters.values():
                # 获取参数类型（兼容无注解的情况）
                if param.annotation is not param.empty:
                    param_type = param.annotation.__name__
                else:
                    param_type = "str"  # 默认字符串类型
                # 获取参数描述
                param_desc = doc_info["params_desc"].get(param.name, "")
                params.append({
                    "name": param.name,
                    "type": param_type,
                    "description": param_desc
                })
            tool_list.append({
                "name": name,
                "description": doc_info["description"],
                "parameters": params
            })
        return {"tools": tool_list}

    def call_tool(self, name: str, **kwargs) -> Any:
        if name not in self.tools:
            raise ValueError(f"工具 {name} 不存在")
        return self.tools[name](**kwargs)

    def auto_discover_tools(self, package: str = "tools"):
        package_path = os.path.join(os.getcwd(), package)
        # 处理目录不存在的情况
        if not os.path.exists(package_path):
            print(f"警告：工具目录 {package_path} 不存在")
            return
        for filename in os.listdir(package_path):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = f"{package}.{filename[:-3]}"
                try:
                    importlib.import_module(module_name)
                except Exception as e:
                    print(f"加载工具模块 {module_name} 失败: {e}")


tool_registry = ToolRegistry()
tool = tool_registry.tool