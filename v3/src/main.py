"""
主程序入口
Agent编程项目的主入口点
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from v3.src.core.agent import Agent
from v3.src.core.tools import CalculatorTool, SearchTool
from v3.src.utils.logger import setup_logger, get_logger


def create_agent() -> Agent:
    """
    创建一个配置好的Agent实例

    Returns:
        Agent实例
    """
    # 创建工具
    calculator = CalculatorTool()
    search = SearchTool()

    # 创建Agent
    agent = Agent(
        name="Assistant",
        description="A helpful AI assistant with calculator and search capabilities",
        memory_size=100,
        tools=[calculator, search]
    )

    return agent


def interactive_mode(agent: Agent) -> None:
    """
    交互模式

    Args:
        agent: Agent实例
    """
    logger = get_logger()
    logger.info("Starting interactive mode. Type 'quit' or 'exit' to exit.")
    print("\n" + "="*50)
    print("Agent Interactive Mode")
    print("="*50)
    print("Type your message and press Enter.")
    print("Type 'quit' or 'exit' to exit.")
    print("Type 'status' to see agent status.")
    print("Type 'history' to see conversation history.")
    print("Type 'clear' to clear conversation history.")
    print("="*50 + "\n")

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit"):
                print("Goodbye!")
                break

            if user_input.lower() == "status":
                status = agent.get_status()
                print("\nAgent Status:")
                for key, value in status.items():
                    print(f"  {key}: {value}")
                print()
                continue

            if user_input.lower() == "history":
                history = agent.get_conversation_history()
                if not history:
                    print("\nNo conversation history.\n")
                else:
                    print("\nConversation History:")
                    for msg in history[-10:]:  # 显示最后10条
                        role = msg["role"].capitalize()
                        content = msg["content"][:100]  # 截断长消息
                        print(f"  {role}: {content}")
                print()
                continue

            if user_input.lower() == "clear":
                agent.clear_memory()
                print("\nMemory cleared.\n")
                continue

            # 处理用户消息
            response = agent.chat(user_input)
            print(f"\nAgent: {response}\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"\nError: {e}\n")


def demo_mode(agent: Agent) -> None:
    """
    演示模式

    Args:
        agent: Agent实例
    """
    print("\n" + "="*50)
    print("Agent Demo Mode")
    print("="*50)

    # 显示Agent状态
    status = agent.get_status()
    print("\nAgent Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")

    # 演示对话
    demo_messages = [
        "Hello! What can you do?",
        "Calculate 2 + 2",
        "Search for information about Python",
        "What is the meaning of life?"
    ]

    print("\nDemo Conversation:")
    print("-"*50)

    for message in demo_messages:
        print(f"\nUser: {message}")
        response = agent.chat(message)
        print(f"Agent: {response}")

    print("\n" + "="*50)
    print("Demo completed!")
    print("="*50 + "\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Agent Programming Project"
    )

    parser.add_argument(
        "--mode",
        choices=["interactive", "demo"],
        default="interactive",
        help="Run mode (default: interactive)"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level (default: INFO)"
    )

    parser.add_argument(
        "--log-file",
        help="Log file path (optional)"
    )

    args = parser.parse_args()

    # 设置日志
    setup_logger(
        name="ouragent",
        level=args.log_level,
        log_file=args.log_file
    )

    logger = get_logger()
    logger.info(f"Starting Agent in {args.mode} mode")

    # 创建Agent
    agent = create_agent()
    logger.info(f"Agent created: {agent.name} (ID: {agent.id})")

    # 运行模式
    if args.mode == "interactive":
        interactive_mode(agent)
    elif args.mode == "demo":
        demo_mode(agent)


if __name__ == "__main__":
    main()
