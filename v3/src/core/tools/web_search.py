"""网络搜索工具 - 当知识库无结果时降级使用"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from .base import Tool

logger = logging.getLogger(__name__)


class WebSearchTool(Tool):
    """
    网络搜索工具

    当知识库检索不到相关内容时，使用 DuckDuckGo 搜索补充信息。
    无需 API Key，但结果质量不如 Google/Bing。
    """

    name = "web_search"
    description = "搜索互联网获取最新信息，当知识库中没有相关内容时使用"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词"},
            "max_results": {"type": "integer", "description": "最大结果数，默认 3"},
        },
        "required": ["query"],
    }

    async def execute(self, query: str, max_results: int = 3, **kwargs) -> List[Dict[str, str]]:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            logger.warning("duckduckgo-search 未安装")
            return [{"title": "搜索不可用", "snippet": "请安装 duckduckgo-search 包"}]

        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            return [
                {"title": r.get("title", ""), "snippet": r.get("body", "")}
                for r in results
            ]
        except Exception as e:
            logger.error("网络搜索失败: %s", e)
            return [{"title": "搜索失败", "snippet": str(e)}]
