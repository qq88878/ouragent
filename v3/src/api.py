"""
Agent微服务 - FastAPI应用
提供REST API接口供Java后端调用

接口清单:
  基础模块:
    GET  /health            - 健康检查
    GET  /agent/status      - Agent状态

  Agent模块:
    POST /agent/chat        - 对话
    POST /agent/tool        - 调用工具
    GET  /agent/tools       - 列出可用工具
    DELETE /agent/memory    - 清除记忆
"""

import sys
import io

# 确保标准输出使用 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional

# 导入配置和数据库
from config.settings import settings
from src.db.database import get_db, init_db, close_db
from sqlalchemy.ext.asyncio import AsyncSession

# 导入鉴权模块（服务间密钥验证）
from src.auth.security import get_current_user

# 导入核心模块
from src.core.agent import Agent
from src.core.tools import CalculatorTool, SearchTool


# ==================== FastAPI应用 ====================

app = FastAPI(
    title="Agent Service",
    description="Python Agent微服务 - 提供AI能力（供Java后端内部调用）",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局 Agent 实例
agent: Optional[Agent] = None


# ==================== 数据模型 ====================

class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    response: str
    agent_id: str
    status: str = "success"


class ToolRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]


class ToolResponse(BaseModel):
    result: Any
    tool_name: str
    status: str = "success"


# ==================== 生命周期 ====================

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    print("🚀 Agent Service 启动中...")
    await init_db()

    # 初始化 Agent 实例
    global agent
    agent = Agent(
        name="MainAgent",
        description="Main Agent for handling requests from Java backend",
        memory_size=settings.AGENT_DEFAULT_MEMORY_SIZE,
        tools=[CalculatorTool(), SearchTool()],
    )
    print("✅ Agent Service 启动完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    print("🛑 Agent Service 关闭中...")
    await close_db()
    print("✅ Agent Service 已关闭")


# ==================== 基础接口 ====================

@app.get("/health")
async def health_check():
    """健康检查 - 供K8s/Docker探活和Java后端调用"""
    return {
        "status": "healthy",
        "agent_available": agent is not None,
        "database": "connected",
        "redis": "connected",
    }


@app.get("/agent/status")
async def get_agent_status():
    """获取Agent运行状态"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent未初始化")

    return agent.get_status()


# ==================== Agent接口 ====================

@app.post("/agent/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    与Agent对话（需要服务间密钥）

    Java调用示例:
      POST /agent/chat
      X-Service-Key: <key>
      {"message": "你好", "context": {"session_id": "xxx"}}
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent未初始化")

    try:
        response = agent.chat(request.message, request.context)
        return ChatResponse(
            response=response,
            agent_id=agent.id,
            status="success",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/tool", response_model=ToolResponse)
async def call_tool(
    request: ToolRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    调用Agent工具（需要服务间密钥）

    Java调用示例:
      POST /agent/tool
      X-Service-Key: <key>
      {"tool_name": "calculator", "parameters": {"expression": "2+2"}}
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent未初始化")

    tool = agent.get_tool(request.tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"工具 {request.tool_name} 不存在")

    try:
        result = tool.execute(**request.parameters)
        return ToolResponse(
            result=result,
            tool_name=request.tool_name,
            status="success",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/tools")
async def list_tools():
    """列出所有可用工具（无需鉴权）"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent未初始化")

    return {"tools": agent.list_tools()}


@app.delete("/agent/memory")
async def clear_memory(current_user: dict = Depends(get_current_user)):
    """清除Agent记忆（需要服务间密钥）"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent未初始化")

    agent.clear_memory()
    return {"message": "记忆已清除"}
