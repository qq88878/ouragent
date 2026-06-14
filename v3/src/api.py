"""
Agent 微服务 API - 供 Java 后端调用

接口清单（对齐 Java AgentServiceClient）:
  GET  /health                  - 健康检查
  GET  /agent/status            - Agent 状态

  POST /agent/chat              - 对话（RAG 增强）
  POST /agent/chat/context      - 带上下文的对话（知识库 + 学生画像）

  POST /agent/knowledge/ingest  - 知识文档入库（向量化）
  GET  /agent/knowledge/status  - 查询知识库状态

  POST /agent/analyze           - 学生画像分析
  POST /agent/plan              - 生成学习路径
  POST /agent/generate          - 生成教学资源（题目/思维导图/摘要）
  POST /agent/evaluate          - 评估学生答案

  POST /agent/tool              - 直接调用工具
  GET  /agent/tools             - 列出可用工具
"""

import sys
import io
import json
import logging

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, field_validator
from typing import Literal

from config.settings import settings, DATA_DIR
from src.auth.security import get_current_user
from src.core.llm import create_llm_provider
from src.core.rag import RAGPipeline, VectorStore, create_embedding_provider
from src.core.agents import Orchestrator
from src.core.exceptions import AgentException, ValidationError, NotFoundError, ServiceUnavailableError
from src.middleware.rate_limit import RateLimitMiddleware

logger = logging.getLogger(__name__)


# ==================== 数据模型 ====================


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="用户消息")
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = Field(None, pattern=r"^[a-f0-9\-]{36}$", description="会话ID（UUID格式）")

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("消息不能为空")
        return v


class ChatResponse(BaseModel):
    response: str
    session_id: Optional[str] = None
    status: str = "success"


class ChatWithContextRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    context: Dict[str, Any] = {}
    session_id: Optional[str] = Field(None, pattern=r"^[a-f0-9\-]{36}$")


class CreateSessionRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    course_id: Optional[int] = Field(None, gt=0)


class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    course_id: Optional[int] = None
    created_at: str
    last_active: str
    message_count: int


class KnowledgeIngestRequest(BaseModel):
    knowledge_id: int = Field(..., gt=0)
    course_id: int = Field(..., gt=0)
    content: str = Field(..., min_length=1)
    file_type: Literal["txt", "md", "pdf", "docx", "pptx", "xlsx", "html"] = "txt"


class KnowledgeIngestResponse(BaseModel):
    knowledge_id: int
    chunks: int
    status: str


class AnalyzeRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    course_id: Optional[int] = Field(None, gt=0)
    chat_history: List[Dict[str, str]] = Field(default_factory=list, max_length=100)
    study_records: List[Dict[str, Any]] = Field(default_factory=list, max_length=100)
    current_profile: Optional[Dict[str, Any]] = None


class PlanRequest(BaseModel):
    student_profile: Dict[str, Any]
    course_title: str = Field(..., min_length=1, max_length=200)
    course_knowledge: List[Dict[str, Any]] = Field(default_factory=list, max_length=500)
    goal: str = Field(default="掌握课程核心知识", max_length=500)


class GenerateRequest(BaseModel):
    type: Literal["question", "mindmap", "summary"]
    topic: str = Field(..., min_length=1, max_length=200)
    knowledge_ids: Optional[List[int]] = None
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    count: int = Field(default=5, ge=1, le=20)


class EvaluateRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=5000)
    student_answer: str = Field(..., min_length=1, max_length=5000)
    reference_answer: str = Field(default="", max_length=5000)
    knowledge_context: str = Field(default="", max_length=10000)


class ToolRequest(BaseModel):
    tool_name: str = Field(..., min_length=1, max_length=50)
    parameters: Dict[str, Any] = {}


# ==================== 全局实例 ====================

orchestrator: Optional[Orchestrator] = None
rag_pipeline: Optional[RAGPipeline] = None


# ==================== 生命周期 ====================


