"""
Agent微服务 - FastAPI应用
提供REST API接口供Java后端调用

接口清单:
  认证模块:
    POST /auth/register     - 用户注册
    POST /auth/login        - 用户登录
    POST /auth/refresh      - 刷新令牌
    GET  /auth/me           - 获取当前用户信息

  Agent模块:
    GET  /health            - 健康检查
    GET  /agent/status      - Agent状态
    POST /agent/chat        - 对话
    POST /agent/tool        - 调用工具
    GET  /agent/tools       - 列出可用工具
    GET  /agent/history     - 对话历史
    DELETE /agent/memory    - 清除记忆
"""

import sys
import io

# 确保标准输出使用 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Dict, List, Any, Optional
from datetime import timedelta

# 导入配置和数据库
from config.settings import settings
from db.database import get_db, init_db, close_db
from sqlalchemy.ext.asyncio import AsyncSession

# 导入认证模块
from auth.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    get_current_user,
)

# 导入核心模块
from src.core.agent import Agent
from src.core.tools import CalculatorTool, SearchTool


# ==================== FastAPI应用 ====================

app = FastAPI(
    title="Agent Service",
    description="Python Agent微服务 - 提供AI能力",
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

# 认证相关
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str] = None


# Agent相关
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


# ==================== 认证接口 ====================

@app.post("/auth/register", response_model=UserResponse)
async def register(user: UserRegister, db: AsyncSession = Depends(get_db)):
    """用户注册"""
    # TODO: 检查用户是否已存在
    # TODO: 创建用户并保存密码哈希
    # user_data = {
    #     "username": user.username,
    #     "email": user.email,
    #     "hashed_password": get_password_hash(user.password),
    #     "full_name": user.full_name,
    # }
    # new_user = User(**user_data)
    # db.add(new_user)
    # await db.commit()
    # await db.refresh(new_user)

    # 临时返回
    return {
        "id": "temp-id",
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
    }


@app.post("/auth/login", response_model=TokenResponse)
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    # TODO: 查询用户
    # TODO: 验证密码
    # user = await db.execute(select(User).where(User.username == user.username))
    # user = user.scalar_one_or_none()
    # if not user or not verify_password(user.password, user.hashed_password):
    #     raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 创建令牌
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@app.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """刷新令牌"""
    # TODO: 验证 refresh token
    # TODO: 生成新的 access token
    from auth.security import decode_token

    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="无效的刷新令牌")

    new_access_token = create_access_token(data={"sub": payload.get("sub")})

    return {
        "access_token": new_access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@app.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "id": current_user.get("sub"),
        "username": current_user.get("sub"),
        "email": "user@example.com",
        "full_name": None,
    }


# ==================== Agent API接口 ====================

@app.get("/health")
async def health_check():
    """健康检查 - 供K8s/Docker探活使用"""
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


@app.post("/agent/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    与Agent对话 (需要认证)

    Java调用示例:
      POST /agent/chat
      Authorization: Bearer <token>
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
    调用Agent工具 (需要认证)

    Java调用示例:
      POST /agent/tool
      Authorization: Bearer <token>
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
    """列出所有可用工具"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent未初始化")

    return {"tools": agent.list_tools()}


@app.get("/agent/history")
async def get_history(
    limit: Optional[int] = 50,
    offset: Optional[int] = 0,
    current_user: dict = Depends(get_current_user)
):
    """获取对话历史 (需要认证)"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent未初始化")

    history = agent.get_conversation_history(limit=limit)
    return {"history": history, "total": len(history)}


@app.delete("/agent/memory")
async def clear_memory(current_user: dict = Depends(get_current_user)):
    """清除Agent记忆 (需要认证)"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent未初始化")

    agent.clear_memory()
    return {"message": "记忆已清除"}
