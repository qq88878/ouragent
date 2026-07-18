"""
Agent 微服务 API - 供 Java 后端调用

接口清单（对齐 Java AgentServiceClient）:
  GET  /health                  - 健康检查
  GET  /agent/status            - Agent 状态

  POST /agent/chat              - 对话（RAG 增强，支持 context 和 session_id）
  POST /agent/chat/stream       - 流式对话（SSE）

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
from pydantic import BaseModel, Field, field_validator, model_validator
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
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文（knowledge_ids, basic_profile 等）")
    session_id: Optional[str] = None

    @field_validator("session_id", mode="before")
    @classmethod
    def coerce_session_id(cls, v):
        return str(v) if v is not None else v

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


class BasicProfileRequest(BaseModel):
    """基础画像分析请求 — 简洁问卷数据"""
    user_id: str = Field(..., min_length=1, max_length=100)
    education_level: str = Field(default="", max_length=50, description="学历阶段: HIGH_SCHOOL/ASSOCIATE/BACHELOR/MASTER/PHD/OTHER")
    major_direction: str = Field(default="", max_length=100, description="专业/兴趣方向")
    learning_goals: List[str] = Field(default_factory=list, max_length=10, description="学习目标")
    subject_level: str = Field(default="", max_length=50, description="当前学科水平: ZERO_BASIC/BEGINNER/INTERMEDIATE/ADVANCED")
    learning_methods: List[str] = Field(default_factory=list, max_length=10, description="偏好学习方式: VIDEO/READING/HANDS_ON/DISCUSSION/LECTURE/QUIZ")
    session_duration: str = Field(default="", max_length=50, description="单次学习时长")
    focus_level: str = Field(default="", max_length=50, description="专注力水平")
    self_strengths: List[str] = Field(default_factory=list, max_length=10, description="自评优势")
    self_weaknesses: List[str] = Field(default_factory=list, max_length=10, description="自评不足")
    daily_study_hours: str = Field(default="", max_length=50, description="每日学习时间")


class AnalyzeRequest(BaseModel):
    """课程画像分析请求 — 基础画像 + 对话历史"""
    user_id: str = Field(..., min_length=1, max_length=100)
    course_id: Optional[int] = Field(None, gt=0)
    basic_profile: Dict[str, Any] = Field(default_factory=dict, description="基础画像（来自问卷分析）")
    chat_history: List[Dict[str, str]] = Field(default_factory=list, max_length=100)
    study_records: List[Dict[str, Any]] = Field(default_factory=list, max_length=100)


class PlanRequest(BaseModel):
    basic_profile: Dict[str, Any] = Field(default_factory=dict, description="基础画像（跨课程共享）")
    course_title: str = Field(default="课程", max_length=200)
    course_description: str = Field(default="", max_length=500, description="课程描述")
    course_knowledge: List[Dict[str, Any]] = Field(default_factory=list, max_length=500)
    goal: str = Field(default="掌握课程核心知识", max_length=500)
    schedule: Optional[Dict[str, Any]] = Field(default=None, description="课表信息")

    chat_signals: Dict[str, Any] = Field(default_factory=dict, description="对话信号，用于画像增强")
    study_records: List[Dict[str, Any]] = Field(default_factory=list, max_length=100, description="本课程学习记录")
    evaluation_history: List[Dict[str, Any]] = Field(default_factory=list, max_length=100, description="评估历史")
    prior_paths: List[Dict[str, Any]] = Field(default_factory=list, max_length=50, description="历史学习路径")

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data):
        # 兼容 Java 客户端: student_profile → basic_profile
        if isinstance(data, dict):
            if "student_profile" in data and "basic_profile" not in data:
                data["basic_profile"] = data.pop("student_profile")
            # course_id 不是必需的，忽略
            data.pop("course_id", None)
        return data


class GenerateRequest(BaseModel):
    type: str = Field(..., min_length=1, description="question|mindmap|summary|generate_questions|generate_mindmap|generate_summary")
    topic: str = Field(..., min_length=1, max_length=200)
    knowledge_ids: Optional[List[int]] = None
    difficulty: str = Field(default="medium", description="easy|medium|hard|mixed")
    count: int = Field(default=5, ge=1, le=20)
    question_type: str = Field(default="mixed")
    student_profile: Dict[str, Any] = Field(default_factory=dict, description="Optional student profile for personalization")

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, v: str) -> str:
        mapping = {"generate_questions": "question", "generate_mindmap": "mindmap", "generate_summary": "summary"}
        return mapping.get(v, v)

class EvaluateRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=5000)
    student_answer: str = Field(..., min_length=1, max_length=5000)
    reference_answer: str = Field(default="", max_length=5000)
    knowledge_context: str = Field(default="", max_length=10000)


class QAWithCheckRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    context: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None
    max_retries: int = Field(default=2, ge=0, le=5)
    quality_threshold: float = Field(default=70.0, ge=0, le=100)

    @field_validator("session_id", mode="before")
    @classmethod
    def coerce_session_id(cls, v):
        return str(v) if v is not None else v


class DiagnosePracticeRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    question: str = Field(..., min_length=1, max_length=5000)
    student_answer: str = Field(..., min_length=1, max_length=5000)
    correct_answer: str = Field(default="", max_length=5000)
    course_id: Optional[int] = Field(None, gt=0)


class ChatPathRequest(BaseModel):
    messages: List[Dict[str, str]] = Field(..., min_length=1, max_length=100)
    course_id: Optional[str] = None
    course_title: str = Field(default="", max_length=200)
    course_description: str = Field(default="", max_length=500)


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

    # 初始化 Embedding Provider
    # 优先使用配置的 Embedding API，否则降级为本地 TF-IDF
    has_embedding_api = (
        settings.EMBEDDING_API_KEY
        and settings.EMBEDDING_BASE_URL
        and "mimo" not in (settings.EMBEDDING_BASE_URL or "").lower()
    )

    if has_embedding_api:
        logger.info("使用 Embedding API: %s / %s", settings.EMBEDDING_BASE_URL, settings.EMBEDDING_MODEL)
        embedding_provider = create_embedding_provider(
            provider="openai",
            api_key=settings.embedding_api_key,
            base_url=settings.embedding_base_url,
            model=settings.EMBEDDING_MODEL,
        )
    else:
        logger.info("未配置 Embedding API，使用本地 TF-IDF 嵌入")
        embedding_provider = create_embedding_provider(provider="local")

    # 动态获取向量维度（API 嵌入返回后更新，本地默认 384）
    embedding_dim = getattr(embedding_provider, '_dimension', 384)
    vector_store = VectorStore(dimension=embedding_dim)
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
    RAG 增强对话（支持会话记忆 + 上下文）

    context 可包含:
      - knowledge_ids: 知识库 ID 列表
      - student_profile: 学生画像
      - history: 对话历史（如果提供 session_id，优先使用 Redis 中的历史）

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


# ==================== 流式对话接口 ====================


SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


@app.post("/agent/chat/stream")
async def chat_stream(request: ChatRequest, _: dict = Depends(get_current_user)):
    """流式对话（SSE）— 前端 fetch ReadableStream / Java SSE 消费"""
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


@app.post("/agent/chat/stream-quality-check")
async def stream_chat_with_quality_check(request: QAWithCheckRequest, _: dict = Depends(get_current_user)):
    """流式深度答疑 — 先流式返回回答，后台异步质检"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    async def event_generator():
        try:
            async for event in orchestrator.stream_answer_with_quality_check(
                question=request.message,
                context=request.context,
                session_id=request.session_id,
                quality_threshold=request.quality_threshold,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=SSE_HEADERS)


