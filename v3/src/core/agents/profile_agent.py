"""学生画像分析 Agent — 两层画像：基础画像（问卷→持久化） + 课程画像（对话→不持久化）"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from .base import BaseAgent
from ..utils import parse_llm_json

logger = logging.getLogger(__name__)


class ProfileAgent(BaseAgent):
    """学生画像分析 Agent — 两层画像架构"""

    name = "profile_agent"
    description = "分析学生学习特征、识别薄弱点、生成学习画像"

    TASK_ANALYZE_BASIC = "analyze_basic"
    TASK_ANALYZE_COURSE = "analyze_course"
    TASK_ANALYZE_DIMENSIONS = "analyze_dimensions"
    TASK_UPDATE_FROM_ACTIVITY = "update_from_activity"
    TASK_ENRICH_FOR_PATH = "enrich_for_path"

    @property
    def system_prompt(self) -> str:
        return """你是一位教育心理学专家，专注于学习者画像分析。

你的任务是根据学生的问卷数据和对话历史，分析出:
1. 学习风格偏好（visual/auditory/reading/kinesthetic）
2. 知识掌握情况（强项和薄弱点）
3. 学习兴趣方向
4. 适合的学习策略

输出必须是结构化的 JSON 格式。"""

    async def execute(self, task_type: str, **kwargs) -> Dict[str, Any]:
        if task_type == self.TASK_ANALYZE_BASIC:
            return await self.analyze_basic_profile(
                questionnaire_data=kwargs.get("questionnaire_data", {}),
            )
        elif task_type == self.TASK_ANALYZE_COURSE:
            return await self.analyze_course_profile(
                basic_profile=kwargs.get("basic_profile", {}),
                chat_history=kwargs.get("chat_history", []),
                study_records=kwargs.get("study_records", []),
            )
        elif task_type == self.TASK_ANALYZE_DIMENSIONS:
            return await self.analyze_dimensions(
                basic_profile=kwargs.get("basic_profile", {}),
                study_records=kwargs.get("study_records", []),
                evaluation_history=kwargs.get("evaluation_history", []),
                chat_signals=kwargs.get("chat_signals", {}),
                learning_path_progress=kwargs.get("learning_path_progress", {}),
            )
        elif task_type == self.TASK_UPDATE_FROM_ACTIVITY:
            return await self.update_profile_from_activity(
                current_profile=kwargs.get("current_profile", {}),
                new_signals=kwargs.get("new_signals", {}),
                evaluation_results=kwargs.get("evaluation_results", []),
            )
        elif task_type == self.TASK_ENRICH_FOR_PATH:
            return await self.enrich_for_path_generation(
                basic_profile=kwargs.get("basic_profile", {}),
                course_title=kwargs.get("course_title", ""),
                course_description=kwargs.get("course_description", ""),
                chat_signals=kwargs.get("chat_signals", {}),
                study_records=kwargs.get("study_records", []),
                evaluation_history=kwargs.get("evaluation_history", []),
                prior_paths=kwargs.get("prior_paths", []),
                knowledge_context=kwargs.get("knowledge_context", ""),
            )
        else:
            raise ValueError(f"ProfileAgent 不支持任务类型: {task_type}")

    # ==================== 基础画像（简洁问卷 → LLM → 持久化） ====================

    async def analyze_basic_profile(
        self,
        questionnaire_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """从 6 字段简洁问卷生成基础画像（持久化，跨课程共享）"""
        edu_level = questionnaire_data.get("education_level", "")
        major = questionnaire_data.get("major_direction", "")
        goals = questionnaire_data.get("learning_goals", [])
        methods = questionnaire_data.get("learning_methods", [])
        strengths = questionnaire_data.get("self_strengths", [])
        weaknesses = questionnaire_data.get("self_weaknesses", [])

        level_map = {
            "HIGH_SCHOOL": "高中", "ASSOCIATE": "大专", "BACHELOR": "本科",
            "MASTER": "硕士", "PHD": "博士", "OTHER": "其他"
        }
        goal_map = {
            "EXAM": "应对考试", "POSTGRADUATE": "考研升学",
            "EMPLOYMENT": "求职就业", "SELF_IMPROVEMENT": "自我提升"
        }
        method_map = {
            "VIDEO": "看视频", "READING": "读文档/教材",
            "DISCUSSION": "讨论交流", "QUIZ": "刷题练习"
        }
        trait_map = {
            "COMPREHENSION": "理解力", "MEMORY": "记忆力",
            "FOCUS": "专注力", "DISCIPLINE": "自律性", "EXPRESSION": "表达力"
        }

        prompt = f"""请根据以下学生的简洁问卷数据，生成一份基础学习画像。

