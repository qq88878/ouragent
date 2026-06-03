"""
配置测试模块
测试配置管理功能
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from v3.src.utils.config import Config, get_config, reload_config


@pytest.fixture
def sample_env_file(tmp_path):
    """创建示例环境文件"""
    env_content = """
APP_ENV=testing
DEBUG=true
LOG_LEVEL=DEBUG
API_KEY=test-api-key
SECRET_KEY=test-secret
MAX_MEMORY_SIZE=50
"""
    env_file = tmp_path / ".env"
    env_file.write_text(env_content)
    return str(env_file)


@pytest.fixture
def config(sample_env_file):
    """创建配置实例"""
    return Config(sample_env_file)


class TestConfig:
    """配置类测试"""

    def test_config_initialization(self, config):
        """测试配置初始化"""
        assert config is not None
        assert isinstance(config, Config)

    def test_config_defaults(self):
        """测试默认配置"""
        config = Config()
        assert config.get("APP_ENV") == "development"
        assert config.get("DEBUG") == "true"
        assert config.get("LOG_LEVEL") == "INFO"

    def test_config_from_file(self, config):
        """测试从文件加载配置"""
        assert config.get("APP_ENV") == "testing"
        assert config.get("API_KEY") == "test-api-key"

    def test_config_get(self, config):
        """测试获取配置"""
        assert config.get("APP_ENV") == "testing"
        assert config.get("NONEXISTENT") is None
        assert config.get("NONEXISTENT", "default") == "default"

    def test_config_set(self, config):
        """测试设置配置"""
        config.set("NEW_KEY", "new_value")
        assert config.get("NEW_KEY") == "new_value"

    def test_config_get_int(self, config):
        """测试获取整数配置"""
        assert config.get_int("MAX_MEMORY_SIZE") == 50
        assert config.get_int("NONEXISTENT", 100) == 100

    def test_config_get_bool(self, config):
        """测试获取布尔配置"""
        assert config.get_bool("DEBUG") is True
        assert config.get_bool("NONEXISTENT", False) is False

    def test_config_get_float(self):
        """测试获取浮点配置"""
        config = Config()
        config.set("FLOAT_VALUE", "3.14")
        assert config.get_float("FLOAT_VALUE") == 3.14

    def test_config_get_list(self):
        """测试获取列表配置"""
        config = Config()
        config.set("LIST_VALUE", "a,b,c")
        result = config.get_list("LIST_VALUE")
        assert result == ["a", "b", "c"]

    def test_config_is_development(self, config):
        """测试环境判断"""
        assert config.is_development() is False
        assert config.is_testing() is True
        assert config.is_production() is False

    def test_config_get_all(self, config):
        """测试获取所有配置"""
        all_config = config.get_all()
        assert isinstance(all_config, dict)
        assert "APP_ENV" in all_config


class TestGlobalConfig:
    """全局配置测试"""

    def test_get_config(self):
        """测试获取全局配置"""
        config = get_config()
        assert config is not None

    def test_reload_config(self, sample_env_file):
        """测试重新加载配置"""
        config1 = get_config(sample_env_file)
        config2 = reload_config(sample_env_file)

        # 应该是同一个实例（全局缓存）
        assert config1 is not None
        assert config2 is not None


class TestConfigValidation:
    """配置验证测试"""

    def test_missing_required_key(self):
        """测试缺失必需的配置键"""
        # 这里只是示例，实际根据项目需求定义
        config = Config()
        assert config.get("MISSING_KEY") is None

    def test_invalid_env_file(self, tmp_path):
        """测试无效的环境文件"""
        invalid_file = str(tmp_path / "nonexistent.env")
        config = Config(invalid_file)
        # 应该使用默认值
        assert config.get("APP_ENV") == "development"
