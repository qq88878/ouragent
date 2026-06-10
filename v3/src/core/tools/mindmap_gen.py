"""思维导图生成工具 - 将知识结构化为树形图"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from .base import Tool

logger = logging.getLogger(__name__)


class MindmapGenTool(Tool):
    """
    思维导图生成工具

    调用 LLM 将主题知识点整理为树形结构，输出 JSON 格式，
    前端可直接渲染为思维导图。
    """

    name = "mindmap_generator"
    description = "将知识点整理为思维导图结构（JSON 树形格式）"
    parameters = {
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "思维导图主题"},
            "depth": {"type": "integer", "description": "展开层级，默认 3"},
            "context": {"type": "string", "description": "参考知识内容"},
        },
        "required": ["topic"],
    }

    def __init__(self, llm):
        self.llm = llm

    async def execute(
        self,
        topic: str,
        depth: int = 3,
        context: str = "",
        **kwargs,
    ) -> Dict[str, Any]:
        prompt = f"""你是一位教育专家。请为以下主题生成思维导图。

主题: {topic}
展开层级: {depth}

参考知识:
{context if context else "（无参考知识）"}

请严格按照以下 JSON 格式输出，不要输出其他内容:
{{
  "topic": "主题名称",
  "children": [
    {{
      "name": "子主题1",
      "children": [
        {{"name": "要点1", "children": []}},
        {{"name": "要点2", "children": []}}
      ]
    }},
    {{
      "name": "子主题2",
      "children": []
    }}
  ]
}}
"""

        messages = [
            {"role": "system", "content": "你是一个知识结构化专家，只输出JSON格式的思维导图。"},
            {"role": "user", "content": prompt},
        ]

        try:
            response = await self.llm.chat(messages, temperature=0.5)
            response = response.strip()
            if response.startswith("```"):
                response = response.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("LLM 返回的思维导图不是有效 JSON")
            return {"topic": topic, "children": [], "raw_response": response}
        except Exception as e:
            logger.error("思维导图生成失败: %s", e)
            return {"topic": topic, "children": [], "error": str(e)}
