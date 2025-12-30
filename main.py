# main.py 完整生产级版本
import inspect
from json import JSONDecodeError

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional, Union, List
from tool_registry import tool_registry
import uvicorn
import json
import logging

# 生产级日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-server")

app = FastAPI(title="生产级 MCP Server (JSON-RPC 2.0)", version="1.0")

# 启动时自动扫描 tools 目录（生产级容错）
try:
    tool_registry.auto_discover_tools("tools")
    logger.info(f"成功加载 {len(tool_registry.tools)} 个工具")
except Exception as e:
    logger.error(f"工具加载失败: {e}")
    raise RuntimeError("生产环境工具加载失败，服务启动终止")


# ------------------------------
# 基础模型（生产级）
# ------------------------------
class ToolRequest(BaseModel):
    parameters: Dict[str, Any]


class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class JSONRPCError(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None


class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None


# ------------------------------
# 保留原有接口（过渡期兼容，生产环境可逐步下线）
# ------------------------------
@app.get("/mcp/v1/tools", tags=["兼容层"])
async def list_tools():
    return tool_registry.list_tools()


@app.post("/mcp/v1/tools/{tool_name}", tags=["兼容层"])
async def call_tool(tool_name: str, request: ToolRequest):
    try:
        result = tool_registry.call_tool(tool_name, **request.parameters)
        return {"result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"工具调用失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ------------------------------
# 生产级JSON-RPC 2.0核心接口（MCP标准）
# ------------------------------
@app.post("/mcp/v1/rpc", tags=["MCP 标准接口"])
async def json_rpc_handler(request: Request):
    """
    生产级JSON-RPC 2.0接口（符合MCP规范）
    支持：单请求/批量请求、标准化错误、日志审计
    """
    try:
        # 1. 解析请求体（生产级容错）
        raw_body = await request.body()
        if not raw_body:
            raise ValueError("空请求体")

        # 兼容批量请求（MCP生产环境常见场景）
        body_data = json.loads(raw_body)
        is_batch = isinstance(body_data, list)
        requests = body_data if is_batch else [body_data]

        responses: List[JSONRPCResponse] = []
        for req in requests:
            try:
                rpc_req = JSONRPCRequest(**req)
                # 2. 协议校验（生产级）
                if rpc_req.jsonrpc != "2.0":
                    raise ValueError("仅支持JSON-RPC 2.0协议")

                # 3. 工具调用（生产级日志）
                logger.info(f"接收MCP调用请求: id={rpc_req.id}, method={rpc_req.method}")
                tool_name = rpc_req.method
                params = rpc_req.params or {}

                # 4. 工具存在性校验
                if tool_name not in tool_registry.tools:
                    error = JSONRPCError(
                        code=-32601,
                        message=f"工具 {tool_name} 不存在",
                        data={"available_tools": list(tool_registry.tools.keys())}
                    )
                    responses.append(JSONRPCResponse(id=rpc_req.id, error=error))
                    continue

                # 5. 工具执行（生产级异常捕获）
                try:
                    result = tool_registry.call_tool(tool_name, **params)
                    # MCP标准响应格式（包装value字段，兼容主流MCP客户端）
                    responses.append(JSONRPCResponse(
                        id=rpc_req.id,
                        result={"value": result}
                    ))
                    logger.info(f"MCP调用成功: id={rpc_req.id}, method={tool_name}")
                except TypeError as e:
                    # 参数不匹配（生产级详细错误）
                    sig = inspect.signature(tool_registry.tools[tool_name])
                    required_params = [p.name for p in sig.parameters.values()]
                    error = JSONRPCError(
                        code=-32602,
                        message="参数错误",
                        data={
                            "error": str(e),
                            "required_params": required_params,
                            "received_params": list(params.keys())
                        }
                    )
                    responses.append(JSONRPCResponse(id=rpc_req.id, error=error))
                except Exception as e:
                    # 工具执行内部错误（生产级不暴露敏感信息）
                    logger.error(f"工具执行失败: id={rpc_req.id}, method={tool_name}, error={e}")
                    error = JSONRPCError(
                        code=-32603,
                        message="工具执行失败",
                        data={"error_code": "TOOL_EXECUTE_FAILED"}  # 生产级脱敏
                    )
                    responses.append(JSONRPCResponse(id=rpc_req.id, error=error))

            except JSONDecodeError:
                # JSON解析失败
                error = JSONRPCError(code=-32700, message="无效的JSON格式")
                responses.append(JSONRPCResponse(id=None, error=error))
            except Exception as e:
                # 请求解析失败（生产级日志）
                logger.error(f"请求解析失败: {e}")
                error = JSONRPCError(code=-32600, message="无效的请求格式", data=str(e))
                responses.append(JSONRPCResponse(id=None, error=error))

        # 批量请求返回列表，单请求返回对象（MCP标准）
        return responses if is_batch else responses[0]

    except Exception as e:
        # 全局异常捕获（生产级兜底）
        logger.critical(f"RPC接口全局异常: {e}")
        return JSONRPCResponse(
            id=None,
            error=JSONRPCError(code=-32603, message="服务器内部错误")
        )


# ------------------------------
# 生产级健康检查接口（必加）
# ------------------------------
@app.get("/health", tags=["运维接口"])
async def health_check():
    return {
        "status": "healthy",
        "tool_count": len(tool_registry.tools),
        "version": "1.0"
    }


if __name__ == "__main__":
    # 生产级启动配置（端口、日志、重启策略）
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info",
        access_log=True  # 生产级访问日志
    )