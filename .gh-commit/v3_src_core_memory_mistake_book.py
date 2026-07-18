"""??? + ????????????

Redis ????:
- mistakes:{user_id} (Sorted Set) ? ?????score=timestamp
- mistake:{mistake_id} (Hash) ? ????
- review_schedule:{user_id} (Sorted Set) ? ?????score=???????
- error_patterns:{user_id} (Hash) ? ??????
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .redis_client import RedisClient

logger = logging.getLogger(__name__)

# ?? TTL?365 ?
MISTAKE_TTL = 365 * 24 * 3600

# ???????????????
EBBINGHAUS_INTERVALS = [1, 2, 4, 7, 15, 30]


class MistakeBook:
    """?????"""

    def __init__(self, redis: RedisClient):
        self.redis = redis

    # ==================== Redis Key ?? ====================

    def _mistake_key(self, mistake_id: str) -> str:
        return f"mistake:{mistake_id}"

    def _mistake_index_key(self, user_id: str) -> str:
        return f"mistakes:{user_id}"

    def _review_schedule_key(self, user_id: str) -> str:
        return f"review_schedule:{user_id}"

    def _error_patterns_key(self, user_id: str) -> str:
        return f"error_patterns:{user_id}"

    def _notification_key(self, user_id: str) -> str:
        return f"notifications:{user_id}"

    # ==================== review ====================

    async def add_mistake(
        self,
        user_id: str,
        question: str,
        student_answer: str,
        reference_answer: str = "",
        error_category: str = "concept_unclear",
        error_pattern: str = "",
        error_root_cause: str = "",
        knowledge_id: Optional[int] = None,
        knowledge_name: str = "",
        course_id: Optional[int] = None,
        diagnosis: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """??????"""
        mistake_id = f"mistake_{uuid.uuid4().hex[:12]}"
        now = datetime.now()
        timestamp = now.timestamp()

        mistake = {
            "id": mistake_id,
            "user_id": user_id,
            "question": question,
            "student_answer": student_answer,
            "reference_answer": reference_answer,
            "error_category": error_category,
            "error_pattern": error_pattern,
            "error_root_cause": error_root_cause,
            "knowledge_id": knowledge_id,
            "knowledge_name": knowledge_name,
            "course_id": course_id,
            "diagnosis": diagnosis or {},
            "created_at": now.isoformat(),
            "review_count": 0,
            "next_review_at": None,
            "review_stage": 0,
            "mastered": False,
        }

        # ??????
        await self.redis.set_json(self._mistake_key(mistake_id), mistake, ttl=MISTAKE_TTL)

        # ??????
        await self.redis.redis.zadd(self._mistake_index_key(user_id), {mistake_id: timestamp})

        # ???1?????
        first_review = now + timedelta(days=EBBINGHAUS_INTERVALS[0])
        await self.redis.redis.zadd(
            self._review_schedule_key(user_id),
            {mistake_id: first_review.timestamp()},
        )

        # ????????
        await self._update_error_patterns(user_id, error_category, error_pattern, knowledge_name)

        logger.info(
            "?????: user=%s, mistake_id=%s, category=%s, pattern=%s",
            user_id, mistake_id, error_category, error_pattern,
        )

        return mistake

    # ==================== review ====================

    async def get_mistake(self, mistake_id: str) -> Optional[Dict[str, Any]]:
        """??????"""
        return await self.redis.get_json(self._mistake_key(mistake_id))

    
    async def delete_mistake(self, mistake_id: str) -> bool:
        """删除单条错题"""
        mistake = await self.get_mistake(mistake_id)
        if not mistake:
            return False
        user_id = mistake.get("user_id", "")
        # 从索引中移除
        if user_id:
            await self.redis.redis.zrem(self._mistake_index_key(user_id), mistake_id)
            await self.redis.redis.zrem(self._review_schedule_key(user_id), mistake_id)
        # 删除错题数据
        await self.redis.delete(self._mistake_key(mistake_id))
        return True

    async def clear_all_mistakes(self, user_id: str) -> int:
        """清空用户所有错题，返回删除数量"""
        mistake_ids = await self.redis.redis.zrange(self._mistake_index_key(user_id), 0, -1)
        count = 0
        for mid in mistake_ids:
            mid_str = mid.decode() if isinstance(mid, bytes) else mid
            await self.redis.delete(self._mistake_key(mid_str))
            count += 1
        await self.redis.redis.delete(self._mistake_index_key(user_id))
        await self.redis.redis.delete(self._review_schedule_key(user_id))
        await self.redis.redis.delete(self._error_patterns_key(user_id))
        return count

    async def list_mistakes(
        self,
        user_id: str,
        course_id: Optional[int] = None,
        knowledge_id: Optional[int] = None,
        error_category: Optional[str] = None,
        mastered: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """????????"""
        mistake_ids = await self.redis.redis.zrevrange(
            self._mistake_index_key(user_id), offset, offset + limit - 1,
        )

        if not mistake_ids:
            return []

        mistakes = []
        for mid in mistake_ids:
            m = await self.get_mistake(mid.decode() if isinstance(mid, bytes) else mid)
            if m is None:
                continue
            # ??
            if course_id is not None and m.get("course_id") != course_id:
                continue
            if knowledge_id is not None and m.get("knowledge_id") != knowledge_id:
                continue
            if error_category is not None and m.get("error_category") != error_category:
                continue
            if mastered is not None and m.get("mastered") != mastered:
                continue
            mistakes.append(m)

        return mistakes

    # ==================== review ====================

    async def record_review(
        self,
        mistake_id: str,
        recalled: bool,
    ) -> Optional[Dict[str, Any]]:
        """???????????????????"""
        mistake = await self.get_mistake(mistake_id)
        if not mistake:
            return None

        now = datetime.now()
        user_id = mistake["user_id"]

        if recalled:
            # ???? ? ???????
            mistake["review_stage"] = mistake.get("review_stage", 0) + 1
            stage = min(mistake["review_stage"], len(EBBINGHAUS_INTERVALS) - 1)
            next_days = EBBINGHAUS_INTERVALS[stage]
            mistake["review_count"] = mistake.get("review_count", 0) + 1

            # ???????????????
            if mistake["review_stage"] >= len(EBBINGHAUS_INTERVALS):
                mistake["mastered"] = True
                await self.redis.redis.zrem(
                    self._review_schedule_key(user_id), mistake_id,
                )
                logger.info("?????: %s", mistake_id)
            else:
                next_review = now + timedelta(days=next_days)
                mistake["next_review_at"] = next_review.isoformat()
                await self.redis.redis.zadd(
                    self._review_schedule_key(user_id),
                    {mistake_id: next_review.timestamp()},
                )
        else:
            # ???? ? ????1??
            mistake["review_stage"] = 0
            next_review = now + timedelta(days=EBBINGHAUS_INTERVALS[0])
            mistake["next_review_at"] = next_review.isoformat()
            mistake["review_count"] = mistake.get("review_count", 0) + 1
            await self.redis.redis.zadd(
                self._review_schedule_key(user_id),
                {mistake_id: next_review.timestamp()},
            )

        mistake["last_review_at"] = now.isoformat()
        await self.redis.set_json(self._mistake_key(mistake_id), mistake, ttl=MISTAKE_TTL)

        return mistake

    async def get_due_reviews(
        self,
        user_id: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """???????????"""
        now_ts = datetime.now().timestamp()
        due_ids = await self.redis.redis.zrangebyscore(
            self._review_schedule_key(user_id),
            0, now_ts, start=0, num=limit,
        )

        mistakes = []
        for mid in due_ids:
            mid_str = mid.decode() if isinstance(mid, bytes) else mid
            m = await self.get_mistake(mid_str)
            if m and not m.get("mastered"):
                mistakes.append(m)

        return mistakes

    # ==================== ?????? ====================

    async def _update_error_patterns(
        self,
        user_id: str,
        error_category: str,
        error_pattern: str,
        knowledge_name: str,
    ):
        """????????"""
        key = self._error_patterns_key(user_id)
        patterns = await self.redis.redis.hgetall(key)

        # ???????
        cat_count = int(patterns.get(f"cat:{error_category}", 0)) + 1
        await self.redis.redis.hset(key, f"cat:{error_category}", cat_count)

        # ?????????
        if knowledge_name:
            kn_count = int(patterns.get(f"kn:{knowledge_name}", 0)) + 1
            await self.redis.redis.hset(key, f"kn:{knowledge_name}", kn_count)

        # ??????
        if error_pattern:
            ep_count = int(patterns.get(f"ep:{error_pattern}", 0)) + 1
            await self.redis.redis.hset(key, f"ep:{error_pattern}", ep_count)

        await self.redis.expire(key, MISTAKE_TTL)

    async def get_error_patterns(self, user_id: str) -> Dict[str, Any]:
        """??????????"""
        key = self._error_patterns_key(user_id)
        raw = await self.redis.redis.hgetall(key)

        if not raw:
            return {
                "by_category": {},
                "by_knowledge": {},
                "by_pattern": {},
                "weak_points": [],
                "primary_error_type": "",
            }

        result = {
            "by_category": {},
            "by_knowledge": {},
            "by_pattern": {},
            "weak_points": [],
            "primary_error_type": "",
        }

        for k, v in raw.items():
            k_str = k.decode() if isinstance(k, bytes) else k
            count = int(v)
            if k_str.startswith("cat:"):
                result["by_category"][k_str[4:]] = count
            elif k_str.startswith("kn:"):
                result["by_knowledge"][k_str[3:]] = count
            elif k_str.startswith("ep:"):
                result["by_pattern"][k_str[3:]] = count

        # ?????????????? Top 5?
        sorted_kn = sorted(result["by_knowledge"].items(), key=lambda x: x[1], reverse=True)
        result["weak_points"] = [kn for kn, _ in sorted_kn[:5]]

        # ??????
        if result["by_category"]:
            result["primary_error_type"] = max(result["by_category"], key=result["by_category"].get)

        return result

    # ==================== ?????? ====================

    async def generate_daily_review_notifications(
        self,
        user_id: str,
    ) -> List[Dict[str, Any]]:
        """????????????????????"""
        now = datetime.now()
        now_ts = now.timestamp()

        # ????????
        due_ids = await self.redis.redis.zrangebyscore(
            self._review_schedule_key(user_id),
            0, now_ts, start=0, num=50,
        )

        if not due_ids:
            return []

        notifications = []
        notif_key = self._notification_key(user_id)

        for mid in due_ids:
            mid_str = mid.decode() if isinstance(mid, bytes) else mid
            mistake = await self.get_mistake(mid_str)
            if not mistake or mistake.get("mastered"):
                continue

            # ?????????
            last_notif = await self.redis.redis.get(f"last_notif:{user_id}:{mid_str}")
            if last_notif:
                try:
                    last_time = datetime.fromisoformat(last_notif.decode() if isinstance(last_notif, bytes) else last_notif)
                    if last_time.date() == now.date():
                        continue
                except (ValueError, TypeError):
                    pass

            # ??????
            next_review_str = mistake.get("next_review_at")
            overdue_days = 0
            if next_review_str:
                try:
                    next_review = datetime.fromisoformat(next_review_str)
                    overdue_days = (now - next_review).days
                except (ValueError, TypeError):
                    pass

            review_stage = mistake.get("review_stage", 0)
            stage_desc = f"?{review_stage + 1}?" if review_stage < len(EBBINGHAUS_INTERVALS) else "????"

            notification = {
                "id": f"notif_{uuid.uuid4().hex[:8]}",
                "user_id": user_id,
                "mistake_id": mid_str,
                "type": "review_due",
                "title": "??????",
                "message": (
                    f"?{mistake.get('knowledge_name', '?????')}??????"
                    f"?{stage_desc}?{'??' + str(overdue_days) + '?' if overdue_days > 0 else '????'}?"
                ),
                "error_category": mistake.get("error_category", ""),
                "knowledge_name": mistake.get("knowledge_name", ""),
                "review_stage": review_stage,
                "overdue_days": overdue_days,
                "created_at": now.isoformat(),
            }

            await self.redis.redis.lpush(notif_key, json.dumps(notification, ensure_ascii=False))
            await self.redis.redis.setex(
                f"last_notif:{user_id}:{mid_str}",
                86400,
                now.isoformat(),
            )

            notifications.append(notification)

        # ????? 50 ???
        await self.redis.redis.ltrim(notif_key, 0, 49)
        await self.redis.expire(notif_key, 7 * 86400)

        logger.info("???????: user=%s, notifications=%d", user_id, len(notifications))

        return notifications

    async def get_pending_notifications(
        self,
        user_id: str,
        limit: int = 10,
        mark_read: bool = False,
    ) -> List[Dict[str, Any]]:
        """???????"""
        key = self._notification_key(user_id)
        raw_list = await self.redis.redis.lrange(key, 0, limit - 1)

        notifications = []
        for raw in raw_list:
            try:
                data = raw.decode() if isinstance(raw, bytes) else raw
                notifications.append(json.loads(data))
            except json.JSONDecodeError:
                continue

        if mark_read and notifications:
            await self.redis.redis.ltrim(key, len(notifications), -1)

        return notifications

    async def clear_notifications(self, user_id: str) -> int:
        """??????"""
        key = self._notification_key(user_id)
        return await self.redis.redis.delete(key)

    # ==================== ?? ====================

    async def get_stats(self, user_id: str) -> Dict[str, Any]:
        """????????"""
        total = await self.redis.redis.zcard(self._mistake_index_key(user_id))

        now_ts = datetime.now().timestamp()
        due = await self.redis.redis.zcount(
            self._review_schedule_key(user_id), 0, now_ts,
        )

        future_ts = (datetime.now() + timedelta(days=7)).timestamp()
        upcoming = await self.redis.redis.zcount(
            self._review_schedule_key(user_id), now_ts, future_ts,
        )

        patterns = await self.get_error_patterns(user_id)

        return {
            "total_mistakes": int(total),
            "due_reviews": int(due),
            "upcoming_reviews_7d": int(upcoming),
            "weak_points": patterns.get("weak_points", []),
            "primary_error_type": patterns.get("primary_error_type", ""),
            "by_category": patterns.get("by_category", {}),
        }


# ??????
ERROR_CATEGORY_LABELS = {
    "concept_unclear": "????",
    "careless": "????",
    "wrong_approach": "????",
    "incomplete": "?????",
    "correct": "????",
}
