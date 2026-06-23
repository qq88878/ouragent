"""Agent 基类 - 所有专业 Agent 的公共基础"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Agent 基类

    每个 Agent 专注一个职责，通过 LLM 完成特定任务。
    子类必须实现：
    - name: Agent 名称
    - system_prompt: 系统提示词
    - execute(): 统一的任务执行接口
    """

    name: str = "base"
    description: str = ""

    def __init__(self, llm, tools: list | None = None):
        self.llm = llm
        self.tools = {t.name: t for t in (tools or [])}

    @property
    def system_prompt(self) -> str:
        return "你是一个AI助手。"

    @abstractmethod
    async def execute(self, task_type: str, **kwargs) -> Dict[str, Any]:
        """
        统一的任务执行接口

        Args:
            task_type: 任务类型（由子类定义）
            **kwargs: 任务参数

        Returns:
            任务结果字典
        """
        ...

    def register_tool(self, tool) -> None:
        self.tools[tool.name] = tool

    async def chat(
        self,
        user_message: str,
        context: str = "",
        history: List[Dict[str, str]] | None = None,
        **kwargs,
    ) -> str:
        """
        调用 LLM 生成回复

        Args:
            user_message: 用户输入
            context: 检索到的知识上下文
            history: 对话历史 [{"role": "user/assistant", "content": "..."}]
        """
        messages = [{"role": "system", "content": self.system_prompt}]

        if context:
            messages.append({
                "role": "system",
                "content": f"以下是相关知识库内容，请基于这些内容回答:\n\n{context}",
            })

        if history:
            messages.extend(history[-10:])

        messages.append({"role": "user", "content": user_message})

        try:
            return await self.llm.chat(messages, **kwargs)
        except Exception as e:
            logger.error("[%s] LLM 调用失败: %s", self.name, e)
            return f"[Agent {self.name} 调用失败: {e}]"

    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """调用已注册的工具"""
        tool = self.tools.get(tool_name)
        if tool is None:
            raise ValueError(f"工具 {tool_name} 未注册到 {self.name}")
        return await tool.execute(**kwargs)

    def get_info(self) -> Dict[str, Any]:
        """获取 Agent 基本信息"""
        return {
            "name": self.name,
            "description": self.description,
            "tools": list(self.tools.keys()),
        }
