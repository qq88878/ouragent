"""向量存储 - FAISS 实现，支持余弦相似度检索，高性能持久化"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False

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
    FAISS 向量存储

    特性：
    - 用 FAISS IndexFlatIP 做余弦相似度检索（L2 归一化后内积 = 余弦相似度）
    - 支持二进制持久化（FAISS 索引 + JSON 元数据）
    - 删除操作通过重建索引实现
    - 向下兼容旧格式（v1 JSON / v2 numpy）

    接口与原 numpy 实现完全一致，RAGPipeline 无需修改。
    """

    def __init__(self, dimension: int = 384, auto_save: bool = True):
        self.dimension = dimension
        self.auto_save = auto_save
        self._documents: List[Document] = []
        self._index: Optional[faiss.Index] = None
        self._dirty = True
        self._save_path: Optional[str] = None
        self._last_save_time: float = 0
        self._changes_since_save: int = 0
        self._use_faiss = HAS_FAISS

        if not HAS_FAISS:
            logger.warning("faiss 未安装，回退到 numpy 实现。请运行: pip install faiss-cpu")

    def _ensure_index(self) -> None:
        """确保 FAISS 索引存在并同步"""
        if not self._use_faiss:
            return

        if not self._dirty and self._index is not None:
            return

        if not self._documents:
            self._index = faiss.IndexFlatIP(self.dimension)
            self._dirty = False
            return

        # 构建向量矩阵
        embeddings = []
        for doc in self._documents:
            if doc.embedding is not None:
                embeddings.append(doc.embedding)
            else:
                embeddings.append(np.zeros(self.dimension, dtype=np.float32))

        matrix = np.array(embeddings, dtype=np.float32)
        if matrix.ndim == 1:
            matrix = matrix.reshape(1, -1)

        # L2 归一化（内积 = 余弦相似度）
        faiss.normalize_L2(matrix)

        # 创建新的 FAISS 索引
        self._index = faiss.IndexFlatIP(self.dimension)
        self._index.add(matrix)
        self._dirty = False

        logger.debug("FAISS 索引已重建: %d 个向量", self._index.ntotal)

    def add(self, doc: Document) -> None:
        if doc.embedding is None:
            raise ValueError("Document must have an embedding before adding to store")

        self._documents.append(doc)
        self._dirty = True
        self._changes_since_save += 1

        # 增量添加到 FAISS 索引（如果索引已存在）
        if self._use_faiss and self._index is not None and not self._dirty:
            vec = doc.embedding.reshape(1, -1).astype(np.float32)
            faiss.normalize_L2(vec)
            self._index.add(vec)

    def add_batch(self, docs: List[Document]) -> int:
        count = 0
        new_embeddings = []

        for doc in docs:
            if doc.embedding is not None:
                self._documents.append(doc)
                new_embeddings.append(doc.embedding)
                count += 1

        if count > 0:
            self._dirty = True
            self._changes_since_save += count

            # 增量添加到 FAISS 索引
            if self._use_faiss and self._index is not None and not self._dirty:
                # 如果之前索引已同步，现在变脏了，需要重建
                self._dirty = True

        return count

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[tuple]:
        """返回 (document, similarity_score) 列表，按相似度降序"""
        if not self._documents:
            return []

        top_k = min(top_k, len(self._documents))

        if self._use_faiss:
            return self._search_faiss(query_embedding, top_k)
        else:
            return self._search_numpy(query_embedding, top_k)

    def _search_faiss(self, query_embedding: np.ndarray, top_k: int) -> List[tuple]:
        """FAISS 检索"""
        self._ensure_index()

        if self._index.ntotal == 0:
            return []

        # 查询向量归一化
        query = query_embedding.reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(query)

        # 检索
        scores, indices = self._index.search(query, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and score > 0:  # FAISS 返回 -1 表示无效
                results.append((self._documents[idx], float(score)))

        return results

    def _search_numpy(self, query_embedding: np.ndarray, top_k: int) -> List[tuple]:
        """numpy 回退检索"""
        embeddings = []
        for doc in self._documents:
            if doc.embedding is not None:
                embeddings.append(doc.embedding)
            else:
                embeddings.append(np.zeros(self.dimension, dtype=np.float32))

        matrix = np.array(embeddings, dtype=np.float32)
        if matrix.ndim == 1:
            matrix = matrix.reshape(1, -1)

        # L2 归一化
        norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10
        matrix = matrix / norms

        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
        similarities = matrix @ query_norm

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
            self._index = None  # 标记需要重建
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
            self._index = None  # 标记需要重建
        return removed

    def count(self) -> int:
        return len(self._documents)

    # ==================== 持久化 ====================

    def save(self, path: str, force: bool = False) -> None:
        """
        保存向量存储

        保存内容：
        - {stem}.faiss  -- FAISS 索引（二进制）
        - {stem}_meta.json -- 文档元数据
        - {stem}_index.json -- 版本/维度信息

        Args:
            path: 保存路径（会自动添加后缀）
            force: 强制保存（忽略变更检查）
        """
        if not force and not self._dirty:
            logger.debug("无变更，跳过保存")
            return

        # 确保 FAISS 索引同步
        if self._use_faiss:
            self._ensure_index()

        save_dir = Path(path)
        base_name = save_dir.stem
        parent_dir = save_dir.parent
        parent_dir.mkdir(parents=True, exist_ok=True)

        # 1. 保存 FAISS 索引
        if self._use_faiss and self._index is not None and self._index.ntotal > 0:
            faiss_path = parent_dir / f"{base_name}.faiss"
            faiss.write_index(self._index, str(faiss_path))
            logger.debug("FAISS 索引已保存: %s", faiss_path)

        # 2. 保存元数据
        metadata_list = []
        for doc in self._documents:
            metadata_list.append({
                "id": doc.id,
                "content": doc.content,
                "metadata": doc.metadata,
            })

        metadata_path = parent_dir / f"{base_name}_meta.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata_list, f, ensure_ascii=False, separators=(",", ":"))

        # 3. 保存索引信息
        index_path = parent_dir / f"{base_name}_index.json"
        index_info = {
            "version": 3,  # v3 = FAISS
            "dimension": self.dimension,
            "count": len(self._documents),
            "faiss_file": f"{base_name}.faiss",
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

        logger.info("向量存储已保存: %d 个文档 -> %s", len(self._documents), path)

    def load(self, path: str) -> int:
        """
        加载向量存储

        支持三种格式：
        - v3: FAISS 索引 + JSON 元数据（新格式）
        - v2: numpy 二进制 + JSON 元数据
        - v1: 纯 JSON（旧格式，兼容）

        Returns:
            加载的文档数量
        """
        save_dir = Path(path)
        base_name = save_dir.stem
        parent_dir = save_dir.parent

        if not parent_dir.exists():
            return 0

        # 尝试加载 v3 格式（FAISS）
        index_path = parent_dir / f"{base_name}_index.json"
        if index_path.exists():
            with open(index_path, "r", encoding="utf-8") as f:
                index_info = json.load(f)

            if index_info.get("version") == 3:
                return self._load_v3(parent_dir, base_name, index_info)
            else:
                return self._load_v2(parent_dir, base_name, index_info)

        # 尝试加载 v1 格式（纯 JSON）
        if save_dir.exists():
            return self._load_v1(save_dir)

        return 0

    def _load_v3(self, parent_dir: Path, base_name: str, index_info: dict) -> int:
        """加载 v3 格式（FAISS + JSON）"""
        # 加载元数据
        metadata_path = parent_dir / index_info["metadata_file"]
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata_list = json.load(f)

        self._documents = []
        for meta in metadata_list:
            self._documents.append(Document(
                id=meta["id"],
                content=meta["content"],
                embedding=None,  # FAISS 索引中已有向量，不需要单独存储
                metadata=meta.get("metadata", {}),
            ))

        # 加载 FAISS 索引
        faiss_path = parent_dir / index_info.get("faiss_file", f"{base_name}.faiss")
        if self._use_faiss and faiss_path.exists():
            self._index = faiss.read_index(str(faiss_path))
            self._dirty = False
            logger.info("向量存储已加载 (v3/FAISS): %d 个文档, 索引中 %d 个向量",
                       len(self._documents), self._index.ntotal)
        else:
            self._dirty = True
            logger.info("向量存储已加载 (v3/元数据): %d 个文档 (FAISS 索引将在首次检索时重建)",
                       len(self._documents))

        self.dimension = index_info.get("dimension", self.dimension)
        self._save_path = str(parent_dir / base_name)
        return len(self._documents)

    def _load_v2(self, parent_dir: Path, base_name: str, index_info: dict) -> int:
        """加载 v2 格式（numpy + JSON）→ 迁移到 FAISS"""
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
        self._dirty = True  # 需要重建 FAISS 索引
        self._save_path = str(parent_dir / base_name)

        logger.info("向量存储已加载 (v2→FAISS 迁移): %d 个文档", len(self._documents))
        return len(self._documents)

    def _load_v1(self, path: Path) -> int:
        """加载 v1 格式（纯 JSON）→ 迁移到 FAISS"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._documents = []
        for item in data:
            emb = np.array(item["embedding"], dtype=np.float32) if item.get("embedding") else None
            self._documents.append(Document(
                id=item["id"],
                content=item["content"],
                embedding=emb,
                metadata=item.get("metadata", {}),
            ))

        self._dirty = True  # 需要重建 FAISS 索引
        logger.info("向量存储已加载 (v1→FAISS 迁移): %d 个文档", len(self._documents))
        return len(self._documents)

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f}TB"

    def get_stats(self) -> Dict[str, Any]:
        return {
            "document_count": len(self._documents),
            "dimension": self.dimension,
            "is_dirty": self._dirty,
            "changes_since_save": self._changes_since_save,
            "save_path": self._save_path,
            "backend": "faiss" if self._use_faiss else "numpy",
            "faiss_index_size": self._index.ntotal if self._index else 0,
        }
