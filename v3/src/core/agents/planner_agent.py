"""学习规划 Agent - 生成个性化学习路径"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from .base import BaseAgent
from ..utils import parse_llm_json

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
        return """你是一位经验丰富的教育规划专家，擅长制定个性化学习计划。

你的原则:
1. 由浅入深，循序渐进，先打基础再进阶
2. 根据学生画像调整侧重点和学习方式
3. 每个步骤必须详细列出需要掌握的具体知识点（3-5个知识点）
4. 每个知识点要有明确的说明：是什么、为什么重要、怎么学
5. 合理分配学习时间，给出可执行的学习建议
6. 设置阶段性检查点，让学生知道何时算"学会了"
7. 每个步骤必须关联知识库条目，指导学生按知识库内容学习
8. 在 description 中详细说明学什么、怎么学、学到什么程度

输出必须是结构化的 JSON 格式，不要输出其他文字。"""

    async def execute(self, task_type: str, **kwargs) -> Dict[str, Any]:
        """
        统一任务执行接口

        Args:
            task_type: "generate_path"
            **kwargs: generate_path(student_profile, course_title, course_description, course_knowledge, goal, schedule)
        """
        if task_type == self.TASK_GENERATE_PATH:
            return await self.generate_path(
                student_profile=kwargs.get("student_profile", {}),
                course_title=kwargs.get("course_title", ""),
                course_description=kwargs.get("course_description", ""),
                course_knowledge=kwargs.get("course_knowledge", []),
                goal=kwargs.get("goal", "掌握课程核心知识"),
                schedule=kwargs.get("schedule"),
            )
        else:
            raise ValueError(f"PlannerAgent 不支持任务类型: {task_type}")

    async def generate_path(
        self,
        student_profile: Dict[str, Any],
        course_title: str,
        course_knowledge: List[Dict[str, Any]],
        course_description: str = "",
        goal: str = "掌握课程核心知识",
        schedule: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        生成学习路径

        Args:
            student_profile: 学生画像
            course_title: 课程名称
            course_description: 课程描述
            course_knowledge: 课程知识条目列表（含 content 字段）
            goal: 学习目标
            schedule: 课表信息

        Returns:
            学习路径 JSON
        """
        # 构建画像摘要
        profile_summary = self._build_profile_summary(student_profile)

        # 构建知识库摘要（更大的限制）
        knowledge_summary = self._build_knowledge_summary(course_knowledge)

        # 构建课表摘要
        schedule_text = ""
        if schedule:
            lines = []
            for day, courses in schedule.items():
                lines.append(f"  {day}: {', '.join(courses)}")
            schedule_text = "\n".join(lines)

        prompt = f"""请为以下学生生成一份详细的、个性化的学习路径方案。

【课程名称】{course_title}
{f"【课程简介】{course_description}" if course_description else ""}
【学习目标】{goal}

【学生画像】
{profile_summary}

【知识库资料】
以下是课程关联的知识库内容，请基于这些内容规划学习路径：
{knowledge_summary}

{"【课表安排】" + chr(10) + schedule_text + chr(10) if schedule_text else ""}要求：
1. 生成 4-6 个学习步骤，由浅入深，循序渐进
2. 每个步骤的 title 要简洁明了（如"第一章：Python基础语法"）
3. 每个步骤的 description 必须详细说明：
   - 本步骤要学什么具体内容（列出 3-5 个具体知识点）
   - 每个知识点要说明：是什么、为什么重要、怎么学
   - 学到什么程度算掌握（给出可衡量的标准）
   - 推荐的学习方法和技巧
4. 每个步骤必须关联 knowledge_ids（从知识库中选取最相关的）
5. 根据学生画像调整学习方式：
   - 视觉型 → 多推荐图表、思维导图、视频
   - 听觉型 → 多推荐讲解视频、讨论
   - 阅读型 → 多推荐文档、书籍
   - 动手型 → 多推荐编程练习、项目实战
6. estimated_hours 要合理（基础步骤 2-3h，进阶步骤 3-5h）
7. 每个步骤的 resources 要推荐具体的学习资源（如"知识库中的XX文档"、"官方文档"等）
8. 如果有课表信息，合理安排学习节奏

只输出 JSON，格式：
{{
  "title": "学习路径标题（要具体，如'Python从入门到实战学习路径'）",
  "description": "路径概述（说明整体规划思路、为什么这样安排、适合什么样的学生）",
  "knowledge_points_summary": "本课程需要掌握的核心知识点总结（200字左右，概括全貌）",
  "steps": [
    {{
      "order": 1,
      "title": "步骤标题",
      "description": "详细说明（至少200字）：要学什么、怎么学、学到什么程度",
      "knowledge_ids": [1, 2],
      "key_points": ["知识点1: 简要说明", "知识点2: 简要说明", "知识点3: 简要说明"],
      "estimated_hours": 2,
      "resources": ["推荐资源1", "推荐资源2"],
      "milestone": "完成标志（如：能独立完成XX练习）"
    }}
  ]
}}"""

        response = await self.chat(prompt, max_tokens=4096)
        return parse_llm_json(response, fallback={"title": course_title, "steps": []})

    def _build_profile_summary(self, profile: Dict[str, Any]) -> str:
        """将画像字典转为可读文本"""
        if not profile:
            return "暂无画像数据"

        parts = []
        style = profile.get("learningStyle") or profile.get("learning_style", "")
        if style:
            style_map = {
                "VISUAL": "视觉型（喜欢图表、思维导图）",
                "AUDITORY": "听觉型（喜欢听讲、讨论）",
                "READING": "阅读型（喜欢文字材料）",
                "KINESTHETIC": "动手型（喜欢实践操作）",
            }
            parts.append(f"学习风格: {style_map.get(style, style)}")

        strengths = profile.get("strengths", "")
        if strengths:
            parts.append(f"优势: {strengths}")

        weaknesses = profile.get("weaknesses", "")
        if weaknesses:
            parts.append(f"薄弱点: {weaknesses}")

        interests = profile.get("interests", "")
        if interests:
            parts.append(f"兴趣: {interests}")

        grade = profile.get("gradeLevel") or profile.get("grade_level", "")
        if grade:
            parts.append(f"年级: {grade}")

        return "\n".join(parts) if parts else "暂无画像数据"

    def _build_knowledge_summary(self, knowledge: List[Dict[str, Any]]) -> str:
        """将知识库条目转为可读文本"""
        if not knowledge:
            return "暂无知识库内容"

        lines = []
        total_len = 0
        max_len = 6000  # 支持更多内容

        for item in knowledge:
            kid = item.get("id", "?")
            title = item.get("title", "未知")
            desc = item.get("description", "")
            content = item.get("content", "")

            line = f"[知识库id={kid}] {title}"
            if desc:
                line += f" — {desc}"
            if content:
                snippet = content[:500] + ("..." if len(content) > 500 else "")
                line += f"\n      内容: {snippet}"

            if total_len + len(line) > max_len:
                lines.append(f"  ... 还有 {len(knowledge) - len(lines)} 个条目（已省略）")
                break
            lines.append(f"  {line}")
            total_len += len(line)

        return "\n".join(lines)
