"""
Agent测试模块
测试Agent核心功能
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from v3.src import Agent
from v3.src.core.tools import CalculatorTool, SearchTool


@pytest.fixture
def basic_agent():
    """创建基础Agent实例"""
    return Agent(
        name="TestAgent",
        description="A test agent",
        memory_size=50
    )


@pytest.fixture
def agent_with_tools():
    """创建带工具的Agent实例"""
    calculator = CalculatorTool()
    search = SearchTool()
    return Agent(
        name="TestAgentWithTools",
        description="A test agent with tools",
        memory_size=50,
        tools=[calculator, search]
    )


class TestAgentBasic:
    """基础Agent测试"""

    def test_agent_creation(self, basic_agent):
        """测试Agent创建"""
        assert basic_agent.name == "TestAgent"
        assert basic_agent.description == "A test agent"
        assert basic_agent.id is not None

    def test_agent_id_unique(self):
        """测试Agent ID唯一性"""
        agent1 = Agent(name="Agent1")
        agent2 = Agent(name="Agent2")
        assert agent1.id != agent2.id

    def test_agent_chat(self, basic_agent):
        """测试Agent对话"""
        response = basic_agent.chat("Hello")
        assert isinstance(response, str)
        assert len(response) > 0

    def test_agent_memory(self, basic_agent):
        """测试Agent记忆"""
        # 添加消息
        basic_agent.chat("Message 1")
        basic_agent.chat("Message 2")

        # 检查历史
        history = basic_agent.get_conversation_history()
        assert len(history) == 4  # 2 user + 2 assistant

    def test_agent_clear_memory(self, basic_agent):
        """测试清除记忆"""
        basic_agent.chat("Test message")
        assert len(basic_agent.get_conversation_history()) > 0

        basic_agent.clear_memory()
        assert len(basic_agent.get_conversation_history()) == 0

    def test_agent_status(self, basic_agent):
        """测试Agent状态"""
        status = basic_agent.get_status()
        assert "id" in status
        assert "name" in status
        assert "description" in status
        assert "created_at" in status
        assert "memory_size" in status


class TestAgentWithTools:
    """带工具的Agent测试"""

    def test_agent_has_tools(self, agent_with_tools):
        """测试Agent有工具"""
        tools = agent_with_tools.list_tools()
        assert "calculator" in tools
        assert "search" in tools

    def test_agent_get_tool(self, agent_with_tools):
        """测试获取工具"""
        tool = agent_with_tools.get_tool("calculator")
        assert tool is not None
        assert tool.name == "calculator"

    def test_agent_get_nonexistent_tool(self, agent_with_tools):
        """测试获取不存在的工具"""
        tool = agent_with_tools.get_tool("nonexistent")
        assert tool is None

    def test_agent_register_tool(self, basic_agent):
        """测试注册工具"""
        calculator = CalculatorTool()
        basic_agent.register_tool(calculator)

        assert "calculator" in basic_agent.list_tools()

    def test_agent_chat_with_tools(self, agent_with_tools):
        """测试带工具的对话"""
        response = agent_with_tools.chat("Calculate 2 + 2")
        assert isinstance(response, str)


class TestMemory:
    """内存测试"""

    def test_memory_initialization(self, basic_agent):
        """测试内存初始化"""
        assert basic_agent.memory is not None
        assert len(basic_agent.memory) == 0

    def test_memory_add_message(self, basic_agent):
        """测试添加消息"""
        basic_agent.memory.add_message("user", "Test")
        assert len(basic_agent.memory) == 1

    def test_memory_get_messages(self, basic_agent):
        """测试获取消息"""
        basic_agent.memory.add_message("user", "Message 1")
        basic_agent.memory.add_message("assistant", "Response 1")

        messages = basic_agent.memory.get_messages()
        assert len(messages) == 2

    def test_memory_limit(self):
        """测试内存限制"""
        agent = Agent(memory_size=5)
        for i in range(10):
            agent.chat(f"Message {i}")

        # 内存应该只保留最后5条对话（10条消息）
        assert len(agent.memory) == 10

    def test_memory_context_window(self, basic_agent):
        """测试上下文窗口"""
        for i in range(10):
            basic_agent.chat(f"Message {i}")

        context = basic_agent.memory.get_context_window(window_size=5)
        assert len(context) == 5

    def test_memory_usage(self, basic_agent):
        """测试内存使用情况"""
        basic_agent.chat("Test")
        usage = basic_agent.memory.get_memory_usage()

        assert "current_size" in usage
        assert "max_size" in usage
        assert "usage_percentage" in usage
