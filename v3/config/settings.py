"""
项目配置管理
使用 pydantic-settings 管理配置，支持环境变量和 .env 文件
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
from pathlib import Path
import os


class Settings(BaseSettings):
    """应用配置类"""

    # ==================== 应用配置 ====================
    APP_ENV: str = Field(default="development", description="运行环境")
    DEBUG: bool = Field(default=True, description="调试模式")
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    PORT: int = Field(default=8000, description="服务端口")

    # ==================== 数据库配置 ====================
    DB_HOST: str = Field(default="localhost", description="数据库主机")
    DB_PORT: int = Field(default=5432, description="数据库端口")
    DB_NAME: str = Field(default="agent_db", description="数据库名称")
    DB_USER: str = Field(default="agent", description="数据库用户")
    DB_PASSWORD: str = Field(default="agent_password", description="数据库密码")

    # 连接池配置 (性能需求 P4)
    DB_POOL_SIZE: int = Field(default=10, description="连接池大小")
    DB_MAX_OVERFLOW: int = Field(default=20, description="连接池最大溢出")

    # ==================== Redis配置 ====================
    REDIS_HOST: str = Field(default="localhost", description="Redis主机")
    REDIS_PORT: int = Field(default=6379, description="Redis端口")
    REDIS_PASSWORD: str = Field(default="", description="Redis密码")
    REDIS_DB: int = Field(default=0, description="Redis数据库")

    # ==================== Milvus配置 ====================
    MILVUS_HOST: str = Field(default="localhost", description="Milvus主机")
    MILVUS_PORT: int = Field(default=19530, description="Milvus端口")

    # ==================== 安全配置 ====================
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT密钥"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT算法")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Access Token过期时间(分钟)"
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Refresh Token过期时间(天)"
    )

    # 密码加密 (安全需求 S1)
    PASSWORD_HASH_ALGORITHM: str = Field(default="bcrypt", description="密码哈希算法")
    PASSWORD_HASH_ROUNDS: int = Field(default=12, description="密码哈希轮数")

    # ==================== LLM配置 ====================
    LLM_PROVIDER: str = Field(default="openai", description="LLM提供商: spark / openai")

    # 星火大模型配置
    SPARK_APP_ID: Optional[str] = Field(default=None, description="星火 App ID")
    SPARK_API_KEY: Optional[str] = Field(default=None, description="星火 API Key")
    SPARK_API_SECRET: Optional[str] = Field(default=None, description="星火 API Secret")
    SPARK_MODEL: str = Field(default="generalv3.5", description="星火模型版本")
    SPARK_BASE_URL: str = Field(default="https://spark-api-open.xf-yun.com/v1", description="星火 API 地址")

    # OpenAI 兼容接口配置（也支持 DeepSeek、MIMO 等）
    LLM_API_KEY: Optional[str] = Field(default=None, description="LLM API Key")
    LLM_MODEL: str = Field(default="gpt-3.5-turbo", description="LLM 模型名称")
    LLM_BASE_URL: str = Field(default="https://api.openai.com/v1", description="LLM API 地址")

    # Embedding 配置（默认复用 LLM 的 key 和 url）
    EMBEDDING_API_KEY: Optional[str] = Field(default=None, description="Embedding API Key")
    EMBEDDING_BASE_URL: Optional[str] = Field(default=None, description="Embedding API 地址")
    EMBEDDING_MODEL: str = Field(default="text-embedding-3-small", description="Embedding 模型名称")

    # ==================== CORS配置 ====================
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="允许的CORS源"
    )

    # ==================== Agent配置 ====================
    AGENT_DEFAULT_MEMORY_SIZE: int = Field(default=100, description="Agent默认记忆大小")
    AGENT_MAX_MEMORY_SIZE: int = Field(default=1000, description="Agent最大记忆大小")

    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        """验证密钥安全性"""
        if v == "your-secret-key-change-in-production":
            import warnings
            warnings.warn("⚠️  警告: 使用默认 SECRET_KEY，生产环境必须修改！")
        return v

    @property
    def embedding_api_key(self) -> str:
        return self.EMBEDDING_API_KEY or self.LLM_API_KEY or ""

    @property
    def embedding_base_url(self) -> str:
        return self.EMBEDDING_BASE_URL or self.LLM_BASE_URL

    @property
    def DATABASE_URL(self) -> str:
        """获取数据库连接 URL (使用 asyncpg 异步驱动)"""
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


    @property
    def REDIS_URL(self) -> str:
        """获取 Redis 连接 URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def MILVUS_URI(self) -> str:
        """获取 Milvus 连接 URI"""
        return f"http://{self.MILVUS_HOST}:{self.MILVUS_PORT}"

    @property
    def cors_origins_list(self) -> List[str]:
        """获取 CORS 源列表"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = str(Path(__file__).parent / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True


# 全局配置实例
settings = Settings()


# ==================== 目录配置 ====================
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
TESTS_DIR = PROJECT_ROOT / "tests"
DOCS_DIR = PROJECT_ROOT / "docs"
CONFIG_DIR = PROJECT_ROOT / "config"
LOGS_DIR = PROJECT_ROOT / "logs"
DATA_DIR = PROJECT_ROOT / "data"


def ensure_directories():
    """确保必要的目录存在"""
    directories = [LOGS_DIR, DATA_DIR]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


# 初始化时确保目录存在
ensure_directories()
