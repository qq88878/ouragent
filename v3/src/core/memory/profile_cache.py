"""用户画像缓存 - 避免重复调用 LLM 分析"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .redis_client import RedisClient

logger = logging.getLogger(__name__)

# 画像缓存过期时间：24小时
PROFILE_TTL = 24 * 3600


class ProfileCache:
    """
    用户画像缓存

    缓存策略：
    - key: profile:{user_id}:{course_id}
    - 每次分析后缓存结果
    - 下次查询时优先返回缓存
    - 可手动清除（如用户主动更新画像）
    """

    def __init__(self, redis: RedisClient):
        self.redis = redis

    def _profile_key(self, user_id: str, course_id: Optional[int] = None) -> str:
        if course_id:
            return f"profile:{user_id}:{course_id}"
        return f"profile:{user_id}:global"

    async def get_profile(
        self,
        user_id: str,
        course_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        获取缓存的用户画像

        Returns:
            画像 dict 或 None（缓存未命中）
        """
        key = self._profile_key(user_id, course_id)
        return await self.redis.get_json(key)

    async def set_profile(
        self,
        user_id: str,
        profile: Dict[str, Any],
        course_id: Optional[int] = None,
        ttl: int = PROFILE_TTL,
    ) -> bool:
        """
        缓存用户画像

        Args:
            user_id: 用户ID
            profile: 画像数据
            course_id: 课程ID（可选）
            ttl: 过期时间（秒）
        """
        key = self._profile_key(user_id, course_id)

        # 添加元信息
        profile_with_meta = {
            **profile,
            "_cached": True,
            "_user_id": user_id,
            "_course_id": course_id,
        }

        success = await self.redis.set_json(key, profile_with_meta, ttl=ttl)
        if success:
            logger.debug("画像缓存已更新: user=%s course=%s", user_id, course_id)
        return success

    async def invalidate_profile(
        self,
        user_id: str,
        course_id: Optional[int] = None,
    ) -> bool:
        """清除指定用户的画像缓存"""
        key = self._profile_key(user_id, course_id)
        return await self.redis.delete(key)

    async def invalidate_user_all(self, user_id: str) -> int:
        """清除用户的所有画像缓存"""
        pattern = f"profile:{user_id}:*"
        keys = await self.redis.scan_keys(pattern)

        count = 0
        for key in keys:
            if await self.redis.delete(key):
                count += 1

        logger.info("清除用户 %s 的 %d 个画像缓存", user_id, count)
        return count


class RAGCache:
    """
    RAG 检索结果缓存

    缓存策略：
    - key: rag:{query_hash}
    - 缓存检索结果，避免重复向量搜索
    - TTL 较短（1小时），因为知识库可能更新
    """

    RAG_TTL = 3600  # 1小时

    def __init__(self, redis: RedisClient):
        self.redis = redis

    def _rag_key(self, query: str, knowledge_ids: Optional[list] = None) -> str:
        import hashlib
        # 构造缓存 key：query + knowledge_ids
        content = query
        if knowledge_ids:
            content += f":{','.join(sorted(map(str, knowledge_ids)))}"
        query_hash = hashlib.md5(content.encode()).hexdigest()[:12]
        return f"rag:{query_hash}"

    async def get_results(
        self,
        query: str,
        knowledge_ids: Optional[list] = None,
    ) -> Optional[list]:
        """获取缓存的 RAG 结果"""
        key = self._rag_key(query, knowledge_ids)
        return await self.redis.get_json(key)

    async def set_results(
        self,
        query: str,
        results: list,
        knowledge_ids: Optional[list] = None,
    ) -> bool:
        """缓存 RAG 结果"""
        key = self._rag_key(query, knowledge_ids)
        return await self.redis.set_json(key, results, ttl=self.RAG_TTL)
