"""学习进度存储 - 追踪学生的学习进度和知识点掌握度"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .redis_client import RedisClient

logger = logging.getLogger(__name__)

# 进度数据过期时间：90天
PROGRESS_TTL = 90 * 24 * 3600
# 统计数据过期时间：365天
STATS_TTL = 365 * 24 * 3600


class LearningProgress:
    """
    学习进度管理

    Redis 数据结构：
    - progress:{user_id}:course:{course_id} (Hash) - 课程进度
    - mastery:{user_id} (Sorted Set) - 知识点掌握度，score 为掌握分数
    - stats:{user_id} (Hash) - 学习统计
    - history:{user_id} (List) - 学习记录历史
    """

    def __init__(self, redis: RedisClient):
        self.redis = redis

    # ==================== 课程进度 ====================

    def _course_progress_key(self, user_id: str, course_id: int) -> str:
        return f"progress:{user_id}:course:{course_id}"

    async def get_course_progress(
        self,
        user_id: str,
        course_id: int,
    ) -> Dict[str, Any]:
        """获取用户在某课程的学习进度"""
        key = self._course_progress_key(user_id, course_id)
        progress = await self.redis.get_json(key)

        if not progress:
            # 返回默认进度
            return {
                "user_id": user_id,
                "course_id": course_id,
                "status": "not_started",  # not_started / in_progress / completed
                "current_step": 0,
                "total_steps": 0,
                "completed_steps": [],
                "start_time": None,
                "last_study_time": None,
                "study_duration_minutes": 0,
                "completion_rate": 0.0,
            }

        return progress

    async def update_course_progress(
        self,
        user_id: str,
        course_id: int,
        updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        更新课程进度

        Args:
            user_id: 用户ID
            course_id: 课程ID
            updates: 要更新的字段

        Returns:
            更新后的进度
        """
        progress = await self.get_course_progress(user_id, course_id)
        progress.update(updates)

        # 自动更新状态
        if progress.get("completion_rate", 0) >= 1.0:
            progress["status"] = "completed"
        elif progress.get("current_step", 0) > 0:
            progress["status"] = "in_progress"

        # 更新时间
        progress["last_study_time"] = datetime.now().isoformat()

        key = self._course_progress_key(user_id, course_id)
        await self.redis.set_json(key, progress, ttl=PROGRESS_TTL)

        return progress

    async def complete_step(
        self,
        user_id: str,
        course_id: int,
        step_id: int,
        duration_minutes: int = 0,
    ) -> Dict[str, Any]:
        """
        完成一个学习步骤

        Args:
            user_id: 用户ID
            course_id: 课程ID
            step_id: 步骤ID
            duration_minutes: 学习时长（分钟）

        Returns:
            更新后的进度
        """
        progress = await self.get_course_progress(user_id, course_id)

        # 添加到已完成列表
        completed = progress.get("completed_steps", [])
        if step_id not in completed:
            completed.append(step_id)
            completed.sort()

        # 更新进度
        updates = {
            "completed_steps": completed,
            "current_step": max(progress.get("current_step", 0), step_id + 1),
            "study_duration_minutes": progress.get("study_duration_minutes", 0) + duration_minutes,
            "start_time": progress.get("start_time") or datetime.now().isoformat(),
        }

        # 计算完成率
        total = progress.get("total_steps", 0)
        if total > 0:
            updates["completion_rate"] = len(completed) / total

        return await self.update_course_progress(user_id, course_id, updates)

    async def set_course_steps(
        self,
        user_id: str,
        course_id: int,
        total_steps: int,
    ) -> Dict[str, Any]:
        """设置课程总步骤数"""
        return await self.update_course_progress(user_id, course_id, {
            "total_steps": total_steps,
        })

    # ==================== 知识点掌握度 ====================

    def _mastery_key(self, user_id: str) -> str:
        return f"mastery:{user_id}"

    async def get_mastery(
        self,
        user_id: str,
        knowledge_ids: Optional[List[int]] = None,
    ) -> Dict[str, float]:
        """
        获取知识点掌握度

        Args:
            user_id: 用户ID
            knowledge_ids: 指定知识点ID列表，None 则返回全部

        Returns:
            {knowledge_id: mastery_score} 掌握分数 0-100
        """
        key = self._mastery_key(user_id)

        if knowledge_ids:
            # 获取指定知识点
            scores = await self.redis.redis.zmscore(
                key,
                [str(kid) for kid in knowledge_ids],
            )
            return {
                kid: float(score) if score else 0.0
                for kid, score in zip(knowledge_ids, scores)
            }
        else:
            # 获取全部
            items = await self.redis.redis.zrangebyscore(
                key, 0, 100, withscores=True,
            )
            return {int(kid): score for kid, score in items}

    async def update_mastery(
        self,
        user_id: str,
        knowledge_id: int,
        score_delta: float,
        max_score: float = 100.0,
    ) -> float:
        """
        更新知识点掌握度

        Args:
            user_id: 用户ID
            knowledge_id: 知识点ID
            score_delta: 分数变化（正数增加，负数减少）
            max_score: 最大分数

        Returns:
            更新后的分数
        """
        key = self._mastery_key(user_id)

        # 使用 ZINCRBY 原子操作
        new_score = await self.redis.redis.zincrby(key, score_delta, str(knowledge_id))

        # 限制范围
        new_score = max(0, min(max_score, new_score))

        # 如果超出范围，修正
        if new_score != float(await self.redis.redis.zscore(key, str(knowledge_id))):
            await self.redis.redis.zadd(key, {str(knowledge_id): new_score})

        # 续期
        await self.redis.expire(key, PROGRESS_TTL)

        return new_score

    async def set_mastery(
        self,
        user_id: str,
        knowledge_id: int,
        score: float,
    ) -> float:
        """直接设置知识点掌握度"""
        key = self._mastery_key(user_id)
        score = max(0, min(100, score))
        await self.redis.redis.zadd(key, {str(knowledge_id): score})
        await self.redis.expire(key, PROGRESS_TTL)
        return score

    async def get_weak_knowledge(
        self,
        user_id: str,
        threshold: float = 60.0,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        获取薄弱知识点

        Args:
            user_id: 用户ID
            threshold: 掌握度阈值（低于此值为薄弱）
            limit: 返回数量

        Returns:
            [{"knowledge_id": 1, "mastery": 45.0}, ...]
        """
        key = self._mastery_key(user_id)
        items = await self.redis.redis.zrangebyscore(
            key, 0, threshold, withscores=True,
        )

        result = [
            {"knowledge_id": int(kid), "mastery": score}
            for kid, score in items[:limit]
        ]

        # 按掌握度升序
        result.sort(key=lambda x: x["mastery"])
        return result

    async def get_strong_knowledge(
        self,
        user_id: str,
        threshold: float = 80.0,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """获取优势知识点"""
        key = self._mastery_key(user_id)
        items = await self.redis.redis.zrangebyscore(
            key, threshold, 100, withscores=True,
        )

        result = [
            {"knowledge_id": int(kid), "mastery": score}
            for kid, score in items[:limit]
        ]

        # 按掌握度降序
        result.sort(key=lambda x: x["mastery"], reverse=True)
        return result

    # ==================== 学习统计 ====================

    def _stats_key(self, user_id: str) -> str:
        return f"stats:{user_id}"

    async def get_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户学习统计"""
        key = self._stats_key(user_id)
        stats = await self.redis.get_json(key)

        if not stats:
            return {
                "user_id": user_id,
                "total_study_minutes": 0,
                "total_courses": 0,
                "completed_courses": 0,
                "total_questions": 0,
                "correct_questions": 0,
                "accuracy_rate": 0.0,
                "study_days": 0,
                "current_streak": 0,
                "longest_streak": 0,
                "last_study_date": None,
            }

        return stats

    async def update_stats(
        self,
        user_id: str,
        updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        """更新学习统计"""
        stats = await self.get_stats(user_id)
        stats.update(updates)

        # 自动计算正确率
        total = stats.get("total_questions", 0)
        correct = stats.get("correct_questions", 0)
        if total > 0:
            stats["accuracy_rate"] = round(correct / total, 4)

        key = self._stats_key(user_id)
        await self.redis.set_json(key, stats, ttl=STATS_TTL)

        return stats

    async def add_study_time(
        self,
        user_id: str,
        minutes: int,
    ) -> Dict[str, Any]:
        """添加学习时长"""
        stats = await self.get_stats(user_id)

        # 更新学习时长
        stats["total_study_minutes"] = stats.get("total_study_minutes", 0) + minutes

        # 更新连续学习天数
        today = datetime.now().date().isoformat()
        last_date = stats.get("last_study_date")

        if last_date == today:
            # 今天已学习，不更新连续天数
            pass
        elif last_date == (datetime.now().date() - timedelta(days=1)).isoformat():
            # 昨天学习了，连续天数+1
            stats["current_streak"] = stats.get("current_streak", 0) + 1
        else:
            # 断了，重新开始
            stats["current_streak"] = 1

        stats["last_study_date"] = today
        stats["longest_streak"] = max(
            stats.get("longest_streak", 0),
            stats.get("current_streak", 0),
        )

        # 计算学习天数
        if stats.get("study_days") is None:
            stats["study_days"] = 1
        elif last_date != today:
            stats["study_days"] = stats.get("study_days", 0) + 1

        return await self.update_stats(user_id, stats)

    async def add_question_result(
        self,
        user_id: str,
        is_correct: bool,
    ) -> Dict[str, Any]:
        """添加答题结果"""
        stats = await self.get_stats(user_id)
        stats["total_questions"] = stats.get("total_questions", 0) + 1
        if is_correct:
            stats["correct_questions"] = stats.get("correct_questions", 0) + 1
        return await self.update_stats(user_id, stats)

    # ==================== 学习记录历史 ====================

    def _history_key(self, user_id: str) -> str:
        return f"history:{user_id}"

    async def add_history(
        self,
        user_id: str,
        record: Dict[str, Any],
        max_records: int = 100,
    ) -> int:
        """
        添加学习记录

        Args:
            user_id: 用户ID
            record: 记录内容
            max_records: 最大记录数

        Returns:
            当前记录总数
        """
        import json

        key = self._history_key(user_id)

        # 添加时间戳
        record["timestamp"] = datetime.now().isoformat()

        # 左推入（最新在前）
        data = json.dumps(record, ensure_ascii=False)
        await self.redis.redis.lpush(key, data)

        # 裁剪到最大数量
        await self.redis.redis.ltrim(key, 0, max_records - 1)

        # 续期
        await self.redis.expire(key, PROGRESS_TTL)

        return await self.redis.redis.llen(key)

    async def get_history(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """获取学习记录历史"""
        import json

        key = self._history_key(user_id)
        raw_list = await self.redis.redis.lrange(key, offset, offset + limit - 1)

        records = []
        for raw in raw_list:
            try:
                records.append(json.loads(raw))
            except json.JSONDecodeError:
                continue

        return records

    # ==================== 聚合查询 ====================

    async def get_user_summary(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """获取用户学习摘要（聚合多个数据源）"""
        stats = await self.get_stats(user_id)
        weak = await self.get_weak_knowledge(user_id, limit=5)
        strong = await self.get_strong_knowledge(user_id, limit=5)

        return {
            "stats": stats,
            "weak_knowledge": weak,
            "strong_knowledge": strong,
            "recommendation": self._generate_recommendation(stats, weak),
        }

    def _generate_recommendation(
        self,
        stats: Dict[str, Any],
        weak: List[Dict[str, Any]],
    ) -> str:
        """生成学习建议"""
        recommendations = []

        # 基于连续学习天数
        streak = stats.get("current_streak", 0)
        if streak == 0:
            recommendations.append("建议每天坚持学习，保持学习连续性")
        elif streak < 3:
            recommendations.append("继续保持，争取连续学习一周")
        else:
            recommendations.append(f"已连续学习{streak}天，保持良好习惯")

        # 基于薄弱知识点
        if weak:
            topics = [str(w["knowledge_id"]) for w in weak[:3]]
            recommendations.append(f"建议重点复习知识点: {', '.join(topics)}")

        # 基于正确率
        accuracy = stats.get("accuracy_rate", 0)
        if accuracy < 0.6:
            recommendations.append("正确率较低，建议多做基础练习")
        elif accuracy > 0.9:
            recommendations.append("正确率很高，可以尝试更高难度的题目")

        return "；".join(recommendations) if recommendations else "继续努力学习"