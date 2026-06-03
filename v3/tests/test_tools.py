"""
工具测试模块
测试工具相关功能
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from v3.src.core.tools import Tool, ToolRegistry, CalculatorTool, SearchTool


# ==================== 工具基类测试 (阶段一即可通过) ====================

class TestToolBase:
    """工具基类测试"""

    def test_tool_initialization(self):
        class DummyTool(Tool):
            def execute(self, **kwargs):
                return "ok"

        tool = DummyTool(name="test", description="desc")
        assert tool.name == "test"
        assert tool.id is not None

    def test_tool_schema_generation(self):
        class DummyTool(Tool):
            def execute(self, **kwargs):
                return "ok"

        params = {"type": "object", "properties": {"input": {"type": "string"}}}
        tool = DummyTool(name="test", description="desc", parameters=params)
        schema = tool.get_schema()
        assert schema["name"] == "test"
        assert schema["parameters"] == params

    def test_tool_validate_required_params(self):
        class DummyTool(Tool):
            def execute(self, **kwargs):
                return "ok"

        tool = DummyTool(
            name="test", description="desc",
            parameters={"required": ["expression"]}
        )
        assert tool.validate_parameters({"expression": "1+1"}) is True
        with pytest.raises(ValueError):
            tool.validate_parameters({})


# ==================== 工具注册表测试 (阶段一即可通过) ====================

class TestToolRegistry:
    """工具注册表测试"""

    def test_register_and_list(self):
        registry = ToolRegistry()
        class DummyTool(Tool):
            def execute(self, **kwargs):
                return "ok"

        registry.register(DummyTool(name="t1", description="d"))
        assert "t1" in registry.list_tools()

    def test_unregister(self):
        registry = ToolRegistry()
        class DummyTool(Tool):
            def execute(self, **kwargs):
                return "ok"

        registry.register(DummyTool(name="t1", description="d"))
        registry.unregister("t1")
        assert "t1" not in registry.list_tools()

    def test_get_nonexistent_tool(self):
        registry = ToolRegistry()
        assert registry.get_tool("nonexistent") is None


# ==================== 内置工具测试 ====================

class TestCalculatorTool:
    """
    计算器工具测试

    TODO: 阶段三 - 实现CalculatorTool后启用
      - test_basic_operations: 基本四则运算
      - test_complex_expressions: 复杂表达式
      - test_invalid_input: 错误输入处理
    """

    @pytest.mark.skip(reason="TODO: 阶段三 - CalculatorTool实现后启用")
    def test_basic_operations(self):
        pass


class TestSearchTool:
    """
    搜索工具测试

    TODO: 阶段三 - 实现SearchTool后启用
      - test_search_returns_results: 搜索返回结果
      - test_search_api_error: 搜索API异常处理
    """

    @pytest.mark.skip(reason="TODO: 阶段三 - SearchTool实现后启用")
    def test_search_returns_results(self):
        pass
