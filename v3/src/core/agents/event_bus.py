"""Agent 事件总线 - Agent 间异步通信机制"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class AgentEventBus:
    """
    轻量级异步事件总线

    用于 Agent 之间的解耦通信，支持：
    - 事件订阅（on）
    - 事件触发（emit）
    - 事件历史记录（用于调试）
    """

    def __init__(self, max_history: int = 200):
        self._handlers: Dict[str, List[Callable]] = {}
        self._history: List[Dict[str, Any]] = []
        self._max_history = max_history

    def on(self, event: str, handler: Callable) -> None:
        """订阅事件"""
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)
        logger.debug("事件订阅: %s -> %s", event, handler.__name__ if hasattr(handler, '__name__') else handler)

    def off(self, event: str, handler: Optional[Callable] = None) -> None:
        """取消订阅"""
        if handler is None:
            self._handlers.pop(event, None)
        elif event in self._handlers:
            self._handlers[event] = [h for h in self._handlers[event] if h != handler]

    async def emit(self, event: str, data: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        触发事件，异步调用所有订阅者

        Args:
            event: 事件名称
            data: 事件数据

        Returns:
            所有订阅者返回值的列表
        """
        data = data or {}
        results = []

        # 记录事件历史
        record = {
            "event": event,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "handler_count": len(self._handlers.get(event, [])),
        }
        self._history.append(record)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        handlers = self._handlers.get(event, [])
        if not handlers:
            return results

        for handler in handlers:
            try:
                if asyncio_iscoroutinefunction(handler):
                    result = await handler(data)
                else:
                    result = handler(data)
                results.append(result)
            except Exception as e:
                logger.error("事件处理失败 [%s]: %s", event, e)
                results.append(None)

        return results

    def get_history(self, limit: int = 50, event: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取事件历史"""
        history = self._history
        if event:
            history = [r for r in history if r["event"] == event]
        return history[-limit:]

    def clear_history(self) -> None:
        """清空事件历史"""
        self._history.clear()

    def get_subscribed_events(self) -> List[str]:
        """获取所有已订阅的事件名"""
        return list(self._handlers.keys())


def asyncio_iscoroutinefunction(obj) -> bool:
    """检查是否为异步函数"""
    import asyncio
    return asyncio.iscoroutinefunction(obj)
