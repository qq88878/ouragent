"""
从多个来源导入教育资源到向量库

来源：
1. HuggingFace chinese-fineweb-edu-v2 数据集（中文教育语料）
2. GitHub 中文教材仓库（Ai-Learn、free-programming-books）
3. 本地 Markdown 文件
"""

import asyncio
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# 设置国内镜像（可选）
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

sys.path.insert(0, str(Path(__file__).parent))

from src.core.rag import RAGPipeline, VectorStore, create_embedding_provider

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)


async def load_huggingface_dataset(max_items: int = 5000) -> List[Dict[str, str]]:
    """从 HuggingFace 加载中文教育数据集"""
    logger.info("正在加载 HuggingFace 数据集...")

    try:
        from datasets import load_dataset
    except ImportError:
        logger.warning("datasets 未安装，跳过 HuggingFace 数据集。安装命令: pip install datasets")
        return []

    # 尝试多个中文教育数据集
    datasets_to_try = [
        ("wikiann", "zh"),  # 中文维基百科标注数据
        ("tyqiangz/multilingual-sentiments", "chinese"),  # 多语言情感数据
    ]

    docs = []
    for ds_name, config in datasets_to_try:
        try:
            logger.info(f"尝试加载 {ds_name}...")
            ds = load_dataset(ds_name, config, split="train", streaming=True)

            count = 0
            for i, item in enumerate(ds):
                if count >= max_items // len(datasets_to_try):
                    break

                # 根据不同数据集提取文本
                text = ""
                if "tokens" in item:
                    text = " ".join(item["tokens"])
                elif "text" in item:
                    text = item["text"]
                elif "content" in item:
                    text = item["content"]

                text = text.strip()
                if len(text) < 30:
                    continue

                docs.append({
                    "content": text[:1500],
                    "source": f"huggingface/{ds_name}/{count}",
                    "metadata": {
                        "type": "education_corpus",
                        "dataset": ds_name,
                    },
                })
                count += 1

                if count % 200 == 0:
                    logger.info(f"  已加载 {count} 条...")

            logger.info(f"{ds_name} 加载完成: {count} 条")
            if docs:
                break  # 成功加载一个就停止

        except Exception as e:
            logger.warning(f"加载 {ds_name} 失败: {e}")
            continue

    if not docs:
        logger.warning("所有 HuggingFace 数据集加载失败，使用本地教育资源")
        # 生成一些基础教育内容
        docs = _generate_basic_education_content()

    return docs


