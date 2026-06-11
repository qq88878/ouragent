"""
Agent 模块单元测试
使用 mock LLM 测试各 Agent
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.agents.base import BaseAgent
from src.core.agents.profile_agent import ProfileAgent
from src.core.agents.planner_agent import PlannerAgent
from src.core.agents.resource_agent import ResourceAgent
from src.core.agents.evaluator_agent import EvaluatorAgent


# ==================== ProfileAgent 测试 ====================


class TestProfileAgent:
    """学生画像分析 Agent 测试"""

    @pytest.fixture
    def agent(self, mock_llm):
        return ProfileAgent(llm=mock_llm)

    def test_name(self, agent):
        """测试 Agent 名称"""
        assert agent.name == "profile_agent"

    def test_system_prompt(self, agent):
        """测试系统提示词"""
        assert "教育心理学专家" in agent.system_prompt

    @pytest.mark.asyncio
    async def test_analyze(self, agent, mock_llm):
        """测试画像分析"""
        # 设置 LLM 返回
        mock_llm.chat.return_value = json.dumps({
            "learning_style": "visual",
            "strengths": ["循环"],
            "weaknesses": ["递归"],
            "confidence": 0.8,
        })

        result = await agent.analyze(
            chat_history=[{"role": "user", "content": "什么是递归？"}],
            study_records=[{"topic": "递归", "score": 60}],
        )

        assert result["learning_style"] == "visual"
        assert "递归" in result["weaknesses"]

    @pytest.mark.asyncio
    async def test_execute(self, agent, mock_llm):
        """测试统一执行接口"""
        mock_llm.chat.return_value = json.dumps({
            "learning_style": "reading",
            "confidence": 0.9,
        })

        result = await agent.execute(
            "analyze",
            chat_history=[],
            study_records=[],
        )

        assert "learning_style" in result

    @pytest.mark.asyncio
    async def test_execute_invalid_task(self, agent):
        """测试无效任务类型"""
        with pytest.raises(ValueError, match="不支持任务类型"):
            await agent.execute("invalid_task")


# ==================== PlannerAgent 测试 ====================


class TestPlannerAgent:
    """学习规划 Agent 测试"""

    @pytest.fixture
    def agent(self, mock_llm):
        return PlannerAgent(llm=mock_llm)

    def test_name(self, agent):
        assert agent.name == "planner_agent"

    @pytest.mark.asyncio
    async def test_generate_path(self, agent, mock_llm):
        """测试生成学习路径"""
        mock_llm.chat.return_value = json.dumps({
            "title": "Python基础学习路径",
            "total_steps": 3,
            "steps": [
                {"order": 1, "title": "变量与数据类型"},
                {"order": 2, "title": "控制流"},
                {"order": 3, "title": "函数"},
            ],
        })

        result = await agent.generate_path(
            student_profile={"learning_style": "visual"},
            course_title="Python基础",
            course_knowledge=[],
        )

        assert result["title"] == "Python基础学习路径"
        assert len(result["steps"]) == 3

    @pytest.mark.asyncio
    async def test_execute(self, agent, mock_llm):
        """测试统一执行接口"""
        mock_llm.chat.return_value = json.dumps({
            "title": "测试路径",
            "steps": [],
        })

        result = await agent.execute(
            "generate_path",
            student_profile={},
            course_title="测试课程",
        )

        assert "title" in result


# ==================== ResourceAgent 测试 ====================


class TestResourceAgent:
    """资源生成 Agent 测试"""

    @pytest.fixture
    def agent(self, mock_llm):
        return ResourceAgent(llm=mock_llm, tools=[])

    def test_name(self, agent):
        assert agent.name == "resource_agent"

    @pytest.mark.asyncio
    async def test_generate_questions(self, agent, mock_llm):
        """测试生成题目"""
        mock_llm.chat.return_value = json.dumps({
            "topic": "Python列表",
            "questions": [
                {
                    "type": "choice",
                    "question": "如何创建列表？",
                    "options": ["A. []", "B. ()", "C. {}", "D. <>"],
                    "answer": "A",
                }
            ],
        })

        result = await agent.generate_questions(
            topic="Python列表",
            count=1,
        )

        assert result["topic"] == "Python列表"
        assert len(result["questions"]) == 1

    @pytest.mark.asyncio
    async def test_generate_mindmap(self, agent, mock_llm):
        """测试生成思维导图"""
        mock_llm.chat.return_value = json.dumps({
            "topic": "Python数据结构",
            "children": [
                {"name": "列表", "children": []},
                {"name": "元组", "children": []},
            ],
        })

        result = await agent.generate_mindmap(topic="Python数据结构")

        assert result["topic"] == "Python数据结构"
        assert len(result["children"]) == 2

    @pytest.mark.asyncio
    async def test_generate_summary(self, agent, mock_llm):
        """测试生成摘要"""
        mock_llm.chat.return_value = "Python列表是一种有序的数据结构..."

        result = await agent.generate_summary(topic="Python列表")

        assert result["topic"] == "Python列表"
        assert "Python列表" in result["summary"]

    @pytest.mark.asyncio
    async def test_execute_questions(self, agent, mock_llm):
        """测试统一执行接口 - 题目"""
        mock_llm.chat.return_value = json.dumps({
            "topic": "测试",
            "questions": [],
        })

        result = await agent.execute("generate_questions", topic="测试")
        assert "questions" in result

    @pytest.mark.asyncio
    async def test_execute_mindmap(self, agent, mock_llm):
        """测试统一执行接口 - 思维导图"""
        mock_llm.chat.return_value = json.dumps({
            "topic": "测试",
            "children": [],
        })

        result = await agent.execute("generate_mindmap", topic="测试")
        assert "children" in result

    @pytest.mark.asyncio
    async def test_execute_summary(self, agent, mock_llm):
        """测试统一执行接口 - 摘要"""
        mock_llm.chat.return_value = "测试摘要"

        result = await agent.execute("generate_summary", topic="测试")
        assert "summary" in result


# ==================== EvaluatorAgent 测试 ====================


class TestEvaluatorAgent:
    """评估 Agent 测试"""

    @pytest.fixture
    def agent(self, mock_llm):
        return EvaluatorAgent(llm=mock_llm)

    def test_name(self, agent):
        assert agent.name == "evaluator_agent"

    @pytest.mark.asyncio
    async def test_evaluate_answer(self, agent, mock_llm):
        """测试评估答案"""
        mock_llm.chat.return_value = json.dumps({
            "score": 85,
            "is_correct": True,
            "completeness": "partial",
            "suggestions": ["可以更详细"],
        })

        result = await agent.evaluate_answer(
            question="什么是Python列表？",
            student_answer="Python列表是一种数据结构",
        )

        assert result["score"] == 85
        assert result["is_correct"] == True

    @pytest.mark.asyncio
    async def test_assess_progress(self, agent, mock_llm):
        """测试评估进度"""
        mock_llm.chat.return_value = json.dumps({
            "overall_progress": "improving",
            "mastery_level": "intermediate",
            "recommendations": ["继续练习"],
        })

        result = await agent.assess_progress(
            student_id="123",
            recent_records=[],
            current_profile={},
        )

        assert result["overall_progress"] == "improving"

    @pytest.mark.asyncio
    async def test_execute_evaluate(self, agent, mock_llm):
        """测试统一执行接口 - 评估"""
        mock_llm.chat.return_value = json.dumps({
            "score": 90,
            "is_correct": True,
        })

        result = await agent.execute(
            "evaluate_answer",
            question="测试",
            student_answer="回答",
        )

        assert "score" in result

    @pytest.mark.asyncio
    async def test_execute_assess(self, agent, mock_llm):
        """测试统一执行接口 - 进度评估"""
        mock_llm.chat.return_value = json.dumps({
            "overall_progress": "stable",
        })

        result = await agent.execute(
            "assess_progress",
            student_id="123",
            recent_records=[],
            current_profile={},
        )

        assert "overall_progress" in result


# ==================== BaseAgent 测试 ====================


class TestBaseAgent:
    """Agent 基类测试"""

    def test_abstract_execute(self):
        """测试 execute 是抽象方法"""
        # 不能直接实例化 BaseAgent
        with pytest.raises(TypeError):
            BaseAgent(llm=MagicMock())

    @pytest.mark.asyncio
    async def test_chat(self, mock_llm):
        """测试 chat 方法"""
        mock_llm.chat.return_value = "测试回复"

        # 创建一个具体子类
        class TestAgent(BaseAgent):
            name = "test"
            async def execute(self, task_type, **kwargs):
                return {}

        agent = TestAgent(llm=mock_llm)
        response = await agent.chat("测试消息")

        assert response == "测试回复"
        mock_llm.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_context(self, mock_llm):
        """测试带上下文的 chat"""
        mock_llm.chat.return_value = "回复"

        class TestAgent(BaseAgent):
            name = "test"
            async def execute(self, task_type, **kwargs):
                return {}

        agent = TestAgent(llm=mock_llm)
        await agent.chat("消息", context="知识上下文")

        # 验证消息包含上下文
        call_args = mock_llm.chat.call_args[0][0]
        assert any("知识上下文" in msg["content"] for msg in call_args)

    def test_get_info(self, mock_llm):
        """测试 get_info"""

        class TestAgent(BaseAgent):
            name = "test"
            description = "测试Agent"
            async def execute(self, task_type, **kwargs):
                return {}

        agent = TestAgent(llm=mock_llm)
        info = agent.get_info()

        assert info["name"] == "test"
        assert info["description"] == "测试Agent"
