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
        tools: Optional[List[Tool]] = None,
        llm=None,
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.created_at = datetime.now()

        # 初始化 LLM
        self.llm = llm

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
            context: 可选上下文（session_id, knowledge_ids 等）

        Returns:
            Agent 回复文本
        """
        self.memory.add_message("user", message, context)

        response = self._generate_response(message, context)

        self.memory.add_message("assistant", response)
        return response

    def _generate_response(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        生成回复 — 调用 LLM

        构造 messages 列表: system prompt + 历史消息 + 当前用户消息
        """
        if not self.llm:
            return f"Echo: {message}"

        # 构造消息列表
        messages = [
            {
                "role": "system",
                "content": (
                    f"你是 {self.name}，{self.description}。"
                    "请用中文回答用户的问题，保持友好和专业。"
                ),
            }
        ]

        # 加入历史消息（最近 10 条）
        history = self.memory.get_messages(limit=10)
        for msg in history:
            if msg["role"] in ("user", "assistant"):
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

        # 调用 LLM
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 在已有事件循环中（FastAPI），用 asyncio.ensure_future 等待
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        self.llm.chat(messages)
                    )
                    return future.result(timeout=60)
            else:
                return asyncio.run(self.llm.chat(messages))
        except Exception as e:
            return f"[LLM 调用失败: {e}]"

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
            "available_tools": self.list_tools(),
            "llm_provider": type(self.llm).__name__ if self.llm else "None (Echo mode)",
        }

    def __repr__(self) -> str:
        return f"Agent(name='{self.name}', id='{self.id}')"
