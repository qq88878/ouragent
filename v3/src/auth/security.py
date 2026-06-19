"""
服务间认证 + JWT用户认证
支持两种认证方式：
1. X-Service-Key — Java后端内部调用
2. JWT Bearer Token — 前端直接调用
"""

import os
import logging
from fastapi import Depends, HTTPException, Header, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# 服务间共享密钥
AGENT_SERVICE_KEY = os.environ.get("AGENT_SERVICE_KEY", "default-dev-key")

# JWT认证方案
security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    x_service_key: str = Header(default=None, alias="X-Service-Key"),
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> dict:
    """
    双重认证：JWT Token 或 X-Service-Key

    优先级：JWT > X-Service-Key
    """
    # 方式1：JWT Bearer Token
    if credentials:
        try:
            from src.auth.jwt_handler import decode_jwt_token
            payload = decode_jwt_token(credentials.credentials)
            return {"user_id": str(payload.get("user_id", payload.get("sub", ""))), "authenticated": True, "auth_type": "jwt"}
        except Exception as e:
            logger.warning(f"JWT验证失败: {e}")

    # 方式2：X-Service-Key
    if x_service_key and x_service_key == AGENT_SERVICE_KEY:
        return {"service": "java-backend", "authenticated": True, "auth_type": "service_key"}

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="认证失败：请提供有效的JWT Token或服务密钥",
    )