@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator, rag_pipeline

    logger.info("Agent Service 启动中...")

    # 初始化 LLM
    try:
        llm = create_llm_provider()
        logger.info("LLM 初始化完成: %s", type(llm).__name__)
    except Exception as e:
        logger.warning("LLM 初始化失败，将以 Echo 模式运行: %s", e)
        llm = None

    # TODO: Embedding 当前降级为本地 TF-IDF（MIMO 不支持 /embeddings 端点）
    #       后续接入星火/其他有 Embedding API 的服务后，改为 provider="openai"
    #       只需在 .env 中配置 EMBEDDING_API_KEY / EMBEDDING_BASE_URL / EMBEDDING_MODEL
    has_embedding_api = (
        settings.EMBEDDING_API_KEY
        and settings.EMBEDDING_BASE_URL
        and "mimo" not in (settings.EMBEDDING_BASE_URL or "").lower()
    )
    embedding_provider = create_embedding_provider(
        provider="openai" if has_embedding_api else "local",
        api_key=settings.embedding_api_key,
        base_url=settings.embedding_base_url,
        model=settings.EMBEDDING_MODEL,
    )
    vector_store = VectorStore(dimension=768)
    rag_pipeline = RAGPipeline(
        vector_store=vector_store,
        embedding_provider=embedding_provider,
    )

    # 尝试从磁盘加载已有向量数据
    vector_store.load(str(DATA_DIR / "vector_store.json"))

    # 初始化 Orchestrator（多 Agent 编排器）
    orchestrator = Orchestrator(llm=llm, rag_pipeline=rag_pipeline)
    logger.info("Agent Service 启动完成")

    yield

    # 关闭时保存向量数据
    logger.info("Agent Service 关闭中...")
    vector_store.save(str(DATA_DIR / "vector_store.json"))
    logger.info("Agent Service 已关闭")


