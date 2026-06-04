"""
项目配置文件
包含各种配置常量和默认值
"""

import os
from pathlib import Path


# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 源代码目录
SRC_DIR = PROJECT_ROOT / "src"

# 测试目录
TESTS_DIR = PROJECT_ROOT / "tests"

# 文档目录
DOCS_DIR = PROJECT_ROOT / "docs"

# 配置目录
CONFIG_DIR = PROJECT_ROOT / "config"

# 日志目录
LOGS_DIR = PROJECT_ROOT / "logs"

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"


# 应用配置
APP_CONFIG = {
    "name": "ouragent",
    "version": "1.0.0",
    "description": "Agent programming project",
    "author": "Agent Programming Team",
}


# Agent配置
AGENT_CONFIG = {
    "default_name": "Assistant",
    "default_description": "A helpful AI assistant",
    "default_memory_size": 100,
    "max_memory_size": 1000,
}


# 日志配置
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": str(LOGS_DIR / "app.log"),
            "mode": "a",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}


# 工具配置
TOOLS_CONFIG = {
    "calculator": {
        "enabled": True,
        "description": "Perform basic arithmetic operations",
    },
    "search": {
        "enabled": True,
        "description": "Search for information",
    },
}


# API配置
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": True,
    "reload": True,
}


# 数据库配置（从环境变量读取，支持Docker部署）
DATABASE_CONFIG = {
    "url": os.getenv(
        "DATABASE_URL",
        f"postgresql://{os.getenv('DB_USER', 'agent')}:{os.getenv('DB_PASSWORD', 'agent_password')}"
        f"@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}"
        f"/{os.getenv('DB_NAME', 'agent_db')}"
    ),
    "echo": os.getenv("DB_ECHO", "false").lower() == "true",
}


# 安全配置
SECURITY_CONFIG = {
    "secret_key": os.getenv("SECRET_KEY", "change-this-in-production"),
    "algorithm": "HS256",
    "access_token_expire_minutes": 30,
}

# Redis配置（从环境变量读取，支持Docker部署）
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", "6379")),
    "password": os.getenv("REDIS_PASSWORD", ""),
    "db": int(os.getenv("REDIS_DB", "0")),
}


def ensure_directories():
    """确保必要的目录存在"""
    directories = [
        LOGS_DIR,
        DATA_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


# 初始化时确保目录存在
ensure_directories()
