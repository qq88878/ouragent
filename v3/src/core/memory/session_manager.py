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


class SessionManager:
    """
    会话管理器

    职责：
    - 生成唯一的 session_id
    - 存储/读取会话元数据（创建时间、用户ID、课程ID等）
    - 管理会话生命周期
    """

    def __init__(self, redis: RedisClient):
        self.redis = redis

    def _meta_key(self, session_id: str) -> str:
        return f"session:{session_id}:meta"

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
        meta = {
            "session_id": session_id,
            "user_id": user_id,
            "course_id": course_id,
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "message_count": 0,
            **(metadata or {}),
        }

        await self.redis.set_json(
            self._meta_key(session_id),
            meta,
            ttl=SESSION_META_TTL,
        )

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
        """删除会话（同时删除关联的对话历史）"""
        from .conversation_memory import ConversationMemory

        # 删除元数据
        deleted = await self.redis.delete(self._meta_key(session_id))

        # 删除对话历史
        conv = ConversationMemory(self.redis, session_id)
        await conv.clear()

        logger.info("会话删除: %s", session_id)
        return deleted > 0

    async def list_user_sessions(
        self,
        user_id: str,
        limit: int = 20,
    ) -> list[Dict[str, Any]]:
        """列出用户的会话（按创建时间倒序）"""
        pattern = f"session:*:meta"
        keys = await self.redis.scan_keys(pattern)

        sessions = []
        for key in keys:
            meta = await self.redis.get_json(key)
            if meta and meta.get("user_id") == user_id:
                sessions.append(meta)

        # 按创建时间倒序
        sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return sessions[:limit]
