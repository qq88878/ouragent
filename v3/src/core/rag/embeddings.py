"""向量嵌入 - 调用 LLM API 或本地模型生成文本向量"""

from __future__ import annotations

import logging
import math
from abc import ABC, abstractmethod
from typing import List, Optional

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


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """
    基于 sentence-transformers 的本地嵌入

    优点：
    - 真正的语义嵌入，检索质量高
    - 支持中英文
    - 无需 API 调用

    缺点：
    - 需要下载模型（首次使用）
    - 推理速度较慢（CPU）
    """

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self.model_name = model_name
        self._model = None
        self._dimension = 384  # MiniLM default

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info("加载 SentenceTransformer 模型: %s", self.model_name)
                self._model = SentenceTransformer(self.model_name)
                self._dimension = self._model.get_sentence_embedding_dimension()
                logger.info("模型加载完成，维度: %d", self._dimension)
            except ImportError:
                raise ImportError("sentence-transformers 未安装，请运行: pip install sentence-transformers")
            except Exception as e:
                logger.error("模型加载失败: %s", e)
                raise

    async def embed(self, texts: List[str]) -> List[np.ndarray]:
        if not texts:
            return []

        self._load_model()

        # sentence-transformers 是同步的，在线程池中运行
        import asyncio
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False),
        )

        return [np.array(emb, dtype=np.float32) for emb in embeddings]

    def dimension(self) -> int:
        return self._dimension


class ImprovedLocalEmbeddingProvider(EmbeddingProvider):
    """
    改进的本地 TF-IDF 嵌入

    改进点：
    - 使用 jieba 分词，提高中文分词质量
    - 使用特征哈希（Feature Hashing）减少碰撞
    - 支持 n-gram 特征
    """

    def __init__(self, dimension: int = 384, ngram_range: tuple = (1, 2)):
        self._dimension = dimension
        self._ngram_range = ngram_range
        self._idf: dict[str, float] = {}
        self._doc_count = 0
        self._vocab_size = 10000  # 限制词表大小

    async def embed(self, texts: List[str]) -> List[np.ndarray]:
        if not texts:
            return []

        # 计算 IDF
        self._update_idf(texts)

        # 生成向量
        results = []
        for text in texts:
            vec = self._text_to_vec(text)
            results.append(vec)
        return results

    def dimension(self) -> int:
        return self._dimension

    def _tokenize(self, text: str) -> List[str]:
        """使用 jieba 分词"""
        try:
            import jieba
            # jieba 分词
            tokens = list(jieba.cut(text.lower()))
            # 过滤短词和停用词
            tokens = [t.strip() for t in tokens if len(t.strip()) > 1]
            return tokens
        except ImportError:
            # 降级到简单分词
            import re
            text = text.lower()
            tokens = re.findall(r'[一-鿿]{2,}|[a-z0-9]{2,}', text)
            return tokens

    def _get_ngrams(self, tokens: List[str]) -> List[str]:
        """生成 n-gram 特征"""
        ngrams = []
        for n in range(self._ngram_range[0], self._ngram_range[1] + 1):
            for i in range(len(tokens) - n + 1):
                ngram = "_".join(tokens[i:i + n])
                ngrams.append(ngram)
        return ngrams

    def _update_idf(self, texts: List[str]):
        """更新 IDF 统计"""
        from collections import Counter
        doc_freq: Counter = Counter()

        for text in texts:
            tokens = self._tokenize(text)
            ngrams = self._get_ngrams(tokens)
            unique_ngrams = set(ngrams)
            for ngram in unique_ngrams:
                doc_freq[ngram] += 1
                self._doc_count += 1

        for ngram, freq in doc_freq.items():
            self._idf[ngram] = math.log((self._doc_count + 1) / (freq + 1)) + 1

    def _text_to_vec(self, text: str) -> np.ndarray:
        """将文本转换为向量"""
        from collections import Counter

        tokens = self._tokenize(text)
        ngrams = self._get_ngrams(tokens)
        tf = Counter(ngrams)
        total = max(len(ngrams), 1)

        vec = np.zeros(self._dimension, dtype=np.float32)
        for ngram, count in tf.items():
            # 特征哈希：使用两个哈希函数减少碰撞
            hash1 = hash(ngram) % self._dimension
            hash2 = hash(ngram + "_salt") % self._dimension

            tfidf = (count / total) * self._idf.get(ngram, 1.0)

            # 交替使用正负值
            if hash2 % 2 == 0:
                vec[hash1] += tfidf
            else:
                vec[hash1] -= tfidf

        # L2 normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec


class LocalEmbeddingProvider(EmbeddingProvider):
    """
    基础本地 TF-IDF 嵌入（最后降级方案）

    当没有 API 可用且 jieba 未安装时使用。
    效果有限，但能保证流程跑通。
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
    """
    工厂方法：根据配置创建嵌入提供者

    优先级：
    1. OpenAI 兼容 API（如果有配置）
    2. SentenceTransformer（如果已安装）
    3. 改进的本地 TF-IDF（如果 jieba 已安装）
    4. 基础本地 TF-IDF（最后降级）
    """
    if provider == "openai" and api_key and base_url:
        logger.info("使用 OpenAI Embedding API: %s", model)
        return OpenAIEmbeddingProvider(api_key=api_key, base_url=base_url, model=model)

    # 尝试 SentenceTransformer
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("使用 SentenceTransformer 本地嵌入")
        return SentenceTransformerEmbeddingProvider()
    except ImportError:
        pass

    # 尝试改进的本地方案
    try:
        import jieba
        logger.info("使用改进的本地 TF-IDF 嵌入（jieba 分词）")
        return ImprovedLocalEmbeddingProvider()
    except ImportError:
        pass

    # 最后降级
    logger.warning("无可用 Embedding API，使用基础本地 TF-IDF 方案")
    return LocalEmbeddingProvider()
