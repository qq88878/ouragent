"""动态话题关键词管理 — 从知识库导入时自动提取，Redis 存储，对话时合并静态词典

支持两种提取模式（可同时启用）：
  1. 规则提取（默认，零成本）—— 从标题 / metadata / 内容预览做关键词匹配
  2. LLM 提取（可选，需传入 LLMProvider）—— 让大模型理解文档语义，生成更精准的标签
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from .redis_client import RedisClient

logger = logging.getLogger(__name__)


def _extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """从 LLM 回复中提取 JSON（兼容 Markdown 代码块、前后多余文字等情况）"""
    if not text:
        return None
    # 优先尝试直接解析
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    # 匹配 ```json ... ``` 或 ``` ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except Exception:
            pass
    # 匹配第一个 { ... }
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return None

KEYWORDS_TTL = 30 * 24 * 3600  # 30 天
GLOBAL_KEY = "topic_keywords:global"
KNOWLEDGE_KEY_PREFIX = "topic_keywords:knowledge:"

# ── 静态基线词典：中英文词形归一映射 ────────────────
_NORMALIZE_MAP: Dict[str, str] = {
    # Python
    "列表": "Python列表", "list": "Python列表", "lists": "Python列表",
    "元组": "元组", "tuple": "元组", "tuples": "元组",
    "字典": "字典", "dict": "字典", "dictionaries": "字典",
    "集合": "集合", "set": "集合", "sets": "集合",
    "字符串": "字符串", "string": "字符串", "str": "字符串",
    "函数": "函数", "function": "函数", "functions": "函数", "func": "函数",
    "类": "面向对象", "class": "面向对象", "classes": "面向对象",
    "继承": "继承", "inheritance": "继承",
    "装饰器": "装饰器", "decorator": "装饰器", "decorators": "装饰器",
    "迭代器": "迭代器", "iterator": "迭代器", "iterators": "迭代器",
    "生成器": "生成器", "generator": "生成器", "yield": "生成器",
    "异常": "异常处理", "exception": "异常处理", "exceptions": "异常处理",
    "模块": "模块与包", "module": "模块与包", "modules": "模块与包",
    "文件": "文件操作", "file": "文件操作",
    "协程": "协程", "async": "协程", "await": "协程", "coroutine": "协程",
    "递归": "递归", "recursion": "递归", "recursive": "递归",
    "lambda": "Lambda表达式",
    # 数据结构与算法
    "算法": "算法", "algorithm": "算法", "algorithms": "算法",
    "排序": "排序算法", "sort": "排序算法",
    "搜索": "搜索算法", "search": "搜索算法",
    "二叉树": "二叉树", "binary tree": "二叉树", "btree": "二叉树",
    "链表": "链表", "linked list": "链表",
    "栈": "栈", "stack": "栈",
    "队列": "队列", "queue": "队列",
    "哈希": "哈希表", "hash": "哈希表", "hashmap": "哈希表",
    "图": "图论", "graph": "图论", "graphs": "图论",
    "动态规划": "动态规划", "dp": "动态规划",
    # 数据库
    "数据库": "数据库", "database": "数据库", "databases": "数据库", "db": "数据库",
    "sql": "SQL", "查询": "SQL查询",
    "索引": "数据库索引", "index": "数据库索引", "indexes": "数据库索引",
    "事务": "数据库事务", "transaction": "数据库事务",
    # 数学
    "方程": "方程", "equation": "方程",
    "矩阵": "矩阵", "matrix": "矩阵",
    "导数": "导数", "derivative": "导数",
    "积分": "积分", "integral": "积分",
    "概率": "概率", "probability": "概率",
    "统计": "统计学", "statistics": "统计学",
    "线性代数": "线性代数", "linear algebra": "线性代数",
    # Web
    "html": "HTML",
    "css": "CSS",
    "javascript": "JavaScript", "js": "JavaScript",
    "前端": "前端开发", "frontend": "前端开发",
    "api": "API接口", "接口": "API接口",
    "http": "HTTP协议", "https": "HTTP协议",
    # 通用
    "变量": "变量", "variable": "变量",
    "循环": "循环", "loop": "循环", "for": "循环", "while": "循环",
    "数组": "数组", "array": "数组",
    "指针": "指针", "pointer": "指针",
    "进程": "进程", "process": "进程",
    "线程": "线程", "thread": "线程",
    "网络": "计算机网络", "network": "计算机网络",
    "操作系统": "操作系统", "operating system": "操作系统",
}

# 中文同义词扩展
_CN_NORMALIZE_MAP: Dict[str, str] = {
    "函数定义": "函数", "方法": "函数",
    "类定义": "面向对象", "面向对象编程": "面向对象", "oop": "面向对象",
    "子类": "继承", "父类": "继承",
    "装饰器模式": "装饰器", "包装函数": "装饰器",
    "迭代": "迭代器", "可迭代": "迭代器",
    "生成器函数": "生成器",
    "异常捕获": "异常处理", "错误处理": "异常处理",
    "模块导入": "模块与包", "包管理": "模块与包",
    "文件读写": "文件操作", "文件处理": "文件操作",
    "正则匹配": "正则表达式",
    "多线程编程": "多线程", "并发": "多线程",
    "异步编程": "协程", "asyncio": "协程", "异步": "协程",
    "递归调用": "递归",
    "匿名函数": "Lambda表达式",
    "算法题": "算法", "算法设计": "算法",
    "排序算法": "排序算法",
    "树": "二叉树", "树结构": "二叉树",
    "链表操作": "链表",
    "栈操作": "栈",
    "队列操作": "队列",
    "散列表": "哈希表",
    "图算法": "图论",
    "数据库操作": "数据库",
    "索引优化": "数据库索引",
    "事务处理": "数据库事务",
    "网页": "HTML", "样式": "CSS",
    "脚本": "JavaScript",
}


def get_static_keywords() -> Dict[str, str]:
    """获取静态基线关键词字典（keyword -> canonical_name）"""
    merged: Dict[str, str] = {}
    for k, v in _NORMALIZE_MAP.items():
        merged[k] = v
    for k, v in _CN_NORMALIZE_MAP.items():
        merged[k] = v
    return merged


def _extract_from_title(title: str) -> Dict[str, str]:
    """从文档标题中提取关键词 -> 规范名 映射"""
    result: Dict[str, str] = {}
    text = title.strip().lower()

    # 去掉扩展名
    for ext in (".pdf", ".txt", ".md", ".docx", ".doc", ".pptx", ".xlsx", ".html"):
        if text.endswith(ext):
            text = text[: -len(ext)]

    # 匹配已有映射表中的词汇
    for word, canonical in _NORMALIZE_MAP.items():
        if word in text:
            result[word] = canonical
            result[canonical.lower()] = canonical
    for word, canonical in _CN_NORMALIZE_MAP.items():
        if word.lower() in text:
            result[word.lower()] = canonical

    # 标题本身也是关键词
    clean_title = re.sub(r"[_\-\(\)\[\]（）【】《》「」『』]+", " ", title).strip()
    if 2 <= len(clean_title) <= 30:
        result[clean_title.lower()] = clean_title

    # 从标题中提取 2~10 个字的中文/英文短语
    for match in re.findall(r"[\u4e00-\u9fa5A-Za-z]{2,10}", clean_title):
        if 2 <= len(match) <= 15:
            result[match.lower()] = match

    return result


def _extract_from_metadata(metadata: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """从 metadata（tags、category、topics 等）中提取关键词"""
    if not metadata:
        return {}
    result: Dict[str, str] = {}
    for key in ("tags", "tag", "categories", "category", "topics", "topic",
                "keywords", "subject", "chapter", "section"):
        if key not in metadata:
            continue
        value = metadata[key]
        if isinstance(value, str):
            items = [v.strip() for v in re.split(r"[,，;；|/]", value) if v.strip()]
        elif isinstance(value, (list, tuple)):
            items = [str(v).strip() for v in value if v]
        else:
            continue
        for item in items:
            if 2 <= len(item) <= 30:
                canonical = _NORMALIZE_MAP.get(item.lower(), None) or \
                            _CN_NORMALIZE_MAP.get(item.lower(), None) or item
                result[item.lower()] = canonical
    return result


def _extract_from_preview(text_preview: str, max_keywords: int = 8) -> Dict[str, str]:
    """从文档前 500 字中提取已登记的关键词"""
    if not text_preview:
        return {}
    text = text_preview[:500].lower()
    result: Dict[str, str] = {}
    for word, canonical in _NORMALIZE_MAP.items():
        if word in text:
            result[word] = canonical
    for word, canonical in _CN_NORMALIZE_MAP.items():
        if word.lower() in text:
            result[word.lower()] = canonical
    return dict(list(result.items())[:max_keywords])


class TopicKeywordManager:
    """动态话题关键词管理器

    职责：
    1. 导入文档时，从标题+metadata+内容预览+LLM(可选)提取关键词，存 Redis
    2. 对话信号提取时，合并静态词典 + Redis 动态 + 指定知识库关键词
    3. 提供增删改查管理接口（供 /agent/topics API 调用）
    """

    def __init__(self, redis_client: RedisClient, llm: Any = None):
        """
        Args:
            redis_client: Redis 客户端（必需）
            llm: 可选的 LLMProvider 实例。提供后会在文档导入时额外做
                 语义级关键词提取，覆盖规则词典之外的新领域。
                 不提供时，纯规则提取，零成本。
        """
        self.redis = redis_client
        self.llm = llm  # LLMProvider 或 None

    # ── 导入文档时提取关键词（规则 + 可选 LLM） ───────

    async def extract_and_register(
        self,
        knowledge_id: int,
        source_name: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        content_preview: Optional[str] = None,
        use_llm: Optional[bool] = None,
    ) -> Dict[str, str]:
        """提取关键词并保存到 Redis（knowledge 级 + global 级）

        Args:
            use_llm: 是否启用 LLM 语义提取。None 表示使用 self.llm 是否存在自动判断。
                     显式 True/False 可强制开关。
        """
        should_use_llm = self.llm is not None if use_llm is None else use_llm and self.llm is not None

        # ① 规则提取（零成本，总是执行）
        mapping: Dict[str, str] = {}
        if title:
            mapping.update(_extract_from_title(title))
        if metadata:
            mapping.update(_extract_from_metadata(metadata))
        if content_preview:
            mapping.update(_extract_from_preview(content_preview))

        # ② LLM 语义提取（可选，仅在 llm 可用 + 有内容时调用）
        llm_extra: Dict[str, str] = {}
        if should_use_llm and content_preview:
            try:
                llm_extra = await self._extract_with_llm(
                    content_preview=content_preview, title=title,
                    existing_keywords=list(mapping.values()),
                )
                if llm_extra:
                    logger.info("LLM 补充提取到 %d 个语义关键词: %s",
                                len(llm_extra), list(llm_extra.keys())[:10])
                    mapping.update(llm_extra)
            except Exception as e:
                logger.debug("LLM 关键词提取失败（不影响规则结果）: %s", e)

        if mapping:
            await self._save_for_knowledge(knowledge_id, mapping, source_name)
            await self._merge_to_global(mapping)
            logger.info("知识库 %s 共提取到 %d 话题关键词: %s",
                         knowledge_id, len(mapping), list(mapping.keys())[:10])

        return mapping

    # ── LLM 语义提取（混合模式的核心） ────────────────

    async def _extract_with_llm(
        self,
        content_preview: str,
        title: Optional[str] = None,
        existing_keywords: Optional[List[str]] = None,
        max_keywords: int = 10,
    ) -> Dict[str, str]:
        """让 LLM 理解文档内容，从文档前 1000 字提取话题关键词。
        返回 {keyword_lower: canonical_name} 格式的字典。
        失败时返回空字典，不会影响规则提取的结果。
        """
        if not content_preview:
            return {}

        existing = "、".join(existing_keywords[:20]) if existing_keywords else "（无）"

        prompt = f"""你是一个教学内容分析助手。请分析以下文档的标题和内容，提取 {max_keywords} 个以内的话题关键词。