def _generate_basic_education_content() -> List[Dict[str, str]]:
    """生成基础教育内容作为兜底"""
    contents = [
        {
            "title": "Python 基础语法",
            "content": """Python 是一种解释型、面向对象的高级编程语言。

变量和数据类型：
- 整数 (int): 如 42, -10
- 浮点数 (float): 如 3.14, -0.5
- 字符串 (str): 如 "Hello", 'World'
- 布尔值 (bool): True 或 False
- 列表 (list): 如 [1, 2, 3]
- 字典 (dict): 如 {"name": "Alice", "age": 25}

控制流：
```python
# if 语句
if score >= 90:
    print("优秀")
elif score >= 60:
    print("及格")
else:
    print("不及格")

# for 循环
for i in range(10):
    print(i)

# while 循环
count = 0
while count < 5:
    print(count)
    count += 1
```

函数定义：
```python
def greet(name):
    return f"你好, {name}!"

result = greet("世界")
print(result)
```"""
        },
        {
            "title": "Python 列表和元组",
            "content": """列表 (List) 是 Python 中最常用的数据结构之一。

创建列表：
```python
fruits = ["苹果", "香蕉", "橙子"]
numbers = [1, 2, 3, 4, 5]
mixed = [1, "hello", 3.14, True]
```

列表操作：
```python
# 添加元素
fruits.append("葡萄")  # 末尾添加
fruits.insert(0, "西瓜")  # 指定位置添加

# 删除元素
fruits.remove("香蕉")  # 删除指定元素
popped = fruits.pop()  # 删除并返回最后一个
del fruits[0]  # 删除指定索引

# 切片
subset = fruits[1:3]  # 获取索引 1-2 的元素
reversed_list = fruits[::-1]  # 反转列表

# 列表推导式
squares = [x**2 for x in range(10)]
evens = [x for x in range(20) if x % 2 == 0]
```

元组 (Tuple) 是不可变的列表：
```python
point = (3, 4)
x, y = point  # 解包
```

列表 vs 元组：
- 列表可变，元组不可变
- 元组性能更好，可作为字典的键
- 元组用于函数返回多个值"""
        },
        {
            "title": "机器学习基础概念",
            "content": """机器学习是人工智能的一个分支，让计算机从数据中学习规律。

三大类型：
1. 监督学习 (Supervised Learning)
   - 有标签数据
   - 分类：预测离散类别（如垃圾邮件检测）
   - 回归：预测连续值（如房价预测）

2. 无监督学习 (Unsupervised Learning)
   - 无标签数据
   - 聚类：将数据分成 groups
   - 降维：减少特征数量

3. 强化学习 (Reinforcement Learning)
   - 通过奖励/惩罚学习
   - 应用：游戏 AI、机器人控制

常用算法：
- 线性回归：y = wx + b
- 逻辑回归：用于二分类
- 决策树：基于规则的分类
- 随机森林：多个决策树的集成
- SVM：找到最优分离超平面
- KNN：基于最近邻的分类
- K-Means：聚类算法
- 神经网络：模拟人脑结构

评估指标：
- 准确率 (Accuracy)
- 精确率 (Precision)
- 召回率 (Recall)
- F1 分数
- AUC-ROC

```python
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# 划分数据集
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# 训练模型
model = RandomForestClassifier()
model.fit(X_train, y_train)

# 预测和评估
predictions = model.predict(X_test)
print(f"准确率: {accuracy_score(y_test, predictions)}")
```"""
        },
        {
            "title": "数据结构与算法",
            "content": """数据结构是计算机存储和组织数据的方式。

常见数据结构：

1. 数组 (Array)
   - 连续内存存储
   - 随机访问 O(1)
   - 插入删除 O(n)

2. 链表 (Linked List)
   - 非连续内存
   - 插入删除 O(1)
   - 访问 O(n)

3. 栈 (Stack)
   - 后进先出 (LIFO)
   - 操作：push, pop, peek

4. 队列 (Queue)
   - 先进先出 (FIFO)
   - 操作：enqueue, dequeue

5. 哈希表 (Hash Table)
   - 键值对存储
   - 平均 O(1) 查找
   - 处理冲突：链地址法、开放寻址

6. 树 (Tree)
   - 二叉树、二叉搜索树
   - 平衡树：AVL、红黑树
   - 堆：最大堆、最小堆

7. 图 (Graph)
   - 有向图、无向图
   - 遍历：BFS、DFS

常见算法：
- 排序：冒泡、选择、插入、快速、归并
- 搜索：线性、二分
- 动态规划：背包问题、最长公共子序列
- 贪心：活动选择、霍夫曼编码"""
        },
        {
            "title": "Web 开发基础",
            "content": """Web 开发分为前端和后端。

前端三件套：
1. HTML - 结构
```html
<!DOCTYPE html>
<html>
<head>
    <title>我的页面</title>
</head>
<body>
    <h1>标题</h1>
    <p>段落</p>
</body>
</html>
```

2. CSS - 样式
```css
body {
    font-family: Arial;
    background: #f0f0f0;
}
h1 {
    color: blue;
    text-align: center;
}
```

3. JavaScript - 行为
```javascript
document.getElementById('btn').addEventListener('click', () => {
    alert('点击了按钮!');
});
```

后端框架：
- Python: Flask, Django, FastAPI
- Java: Spring Boot
- Node.js: Express
- Go: Gin

RESTful API 设计：
- GET /api/users - 获取用户列表
- POST /api/users - 创建用户
- GET /api/users/1 - 获取用户详情
- PUT /api/users/1 - 更新用户
- DELETE /api/users/1 - 删除用户

数据库：
- 关系型：MySQL, PostgreSQL, SQLite
- NoSQL：MongoDB, Redis

部署：
- Docker 容器化
- Nginx 反向代理
- CI/CD 自动化"""
        },
        {
            "title": "数学基础：线性代数",
            "content": """线性代数是机器学习和数据科学的基础。

向量 (Vector)：
- n 维空间中的点
- 加法：v1 + v2 = [a1+b1, a2+b2, ...]
- 标量乘法：c * v = [c*a1, c*a2, ...]
- 点积：v1 · v2 = a1*b1 + a2*b2 + ...
- 模长：||v|| = sqrt(a1^2 + a2^2 + ...)

矩阵 (Matrix)：
- m×n 的数组
- 加法：对应元素相加
- 乘法：(AB)ij = Σ aik * bkj
- 转置：行变列，列变行

特殊矩阵：
- 单位矩阵 I：对角线为 1
- 零矩阵：所有元素为 0
- 对称矩阵：A = A^T
- 正交矩阵：A^T = A^-1

线性变换：
- 矩阵乘法表示线性变换
- 旋转、缩放、投影

特征值和特征向量：
- Av = λv
- 用于 PCA 降维
- 用于谱聚类

应用：
- 主成分分析 (PCA)
- 奇异值分解 (SVD)
- 最小二乘法
- 神经网络中的权重矩阵"""
        },
        {
            "title": "概率论与统计基础",
            "content": """概率论和统计是数据分析的核心。

概率基础：
- 随机事件：可能发生也可能不发生
- 概率：P(A) ∈ [0, 1]
- 条件概率：P(A|B) = P(A∩B) / P(B)
- 贝叶斯定理：P(A|B) = P(B|A) * P(A) / P(B)

常见分布：
- 离散：伯努利、二项、泊松
- 连续：均匀、正态、指数

正态分布 N(μ, σ²)：
- 68-95-99.7 法则
- 中心极限定理

描述统计：
- 均值：μ = Σxi / n
- 中位数：排序后的中间值
- 众数：出现最多的值
- 方差：σ² = Σ(xi-μ)² / n
- 标准差：σ = sqrt(σ²)

推断统计：
- 点估计：用样本统计量估计总体参数
- 区间估计：置信区间
- 假设检验：t 检验、卡方检验、ANOVA

相关性与回归：
- 相关系数 r ∈ [-1, 1]
- 线性回归：y = β0 + β1*x + ε
- R² 决定系数

```python
import numpy as np
from scipy import stats

data = np.random.normal(100, 15, 1000)
mean, std = np.mean(data), np.std(data)
ci = stats.t.interval(0.95, len(data)-1, loc=mean, scale=stats.sem(data))
```"""
        },
        {
            "title": "深度学习入门",
            "content": """深度学习是机器学习的子集，使用多层神经网络。

神经网络基础：
- 神经元：接收输入，加权求和，激活函数输出
- 层：输入层、隐藏层、输出层
- 激活函数：ReLU、Sigmoid、Tanh、Softmax

前向传播：
```
输入 → 隐藏层1 → 隐藏层2 → ... → 输出
每层：z = Wx + b, a = f(z)
```

反向传播：
- 计算损失函数梯度
- 链式法则
- 梯度下降优化

常见架构：
1. 全连接网络 (FCN)
2. 卷积神经网络 (CNN)
   - 卷积层：提取特征
   - 池化层：降维
   - 应用：图像识别

3. 循环神经网络 (RNN)
   - 处理序列数据
   - LSTM、GRU 解决长期依赖
   - 应用：文本、时间序列

4. Transformer
   - 自注意力机制
   - 并行计算
   - 应用：BERT、GPT

```python
import torch
import torch.nn as nn

class SimpleNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(784, 128)
        self.fc2 = nn.Linear(128, 10)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        return self.fc2(x)
```

训练技巧：
- 学习率调整
- 正则化：Dropout、L2
- 批量归一化
- 数据增强"""
        },
    ]

    docs = []
    for item in contents:
        docs.append({
            "content": item["content"],
            "source": f"education/{item['title']}",
            "metadata": {
                "type": "education_content",
                "title": item["title"],
            },
        })

    logger.info(f"生成了 {len(docs)} 个教育内容文档")
    return docs


