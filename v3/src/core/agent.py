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

        TODO: 阶段二 - 接入LLM (OpenAI/Claude/本地模型)
          1. 构造prompt (系统提示 + 历史消息 + 当前输入)
          2. 调用LLM API获取回复
          3. 解析回复，判断是否需要调用工具
          4. 如需工具 -> 执行工具 -> 将结果反馈给LLM -> 获取最终回复

        TODO: 阶段三 - 实现工具调用链 (ReAct模式)
          1. LLM决定是否调用工具
          2. 执行工具，获取结果
          3. 将工具结果传回LLM
          4. 循环直到LLM给出最终答案
        """
        self.memory.add_message("user", message, context)

        response = self._generate_response(message, context)

        self.memory.add_message("assistant", response)
        return response

    def _generate_response(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        生成回复

        TODO: 阶段二 - 替换为LLM调用
          - 根据配置选择LLM provider (openai/claude/local)
          - 构造messages列表 (system + history + user)
          - 处理streaming响应 (可选)
          - 错误处理与重试
        """
        # 临时占位实现
        return f"Echo: {message}"

    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return self.memory.get_messages(limit=limit)

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
