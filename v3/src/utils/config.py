"""
配置管理模块
处理环境变量和配置文件
"""

import os
from typing import Any, Optional
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """
    配置管理类
    统一管理所有配置项
    """

    # 默认配置
    DEFAULTS = {
        "APP_ENV": "development",
        "DEBUG": "true",
        "LOG_LEVEL": "INFO",
        "HOST": "0.0.0.0",
        "PORT": "8000",
        "API_KEY": "",
        "SECRET_KEY": "default-secret-key-change-in-production",
        "DATABASE_URL": "sqlite:///./app.db",
        "MAX_MEMORY_SIZE": "100",
    }

    def __init__(self, env_file: Optional[str] = None):
        """
        初始化配置

        Args:
            env_file: 环境配置文件路径
        """
        self._config = {}

        # 加载.env文件
        if env_file:
            env_path = Path(env_file)
        else:
            env_path = Path.cwd() / ".env"

        if env_path.exists():
            load_dotenv(env_path)

        # 加载所有配置
        self._load_config()

    def _load_config(self) -> None:
        """加载配置"""
        for key, default_value in self.DEFAULTS.items():
            self._config[key] = os.getenv(key, default_value)

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        设置配置值

        Args:
            key: 配置键
            value: 配置值
        """
        self._config[key] = value

    def get_int(self, key: str, default: int = 0) -> int:
        """获取整数配置"""
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔配置"""
        value = self.get(key, str(default))
        return value.lower() in ("true", "1", "yes", "on")

    def get_float(self, key: str, default: float = 0.0) -> float:
        """获取浮点数配置"""
        value = self.get(key, default)
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def get_list(self, key: str, separator: str = ",", default: Optional[list] = None) -> list:
        """获取列表配置"""
        value = self.get(key, "")
        if not value:
            return default or []
        return [item.strip() for item in value.split(separator)]

    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.get("APP_ENV") == "development"

    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.get("APP_ENV") == "production"

    def is_testing(self) -> bool:
        """是否为测试环境"""
        return self.get("APP_ENV") == "testing"

    def get_all(self) -> dict:
        """获取所有配置"""
        return self._config.copy()

    def __repr__(self) -> str:
        return f"Config(env={self.get('APP_ENV')})"


# 全局配置实例
_config: Optional[Config] = None


def get_config(env_file: Optional[str] = None) -> Config:
    """
    获取全局配置实例

    Args:
        env_file: 环境配置文件路径

    Returns:
        Config实例
    """
    global _config
    if _config is None:
        _config = Config(env_file)
    return _config


def reload_config(env_file: Optional[str] = None) -> Config:
    """
    重新加载配置

    Args:
        env_file: 环境配置文件路径

    Returns:
        新的Config实例
    """
    global _config
    _config = Config(env_file)
    return _config
