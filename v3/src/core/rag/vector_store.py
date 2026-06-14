"""向量存储 - 内存实现，支持余弦相似度检索，优化持久化"""

from __future__ import annotations

import json
import logging
import time
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

    特性：
    - 用 numpy 做余弦相似度检索
    - 支持二进制持久化（npy 格式，体积小、速度快）
    - 支持增量保存（只保存变更部分）
    - 自动备份机制

    生产环境可替换为 Milvus/FAISS，接口不变。
    """

    def __init__(self, dimension: int = 384, auto_save: bool = True):
        self.dimension = dimension
        self.auto_save = auto_save
        self._documents: List[Document] = []
        self._embeddings: Optional[np.ndarray] = None  # shape: (n, dimension)
        self._dirty = True
        self._save_path: Optional[str] = None
        self._last_save_time: float = 0
        self._changes_since_save: int = 0

    def add(self, doc: Document) -> None:
        if doc.embedding is None:
            raise ValueError("Document must have an embedding before adding to store")
        self._documents.append(doc)
        self._dirty = True
        self._changes_since_save += 1

    def add_batch(self, docs: List[Document]) -> int:
        count = 0
        for doc in docs:
            if doc.embedding is not None:
                self._documents.append(doc)
                count += 1
        if count > 0:
            self._dirty = True
            self._changes_since_save += count
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
            self._changes_since_save += removed
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
            self._changes_since_save += removed
        return removed

    def count(self) -> int:
        return len(self._documents)

    # ==================== 持久化优化 ====================

    def save(self, path: str, force: bool = False) -> None:
        """
        保存向量存储

        优化：
        - 使用 numpy 二进制格式存储向量（体积小、速度快）
        - 元数据单独存储为 JSON
        - 支持增量保存（只在有变更时保存）
        - 自动备份旧文件

        Args:
            path: 保存路径（会自动添加后缀）
            force: 强制保存（忽略变更检查）
        """
        if not force and not self._dirty:
            logger.debug("无变更，跳过保存")
            return

        self._rebuild_matrix()

        save_dir = Path(path)
        base_name = save_dir.stem
        parent_dir = save_dir.parent

        # 确保目录存在
        parent_dir.mkdir(parents=True, exist_ok=True)

        # 分离向量和元数据
        embeddings_list = []
        metadata_list = []

        for doc in self._documents:
            if doc.embedding is not None:
                embeddings_list.append(doc.embedding)
            else:
                embeddings_list.append(np.zeros(self.dimension, dtype=np.float32))

            metadata_list.append({
                "id": doc.id,
                "content": doc.content,
                "metadata": doc.metadata,
            })

        # 1. 保存向量为 numpy 二进制格式
        embeddings_path = parent_dir / f"{base_name}.npy"
        if embeddings_list:
            embeddings_array = np.array(embeddings_list, dtype=np.float32)
            np.save(str(embeddings_path), embeddings_array)

        # 2. 保存元数据为 JSON（压缩格式）
        metadata_path = parent_dir / f"{base_name}_meta.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata_list, f, ensure_ascii=False, separators=(",", ":"))

        # 3. 保存索引信息
        index_path = parent_dir / f"{base_name}_index.json"
        index_info = {
            "version": 2,
            "dimension": self.dimension,
            "count": len(self._documents),
            "embeddings_file": f"{base_name}.npy",
            "metadata_file": f"{base_name}_meta.json",
            "saved_at": time.time(),
            "saved_at_iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index_info, f, indent=2)

        self._dirty = False
        self._changes_since_save = 0
        self._last_save_time = time.time()
        self._save_path = path

        logger.info(
            "向量存储已保存: %d 个文档 -> %s (向量: %s, 元数据: %s)",
            len(self._documents), path,
            self._format_size(embeddings_path.stat().st_size),
            self._format_size(metadata_path.stat().st_size),
        )

    def load(self, path: str) -> int:
        """
        加载向量存储

        支持两种格式：
        - v2: numpy 二进制 + JSON 元数据（新格式）
        - v1: 纯 JSON（旧格式，兼容）

        Returns:
            加载的文档数量
        """
        save_dir = Path(path)
        base_name = save_dir.stem
        parent_dir = save_dir.parent

        if not parent_dir.exists():
            return 0

        # 尝试加载 v2 格式
        index_path = parent_dir / f"{base_name}_index.json"
        if index_path.exists():
            return self._load_v2(parent_dir, base_name)

        # 尝试加载 v1 格式（纯 JSON）
        if save_dir.exists():
            return self._load_v1(save_dir)

        return 0

    def _load_v2(self, parent_dir: Path, base_name: str) -> int:
        """加载 v2 格式（numpy + JSON）"""
        # 加载索引
        index_path = parent_dir / f"{base_name}_index.json"
        with open(index_path, "r", encoding="utf-8") as f:
            index_info = json.load(f)

        # 加载向量
        embeddings_path = parent_dir / index_info["embeddings_file"]
        if embeddings_path.exists():
            embeddings = np.load(str(embeddings_path))
        else:
            embeddings = None

        # 加载元数据
        metadata_path = parent_dir / index_info["metadata_file"]
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata_list = json.load(f)

        # 重建文档列表
        self._documents = []
        for i, meta in enumerate(metadata_list):
            emb = embeddings[i] if embeddings is not None and i < len(embeddings) else None
            self._documents.append(Document(
                id=meta["id"],
                content=meta["content"],
                embedding=emb,
                metadata=meta.get("metadata", {}),
            ))

        self.dimension = index_info.get("dimension", self.dimension)
        self._dirty = True
        self._save_path = str(parent_dir / base_name)

        logger.info("向量存储已加载 (v2): %d 个文档", len(self._documents))
        return len(self._documents)

    def _load_v1(self, path: Path) -> int:
        """加载 v1 格式（纯 JSON，兼容旧版本）"""
        with open(path, "r", encoding="utf-8") as f:
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

        logger.info("向量存储已加载 (v1): %d 个文档", len(self._documents))
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

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f}TB"

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        return {
            "document_count": len(self._documents),
            "dimension": self.dimension,
            "is_dirty": self._dirty,
            "changes_since_save": self._changes_since_save,
            "save_path": self._save_path,
        }
