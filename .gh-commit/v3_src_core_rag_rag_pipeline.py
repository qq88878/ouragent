"""RAG Pipeline - 文档入库 + 检索增强生成的完整流程"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from .chunker import TextChunker
from .document_loader import DocumentLoader
from .embeddings import EmbeddingProvider
from .vector_store import VectorStore, Document

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    RAG 完整管线

    入库流程: 文件 -> 提取文本 -> 分块 -> 向量化 -> 存入 VectorStore
    检索流程: 用户问题 -> 向量化 -> 相似度搜索 -> 返回相关文档块
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.loader = DocumentLoader()
        self.chunker = TextChunker(chunk_size=chunk_size, overlap=chunk_overlap)

    async def ingest_text(
        self,
        text: str,
        source: str,
        knowledge_id: Optional[int] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """将文本入库，返回分块数量"""
        metadata = {"source": source}
        if knowledge_id is not None:
            metadata["knowledge_id"] = knowledge_id
        if extra_metadata:
            metadata.update(extra_metadata)

        chunks = self.chunker.chunk(text, metadata)
        if not chunks:
            logger.warning("文档 %s 分块后为空", source)
            return 0

        # 批量生成嵌入向量
        texts = [c.content for c in chunks]
        embeddings = await self.embedding_provider.embed(texts)

        # 构建 Document 并存入向量存储
        docs = []
        for chunk, embedding in zip(chunks, embeddings):
            doc = Document(
                id=str(uuid.uuid4()),
                content=chunk.content,
                embedding=embedding,
                metadata={**chunk.metadata, "chunk_index": chunk.index},
            )
            docs.append(doc)

        count = self.vector_store.add_batch(docs)
        logger.info("文档 %s 入库完成: %d 块", source, count)
        return count

    async def ingest_file(
        self,
        file_path: str,
        knowledge_id: Optional[int] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """从文件路径入库"""
        text = self.loader.load(file_path)
        return await self.ingest_text(
            text=text,
            source=file_path,
            knowledge_id=knowledge_id,
            extra_metadata=extra_metadata,
        )

    async def ingest_bytes(
        self,
        content: bytes,
        filename: str,
        knowledge_id: Optional[int] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """从上传的文件字节入库"""
        text = self.loader.load_bytes(content, filename)
        return await self.ingest_text(
            text=text,
            source=filename,
            knowledge_id=knowledge_id,
            extra_metadata=extra_metadata,
        )

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        knowledge_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        检索与查询最相关的文档块

        Args:
            query: 用户问题
            top_k: 返回数量
            knowledge_ids: 限定在哪些知识库文档中检索（可选）

        Returns:
            [{"content": "...", "score": 0.85, "source": "...", "knowledge_id": 1}, ...]
        """
        query_embedding = (await self.embedding_provider.embed([query]))[0]
        results = self.vector_store.search(query_embedding, top_k=top_k * 2)

        filtered = []
        for doc, score in results:
            # 如果指定了 knowledge_ids，过滤不相关的文档
            if knowledge_ids:
                doc_kid = doc.metadata.get("knowledge_id")
                if doc_kid not in knowledge_ids:
                    continue
            filtered.append({
                "content": doc.content,
                "score": score,
                "source": doc.metadata.get("source", ""),
                "knowledge_id": doc.metadata.get("knowledge_id"),
                "chunk_index": doc.metadata.get("chunk_index", 0),
            })
            if len(filtered) >= top_k:
                break

        return filtered

    def delete_source(self, source: str) -> int:
        return self.vector_store.delete_by_source(source)

    def delete_knowledge(self, knowledge_id: int) -> int:
        return self.vector_store.delete_by_knowledge_id(knowledge_id)

    def stats(self) -> Dict[str, Any]:
        return {
            "total_chunks": self.vector_store.count(),
            "embedding_provider": type(self.embedding_provider).__name__,
            "chunk_size": self.chunker.chunk_size,
        }
