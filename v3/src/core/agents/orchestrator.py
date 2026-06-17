"""Orchestrator - 多 Agent 协作编排器，系统总入口"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, AsyncIterator

from ..memory.redis_client import get_redis, RedisClient
from ..memory.session_manager import SessionManager
from ..memory.conversation_memory import ConversationMemory
from ..memory.profile_cache import ProfileCache, RAGCache
from ..memory.learning_progress import LearningProgress
from ..rag.rag_pipeline import RAGPipeline
from ..tools.base import ToolRegistry
from ..tools.retrieval import RetrievalTool
from datetime import datetime

from ..tools.web_search import WebSearchTool
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
        self._learning_progress: Optional[LearningProgress] = None

        # 注册工具
        self.tools = ToolRegistry()
        self.tools.register(RetrievalTool(rag_pipeline))
        self.tools.register(WebSearchTool())

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
            self._learning_progress = LearningProgress(self._redis_client)
            logger.info("Redis 记忆系统初始化完成")
        return self._redis_client

    @property
    def session_manager(self) -> SessionManager:
        return self._session_manager

    @property
    def learning_progress(self) -> LearningProgress:
        return self._learning_progress

    @property
    def profile_cache(self) -> ProfileCache:
        return self._profile_cache

    # ==================== 核心对话入口 ====================

    async def _prepare_chat_messages(
        self,
        message: str,
        context: Dict[str, Any],
        session_id: Optional[str],
    ) -> list[dict]:
        """
        准备对话消息列表（RAG 检索 + 历史加载 + prompt 构造）。

        chat() 和 stream_chat() 共享此逻辑。
        """
        knowledge_ids = context.get("knowledge_ids")
        student_profile = context.get("student_profile")

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
                    query=message, top_k=5, knowledge_ids=knowledge_ids,
                )
                if retrieved:
                    knowledge_context = "\n\n---\n\n".join(r["content"] for r in retrieved)
                    if self._rag_cache:
                        await self._rag_cache.set_results(message, retrieved, knowledge_ids)
            except Exception as e:
                logger.warning("RAG 检索失败，降级为纯 LLM 对话: %s", e)

        # 构造个性化 prompt
        schedule = context.get("schedule")
        system_prompt = self._build_chat_system_prompt(student_profile, knowledge_context, schedule)
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history[-10:])
        messages.append({"role": "user", "content": message})
        return messages

    async def _save_chat_message(
        self, session_id: Optional[str], message: str, response: str,
    ) -> None:
        """保存对话消息到 Redis。"""
        if session_id and self._session_manager and response:
            try:
                conv = ConversationMemory(self._redis_client, session_id)
                await conv.add_message("user", message)
                await conv.add_message("assistant", response)
            except Exception as e:
                logger.warning("保存对话历史失败: %s", e)

    async def chat(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """
        RAG 增强对话 — 系统主入口

        Args:
            message: 用户消息
            context: {"knowledge_ids": [1,2], "student_profile": {...}}
            session_id: 会话ID（用于记忆对话历史）
        """
        context = context or {}
        messages = await self._prepare_chat_messages(message, context, session_id)

        try:
            response = await self.llm.chat(messages)
            await self._save_chat_message(session_id, message, response)
            return response
        except Exception as e:
            logger.error("对话失败: %s", e)
            return f"抱歉，处理您的问题时出现错误: {e}"

    async def stream_chat(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """流式 RAG 增强对话 — 逐块 yield"""
        context = context or {}
        messages = await self._prepare_chat_messages(message, context, session_id)

        full_response = []
        try:
            async for chunk in self.llm.stream(messages):
                full_response.append(chunk)
                yield chunk
        except Exception as e:
            logger.error("流式对话失败: %s", e)
            yield f"\n\n抱歉，处理时出现错误: {e}"
        finally:
            await self._save_chat_message(session_id, message, "".join(full_response))

    def _build_chat_system_prompt(
        self,
        student_profile: Optional[Dict[str, Any]],
        knowledge_context: str,
        schedule: Optional[Dict[str, Any]] = None,
    ) -> str:
        now = datetime.now()
        weekday_names = ["??", "??", "??", "??", "??", "??", "??"]
        today_str = f"{now.year}?{now.month}?{now.day}? {weekday_names[now.weekday()]}"

        parts = [
            f"???{today_str}?",
            "?????????AI????????????????????????????",
            "",
            "??????? ? ???????",
            "- ????????????????????????????1-2?????????????",
            "- ??????????????????????????????????????????????????????",
            "- ???????????????????????????",
            "- ???????????????????????????",
        ]

        if student_profile:
            parts.append("")
            parts.append("????? ? ????????????????????????????????")
            # ??????
            style = student_profile.get("learning_style", "")
            if style:
                style_map = {
                    "VISUAL": "???",
                    "AUDITORY": "???",
                    "READING": "???",
                    "KINESTHETIC": "???",
                }
                if style in style_map:
                    parts.append(f"- ?????{style_map[style]}")

            # ???
            strengths = student_profile.get("strengths", "")
            weaknesses = student_profile.get("weaknesses", "")
            if strengths:
                parts.append(f"- ???{strengths}")
            if weaknesses:
                parts.append(f"- ???{weaknesses}")

            interests = student_profile.get("interests", "")
            if interests:
                parts.append(f"- ???{interests}")

            # ???????
            q = student_profile.get("questionnaire")
            if q:
                major = q.get("major_direction", "")
                if major:
                    parts.append(f"- ?????{major}")

                education = q.get("education_level", "")
                if education:
                    edu_map = {
                        "HIGH_SCHOOL": "??", "ASSOCIATE": "??", "BACHELOR": "??",
                        "MASTER": "??", "PHD": "??", "OTHER": "??"
                    }
                    parts.append(f"- ???{edu_map.get(education, education)}")

                goals = q.get("learning_goals", [])
                if goals:
                    goal_map = {
                        "EXAM": "????", "INTEREST": "????", "EMPLOYMENT": "????",
                        "PROMOTION": "????", "SELF_IMPROVEMENT": "????", "OTHER": "??"
                    }
                    goals_cn = [goal_map.get(g, g) for g in goals]
                    parts.append(f"- ?????{', '.join(goals_cn)}")

                motivation = q.get("motivation_level", "")
                if motivation:
                    mot_map = {"STRONG": "??", "MODERATE": "??", "WEAK": "??"}
                    parts.append(f"- ???{mot_map.get(motivation, motivation)}")

                subj_level = q.get("subject_level", "")
                if subj_level:
                    lvl_map = {"ZERO_BASIC": "???", "BEGINNER": "??", "INTERMEDIATE": "??", "ADVANCED": "??"}
                    parts.append(f"- ?????{lvl_map.get(subj_level, subj_level)}")

                self_strengths = q.get("self_strengths", [])
                if self_strengths:
                    parts.append(f"- ?????{', '.join(self_strengths)}")

                self_weaknesses = q.get("self_weaknesses", [])
                if self_weaknesses:
                    parts.append(f"- ?????{', '.join(self_weaknesses)}")

                learning_methods = q.get("learning_methods", [])
                if learning_methods:
                    method_map = {
                        "VIDEO": "???", "READING": "????", "HANDS_ON": "????",
                        "DISCUSSION": "????", "LECTURE": "???", "QUIZ": "????"
                    }
                    methods_cn = [method_map.get(m, m) for m in learning_methods]
                    parts.append(f"- ???????{', '.join(methods_cn)}")

                session_dur = q.get("session_duration", "")
                if session_dur:
                    dur_map = {
                        "LESS_30MIN": "??30??", "30_60MIN": "30-60??", "1_2HOURS": "1-2??",
                        "2_4HOURS": "2-4??", "MORE_4HOURS": "4????"
                    }
                    parts.append(f"- ???????{dur_map.get(session_dur, session_dur)}")

                focus = q.get("focus_level", "")
                if focus:
                    f_map = {"VERY_HIGH": "????", "HIGH": "????", "MODERATE": "??", "LOW": "????", "VERY_LOW": "????"}
                    parts.append(f"- ?????{f_map.get(focus, focus)}")

                plan = q.get("planning_habit", "")
                if plan:
                    p_map = {"ALWAYS": "????", "OFTEN": "????", "SOMETIMES": "????", "RARELY": "????", "NEVER": "????"}
                    parts.append(f"- ??????{p_map.get(plan, plan)}")

                confidence = q.get("confidence_level", "")
                if confidence:
                    c_map = {"VERY_HIGH": "?????", "HIGH": "?????", "MODERATE": "??", "LOW": "????", "VERY_LOW": "??????"}
                    parts.append(f"- ????{c_map.get(confidence, confidence)}")

                barriers = q.get("main_barriers", [])
                if barriers:
                    b_map = {
                        "LAZINESS": "????", "DISTRACTION": "????", "NO_METHOD": "????",
                        "NO_CONFIDENCE": "????", "NO_TIME": "????", "NO_SUPPORT": "????",
                        "BORING": "????", "ANXIETY": "????"
                    }
                    b_cn = [b_map.get(b, b) for b in barriers]
                    parts.append(f"- ???????{', '.join(b_cn)}")

                mentor = q.get("has_mentor", "")
                if mentor:
                    m_map = {"YES": "???/??", "NO": "???/??", "WANT": "?????/??"}
                    parts.append(f"- ?????{m_map.get(mentor, mentor)}")

        if schedule:
            parts.append("")
            parts.append("????? ? ?????????????????????????????")
            if isinstance(schedule, dict):
                for day, courses in schedule.items():
                    if isinstance(courses, list):
                        course_str = "?".join(str(c) for c in courses)
                        parts.append(f"- {day}?{course_str}")
                    else:
                        parts.append(f"- {day}?{courses}")

        if knowledge_context:
            parts.append(f"\n??????????????????:\n\n{knowledge_context}")
        else:
            parts.append("\n???????????????????????????")

        return "\n".join(parts)


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

    # ==================== 学习进度管理 ====================

    async def get_course_progress(
        self,
        user_id: str,
        course_id: int,
    ) -> Dict[str, Any]:
        """获取用户在某课程的学习进度"""
        await self._ensure_redis()
        return await self._learning_progress.get_course_progress(user_id, course_id)

    async def complete_learning_step(
        self,
        user_id: str,
        course_id: int,
        step_id: int,
        duration_minutes: int = 0,
    ) -> Dict[str, Any]:
        """完成一个学习步骤"""
        await self._ensure_redis()

        # 更新步骤进度
        progress = await self._learning_progress.complete_step(
            user_id, course_id, step_id, duration_minutes,
        )

        # 更新学习时长统计
        await self._learning_progress.add_study_time(user_id, duration_minutes)

        # 记录学习历史
        await self._learning_progress.add_history(user_id, {
            "type": "step_completed",
            "course_id": course_id,
            "step_id": step_id,
            "duration_minutes": duration_minutes,
        })

        return progress

    async def get_knowledge_mastery(
        self,
        user_id: str,
        knowledge_ids: Optional[List[int]] = None,
    ) -> Dict[str, float]:
        """获取知识点掌握度"""
        await self._ensure_redis()
        return await self._learning_progress.get_mastery(user_id, knowledge_ids)

    async def update_knowledge_mastery(
        self,
        user_id: str,
        knowledge_id: int,
        score_delta: float,
    ) -> float:
        """更新知识点掌握度"""
        await self._ensure_redis()

        new_score = await self._learning_progress.update_mastery(
            user_id, knowledge_id, score_delta,
        )

        # 记录历史
        await self._learning_progress.add_history(user_id, {
            "type": "mastery_updated",
            "knowledge_id": knowledge_id,
            "score_delta": score_delta,
            "new_score": new_score,
        })

        return new_score

    async def get_learning_stats(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """获取学习统计"""
        await self._ensure_redis()
        return await self._learning_progress.get_stats(user_id)

    async def get_learning_summary(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """获取学习摘要（包含统计、薄弱点、建议）"""
        await self._ensure_redis()
        return await self._learning_progress.get_user_summary(user_id)

    async def get_learning_history(
        self,
        user_id: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """获取学习历史记录"""
        await self._ensure_redis()
        return await self._learning_progress.get_history(user_id, limit)

    async def record_answer_result(
        self,
        user_id: str,
        question_id: str,
        is_correct: bool,
        knowledge_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """记录答题结果"""
        await self._ensure_redis()

        # 更新答题统计
        await self._learning_progress.add_question_result(user_id, is_correct)

        # 如果答错，降低知识点掌握度；答对，提高掌握度
        if knowledge_id is not None:
            delta = 5.0 if is_correct else -3.0
            await self._learning_progress.update_mastery(user_id, knowledge_id, delta)

        # 记录历史
        await self._learning_progress.add_history(user_id, {
            "type": "question_answered",
            "question_id": question_id,
            "is_correct": is_correct,
            "knowledge_id": knowledge_id,
        })

        return {"recorded": True, "is_correct": is_correct}
