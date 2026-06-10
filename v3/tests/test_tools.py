"""
测试工具模块
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.tools.base import Tool, ToolRegistry


class TestToolBase:
    """工具基类测试"""

    def test_tool_schema(self):
        class Dummy(Tool):
            name = "dummy"
            description = "test"
            parameters = {"type": "object", "properties": {"x": {"type": "string"}}}

            async def execute(self, **kwargs):
                return "ok"

        tool = Dummy()
        schema = tool.get_schema()
        assert schema["name"] == "dummy"
        assert "x" in schema["parameters"]["properties"]

    def test_registry_register_and_list(self):
        registry = ToolRegistry()

        class T1(Tool):
            name = "t1"
            description = "d"
            async def execute(self, **kwargs):
                pass

        registry.register(T1())
        assert "t1" in registry.list_tools()

    def test_registry_get_nonexistent(self):
        registry = ToolRegistry()
        assert registry.get("nope") is None

    def test_registry_execute(self):
        registry = ToolRegistry()

        class Echo(Tool):
            name = "echo"
            description = "echo"
            async def execute(self, **kwargs):
                return kwargs

        registry.register(Echo())
        import asyncio
        result = asyncio.run(registry.execute("echo", a=1))
        assert result == {"a": 1}

    def test_registry_execute_unknown(self):
        registry = ToolRegistry()
        import asyncio
        with pytest.raises(ValueError):
            asyncio.run(registry.execute("nope"))


class TestToolSchemas:
    """测试各工具的 schema 定义"""

    def test_retrieval_tool_schema(self):
        from src.core.tools.retrieval import RetrievalTool
        tool = RetrievalTool(rag_pipeline=None)
        schema = tool.get_schema()
        assert schema["name"] == "knowledge_retrieval"
        assert "query" in schema["parameters"]["properties"]

    def test_web_search_schema(self):
        from src.core.tools.web_search import WebSearchTool
        tool = WebSearchTool()
        schema = tool.get_schema()
        assert schema["name"] == "web_search"

    def test_question_gen_schema(self):
        from src.core.tools.question_gen import QuestionGenTool
        tool = QuestionGenTool(llm=None)
        schema = tool.get_schema()
        assert schema["name"] == "question_generator"

    def test_mindmap_gen_schema(self):
        from src.core.tools.mindmap_gen import MindmapGenTool
        tool = MindmapGenTool(llm=None)
        schema = tool.get_schema()
        assert schema["name"] == "mindmap_generator"

    def test_study_plan_schema(self):
        from src.core.tools.study_plan import StudyPlanTool
        tool = StudyPlanTool(llm=None)
        schema = tool.get_schema()
        assert schema["name"] == "study_plan"