async def load_github_repo(repo_url: str, repo_name: str, max_files: int = 200) -> List[Dict[str, str]]:
    """从 GitHub 仓库加载 Markdown 文件"""
    import subprocess

    repo_dir = DATA_DIR / "repos" / repo_name
    docs = []

    # Clone 仓库（如果不存在）
    if not repo_dir.exists():
        logger.info(f"正在克隆 {repo_url}...")
        try:
            subprocess.run(
                ["git", "clone", "--depth=1", repo_url, str(repo_dir)],
                check=True,
                capture_output=True,
                timeout=300,
            )
        except Exception as e:
            logger.error(f"克隆失败: {e}")
            return []
    else:
        logger.info(f"仓库已存在: {repo_dir}")

    # 扫描 Markdown 文件
    md_files = list(repo_dir.rglob("*.md"))[:max_files]
    logger.info(f"找到 {len(md_files)} 个 Markdown 文件")

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8", errors="ignore").strip()
            if len(content) < 100:  # 过滤太短的文件
                continue

            rel_path = md_file.relative_to(repo_dir)
            docs.append({
                "content": content[:3000],  # 限制长度
                "source": f"github/{repo_name}/{rel_path}",
                "metadata": {
                    "type": "textbook",
                    "repo": repo_name,
                    "file": str(rel_path),
                },
            })
        except Exception as e:
            logger.warning(f"读取失败 {md_file}: {e}")

    logger.info(f"GitHub 仓库 {repo_name} 加载完成: {len(docs)} 条")
    return docs