【基础身份】
- 学历阶段：{level_map.get(edu_level, edu_level)}
- 专业/兴趣方向：{major}

【学习目标】
{', '.join(goal_map.get(g, g) for g in goals) if goals else '未填写'}

【学习风格】
偏好方式：{', '.join(method_map.get(m, m) for m in methods) if methods else '未填写'}

【自我认知】
- 自评优势：{', '.join(trait_map.get(s, s) for s in strengths) if strengths else '未填写'}
- 自评不足：{', '.join(trait_map.get(w, w) for w in weaknesses) if weaknesses else '未填写'}

请基于以上信息推断并输出 JSON 格式的基础画像:
{{
  "learning_style": "VISUAL|AUDITORY|READING|KINESTHETIC",
  "grade_level": "BEGINNER|INTERMEDIATE|ADVANCED",
  "interests": ["兴趣方向1", "兴趣方向2"],
  "strengths": ["推断的优势"],
  "weaknesses": ["推断的薄弱点"],
  "recommended_methods": ["VIDEO", "READING"],
  "recommended_strategy": "个性化学习策略建议（2-3句话）",
  "study_pace": "SLOW|MODERATE|FAST",
  "education_level": "{edu_level}",
  "major": "{major}",
  "confidence": 0.8
}}

注意：
- learning_style 根据学习方式偏好推断（VIDEO→VISUAL, READING→READING, DISCUSSION→AUDITORY, QUIZ→KINESTHETIC）
- recommended_methods 最多 3 个
- study_pace 根据自律性和专注力推断"""

        response = await self.chat(prompt)
        result = parse_llm_json(response, fallback={
            "learning_style": "VISUAL",
            "grade_level": "BEGINNER",
            "interests": [],
            "strengths": [],
            "weaknesses": [],
            "recommended_methods": [],
            "recommended_strategy": "",
            "study_pace": "MODERATE",
            "confidence": 0,
        })
        logger.info("基础画像生成完成: learning_style=%s, grade_level=%s",
                     result.get("learning_style"), result.get("grade_level"))
        return result

    # ==================== 课程画像（基础画像 + 对话历史 → 不持久化） ====================

    async def analyze_course_profile(
        self,
        basic_profile: Dict[str, Any],
        chat_history: List[Dict[str, str]],
        study_records: List[Dict[str, Any]] | None = None,
        knowledge_context: str = "",
        chat_signals: Dict[str, Any] | None = None,
        course_title: str = "",
        course_description: str = "",
    ) -> Dict[str, Any]:
        """结合基础画像、对话历史、知识库上下文，动态构建课程学生画像（不持久化）"""
        if not chat_history:
            return {
                "course_strengths": [],
                "course_weaknesses": [],
                "topics_discussed": [],
                "engagement_level": "UNKNOWN",
                "note": "暂无本课程对话记录",
            }

        history_text = "\n".join(
            f"{m['role']}: {m['content'][:200]}" for m in chat_history[-30:]
        )
        records_text = json.dumps(study_records, ensure_ascii=False) if study_records else "暂无学习记录"
        knowledge_text = knowledge_context[:1000] if knowledge_context else "暂无知识库上下文"
        signals_text = json.dumps(chat_signals or {}, ensure_ascii=False) if chat_signals else "暂无信号"
        profile_text = json.dumps(basic_profile, ensure_ascii=False)

        prompt = f"""【当前课程：{course_title}】\n\n请根据学生的基础画像和本课程的对话历史，生成该课程特有的学生理解。

【基础画像（跨课程共享）】
{profile_text}

