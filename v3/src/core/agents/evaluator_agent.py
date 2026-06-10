"""学习评估 Agent - 评估学习效果和答题质量"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from .base import BaseAgent

logger = logging.getLogger(__name__)


class EvaluatorAgent(BaseAgent):
    """
    学习评估 Agent

    职责：
    - 评估学生回答的正确性和质量
    - 提供详细的反馈和改进建议
    - 跟踪学习进度
    - 识别需要加强的知识点
    """

    name = "evaluator_agent"
    description = "评估学习效果、批改答案、提供反馈"

    @property
    def system_prompt(self) -> str:
        return """你是一位严格的教育评估专家。

你的任务:
1. 客观评估学生的回答
2. 指出错误并解释原因
3. 给出改进建议
4. 鼓励正确的地方，温和纠正错误

评估标准:
- 完整性：是否覆盖了所有要点
- 准确性：概念是否正确
- 逻辑性：推理是否合理
- 表达：是否清晰"""

    async def evaluate_answer(
        self,
        question: str,
        student_answer: str,
        reference_answer: str = "",
        knowledge_context: str = "",
    ) -> Dict[str, Any]:
        """
        评估学生答案

        Args:
            question: 题目
            student_answer: 学生回答
            reference_answer: 参考答案（可选）
            knowledge_context: 相关知识上下文（可选）

        Returns:
            评估结果 JSON
        """
        prompt = f"""请评估以下学生回答。

题目: {question}
学生回答: {student_answer}
参考答案: {reference_answer if reference_answer else "无"}
相关知识: {knowledge_context if knowledge_context else "无"}

请输出 JSON:
{{
  "score": 0-100,
  "is_correct": true/false,
  "completeness": "complete|partial|missing",
  "correct_points": ["正确的地方"],
  "errors": ["错误之处"],
  "suggestions": ["改进建议"],
  "encouragement": "鼓励性评语",
  "related_knowledge": ["涉及的知识点"]
}}"""

        response = await self.chat(prompt)
        try:
            response = response.strip()
            if response.startswith("```"):
                response = response.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(response)
        except json.JSONDecodeError:
            return {"score": 0, "raw_response": response}

    async def assess_progress(
        self,
        student_id: str,
        recent_records: List[Dict[str, Any]],
        current_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        评估学习进度

        Args:
            student_id: 学生 ID
            recent_records: 最近的学习记录
            current_profile: 当前画像

        Returns:
            进度评估 JSON
        """
        records_text = json.dumps(recent_records, ensure_ascii=False)
        profile_text = json.dumps(current_profile, ensure_ascii=False)

        prompt = f"""请评估该学生的学习进度。

最近学习记录:
{records_text}

当前画像:
{profile_text}

请输出 JSON:
{{
  "overall_progress": "improving|stable|declining",
  "mastery_level": "beginner|intermediate|advanced",
  "strong_areas": ["进步明显的领域"],
  "weak_areas": ["需要加强的领域"],
  "recommendations": ["具体建议"],
  "motivation_tip": "激励语"
}}"""

        response = await self.chat(prompt)
        try:
            response = response.strip()
            if response.startswith("```"):
                response = response.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(response)
        except json.JSONDecodeError:
            return {"overall_progress": "unknown", "raw_response": response}
