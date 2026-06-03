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

from src.core.agent import Agent
from src.core.tools import CalculatorTool, SearchTool


def create_agent() -> Agent:
    """
    创建一个配置好的Agent实例

    TODO: 阶段二 - 从配置文件/env加载Agent参数
      - LLM provider配置 (api_key, model, temperature等)
      - 工具列表配置 (启用哪些工具)
      - 记忆策略配置 (窗口大小、持久化方式)
    """
    # TODO: 阶段三 - 注册已实现的工具
    # tools = [CalculatorTool(), SearchTool()]
    tools = []

    agent = Agent(
        name="Assistant",
        description="A helpful AI assistant",
        memory_size=100,
        tools=tools
    )
    return agent


def interactive_mode(agent: Agent) -> None:
    """
    交互模式 - 命令行对话

    TODO: 阶段五 - 增强交互体验
      - 支持多行输入
      - 支持命令 (/clear, /history, /tools, /save)
      - 输入历史 (上下键)
      - Markdown渲染输出
    """
    print("\n" + "=" * 50)
    print("Agent Interactive Mode")
    print("=" * 50)
    print("Type 'quit' or 'exit' to exit.")
    print("=" * 50 + "\n")

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit"):
                print("Goodbye!")
                break

            response = agent.chat(user_input)
            print(f"\nAgent: {response}\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Agent Service")
    parser.add_argument("--mode", choices=["interactive", "api"],
                        default="api", help="Run mode (default: api)")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.mode == "api":
        # TODO: 阶段一 - 启动FastAPI服务
        import uvicorn
        uvicorn.run("src.api:app", host=args.host, port=args.port, reload=True)
    else:
        agent = create_agent()
        interactive_mode(agent)


if __name__ == "__main__":
    main()
