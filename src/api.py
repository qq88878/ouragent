"""
Agent微服务 - FastAPI应用
提供REST API接口供Java后端调用
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uvicorn

from src.core.agent import Agent
from src.core.tools import CalculatorTool, SearchTool
from src.utils.config import get_config
from src.utils.logger import setup_logger, get_logger

# 初始化日志
setup_logger(level="INFO")
logger = get_logger()

# 创建FastAPI应用
app = FastAPI(
    title="Agent Service",
    description="Python Agent微服务 - 提供AI能力",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS（允许Java后端调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局Agent实例
agent: Optional[Agent] = None


# ==================== 数据模型 ====================

class ChatRequest(BaseModel):
    """对话请求"""
    message: str
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    """对话响应"""
    response: str
    agent_id: str
    status: str = "success"


class ToolRequest(BaseModel):
    """工具调用请求"""
    tool_name: str
    parameters: Dict[str, Any]


class ToolResponse(BaseModel):
    """工具调用响应"""
    result: Any
    tool_name: str
    status: str = "success"


class AgentStatus(BaseModel):
    """Agent状态"""
    id: str
    name: str
    description: str
    available_tools: List[str]
    memory_size: int


# ==================== 初始化 ====================

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化Agent"""
    global agent

    logger.info("Initializing Agent...")

    # 创建工具
    calculator = CalculatorTool()
    search = SearchTool()

    # 创建Agent
    agent = Agent(
        name="MainAgent",
        description="Main Agent for handling requests from Java backend",
        memory_size=200,
        tools=[calculator, search]
    )

    logger.info(f"Agent initialized: {agent.name} (ID: {agent.id})")


# ==================== API接口 ====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Agent Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "agent_available": agent is not None
    }


@app.get("/agent/status", response_model=AgentStatus)
async def get_agent_status():
    """获取Agent状态"""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    status = agent.get_status()
    return AgentStatus(**status)


@app.post("/agent/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    与Agent对话

    Java调用示例:
    ```java
    // 使用RestTemplate
    ChatRequest request = new ChatRequest("你好");
    ChatResponse response = restTemplate.postForObject(
        "http://agent-service:8000/agent/chat",
        request,
        ChatResponse.class
    );
    ```
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        logger.info(f"Chat request: {request.message[:50]}...")

        # 调用Agent
        response = agent.chat(request.message, request.context)

        return ChatResponse(
            response=response,
            agent_id=agent.id,
            status="success"
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/tool", response_model=ToolResponse)
async def call_tool(request: ToolRequest):
    """
    调用Agent工具

    Java调用示例:
    ```java
    ToolRequest request = new ToolRequest("calculator", Map.of("expression", "2+2"));
    ToolResponse response = restTemplate.postForObject(
        "http://agent-service:8000/agent/tool",
        request,
        ToolResponse.class
    );
    ```
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        tool = agent.get_tool(request.tool_name)
        if tool is None:
            raise HTTPException(
                status_code=404,
                detail=f"Tool not found: {request.tool_name}"
            )

        result = tool.execute(**request.parameters)

        return ToolResponse(
            result=result,
            tool_name=request.tool_name,
            status="success"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tool error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/tools")
async def list_tools():
    """列出所有可用工具"""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    return {
        "tools": agent.list_tools()
    }


@app.get("/agent/history")
async def get_history(limit: int = 50):
    """获取对话历史"""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    history = agent.get_conversation_history(limit=limit)
    return {
        "history": history,
        "total": len(agent.get_conversation_history())
    }


@app.delete("/agent/memory")
async def clear_memory():
    """清除Agent记忆"""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    agent.clear_memory()
    return {"status": "success", "message": "Memory cleared"}


# ==================== 批量接口 ====================

class BatchChatRequest(BaseModel):
    """批量对话请求"""
    messages: List[str]
    user_id: Optional[str] = None


@app.post("/agent/batch/chat")
async def batch_chat(request: BatchChatRequest):
    """
    批量对话接口

    Java调用示例:
    ```java
    BatchChatRequest request = new BatchChatRequest(List.of("问题1", "问题2"));
    BatchChatResponse response = restTemplate.postForObject(
        "http://agent-service:8000/agent/batch/chat",
        request,
        BatchChatResponse.class
    );
    ```
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    results = []
    for message in request.messages:
        try:
            response = agent.chat(message)
            results.append({
                "message": message,
                "response": response,
                "status": "success"
            })
        except Exception as e:
            results.append({
                "message": message,
                "response": None,
                "status": "error",
                "error": str(e)
            })

    return {
        "results": results,
        "total": len(results)
    }


# ==================== 运行 ====================

if __name__ == "__main__":
    config = get_config()

    uvicorn.run(
        "src.api:app",
        host=config.get("HOST", "0.0.0.0"),
        port=config.get_int("PORT", 8000),
        reload=config.get_bool("DEBUG", True)
    )