【本课程对话历史（最近30条）】
{history_text}

【本课程学习记录】
{records_text}

【课程知识库】
{knowledge_text}

【对话信号】
{signals_text}

请输出 JSON 格式的课程画像:
{{
  "course_strengths": ["本课程中学生表现好的知识点"],
  "course_weaknesses": ["本课程中学生遇到困难的知识点"],
  "topics_discussed": ["已讨论的主题"],
  "engagement_level": "HIGH|MEDIUM|LOW",
  "questions_frequency": "FREQUENT|MODERATE|RARE",
  "summary": "一句话总结该学生在本课程中的表现"
}}

注意：只关注本课程内的表现，不要引入基础画像中已有的通用结论。"""

        response = await self.chat(prompt)
        result = parse_llm_json(response, fallback={
            "course_strengths": [],
            "course_weaknesses": [],
            "topics_discussed": [],
            "engagement_level": "UNKNOWN",
        })
        logger.debug("课程画像构建完成: topics=%d, strengths=%d, weaknesses=%d",
                      len(result.get("topics_discussed", [])),
                      len(result.get("course_strengths", [])),
                      len(result.get("course_weaknesses", [])))
        return result

    # ======================== Dimension Scoring (data-driven for radar chart) ========================

    async def analyze_dimensions(
        self,
        basic_profile: Dict[str, Any],
        study_records: List[Dict[str, Any]],
        evaluation_history: List[Dict[str, Any]],
        chat_signals: Dict[str, Any] | None = None,
        learning_path_progress: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Generate 5-dimension ability scores from learning data"""
        profile_text = json.dumps(basic_profile, ensure_ascii=False)
        records_text = json.dumps(study_records[-20:] if study_records else [], ensure_ascii=False)
        eval_text = json.dumps(evaluation_history[-10:] if evaluation_history else [], ensure_ascii=False)
        signals_text = json.dumps(chat_signals or {}, ensure_ascii=False)
        progress_text = json.dumps(learning_path_progress or {}, ensure_ascii=False)

        prompt = f"""Student Ability Dimension Assessment

Evaluate the student on 5 dimensions (0-100) based on the data below.

[Basic Profile]
{profile_text}

[Study Records (last 20)] 
{records_text}

[Evaluation History (last 10)]
{eval_text}

[Chat Signals]
{signals_text}

[Learning Path Progress]
{progress_text}

Output JSON:
{{
  "dimensions": {{
    "theoretical_knowledge": {{"score": 0-100, "label": "Theory", "description": "reasoning"}},
    "practical_ability": {{"score": 0-100, "label": "Practice", "description": "reasoning"}},
    "problem_solving": {{"score": 0-100, "label": "Problem Solving", "description": "reasoning"}},
    "innovative_thinking": {{"score": 0-100, "label": "Innovation", "description": "reasoning"}},
    "collaboration": {{"score": 0-100, "label": "Collaboration", "description": "reasoning"}}
  }},
  "overall_assessment": "2-3 sentence summary",
  "confidence": 0.0-1.0
}}

Rules: base scores on actual data; use 50 as default when no data."""
        response = await self.chat(prompt)
        result = parse_llm_json(response, fallback={
            "dimensions": {
                "theoretical_knowledge": {"score": 50, "label": "Theory", "description": "No data"},
                "practical_ability": {"score": 50, "label": "Practice", "description": "No data"},
                "problem_solving": {"score": 50, "label": "Problem Solving", "description": "No data"},
                "innovative_thinking": {"score": 50, "label": "Innovation", "description": "No data"},
                "collaboration": {"score": 50, "label": "Collaboration", "description": "No data"},
            },
            "overall_assessment": "",
            "confidence": 0.0,
        })
        logger.info("Dimension analysis complete: confidence=%.2f", result.get("confidence", 0))
        return result

    async def update_profile_from_activity(
        self,
        current_profile: Dict[str, Any],
        new_signals: Dict[str, Any],
        evaluation_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Merge new learning signals into existing profile"""
        signals_text = json.dumps(new_signals, ensure_ascii=False)
        eval_text = json.dumps(evaluation_results, ensure_ascii=False)
        profile_text = json.dumps(current_profile, ensure_ascii=False)

        prompt = f"""Merge new learning signals into the student's profile.

[Current Profile]
{profile_text}

[New Chat Signals]
{signals_text}

[Recent Evaluations]
{eval_text}

Output JSON (only updated fields):
{{
  "learning_style": "current or updated",
  "grade_level": "current or updated",
  "strengths": ["updated strengths"],
  "weaknesses": ["updated weaknesses"],
  "interests": ["updated interests"],
  "recommended_strategy": "updated strategy (optional)",
  "change_summary": "1-2 sentences describing what changed and why",
  "confidence": 0.0-1.0
}}

Rules: only change fields where there is clear evidence. If no change, return current values."""
        response = await self.chat(prompt)
        result = parse_llm_json(response, fallback={
            "learning_style": current_profile.get("learning_style", "VISUAL"),
            "grade_level": current_profile.get("grade_level", "BEGINNER"),
            "strengths": current_profile.get("strengths", []),
            "weaknesses": current_profile.get("weaknesses", []),
            "interests": current_profile.get("interests", []),
            "change_summary": "",
            "confidence": 0.0,
        })
        logger.info("Profile update: change_summary=%s", result.get("change_summary", ""))
        return result

    async def enrich_for_path_generation(
        self,
        basic_profile: Dict[str, Any],
        course_title: str,
        course_description: str = "",
        chat_signals: Dict[str, Any] | None = None,
        study_records: List[Dict[str, Any]] | None = None,
        evaluation_history: List[Dict[str, Any]] | None = None,
        prior_paths: List[Dict[str, Any]] | None = None,
        knowledge_context: str = "",
    ) -> Dict[str, Any]:
        """
        ?????????????????

        ?????? + ?????? + ???? + ???? + ???????
        ???????? PlannerAgent ????????????????????
        """
        profile_text = json.dumps(basic_profile, ensure_ascii=False)
        signals_text = json.dumps(chat_signals or {}, ensure_ascii=False)
        records_text = json.dumps((study_records or [])[-10:], ensure_ascii=False)
        eval_text = json.dumps((evaluation_history or [])[-10:], ensure_ascii=False)
        paths_text = json.dumps((prior_paths or [])[-3:], ensure_ascii=False)
        knowledge_snippet = knowledge_context[:1500] if knowledge_context else "?"

        prompt = f"""????????"{course_title}"?????????????????????????

??????
{profile_text}

?????????
{signals_text}

?????????
{records_text}

?????????
{eval_text}

????????
{paths_text}

???????????
{knowledge_snippet}

??? JSON?
{{
  "learning_style": "VISUAL/AUDITORY/READING/KINESTHETIC",
  "grade_level": "ZERO_BASIC/BEGINNER/INTERMEDIATE/ADVANCED",
  "course_specific_strengths": ["??????????"],
  "course_specific_weaknesses": ["????????"],
  "knowledge_gaps": ["?????????????"],
  "topic_interests": ["??????????"],
  "estimated_course_level": "??/??/??",
  "recommended_pace": "slow/moderate/fast",
  "recommended_strategy": "??????????????????????",
  "attention_points": ["???????????"],
  "preferred_resource_types": ["??/??/??/??"],
  "change_summary": "???????????????????"
}}"""

        response = await self.chat(prompt, max_tokens=2048)
        result = parse_llm_json(response, fallback={
            "learning_style": basic_profile.get("learning_style", "VISUAL"),
            "grade_level": basic_profile.get("grade_level", "BEGINNER"),
            "course_specific_strengths": [],
            "course_specific_weaknesses": [],
            "knowledge_gaps": [],
            "topic_interests": [],
            "estimated_course_level": "??",
            "recommended_pace": "moderate",
            "recommended_strategy": "??????????",
            "attention_points": [],
            "preferred_resource_types": ["??", "??"],
            "change_summary": "",
        })
        logger.info("Path enrichment: course=%s, gaps=%d, style=%s",
                      course_title, len(result.get("knowledge_gaps", [])),
                      result.get("learning_style", ""))
        return result