app = FastAPI(
    title="Agent Service",
    description="RAG 增强的教育智能体微服务",
    version="4.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 限流中间件
if settings.APP_ENV != "development":
    app.add_middleware(RateLimitMiddleware)


# ==================== 异常处理器 ====================


@app.exception_handler(AgentException)
async def agent_exception_handler(request: Request, exc: AgentException):
    """处理自定义业务异常"""
    logger.warning("业务异常: %s - %s", exc.code, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理未捕获的系统异常"""
    logger.error("系统异常: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "服务内部错误，请稍后重试",
            }
        },
    )


# ==================== 基础接口 ====================


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agent_available": orchestrator is not None,
        "rag_available": rag_pipeline is not None,
    }


@app.get("/agent/status")
async def get_agent_status():
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")
    return orchestrator.get_status()


# ==================== 对话接口 ====================


@app.post("/agent/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, _: dict = Depends(get_current_user)):
    """
    RAG 增强对话（支持会话记忆）

    Java 调用:
      POST /agent/chat
      {"message": "什么是Python列表？", "context": {"knowledge_ids": [1, 2]}, "session_id": "xxx"}
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        response = await orchestrator.chat(
            request.message,
            request.context,
            session_id=request.session_id,
        )
        return ChatResponse(response=response, session_id=request.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/chat/context", response_model=ChatResponse)
async def chat_with_context(request: ChatWithContextRequest, _: dict = Depends(get_current_user)):
    """
    带完整上下文的对话（Java AgentServiceClient.chatWithContext）

    context 可包含:
      - knowledge_ids: 知识库 ID 列表
      - student_profile: 学生画像
      - history: 对话历史（如果提供 session_id，优先使用 Redis 中的历史）
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        response = await orchestrator.chat(
            request.message,
            request.context,
            session_id=request.session_id,
        )
        return ChatResponse(response=response, session_id=request.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 流式对话接口 ====================


SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


@app.post("/agent/chat/stream")
async def chat_stream(request: ChatRequest, _: dict = Depends(get_current_user)):
    """流式对话（SSE）— 前端 fetch ReadableStream 消费"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    async def event_generator():
        try:
            async for chunk in orchestrator.stream_chat(
                request.message, request.context, session_id=request.session_id,
            ):
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=SSE_HEADERS)


@app.post("/agent/chat/context/stream")
async def chat_with_context_stream(request: ChatWithContextRequest, _: dict = Depends(get_current_user)):
    """带上下文的流式对话（SSE）— Java AgentServiceClient 调用"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    async def event_generator():
        try:
            async for chunk in orchestrator.stream_chat(
                request.message, request.context, session_id=request.session_id,
            ):
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=SSE_HEADERS)


# ==================== 知识库接口 ====================


@app.post("/agent/knowledge/ingest")
async def ingest_knowledge(
    file: UploadFile = File(...),
    knowledge_id: int = Form(...),
    course_id: int = Form(...),
    _: dict = Depends(get_current_user),
):
    """
    知识文档入库（Java AgentServiceClient.ingestKnowledge）

    接收上传的文件，解析文本 -> 分块 -> 向量化 -> 存入向量库
    """
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="RAG 未初始化")

    try:
        content = await file.read()
        chunks = await rag_pipeline.ingest_bytes(
            content=content,
            filename=file.filename or "unknown.txt",
            knowledge_id=knowledge_id,
            extra_metadata={"course_id": course_id},
        )
        return {
            "knowledge_id": knowledge_id,
            "chunks": chunks,
            "status": "indexed" if chunks > 0 else "failed",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/knowledge/ingest-text")
async def ingest_knowledge_text(
    request: KnowledgeIngestRequest,
    _: dict = Depends(get_current_user),
):
    """
    文本内容入库（备用接口，直接传文本）
    """
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="RAG 未初始化")

    try:
        chunks = await rag_pipeline.ingest_text(
            text=request.content,
            source=f"knowledge_{request.knowledge_id}",
            knowledge_id=request.knowledge_id,
            extra_metadata={"course_id": request.course_id, "file_type": request.file_type},
        )
        return KnowledgeIngestResponse(
            knowledge_id=request.knowledge_id,
            chunks=chunks,
            status="indexed" if chunks > 0 else "failed",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/knowledge/status")
async def get_knowledge_status(_: dict = Depends(get_current_user)):
    """查询知识库状态"""
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="RAG 未初始化")
    return rag_pipeline.stats()


# ==================== 多 Agent 接口 ====================


@app.post("/agent/analyze")
async def analyze_profile(request: AnalyzeRequest, _: dict = Depends(get_current_user)):
    """
    学生画像分析（带缓存）

    分析学生学习历史，返回学习风格、薄弱点等结构化画像。
    结果会缓存到 Redis，相同 user_id + course_id 的请求会返回缓存结果。
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        result = await orchestrator.analyze_profile(
            user_id=request.user_id,
            chat_history=request.chat_history,
            study_records=request.study_records,
            current_profile=request.current_profile,
            course_id=request.course_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/plan")
async def generate_plan(request: PlanRequest, _: dict = Depends(get_current_user)):
    """
    生成学习路径（Java AgentServiceClient.generateLearningPath）
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        result = await orchestrator.generate_learning_path(
            student_profile=request.student_profile,
            course_title=request.course_title,
            course_knowledge=request.course_knowledge,
            goal=request.goal,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/generate")
async def generate_resource(request: GenerateRequest, _: dict = Depends(get_current_user)):
    """
    生成教学资源（题目/思维导图/摘要）

    Java 调用示例:
      POST /agent/generate
      {"type": "question", "topic": "Python列表", "difficulty": "medium", "count": 5}
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        result = await orchestrator.generate_resource(
            resource_type=request.type,
            topic=request.topic,
            knowledge_ids=request.knowledge_ids,
            difficulty=request.difficulty,
            count=request.count,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/evaluate")
async def evaluate_answer(request: EvaluateRequest, _: dict = Depends(get_current_user)):
    """
    评估学生答案（Java AgentServiceClient.evaluateAnswer）
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        result = await orchestrator.evaluate_answer(
            question=request.question,
            student_answer=request.student_answer,
            reference_answer=request.reference_answer,
            knowledge_context=request.knowledge_context,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 工具接口 ====================


@app.get("/agent/tools")
async def list_tools():
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")
    return {"tools": orchestrator.tools.list_tools()}


@app.post("/agent/tool")
async def call_tool(request: ToolRequest, _: dict = Depends(get_current_user)):
    """
    直接调用工具

    Java 调用:
      POST /agent/tool
      {"tool_name": "knowledge_retrieval", "parameters": {"query": "Python列表"}}
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        result = await orchestrator.tools.execute(request.tool_name, **request.parameters)
        return {"result": result, "tool_name": request.tool_name, "status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 会话管理接口 ====================


@app.post("/agent/sessions")
async def create_session(
    request: CreateSessionRequest,
    _: dict = Depends(get_current_user),
):
    """
    创建新会话

    Java 调用:
      POST /agent/sessions
      {"user_id": "123", "course_id": 1}
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        session_id = await orchestrator.create_session(
            user_id=request.user_id,
            course_id=request.course_id,
        )
        return {"session_id": session_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/sessions/{session_id}")
async def get_session(
    session_id: str,
    _: dict = Depends(get_current_user),
):
    """获取会话信息"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    session = await orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    return session


@app.delete("/agent/sessions/{session_id}")
async def delete_session(
    session_id: str,
    _: dict = Depends(get_current_user),
):
    """删除会话（同时清除对话历史）"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    deleted = await orchestrator.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"status": "deleted", "session_id": session_id}


@app.get("/agent/sessions/{session_id}/history")
async def get_conversation_history(
    session_id: str,
    limit: int = 50,
    _: dict = Depends(get_current_user),
):
    """
    获取对话历史

    Java 调用:
      GET /agent/sessions/{session_id}/history?limit=50
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        history = await orchestrator.get_conversation_history(session_id, limit)
        return {"session_id": session_id, "messages": history, "count": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/users/{user_id}/sessions")
async def list_user_sessions(
    user_id: str,
    limit: int = 20,
    _: dict = Depends(get_current_user),
):
    """
    列出用户的所有会话

    Java 调用:
      GET /agent/users/{user_id}/sessions?limit=20
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        sessions = await orchestrator.list_user_sessions(user_id, limit)
        return {"user_id": user_id, "sessions": sessions, "count": len(sessions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 学习进度接口 ====================


class CompleteStepRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    course_id: int = Field(..., gt=0)
    step_id: int = Field(..., ge=0)
    duration_minutes: int = Field(default=0, ge=0)


class UpdateMasteryRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    knowledge_id: int = Field(..., gt=0)
    score_delta: float = Field(..., ge=-100, le=100)


class RecordAnswerRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    question_id: str = Field(..., min_length=1)
    is_correct: bool
    knowledge_id: Optional[int] = Field(None, gt=0)


@app.get("/agent/progress/{user_id}/course/{course_id}")
async def get_course_progress(
    user_id: str,
    course_id: int,
    _: dict = Depends(get_current_user),
):
    """
    获取用户在某课程的学习进度

    Java 调用:
      GET /agent/progress/{user_id}/course/{course_id}
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        progress = await orchestrator.get_course_progress(user_id, course_id)
        return progress
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/progress/complete-step")
async def complete_learning_step(
    request: CompleteStepRequest,
    _: dict = Depends(get_current_user),
):
    """
    完成一个学习步骤

    Java 调用:
      POST /agent/progress/complete-step
      {"user_id": "123", "course_id": 1, "step_id": 0, "duration_minutes": 30}
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        progress = await orchestrator.complete_learning_step(
            user_id=request.user_id,
            course_id=request.course_id,
            step_id=request.step_id,
            duration_minutes=request.duration_minutes,
        )
        return progress
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/mastery/{user_id}")
async def get_knowledge_mastery(
    user_id: str,
    knowledge_ids: Optional[str] = None,
    _: dict = Depends(get_current_user),
):
    """
    获取知识点掌握度

    Java 调用:
      GET /agent/mastery/{user_id}?knowledge_ids=1,2,3
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        ids = None
        if knowledge_ids:
            ids = [int(kid.strip()) for kid in knowledge_ids.split(",")]
        mastery = await orchestrator.get_knowledge_mastery(user_id, ids)
        # 将 int key 转为 string（JSON 要求）
        return {"user_id": user_id, "mastery": {str(k): v for k, v in mastery.items()}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/mastery/update")
async def update_knowledge_mastery(
    request: UpdateMasteryRequest,
    _: dict = Depends(get_current_user),
):
    """
    更新知识点掌握度

    Java 调用:
      POST /agent/mastery/update
      {"user_id": "123", "knowledge_id": 1, "score_delta": 5.0}
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        new_score = await orchestrator.update_knowledge_mastery(
            user_id=request.user_id,
            knowledge_id=request.knowledge_id,
            score_delta=request.score_delta,
        )
        return {"new_score": new_score, "status": "updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/stats/{user_id}")
async def get_learning_stats(
    user_id: str,
    _: dict = Depends(get_current_user),
):
    """
    获取学习统计

    Java 调用:
      GET /agent/stats/{user_id}
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        stats = await orchestrator.get_learning_stats(user_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/summary/{user_id}")
async def get_learning_summary(
    user_id: str,
    _: dict = Depends(get_current_user),
):
    """
    获取学习摘要（包含统计、薄弱点、建议）

    Java 调用:
      GET /agent/summary/{user_id}
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        summary = await orchestrator.get_learning_summary(user_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/history/{user_id}")
async def get_learning_history(
    user_id: str,
    limit: int = 20,
    _: dict = Depends(get_current_user),
):
    """
    获取学习历史记录

    Java 调用:
      GET /agent/history/{user_id}?limit=20
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        history = await orchestrator.get_learning_history(user_id, limit)
        return {"user_id": user_id, "history": history, "count": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/answer/result")
async def record_answer_result(
    request: RecordAnswerRequest,
    _: dict = Depends(get_current_user),
):
    """
    记录答题结果

    Java 调用:
      POST /agent/answer/result
      {"user_id": "123", "question_id": "q1", "is_correct": true, "knowledge_id": 1}
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        result = await orchestrator.record_answer_result(
            user_id=request.user_id,
            question_id=request.question_id,
            is_correct=request.is_correct,
            knowledge_id=request.knowledge_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
