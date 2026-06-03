"""
工具接口模块
定义和管理Agent可用的工具
"""

from typing import Dict, List, Any, Optional, Callable
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
        """
        初始化工具

        Args:
            name: 工具名称
            description: 工具描述
            parameters: 参数定义（JSON Schema格式）
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.parameters = parameters or {}
        self.created_at = datetime.now()

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        执行工具（必须被子类实现）

        Args:
            **kwargs: 工具参数

        Returns:
            执行结果
        """
        pass

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """
        验证参数

        Args:
            params: 参数字典

        Returns:
            验证是否通过
        """
        # 基础验证：检查必需参数
        required = self.parameters.get("required", [])
        for param_name in required:
            if param_name not in params:
                raise ValueError(f"Missing required parameter: {param_name}")
        return True

    def get_schema(self) -> Dict[str, Any]:
        """获取工具的JSON Schema"""
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
        """初始化工具注册表"""
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
        """获取所有工具的Schema"""
        return [tool.get_schema() for tool in self.tools.values()]

    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """
        执行指定工具

        Args:
            tool_name: 工具名称
            **kwargs: 工具参数

        Returns:
            执行结果

        Raises:
            ValueError: 工具不存在
        """
        tool = self.get_tool(tool_name)
        if tool is None:
            raise ValueError(f"Tool not found: {tool_name}")

        tool.validate_parameters(kwargs)
        return tool.execute(**kwargs)


# 内置工具示例

class CalculatorTool(Tool):
    """计算器工具示例"""

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
        """执行计算"""
        try:
            # 安全起见，使用受限的eval
            result = eval(expression, {"__builtins__": {}}, {})
            return {"result": result}
        except Exception as e:
            return {"error": str(e)}


class SearchTool(Tool):
    """搜索工具示例"""

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
        """执行搜索（示例实现）"""
        # 这里只是一个示例，实际应该连接到搜索API
        return {"results": [f"Result for: {query}"]}
