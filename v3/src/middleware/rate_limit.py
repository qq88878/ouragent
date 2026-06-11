"""API 限流中间件 - 基于 Redis 的滑动窗口限流"""

from __future__ import annotations

import logging
import time
from typing import Callable, Dict, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.memory.redis_client import get_redis, RedisClient

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """限流配置"""

    def __init__(
        self,
        requests: int = 100,
        window: int = 60,
        burst: int = 10,
    ):
        self.requests = requests  # 窗口期内允许的最大请求数
        self.window = window  # 窗口期（秒）
        self.burst = burst  # 突发请求允许数


# 默认限流配置
DEFAULT_CONFIG = RateLimitConfig(requests=100, window=60)

# 端点特定限流配置
ENDPOINT_CONFIGS: Dict[str, RateLimitConfig] = {
    "/agent/chat": RateLimitConfig(requests=30, window=60),
    "/agent/chat/context": RateLimitConfig(requests=30, window=60),
    "/agent/generate": RateLimitConfig(requests=10, window=60),
    "/agent/analyze": RateLimitConfig(requests=20, window=60),
    "/agent/plan": RateLimitConfig(requests=10, window=60),
    "/agent/sessions": RateLimitConfig(requests=50, window=60),
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    基于 Redis 的滑动窗口限流中间件

    使用 Redis 的有序集合实现滑动窗口算法：
    - 每个请求记录时间戳
    - 清理窗口外的旧记录
    - 检查窗口内的请求数是否超限
    """

    def __init__(self, app, redis_client: Optional[RedisClient] = None):
        super().__init__(app)
        self._redis: Optional[RedisClient] = redis_client

    async def _get_redis(self) -> RedisClient:
        if self._redis is None:
            conn = await get_redis()
            self._redis = RedisClient(conn)
        return self._redis

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端 IP"""
        # 优先从代理头获取
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        return request.client.host if request.client else "unknown"

    def _get_config(self, path: str) -> RateLimitConfig:
        """获取端点的限流配置"""
        # 精确匹配
        if path in ENDPOINT_CONFIGS:
            return ENDPOINT_CONFIGS[path]
        # 前缀匹配
        for prefix, config in ENDPOINT_CONFIGS.items():
            if path.startswith(prefix):
                return config
        return DEFAULT_CONFIG

    async def _check_rate_limit(
        self,
        client_ip: str,
        path: str,
        config: RateLimitConfig,
    ) -> tuple[bool, int, int]:
        """
        检查是否超过限流

        Returns:
            (is_allowed, remaining, retry_after)
        """
        redis = await self._get_redis()
        key = f"rate_limit:{client_ip}:{path}"

        now = time.time()
        window_start = now - config.window

        try:
            pipe = redis.redis.pipeline()

            # 清理窗口外的旧记录
            pipe.zremrangebyscore(key, 0, window_start)

            # 统计窗口内的请求数
            pipe.zcard(key)

            # 添加当前请求
            pipe.zadd(key, {str(now): now})

            # 设置 key 过期
            pipe.expire(key, config.window)

            results = await pipe.execute()

            request_count = results[1]

            if request_count >= config.requests:
                # 计算需要等待的时间
                oldest = await redis.redis.zrange(key, 0, 0, withscores=True)
                if oldest:
                    retry_after = int(oldest[0][1] + config.window - now) + 1
                else:
                    retry_after = config.window
                return False, 0, retry_after

            return True, config.requests - request_count - 1, 0

        except Exception as e:
            logger.error("限流检查失败: %s", e)
            # Redis 故障时放行
            return True, config.requests, 0

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        # 跳过健康检查和 OPTIONS 请求
        if request.url.path in ("/health", "/docs", "/openapi.json"):
            return await call_next(request)
        if request.method == "OPTIONS":
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        path = request.url.path
        config = self._get_config(path)

        is_allowed, remaining, retry_after = await self._check_rate_limit(
            client_ip, path, config
        )

        if not is_allowed:
            logger.warning("限流触发: ip=%s path=%s", client_ip, path)
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"请求过于频繁，请 {retry_after} 秒后重试",
                        "retry_after": retry_after,
                    }
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(config.requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                },
            )

        # 正常处理请求
        response = await call_next(request)

        # 添加限流响应头
        response.headers["X-RateLimit-Limit"] = str(config.requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + config.window)

        return response
