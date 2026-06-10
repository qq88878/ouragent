"""向量存储 - 内存实现，支持余弦相似度检索"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """一个文档块"""
    id: str
    content: str
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class VectorStore:
    """
    内存向量存储

    用 numpy 做余弦相似度检索，支持持久化到 JSON。
    生产环境可替换为 Milvus/FAISS，接口不变。
    """

    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self._documents: List[Document] = []
        self._embeddings: Optional[np.ndarray] = None  # shape: (n, dimension)
        self._dirty = True

    def add(self, doc: Document) -> None:
        if doc.embedding is None:
            raise ValueError("Document must have an embedding before adding to store")
        self._documents.append(doc)
        self._dirty = True

    def add_batch(self, docs: List[Document]) -> int:
        count = 0
        for doc in docs:
            if doc.embedding is not None:
                self._documents.append(doc)
                count += 1
        if count > 0:
            self._dirty = True
        return count

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[tuple[Document, float]]:
        """返回 (document, similarity_score) 列表，按相似度降序"""
        if not self._documents:
            return []

        self._rebuild_matrix()

        # 余弦相似度
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
        similarities = self._embeddings @ query_norm

        top_k = min(top_k, len(self._documents))
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score > 0:
                results.append((self._documents[idx], score))
        return results

    def delete_by_source(self, source: str) -> int:
        """删除指定来源的所有文档块"""
        before = len(self._documents)
        self._documents = [d for d in self._documents if d.metadata.get("source") != source]
        removed = before - len(self._documents)
        if removed > 0:
            self._dirty = True
        return removed

    def delete_by_knowledge_id(self, knowledge_id: int) -> int:
        before = len(self._documents)
        self._documents = [
            d for d in self._documents
            if d.metadata.get("knowledge_id") != knowledge_id
        ]
        removed = before - len(self._documents)
        if removed > 0:
            self._dirty = True
        return removed

    def count(self) -> int:
        return len(self._documents)

    def save(self, path: str) -> None:
        data = []
        for doc in self._documents:
            data.append({
                "id": doc.id,
                "content": doc.content,
                "embedding": doc.embedding.tolist() if doc.embedding is not None else None,
                "metadata": doc.metadata,
            })
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        logger.info("Vector store saved: %d documents -> %s", len(data), path)

    def load(self, path: str) -> int:
        p = Path(path)
        if not p.exists():
            return 0
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._documents = []
        for item in data:
            emb = np.array(item["embedding"], dtype=np.float32) if item["embedding"] else None
            self._documents.append(Document(
                id=item["id"],
                content=item["content"],
                embedding=emb,
                metadata=item.get("metadata", {}),
            ))
        self._dirty = True
        logger.info("Vector store loaded: %d documents from %s", len(self._documents), path)
        return len(self._documents)

    def _rebuild_matrix(self):
        if not self._dirty:
            return
        embeddings = []
        for doc in self._documents:
            if doc.embedding is not None:
                embeddings.append(doc.embedding)
            else:
                embeddings.append(np.zeros(self.dimension, dtype=np.float32))
        self._embeddings = np.array(embeddings, dtype=np.float32)
        # L2 normalize
        norms = np.linalg.norm(self._embeddings, axis=1, keepdims=True) + 1e-10
        self._embeddings = self._embeddings / norms
        self._dirty = False
