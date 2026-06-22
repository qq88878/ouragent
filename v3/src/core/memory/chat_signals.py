"""对话实时学习信号提取与缓存 — 规则提取，零 LLM 调用"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from .redis_client import RedisClient

logger = logging.getLogger(__name__)

SIGNALS_TTL = 7 * 24 * 3600  # 7 days

# ── 教育关键词词典（keyword -> canonical topic name）──────────────────
_TOPIC_KEYWORDS: Dict[str, str] = {
    # Python
    "列表": "Python列表", "list": "Python列表",
    "元组": "元组", "tuple": "元组",
    "字典": "字典", "dict": "字典",
    "集合": "集合", "set": "集合",
    "字符串": "字符串", "string": "字符串", "str": "字符串",
    "函数": "函数", "function": "函数",
    "类": "面向对象", "class": "面向对象",
    "继承": "继承", "inheritance": "继承",
    "装饰器": "装饰器", "decorator": "装饰器",
    "迭代器": "迭代器", "iterator": "迭代器",
    "生成器": "生成器", "generator": "生成器",
    "异常": "异常处理", "exception": "异常处理",
    "模块": "模块与包", "module": "模块与包", "package": "模块与包",
    "文件": "文件操作", "file": "文件操作",
    "正则": "正则表达式", "regex": "正则表达式", "regular expression": "正则表达式",
    "多线程": "多线程", "threading": "多线程",
    "协程": "协程", "async": "协程", "await": "协程", "coroutine": "协程",
    "递归": "递归", "recursion": "递归",
    "lambda": "Lambda表达式",
    "列表推导": "列表推导式", "list comprehension": "列表推导式",
    "切片": "切片", "slice": "切片",
    # 数据结构与算法
    "算法": "算法", "algorithm": "算法",
    "排序": "排序算法", "sort": "排序算法",
    "搜索": "搜索算法", "search": "搜索算法",
    "二叉树": "二叉树", "binary tree": "二叉树",
    "链表": "链表", "linked list": "链表",
    "栈": "栈", "stack": "栈",
    "队列": "队列", "queue": "队列",
    "哈希": "哈希表", "hash": "哈希表",
    "图": "图论", "graph": "图论",
    "动态规划": "动态规划", "dynamic programming": "动态规划",
    # 数据库
    "数据库": "数据库", "database": "数据库",
    "sql": "SQL", "查询": "SQL查询",
    "索引": "数据库索引", "index": "数据库索引",
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
    "html": "HTML", "css": "CSS", "javascript": "JavaScript", "js": "JavaScript",
    "react": "React", "vue": "Vue", "前端": "前端开发", "frontend": "前端开发",
    "api": "API", "接口": "API接口",
    "http": "HTTP协议", "https": "HTTP协议",
    # 通用
    "变量": "变量", "variable": "变量",
    "循环": "循环", "loop": "循环", "for": "循环", "while": "循环",
    "条件": "条件判断", "if": "条件判断",
    "数组": "数组", "array": "数组",
    "指针": "指针", "pointer": "指针",
    "进程": "进程", "process": "进程",
    "线程": "线程", "thread": "线程",
    "网络": "计算机网络", "network": "计算机网络",
    "操作系统": "操作系统", "operating system": "操作系统",
}

# 难度关键词
_DIFFICULTY_KEYWORDS: Dict[str, List[str]] = {
    "beginner": [
        "是什么", "什么是", "定义", "入门", "基础", "简单", "初学",
        "基本概念", "初步", "初识", "了解",
        "what is", "define", "basic", "simple", "introduction", "beginner",
    ],
    "advanced": [
        "证明", "优化", "复杂度", "高级", "深入", "源码", "原理",
        "底层", "架构", "设计模式", "性能", "调优", "并发",
        "prove", "optimize", "complexity", "advanced", "internals", "deep dive",
    ],
}

# 问题类型模式
_QUESTION_PATTERNS: Dict[str, List[str]] = {
    "what_is": ["什么是", "是什么", "什么叫", "含义是", "what is", "what are"],
    "how_to": ["怎么", "如何", "怎样", "怎么做", "如何实现", "how to", "how do", "how can"],
    "why": ["为什么", "为啥", "原因是", "why", "why does", "why is"],
    "compare": ["区别", "对比", "比较", "异同", "vs", "difference", "compare"],
    "example": ["举例", "例如", "比如", "例子", "举个", "example", "for instance"],
}

# 困惑/不理解信号
_GAP_PATTERNS = [
    "不懂", "不理解", "不明白", "搞不清", "什么意思", "没听懂",
    "看不懂", "还是不懂", "不太懂", "模糊", "困惑", "没搞懂",
    "一头雾水", "云里雾里", "confused", "don't understand", "unclear",
]


class ChatSignalExtractor:
    """无状态规则提取器 — 从单轮对话提取学习信号 delta"""

    def extract(self, user_message: str, assistant_response: str) -> Dict[str, Any]:
        topics = self._extract_topics(user_message, assistant_response)
        difficulty = self._detect_difficulty(user_message)
        question_type = self._detect_question_type(user_message)
        gap_keywords = self._detect_gaps(user_message)

        delta: Dict[str, Any] = {}
        if topics:
            delta["topics"] = topics
        if difficulty != "neutral":
            delta["difficulty_hint"] = difficulty
        if question_type:
            delta["question_type"] = question_type
        if gap_keywords:
            delta["gap_keywords"] = gap_keywords
        delta["question_increment"] = 1 if self._is_question(user_message) else 0
        return delta

    # ── 内部方法 ────────────────────────────────────────────

    def _extract_topics(self, user_msg: str, assistant_resp: str) -> List[str]:
        """通过关键词词典 + 助手回复模式提取话题"""
        text = (user_msg + " " + assistant_resp[:500]).lower()
        found: List[str] = []

        # 词典匹配（按出现顺序，去重）
        for keyword, topic in _TOPIC_KEYWORDS.items():
            if keyword in text and topic not in found:
                found.append(topic)
            if len(found) >= 5:
                break

        # 从助手回复中提取主题提示（如 "关于xxx", "xxx指的是"）
        if len(found) < 5:
            patterns = [
                r"关于[「『《]?([^」』》,，。\.]{2,15})[」』》]?",
                r"[这那]个[是叫]?[「『《]?([^」』》,，。\.]{2,15})",
                r"([^，。,\.]{2,10})指的是",
                r"([^，。,\.]{2,10})是[一这]种",
            ]
            for pat in patterns:
                for m in re.finditer(pat, assistant_resp[:500]):
                    topic = m.group(1).strip()
                    if topic and topic not in found and len(topic) >= 2:
                        found.append(topic)
                    if len(found) >= 5:
                        break

        return found[:5]

    def _detect_difficulty(self, message: str) -> str:
        msg = message.lower()
        beginner = sum(1 for kw in _DIFFICULTY_KEYWORDS["beginner"] if kw in msg)
        advanced = sum(1 for kw in _DIFFICULTY_KEYWORDS["advanced"] if kw in msg)
        if beginner > advanced:
            return "beginner"
        if advanced > beginner:
            return "advanced"
        return "neutral"

    def _detect_question_type(self, message: str) -> Optional[str]:
        msg = message.lower()
        for qtype, patterns in _QUESTION_PATTERNS.items():
            if any(p in msg for p in patterns):
                return qtype
        return None

    def _detect_gaps(self, message: str) -> List[str]:
        """检测困惑信号，提取困惑点附近的名词短语"""
        gaps = []
        msg_lower = message.lower()
        for pattern in _GAP_PATTERNS:
            if pattern in msg_lower:
                # 提取困惑关键词周围 2-8 字的上下文
                idx = msg_lower.find(pattern)
                start = max(0, idx - 8)
                end = min(len(message), idx + len(pattern) + 8)
                context = message[start:end].strip()
                if context and context not in gaps:
                    gaps.append(context)
                if len(gaps) >= 3:
                    break
        return gaps

    @staticmethod
    def _is_question(message: str) -> bool:
        """判断消息是否为提问"""
        return bool(re.search(r"[?？]|吗|呢|什么|怎么|如何|为什么|哪个|多少", message))


class ChatSignalsCache:
    """Redis 缓存 — 会话级学习信号存储"""

    def __init__(self, redis: RedisClient):
        self.redis = redis

    def _signals_key(self, user_id: str, session_id: str) -> str:
        return f"chat_signals:{user_id}:{session_id}"

    async def get_signals(self, user_id: str, session_id: str) -> Dict[str, Any]:
        key = self._signals_key(user_id, session_id)
        return await self.redis.get_json(key) or self._default_signals()

    async def update_signals(self, user_id: str, session_id: str, delta: Dict[str, Any]) -> Dict[str, Any]:
        current = await self.get_signals(user_id, session_id)
        merged = self._merge(current, delta)
        key = self._signals_key(user_id, session_id)
        await self.redis.set_json(key, merged, ttl=SIGNALS_TTL)
        return merged

    async def invalidate(self, user_id: str, session_id: str) -> bool:
        return await self.redis.delete(self._signals_key(user_id, session_id))

    @staticmethod
    def get_effective_difficulty(signals: Dict[str, Any]) -> str:
        dist = signals.get("difficulty_distribution", {})
        if not dist or sum(dist.values()) == 0:
            return "neutral"
        return max(dist, key=dist.get)

    @staticmethod
    def _default_signals() -> Dict[str, Any]:
        return {
            "active_topics": [],
            "topic_history": [],
            "difficulty_distribution": {"beginner": 0, "neutral": 0, "advanced": 0},
            "question_count": 0,
            "gap_keywords": [],
            "question_type_dist": {},
            "last_updated": None,
            "exchange_count": 0,
        }

    @staticmethod
    def _merge(current: Dict[str, Any], delta: Dict[str, Any]) -> Dict[str, Any]:
        # topics: prepend new, deduplicate, cap at 10
        if delta.get("topics"):
            existing = current.get("active_topics", [])
            new_set = {t.lower() for t in delta["topics"]}
            demoted = [t for t in existing if t.lower() not in new_set]
            history = current.get("topic_history", [])
            history = (demoted + history)[:20]
            combined = delta["topics"] + [t for t in existing if t.lower() not in new_set]
            current["active_topics"] = combined[:10]
            current["topic_history"] = history

        # difficulty
        if delta.get("difficulty_hint"):
            dist = current.get("difficulty_distribution", {"beginner": 0, "neutral": 0, "advanced": 0})
            dist[delta["difficulty_hint"]] = dist.get(delta["difficulty_hint"], 0) + 1
            current["difficulty_distribution"] = dist

        # question count
        current["question_count"] = current.get("question_count", 0) + delta.get("question_increment", 0)

        # gap keywords: deduplicate, cap at 10
        if delta.get("gap_keywords"):
            existing_gaps = {kw.lower() for kw in current.get("gap_keywords", [])}
            new_gaps = [kw for kw in delta["gap_keywords"] if kw.lower() not in existing_gaps]
            current["gap_keywords"] = (new_gaps + current.get("gap_keywords", []))[:10]

        # question type distribution
        if delta.get("question_type"):
            qt_dist = current.get("question_type_dist", {})
            qt_dist[delta["question_type"]] = qt_dist.get(delta["question_type"], 0) + 1
            current["question_type_dist"] = qt_dist

        current["last_updated"] = datetime.now().isoformat()
        current["exchange_count"] = current.get("exchange_count", 0) + 1

        return current