async def load_local_pmd() -> List[Dict[str, str]]:
    """加载本地 p.md 内容"""
    p_md_path = Path(__file__).parent / "p.md"
    if not p_md_path.exists():
        return []

    content = p_md_path.read_text(encoding="utf-8").strip()
    if not content:
        return []

    return [{
        "content": content,
        "source": "p.md",
        "metadata": {"type": "guide", "file": "p.md"},
    }]


async def main():
    """主函数：从多个来源导入数据"""
    import argparse

    parser = argparse.ArgumentParser(description="导入教育资源到向量库")
    parser.add_argument("--source", choices=["huggingface", "github", "local", "all"], default="all")
    parser.add_argument("--max-items", type=int, default=2000, help="HuggingFace 最大条目数")
    parser.add_argument("--max-files", type=int, default=100, help="GitHub 每仓库最大文件数")
    parser.add_argument("--provider", choices=["local", "api"], default="api", help="嵌入方式")
    args = parser.parse_args()

    # 收集所有文档
    all_docs: List[Dict[str, str]] = []

    if args.source in ("huggingface", "all"):
        hf_docs = await load_huggingface_dataset(max_items=args.max_items)
        all_docs.extend(hf_docs)

    if args.source in ("github", "all"):
        repos = [
            ("https://github.com/tangyudi/Ai-Learn", "Ai-Learn"),
            ("https://github.com/justjavac/free-programming-books-zh_CN", "free-programming-books"),
        ]
        for url, name in repos:
            repo_docs = await load_github_repo(url, name, max_files=args.max_files)
            all_docs.extend(repo_docs)

    if args.source in ("local", "all"):
        local_docs = await load_local_pmd()
        all_docs.extend(local_docs)

    if not all_docs:
        logger.warning("没有文档可导入")
        return

    logger.info(f"共收集 {len(all_docs)} 条文档，开始导入向量库...")

    # 初始化嵌入提供者
    if args.provider == "api":
        from config.settings import settings
        if settings.EMBEDDING_API_KEY and settings.EMBEDDING_BASE_URL:
            logger.info(f"使用 Embedding API: {settings.EMBEDDING_BASE_URL}")
            embedding_provider = create_embedding_provider(
                provider="openai",
                api_key=settings.embedding_api_key,
                base_url=settings.embedding_base_url,
                model=settings.EMBEDDING_MODEL,
            )
        else:
            logger.warning("未配置 EMBEDDING_API_KEY，降级为本地嵌入")
            embedding_provider = create_embedding_provider(provider="local")
    else:
        embedding_provider = create_embedding_provider(provider="local")

    # 动态获取向量维度
    embedding_dim = getattr(embedding_provider, '_dimension', 384)
    logger.info(f"嵌入维度: {embedding_dim}")

    vector_store = VectorStore(dimension=embedding_dim)

    store_path = str(DATA_DIR / "vector_store.json")
    existing = vector_store.load(store_path)
    if existing > 0:
        logger.info(f"已加载 {existing} 个已有文档")

    rag = RAGPipeline(
        vector_store=vector_store,
        embedding_provider=embedding_provider,
        chunk_size=500,
        chunk_overlap=50,
    )

    # 批量导入
    total_chunks = 0
    for i, doc in enumerate(all_docs):
        chunks = await rag.ingest_text(
            text=doc["content"],
            source=doc["source"],
            extra_metadata=doc.get("metadata", {}),
        )
        total_chunks += chunks

        if (i + 1) % 100 == 0:
            logger.info(f"已处理 {i + 1}/{len(all_docs)} 条...")

    # 保存
    vector_store.save(store_path, force=True)
    logger.info(f"导入完成! 总计 {total_chunks} 个文档块，向量库已保存到: {store_path}")

    # 统计
    stats = rag.stats()
    logger.info(f"向量库统计: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
