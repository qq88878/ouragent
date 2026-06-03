"""
工具测试模块
测试工具相关功能
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from v3.src.core.tools import Tool, ToolRegistry, CalculatorTool, SearchTool


@pytest.fixture
def calculator():
    """创建计算器工具实例"""
    return CalculatorTool()


@pytest.fixture
def search():
    """创建搜索工具实例"""
    return SearchTool()


@pytest.fixture
def registry():
    """创建工具注册表实例"""
    return ToolRegistry()


class TestCalculatorTool:
    """计算器工具测试"""

    def test_calculator_creation(self, calculator):
        """测试计算器创建"""
        assert calculator.name == "calculator"
        assert calculator.description is not None
        assert calculator.parameters is not None

    def test_calculator_schema(self, calculator):
        """测试计算器Schema"""
        schema = calculator.get_schema()
        assert "name" in schema
        assert "description" in schema
        assert "parameters" in schema

    def test_calculator_basic_operations(self, calculator):
        """测试基本运算"""
        result = calculator.execute(expression="2 + 2")
        assert result["result"] == 4

        result = calculator.execute(expression="10 * 5")
        assert result["result"] == 50

    def test_calculator_complex_operations(self, calculator):
        """测试复杂运算"""
        result = calculator.execute(expression="(2 + 3) * 4")
        assert result["result"] == 20

    def test_calculator_invalid_expression(self, calculator):
        """测试无效表达式"""
        result = calculator.execute(expression="invalid")
        assert "error" in result

    def test_calculator_validate_parameters(self, calculator):
        """测试参数验证"""
        # 应该通过验证
        assert calculator.validate_parameters({"expression": "2+2"}) is True

        # 应该失败（缺少必需参数）
        with pytest.raises(ValueError):
            calculator.validate_parameters({})


class TestSearchTool:
    """搜索工具测试"""

    def test_search_creation(self, search):
        """测试搜索工具创建"""
        assert search.name == "search"
        assert search.description is not None

    def test_search_execute(self, search):
        """测试搜索执行"""
        result = search.execute(query="Python")
        assert "results" in result
        assert len(result["results"]) > 0

    def test_search_schema(self, search):
        """测试搜索Schema"""
        schema = search.get_schema()
        assert schema["name"] == "search"


class TestToolRegistry:
    """工具注册表测试"""

    def test_registry_initialization(self, registry):
        """测试注册表初始化"""
        assert len(registry.list_tools()) == 0

    def test_registry_register(self, registry, calculator):
        """测试注册工具"""
        registry.register(calculator)
        assert "calculator" in registry.list_tools()

    def test_registry_unregister(self, registry, calculator):
        """测试注销工具"""
        registry.register(calculator)
        assert "calculator" in registry.list_tools()

        registry.unregister("calculator")
        assert "calculator" not in registry.list_tools()

    def test_registry_get_tool(self, registry, calculator):
        """测试获取工具"""
        registry.register(calculator)
        tool = registry.get_tool("calculator")
        assert tool is not None
        assert tool.name == "calculator"

    def test_registry_get_nonexistent_tool(self, registry):
        """测试获取不存在的工具"""
        tool = registry.get_tool("nonexistent")
        assert tool is None

    def test_registry_get_all_schemas(self, registry, calculator, search):
        """测试获取所有Schema"""
        registry.register(calculator)
        registry.register(search)

        schemas = registry.get_all_schemas()
        assert len(schemas) == 2

    def test_registry_execute_tool(self, registry, calculator):
        """测试执行工具"""
        registry.register(calculator)
        result = registry.execute_tool("calculator", expression="5 + 5")
        assert result["result"] == 10

    def test_registry_execute_nonexistent_tool(self, registry):
        """测试执行不存在的工具"""
        with pytest.raises(ValueError):
            registry.execute_tool("nonexistent")


class TestToolBase:
    """工具基类测试"""

    def test_tool_initialization(self):
        """测试工具初始化"""
        class TestTool(Tool):
            def execute(self, **kwargs):
                return "test"

        tool = TestTool(name="test", description="Test tool")
        assert tool.name == "test"
        assert tool.description == "Test tool"
        assert tool.id is not None

    def test_tool_schema_generation(self):
        """测试Schema生成"""
        class TestTool(Tool):
            def execute(self, **kwargs):
                return "test"

        parameters = {
            "type": "object",
            "properties": {
                "input": {"type": "string"}
            }
        }

        tool = TestTool(
            name="test",
            description="Test tool",
            parameters=parameters
        )

        schema = tool.get_schema()
        assert schema["name"] == "test"
        assert schema["parameters"] == parameters
