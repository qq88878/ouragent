"""
高级Agent示例
展示高级Agent功能，包括自定义工具和内存管理
"""
import os
import sys
from os import environ
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from v3.src.core.agent import Agent
from v3.src.core.tools import Tool, ToolRegistry
from v3.src.utils.logger import setup_logger
from v3.src.utils.config import get_config

config = get_config(env_file=str(project_root / "config" / ".env"))
mimo_api_key = config.get("MIMO_API_KEY")

class WeatherTool(Tool):
    """天气查询工具示例"""

    def __init__(self):
        super().__init__(
            name="weather",
            description="Get weather information for a location",
            parameters={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location name (e.g., 'Beijing', 'New York')"
                    }
                },
                "required": ["location"]
            }
        )

    def execute(self, location: str = "", **kwargs) -> Any:
        """执行天气查询（示例）"""
        # 这里只是示例，实际应该调用天气API
        weather_data = {
            "location": location,
            "temperature": 22,
            "condition": "Sunny",
            "humidity": 65,
            "wind": "10 km/h"
        }
        return weather_data


class TranslationTool(Tool):
    """翻译工具示例"""

    def __init__(self):
        super().__init__(
            name="translate",
            description="Translate text between languages",
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to translate"
                    },
                    "target_language": {
                        "type": "string",
                        "description": "Target language (e.g., 'en', 'zh', 'ja')"
                    }
                },
                "required": ["text", "target_language"]
            }
        )

    def execute(self, text: str = "", target_language: str = "", **kwargs) -> Any:
        """执行翻译（示例）"""
        # 这里只是示例，实际应该调用翻译API
        translations = {
            "en": "Hello, World!",
            "zh": "你好，世界！",
            "ja": "こんにちは、世界！",
        }
        return {
            "original": text,
            "translated": translations.get(target_language, text),
            "target_language": target_language
        }


def main():
    """主函数"""
    # 设置日志
    setup_logger(level="INFO")

    print("="*60)
    print("高级Agent示例")
    print("="*60)

    # 创建自定义工具
    weather = WeatherTool()
    translator = TranslationTool()

    # 创建工具注册表
    registry = ToolRegistry()
    registry.register(weather)
    registry.register(translator)

    print(f"\n✓ 注册了 {len(registry.list_tools())} 个工具: {registry.list_tools()}")

    # 创建Agent
    agent = Agent(
        name="AdvancedAgent",
        description="An advanced agent with custom tools",
        memory_size=100,
        tools=[weather, translator]
    )

    print(f"✓ Agent创建成功: {agent.name}")

    # 演示高级功能
    print("\n" + "-"*60)
    print("演示自定义工具")
    print("-"*60)

    # 使用天气工具
    print("\n[测试] 查询天气:")
    result = agent.chat("查询北京的天气")
    print(f"  结果: {result}")

    # 使用翻译工具
    print("\n[测试] 翻译文本:")
    result = agent.chat("将'你好'翻译成英文")
    print(f"  结果: {result}")

    # 显示工具信息
    print("\n" + "-"*60)
    print("工具详细信息")
    print("-"*60)

    for tool_name in agent.list_tools():
        tool = agent.get_tool(tool_name)
        if tool:
            schema = tool.get_schema()
            print(f"\n  工具: {schema['name']}")
            print(f"  描述: {schema['description']}")
            print(f"  参数: {schema['parameters']}")

    # 演示内存管理
    print("\n" + "-"*60)
    print("内存管理演示")
    print("-"*60)

    # 添加一些消息
    for i in range(5):
        agent.chat(f"测试消息 {i+1}")

    # 查看内存使用
    usage = agent.memory.get_memory_usage()
    print(f"\n  当前内存使用: {usage['current_size']}/{usage['max_size']}")
    print(f"  使用率: {usage['usage_percentage']:.1f}%")

    # 获取上下文窗口
    context = agent.memory.get_context_window(window_size=3)
    print(f"\n  最近3条消息:")
    for msg in context:
        print(f"    {msg['role']}: {msg['content'][:50]}...")

    # 清除内存
    agent.clear_memory()
    print(f"\n  ✓ 内存已清除")
    print(f"  当前内存: {len(agent.memory)} 条消息")

    print("\n" + "="*60)
    print("高级示例完成！")
    print("="*60)


if __name__ == "__main__":
    main()
