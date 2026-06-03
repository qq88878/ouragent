"""
Agent核心模块
实现基础的Agent类和相关功能
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from .memory import Memory
from .tools import Tool


class Agent:
    """
    基础Agent类
    实现Agent的核心功能，包括对话、记忆和工具调用
    """

    def __init__(
        self,
        name: str = "Agent",
        description: str = "A helpful AI assistant",
        memory_size: int = 100,
        tools: Optional[List[Tool]] = None
    ):
        """
        初始化Agent

        Args:
            name: Agent名称
            description: Agent描述
            memory_size: 记忆容量（最大对话轮数）
            tools: 可用的工具列表
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.created_at = datetime.now()

        # 初始化内存
        self.memory = Memory(max_size=memory_size)

        # 初始化工具
        self.tools = {}
        if tools:
            for tool in tools:
                self.register_tool(tool)

    def register_tool(self, tool: Tool) -> None:
        """注册一个工具"""
        self.tools[tool.name] = tool

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """获取指定名称的工具"""
        return self.tools.get(tool_name)

    def list_tools(self) -> List[str]:
        """列出所有可用工具的名称"""
        return list(self.tools.keys())

    def chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        与Agent对话

        Args:
            message: 用户消息
            context: 上下文信息

        Returns:
            Agent的回复
        """
        # 记录用户消息
        self.memory.add_message("user", message, context)

        # 生成回复（基础实现，子类应覆盖）
        response = self._generate_response(message, context)

        # 记录Agent回复
        self.memory.add_message("assistant", response)

        return response

    def _generate_response(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        生成回复（应被子类覆盖）

        Args:
            message: 用户消息
            context: 上下文信息

        Returns:
            生成的回复
        """
        # 基础实现：简单的回显
        return f"Echo: {message}"

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return self.memory.get_messages()

    def clear_memory(self) -> None:
        """清除记忆"""
        self.memory.clear()

    def get_status(self) -> Dict[str, Any]:
        """获取Agent状态"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "memory_size": len(self.memory),
            "available_tools": self.list_tools()
        }

    def __repr__(self) -> str:
        return f"Agent(name='{self.name}', id='{self.id}')"