# ==================== 知识库接口 ====================


async def _extract_topic_keywords_for_knowledge(
    knowledge_id: int,
    source_name: str,
    title: str,
    metadata: dict,
    content: str,
    use_llm: Optional[bool] = None,
) -> list:
    """从文档中提取话题关键词（规则提取 + 可选 LLM 语义提取）
    use_llm: None = 自动（有 LLM 就用），True = 强制启用，False = 强制禁用
    """
    topics = []
    if orchestrator is not None:
        try:
            await orchestrator._ensure_redis()
            if orchestrator._topic_kw_mgr is not None:
                mapping = await orchestrator._topic_kw_mgr.extract_and_register(
                    knowledge_id=knowledge_id,
                    source_name=source_name,
                    title=title,
                    metadata=metadata,
                    content_preview=content[:1000],
                    use_llm=use_llm,
                )
                topics = list(set(mapping.values()))
        except Exception as e:
            logger.debug("话题关键词提取失败（不影响文档入库）: %s", e)
    return topics


@app.post("/agent/knowledge/ingest")
async def ingest_knowledge(
    file: UploadFile = File(...),
    knowledge_id: int = Form(...),
    course_id: int = Form(0),
    use_llm: Optional[bool] = Form(None),
    _: dict = Depends(get_current_user),
):
    """
    知识文档入库（Java AgentServiceClient.ingestKnowledge）

    接收上传的文件，解析文本 -> 分块 -> 向量化 -> 存入向量库
    + 自动提取话题关键词（规则 + 可选 LLM 语义提取）

    - use_llm: None=自动（有 LLM Provider 就启用），True=强制启用，False=强制禁用
    """
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="RAG 未初始化")

    try:
        content = await file.read()
        filename = file.filename or "unknown.txt"
        chunks = await rag_pipeline.ingest_bytes(
            content=content,
            filename=filename,
            knowledge_id=knowledge_id,
            extra_metadata={"course_id": course_id},
        )
        # ⭐ 自动提取话题关键词（规则 + 可选 LLM）
        text_content = content.decode("utf-8", errors="ignore") if isinstance(content, bytes) else content
        topics = await _extract_topic_keywords_for_knowledge(
            knowledge_id=knowledge_id,
            source_name=filename,
            title=filename,
            metadata={"course_id": course_id},
            content=text_content,
            use_llm=use_llm,
        )
        return {
            "knowledgeId": knowledge_id,
            "chunks": chunks,
            "status": "indexed" if chunks > 0 else "failed",
            "topics": topics,
            "llm_enabled": (orchestrator is not None and orchestrator.llm is not None),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/knowledge/ingest-text")
async def ingest_knowledge_text(
    request: KnowledgeIngestRequest,
    use_llm: Optional[bool] = None,
    _: dict = Depends(get_current_user),
):
    """
    文本内容入库（备用接口，直接传文本）
    + 自动提取话题关键词（规则 + 可选 LLM 语义提取）

    - use_llm: None=自动（有 LLM Provider 就启用），True=强制启用，False=强制禁用
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
        topics = await _extract_topic_keywords_for_knowledge(
            knowledge_id=request.knowledge_id,
            source_name=f"knowledge_{request.knowledge_id}",
            title=f"knowledge_{request.knowledge_id}",
            metadata={"course_id": request.course_id},
            content=request.content,
            use_llm=use_llm,
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


# ==================== 话题关键词管理 ====================

@app.get("/agent/topics")
async def list_topics(knowledge_id: Optional[int] = None,
                       _: dict = Depends(get_current_user)):
    """查询当前动态提取到的话题关键词
    - 不传 knowledge_id → 返回全局合并后的关键词
    - 传 knowledge_id → 只返回该知识库提取到的关键词
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")
    await orchestrator._ensure_redis()
    mgr = orchestrator._topic_kw_mgr
    llm_available = orchestrator.llm is not None if orchestrator else False
    if mgr is None:
        return {"dynamic_count": 0, "dynamic_keywords": {}, "llm_enabled": llm_available}
    if knowledge_id is not None:
        data = await mgr.list_by_knowledge(knowledge_id)
        return {"knowledge_id": knowledge_id, "data": data, "llm_enabled": llm_available}
    dynamic = await mgr.list_all()
    return {
        "dynamic_count": len(dynamic),
        "dynamic_keywords": dict(list(dynamic.items())[:100]),
        "llm_enabled": llm_available,
    }


@app.post("/agent/topics")
async def add_topic_keyword(keyword: str, canonical_name: str,
                              _: dict = Depends(get_current_user)):
    """人工添加关键词（导入新知识域时手工补齐）"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")
    await orchestrator._ensure_redis()
    if orchestrator._topic_kw_mgr is None:
        raise HTTPException(status_code=500, detail="关键词管理器未就绪")
    await orchestrator._topic_kw_mgr.add_keyword(keyword, canonical_name)
    return {"success": True, "keyword": keyword, "canonical_name": canonical_name}


@app.delete("/agent/topics")
async def delete_topic_keyword(keyword: str,
                                 _: dict = Depends(get_current_user)):
    """从全局动态词典中删除某个关键词"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")
    await orchestrator._ensure_redis()
    if orchestrator._topic_kw_mgr is None:
        raise HTTPException(status_code=500, detail="关键词管理器未就绪")
    removed = await orchestrator._topic_kw_mgr.remove_keyword(keyword)
    return {"success": removed, "keyword": keyword}


