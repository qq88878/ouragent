"""对话历史存储 - 基于 Redis List 的消息队列"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .redis_client import RedisClient

logger = logging.getLogger(__name__)

# 对话历史过期时间：7天
CONVERSATION_TTL = 7 * 24 * 3600
# 默认保留最近 N 条消息
DEFAULT_HISTORY_LIMIT = 50


class ConversationMemory:
    """
    对话历史管理

    使用 Redis List 存储消息，支持：
    - 追加消息（左推入，最新在前）
    - 获取最近 N 条消息
    - 按会话隔离
    - 自动过期（TTL）
    """

    def __init__(self, redis: RedisClient, session_id: str):
        self.redis = redis
        self.session_id = session_id

    def _list_key(self) -> str:
        return f"session:{self.session_id}:messages"

    def _count_key(self) -> str:
        return f"session:{self.session_id}:msg_count"

    async def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        添加一条消息

        Args:
            role: "user" 或 "assistant"
            content: 消息内容
            metadata: 额外元数据（如 token 使用量、工具调用等）

        Returns:
            当前消息总数
        """
        import json
        from datetime import datetime

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            **(metadata or {}),
        }

        key = self._list_key()
        data = json.dumps(message, ensure_ascii=False)

        # 左推入（最新在前）
        await self.redis.redis.lpush(key, data)
        # 续期 TTL
        await self.redis.expire(key, CONVERSATION_TTL)

        # 更新计数
        count = await self.redis.incr(self._count_key())
        await self.redis.expire(self._count_key(), CONVERSATION_TTL)

        return count

    async def get_history(
        self,
        limit: int = DEFAULT_HISTORY_LIMIT,
        offset: int = 0,
    ) -> List[Dict[str, str]]:
        """
        获取对话历史（按时间正序）

        Args:
            limit: 返回条数
            offset: 偏移量

        Returns:
            [{"role": "user", "content": "..."}, ...]
        """
        import json

        key = self._list_key()
        # 获取范围（LRANGE 是左闭右闭）
        raw_list = await self.redis.redis.lrange(key, offset, offset + limit - 1)

        messages = []
        for raw in reversed(raw_list):  # 反转为时间正序
            try:
                msg = json.loads(raw)
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })
            except (json.JSONDecodeError, KeyError):
                continue

        return messages

    async def get_full_context(
        self,
        limit: int = DEFAULT_HISTORY_LIMIT,
    ) -> List[Dict[str, str]]:
        """获取完整对话上下文（用于发送给 LLM）"""
        return await self.get_history(limit=limit)

    async def get_message_count(self) -> int:
        """获取消息总数"""
        count = await self.redis.get_json(self._count_key())
        return count if count else 0

    async def clear(self) -> bool:
        """清空对话历史"""
        await self.redis.delete(self._list_key())
        await self.redis.delete(self._count_key())
        return True

    async def get_recent_context_for_llm(
        self,
        max_messages: int = 10,
    ) -> List[Dict[str, str]]:
        """
        获取最近 N 条消息，格式化为 LLM 对话格式

        返回格式: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        """
        return await self.get_history(limit=max_messages)
