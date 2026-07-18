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

        prompt = f"""你是教育规划专家。为课程"{course_title}"生成个性化学习路径。
{f"课程描述: {course_description}\n" if course_description else ""}目标: {goal}
学生画像: {profile_summary}
知识库: {knowledge_summary}
{f"课表: {schedule_text}\n" if schedule_text else ""}
要求: 分3-5阶段(phases),每阶段3-8步,共15-30步。每阶段末至少1步设is_checkpoint=true。
每步必含:order,title,description(含学什么/怎么学/学到什么程度,200字以上),knowledge_ids(知识库id数组),key_points(3-5个要点),estimated_hours(概念0.5-1h,练习1-2h,复习1-2h,项目2-3h),resources(推荐资源数组),milestone(is_checkpoint=true时必填),is_checkpoint。
输出纯JSON(不要markdown代码块,不要额外文字):
{{"title":"路径标题","description":"概述(200字)","phases":[{{"phase_name":"阶段名","phase_goal":"目标","phase_order":1,"steps":[{{"order":1,"title":"步骤","description":"详细描述","knowledge_ids":[1],"key_points":["要点1"],"estimated_hours":0.5,"resources":["资源"],"milestone":"里程碑","is_checkpoint":false}}]}}],"total_estimated_hours":30}}"""

        response = await self.chat(prompt, max_tokens=8192)
        return parse_llm_json(response, fallback={"title": course_title, "steps": []})

    def _build_profile_summary(self, profile: Dict[str, Any]) -> str:
        """Convert profile dict to readable text, supports enriched profile"""
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

        level = profile.get("gradeLevel") or profile.get("grade_level", "")
        if not level:
            level = profile.get("estimated_course_level", "")
        if level:
            parts.append(f"当前水平: {level}")

        pace = profile.get("recommended_pace", "")
        if pace:
            pace_map = {"slow": "慢速细致", "moderate": "正常进度", "fast": "快速推进"}
            parts.append(f"推荐学习节奏: {pace_map.get(pace, pace)}")

        course_strengths = profile.get("course_specific_strengths", [])
        if course_strengths:
            parts.append(f"本课程已掌握: {', '.join(course_strengths)}")

        course_weaknesses = profile.get("course_specific_weaknesses", [])
        if course_weaknesses:
            parts.append(f"本课程薄弱点: {', '.join(course_weaknesses)}")

        gaps = profile.get("knowledge_gaps", [])
        if gaps:
            parts.append(f"知识盲区: {', '.join(gaps)}")

        interests = profile.get("topic_interests") or profile.get("interests", "")
        if interests:
            if isinstance(interests, list):
                parts.append(f"兴趣主题: {', '.join(interests)}")
            else:
                parts.append(f"兴趣: {interests}")

        if not course_strengths:
            strengths = profile.get("strengths", "")
            if strengths:
                parts.append(f"优势: {strengths}")
        if not course_weaknesses:
            weaknesses = profile.get("weaknesses", "")
            if weaknesses:
                parts.append(f"薄弱点: {weaknesses}")

        strategy = profile.get("recommended_strategy", "")
        if strategy:
            parts.append(f"学习策略: {strategy}")

        attention = profile.get("attention_points", [])
        if attention:
            parts.append(f"重点关注: {', '.join(attention)}")

        pref_resources = profile.get("preferred_resource_types", [])
        if pref_resources:
            parts.append(f"偏好资源: {', '.join(pref_resources)}")

        return "\n".join(parts) if parts else "暂无画像数据"
    def _build_knowledge_summary(self, knowledge: List[Dict[str, Any]]) -> str:
        """将知识库条目转为可读文本"""
        if not knowledge:
            return "暂无知识库内容"

        lines = []
        total_len = 0
        max_len = 8000  # 支持更多内容

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
