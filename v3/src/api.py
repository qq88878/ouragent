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

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config.settings import settings, DATA_DIR
from src.auth.security import get_current_user
from src.core.llm import create_llm_provider
from src.core.rag import RAGPipeline, VectorStore, create_embedding_provider
from src.core.agents import Orchestrator


# ==================== 数据模型 ====================


class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    response: str
    status: str = "success"


class ChatWithContextRequest(BaseModel):
    message: str
    context: Dict[str, Any] = {}


class KnowledgeIngestRequest(BaseModel):
    knowledge_id: int
    course_id: int
    content: str
    file_type: str = "txt"


class KnowledgeIngestResponse(BaseModel):
    knowledge_id: int
    chunks: int
    status: str


class AnalyzeRequest(BaseModel):
    user_id: str
    course_id: Optional[int] = None
    chat_history: List[Dict[str, str]] = []
    study_records: List[Dict[str, Any]] = []
    current_profile: Optional[Dict[str, Any]] = None


class PlanRequest(BaseModel):
    student_profile: Dict[str, Any]
    course_title: str
    course_knowledge: List[Dict[str, Any]] = []
    goal: str = "掌握课程核心知识"


class GenerateRequest(BaseModel):
    type: str  # "question" | "mindmap" | "summary"
    topic: str
    knowledge_ids: Optional[List[int]] = None
    difficulty: str = "medium"
    count: int = 5


class EvaluateRequest(BaseModel):
    question: str
    student_answer: str
    reference_answer: str = ""
    knowledge_context: str = ""


class ToolRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = {}


# ==================== 全局实例 ====================

orchestrator: Optional[Orchestrator] = None
rag_pipeline: Optional[RAGPipeline] = None


# ==================== 生命周期 ====================


@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator, rag_pipeline

    print("Agent Service 启动中...")

    # 初始化 LLM
    try:
        llm = create_llm_provider()
        print(f"LLM 初始化完成: {type(llm).__name__}")
    except Exception as e:
        print(f"LLM 初始化失败，将以 Echo 模式运行: {e}")
        llm = None

    # 初始化 RAG Pipeline
    embedding_provider = create_embedding_provider(
        provider="openai",
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
    print("Agent Service 启动完成")

    yield

    # 关闭时保存向量数据
    print("Agent Service 关闭中...")
    vector_store.save(str(DATA_DIR / "vector_store.json"))
    print("Agent Service 已关闭")


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
    RAG 增强对话

    Java 调用:
      POST /agent/chat
      {"message": "什么是Python列表？", "context": {"knowledge_ids": [1, 2]}}
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        response = await orchestrator.chat(request.message, request.context)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/chat/context", response_model=ChatResponse)
async def chat_with_context(request: ChatWithContextRequest, _: dict = Depends(get_current_user)):
    """
    带完整上下文的对话（Java AgentServiceClient.chatWithContext）

    context 可包含:
      - knowledge_ids: 知识库 ID 列表
      - student_profile: 学生画像
      - session_id: 会话 ID
      - history: 对话历史
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        response = await orchestrator.chat(request.message, request.context)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
    学生画像分析（Java AgentServiceClient 无直接对应，供高级调用）

    分析学生学习历史，返回学习风格、薄弱点等结构化画像
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        result = await orchestrator.analyze_profile(
            chat_history=request.chat_history,
            study_records=request.study_records,
            current_profile=request.current_profile,
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
