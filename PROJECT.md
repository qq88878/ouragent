# OurAgent 项目开发手册

> **项目名称**：基于大模型的个性化资源生成与学习多智能体系统
> **架构版本**：v3.0（Java + Python 微服务架构）
> **更新日期**：2026年6月

---

## 目录

1. [项目概述](#一项目概述)
2. [需求分析](#二需求分析)
3. [系统架构](#三系统架构)
4. [技术栈](#四技术栈)
5. [现有代码说明](#五现有代码说明)
6. [Agent 服务详解（Python）](#六agent-服务详解python)
7. [Java 业务服务设计（参考 javaarea）](#七java-业务服务设计参考-javaarea)
8. [Java-Python 集成方案](#八java-python-集成方案)
9. [数据库设计](#九数据库设计)
10. [项目目录结构](#十项目目录结构)
11. [开发流程](#十一开发流程)
12. [Docker 部署](#十二docker-部署)
13. [环境变量](#十三环境变量)
14. [风险与应对](#十四风险与应对)
15. [团队分工](#十五团队分工)

---

## 一、项目概述

### 1.1 项目背景

在计算机/编程教育领域，传统"一刀切"的教学方式无法满足不同学生的个性化需求。本项目通过 **大语言模型 + 多智能体架构**，构建一个能够自动分析学生画像、规划个性化学习路径、智能生成教学资源（题库、思维导图、文档、PPT）、提供智能辅导与学习评估的智能学习平台。

### 1.2 核心目标

| 目标 | 说明 |
|------|------|
| 个性化 | 根据学生画像动态调整学习内容和路径 |
| 智能化 | 基于星火大模型驱动多智能体协作 |
| 可交互 | 生成的教学资源支持下载和预览 |
| 易部署 | `docker-compose up` 一键启动 |

### 1.3 比赛硬性要求

| 要求 | 说明 |
|------|------|
| 必须使用星火大模型 | 核心推理引擎 |
| 必须体现多智能体 | 至少 3 个 Agent 分工协作 |
| 资源必须可交互 | 生成的内容支持下载 / 预览 |
| 一键启动 | `docker-compose up` 即可运行 |

### 1.4 架构策略

**双语言微服务架构**：

| 语言 | 负责领域 | 说明 |
|------|---------|------|
| **Python** | Agent 智能体层 | AI 推理、多智能体协作、RAG 知识库、工具调用 |
| **Java** | 业务服务层 | 用户管理、认证授权、业务编排、API 网关 |

**现有代码基础**：

| 模块 | 目录 | 状态 |
|------|------|------|
| Python Agent 核心框架 | `v3/src/core/` | **已有**（Agent、Memory、Tools） |
| Python API 服务 | `src/api.py` | **已有**（FastAPI 接口） |
| Java 集成参考代码 | `javaarea/` | **已有**（调用示例） |
| Java 业务服务 | `user-service/` | **待建** |
| 前端 SPA | `frontend/` | **待建** |

**双模型策略**：
- **星火大模型**：核心功能（画像分析、路径规划、资源生成）
- **小米 MiMo**：辅助功能（对话补全、简单问答、测试阶段）


---

## 二、需求分析

### 2.1 用户角色

| 角色 | 编号 | 说明 |
|------|------|------|
| 学生 | R01 | 平台主要使用者，学习、做练习、查看资源 |
| 教师/管理员 | R02 | 管理学生、查看学习数据、管理系统 |
| 游客 | R03 | 未登录用户，仅可浏览首页和登录/注册 |

### 2.2 功能需求详细列表

#### 2.2.1 用户模块（Java user-service，待建）

| 编号 | 功能 | 优先级 | 角色 | 详细描述 |
|------|------|--------|------|----------|
| F001 | 用户注册 | P0 | R01, R02 | 输入用户名+邮箱+密码，邮箱唯一校验 |
| F002 | 用户登录 | P0 | R01, R02 | 邮箱+密码登录，返回 JWT Token |
| F003 | Token 刷新 | P0 | R01, R02 | Access 过期后自动用 Refresh Token 续期 |
| F004 | 获取当前用户 | P1 | R01, R02 | 根据 Token 返回当前用户信息 |
| F005 | 退出登录 | P1 | R01, R02 | 吊销 Refresh Token |
| F006 | 用户管理 | P2 | R02 | 查看/禁用/删除用户 |

#### 2.2.2 Agent 模块（Python agent-service，已有框架待完善）

| 编号 | 功能 | 优先级 | 角色 | 关联代码 | 说明 |
|------|------|--------|------|---------|------|
| F101 | 学生画像分析 | P0 | R01 | `core/agent.py` 扩展 | 根据答题记录生成能力画像 |
| F102 | 学习路径规划 | P0 | R01 | `core/agent.py` 扩展 | 根据画像生成学习路线图 |
| F103 | 题目生成 | P0 | R01 | 新增 Agent 子类 | 自动生成选择题/填空题/编程题 |
| F104 | 思维导图生成 | P0 | R01 | 新增工具 `tools.py` | 结构化知识点为思维导图 |
| F105 | 文档生成 | P1 | R01 | 新增工具 | 生成 Markdown/PDF 可下载文档 |
| F106 | PPT 生成 | P1 | R01 | 新增工具 | 自动生成教学 PPT |
| F107 | 智能对话辅导 | P0 | R01 | `api.py` 已有 `/agent/chat` | 学生提问，Agent 智能回答 |
| F108 | 学习效果评估 | P1 | R01 | 新增 Agent 子类 | 评分和反馈 |
| F109 | RAG 知识库检索 | P1 | R01 | 新增模块 | 向量库检索增强回答 |
| F110 | 工具调用 | P0 | R01 | `tools.py` 已有框架 | Calculator, Search 等工具 |

#### 2.2.3 前端模块（Vue3 frontend，待建）

| 编号 | 功能 | 优先级 | 角色 | 说明 |
|------|------|--------|------|------|
| F201 | 登录页 | P0 | R01, R02 | 邮箱+密码登录，错误提示 |
| F202 | 注册页 | P0 | R01, R02 | 用户名+邮箱+密码+确认密码 |
| F203 | 首页仪表盘 | P0 | R01 | 学习概览、推荐路径 |
| F204 | 智能对话页 | P0 | R01 | 与 AI 助手的聊天界面 |
| F205 | 学习路径页 | P1 | R01 | 展示学习路径图 |
| F206 | 资源管理页 | P1 | R01 | 查看/下载生成的资源 |

### 2.3 非功能需求

| 编号 | 分类 | 需求 | 指标 |
|------|------|------|------|
| N001 | 性能 | API 响应时间 | 常规 < 500ms，Agent < 5s |
| N002 | 安全 | 密码存储 | bcrypt 哈希 |
| N003 | 安全 | 接口鉴权 | JWT 校验（除登录/注册）|
| N004 | 可维护性 | 容器化部署 | Docker Compose 一键启动 |
| N005 | 可扩展性 | 微服务架构 | 支持独立扩缩容 |

### 2.4 用例分析

#### UC01：学生注册使用流程
用户 -> 打开首页 -> 点注册 -> 填写信息 -> POST /api/auth/register -> Java 校验 -> bcrypt 加密 -> 存入 MySQL -> 返回成功 -> 跳转登录

#### UC02：智能学习流程
用户已登录 -> 进入智能学习页 -> POST /api/agent/chat -> Nginx 转发 -> Java 鉴权 -> Python Agent 处理 -> Orchestrator 调度子 Agent -> 返回结果

#### UC03：智能对话流程（现有 api.py 支持）
用户 -> 打开对话页 -> 输入问题 -> POST /agent/chat -> `api.py` 接收 -> `Agent.chat()` 处理 -> `Memory` 记录上下文 -> 返回回复

### 2.5 需求矩阵

| 编号 | 功能 | 服务 | 优先级 | 阶段 | 现有代码 |
|------|------|------|--------|------|---------|
| F001-F003 | 注册/登录/Token | user-service | P0 | 阶段二 | 无 |
| F107 | 智能对话 | agent-service | P0 | 阶段一 | `api.py` + `agent.py` |
| F110 | 工具调用 | agent-service | P0 | 阶段一 | `tools.py` |
| F101 | 画像分析 | agent-service | P0 | 阶段三 | 待扩展 |
| F102 | 路径规划 | agent-service | P0 | 阶段三 | 待扩展 |
| F103-F106 | 资源生成 | agent-service | P0/P1 | 阶段四 | 待新建 |
| F201-F206 | 前端页面 | frontend | P0/P1 | 阶段二至五 | 无 |


---

## 三、系统架构

### 3.1 服务拆分

| 服务名 | 语言 | 职责 | 端口 | 状态 |
|--------|------|------|------|------|
| `agent-service` | **Python** | 多智能体推理、对话、工具调用 | 8000 | **已有框架** |
| `user-service` | **Java** | 用户注册/登录/JWT 鉴权 | 9001 | **待建** |
| `business-service` | **Java** | 业务编排、资源管理 | 9002 | **待建** |
| `frontend` | Vue3 | 前端 SPA 页面 | 3000 | **待建** |
| `mysql` | — | 业务数据库 | 3306 | Docker |
| `redis` | — | 缓存/会话 | 6379 | Docker |
| `postgres` | — | Agent 数据库 | 5432 | Docker |

### 3.2 架构图

```
[浏览器/Vue3] -> [Nginx]
                     |
            +--------+--------+
            |                 |
       /api/auth/*       /api/agent/*
            |                 |
   [Java user-service]   [Python agent-service]
    Spring Boot 3.2       FastAPI (src/api.py)
            |                 |
     [MySQL + Redis]    [Postgres + Redis]
                              |
                      [javaarea/ 参考代码]
```

### 3.3 通信方式

| 方向 | 方式 |
|------|------|
| 浏览器 -> Nginx | HTTP |
| Nginx -> Java | 反向代理 |
| Nginx -> Python | 反向代理 |
| Java -> Python | REST（参考 `javaarea/AgentServiceClient.java`）|
| Python -> DB | SQLAlchemy / redis-py |


---

## 四、技术栈

### 4.1 Python 技术栈（已有代码）

| 组件 | 选型 | 所在位置 | 用途 |
|------|------|---------|------|
| Web 框架 | FastAPI | `src/api.py` | API 接口 |
| ASGI 服务器 | Uvicorn | `requirements.txt` | 异步服务器 |
| Agent 框架 | 自定义 Agent 类 | `v3/src/core/agent.py` | 多智能体核心 |
| 内存管理 | Memory 类 | `v3/src/core/memory.py` | 对话历史存储 |
| 工具系统 | Tool 基类 | `v3/src/core/tools.py` | 工具定义与调用 |
| 配置管理 | Config 类 | `v3/src/utils/config.py` | 环境变量读取 |
| 日志系统 | Logger | `v3/src/utils/logger.py` | 日志记录 |
| gRPC | grpcio | `src/grpc/agent.proto` | (可选)高性能通信 |
| 构建工具 | pyproject.toml + Makefile | `v3/` | 项目构建与开发命令 |

### 4.2 Java 技术栈（参考 javaarea，待建完整服务）

| 组件 | 选型 | 参考文件 |
|------|------|---------|
| 框架 | Spring Boot 3.2.x | `javaarea/pom.xml` |
| JDK | Java 17 | — |
| 认证 | Spring Security + JWT | `javaarea/AgentServiceConfig.java` |
| 加密 | BCryptPasswordEncoder | — |
| ORM | Spring Data JPA | — |
| 数据库 | MySQL 8.0 | — |
| 缓存 | Redis | — |
| 构建 | Maven | `javaarea/pom.xml` |

### 4.3 前端技术栈（待建）

| 组件 | 选型 |
|------|------|
| 框架 | Vue 3 + Composition API |
| UI 库 | Element Plus |
| 构建 | Vite |
| HTTP | Axios |
| 路由 | Vue Router |
| 状态管理 | Pinia |


---

## 五、现有代码说明

> 本项目已有 Python Agent 框架的完整基础代码，分布在 `src/` 和 `v3/` 两个目录。以下说明其关系和使用方式。

### 5.1 目录关系

```
ouragent/
│
├── src/                         # API 层（面向 Java 的接口）
│   ├── api.py                   # FastAPI 应用，提供 REST API
│   └── grpc/
│       └── agent.proto          # gRPC 协议定义
│
├── v3/                          # Agent 核心框架（独立 Python 包）
│   ├── src/core/
│   │   ├── agent.py             # Agent 核心类
│   │   ├── memory.py            # 对话记忆管理
│   │   └── tools.py             # 工具基类及实现
│   ├── src/utils/
│   │   ├── config.py            # 配置管理
│   │   └── logger.py            # 日志管理
│   ├── src/main.py              # 独立入口
│   ├── tests/                   # 单元测试
│   ├── examples/                # 使用示例
│   ├── requirements.txt         # 依赖
│   ├── pyproject.toml           # 项目配置
│   └── Makefile                 # 开发命令
│
├── javaarea/                    # Java 参考代码
│   ├── pom.xml                  # Maven 依赖
│   ├── AgentController.java     # Java Controller 示例
│   ├── AgentServiceClient.java  # Java 调用 Agent 的客户端
│   ├── AgentServiceConfig.java  # 配置类
│   └── application-agent.yml    # 配置示例
│
└── docs/                        # 文档
    ├── JAVA_INTEGRATION_GUIDE.md
    └── MICROSERVICE_ARCHITECTURE.md
```

### 5.2 核心类说明

| 类/文件 | 位置 | 功能 | 关键方法 |
|---------|------|------|---------|
| `Agent` | `v3/src/core/agent.py` | Agent 核心类，管理对话、记忆、工具 | `chat()`, `register_tool()`, `get_tool()` |
| `Memory` | `v3/src/core/memory.py` | 环形缓冲区，存储对话历史 | `add_message()`, `get_history()` |
| `Tool` | `v3/src/core/tools.py` | 工具基类，可扩展 | `execute()` |
| `FastAPI` | `src/api.py` | REST API 入口 | `/agent/chat`, `/agent/tool`, `/health` |
| `Config` | `v3/src/utils/config.py` | 环境变量读取 | `get()`, `get_int()`, `get_bool()` |

### 5.3 现有 API 接口（src/api.py）

| 端点 | 方法 | 说明 | 请求/响应 |
|------|------|------|---------|
| `/` | GET | 服务信息 | `{service, version, status}` |
| `/health` | GET | 健康检查 | `{status, agent_available}` |
| `/agent/status` | GET | Agent 状态 | `{id, name, tools, memory_size}` |
| `/agent/chat` | POST | 对话 | 请求: `{message, context}` -> 响应: `{response, agent_id}` |
| `/agent/tool` | POST | 调用工具 | 请求: `{tool_name, parameters}` -> 响应: `{result}` |
| `/agent/tools` | GET | 列出工具 | `{tools: [名称列表]}` |
| `/agent/history` | GET | 获取历史 | `{history: [...], total}` |
| `/agent/batch/chat` | POST | 批量对话 | `{messages: [...]}` -> `{results: [...]}` |

### 5.4 现有代码如何使用

```bash
# 启动 Agent 服务（根目录的 Dockerfile 已配置）
docker-compose up -d

# 或手动运行
cd ouragent
pip install -r v3/requirements.txt
python -m src.api

# 测试（服务运行后）
curl http://localhost:8000/health
curl http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好，请介绍自己"}'
```


---

## 六、Agent 服务详解（Python）

### 6.1 总体架构

```
[API 层] src/api.py          ← Java 后端直接调用的 REST 接口
    |
[核心层] v3/src/core/
    ├── agent.py              Agent 核心：接收消息 → 调用记忆 → 选择工具 → 返回回复
    ├── memory.py             记忆管理：存储对话上下文
    └── tools.py              工具系统：扩展 Agent 能力
```

### 6.2 多智能体扩展设计

当前 `agent.py` 是单 Agent 实现。要满足比赛"多智能体"要求，需扩展为：

| Agent 名称 | 基类 | 职责 | 扩展方式 |
|-----------|------|------|---------|
| **MainAgent** | `Agent`（已有） | 对话辅导、工具调用 | **已有** |
| **ProfileAgent** | 继承 `Agent` | 学生画像分析 | 新增子类 |
| **PlannerAgent** | 继承 `Agent` | 学习路径规划 | 新增子类 |
| **ResourceAgent** | 继承 `Agent` | 教学资源生成 | 新增子类 |
| **EvaluatorAgent** | 继承 `Agent` | 学习评估 | 新增子类 |
| **Orchestrator** | — | 任务调度、汇总 | 新增 workﬂow |

### 6.3 代码扩展示例

```python
# 在 v3/src/core/ 下新建子类，继承 Agent
from .agent import Agent

class ProfileAgent(Agent):
    """学生画像 Agent"""

    def __init__(self):
        super().__init__(name="ProfileAgent", description="分析学生画像")

    async def analyze(self, user_id: str) -> dict:
        # TODO: 调用星火大模型分析
        return {"user_id": user_id, "level": "beginner", "weaknesses": []}
```

### 6.4 已有工具说明（v3/src/core/tools.py）

| 工具类 | 用途 | 已有/待建 |
|--------|------|---------|
| `CalculatorTool` | 计算器 | **已有** |
| `SearchTool` | 搜索 | **已有** |
| `QuestionGenerator` | 题目生成 | 待建 |
| `MindMapGenerator` | 思维导图生成 | 待建 |
| `DocGenerator` | 文档生成 | 待建 |
| `PPTGenerator` | PPT 生成 | 待建 |


---

## 七、Java 业务服务设计（参考 javaarea）

### 7.1 javaarea 现有代码参考

`javaarea/` 目录已有 Java 集成参考代码，可直接复用：

| 文件 | 用途 | 说明 |
|------|------|------|
| `pom.xml` | Maven 依赖 | Spring Boot + Web + JWT 等 |
| `AgentController.java` | Java API 控制器 | 定义 REST 端点 |
| `AgentServiceClient.java` | 调用 Python Agent 的客户端 | 使用 RestTemplate 转发请求 |
| `AgentServiceConfig.java` | 配置类 | 服务地址、超时等 |
| `application-agent.yml` | 配置文件 | 示例配置 |

### 7.2 user-service 设计（基于 javaarea 扩展）

利用 `javaarea/` 的参考代码，扩展为完整的 Spring Boot 微服务。

**API 端点**：

| 端点 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/api/auth/register` | POST | 注册 | 无 |
| `/api/auth/login` | POST | 登录 | 无 |
| `/api/auth/refresh` | POST | 刷新 Token | 无 |
| `/api/auth/me` | GET | 当前用户 | JWT |
| `/api/agent/chat` | POST | 转发到 Python Agent（参考 `AgentController.java`）| JWT |
| `/api/agent/tool` | POST | 调用工具（参考 `AgentController.java`）| JWT |

### 7.3 Java 调用 Python Agent 示例

```java
// 参考 javaarea/AgentServiceClient.java
@Service
public class AgentServiceClient {
    private final RestTemplate restTemplate;

    public AgentServiceClient() {
        this.restTemplate = new RestTemplate();
    }

    public String chat(Long userId, String message) {
        // 构建请求
        Map<String, Object> body = new HashMap<>();
        body.put("user_id", userId.toString());
        body.put("message", message);

        // 调用 Python Agent
        ResponseEntity<String> response = restTemplate.postForEntity(
            "http://agent-service:8000/agent/chat",  // 注意路径与 api.py一致
            body,
            String.class
        );
        return response.getBody();
    }
}
```


---

## 八、Java-Python 集成方案

### 8.1 调用链路

```
浏览器 -> Nginx
  ├── /api/auth/*     -> Java user-service (JWT 鉴权)
  └── /api/agent/*    -> Java -> Python agent-service:8000/agent/*
                     （Java 提取 user_id 注入 Header 后转发）
```

### 8.2 鉴权流程

```
请求到达 Java
  → JwtAuthFilter 拦截
  → 提取 Authorization: Bearer xxx
  → 校验 JWT 签名+过期时间
  → 提取 user_id 存入 SecurityContext
  → 转发请求到 Python Agent（附带 user_id）
```

### 8.3 Nginx 配置

```nginx
server {
    listen 80;
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
    location /api/auth/ {
        proxy_pass http://user-service:9001;
    }
    location /api/agent/ {
        proxy_pass http://agent-service:8000;  # Python 的 /agent/* 接口
    }
}
```

---

## 九、数据库设计

### 9.1 MySQL（Java 业务库）
- 数据库名：`ouragent`，字符集 `utf8mb4`
- 核心表：`users`（用户）、`refresh_tokens`（刷新令牌）

### 9.2 PostgreSQL（Python Agent 库）
- 数据库名：`agent_db`
- 核心表：`conversations`（对话）、`agent_logs`（日志）

### 9.3 Redis 缓存
| Key 模式 | 用途 | 过期 |
|---------|------|------|
| `session:{user_id}` | 用户会话 | 30min |
| `chat:{session_id}` | 对话上下文 | 24h |


---

## 十、项目目录结构

```
ouragent/                              # 项目根目录
│
├── PROJECT.md                         # 本文档
├── README.md                          # 快速入门
├── docker-compose.yml                 # Docker 编排
├── Dockerfile                         # Agent 服务 Dockerfile
│
├── src/                               # ===== Python API 层 =====
│   ├── api.py                         # FastAPI 应用（REST 端点）
│   └── grpc/
│       └── agent.proto                # gRPC 协议定义
│
├── v3/                                # ===== Python Agent 核心框架 =====
│   ├── src/
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py               # Agent 核心类
│   │   │   ├── memory.py              # 记忆管理
│   │   │   └── tools.py               # 工具系统
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── config.py              # 配置管理
│   │   │   └── logger.py              # 日志
│   │   └── main.py                    # 独立入口
│   ├── tests/
│   │   ├── test_agent.py
│   │   ├── test_config.py
│   │   └── test_tools.py
│   ├── examples/
│   │   ├── basic_agent.py
│   │   └── advanced_agent.py
│   ├── config/                        # 配置文件
│   ├── docs/                          # 子文档
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── Makefile
│
├── user-service/                      # ===== [Java] 用户服务（待建）=====
│   ├── pom.xml                        # Maven 配置
│   └── src/main/java/com/ouragent/user/
│       ├── UserApplication.java       # 启动类
│       ├── controller/AuthController.java
│       ├── service/UserService.java
│       ├── service/JwtService.java
│       ├── repository/UserRepository.java
│       ├── model/User.java
│       ├── dto/*.java
│       └── middleware/JwtAuthFilter.java
│
├── frontend/                          # ===== [Vue3] 前端（待建）=====
│   ├── src/views/Login.vue
│   ├── src/views/Register.vue
│   ├── src/api/index.js               # Axios 封装
│   ├── src/router/index.js            # 路由守卫
│   └── nginx.conf
│
├── javaarea/                          # ===== Java 参考代码（已有）=====
│   ├── pom.xml
│   ├── AgentController.java
│   ├── AgentServiceClient.java
│   ├── AgentServiceConfig.java
│   └── application-agent.yml
│
└── docs/                              # 文档
    ├── JAVA_INTEGRATION_GUIDE.md
    └── MICROSERVICE_ARCHITECTURE.md
```


---

## 十一、开发流程（傻瓜式教学版）

> 每步标注了"谁来做"、"做什么"、"怎么做"、"验证方式"。

---

### 阶段零：准备工作（第 0 天）

#### Z.1 安装软件

| 软件 | 版本 | 验证命令 |
|------|------|---------|
| Python | >=3.10 | `python --version` |
| JDK | 17 | `java -version` |
| Maven | >=3.9 | `mvn --version` |
| Node.js | >=18 | `node --version` |
| Docker Desktop | 最新 | `docker --version` |
| Git | >=2.30 | `git --version` |

#### Z.2 进入项目并创建虚拟环境

```bash
cd C:\Users\23705\ouragent   # 或 cd ouragent

# 创建 Python 虚拟环境
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

# 安装 Agent 框架依赖
pip install -r v3/requirements.txt

# 验证
python -c "from src.core.agent import Agent; print('OK')"
```

#### Z.3 启动 Docker 依赖

```bash
docker-compose up -d
docker-compose ps
# 看到 agent-service、redis、postgres 状态为 Up
```

---

### 阶段一：Agent 服务完善（第 1-3 天）

#### 【第 1 天】任务 1.1：理解并启动现有代码

**谁来做**：你
**目标**：让现有 Python Agent 服务跑起来，熟悉代码。

```bash
# 安装依赖（如果还没装）
pip install -r v3/requirements.txt

# 启动服务（根目录 docker-compose 已配置，或手动启动）
# 方式 A：Docker
docker-compose up -d agent-service

# 方式 B：手动
python -m src.api
```

**验证**：

```bash
curl http://localhost:8000/health
# 期望：{"status":"healthy","agent_available":true}

curl http://localhost:8000/agent/status
# 期望：Agent 状态信息

curl http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"你好\"}"
# 期望：{"response":"...","agent_id":"...","status":"success"}

curl http://localhost:8000/agent/tools
# 期望：工具列表
```

#### 【第 2 天】任务 1.2：扩展 Agent 为多智能体

**谁来做**：你
**目标**：基于 `v3/src/core/agent.py` 的 Agent 基类，创建多个子类 Agent。

```python
# 在 v3/src/core/agents/ 目录下创建（新建目录）
# 或直接在 v3/src/core/ 下创建

# profile_agent.py
from .agent import Agent

class ProfileAgent(Agent):
    def __init__(self):
        super().__init__(name="ProfileAgent", description="分析学生画像")

    def analyze(self, user_id: str) -> dict:
        # 调用大模型分析
        history = self.memory.get_history()
        return {"level": "beginner", "weaknesses": ["Python基础"]}
```

```python
# planner_agent.py
class PlannerAgent(Agent):
    def __init__(self):
        super().__init__(name="PlannerAgent", description="学习路径规划")

    def generate_plan(self, profile: dict) -> list:
        return [
            {"topic": "Python基础", "days": 3},
            {"topic": "数据结构", "days": 5},
        ]
```

```python
# resource_agent.py
class ResourceAgent(Agent):
    def __init__(self):
        super().__init__(name="ResourceAgent", description="教学资源生成")

    def generate_question(self, topic: str) -> dict:
        return {"type": "choice", "question": "...", "answer": "..."}

    def generate_mindmap(self, topic: str) -> str:
        return "# 思维导图\n- 知识点1\n  - 子知识点"
```

```python
# evaluator_agent.py
class EvaluatorAgent(Agent):
    def __init__(self):
        super().__init__(name="EvaluatorAgent", description="学习评估")

    def evaluate(self, answers: list) -> dict:
        return {"score": 85, "feedback": "基础扎实，需要加强实践"}
```

**验证**：

```python
# 测试
from v3.src.core.profile_agent import ProfileAgent
agent = ProfileAgent()
result = agent.analyze("user_001")
print(result)
```

#### 【第 3 天】任务 1.3：扩展 API 层（src/api.py）

**谁来做**：你
**目标**：在 `src/api.py` 中添加新的端点，把多 Agent 能力暴露为 REST API。

在 `src/api.py` 中新增以下端点：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/agent/analyze` | POST | 学生画像分析 |
| `/agent/plan` | POST | 学习路径规划 |
| `/agent/generate` | POST | 资源生成 |
| `/agent/evaluate` | POST | 学习评估 |

```python
# 在 src/api.py 末尾添加

class AnalyzeRequest(BaseModel):
    user_id: str

@app.post("/agent/analyze")
async def analyze(request: AnalyzeRequest):
    """学生画像分析"""
    profile_agent = ProfileAgent()
    result = profile_agent.analyze(request.user_id)
    return {"status": "success", "profile": result}
```

**验证**：

```bash
curl -X POST http://localhost:8000/agent/analyze \
  -H "Content-Type: application/json" \
  -d '{"user_id":"001"}'
# 期望返回画像数据
```


---

### 阶段二：Java 用户服务（第 4-6 天）

#### 【第 4 天】任务 2.1：搭建 Spring Boot 项目

**谁来做**：队友B
**目标**：利用 `javaarea/pom.xml` 的依赖，创建完整的 user-service。

```bash
# 创建目录
mkdir -p user-service/src/main/java/com/ouragent/user/{config,controller,service,repository,model,dto,middleware}
mkdir -p user-service/src/main/resources

# 复制参考代码的 pom.xml 并扩展
# javaarea/pom.xml 已有 Spring Boot + JWT 依赖，复制过来
```

#### 【第 5-6 天】任务 2.2-2.3：实现注册/登录 API

**谁来做**：队友B
**目标**：实现完整的 JWT 鉴权。

**核心类**（参考 `javaarea/` 的代码风格）：

| 类 | 说明 | 参考文件 |
|----|------|---------|
| `User.java` | 用户实体 | 从 `javaarea/` 扩展 |
| `UserRepository.java` | 数据访问 | — |
| `JwtService.java` | JWT 生成/校验 | `javaarea/AgentServiceConfig.java` |
| `UserService.java` | 注册/登录逻辑 | — |
| `AuthController.java` | API 端点 | `javaarea/AgentController.java` |
| `SecurityConfig.java` | 安全配置 | `javaarea/AgentServiceConfig.java` |

**验证**：

```bash
# 确保 MySQL 已启动
docker-compose up -d mysql

# 启动 Java 服务
cd user-service
mvn spring-boot:run

# 测试注册
curl -X POST http://localhost:9001/api/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"alice\",\"email\":\"alice@test.com\",\"password\":\"123456\"}"

# 测试登录
curl -X POST http://localhost:9001/api/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"alice@test.com\",\"password\":\"123456\"}"
```

---

### 阶段三：前端认证（第 7-8 天）

#### 【第 7 天】任务 3.1：初始化 Vue3 项目

**谁来做**：队友A

```bash
cd ouragent
npm create vite@latest frontend -- --template vue
cd frontend
npm install
npm install vue-router@4 pinia element-plus axios
npm run dev
```

#### 【第 8 天】任务 3.2：实现登录/注册页面

**谁来做**：队友A

创建以下文件：
- `src/views/Login.vue`：邮箱+密码登录表单
- `src/views/Register.vue`：用户名+邮箱+密码+确认密码
- `src/api/index.js`：Axios 封装（自动添加 Token）
- `src/router/index.js`：路由守卫（未登录跳转 /login）

验证方式：
- 访问 `http://localhost:5173/login` 看到登录表单
- 输入错误邮箱格式有校验提示
- 登录成功后跳转首页

---

### 阶段四：Agent 增强与资源生成（第 9-13 天）

**谁来做**：你 + 队友A + 队友B

| 天数 | 任务 | 负责人 | 操作 |
|------|------|--------|------|
| 第9天 | 接入星火大模型 | 你 | 在 `v3/src/core/llm/` 创建 SparkLLM 类 |
| 第10天 | Profile + Planner Agent 完善 | 你 | 调用大模型做真实分析 |
| 第11天 | Resource Agent 题目/思维导图生成 | 你 | 新建工具类继承 Tool |
| 第12天 | 前端对话 + 学习页面 | 队友A | 对接 `/agent/chat` |
| 第13天 | Tutor + Evaluator Agent | 你 | 对话辅导 + 评估 |

---

### 阶段五：工具集成与 RAG（第 14-17 天）

| 天数 | 任务 | 负责人 | 操作 |
|------|------|--------|------|
| 第14天 | Resource Agent 文档/PPT 生成 | 你 | python-pptx / markdown 库 |
| 第15天 | RAG 知识库（Milvus） | 你 | 文档分块+向量化+检索 |
| 第16天 | 前端资源展示页 | 队友A | 展示/下载生成的资源 |
| 第17天 | 前端首页 | 队友A | 仪表盘+引导 |

---

### 阶段六：测试与部署（第 18-20 天）

| 天数 | 任务 | 负责人 | 操作 |
|------|------|--------|------|
| 第18天 | 集成测试 | 所有人 | 测试完整流程：注册->登录->对话->生成资源 |
| 第19天 | Docker 完善 | 队友B | 编写 user-service Dockerfile + 更新 docker-compose |
| 第20天 | 最终检查 | 所有人 | 比赛要求检查 + 演示准备 |

**Docker 检查清单**：
- [ ] `src/api.py` 通过 Docker 启动（已有 `Dockerfile`）
- [ ] `user-service` 有 Dockerfile
- [ ] `frontend` 有 Dockerfile + nginx.conf
- [ ] `docker-compose.yml` 包含所有服务
- [ ] `docker-compose up -d` 正常启动
- [ ] `http://localhost:8000/health` 返回 healthy
- [ ] `http://localhost:9001/api/auth/register` 可注册
- [ ] `http://localhost:3000` 看到前端页面


---

## 十二、Docker 部署

```bash
# 一键启动
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f agent-service
```

| 服务 | 端口映射 | 依赖 | 状态 |
|------|---------|------|------|
| agent-service | 8000:8000 | redis, postgres | **已有 Dockerfile** |
| user-service | 9001:9001 | mysql, redis | 待建 |
| frontend | 3000:80 | user-service, agent-service | 待建 |
| mysql | 3306:3306 | — | Docker |
| postgres | 5432:5432 | — | Docker |
| redis | 6379:6379 | — | Docker |

---

## 十三、环境变量

| 变量 | 默认值 | 服务 | 说明 |
|------|--------|------|------|
| `JWT_SECRET` | — | Java | JWT 签名密钥 |
| `JWT_ACCESS_EXPIRE` | 1800 | Java | Access Token 过期秒数 |
| `JWT_REFRESH_EXPIRE` | 604800 | Java | Refresh Token 过期秒数 |
| `MYSQL_HOST` | mysql | Java | MySQL 地址 |
| `MYSQL_DB` | ouragent | Java | MySQL 数据库 |
| `POSTGRES_HOST` | postgres | Python | PostgreSQL 地址 |
| `REDIS_HOST` | redis | 通用 | Redis 地址 |
| `SPARK_APP_ID` | — | Python | 星火 APP ID |
| `SPARK_API_KEY` | — | Python | 星火 API Key |
| `MIKO_API_KEY` | — | Python | MiMo API Key |
| `PORT` | 8000 | Python | Agent 服务端口 |
| `DEBUG` | true | Python | 调试模式 |

---

## 十四、风险与应对

| 风险 | 概率 | 应对 |
|------|------|------|
| 星火 API 延迟 | 中 | 现有 Agent 框架可先本地运行，前端加 loading |
| 时间不够 | 高 | 现有代码已有基础 Agent + API，只需扩展子类和前端 |
| Java-Python 联调 | 中 | `javaarea/` 已有参考代码，`src/api.py` 已有接口 |
| 多智能体要求 | 低 | `agent.py` 基类完善，继承扩展即可 |

---

## 十五、团队分工

| 角色 | 负责 | 涉及代码 |
|------|------|---------|
| **你** | 架构 + Python Agent 扩展 + 难点攻克 | `v3/src/core/` 扩展, `src/api.py` 完善 |
| **队友A** | 前端界面（Vue3）+ API 对接 | `frontend/` 新建 |
| **队友B** | Java 业务服务 + Docker | `user-service/` 新建, `docker-compose.yml` 完善 |

---

> **最后更新**：2026年6月3日
> **文档版本**：v4.0（基于现有代码 + Java Python 微服务架构）

