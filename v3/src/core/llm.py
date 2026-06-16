"""
LLM 调用抽象层
支持多种 LLM 提供商（星火、OpenAI 兼容接口）
"""

import json
import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator

import aiohttp

from config.settings import settings


class LLMProvider(ABC):
    """LLM 提供商基类"""

    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        发送对话请求

        Args:
            messages: [{"role": "system/user/assistant", "content": "..."}]

        Returns:
            LLM 回复文本
        """
        pass

    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """
        流式对话，默认回退到 chat() 一次性返回
        子类可覆盖以支持真正的流式输出
        """
        yield await self.chat(messages, **kwargs)


class SparkProvider(LLMProvider):
    """
    星火大模型（讯飞星火）
    使用 HTTP 接口调用，兼容星火 Lite/Pro/Max
    """

    def __init__(self):
        self.api_key = settings.SPARK_API_KEY
        self.api_secret = settings.SPARK_API_SECRET
        self.app_id = settings.SPARK_APP_ID
        self.model = settings.SPARK_MODEL
        self.base_url = settings.SPARK_BASE_URL

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """调用星火 API"""
        if not self.api_key:
            raise ValueError("SPARK_API_KEY 未配置")

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 2048),
            "temperature": kwargs.get("temperature", 0.7),
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=120),
            connector=aiohttp.TCPConnector(ssl=True),
        ) as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data['choices'][0]['message'].get('content') or data['choices'][0]['message'].get('reasoning_content', '')

    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """星火流式输出"""
        if not self.api_key:
            raise ValueError("SPARK_API_KEY 未配置")

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 2048),
            "temperature": kwargs.get("temperature", 0.7),
            "stream": True,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=120),
            connector=aiohttp.TCPConnector(ssl=True),
        ) as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.content:
                    line = line.decode("utf-8").strip()
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get('content') or delta.get('reasoning_content')
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue


class OpenAIProvider(LLMProvider):
    """
    OpenAI 兼容接口
    支持 OpenAI、DeepSeek、以及其它兼容接口
    """

    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL
        self.base_url = settings.LLM_BASE_URL

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """调用 OpenAI 兼容 API"""
        if not self.api_key:
            raise ValueError("LLM_API_KEY 未配置")

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 2048),
            "temperature": kwargs.get("temperature", 0.7),
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=120),
            connector=aiohttp.TCPConnector(ssl=True),
        ) as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data['choices'][0]['message'].get('content') or data['choices'][0]['message'].get('reasoning_content', '')

    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """OpenAI 兼容流式输出"""
        if not self.api_key:
            raise ValueError("LLM_API_KEY 未配置")

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 2048),
            "temperature": kwargs.get("temperature", 0.7),
            "stream": True,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=120),
            connector=aiohttp.TCPConnector(ssl=True),
        ) as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.content:
                    line = line.decode("utf-8").strip()
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get('content') or delta.get('reasoning_content')
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue


def create_llm_provider(provider: Optional[str] = None) -> LLMProvider:
    """
    根据配置创建 LLM 提供商实例

    Args:
        provider: 提供商名称，可选 "spark" 或 "openai"。默认从配置读取。

    Returns:
        LLMProvider 实例
    """
    provider = provider or settings.LLM_PROVIDER

    if provider == "spark":
        return SparkProvider()
    elif provider == "openai":
        return OpenAIProvider()
    else:
        raise ValueError(f"不支持的 LLM 提供商: {provider}")
