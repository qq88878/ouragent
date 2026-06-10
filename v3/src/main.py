"""主程序入口"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Agent Service")
    parser.add_argument("--mode", choices=["interactive", "api"], default="api")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.mode == "api":
        import uvicorn
        uvicorn.run("src.api:app", host=args.host, port=args.port, reload=True)
    else:
        print("交互模式暂未实现，请使用 --mode api 启动 HTTP 服务")


if __name__ == "__main__":
    main()
