"""
服务间认证 - Agent微服务内部调用鉴权
使用共享密钥验证，不面向终端用户
"""

import os
from fastapi import Depends, HTTPException, Header, status

# 服务间共享密钥（从环境变量读取）
AGENT_SERVICE_KEY = os.environ.get("AGENT_SERVICE_KEY", "default-dev-key")


async def get_current_user(x_service_key: str = Header(..., alias="X-Service-Key")) -> dict:
    """
    验证服务间密钥（FastAPI 依赖注入）

    Java后端调用Agent时必须在请求头中携带:
        X-Service-Key: <密钥>

    Returns:
        dict: 包含 service 信息的字典

    Raises:
        HTTPException 403: 密钥不匹配
    """
    if x_service_key != AGENT_SERVICE_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无效的服务密钥",
        )

    return {"service": "java-backend", "authenticated": True}
