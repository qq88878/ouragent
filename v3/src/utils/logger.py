"""
日志管理模块
统一的日志记录功能
"""

import logging
import sys
from typing import Optional
from pathlib import Path
from datetime import datetime


def setup_logger(
    name: str = "ouragent",
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别
        log_file: 日志文件路径（可选）
        log_format: 日志格式（可选）

    Returns:
        配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger(name)

    # 设置日志级别
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # 清除现有的处理器
    logger.handlers.clear()

    # 默认日志格式
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(log_format)

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（如果指定了日志文件）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "ouragent") -> logging.Logger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        日志记录器
    """
    return logging.getLogger(name)


class LoggerMixin:
    """
    日志混入类
    为类提供日志功能
    """

    @property
    def logger(self) -> logging.Logger:
        """获取日志记录器"""
        class_name = self.__class__.__name__
        return get_logger(f"ouragent.{class_name}")


def log_function_call(logger: Optional[logging.Logger] = None):
    """
    函数调用日志装饰器

    Args:
        logger: 日志记录器（可选）
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger()

            logger.info(f"Calling {func.__name__}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"{func.__name__} completed successfully")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} failed: {e}")
                raise
        return wrapper
    return decorator


def log_execution_time(logger: Optional[logging.Logger] = None):
    """
    执行时间日志装饰器

    Args:
        logger: 日志记录器（可选）
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger()

            start_time = datetime.now()
            logger.info(f"Starting {func.__name__}")

            try:
                result = func(*args, **kwargs)
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                logger.info(f"{func.__name__} completed in {duration:.2f} seconds")
                return result
            except Exception as e:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                logger.error(f"{func.__name__} failed after {duration:.2f} seconds: {e}")
                raise
        return wrapper
    return decorator
