"""
基础Agent示例
展示如何创建和使用基础Agent
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from v3.src.core.agent import Agent
from v3.src.core.tools import CalculatorTool, SearchTool
from v3.src.utils.logger import setup_logger


def main():
    """主函数"""
    # 设置日志
    setup_logger(level="INFO")

    print("="*60)
    print("基础Agent示例")
    print("="*60)

    # 创建工具
    calculator = CalculatorTool()
    search = SearchTool()

    # 创建Agent
    agent = Agent(
        name="BasicAgent",
        description="A simple agent for demonstration",
        memory_size=50,
        tools=[calculator, search]
    )

    print(f"\n✓ Agent创建成功: {agent.name} (ID: {agent.id})")
    print(f"✓ 可用工具: {agent.list_tools()}")

    # 演示对话
    print("\n" + "-"*60)
    print("开始对话演示")
    print("-"*60)

    messages = [
        "你好！你是谁？",
        "你能做什么？",
        "请帮我计算 10 + 20 * 3",
        "搜索一下Python编程的最佳实践",
        "谢谢你的帮助！"
    ]

    for i, message in enumerate(messages, 1):
        print(f"\n[消息 {i}] 用户: {message}")
        response = agent.chat(message)
        print(f"[回复 {i}] Agent: {response}")

    # 显示Agent状态
    print("\n" + "-"*60)
    print("Agent状态")
    print("-"*60)

    status = agent.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")

    # 显示对话历史
    print("\n" + "-"*60)
    print("对话历史")
    print("-"*60)

    history = agent.get_conversation_history()
    print(f"  总消息数: {len(history)}")

    # 内存使用情况
    memory_usage = agent.memory.get_memory_usage()
    print(f"  内存使用: {memory_usage['current_size']}/{memory_usage['max_size']}")

    print("\n" + "="*60)
    print("示例完成！")
    print("="*60)


if __name__ == "__main__":
    main()