要求：
1. 输出严格的 JSON 对象：{{"关键词小写": "规范名称"}}（例如 {{"kubernetes": "Kubernetes", "容器编排": "容器编排"}}）
2. 关键词必须是文档真实涉及的知识点，不要凭空添加
3. 规范名称要适合作为学习标签出现在学习进度中（不超过 10 字，中英文均可）
4. 避免过于泛化的词（如"编程"、"学习"），而使用具体的技术名或知识点
5. 如果规则已提取的关键词列表能覆盖文档，可返回空对象 {{}} 或少量补充
6. 不要输出 JSON 以外的任何解释文字

【文档标题】{title or "(未知)"}
【规则已提取的关键词】{existing}
【文档内容（前 1000 字）】
{content_preview[:1000]}"""

        try:
            response = await self.llm.chat([
                {"role": "system", "content": "你是一个严谨的教学内容分析助手。只输出严格的 JSON 对象，键是小写英文或中文短语，值是规范名称。不要加任何额外文字、不要加代码块标记、不要加解释。"},
                {"role": "user", "content": prompt}
            ], temperature=0.2, max_tokens=400)

            data = _extract_json_from_text(response)
            if not data or not isinstance(data, dict):
                logger.debug("LLM 未返回合法 JSON: %s", response[:100])
                return {}

            # 过滤并规范化
            result: Dict[str, str] = {}
            for k, v in data.items():
                if not isinstance(k, str) or not isinstance(v, str):
                    continue
                key = k.strip().lower()
                value = v.strip()
                if 0 < len(key) <= 30 and 0 < len(value) <= 30:
                    result[key] = value
            return dict(list(result.items())[:max_keywords])

        except asyncio.TimeoutError:
            logger.debug("LLM 关键词提取超时，跳过")
            return {}
        except Exception as e:
            logger.debug("LLM 关键词提取异常: %s", e)
            return {}

    # ── 对话时合并关键词 ─────────────────────────────────

    async def get_merged_keywords(self, knowledge_ids: Optional[List[int]] = None) -> Dict[str, str]:
        """合并 全局动态 + 指定知识库 + 静态基线 的关键词字典"""
        merged: Dict[str, str] = {}

        # 1. 全局动态关键词（所有导入知识中提取到的）
        global_kws = await self.redis.get_json(GLOBAL_KEY)
        if global_kws and isinstance(global_kws, dict):
            merged.update(global_kws)

        # 2. 指定知识库的关键词
        if knowledge_ids:
            for kid in knowledge_ids:
                data = await self.redis.get_json(f"{KNOWLEDGE_KEY_PREFIX}{kid}")
                if data and isinstance(data, dict):
                    kw_map = data.get("mapping", {}) if isinstance(data, dict) and "mapping" in data \
                             else (data if isinstance(data, dict) else {})
                    if kw_map:
                        merged.update(kw_map)

        # 3. 静态基线（保底）
        merged.update(get_static_keywords())
        return merged

    # ── 管理接口 ─────────────────────────────────────────

    async def add_keyword(self, keyword: str, canonical_name: str) -> None:
        """人工添加单个关键词到全局词典"""
        current = await self.redis.get_json(GLOBAL_KEY) or {}
        current[keyword.lower()] = canonical_name
        await self.redis.set_json(GLOBAL_KEY, current, ttl=KEYWORDS_TTL)

    async def remove_keyword(self, keyword: str) -> bool:
        """从全局动态词典中删除某个关键词"""
        current = await self.redis.get_json(GLOBAL_KEY) or {}
        removed = current.pop(keyword.lower(), None) is not None
        if removed:
            await self.redis.set_json(GLOBAL_KEY, current, ttl=KEYWORDS_TTL)
        return removed

    async def list_all(self) -> Dict[str, str]:
        """返回当前全局动态关键词词典"""
        return await self.redis.get_json(GLOBAL_KEY) or {}

    async def list_by_knowledge(self, knowledge_id: int) -> Dict[str, Any]:
        """返回某个知识库提取到的关键词及其元数据"""
        data = await self.redis.get_json(f"{KNOWLEDGE_KEY_PREFIX}{knowledge_id}")
        return data or {}

    async def clear_knowledge(self, knowledge_id: int) -> None:
        """删除某个知识库对应的关键词缓存（在删除知识库时调用）"""
        await self.redis.delete(f"{KNOWLEDGE_KEY_PREFIX}{knowledge_id}")

    async def clear_all(self) -> None:
        """清空所有动态关键词（调试用）"""
        await self.redis.delete(GLOBAL_KEY)
        try:
            keys = await self.redis.scan_keys(f"{KNOWLEDGE_KEY_PREFIX}*")
            for k in keys:
                await self.redis.delete(k)
        except Exception:
            pass

    # ── 内部方法：Redis 读写 ─────────────────────────────

    async def _save_for_knowledge(self, knowledge_id: int, mapping: Dict[str, str], source: str) -> None:
        import time as _time
        payload = {
            "knowledge_id": knowledge_id,
            "source": source,
            "mapping": mapping,
            "updated_at": _time.time(),
        }
        await self.redis.set_json(
            f"{KNOWLEDGE_KEY_PREFIX}{knowledge_id}",
            payload,
            ttl=KEYWORDS_TTL,
        )

    async def _merge_to_global(self, mapping: Dict[str, str]) -> None:
        current = await self.redis.get_json(GLOBAL_KEY) or {}
        if isinstance(current, dict):
            current.update(mapping)
        else:
            current = mapping
        await self.redis.set_json(GLOBAL_KEY, current, ttl=KEYWORDS_TTL)
