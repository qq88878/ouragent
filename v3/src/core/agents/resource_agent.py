"""教学资源生成 Agent - 生成题目、思维导图、学习资料"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .base import BaseAgent
from ..tools.retrieval import RetrievalTool
from ..utils import parse_llm_json

logger = logging.getLogger(__name__)


class ResourceAgent(BaseAgent):
    """
    教学资源生成 Agent

    职责：
    - 基于知识库内容生成练习题
    - 生成思维导图结构
    - 生成学习摘要和笔记
    - 所有生成内容都基于 RAG 检索，确保准确性
    """

    name = "resource_agent"
    description = "生成教学资源：练习题、思维导图、学习摘要"

    # 支持的任务类型
    TASK_GENERATE_QUESTIONS = "generate_questions"
    TASK_GENERATE_MINDMAP = "generate_mindmap"
    TASK_GENERATE_SUMMARY = "generate_summary"

    @property
    def system_prompt(self) -> str:
        return """你是一位资深教育内容创作者。

你的任务是基于知识库内容生成高质量的教学资源:
1. 练习题：覆盖核心知识点，难度适中，有详细解析
2. 思维导图：结构清晰，层次分明
3. 学习摘要：简洁易懂，突出重点

所有内容必须基于提供的知识库，不要编造。"""

    async def execute(self, task_type: str, **kwargs) -> Dict[str, Any]:
        """
        统一任务执行接口

        Args:
            task_type: "generate_questions" | "generate_mindmap" | "generate_summary"
            **kwargs: 对应方法的参数
        """
        if task_type == self.TASK_GENERATE_QUESTIONS:
            return await self.generate_questions(
                topic=kwargs.get("topic", ""),
                knowledge_ids=kwargs.get("knowledge_ids"),
                difficulty=kwargs.get("difficulty", "medium"),
                count=kwargs.get("count", 5),
                question_type=kwargs.get("question_type", "mixed"),
                student_profile=kwargs.get("student_profile", {}),
            )
        elif task_type == self.TASK_GENERATE_MINDMAP:
            return await self.generate_mindmap(
                topic=kwargs.get("topic", ""),
                knowledge_ids=kwargs.get("knowledge_ids"),
                student_profile=kwargs.get("student_profile", {}),
            )
        elif task_type == self.TASK_GENERATE_SUMMARY:
            return await self.generate_summary(
                topic=kwargs.get("topic", ""),
                knowledge_ids=kwargs.get("knowledge_ids"),
                student_profile=kwargs.get("student_profile", {}),
            )
        else:
            raise ValueError(f"ResourceAgent 不支持任务类型: {task_type}")

    async def generate_questions(
        self,
        topic: str,
        knowledge_ids: Optional[List[int]] = None,
        difficulty: str = "medium",
        count: int = 5,
        question_type: str = "mixed",
        student_profile: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """生成练习题"""
        context = ""
        if "knowledge_retrieval" in self.tools:
            try:
                results = await self.call_tool(
                    "knowledge_retrieval",
                    query=topic,
                    knowledge_ids=knowledge_ids,
                    top_k=5,
                )
                context = "\n\n".join(r["content"] for r in results)
            except Exception as e:
                logger.warning("知识检索失败: %s", e)

        prompt = f"""请为以下主题生成 {count} 道练习题。

主题: {topic}
难度: {difficulty}
题型: {question_type}

参考知识:
{context if context else "（无参考知识）"}

请输出 JSON:
{{
  "topic": "{topic}",
  "questions": [
    {{
      "type": "choice|fill|short_answer",
      "difficulty": "easy|medium|hard",
      "question": "题目内容",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "answer": "正确答案",
      "explanation": "解析"
    }}
  ]
}}"""

        response = await self.chat(prompt)
        return parse_llm_json(response, fallback={"topic": topic, "questions": []})

    async def generate_mindmap(
        self,
        topic: str,
        knowledge_ids: Optional[List[int]] = None,
        student_profile: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """生成思维导图"""
        context = ""
        if "knowledge_retrieval" in self.tools:
            try:
                results = await self.call_tool(
                    "knowledge_retrieval",
                    query=topic,
                    knowledge_ids=knowledge_ids,
                    top_k=5,
                )
                context = "\n\n".join(r["content"] for r in results)
            except Exception as e:
                logger.warning("知识检索失败: %s", e)

        prompt = f"""请为以下主题生成思维导图结构。

主题: {topic}

参考知识:
{context if context else "（无参考知识）"}

请输出 JSON:
{{
  "topic": "{topic}",
  "children": [
    {{
      "name": "子主题",
      "children": [
        {{"name": "要点", "children": []}}
      ]
    }}
  ]
}}"""

        response = await self.chat(prompt)
        return parse_llm_json(response, fallback={"topic": topic, "children": []})

    async def generate_summary(
        self,
        topic: str,
        knowledge_ids: Optional[List[int]] = None,
        student_profile: Dict[str, Any] | None = None,
    ) -> Dict[str, str]:
        """生成学习摘要"""
        context = ""
        if "knowledge_retrieval" in self.tools:
            try:
                results = await self.call_tool(
                    "knowledge_retrieval",
                    query=topic,
                    knowledge_ids=knowledge_ids,
                    top_k=5,
                )
                context = "\n\n".join(r["content"] for r in results)
            except Exception as e:
                logger.warning("知识检索失败: %s", e)

        prompt = f"""请为以下主题生成简洁的学习摘要。

主题: {topic}

参考知识:
{context if context else "（无参考知识）"}

要求:
- 300字以内
- 突出核心概念和关键点
- 适合学生快速复习"""

        response = await self.chat(prompt)
        return {"topic": topic, "summary": response}
