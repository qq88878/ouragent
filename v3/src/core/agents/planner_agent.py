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
1. 由浅入深，循序渐进
2. 根据学生画像调整侧重点和学习方式
3. 每个步骤必须可执行、可衡量
4. 合理分配学习时间
5. 设置阶段性检查点
6. 每个步骤必须关联知识库条目，指导学生按知识库内容学习

输出必须是结构化的 JSON 格式，不要输出其他文字。"""

    async def execute(self, task_type: str, **kwargs) -> Dict[str, Any]:
        """
        统一任务执行接口

        Args:
            task_type: "generate_path"
            **kwargs: generate_path(student_profile, course_title, course_knowledge, goal, schedule)
        """
        if task_type == self.TASK_GENERATE_PATH:
            return await self.generate_path(
                student_profile=kwargs.get("student_profile", {}),
                course_title=kwargs.get("course_title", ""),
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
        goal: str = "掌握课程核心知识",
        schedule: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        生成学习路径

        Args:
            student_profile: 学生画像
            course_title: 课程名称
            course_knowledge: 课程知识条目列表（含 content 字段）
            goal: 学习目标
            schedule: 课表信息

        Returns:
            学习路径 JSON
        """
        # 构建画像摘要
        profile_summary = self._build_profile_summary(student_profile)

        # 构建知识库摘要（限制长度避免 token 爆炸）
        knowledge_summary = self._build_knowledge_summary(course_knowledge)

        # 构建课表摘要
        schedule_text = ""
        if schedule:
            lines = []
            for day, courses in schedule.items():
                lines.append(f"  {day}: {', '.join(courses)}")
            schedule_text = "\n".join(lines)

        prompt = f"""请为以下学生生成一份个性化的学习路径。

【课程】{course_title}
【学习目标】{goal}

【学生画像】
{profile_summary}

【知识库内容】
{knowledge_summary}

{"【课表安排】" + chr(10) + schedule_text + chr(10) if schedule_text else ""}要求：
1. 生成 3-5 个学习步骤，由浅入深
2. 每个步骤必须引用知识库中的 knowledge_ids
3. 如果知识库中有具体内容，步骤描述要具体到学什么知识点
4. 根据学生画像调整学习方式（如视觉型多推荐图表，动手型多推荐实践）
5. estimated_hours 要合理（基础步骤 1-2h，进阶步骤 2-4h）
6. 如果有课表信息，避开上课时间密集的日期安排较多学习量

只输出 JSON，格式：
{{"title":"路径标题","description":"概述（说明为什么这样安排）","steps":[{{"order":1,"title":"步骤标题","description":"具体学什么、怎么学","knowledge_ids":[1,2],"estimated_hours":2,"resources":["推荐资源"]}}]}}"""

        response = await self.chat(prompt, max_tokens=2048)
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
        """将知识库条目转为可读文本，限制总长度"""
        if not knowledge:
            return "暂无知识库内容"

        lines = []
        total_len = 0
        max_len = 3000  # 限制知识库摘要总长度

        for item in knowledge:
            kid = item.get("id", "?")
            title = item.get("title", "未知")
            desc = item.get("description", "")
            content = item.get("content", "")

            line = f"[id={kid}] {title}"
            if desc:
                line += f" - {desc}"
            if content:
                # 截取内容摘要
                snippet = content[:200] + ("..." if len(content) > 200 else "")
                line += f"\n    内容摘要: {snippet}"

            if total_len + len(line) > max_len:
                lines.append(f"  ... 还有 {len(knowledge) - len(lines)} 个条目（已省略）")
                break
            lines.append(f"  {line}")
            total_len += len(line)

        return "\n".join(lines)
