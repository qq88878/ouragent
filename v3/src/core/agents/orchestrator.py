"""Orchestrator - 多 Agent 协作编排器，系统总入口"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..memory.redis_client import get_redis, RedisClient
from ..memory.session_manager import SessionManager
from ..memory.conversation_memory import ConversationMemory
from ..memory.profile_cache import ProfileCache, RAGCache
from ..rag.rag_pipeline import RAGPipeline
from ..tools.base import ToolRegistry
from ..tools.retrieval import RetrievalTool
from ..tools.web_search import WebSearchTool
from ..tools.question_gen import QuestionGenTool
from ..tools.mindmap_gen import MindmapGenTool
from ..tools.study_plan import StudyPlanTool
from .profile_agent import ProfileAgent
from .planner_agent import PlannerAgent
from .resource_agent import ResourceAgent
from .evaluator_agent import EvaluatorAgent

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    多智能体编排器

    职责：
    - 初始化并管理所有 Agent 和 Tool
    - 提供 RAG 增强的对话能力（主入口）
    - 将请求路由到对应的专业 Agent
    - 协调多 Agent 完成复杂任务（如生成学习路径 = 画像分析 + 路径规划）
    """

    def __init__(self, llm, rag_pipeline: RAGPipeline):
        self.llm = llm
        self.rag = rag_pipeline

        # Redis 记忆组件（懒初始化）
        self._redis_client: Optional[RedisClient] = None
        self._session_manager: Optional[SessionManager] = None
        self._profile_cache: Optional[ProfileCache] = None
        self._rag_cache: Optional[RAGCache] = None

        # 注册工具
        self.tools = ToolRegistry()
        self.tools.register(RetrievalTool(rag_pipeline))
        self.tools.register(WebSearchTool())
        self.tools.register(QuestionGenTool(llm))
        self.tools.register(MindmapGenTool(llm))
        self.tools.register(StudyPlanTool(llm))

        # 初始化 Agent（每个 Agent 挂载需要的工具）
        retrieval_tool = self.tools.get("knowledge_retrieval")

        self.profile_agent = ProfileAgent(llm)
        self.planner_agent = PlannerAgent(llm)
        self.resource_agent = ResourceAgent(llm, tools=[retrieval_tool])
        self.evaluator_agent = EvaluatorAgent(llm)

        logger.info("Orchestrator 初始化完成: 4 agents, %d tools", len(self.tools.list_tools()))

    async def _ensure_redis(self) -> RedisClient:
        """懒初始化 Redis 连接"""
        if self._redis_client is None:
            redis_conn = await get_redis()
            self._redis_client = RedisClient(redis_conn)
            self._session_manager = SessionManager(self._redis_client)
            self._profile_cache = ProfileCache(self._redis_client)
            self._rag_cache = RAGCache(self._redis_client)
            logger.info("Redis 记忆系统初始化完成")
        return self._redis_client

    @property
    def session_manager(self) -> SessionManager:
        return self._session_manager

    @property
    def profile_cache(self) -> ProfileCache:
        return self._profile_cache

    # ==================== 核心对话入口 ====================

    async def chat(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """
        RAG 增强对话 — 系统主入口

        流程:
        1. 从 context 提取 knowledge_ids 和 student_profile
        2. 如果有 session_id，从 Redis 加载对话历史
        3. 用 RAG 检索相关知识（带缓存）
        4. 构造个性化 system prompt
        5. 调用 LLM 生成回答
        6. 保存消息到 Redis

        Args:
            message: 用户消息
            context: {"knowledge_ids": [1,2], "student_profile": {...}}
            session_id: 会话ID（用于记忆对话历史）
        """
        context = context or {}
        knowledge_ids = context.get("knowledge_ids")
        student_profile = context.get("student_profile")

        # 初始化 Redis（如果需要）
        await self._ensure_redis()

        # 获取对话历史（优先从 Redis）
        history = context.get("history")
        if session_id and self._session_manager:
            conv = ConversationMemory(self._redis_client, session_id)
            history = await conv.get_recent_context_for_llm(max_messages=10)
            await self._session_manager.touch_session(session_id)

        # RAG 检索（带缓存）
        knowledge_context = ""
        if self._rag_cache:
            cached_results = await self._rag_cache.get_results(message, knowledge_ids)
            if cached_results:
                knowledge_context = "\n\n---\n\n".join(r["content"] for r in cached_results)
                logger.debug("RAG 缓存命中")

        if not knowledge_context:
            try:
                retrieved = await self.rag.retrieve(
                    query=message,
                    top_k=5,
                    knowledge_ids=knowledge_ids,
                )
                if retrieved:
                    knowledge_context = "\n\n---\n\n".join(r["content"] for r in retrieved)
                    # 缓存结果
                    if self._rag_cache:
                        await self._rag_cache.set_results(message, retrieved, knowledge_ids)
            except Exception as e:
                logger.warning("RAG 检索失败，降级为纯 LLM 对话: %s", e)

        # 构造个性化 prompt
        system_prompt = self._build_chat_system_prompt(student_profile, knowledge_context)

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history[-10:])
        messages.append({"role": "user", "content": message})

        try:
            response = await self.llm.chat(messages)

            # 保存消息到 Redis
            if session_id and self._session_manager:
                conv = ConversationMemory(self._redis_client, session_id)
                await conv.add_message("user", message)
                await conv.add_message("assistant", response)

            return response
        except Exception as e:
            logger.error("对话失败: %s", e)
            return f"抱歉，处理您的问题时出现错误: {e}"

    def _build_chat_system_prompt(
        self,
        student_profile: Optional[Dict[str, Any]],
        knowledge_context: str,
    ) -> str:
        parts = [
            "你是一位专业的教育AI助手，基于知识库内容为学生提供个性化辅导。",
            "请用中文回答，保持友好和专业。",
        ]

        if student_profile:
            style = student_profile.get("learning_style", "")
            weaknesses = student_profile.get("weaknesses", [])
            if style:
                style_map = {
                    "visual": "多使用图表、流程图、示意图来解释",
                    "auditory": "多用类比和故事来解释概念",
                    "reading": "提供结构化的文字说明",
                    "kinesthetic": "多举实际操作的例子",
                }
                if style in style_map:
                    parts.append(f"该学生是{style}型学习者，{style_map[style]}。")
            if weaknesses:
                parts.append(f"该学生在以下方面较薄弱，请多关注: {', '.join(weaknesses)}。")

        if knowledge_context:
            parts.append(f"\n以下是知识库中的相关内容，请基于这些内容回答:\n\n{knowledge_context}")
        else:
            parts.append("\n知识库中没有找到相关内容，请基于你的知识回答，并说明这不是来自课程资料。")

        return "\n".join(parts)

    # ==================== 专业 Agent 调用接口 ====================

    async def analyze_profile(
        self,
        user_id: str,
        chat_history: List[Dict[str, str]],
        study_records: List[Dict[str, Any]],
        current_profile: Optional[Dict[str, Any]] = None,
        course_id: Optional[int] = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        分析学生画像（带缓存）

        Args:
            user_id: 用户ID
            chat_history: 聊天记录
            study_records: 学习记录
            current_profile: 现有画像（增量更新）
            course_id: 课程ID
            force_refresh: 强制刷新缓存
        """
        # 初始化 Redis
        await self._ensure_redis()

        # 检查缓存
        if not force_refresh and self._profile_cache:
            cached = await self._profile_cache.get_profile(user_id, course_id)
            if cached:
                logger.debug("画像缓存命中: user=%s", user_id)
                return cached

        # 调用 Agent 分析
        profile = await self.profile_agent.analyze(chat_history, study_records, current_profile)

        # 缓存结果
        if self._profile_cache and profile:
            await self._profile_cache.set_profile(user_id, profile, course_id)

        return profile

    async def generate_learning_path(
        self,
        student_profile: Dict[str, Any],
        course_title: str,
        course_knowledge: List[Dict[str, Any]],
        goal: str = "掌握课程核心知识",
    ) -> Dict[str, Any]:
        """生成个性化学习路径"""
        return await self.planner_agent.generate_path(
            student_profile=student_profile,
            course_title=course_title,
            course_knowledge=course_knowledge,
            goal=goal,
        )

    async def generate_resource(
        self,
        resource_type: str,
        topic: str,
        knowledge_ids: Optional[List[int]] = None,
        difficulty: str = "medium",
        count: int = 5,
    ) -> Dict[str, Any]:
        """
        生成教学资源

        Args:
            resource_type: "question" | "mindmap" | "summary"
            topic: 主题
            knowledge_ids: 知识库 ID 列表
            difficulty: 难度（仅题目）
            count: 数量（仅题目）
        """
        if resource_type == "question":
            return await self.resource_agent.generate_questions(
                topic=topic,
                knowledge_ids=knowledge_ids,
                difficulty=difficulty,
                count=count,
            )
        elif resource_type == "mindmap":
            return await self.resource_agent.generate_mindmap(
                topic=topic,
                knowledge_ids=knowledge_ids,
            )
        elif resource_type == "summary":
            return await self.resource_agent.generate_summary(
                topic=topic,
                knowledge_ids=knowledge_ids,
            )
        else:
            return {"error": f"不支持的资源类型: {resource_type}"}

    async def evaluate_answer(
        self,
        question: str,
        student_answer: str,
        reference_answer: str = "",
        knowledge_context: str = "",
    ) -> Dict[str, Any]:
        """评估学生答案"""
        return await self.evaluator_agent.evaluate_answer(
            question=question,
            student_answer=student_answer,
            reference_answer=reference_answer,
            knowledge_context=knowledge_context,
        )

    # ==================== 状态查询 ====================

    def get_status(self) -> Dict[str, Any]:
        return {
            "agents": [
                self.profile_agent.name,
                self.planner_agent.name,
                self.resource_agent.name,
                self.evaluator_agent.name,
            ],
            "tools": self.tools.list_tools(),
            "rag": self.rag.stats(),
            "llm": type(self.llm).__name__ if self.llm else "None",
            "memory": {
                "redis_connected": self._redis_client is not None,
                "session_manager": self._session_manager is not None,
                "profile_cache": self._profile_cache is not None,
                "rag_cache": self._rag_cache is not None,
            },
        }

    # ==================== 会话管理 ====================

    async def create_session(
        self,
        user_id: str,
        course_id: Optional[int] = None,
    ) -> str:
        """创建新会话"""
        await self._ensure_redis()
        return await self._session_manager.create_session(user_id, course_id)

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        await self._ensure_redis()
        return await self._session_manager.get_session(session_id)

    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        await self._ensure_redis()
        return await self._session_manager.delete_session(session_id)

    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50,
    ) -> List[Dict[str, str]]:
        """获取对话历史"""
        await self._ensure_redis()
        conv = ConversationMemory(self._redis_client, session_id)
        return await conv.get_history(limit=limit)

    async def list_user_sessions(
        self,
        user_id: str,
        limit: int = 20,
    ) -> list[Dict[str, Any]]:
        """列出用户的会话"""
        await self._ensure_redis()
        return await self._session_manager.list_user_sessions(user_id, limit)
