"""Redis 连接管理 - 连接池、健康检查、序列化"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from config.settings import settings

logger = logging.getLogger(__name__)

# 全局连接池（单例）
_pool: Optional[ConnectionPool] = None
_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """获取 Redis 客户端实例（懒初始化）"""
    global _pool, _client

    if _client is None:
        _pool = ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD or None,
            max_connections=20,
            decode_responses=True,
        )
        _client = redis.Redis(connection_pool=_pool)
        logger.info("Redis 连接池初始化: %s:%s", settings.REDIS_HOST, settings.REDIS_PORT)

    return _client


async def close_redis():
    """关闭 Redis 连接"""
    global _pool, _client
    if _client:
        await _client.close()
        _client = None
    if _pool:
        await _pool.disconnect()
        _pool = None
        logger.info("Redis 连接已关闭")


class RedisClient:
    """Redis 客户端封装，提供便捷的序列化/反序列化方法"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def get_json(self, key: str) -> Optional[Any]:
        """获取 JSON 值"""
        data = await self.redis.get(key)
        if data is None:
            return None
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            logger.warning("Redis JSON 解析失败: %s", key)
            return None

    async def set_json(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """设置 JSON 值"""
        try:
            data = json.dumps(value, ensure_ascii=False)
            if ttl:
                await self.redis.setex(key, ttl, data)
            else:
                await self.redis.set(key, data)
            return True
        except Exception as e:
            logger.error("Redis 写入失败 %s: %s", key, e)
            return False

    async def delete(self, key: str) -> bool:
        """删除键"""
        return bool(await self.redis.delete(key))

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return bool(await self.redis.exists(key))

    async def expire(self, key: str, ttl: int) -> bool:
        """设置过期时间"""
        return bool(await self.redis.expire(key, ttl))

    async def keys(self, pattern: str) -> list[str]:
        """按模式匹配键（慎用，生产环境用 scan）"""
        return await self.redis.keys(pattern)

    async def scan_keys(self, pattern: str, count: int = 100) -> list[str]:
        """安全地扫描键"""
        keys = []
        async for key in self.redis.scan_iter(match=pattern, count=count):
            keys.append(key)
        return keys

    async def incr(self, key: str) -> int:
        """递增计数器"""
        return await self.redis.incr(key)

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            return await self.redis.ping()
        except Exception:
            return False
