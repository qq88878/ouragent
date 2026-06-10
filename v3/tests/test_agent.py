"""
测试 RAG Pipeline 和 VectorStore
"""

import pytest
import sys
import numpy as np
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.rag.vector_store import VectorStore, Document
from src.core.rag.chunker import TextChunker
from src.core.rag.document_loader import DocumentLoader


class TestVectorStore:
    """向量存储测试"""

    def test_add_and_count(self):
        store = VectorStore(dimension=4)
        doc = Document(id="1", content="hello", embedding=np.array([1, 0, 0, 0], dtype=np.float32))
        store.add(doc)
        assert store.count() == 1

    def test_search_returns_sorted(self):
        store = VectorStore(dimension=3)
        store.add(Document(id="1", content="a", embedding=np.array([1, 0, 0], dtype=np.float32)))
        store.add(Document(id="2", content="b", embedding=np.array([0, 1, 0], dtype=np.float32)))
        store.add(Document(id="3", content="c", embedding=np.array([0, 0, 1], dtype=np.float32)))

        query = np.array([1, 0, 0], dtype=np.float32)
        results = store.search(query, top_k=2)
        assert len(results) == 2
        assert results[0][0].id == "1"
        assert results[0][1] > results[1][1]

    def test_delete_by_source(self):
        store = VectorStore(dimension=2)
        store.add(Document(id="1", content="a", embedding=np.array([1, 0], dtype=np.float32), metadata={"source": "file1"}))
        store.add(Document(id="2", content="b", embedding=np.array([0, 1], dtype=np.float32), metadata={"source": "file2"}))

        removed = store.delete_by_source("file1")
        assert removed == 1
        assert store.count() == 1

    def test_save_and_load(self, tmp_path):
        store = VectorStore(dimension=2)
        store.add(Document(id="1", content="hello", embedding=np.array([1, 0], dtype=np.float32)))

        path = str(tmp_path / "store.json")
        store.save(path)

        store2 = VectorStore(dimension=2)
        loaded = store2.load(path)
        assert loaded == 1
        assert store2.count() == 1

    def test_empty_search(self):
        store = VectorStore(dimension=3)
        results = store.search(np.array([1, 0, 0], dtype=np.float32))
        assert results == []


class TestTextChunker:
    """文本分块测试"""

    def test_basic_chunking(self):
        chunker = TextChunker(chunk_size=100, overlap=20)
        text = "段落一。\n\n段落二。\n\n段落三。"
        chunks = chunker.chunk(text)
        assert len(chunks) >= 1
        assert chunks[0].index == 0

    def test_empty_text(self):
        chunker = TextChunker()
        assert chunker.chunk("") == []
        assert chunker.chunk("   ") == []

    def test_long_paragraph_split(self):
        chunker = TextChunker(chunk_size=50, overlap=10)
        long_text = "。".join([f"这是第{i}个句子" for i in range(20)])
        chunks = chunker.chunk(long_text)
        assert len(chunks) > 1

    def test_metadata_preserved(self):
        chunker = TextChunker(chunk_size=100)
        chunks = chunker.chunk("一些文本", metadata={"source": "test.txt"})
        assert all(c.metadata.get("source") == "test.txt" for c in chunks)


class TestDocumentLoader:
    """文档加载器测试"""

    def test_load_txt(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Hello World", encoding="utf-8")
        loader = DocumentLoader()
        text = loader.load(str(f))
        assert text == "Hello World"

    def test_load_md(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("# Title\n\nContent", encoding="utf-8")
        loader = DocumentLoader()
        text = loader.load(str(f))
        assert "Title" in text

    def test_unsupported_format(self, tmp_path):
        f = tmp_path / "test.xyz"
        f.write_text("data")
        loader = DocumentLoader()
        with pytest.raises(ValueError):
            loader.load(str(f))

    def test_load_bytes_txt(self):
        loader = DocumentLoader()
        text = loader.load_bytes(b"Hello", "test.txt")
        assert text == "Hello"
