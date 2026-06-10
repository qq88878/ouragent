"""文本分块 - 将长文档切分为可检索的小块"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List


@dataclass
class Chunk:
    content: str
    index: int
    metadata: dict


class TextChunker:
    """
    文本分块器

    策略：按段落优先分割，保证每块在 chunk_size 附近，
    相邻块之间有 overlap 重叠以保持上下文连贯。
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, metadata: dict | None = None) -> List[Chunk]:
        if not text or not text.strip():
            return []

        metadata = metadata or {}
        paragraphs = self._split_paragraphs(text)
        chunks: List[Chunk] = []
        current = ""
        chunk_idx = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # 段落本身超过 chunk_size，单独分块
            if len(para) > self.chunk_size:
                if current:
                    chunks.append(Chunk(content=current.strip(), index=chunk_idx, metadata=metadata))
                    chunk_idx += 1
                    current = ""
                # 按句子切大段落
                for sub in self._split_by_sentences(para):
                    if len(current) + len(sub) + 1 > self.chunk_size and current:
                        chunks.append(Chunk(content=current.strip(), index=chunk_idx, metadata=metadata))
                        chunk_idx += 1
                        current = current[-self.overlap:] if self.overlap else ""
                    current += sub + "\n"
            elif len(current) + len(para) + 1 > self.chunk_size:
                chunks.append(Chunk(content=current.strip(), index=chunk_idx, metadata=metadata))
                chunk_idx += 1
                current = current[-self.overlap:] if self.overlap else ""
                current += para + "\n"
            else:
                current += para + "\n"

        if current.strip():
            chunks.append(Chunk(content=current.strip(), index=chunk_idx, metadata=metadata))

        return chunks

    def _split_paragraphs(self, text: str) -> List[str]:
        return re.split(r'\n\s*\n', text)

    def _split_by_sentences(self, text: str) -> List[str]:
        sentences = re.split(r'(?<=[。！？.!?])\s*', text)
        return [s for s in sentences if s.strip()]
