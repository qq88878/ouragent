"""学生画像分析 Agent - 分析学生学习特征和薄弱点"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .base import BaseAgent
from ..utils import parse_llm_json

logger = logging.getLogger(__name__)


class ProfileAgent(BaseAgent):
    """
    学生画像分析 Agent

    职责：
    - 分析学生的学习历史和对话记录
    - 推断学习风格（视觉/听觉/阅读/动手）
    - 识别知识薄弱点和优势领域
    - 生成结构化的学生画像
    """

    name = "profile_agent"
    description = "分析学生学习特征、识别薄弱点、生成学习画像"

    # 支持的任务类型
    TASK_ANALYZE = "analyze"

    @property
    def system_prompt(self) -> str:
        return """你是一位教育心理学专家，专注于学习者画像分析。

你的任务是根据学生的学习记录、对话历史和考试表现，分析出:
1. 学习风格偏好（visual/auditory/reading/kinesthetic）
2. 知识掌握情况（强项和薄弱点）
3. 学习兴趣方向
4. 适合的学习策略（要考虑学历阶段和专业特点）

输出必须是结构化的 JSON 格式。"""

    async def execute(self, task_type: str, **kwargs) -> Dict[str, Any]:
        """
        统一任务执行接口

        Args:
            task_type: "analyze"
            **kwargs: analyze(chat_history, study_records, current_profile)
        """
        if task_type == self.TASK_ANALYZE:
            return await self.analyze(
                chat_history=kwargs.get("chat_history", []),
                study_records=kwargs.get("study_records", []),
                current_profile=kwargs.get("current_profile"),
            )
        else:
            raise ValueError(f"ProfileAgent 不支持任务类型: {task_type}")

    async def analyze(
        self,
        chat_history: List[Dict[str, str]],
        study_records: List[Dict[str, Any]],
        current_profile: Optional[Dict[str, Any]] = None,
        education_level: Optional[str] = None,
        major: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        分析学生并生成/更新画像

        Args:
            chat_history: 聊天记录
            study_records: 学习记录
            current_profile: 现有画像（增量更新）

        Returns:
            结构化画像 JSON
        """
        history_text = "\n".join(
            f"{m['role']}: {m['content']}" for m in chat_history[-20:]
        )
        records_text = json.dumps(study_records, ensure_ascii=False) if study_records else "暂无学习记录"
        profile_text = json.dumps(current_profile, ensure_ascii=False) if current_profile else "暂无画像"

        # 学历和学科信息
        edu_info = ""
        if education_level:
            level_map = {"PRIMARY": "小学", "JUNIOR": "初中", "SENIOR": "高中", "UNIVERSITY": "大学"}
            edu_info += f"学历阶段: {level_map.get(education_level, education_level)}\n"
        if major:
            if education_level == "UNIVERSITY":
                edu_info += f"大学专业: {major}\n"
            else:
                edu_info += f"感兴趣学科: {major}\n"

        prompt = f"""请分析以下学生信息，生成学习画像。

{edu_info}最近对话记录:
{history_text}

学习记录:
{records_text}

现有画像:
{profile_text}

请输出 JSON 格式:
{{
  "learning_style": "visual|auditory|reading|kinesthetic",
  "strengths": ["强项1", "强项2"],
  "weaknesses": ["薄弱点1", "薄弱点2"],
  "interests": ["兴趣1", "兴趣2"],
  "grade_level": "beginner|intermediate|advanced",
  "recommended_strategy": "建议的学习策略（要考虑学历阶段特点）",
  "education_level": "{education_level or ''}",
  "major": "{major or ''}",
  "confidence": 0.8
}}"""

        response = await self.chat(prompt)
        return parse_llm_json(response, fallback={"confidence": 0})
