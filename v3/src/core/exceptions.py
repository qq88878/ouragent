"""自定义异常类 - 区分业务异常和系统异常"""

from typing import Any, Dict, Optional


class AgentException(Exception):
    """Agent 基础异常"""

    def __init__(
        self,
        message: str,
        code: str = "AGENT_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(AgentException):
    """输入验证错误"""

    def __init__(self, message: str, field: str = "", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details={"field": field, **(details or {})},
        )


class NotFoundError(AgentException):
    """资源不存在"""

    def __init__(self, resource: str, resource_id: Any = None):
        message = f"{resource}不存在"
        if resource_id:
            message = f"{resource} '{resource_id}' 不存在"
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "resource_id": resource_id},
        )


class ServiceUnavailableError(AgentException):
    """服务不可用"""

    def __init__(self, service: str, reason: str = ""):
        message = f"{service}服务不可用"
        if reason:
            message = f"{service}服务不可用: {reason}"
        super().__init__(
            message=message,
            code="SERVICE_UNAVAILABLE",
            status_code=503,
            details={"service": service, "reason": reason},
        )


class LLMError(AgentException):
    """LLM 调用错误"""

    def __init__(self, message: str, provider: str = "", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="LLM_ERROR",
            status_code=502,
            details={"provider": provider, **(details or {})},
        )


class RateLimitError(AgentException):
    """请求限流"""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            message=f"请求过于频繁，请 {retry_after} 秒后重试",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after": retry_after},
        )
