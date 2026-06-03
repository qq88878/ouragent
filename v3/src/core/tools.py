"""
工具接口模块
定义和管理Agent可用的工具
"""

from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime
import uuid


class Tool(ABC):
    """
    工具基类
    所有工具都应继承此类
    """

    def __init__(
        self,
        name: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.parameters = parameters or {}
        self.created_at = datetime.now()

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        执行工具 (子类必须实现)

        TODO: 阶段三 - 为每个工具实现具体逻辑
        """
        pass

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """
        验证参数

        TODO: 阶段三 - 增强参数校验 (类型检查、范围校验等)
        """
        required = self.parameters.get("required", [])
        for param_name in required:
            if param_name not in params:
                raise ValueError(f"Missing required parameter: {param_name}")
        return True

    def get_schema(self) -> Dict[str, Any]:
        """获取工具的JSON Schema (供LLM function calling使用)"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }

    def __repr__(self) -> str:
        return f"Tool(name='{self.name}', id='{self.id}')"


class ToolRegistry:
    """
    工具注册表
    管理所有可用的工具
    """

    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """注册一个工具"""
        self.tools[tool.name] = tool

    def unregister(self, tool_name: str) -> None:
        """注销一个工具"""
        if tool_name in self.tools:
            del self.tools[tool_name]

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """获取指定工具"""
        return self.tools.get(tool_name)

    def list_tools(self) -> List[str]:
        """列出所有工具名称"""
        return list(self.tools.keys())

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的Schema (供LLM function calling使用)"""
        return [tool.get_schema() for tool in self.tools.values()]

    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """执行指定工具"""
        tool = self.get_tool(tool_name)
        if tool is None:
            raise ValueError(f"Tool not found: {tool_name}")
        tool.validate_parameters(kwargs)
        return tool.execute(**kwargs)


# ==================== 内置工具 (骨架) ====================

class CalculatorTool(Tool):
    """
    计算器工具

    TODO: 阶段三 - 实现
      - 安全的数学表达式求值
      - 支持科学计算 (sin, cos, log等)
      - 单位转换
    """

    def __init__(self):
        super().__init__(
            name="calculator",
            description="Perform basic arithmetic operations",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            }
        )

    def execute(self, expression: str = "", **kwargs) -> Any:
        # TODO: 阶段三 - 实现安全的表达式求值
        raise NotImplementedError("CalculatorTool not yet implemented")


class SearchTool(Tool):
    """
    搜索工具

    TODO: 阶段三 - 实现
      - 接入搜索API (Google/Bing/DuckDuckGo)
      - 结果摘要与排序
      - 搜索结果缓存
    """

    def __init__(self):
        super().__init__(
            name="search",
            description="Search for information",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    }
                },
                "required": ["query"]
            }
        )

    def execute(self, query: str = "", **kwargs) -> Any:
        # TODO: 阶段三 - 实现搜索API调用
        raise NotImplementedError("SearchTool not yet implemented")


# ==================== 扩展工具 (待实现) ====================

# TODO: 阶段四 - 实现更多工具
#   - WebBrowserTool: 网页浏览与内容提取
#   - DatabaseTool: SQL查询执行
#   - FileTool: 文件读写操作
#   - CodeInterpreterTool: Python代码执行
#   - APICallTool: 通用HTTP API调用
