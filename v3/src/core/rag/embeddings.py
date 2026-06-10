"""向量嵌入 - 调用 LLM API 生成文本向量"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import List

import httpx
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """嵌入向量提供者基类"""

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[np.ndarray]:
        ...

    @abstractmethod
    def dimension(self) -> int:
        ...


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """
    OpenAI 兼容的 Embedding API
    支持 text-embedding-ada-002 / text-embedding-3-small 等
    也支持其他兼容接口（星火、DeepSeek 等）
    """

    def __init__(self, api_key: str, base_url: str, model: str = "text-embedding-ada-002"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._dimension = 1536  # ada-002 default

    async def embed(self, texts: List[str]) -> List[np.ndarray]:
        if not texts:
            return []

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "input": texts,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/embeddings",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

        embeddings = []
        for item in sorted(data["data"], key=lambda x: x["index"]):
            vec = np.array(item["embedding"], dtype=np.float32)
            embeddings.append(vec)

        if embeddings:
            self._dimension = len(embeddings[0])

        return embeddings

    def dimension(self) -> int:
        return self._dimension


class LocalEmbeddingProvider(EmbeddingProvider):
    """
    本地 TF-IDF 嵌入（零依赖降级方案）

    当没有 API 可用时，用 TF-IDF 做简单向量化。
    效果不如 API，但能保证流程跑通。

    TODO: 替换为真正的 Embedding API
      - 星火: https://spark-api-open.xf-yun.com/v1/embeddings
      - 或其他 OpenAI 兼容的 Embedding 接口
      - 配置 EMBEDDING_API_KEY / EMBEDDING_BASE_URL / EMBEDDING_MODEL 即可自动切换
    """

    def __init__(self, dimension: int = 384):
        self._dimension = dimension
        self._vocab: dict[str, int] = {}
        self._idf: dict[str, float] = {}
        self._doc_count = 0

    async def embed(self, texts: List[str]) -> List[np.ndarray]:
        if not texts:
            return []

        # 建立词表（增量）
        for text in texts:
            tokens = self._tokenize(text)
            seen = set()
            for token in tokens:
                if token not in seen:
                    self._doc_count += 1
                    seen.add(token)
                if token not in self._vocab:
                    self._vocab[token] = len(self._vocab)

        # 计算 IDF
        from collections import Counter
        doc_freq: Counter = Counter()
        for text in texts:
            tokens = set(self._tokenize(text))
            for token in tokens:
                doc_freq[token] += 1

        import math
        total = max(self._doc_count, 1)
        for token, freq in doc_freq.items():
            self._idf[token] = math.log((total + 1) / (freq + 1)) + 1

        results = []
        for text in texts:
            vec = self._text_to_vec(text)
            results.append(vec)
        return results

    def dimension(self) -> int:
        return self._dimension

    def _tokenize(self, text: str) -> List[str]:
        import re
        # 中文按字分，英文按词分
        text = text.lower()
        tokens = re.findall(r'[一-鿿]|[a-z0-9]+', text)
        return tokens

    def _text_to_vec(self, text: str) -> np.ndarray:
        from collections import Counter
        tokens = self._tokenize(text)
        tf = Counter(tokens)
        total = max(len(tokens), 1)

        vec = np.zeros(self._dimension, dtype=np.float32)
        for token, count in tf.items():
            idx = self._vocab.get(token)
            if idx is None:
                continue
            # hash 到 dimension 维度
            pos = hash(token) % self._dimension
            tfidf = (count / total) * self._idf.get(token, 1.0)
            vec[pos] += tfidf

        # L2 normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec


def create_embedding_provider(
    provider: str = "local",
    api_key: str = "",
    base_url: str = "",
    model: str = "text-embedding-ada-002",
) -> EmbeddingProvider:
    """工厂方法：根据配置创建嵌入提供者"""
    if provider == "openai" and api_key and base_url:
        return OpenAIEmbeddingProvider(api_key=api_key, base_url=base_url, model=model)
    else:
        logger.warning("无可用 Embedding API，使用本地 TF-IDF 方案")
        return LocalEmbeddingProvider()
