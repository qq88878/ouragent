"""
测试配置 - pytest fixtures
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import numpy as np

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_llm():
    """模拟 LLM"""
    llm = AsyncMock()
    llm.chat.return_value = '{"result": "test response"}'
    return llm


@pytest.fixture
def sample_embeddings():
    """示例嵌入向量"""
    return [
        np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32),
        np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32),
        np.array([0.0, 0.0, 1.0, 0.0], dtype=np.float32),
    ]


@pytest.fixture
def sample_documents(sample_embeddings):
    """示例文档"""
    from src.core.rag.vector_store import Document

    return [
        Document(
            id="doc1",
            content="Python列表是一种有序的数据结构",
            embedding=sample_embeddings[0],
            metadata={"source": "python_basics.txt", "knowledge_id": 1},
        ),
        Document(
            id="doc2",
            content="元组是不可变的序列类型",
            embedding=sample_embeddings[1],
            metadata={"source": "python_basics.txt", "knowledge_id": 1},
        ),
        Document(
            id="doc3",
            content="字典是键值对的集合",
            embedding=sample_embeddings[2],
            metadata={"source": "python_data_structures.txt", "knowledge_id": 2},
        ),
    ]


@pytest.fixture
def sample_texts():
    """示例文本"""
    return [
        "Python是一种广泛使用的高级编程语言。",
        "列表是Python中最常用的数据结构之一。",
        "元组与列表类似，但元组的元素不可修改。",
    ]