@app.delete("/agent/topics/all")
async def clear_all_topics(_: dict = Depends(get_current_user)):
    """⚠️ 清空全部动态关键词（用于调试/重建）"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")
    await orchestrator._ensure_redis()
    if orchestrator._topic_kw_mgr is None:
        raise HTTPException(status_code=500, detail="关键词管理器未就绪")
    await orchestrator._topic_kw_mgr.clear_all()
    return {"success": True, "message": "已清空，请重新导入文档以重建关键词"}


# ==================== 多 Agent 接口 ====================


@app.post("/agent/profile/basic")
async def analyze_basic_profile(request: BasicProfileRequest, _: dict = Depends(get_current_user)):
    """
    基础画像分析（简洁问卷 → LLM → 持久化）

    接收简洁问卷数据，调用 LLM 分析生成基础画像。
    基础画像跨课程共享，会缓存到 Redis。
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        result = await orchestrator.analyze_basic_profile(
            user_id=request.user_id,
            questionnaire_data={
                "education_level": request.education_level,
                "major_direction": request.major_direction,
                "learning_goals": request.learning_goals,
                "subject_level": request.subject_level,
                "learning_methods": request.learning_methods,
                "session_duration": request.session_duration,
                "focus_level": request.focus_level,
                "self_strengths": request.self_strengths,
                "self_weaknesses": request.self_weaknesses,
                "daily_study_hours": request.daily_study_hours,
            },
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================= Dimensions Scoring (data-driven radar) =================

class DimensionsRequest(BaseModel):
    """5-dimension scoring request - data-driven radar chart"""
    user_id: str = Field(..., min_length=1, max_length=100)
    basic_profile: Dict[str, Any] = Field(default_factory=dict)
    study_records: List[Dict[str, Any]] = Field(default_factory=list)
    evaluation_history: List[Dict[str, Any]] = Field(default_factory=list)
    chat_signals: Dict[str, Any] = Field(default_factory=dict)
    learning_path_progress: Dict[str, Any] = Field(default_factory=dict)


# =============== Profile Update (dynamic evolution) ===============

class ProfileUpdateRequest(BaseModel):
    """Profile update request - merges new signals into existing profile"""
    user_id: str = Field(..., min_length=1, max_length=100)
    current_profile: Dict[str, Any] = Field(default_factory=dict)
    new_signals: Dict[str, Any] = Field(default_factory=dict, description="Chat signals, quiz results, etc.")
    evaluation_results: List[Dict[str, Any]] = Field(default_factory=list)


@app.post("/agent/profile/update")
async def update_profile(request: ProfileUpdateRequest, _: dict = Depends(get_current_user)):
    """
    Update student profile based on new learning activity.

    Merges new chat signals and evaluation results into the existing profile.
    This enables dynamic profile evolution over time.
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    try:
        result = await orchestrator.update_profile_from_activity(
            user_id=request.user_id,
            current_profile=request.current_profile,
            new_signals=request.new_signals,
            evaluation_results=request.evaluation_results,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/profile/dimensions")
async def analyze_profile_dimensions(request: DimensionsRequest, _: dict = Depends(get_current_user)):
    """
    5-dimension ability scoring (data-driven radar chart)

    Generates 0-100 scores for 5 dimensions based on actual learning data:
      - Theoretical Knowledge
      - Practical Ability
      - Problem Solving
      - Innovative Thinking
      - Collaboration
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    try:
        result = await orchestrator.analyze_profile_dimensions(
            user_id=request.user_id,
            basic_profile=request.basic_profile,
            study_records=request.study_records,
            evaluation_history=request.evaluation_history,
            chat_signals=request.chat_signals,
            learning_path_progress=request.learning_path_progress,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/profile/course")
async def analyze_course_profile(request: AnalyzeRequest, _: dict = Depends(get_current_user)):
    """
    课程画像分析（基础画像 + 对话历史 → 不持久化）

    结合基础画像和本课程的对话历史，动态构建课程特有的学生理解。
    结果不持久化，每门课程的 Agent 独立调用。
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        result = await orchestrator.analyze_course_profile(
            user_id=request.user_id,
            basic_profile=request.basic_profile,
            chat_history=request.chat_history,
            study_records=request.study_records,
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
            basic_profile=request.basic_profile,
            course_title=request.course_title,
            course_description=request.course_description,
            course_knowledge=request.course_knowledge,
            goal=request.goal,
            schedule=request.schedule,
            chat_signals=request.chat_signals if request.chat_signals else None,
            study_records=request.study_records if request.study_records else None,
            evaluation_history=request.evaluation_history if request.evaluation_history else None,
            prior_paths=request.prior_paths if request.prior_paths else None,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/generate")
async def generate_resource(request: GenerateRequest, _: dict = Depends(get_current_user)):
    """
    Generate teaching resources (profile-aware)

    Accepts optional student_profile for personalized content generation.
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        result = await orchestrator.generate_resource(
            resource_type=request.type,
            topic=request.topic,
            knowledge_ids=request.knowledge_ids,
            difficulty=request.difficulty,
            count=request.count,
            question_type=request.question_type,
            student_profile=request.student_profile if request.student_profile else None,
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


@app.post("/agent/chat/quality-check")
async def chat_with_quality_check(request: QAWithCheckRequest, _: dict = Depends(get_current_user)):
    """
    智能答疑 + 质检工作流

    多 Agent 协作：RAG 检索 → LLM 生成 → EvaluatorAgent 质检 → 不达标则重试
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        result = await orchestrator.answer_with_quality_check(
            question=request.message,
            context=request.context,
            session_id=request.session_id,
            max_retries=request.max_retries,
            quality_threshold=request.quality_threshold,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/mistake-book/diagnose-practice")
async def diagnose_and_practice(request: DiagnosePracticeRequest, _: dict = Depends(get_current_user)):
    """
    错题诊断 + 专项练习工作流

    多 Agent 协作：EvaluatorAgent 评估 → ResourceAgent 生成练习 → 保存错题
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        result = await orchestrator.diagnose_and_practice(
            user_id=request.user_id,
            question=request.question,
            student_answer=request.student_answer,
            correct_answer=request.correct_answer,
            course_id=request.course_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/chat/learning-path")
async def generate_chat_learning_path(request: ChatPathRequest, user: dict = Depends(get_current_user)):
    """
    基于对话历史生成关联知识库的学习路径

    分析对话内容，提取已讨论知识点，检索知识库，规划后续学习路径
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        result = await orchestrator.generate_path_from_chat(
            messages=request.messages,
            course_id=request.course_id,
            course_title=request.course_title,
            course_description=request.course_description,
            user_id=str(user.get("sub", user.get("id", ""))),
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/events")
async def get_event_history(limit: int = 50, event: Optional[str] = None):
    """获取 Agent 事件历史（调试用）"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")
    return {"events": orchestrator.event_bus.get_history(limit=limit, event=event)}


@app.get("/agent/stats")
async def get_agent_stats():
    """获取 Agent 统计数据"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")
    return {
        "quality_stats": orchestrator._quality_stats,
        "subscribed_events": orchestrator.event_bus.get_subscribed_events(),
    }


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


@app.get("/agent/signals/{session_id}")
async def get_chat_signals(
    session_id: str,
    _: dict = Depends(get_current_user),
):
    """获取当前会话的实时学习画像信号"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        await orchestrator._ensure_redis()
        session_meta = await orchestrator.session_manager.get_session(session_id)
        if not session_meta:
            return {"session_id": session_id, "signals": {"active_topics": [], "topic_history": [], "difficulty_distribution": {"beginner": 0, "neutral": 0, "advanced": 0}, "question_count": 0, "gap_keywords": [], "question_type_dist": {}, "exchange_count": 0, "last_updated": None}}

        user_id = str(session_meta.get("user_id", ""))
        if not user_id or not orchestrator._signals_cache:
            return {"session_id": session_id, "signals": {"active_topics": [], "topic_history": [], "difficulty_distribution": {"beginner": 0, "neutral": 0, "advanced": 0}, "question_count": 0, "gap_keywords": [], "question_type_dist": {}, "exchange_count": 0, "last_updated": None}}

        signals = await orchestrator._signals_cache.get_signals(user_id, session_id)
        return {"session_id": session_id, "signals": signals}
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

# ==================== 错题本接口 ====================

class MistakeBookAddRequest(BaseModel):
    user_id: str = Field(..., description="用户ID")
    question: str = Field(..., description="题目内容")
    student_answer: str = Field(..., description="学生答案")
    correct_answer: str = Field(default="", description="正确答案")
    error_category: str = Field(default="concept_unclear", description="错误分类")
    course_id: Optional[int] = Field(default=None, description="课程ID")
    knowledge_id: Optional[int] = Field(default=None, description="知识点ID")
    knowledge_name: str = Field(default="", description="知识点名称")

class MistakeBookReviewRequest(BaseModel):
    mistake_id: str = Field(..., description="错题ID")
    recalled: bool = Field(..., description="是否回忆成功")

class MistakeBookDiagnoseRequest(BaseModel):
    user_id: str = Field(..., description="用户ID")
    question: str = Field(..., description="题目")
    student_answer: str = Field(..., description="学生答案")
    correct_answer: str = Field(default="", description="正确答案")
    course_id: Optional[int] = Field(default=None, description="课程ID")

@app.post("/agent/mistake-book/add")
async def add_mistake(request: MistakeBookAddRequest, _: dict = Depends(get_current_user)):
    if not orchestrator: raise HTTPException(status_code=503, detail="Agent 未初始化")
    try:
        result = await orchestrator.add_mistake(user_id=request.user_id, question=request.question, student_answer=request.student_answer, correct_answer=request.correct_answer, error_category=request.error_category, course_id=request.course_id, knowledge_id=request.knowledge_id, knowledge_name=request.knowledge_name)
        return result
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


@app.delete("/agent/mistake-book/{mistake_id}")
async def delete_mistake(mistake_id: str, _: dict = Depends(get_current_user)):
    """删除单条错题"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")
    try:
        result = await orchestrator.delete_mistake(mistake_id)
        if not result:
            raise HTTPException(status_code=404, detail="错题不存在")
        return {"success": True, "mistake_id": mistake_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/agent/mistake-book/user/{user_id}")
async def clear_mistakes(user_id: str, _: dict = Depends(get_current_user)):
    """清空用户所有错题"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")
    try:
        count = await orchestrator.clear_mistakes(user_id)
        return {"success": True, "deleted_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/mistake-book/list/{user_id}")
async def list_mistakes(user_id: str, course_id: Optional[int] = None, error_category: Optional[str] = None, limit: int = 50, offset: int = 0, _: dict = Depends(get_current_user)):
    if not orchestrator: raise HTTPException(status_code=503, detail="Agent 未初始化")
    try:
        result = await orchestrator.list_mistakes(user_id=user_id, course_id=course_id, error_category=error_category, limit=limit, offset=offset)
        return {"mistakes": result, "total": len(result)}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/mistake-book/review")
async def record_review(request: MistakeBookReviewRequest, _: dict = Depends(get_current_user)):
    if not orchestrator: raise HTTPException(status_code=503, detail="Agent 未初始化")
    try:
        result = await orchestrator.record_review(mistake_id=request.mistake_id, recalled=request.recalled)
        return result
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/mistake-book/stats/{user_id}")
async def get_mistake_stats(user_id: str, _: dict = Depends(get_current_user)):
    if not orchestrator: raise HTTPException(status_code=503, detail="Agent 未初始化")
    try:
        result = await orchestrator.get_mistake_stats(user_id)
        return result
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/mistake-book/due/{user_id}")
async def get_due_reviews(user_id: str, limit: int = 20, _: dict = Depends(get_current_user)):
    if not orchestrator: raise HTTPException(status_code=503, detail="Agent 未初始化")
    try:
        result = await orchestrator.get_due_reviews(user_id, limit)
        return {"due_reviews": result, "total": len(result)}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/mistake-book/diagnose")
async def diagnose_mistake(request: MistakeBookDiagnoseRequest, _: dict = Depends(get_current_user)):
    if not orchestrator: raise HTTPException(status_code=503, detail="Agent 未初始化")
    try:
        result = await orchestrator.diagnose_mistake(user_id=request.user_id, question=request.question, student_answer=request.student_answer, correct_answer=request.correct_answer, course_id=request.course_id)
        return result
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/mistake-book/practice")
async def generate_practice(request: MistakeBookDiagnoseRequest, _: dict = Depends(get_current_user)):
    if not orchestrator: raise HTTPException(status_code=503, detail="Agent 未初始化")
    try:
        result = await orchestrator.generate_practice(user_id=request.user_id, question=request.question, student_answer=request.student_answer, correct_answer=request.correct_answer, course_id=request.course_id)
        return result
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/mistake-book/daily-review")
async def daily_review_check(user_id: str = Form(...), _: dict = Depends(get_current_user)):
    if not orchestrator: raise HTTPException(status_code=503, detail="Agent 未初始化")
    try:
        result = await orchestrator.generate_daily_review_notifications(user_id)
        return {"notifications": result, "total": len(result)}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/mistake-book/notifications/{user_id}")
async def get_notifications(user_id: str, limit: int = 10, _: dict = Depends(get_current_user)):
    if not orchestrator: raise HTTPException(status_code=503, detail="Agent 未初始化")
    try:
        result = await orchestrator.get_pending_notifications(user_id, limit)
        return {"notifications": result, "total": len(result)}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

