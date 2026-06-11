"""会话管理 - session_id 生成、会话生命周期"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from .redis_client import RedisClient

logger = logging.getLogger(__name__)

# 会话元数据过期时间：7天
SESSION_META_TTL = 7 * 24 * 3600
# 用户会话索引过期时间：30天（比会话更长，避免索引丢失）
USER_SESSIONS_INDEX_TTL = 30 * 24 * 3600


class SessionManager:
    """
    会话管理器

    职责：
    - 生成唯一的 session_id
    - 存储/读取会话元数据（创建时间、用户ID、课程ID等）
    - 管理会话生命周期
    - 维护用户会话索引（优化查询性能）

    Redis 数据结构：
    - session:{session_id}:meta (Hash) - 会话元数据
    - user:{user_id}:sessions (Sorted Set) - 用户会话索引，score 为创建时间戳
    """

    def __init__(self, redis: RedisClient):
        self.redis = redis

    def _meta_key(self, session_id: str) -> str:
        """会话元数据 key"""
        return f"session:{session_id}:meta"

    def _user_sessions_key(self, user_id: str) -> str:
        """用户会话索引 key"""
        return f"user:{user_id}:sessions"

    async def create_session(
        self,
        user_id: str,
        course_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        创建新会话

        Args:
            user_id: 用户ID
            course_id: 课程ID（可选）
            metadata: 额外元数据

        Returns:
            session_id
        """
        session_id = str(uuid.uuid4())
        now = datetime.now()
        timestamp = now.timestamp()

        meta = {
            "session_id": session_id,
            "user_id": user_id,
            "course_id": course_id,
            "created_at": now.isoformat(),
            "last_active": now.isoformat(),
            "message_count": 0,
            **(metadata or {}),
        }

        # 使用 pipeline 保证原子性
        pipe = self.redis.redis.pipeline()

        # 1. 保存会话元数据
        import json
        meta_data = json.dumps(meta, ensure_ascii=False)
        pipe.setex(self._meta_key(session_id), SESSION_META_TTL, meta_data)

        # 2. 添加到用户会话索引（Sorted Set，score 为时间戳）
        pipe.zadd(self._user_sessions_key(user_id), {session_id: timestamp})

        # 3. 续期用户索引
        pipe.expire(self._user_sessions_key(user_id), USER_SESSIONS_INDEX_TTL)

        await pipe.execute()

        logger.info("会话创建: %s (user=%s)", session_id, user_id)
        return session_id

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话元数据"""
        return await self.redis.get_json(self._meta_key(session_id))

    async def touch_session(self, session_id: str) -> bool:
        """更新会话最后活跃时间，续期 TTL"""
        meta = await self.get_session(session_id)
        if not meta:
            return False

        meta["last_active"] = datetime.now().isoformat()
        meta["message_count"] = meta.get("message_count", 0) + 1

        await self.redis.set_json(
            self._meta_key(session_id),
            meta,
            ttl=SESSION_META_TTL,
        )
        return True

    async def delete_session(self, session_id: str) -> bool:
        """删除会话（同时删除关联的对话历史和索引）"""
        from .conversation_memory import ConversationMemory

        # 先获取会话信息（需要 user_id 来清理索引）
        meta = await self.get_session(session_id)
        user_id = meta.get("user_id") if meta else None

        # 使用 pipeline 批量操作
        pipe = self.redis.redis.pipeline()

        # 1. 删除会话元数据
        pipe.delete(self._meta_key(session_id))

        # 2. 从用户索引中移除
        if user_id:
            pipe.zrem(self._user_sessions_key(user_id), session_id)

        await pipe.execute()

        # 3. 删除对话历史
        conv = ConversationMemory(self.redis, session_id)
        await conv.clear()

        logger.info("会话删除: %s (user=%s)", session_id, user_id)
        return meta is not None

    async def list_user_sessions(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Dict[str, Any]]:
        """
        列出用户的会话（按创建时间倒序）

        使用 Redis Sorted Set 索引，性能优化：
        - 时间复杂度 O(log(N) + M)，N 为用户会话数，M 为返回数
        - 避免全量扫描

        Args:
            user_id: 用户ID
            limit: 返回数量限制
            offset: 偏移量（用于分页）
        """
        index_key = self._user_sessions_key(user_id)

        # 从 Sorted Set 获取 session_id 列表（按 score 倒序）
        session_ids = await self.redis.redis.zrevrange(
            index_key,
            offset,
            offset + limit - 1,
        )

        if not session_ids:
            return []

        # 批量获取会话元数据
        sessions = []
        for session_id in session_ids:
            if isinstance(session_id, bytes):
                session_id = session_id.decode("utf-8")
            meta = await self.get_session(session_id)
            if meta:
                sessions.append(meta)

        return sessions

    async def count_user_sessions(self, user_id: str) -> int:
        """统计用户会话数量"""
        return await self.redis.redis.zcard(self._user_sessions_key(user_id))

    async def cleanup_expired_sessions(self, user_id: str) -> int:
        """
        清理用户已过期的会话索引

        当会话元数据过期但索引还存在时，调用此方法清理。
        """
        index_key = self._user_sessions_key(user_id)
        session_ids = await self.redis.redis.zrange(index_key, 0, -1)

        cleaned = 0
        for session_id in session_ids:
            if isinstance(session_id, bytes):
                session_id = session_id.decode("utf-8")
            # 检查会话元数据是否存在
            if not await self.redis.exists(self._meta_key(session_id)):
                await self.redis.redis.zrem(index_key, session_id)
                cleaned += 1

        if cleaned > 0:
            logger.info("清理用户 %s 的 %d 个过期索引", user_id, cleaned)

        return cleaned
