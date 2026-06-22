"""Orchestrator - 多 Agent 协作编排器，系统总入口"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
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
from .event_bus import AgentEventBus

logger = logging.getLogger(__name__)

RESOURCE_TYPE_MAP = {
    "question": "generate_questions",
    "mindmap": "generate_mindmap",
    "summary": "generate_summary",
}


@dataclass
class WorkflowResult:
    """多 Agent 工作流执行结果"""
    workflow_name: str
    success: bool
    steps: List[Dict[str, Any]] = field(default_factory=list)
    retries: int = 0


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

        # 事件总线
        self.event_bus = AgentEventBus()
        self._quality_stats = {"total": 0, "passed": 0}
        self._register_event_handlers()

        logger.info("Orchestrator 初始化完成: 4 agents, %d tools", len(self.tools.list_tools()))

    def _register_event_handlers(self) -> None:
        """注册事件处理器"""
        self.event_bus.on("quality.checked", self._on_quality_checked)
        self.event_bus.on("mistake.recorded", self._on_mistake_recorded)
        self.event_bus.on("practice.generated", self._on_practice_generated)

    async def _on_quality_checked(self, data: Dict[str, Any]) -> None:
        """质检完成事件处理 - 统计通过率"""
        self._quality_stats["total"] += 1
        if data.get("score", 0) >= 70:
            self._quality_stats["passed"] += 1
        logger.debug("质检统计: total=%d, passed=%d", self._quality_stats["total"], self._quality_stats["passed"])

    async def _on_mistake_recorded(self, data: Dict[str, Any]) -> None:
        """错题记录事件处理 - 记录日志"""
        logger.info("错题已记录: user=%s, question=%s", data.get("user_id"), str(data.get("question", ""))[:50])

    async def _on_practice_generated(self, data: Dict[str, Any]) -> None:
        """练习生成事件处理 - 记录日志"""
        logger.info("练习已生成: user=%s, count=%s", data.get("user_id"), data.get("question_count"))

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

    async def stream_answer_with_quality_check(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        quality_threshold: float = 70.0,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        流式深度答疑

        采用 Stream-then-verify 策略：
        1. 流式返回 LLM 回答（用户立即看到）
        2. 后台异步运行 EvaluatorAgent 质检
        3. 质检完成后发送 quality_check 事件
        """
        await self._ensure_redis()
        context = context or {}
        knowledge_ids = context.get("knowledge_ids")
        student_profile = context.get("student_profile")
        user_id = context.get("user_id", "")
        course_id = context.get("course_id")

        # Step 1: RAG 检索
        knowledge_context = ""
        try:
            retrieved = await self.rag.retrieve(
                query=question, top_k=5, knowledge_ids=knowledge_ids,
            )
            if retrieved:
                knowledge_context = "\n\n---\n\n".join(r["content"] for r in retrieved)
        except Exception as e:
            logger.warning("RAG 检索失败: %s", e)

        # Step 2: 流式生成回答
        system_prompt = self._build_chat_system_prompt(student_profile, knowledge_context)
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": question}]

        full_answer = []
        try:
            async for chunk in self.llm.stream(messages):
                full_answer.append(chunk)
                yield {"type": "text", "content": chunk}
        except Exception as e:
            logger.error("流式生成失败: %s", e)
            yield {"type": "text", "content": f"\n\n抱歉，处理时出现错误: {e}"}
            yield {"type": "done"}
            return

        complete_answer = "".join(full_answer)

        # Step 3: 异步质检
        try:
            quality = await self.evaluator_agent.execute(
                "evaluate_answer",
                question=question,
                student_answer=complete_answer,
                knowledge_context=knowledge_context,
            )
            score = quality.get("score", 0)

            yield {"type": "quality_check", "quality": quality}

            # 触发事件
            await self.event_bus.emit("quality.checked", {
                "question": question, "score": score, "is_correct": quality.get("is_correct"),
            })

            # 质检失败且回答错误时，自动记录错题
            if score < quality_threshold and quality.get("is_correct") is False and user_id:
                try:
                    await self._ensure_mistake_book()
                    await self._mistake_book.add_mistake(
                        user_id=user_id,
                        question=question,
                        student_answer=complete_answer,
                        reference_answer="",
                        error_category="concept_unclear",
                        course_id=course_id,
                    )
                    await self.event_bus.emit("mistake.recorded", {
                        "user_id": user_id, "question": question,
                    })
                except Exception as e:
                    logger.warning("自动记录错题失败: %s", e)

        except Exception as e:
            logger.warning("质检失败: %s", e)
            yield {"type": "quality_check", "quality": {"score": 80, "is_correct": True, "error": str(e)}}

        # 保存对话历史
        await self._save_chat_message(session_id, question, complete_answer)
        yield {"type": "done"}

    def _build_chat_system_prompt(
        self,
        student_profile: Optional[Dict[str, Any]],
        knowledge_context: str,
        schedule: Optional[Dict[str, Any]] = None,
    ) -> str:
        now = datetime.now()
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        today_str = f"{now.year}年{now.month}月{now.day}日 {weekday_names[now.weekday()]}"

        parts = [
            f"今天是{today_str}。",
            "你是我们的AI学习助手，请根据学生的情况提供个性化、友好的学习辅导。",
            "",
            "回答要求：",
            "- 回答要简洁清晰，控制在1-2段以内",
            "- 如果学生有具体的学习风格或薄弱点，请针对性调整回答方式",
            "- 优先基于提供的知识库内容回答",
            "- 如涉及课程安排，请结合课表信息给出建议",
        ]

        if student_profile:
            parts.append("")
            parts.append("当前学生画像信息（请据此调整教学策略）：")
            # 学习风格
            style = student_profile.get("learning_style", "")
            if style:
                style_map = {
                    "VISUAL": "视觉型",
                    "AUDITORY": "听觉型",
                    "READING": "阅读型",
                    "KINESTHETIC": "动手型",
                }
                if style in style_map:
                    parts.append(f"- 学习风格：{style_map[style]}")

            # 优势与劣势
            strengths = student_profile.get("strengths", "")
            weaknesses = student_profile.get("weaknesses", "")
            if strengths:
                parts.append(f"- 优势领域：{strengths}")
            if weaknesses:
                parts.append(f"- 薄弱领域：{weaknesses}")

            interests = student_profile.get("interests", "")
            if interests:
                parts.append(f"- 兴趣爱好：{interests}")

            # 问卷信息
            q = student_profile.get("questionnaire")
            if q:
                major = q.get("major_direction", "")
                if major:
                    parts.append(f"- 专业方向：{major}")

                education = q.get("education_level", "")
                if education:
                    edu_map = {
                        "HIGH_SCHOOL": "高中", "ASSOCIATE": "大专", "BACHELOR": "本科",
                        "MASTER": "硕士", "PHD": "博士", "OTHER": "其他"
                    }
                    parts.append(f"- 学历水平：{edu_map.get(education, education)}")

                goals = q.get("learning_goals", [])
                if goals:
                    goal_map = {
                        "EXAM": "应试备考", "INTEREST": "兴趣学习", "EMPLOYMENT": "求职就业",
                        "PROMOTION": "职场晋升", "SELF_IMPROVEMENT": "自我提升", "OTHER": "其他"
                    }
                    goals_cn = [goal_map.get(g, g) for g in goals]
                    parts.append(f"- 学习目标：{', '.join(goals_cn)}")

                motivation = q.get("motivation_level", "")
                if motivation:
                    mot_map = {"STRONG": "强", "MODERATE": "中等", "WEAK": "弱"}
                    parts.append(f"- 学习动机：{mot_map.get(motivation, motivation)}")

                subj_level = q.get("subject_level", "")
                if subj_level:
                    lvl_map = {"ZERO_BASIC": "零基础", "BEGINNER": "初级", "INTERMEDIATE": "中级", "ADVANCED": "高级"}
                    parts.append(f"- 学科水平：{lvl_map.get(subj_level, subj_level)}")

                self_strengths = q.get("self_strengths", [])
                if self_strengths:
                    parts.append(f"- 自我优势：{', '.join(self_strengths)}")

                self_weaknesses = q.get("self_weaknesses", [])
                if self_weaknesses:
                    parts.append(f"- 自我不足：{', '.join(self_weaknesses)}")

                learning_methods = q.get("learning_methods", [])
                if learning_methods:
                    method_map = {
                        "VIDEO": "视频学习", "READING": "阅读教材", "HANDS_ON": "动手实践",
                        "DISCUSSION": "讨论交流", "LECTURE": "听讲座", "QUIZ": "刷题练习"
                    }
                    methods_cn = [method_map.get(m, m) for m in learning_methods]
                    parts.append(f"- 偏好学习方式：{', '.join(methods_cn)}")

                session_dur = q.get("session_duration", "")
                if session_dur:
                    dur_map = {
                        "LESS_30MIN": "少于30分钟", "30_60MIN": "30-60分钟", "1_2HOURS": "1-2小时",
                        "2_4HOURS": "2-4小时", "MORE_4HOURS": "4小时以上"
                    }
                    parts.append(f"- 单次学习时长：{dur_map.get(session_dur, session_dur)}")

                focus = q.get("focus_level", "")
                if focus:
                    f_map = {"VERY_HIGH": "非常高", "HIGH": "较高", "MODERATE": "中等", "LOW": "较低", "VERY_LOW": "非常低"}
                    parts.append(f"- 专注力水平：{f_map.get(focus, focus)}")

        if knowledge_context:
            parts.append("")
            parts.append("相关知识库内容（优先基于此回答）：\n" + str(knowledge_context))

        if schedule:
            parts.append("")
            parts.append("当前课表信息：")
            parts.append(str(schedule))

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


    # ==================== 错题本 ====================

    async def _ensure_mistake_book(self):
        """懒加载错题本"""
        if not hasattr(self, "_mistake_book"):
            from ..memory.mistake_book import MistakeBook
            await self._ensure_redis()
            self._mistake_book = MistakeBook(self._redis_client)
        return self._mistake_book

    async def add_mistake(self, user_id: str, question: str, student_answer: str, correct_answer: str = "", error_category: str = "concept_unclear", course_id: Optional[int] = None, knowledge_id: Optional[int] = None, knowledge_name: str = "") -> Dict[str, Any]:
        """添加错题"""
        mb = await self._ensure_mistake_book()
        return await mb.add_mistake(user_id=user_id, question=question, student_answer=student_answer, reference_answer=correct_answer, error_category=error_category, course_id=course_id, knowledge_id=knowledge_id, knowledge_name=knowledge_name)

    async def list_mistakes(self, user_id: str, course_id: Optional[int] = None, error_category: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """获取错题列表"""
        mb = await self._ensure_mistake_book()
        return await mb.list_mistakes(user_id=user_id, course_id=course_id, error_category=error_category, limit=limit, offset=offset)

    async def record_review(self, mistake_id: str, recalled: bool) -> Dict[str, Any]:
        """记录复习结果"""
        mb = await self._ensure_mistake_book()
        return await mb.record_review(mistake_id=mistake_id, recalled=recalled)

    async def get_mistake_stats(self, user_id: str) -> Dict[str, Any]:
        """获取错题统计"""
        mb = await self._ensure_mistake_book()
        return await mb.get_stats(user_id=user_id)

    async def get_due_reviews(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取到期需复习的错题"""
        mb = await self._ensure_mistake_book()
        return await mb.get_due_reviews(user_id=user_id, limit=limit)

    async def generate_daily_review_notifications(self, user_id: str) -> List[Dict[str, Any]]:
        """生成每日复习提醒"""
        mb = await self._ensure_mistake_book()
        return await mb.generate_daily_review_notifications(user_id=user_id)

    async def get_pending_notifications(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取待处理通知"""
        mb = await self._ensure_mistake_book()
        return await mb.get_pending_notifications(user_id=user_id, limit=limit)

    async def diagnose_mistake(self, user_id: str, question: str, student_answer: str, correct_answer: str = "", course_id: Optional[int] = None) -> Dict[str, Any]:
        """LLM智能诊断 — 从对话中提取题目/答案/正确答案，然后分析错误原因"""
        import json, re
        mb = await self._ensure_mistake_book()

        # Step 1: 使用LLM从对话中提取结构化信息
        extract_prompt = f"""你是一个错题本助手。请从一段师生对话中提取错题信息。

=== 学生说的话 ===
{question}

=== AI老师纠正的回复（包含正确答案） ===
{correct_answer}

请仔细阅读以上对话，完成以下任务并输出纯JSON（不要任何其他文字）：

{{
    "extracted_question": "学生在回答什么问题？用最简短的一句话描述，如：1+1=?、地球的形状？、水的沸点？",
    "extracted_student_answer": "学生给出的错误答案是什么？只写答案本身",
    "extracted_correct_answer": "从AI纠正中提取正确答案。只写答案本身（数字、词语、短句），如：2、球体、100℃",
    "error_category": "concept_unclear / careless / wrong_approach / incomplete",
    "error_pattern": "一句话描述具体错误",
    "error_root_cause": "错误原因",
    "suggestion": "学习建议",
    "knowledge_name": "知识点名称"
}}

提取示例：
学生说：1加1等于3
老师纠正：1+1=2，不是3哦
→ extracted_question: 1+1=?
→ extracted_student_answer: 3
→ extracted_correct_answer: 2

学生说：地球是平的
老师纠正：地球是球体，不是平的
→ extracted_question: 地球是什么形状？
→ extracted_student_answer: 平的
→ extracted_correct_answer: 球体

关键：extracted_correct_answer 必须是裸答案，不要解释文字！只输出JSON！"""

        try:
            response_text = await self.llm.chat([{"role": "user", "content": extract_prompt}])
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                diagnosis = json.loads(json_match.group())
            else:
                diagnosis = {
                    "extracted_question": question[:100],
                    "extracted_student_answer": student_answer,
                    "extracted_correct_answer": correct_answer[:200] if correct_answer else "",
                    "error_category": "concept_unclear",
                    "error_pattern": "LLM解析失败",
                    "error_root_cause": "LLM返回格式异常",
                    "suggestion": "",
                    "knowledge_name": ""
                }
        except Exception as e:
            diagnosis = {
                "extracted_question": question[:100],
                "extracted_student_answer": student_answer,
                "extracted_correct_answer": correct_answer[:200] if correct_answer else "",
                "error_category": "concept_unclear",
                "error_pattern": f"LLM调用异常: {str(e)[:50]}",
                "error_root_cause": "LLM调用异常",
                "suggestion": "",
                "knowledge_name": ""
            }

        # Step 2: 使用提取后的结构化数据保存到错题本
        extracted_q = diagnosis.get("extracted_question") or question[:100]
        extracted_a = diagnosis.get("extracted_student_answer") or student_answer
        extracted_correct = diagnosis.get("extracted_correct_answer") or correct_answer

        mistake = await mb.add_mistake(
            user_id=user_id,
            question=extracted_q,
            student_answer=extracted_a,
            reference_answer=extracted_correct,
            error_category=diagnosis.get("error_category", "concept_unclear"),
            error_pattern=diagnosis.get("error_pattern", ""),
            error_root_cause=diagnosis.get("error_root_cause", ""),
            knowledge_name=diagnosis.get("knowledge_name", ""),
            course_id=course_id,
            diagnosis=diagnosis,
        )

        return {"mistake": mistake, "diagnosis": diagnosis}

    async def delete_mistake(self, mistake_id: str) -> bool:
        """删除错题"""
        mb = await self._ensure_mistake_book()
        return await mb.delete_mistake(mistake_id)

    async def clear_mistakes(self, user_id: str) -> int:
        """清空用户错题"""
        mb = await self._ensure_mistake_book()
        return await mb.clear_all_mistakes(user_id)

    async def generate_practice(self, user_id: str, question: str, student_answer: str, correct_answer: str = "", course_id: Optional[int] = None) -> Dict[str, Any]:
        """生成专项练习 — 基于同类错误聚合"""
        mb = await self._ensure_mistake_book()

        # 获取用户错误模式
        patterns = await mb.get_error_patterns(user_id)
        weak_points = patterns.get("weak_points", [])
        primary_error = patterns.get("primary_error_type", "concept_unclear")

        # 获取同类错误
        mistakes = await mb.list_mistakes(user_id=user_id, error_category=primary_error, limit=5)

        # 使用LLM生成专项练习
        similar_questions = "\n".join([f"- {m.get('question', '')} (错误原因: {m.get('error_root_cause', '未知')})" for m in mistakes[:3]])

        prompt = f"""你是一位教学专家。请根据学生的错误模式生成针对性练习题。

学生错题：{question}
错误类型：{primary_error}
薄弱知识点：{', '.join(weak_points) if weak_points else '待分析'}

历史同类错误：
{similar_questions if similar_questions else '暂无'}

请生成3道与错误类型高度相关的练习题，输出JSON格式：
{{
    "practice_title": "练习标题",
    "target_skill": "目标技能",
    "questions": [
        {{"question": "题目", "answer": "参考答案", "hint": "解题提示"}}
    ]
}}"""

        try:
            response_text = await self.llm.chat([{"role": "user", "content": prompt}])
            import json, re
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                practice = json.loads(json_match.group())
            else:
                practice = {"practice_title": "专项练习", "target_skill": "待加强", "questions": []}
        except Exception:
            practice = {"practice_title": "专项练习", "target_skill": "待加强", "questions": []}

        return {
            "practice": practice,
            "error_context": {
                "primary_error": primary_error,
                "weak_points": weak_points,
                "similar_mistakes_count": len(mistakes),
            }
        }

    # ==================== 多 Agent 协作接口 ====================

    async def _call_agent_safe(
        self,
        agent_name: str,
        agent,
        task_type: str,
        fallback: Dict[str, Any],
        timeout: float = 30.0,
        **kwargs,
    ) -> Dict[str, Any]:
        """安全调用 Agent，带超时和降级"""
        try:
            result = await asyncio.wait_for(
                agent.execute(task_type, **kwargs),
                timeout=timeout,
            )
            return result
        except asyncio.TimeoutError:
            logger.error("[%s] Agent 超时 (%.1fs)", agent_name, timeout)
            fallback["error"] = f"{agent_name} timeout"
            return fallback
        except Exception as e:
            logger.error("[%s] Agent 调用失败: %s", agent_name, e)
            fallback["error"] = str(e)
            return fallback

    async def analyze_profile(
        self,
        user_id: str,
        chat_history: List[Dict[str, str]],
        study_records: List[Dict[str, Any]],
        current_profile: Optional[Dict[str, Any]] = None,
        course_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """学生画像分析（委托给 ProfileAgent）"""
        await self._ensure_redis()

        # 检查缓存
        if self._profile_cache and course_id:
            cached = await self._profile_cache.get(user_id, course_id)
            if cached:
                logger.debug("画像缓存命中: user=%s, course=%s", user_id, course_id)
                return cached

        fallback = current_profile or {}
        result = await self._call_agent_safe(
            "profile_agent", self.profile_agent, "analyze",
            fallback=fallback,
            chat_history=chat_history,
            study_records=study_records,
            current_profile=current_profile or {},
        )

        # 缓存结果
        if self._profile_cache and course_id and "error" not in result:
            await self._profile_cache.set(user_id, course_id, result)

        return result

    async def generate_learning_path(
        self,
        student_profile: Dict[str, Any],
        course_title: str,
        course_knowledge: List[Dict[str, Any]],
        goal: str = "掌握课程核心知识",
    ) -> Dict[str, Any]:
        """生成学习路径（委托给 PlannerAgent）"""
        return await self._call_agent_safe(
            "planner_agent", self.planner_agent, "generate_path",
            fallback={"title": course_title, "steps": [], "error": "planner_failed"},
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
        """生成教学资源（委托给 ResourceAgent）"""
        task_type = RESOURCE_TYPE_MAP.get(resource_type)
        if not task_type:
            return {"error": f"不支持的资源类型: {resource_type}"}

        return await self._call_agent_safe(
            "resource_agent", self.resource_agent, task_type,
            fallback={"topic": topic, "questions": [], "error": "resource_failed"},
            topic=topic,
            knowledge_ids=knowledge_ids,
            difficulty=difficulty,
            count=count,
        )

    async def evaluate_answer(
        self,
        question: str,
        student_answer: str,
        reference_answer: str = "",
        knowledge_context: str = "",
    ) -> Dict[str, Any]:
        """评估学生答案（委托给 EvaluatorAgent）"""
        return await self._call_agent_safe(
            "evaluator_agent", self.evaluator_agent, "evaluate_answer",
            fallback={"score": 0, "is_correct": False, "error": "evaluator_failed"},
            question=question,
            student_answer=student_answer,
            reference_answer=reference_answer,
            knowledge_context=knowledge_context,
        )

    async def answer_with_quality_check(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        max_retries: int = 2,
        quality_threshold: float = 70.0,
    ) -> Dict[str, Any]:
        """
        智能答疑 + 质检工作流

        流程：
        1. RAG 检索知识
        2. LLM 生成回答
        3. EvaluatorAgent 评估质量
        4. 如果质量不达标 → 优化查询 → 重试
        """
        await self._ensure_redis()
        context = context or {}
        knowledge_ids = context.get("knowledge_ids")
        student_profile = context.get("student_profile")
        user_id = context.get("user_id", "")
        course_id = context.get("course_id")

        workflow = WorkflowResult(workflow_name="qa_with_quality_check", success=False)
        best_answer = ""
        best_quality: Dict[str, Any] = {}
        current_query = question

        for attempt in range(max_retries + 1):
            # Step 1: RAG 检索
            knowledge_context = ""
            try:
                retrieved = await self.rag.retrieve(
                    query=current_query, top_k=5, knowledge_ids=knowledge_ids,
                )
                if retrieved:
                    knowledge_context = "\n\n---\n\n".join(r["content"] for r in retrieved)
                workflow.steps.append({"step": "retrieve", "status": "ok", "attempt": attempt})
            except Exception as e:
                logger.warning("RAG 检索失败: %s", e)
                workflow.steps.append({"step": "retrieve", "status": "error", "error": str(e)})

            # Step 2: LLM 生成回答
            try:
                system_prompt = self._build_chat_system_prompt(student_profile, knowledge_context)
                messages = [{"role": "system", "content": system_prompt}]
                messages.append({"role": "user", "content": question})
                answer = await self.llm.chat(messages)
                workflow.steps.append({"step": "generate", "status": "ok", "attempt": attempt})

                # 触发事件
                await self.event_bus.emit("answer.generated", {
                    "question": question, "answer": answer, "attempt": attempt,
                })
            except Exception as e:
                logger.error("LLM 生成失败: %s", e)
                answer = f"抱歉，处理您的问题时出现错误: {e}"
                workflow.steps.append({"step": "generate", "status": "error", "error": str(e)})
                break

            # Step 3: EvaluatorAgent 质量检查
            try:
                quality = await self.evaluator_agent.execute(
                    "evaluate_answer",
                    question=question,
                    student_answer=answer,
                    knowledge_context=knowledge_context,
                )
                score = quality.get("score", 0)
                workflow.steps.append({"step": "evaluate", "status": "ok", "score": score, "attempt": attempt})

                # 触发事件
                await self.event_bus.emit("quality.checked", {
                    "question": question, "score": score, "is_correct": quality.get("is_correct"),
                })
            except Exception as e:
                logger.warning("质量检查失败，接受回答: %s", e)
                quality = {"score": 80, "is_correct": True, "evaluator_error": str(e)}
                score = 80
                workflow.steps.append({"step": "evaluate", "status": "fallback", "error": str(e)})

            best_answer = answer
            best_quality = quality

            # Step 4: 检查质量是否达标
            if score >= quality_threshold:
                workflow.success = True
                break

            # Step 5: 优化查询，准备重试
            if attempt < max_retries:
                errors = quality.get("errors", [])
                suggestions = quality.get("suggestions", [])
                refinement = " ".join(str(x) for x in errors + suggestions if x)
                if refinement:
                    current_query = f"{question} {refinement}"
                workflow.retries += 1

        # 质检发现问题时自动记录错题
        if not workflow.success and best_quality.get("is_correct") is False and user_id:
            try:
                await self._ensure_mistake_book()
                await self._mistake_book.add_mistake(
                    user_id=user_id,
                    question=question,
                    student_answer=best_answer,
                    reference_answer="",
                    error_category="concept_unclear",
                    course_id=course_id,
                )
                await self.event_bus.emit("mistake.recorded", {
                    "user_id": user_id, "question": question,
                })
            except Exception as e:
                logger.warning("自动记录错题失败: %s", e)

        # 保存对话历史
        await self._save_chat_message(session_id, question, best_answer)

        return {
            "answer": best_answer,
            "quality": best_quality,
            "workflow": {
                "name": workflow.workflow_name,
                "success": workflow.success,
                "steps": workflow.steps,
                "retries": workflow.retries,
            },
            "retries_used": workflow.retries,
        }

    async def diagnose_and_practice(
        self,
        user_id: str,
        question: str,
        student_answer: str,
        correct_answer: str = "",
        course_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        错题诊断 + 专项练习工作流

        流程：
        1. EvaluatorAgent 评估错误类型
        2. ResourceAgent 生成同类练习题
        3. 保存错题 + 返回诊断结果 + 练习题
        """
        await self._ensure_redis()
        workflow = WorkflowResult(workflow_name="diagnose_and_practice", success=False)

        # Step 1: EvaluatorAgent 评估错误
        evaluation = await self._call_agent_safe(
            "evaluator_agent", self.evaluator_agent, "evaluate_answer",
            fallback={"score": 0, "is_correct": False, "errors": ["评估失败"]},
            question=question,
            student_answer=student_answer,
            reference_answer=correct_answer,
        )

        error_category = "concept_unclear"
        if evaluation.get("is_correct"):
            error_category = "correct"
        elif "粗心" in str(evaluation.get("errors", [])):
            error_category = "careless"
        elif "方法" in str(evaluation.get("errors", [])):
            error_category = "wrong_approach"
        elif "不完整" in str(evaluation.get("errors", [])):
            error_category = "incomplete"

        workflow.steps.append({
            "step": "evaluate", "status": "ok",
            "error_category": error_category,
            "score": evaluation.get("score", 0),
        })

        # Step 2: ResourceAgent 生成同类练习题
        practice = await self._call_agent_safe(
            "resource_agent", self.resource_agent, "generate_questions",
            fallback={"questions": [], "topic": question[:50]},
            topic=question,
            difficulty="medium",
            count=3,
        )

        workflow.steps.append({
            "step": "generate_practice", "status": "ok",
            "question_count": len(practice.get("questions", [])),
        })

        # Step 3: 保存错题
        mistake = None
        if error_category != "correct":
            try:
                await self._ensure_mistake_book()
                mistake = await self._mistake_book.add_mistake(
                    user_id=user_id,
                    question=question,
                    student_answer=student_answer,
                    reference_answer=correct_answer,
                    error_category=error_category,
                    error_pattern=str(evaluation.get("errors", ["未知"])),
                    error_root_cause=str(evaluation.get("suggestions", ["未知"])),
                    course_id=course_id,
                    diagnosis=evaluation,
                )
                workflow.steps.append({"step": "save_mistake", "status": "ok"})

                await self.event_bus.emit("mistake.recorded", {
                    "user_id": user_id, "question": question, "error_category": error_category,
                })
            except Exception as e:
                logger.warning("保存错题失败: %s", e)
                workflow.steps.append({"step": "save_mistake", "status": "error", "error": str(e)})

        workflow.success = True

        # 触发事件
        await self.event_bus.emit("practice.generated", {
            "user_id": user_id, "question_count": len(practice.get("questions", [])),
        })

        return {
            "evaluation": evaluation,
            "error_category": error_category,
            "practice": practice,
            "mistake": mistake,
            "workflow": {
                "name": workflow.workflow_name,
                "success": workflow.success,
                "steps": workflow.steps,
            },
        }
