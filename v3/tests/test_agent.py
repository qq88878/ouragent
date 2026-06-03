"""
Agent测试模块
测试Agent核心功能
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from v3.src.core.agent import Agent
from v3.src.core.tools import Tool


# ==================== 阶段一: 基础框架测试 ====================

class TestAgentBasic:
    """Agent基础功能测试 (阶段一即可通过)"""

    def test_agent_creation(self):
        agent = Agent(name="TestAgent", description="test")
        assert agent.name == "TestAgent"
        assert agent.id is not None

    def test_agent_id_unique(self):
        agent1 = Agent(name="A1")
        agent2 = Agent(name="A2")
        assert agent1.id != agent2.id

    def test_agent_chat_returns_string(self):
        agent = Agent()
        response = agent.chat("Hello")
        assert isinstance(response, str)
        assert len(response) > 0

    def test_agent_memory_records_messages(self):
        agent = Agent()
        agent.chat("msg1")
        agent.chat("msg2")
        history = agent.get_conversation_history()
        assert len(history) == 4  # 2 user + 2 assistant

    def test_agent_clear_memory(self):
        agent = Agent()
        agent.chat("test")
        agent.clear_memory()
        assert len(agent.get_conversation_history()) == 0

    def test_agent_status(self):
        agent = Agent(name="Test")
        status = agent.get_status()
        assert "id" in status
        assert "name" in status
        assert status["name"] == "Test"


# ==================== 阶段二: LLM集成测试 ====================

class TestAgentLLM:
    """
    LLM集成测试

    TODO: 阶段二 - 实现
      - test_chat_calls_llm: 验证chat()调用了LLM API
      - test_chat_with_system_prompt: 验证系统提示正确传递
      - test_chat_error_handling: LLM调用失败时的降级处理
      - test_chat_streaming: 流式响应测试
    """

    @pytest.mark.skip(reason="TODO: 阶段二 - LLM集成后启用")
    def test_chat_calls_llm(self):
        pass

    @pytest.mark.skip(reason="TODO: 阶段二 - LLM集成后启用")
    def test_chat_error_handling(self):
        pass


# ==================== 阶段三: 工具调用测试 ====================

class TestAgentToolCalling:
    """
    工具调用测试

    TODO: 阶段三 - 实现
      - test_agent_registers_tools: 验证工具注册
      - test_agent_calls_calculator: 验证计算器工具调用
      - test_agent_calls_search: 验证搜索工具调用
      - test_agent_tool_error_handling: 工具执行失败时的处理
      - test_agent_multi_step_tool: 多步工具调用链
    """

    @pytest.mark.skip(reason="TODO: 阶段三 - 工具实现后启用")
    def test_agent_registers_tools(self):
        pass

    @pytest.mark.skip(reason="TODO: 阶段三 - 工具实现后启用")
    def test_agent_calls_calculator(self):
        pass


# ==================== 记忆模块测试 ====================

class TestMemory:
    """记忆模块测试 (阶段一即可通过)"""

    def test_memory_initialization(self):
        agent = Agent(memory_size=50)
        assert agent.memory is not None
        assert len(agent.memory) == 0

    def test_memory_limit(self):
        agent = Agent(memory_size=5)
        for i in range(10):
            agent.chat(f"msg {i}")
        assert len(agent.memory) == 10

    def test_memory_context_window(self):
        agent = Agent()
        for i in range(10):
            agent.chat(f"msg {i}")
        context = agent.memory.get_context_window(window_size=5)
        assert len(context) == 5
