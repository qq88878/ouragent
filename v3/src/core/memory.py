"""
内存管理模块
处理对话历史和上下文存储
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import deque


class Memory:
    """
    内存管理类
    存储和管理对话历史
    """

    def __init__(self, max_size: int = 100):
        """
        初始化内存

        Args:
            max_size: 最大存储容量（对话轮数）
        """
        self.max_size = max_size
        self.messages: deque = deque(maxlen=max_size)
        self.metadata: Dict[str, Any] = {}

    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        添加一条消息

        Args:
            role: 消息角色（user/assistant/system）
            content: 消息内容
            metadata: 元数据（可选）
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.messages.append(message)

    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取消息历史

        Args:
            limit: 返回的消息数量限制

        Returns:
            消息列表
        """
        if limit is None:
            return list(self.messages)
        return list(self.messages)[-limit:]

    def get_last_message(self) -> Optional[Dict[str, Any]]:
        """获取最后一条消息"""
        if self.messages:
            return self.messages[-1]
        return None

    def get_user_messages(self) -> List[Dict[str, Any]]:
        """获取所有用户消息"""
        return [m for m in self.messages if m["role"] == "user"]

    def get_assistant_messages(self) -> List[Dict[str, Any]]:
        """获取所有助手消息"""
        return [m for m in self.messages if m["role"] == "assistant"]

    def clear(self) -> None:
        """清除所有消息"""
        self.messages.clear()

    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据"""
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        return self.metadata.get(key, default)

    def get_context_window(self, window_size: int = 10) -> List[Dict[str, Any]]:
        """
        获取上下文窗口

        Args:
            window_size: 窗口大小

        Returns:
            最近的消息列表
        """
        return self.get_messages(limit=window_size)

    def get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况"""
        return {
            "current_size": len(self.messages),
            "max_size": self.max_size,
            "usage_percentage": (len(self.messages) / self.max_size) * 100 if self.max_size > 0 else 0
        }

    def __len__(self) -> int:
        """返回消息数量"""
        return len(self.messages)

    def __repr__(self) -> str:
        return f"Memory(size={len(self.messages)}, max_size={self.max_size})"
