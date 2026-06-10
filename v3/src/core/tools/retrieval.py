"""检索工具 - 从知识库中检索相关文档块"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base import Tool


class RetrievalTool(Tool):
    """
    知识库检索工具

    基于用户问题和学生画像，从 RAG Pipeline 中检索最相关的知识片段，
    为 LLM 生成个性化回答提供上下文。
    """

    name = "knowledge_retrieval"
    description = "从课程知识库中检索与问题相关的文档片段"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "检索查询文本"},
            "knowledge_ids": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "限定检索范围的知识库文档 ID 列表（可选）",
            },
            "top_k": {"type": "integer", "description": "返回结果数量，默认 5"},
        },
        "required": ["query"],
    }

    def __init__(self, rag_pipeline):
        self.rag = rag_pipeline

    async def execute(
        self,
        query: str,
        knowledge_ids: Optional[List[int]] = None,
        top_k: int = 5,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        return await self.rag.retrieve(
            query=query,
            top_k=top_k,
            knowledge_ids=knowledge_ids,
        )
