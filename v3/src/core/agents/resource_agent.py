"""教学资源生成 Agent - 生成题目、思维导图、学习资料"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from .base import BaseAgent
from ..tools.retrieval import RetrievalTool

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

    @property
    def system_prompt(self) -> str:
        return """你是一位资深教育内容创作者。

你的任务是基于知识库内容生成高质量的教学资源:
1. 练习题：覆盖核心知识点，难度适中，有详细解析
2. 思维导图：结构清晰，层次分明
3. 学习摘要：简洁易懂，突出重点

所有内容必须基于提供的知识库，不要编造。"""

    async def generate_questions(
        self,
        topic: str,
        knowledge_ids: Optional[List[int]] = None,
        difficulty: str = "medium",
        count: int = 5,
        question_type: str = "mixed",
    ) -> Dict[str, Any]:
        """生成练习题"""
        # 先从知识库检索相关内容
        context = ""
        if "knowledge_retrieval" in self.tools:
            results = await self.call_tool(
                "knowledge_retrieval",
                query=topic,
                knowledge_ids=knowledge_ids,
                top_k=5,
            )
            context = "\n\n".join(r["content"] for r in results)

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
        try:
            response = response.strip()
            if response.startswith("```"):
                response = response.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(response)
        except json.JSONDecodeError:
            return {"topic": topic, "questions": [], "raw_response": response}

    async def generate_mindmap(
        self,
        topic: str,
        knowledge_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """生成思维导图"""
        context = ""
        if "knowledge_retrieval" in self.tools:
            results = await self.call_tool(
                "knowledge_retrieval",
                query=topic,
                knowledge_ids=knowledge_ids,
                top_k=5,
            )
            context = "\n\n".join(r["content"] for r in results)

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
        try:
            response = response.strip()
            if response.startswith("```"):
                response = response.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(response)
        except json.JSONDecodeError:
            return {"topic": topic, "children": [], "raw_response": response}

    async def generate_summary(
        self,
        topic: str,
        knowledge_ids: Optional[List[int]] = None,
    ) -> Dict[str, str]:
        """生成学习摘要"""
        context = ""
        if "knowledge_retrieval" in self.tools:
            results = await self.call_tool(
                "knowledge_retrieval",
                query=topic,
                knowledge_ids=knowledge_ids,
                top_k=5,
            )
            context = "\n\n".join(r["content"] for r in results)

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
