"""
RAG 模块单元测试
测试 document_loader, chunker, vector_store, embeddings
"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.core.rag.vector_store import VectorStore, Document
from src.core.rag.chunker import TextChunker
from src.core.rag.document_loader import DocumentLoader


# ==================== VectorStore 测试 ====================


class TestVectorStore:
    """向量存储测试"""

    def test_add_document(self, sample_embeddings):
        """测试添加文档"""
        store = VectorStore(dimension=4)
        doc = Document(id="1", content="test", embedding=sample_embeddings[0])
        store.add(doc)
        assert store.count() == 1

    def test_add_batch(self, sample_documents):
        """测试批量添加"""
        store = VectorStore(dimension=4)
        count = store.add_batch(sample_documents)
        assert count == 3
        assert store.count() == 3

    def test_search(self, sample_documents, sample_embeddings):
        """测试检索"""
        store = VectorStore(dimension=4)
        store.add_batch(sample_documents)

        # 查询最相似的文档
        query = np.array([1.0, 0.1, 0.0, 0.0], dtype=np.float32)
        results = store.search(query, top_k=2)

        assert len(results) == 2
        assert results[0][0].id == "doc1"  # 最相似
        assert results[0][1] > 0  # 相似度 > 0

    def test_delete_by_source(self, sample_documents):
        """测试按来源删除"""
        store = VectorStore(dimension=4)
        store.add_batch(sample_documents)

        removed = store.delete_by_source("python_basics.txt")
        assert removed == 2
        assert store.count() == 1

    def test_delete_by_knowledge_id(self, sample_documents):
        """测试按知识库ID删除"""
        store = VectorStore(dimension=4)
        store.add_batch(sample_documents)

        removed = store.delete_by_knowledge_id(1)
        assert removed == 2
        assert store.count() == 1

    def test_save_load_v2(self, sample_documents, tmp_path):
        """测试 v2 格式保存和加载"""
        store = VectorStore(dimension=4)
        store.add_batch(sample_documents)

        save_path = str(tmp_path / "test_store")
        store.save(save_path)

        # 检查文件生成
        assert (tmp_path / "test_store.npy").exists()
        assert (tmp_path / "test_store_meta.json").exists()
        assert (tmp_path / "test_store_index.json").exists()

        # 加载
        store2 = VectorStore(dimension=4)
        count = store2.load(save_path)
        assert count == 3

        # 验证检索结果一致
        query = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        results1 = store.search(query, top_k=1)
        results2 = store2.search(query, top_k=1)
        assert results1[0][0].id == results2[0][0].id

    def test_get_stats(self, sample_documents):
        """测试获取统计信息"""
        store = VectorStore(dimension=4)
        store.add_batch(sample_documents)

        stats = store.get_stats()
        assert stats["document_count"] == 3
        assert stats["dimension"] == 4
        assert stats["is_dirty"] == True


# ==================== TextChunker 测试 ====================


class TestTextChunker:
    """文本分块测试"""

    def test_chunk_short_text(self):
        """测试短文本分块"""
        chunker = TextChunker(chunk_size=100, overlap=20)
        text = "这是一段短文本。"
        chunks = chunker.chunk(text, {"source": "test"})
        assert len(chunks) >= 1
        assert chunks[0].content == text

    def test_chunk_long_text(self):
        """测试长文本分块"""
        chunker = TextChunker(chunk_size=15, overlap=3)
        text = "第一段内容在这里。\n\n第二段内容在这里。\n\n第三段内容在这里。"
        chunks = chunker.chunk(text, {"source": "test"})
        assert len(chunks) >= 2

    def test_chunk_metadata(self):
        """测试分块元数据"""
        chunker = TextChunker(chunk_size=100, overlap=20)
        text = "测试内容"
        metadata = {"source": "test.txt", "knowledge_id": 1}
        chunks = chunker.chunk(text, metadata)

        assert chunks[0].metadata["source"] == "test.txt"
        assert chunks[0].metadata["knowledge_id"] == 1
        assert chunks[0].index == 0


# ==================== DocumentLoader 测试 ====================


class TestDocumentLoader:
    """文档加载器测试"""

    def test_supported_extensions(self):
        """测试支持的格式"""
        loader = DocumentLoader()
        assert ".txt" in loader.SUPPORTED_EXTENSIONS
        assert ".md" in loader.SUPPORTED_EXTENSIONS
        assert ".pdf" in loader.SUPPORTED_EXTENSIONS
        assert ".docx" in loader.SUPPORTED_EXTENSIONS
        assert ".pptx" in loader.SUPPORTED_EXTENSIONS
        assert ".xlsx" in loader.SUPPORTED_EXTENSIONS
        assert ".html" in loader.SUPPORTED_EXTENSIONS

    def test_load_text_file(self, tmp_path):
        """测试加载文本文件"""
        # 创建测试文件
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!", encoding="utf-8")

        loader = DocumentLoader()
        content = loader.load(str(test_file))
        assert content == "Hello, World!"

    def test_load_markdown_file(self, tmp_path):
        """测试加载 Markdown 文件"""
        test_file = tmp_path / "test.md"
        test_file.write_text("# 标题\n\n内容", encoding="utf-8")

        loader = DocumentLoader()
        content = loader.load(str(test_file))
        assert "标题" in content

    def test_load_bytes(self):
        """测试从字节流加载"""
        loader = DocumentLoader()
        content = loader.load_bytes(b"Hello", "test.txt")
        assert content == "Hello"

    def test_unsupported_format(self):
        """测试不支持的格式"""
        loader = DocumentLoader()
        with pytest.raises(ValueError, match="不支持的文件格式"):
            loader.load_bytes(b"test", "test.xyz")


# ==================== Embeddings 测试 ====================


class TestEmbeddings:
    """嵌入测试"""

    @pytest.mark.asyncio
    async def test_improved_local_embedding(self):
        """测试改进的本地嵌入"""
        from src.core.rag.embeddings import ImprovedLocalEmbeddingProvider

        provider = ImprovedLocalEmbeddingProvider(dimension=64)
        texts = ["Python列表", "什么是递归？"]

        embeddings = await provider.embed(texts)

        assert len(embeddings) == 2
        assert embeddings[0].shape == (64,)
        # 验证 L2 归一化
        norm = np.linalg.norm(embeddings[0])
        assert abs(norm - 1.0) < 1e-5

    @pytest.mark.asyncio
    async def test_local_embedding(self):
        """测试基础本地嵌入"""
        from src.core.rag.embeddings import LocalEmbeddingProvider

        provider = LocalEmbeddingProvider(dimension=64)
        texts = ["Python列表", "什么是递归？"]

        embeddings = await provider.embed(texts)

        assert len(embeddings) == 2
        assert embeddings[0].shape == (64,)

    def test_create_provider_local(self):
        """测试工厂方法 - 本地模式"""
        from src.core.rag.embeddings import create_embedding_provider

        provider = create_embedding_provider(provider="local")
        # 应该返回 ImprovedLocalEmbeddingProvider（如果 jieba 可用）
        assert provider is not None

    def test_create_provider_openai(self):
        """测试工厂方法 - OpenAI 模式"""
        from src.core.rag.embeddings import create_embedding_provider, OpenAIEmbeddingProvider

        provider = create_embedding_provider(
            provider="openai",
            api_key="test-key",
            base_url="https://api.openai.com/v1",
        )
        assert isinstance(provider, OpenAIEmbeddingProvider)
