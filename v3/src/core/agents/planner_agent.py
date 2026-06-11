"""学习规划 Agent - 生成个性化学习路径"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from .base import BaseAgent

logger = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    """
    学习规划 Agent

    职责：
    - 根据学生画像和课程目标生成个性化学习路径
    - 将大目标拆解为可执行的小步骤
    - 合理安排学习顺序（由浅入深）
    - 推荐每个步骤的学习资源
    """

    name = "planner_agent"
    description = "生成个性化学习路径和学习计划"

    # 支持的任务类型
    TASK_GENERATE_PATH = "generate_path"

    @property
    def system_prompt(self) -> str:
        return """你是一位教育规划专家，擅长制定个性化学习计划。

你的原则:
1. 由浅入深，循序渐进
2. 根据学生画像调整侧重点
3. 每个步骤必须可执行、可衡量
4. 合理分配学习时间
5. 设置阶段性检查点

输出必须是结构化的 JSON 格式。"""

    async def execute(self, task_type: str, **kwargs) -> Dict[str, Any]:
        """
        统一任务执行接口

        Args:
            task_type: "generate_path"
            **kwargs: generate_path(student_profile, course_title, course_knowledge, goal)
        """
        if task_type == self.TASK_GENERATE_PATH:
            return await self.generate_path(
                student_profile=kwargs.get("student_profile", {}),
                course_title=kwargs.get("course_title", ""),
                course_knowledge=kwargs.get("course_knowledge", []),
                goal=kwargs.get("goal", "掌握课程核心知识"),
            )
        else:
            raise ValueError(f"PlannerAgent 不支持任务类型: {task_type}")

    async def generate_path(
        self,
        student_profile: Dict[str, Any],
        course_title: str,
        course_knowledge: List[Dict[str, Any]],
        goal: str = "掌握课程核心知识",
    ) -> Dict[str, Any]:
        """
        生成学习路径

        Args:
            student_profile: 学生画像
            course_title: 课程名称
            course_knowledge: 课程知识条目列表
            goal: 学习目标

        Returns:
            学习路径 JSON
        """
        profile_text = json.dumps(student_profile, ensure_ascii=False)
        knowledge_text = json.dumps(course_knowledge, ensure_ascii=False)

        prompt = f"""请为以下学生生成个性化学习路径。

课程: {course_title}
学习目标: {goal}
学生画像: {profile_text}
课程知识列表: {knowledge_text}

请输出 JSON 格式:
{{
  "title": "学习路径标题",
  "description": "路径概述",
  "total_steps": 步骤数,
  "estimated_total_hours": 预计总学时,
  "steps": [
    {{
      "order": 1,
      "title": "步骤标题",
      "description": "具体学习内容和方法",
      "knowledge_ids": [关联的知识库ID],
      "estimated_hours": 预计学时,
      "checkpoint": "该阶段的检验方式"
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
            logger.warning("学习路径生成结果不是有效 JSON")
            return {"title": course_title, "steps": [], "raw_response": response}
