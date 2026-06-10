"""题目生成工具 - 基于知识内容生成练习题"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from .base import Tool

logger = logging.getLogger(__name__)


class QuestionGenTool(Tool):
    """
    练习题生成工具

    根据知识点和难度，调用 LLM 生成选择题、填空题、简答题。
    输出结构化的题目 JSON。
    """

    name = "question_generator"
    description = "根据知识点生成练习题（选择题/填空题/简答题）"
    parameters = {
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "知识点主题"},
            "difficulty": {
                "type": "string",
                "enum": ["easy", "medium", "hard"],
                "description": "难度等级",
            },
            "question_type": {
                "type": "string",
                "enum": ["choice", "fill", "short_answer", "mixed"],
                "description": "题目类型，默认 mixed",
            },
            "count": {"type": "integer", "description": "题目数量，默认 5"},
            "context": {"type": "string", "description": "参考知识内容（从知识库检索）"},
        },
        "required": ["topic"],
    }

    def __init__(self, llm):
        self.llm = llm

    async def execute(
        self,
        topic: str,
        difficulty: str = "medium",
        question_type: str = "mixed",
        count: int = 5,
        context: str = "",
        **kwargs,
    ) -> Dict[str, Any]:
        prompt = f"""你是一位专业的教育工作者。请根据以下信息生成练习题。

主题: {topic}
难度: {difficulty}
题目类型: {question_type}
数量: {count}

参考知识:
{context if context else "（无参考知识，请基于你的专业知识生成）"}

请严格按照以下 JSON 格式输出，不要输出其他内容:
{{
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
}}

注意:
- 选择题必须有4个选项
- 填空题答案用 ___ 标记空位
- 简答题给出参考答案和评分要点
"""

        messages = [
            {"role": "system", "content": "你是一个专业的教育题目生成器，只输出JSON格式的题目。"},
            {"role": "user", "content": prompt},
        ]

        try:
            response = await self.llm.chat(messages, temperature=0.7)
            # 尝试解析 JSON
            response = response.strip()
            if response.startswith("```"):
                response = response.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("LLM 返回的题目不是有效 JSON，返回原始文本")
            return {"questions": [], "raw_response": response}
        except Exception as e:
            logger.error("题目生成失败: %s", e)
            return {"questions": [], "error": str(e)}
