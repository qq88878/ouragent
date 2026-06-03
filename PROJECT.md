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
5. [Agent 服务详解（Python）](#五agent-服务详解python)
6. [Java 业务服务详解](#六java-业务服务详解)
7. [Java-Python 集成方案](#七java-python-集成方案)
8. [数据库设计](#八数据库设计)
9. [项目目录结构](#九项目目录结构)
10. [开发流程](#十一开发流程)
11. [Docker 部署](#十二docker-部署)
12. [环境变量](#十三环境变量)
13. [风险与应对](#十四风险与应对)
14. [团队分工](#十五团队分工)

---

## 一、项目概述

### 1.1 项目背景

在计算机/编程教育领域，传统"一刀切"的教学方式无法满足不同学生的个性化需求。本项目通过 **大语言模型 + 多智能体架构**，构建一个能够：

- 自动分析学生画像
- 规划个性化学习路径
- 智能生成教学资源（题库、思维导图、文档、PPT）
- 提供智能辅导与学习评估

的智能学习平台。

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

| 语言 | 负责领域 | 服务 |
|------|---------|------|
| **Python** | Agent 智能体层 | 多智能体推理、AI 对话、RAG 知识库、工具调用 |
| **Java** | 业务服务层 | 用户管理、认证授权、业务编排、API 网关 |

**双模型策略**：

| 模型 | 用途 | 优先级 |
|------|------|--------|
| **星火大模型**（Spark） | 核心功能：画像分析、路径规划、资源生成 | 主模型 |
| **小米 MiMo** | 辅助功能：对话补全、简单问答、开发测试阶段 | 备选/辅助 |


## 二、需求分析

### 2.1 用户角色

| 角色 | 编号 | 说明 |
|------|------|------|
| 学生 | R01 | 平台主要使用者，学习、做练习、查看资源 |
| 教师/管理员 | R02 | 管理学生、查看学习数据、管理系统 |
| 游客 | R03 | 未登录用户，仅可浏览首页和登录/注册 |

### 2.2 功能需求详细列表

#### 2.2.1 用户模块（Java user-service）

| 编号 | 功能 | 优先级 | 角色 | 详细描述 |
|------|------|--------|------|----------|
| F001 | 用户注册 | P0 | R01, R02 | 输入用户名+邮箱+密码，邮箱唯一校验 |
| F002 | 用户登录 | P0 | R01, R02 | 邮箱+密码登录，返回 JWT Token |
| F003 | Token 刷新 | P0 | R01, R02 | Access 过期后自动用 Refresh Token 续期 |
| F004 | 获取当前用户 | P1 | R01, R02 | 根据 Token 返回当前用户信息 |
| F005 | 退出登录 | P1 | R01, R02 | 吊销 Refresh Token |
| F006 | 用户管理 | P2 | R02 | 查看/禁用/删除用户 |

#### 2.2.2 Agent 模块（Python agent-service）

| 编号 | 功能 | 优先级 | 角色 | 详细描述 |
|------|------|--------|------|----------|
| F101 | 学生画像分析 | P0 | R01 | 根据学生答题记录，自动生成能力画像 |
| F102 | 学习路径规划 | P0 | R01 | 根据画像生成个性化的学习路线图 |
| F103 | 题目生成 | P0 | R01 | 根据知识点自动生成选择题/填空题/编程题 |
| F104 | 思维导图生成 | P0 | R01 | 将知识点结构化为思维导图（可下载） |
| F105 | 文档生成 | P1 | R01 | 生成教学文档（Markdown/PDF 可下载） |
| F106 | PPT 生成 | P1 | R01 | 根据知识点自动生成教学 PPT（可下载） |
| F107 | 智能对话辅导 | P0 | R01 | 学生提问，Agent 智能回答 |
| F108 | 学习效果评估 | P1 | R01 | 对学生的学习成果进行评分和反馈 |
| F109 | RAG 知识库检索 | P1 | R01 | 从向量库中检索相关知识增强回答质量 |
| F110 | 多轮对话管理 | P0 | R01 | 维护对话上下文，支持连续提问 |

#### 2.2.3 前端模块（Vue3 frontend）

| 编号 | 功能 | 优先级 | 角色 | 详细描述 |
|------|------|--------|------|----------|
| F201 | 登录页 | P0 | R01, R02 | 邮箱+密码登录，错误提示，记住我 |
| F202 | 注册页 | P0 | R01, R02 | 用户名+邮箱+密码+确认密码，表单校验 |
| F203 | 首页仪表盘 | P0 | R01 | 展示学习概览、推荐路径 |
| F204 | 学习路径页 | P0 | R01 | 展示学习路径图，可点击学习 |
| F205 | 智能对话页 | P0 | R01 | 与 AI 助手的聊天界面 |
| F206 | 资源管理页 | P1 | R01 | 查看/下载生成的资源 |
| F207 | 个人中心 | P1 | R01 | 个人信息、学习记录 |
| F208 | 管理后台 | P2 | R02 | 用户管理、数据统计 |

### 2.3 非功能需求

| 编号 | 分类 | 需求 | 指标 |
|------|------|------|------|
| N001 | 性能 | API 响应时间 | 常规 API < 500ms，Agent API < 5s |
| N002 | 性能 | 并发支持 | 支持 100 用户同时在线 |
| N003 | 安全 | 密码存储 | bcrypt 哈希，不允许明文存储 |
| N004 | 安全 | 接口鉴权 | 所有 API 需 JWT 校验（除登录/注册）|
| N005 | 可用性 | 系统可用性 | 核心模块 99.9% |
| N006 | 可维护性 | 容器化部署 | Docker Compose 一键启动 |
| N007 | 可扩展性 | 微服务架构 | 支持独立扩缩容每个服务 |
| N008 | 用户体验 | 页面加载 | 首屏加载 < 2s |

### 2.4 用例分析

#### 用例 UC01：学生注册使用流程

用户 -> 打开首页 -> 点击注册 -> 填写信息 -> 表单校验通过 -> 调用 POST /api/auth/register -> Java user-service 校验 -> bcrypt 加密密码 -> 存入 MySQL -> 返回成功 -> 跳转登录页 -> 登录 -> 进入首页

#### 用例 UC02：智能学习流程

用户已登录 -> 进入"智能学习"页面 -> 前端调用 POST /api/agent/study -> Nginx 透传 -> Java 校验 JWT -> 转发到 Python agent-service -> Orchestrator Agent 接收请求 -> Profile Agent 加载学生画像 -> Planner Agent 规划学习路径 -> Resource Agent 生成资源 -> Evaluator Agent 评估 -> Orchestrator 汇总 -> 返回前端

#### 用例 UC03：智能对话流程

用户 -> 打开对话页面 -> 输入问题 -> 前端调用 POST /api/agent/chat -> Python agent-service 接收 -> LangGraph 工作流启动 -> (可选) RAG 知识库检索 -> Tutor Agent 生成回答 -> 流式返回 SSE 给前端 -> 前端实时显示

### 2.5 需求矩阵（Traceability Matrix）

| 需求编号 | 功能 | 对应服务 | 优先级 | 开发阶段 |
|---------|------|---------|--------|---------|
| F001 | 用户注册 | user-service | P0 | 阶段一 |
| F002 | 用户登录 | user-service | P0 | 阶段一 |
| F003 | Token 刷新 | user-service | P0 | 阶段一 |
| F101 | 学生画像分析 | agent-service | P0 | 阶段二 |
| F102 | 学习路径规划 | agent-service | P0 | 阶段二 |
| F107 | 智能对话辅导 | agent-service | P0 | 阶段二 |
| F103 | 题目生成 | agent-service | P0 | 阶段三 |
| F104 | 思维导图生成 | agent-service | P0 | 阶段三 |
| F105 | 文档生成 | agent-service | P1 | 阶段三 |
| F106 | PPT 生成 | agent-service | P1 | 阶段三 |
| F108 | 学习效果评估 | agent-service | P1 | 阶段四 |
| F109 | RAG 知识库 | agent-service | P1 | 阶段四 |
| F201-F208 | 前端页面 | frontend | P0/P1 | 贯穿各阶段 |


## 三、系统架构

### 3.1 服务拆分

| 服务名 | 语言 | 职责 | 端口 |
|--------|------|------|------|
| `agent-service` | **Python** | 多智能体推理、对话、工具调用、RAG | 8000 |
| `user-service` | **Java** | 用户注册/登录/JWT 鉴权/用户管理 | 9001 |
| `business-service` | **Java** | 业务编排、资源管理、数据聚合 | 9002 |
| `frontend` | Vue3 + Nginx | 前端 SPA 页面 | 3000 |
| `mysql` | — | 业务数据库 | 3306 |
| `redis` | — | 缓存 / 会话 | 6379 |
| `postgres` | — | Agent 服务数据库 | 5432 |
| `milvus` | — | 向量数据库 | 19530 |

### 3.2 架构图

```
[Vue3 SPA] -> [Nginx (反向代理)]
                  |
         +--------+--------+
         |                 |
    /api/auth/*       /api/agent/*
    (登录/注册)         (智能功能)
         |                 |
[User Service (Java)] [Agent Service (Python)]
   Spring Boot 3.2       FastAPI + LangGraph
         |                 |
  [MySQL + Redis]    [Postgres + Redis]
                           |
                      [Milvus 向量库]
```

### 3.3 服务间通信

| 通信方向 | 方式 | 说明 |
|---------|------|------|
| 浏览器 -> Nginx | HTTPS | 前端静态资源和 API 请求 |
| Nginx -> Java | HTTP 反向代理 | /api/auth/* 路由到 user-service |
| Nginx -> Python | HTTP 反向代理 | /api/agent/* 路由到 agent-service |
| Java -> Python | REST / gRPC | Java 调用 Agent 功能 |
| Java -> MySQL | Spring Data JPA | ORM 操作业务数据 |
| Python -> Postgres | SQLAlchemy | ORM 操作 Agent 数据 |
| Python -> Redis | redis-py | 缓存对话上下文 |
| Python -> Milvus | pymilvus | 向量存储与检索 |


## 四、技术栈

### 4.1 Python 技术栈（Agent 服务）

| 组件 | 选型 | 版本参考 | 用途 |
|------|------|---------|------|
| Web 框架 | FastAPI | >=0.109 | API 接口 |
| ASGI 服务器 | Uvicorn | >=0.27 | 高性能异步服务器 |
| AI 框架 | LangChain | >=0.1 | LLM 调用链 |
| 工作流框架 | LangGraph | >=0.0.34 | 多智能体协作图 |
| 大模型 SDK | Spark AI SDK | -- | 星火大模型接入 |
| 向量库 | Milvus / ChromaDB | -- | 知识库向量存储 |
| ORM | SQLAlchemy | >=2.0 | 数据库操作 |
| 数据库迁移 | Alembic | -- | 数据库版本管理 |
| 通信 | grpcio | -- | gRPC 服务 |
| HTTP 客户端 | httpx | -- | 异步 HTTP 调用 |
| 任务队列 | Celery（可选）| -- | 异步任务处理 |

### 4.2 Java 技术栈（业务服务）

| 组件 | 选型 | 版本参考 | 用途 |
|------|------|---------|------|
| 框架 | Spring Boot | 3.2.x | 微服务框架 |
| JDK | Java 17 | LTS | 运行环境 |
| 认证 | Spring Security | 6.x | 安全框架 |
| JWT | jjwt | 0.12.x | Token 生成/校验 |
| 加密 | BCryptPasswordEncoder | -- | 密码哈希 |
| ORM | Spring Data JPA | 3.x | 数据库操作 |
| 数据库 | MySQL | 8.0 | 业务数据存储 |
| 缓存 | Redis + Spring Cache | 7.x | 缓存加速 |
| 构建 | Maven | 3.9 | 项目构建 |
| API 文档 | SpringDoc OpenAPI | 2.x | Swagger 文档 |
| 服务调用 | OpenFeign | 4.x | Java 服务间调用 |

### 4.3 前端技术栈

| 组件 | 选型 | 版本参考 | 用途 |
|------|------|---------|------|
| 框架 | Vue 3 | >=3.4 | 前端 SPA 框架 |
| 构建工具 | Vite | >=5.0 | 快速构建 |
| UI 库 | Element Plus | >=2.5 | 组件库 |
| HTTP 客户端 | Axios | >=1.6 | API 调用 |
| 路由 | Vue Router | >=4.2 | 前端路由 |
| 状态管理 | Pinia | >=2.1 | 状态管理 |


## 五、Agent 服务详解（Python 智能体区块）

### 5.1 定位

**Agent 服务是项目的智能核心**，所有 AI 相关的功能都集中在此。采用 LangGraph 构建多智能体协作图（StateGraph），实现任务的分解、调度与执行。

### 5.2 多智能体设计

| Agent 名称 | 类名 | 职责 |
|-----------|------|------|
| **Orchestrator Agent** | `OrchestratorAgent` | 任务接收、解析、分解、调度子 Agent、汇总结果 |
| **Profile Agent** | `ProfileAgent` | 学生画像构建与动态更新 |
| **Planner Agent** | `PlannerAgent` | 个性化学习路径规划 |
| **Resource Agent** | `ResourceAgent` | 教学资源生成（题库、思维导图、文档、PPT）|
| **Tutor Agent** | `TutorAgent` | 智能辅导、对话答疑（流式输出 SSE）|
| **Evaluator Agent** | `EvaluatorAgent` | 学习效果评估与反馈 |

### 5.3 工作流程图

```
[用户请求] -> Nginx -> Java(JWT校验) -> Python Agent

            +-------------------------------------+
            |       Orchestrator Agent            |
            |  接收请求 -> 解析意图 -> 任务分解     |
            +----+----+----+----+----+-----------+
                 |    |    |    |    |
                 v    v    v    v    v
            +--+ +--+ +--+ +--+ +--+
            |Pro| |Pla| |Res| |Tut| |Eva|
            |fil| |nne| |our| |or | |lua|
            |e  | |r  | |ce | |   | |tor|
            +--+ +--+ +--+ +--+ +--+
                 |    |    |    |    |
                 +----+----+----+----+
                         |
            +------------v------------+
            |  Orchestrator Agent     |
            |  汇总结果 -> 格式化 -> 返回 |
            +-------------------------+

            [返回 JSON 给前端]
```

### 5.4 Agent 服务 API 设计

| 端点 | 方法 | 说明 | 请求参数 |
|------|------|------|---------|
| `/api/agent/chat` | POST | 智能对话（流式 SSE）| `{ message, session_id }` |
| `/api/agent/analyze` | POST | 学生画像分析 | `{ user_id }` |
| `/api/agent/plan` | POST | 学习路径规划 | `{ user_id, subject }` |
| `/api/agent/generate` | POST | 资源生成 | `{ type, topic, config }` |
| `/api/agent/evaluate` | POST | 学习评估 | `{ user_id, answers }` |
| `/api/agent/health` | GET | 健康检查 | -- |

### 5.5 Agent 服务目录结构

```
agent-service/                    # [Python] Agent 服务根目录
|
+-- src/                          # 源代码
|   +-- api.py                    # FastAPI 应用入口
|   |   @app.get("/health")       # 健康检查
|   |   @app.post("/api/agent/*") # Agent API
|   |
|   +-- core/                     # 核心逻辑
|   |   +-- agents/               # 多智能体定义
|   |   |   +-- __init__.py
|   |   |   +-- base_agent.py             # Agent 基类
|   |   |   +-- orchestrator_agent.py     # 编排 Agent
|   |   |   +-- profile_agent.py          # 画像 Agent
|   |   |   +-- planner_agent.py          # 规划 Agent
|   |   |   +-- resource_agent.py         # 资源 Agent
|   |   |   +-- tutor_agent.py            # 辅导 Agent
|   |   |   +-- evaluator_agent.py        # 评估 Agent
|   |   |
|   |   +-- graph/                # LangGraph 工作流
|   |   |   +-- __init__.py
|   |   |   +-- state.py          # 状态定义
|   |   |   +-- workflow.py       # 工作流定义
|   |   |
|   |   +-- llm/                  # 大模型封装
|   |   |   +-- __init__.py
|   |   |   +-- base.py           # LLM 基类
|   |   |   +-- spark.py          # 星火模型封装
|   |   |   +-- mimo.py           # MiMo 模型封装
|   |   |
|   |   +-- rag/                  # RAG 知识库
|   |   |   +-- __init__.py
|   |   |   +-- vector_store.py   # 向量库操作
|   |   |   +-- retriever.py      # 检索器
|   |
|   +-- utils/                    # 工具函数
|   |   +-- __init__.py
|   |   +-- tools.py              # 工具函数
|   |   +-- helpers.py            # 辅助函数
|   |
|   +-- models/                   # 数据模型
|   |   +-- __init__.py
|   |   +-- schemas.py            # Pydantic 模型
|   |   +-- database.py           # 数据库模型
|   |
|   +-- grpc/                     # gRPC 定义
|       +-- __init__.py
|       +-- agent.proto           # protobuf 定义
|       +-- server.py             # gRPC 服务端
|
+-- tests/                        # 测试
|   +-- __init__.py
|   +-- test_api.py
|   +-- test_agents/
|   +-- test_rag/
|
+-- config/                       # 配置文件
|   +-- __init__.py
|   +-- settings.py               # 配置管理
|   +-- config.yaml               # 配置文件
|
+-- migrations/                   # 数据库迁移
|   +-- versions/
|
+-- alembic.ini                   # Alembic 配置
+-- requirements.txt              # Python 依赖
+-- Dockerfile                    # Docker 构建
+-- docker-entrypoint.sh          # Docker 启动脚本
+-- main.py                       # 启动入口


## 六、Java 业务服务详解

### 6.1 user-service 模块

#### 6.1.1 数据库设计

**users 表（MySQL）**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | 用户ID |
| username | VARCHAR(50) | UNIQUE, NOT NULL | 用户名 |
| email | VARCHAR(100) | UNIQUE, NOT NULL | 邮箱（登录凭证）|
| password_hash | VARCHAR(255) | NOT NULL | bcrypt 哈希值 |
| avatar | VARCHAR(255) | DEFAULT NULL | 头像URL |
| role | VARCHAR(20) | DEFAULT student | 角色：student/admin |
| status | TINYINT | DEFAULT 1 | 状态：1=正常 0=禁用 |
| created_at | DATETIME | NOT NULL | 注册时间 |
| updated_at | DATETIME | NOT NULL | 更新时间 |

**refresh_tokens 表（MySQL）**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | 主键 |
| user_id | BIGINT | FK -> users.id | 用户ID |
| token | VARCHAR(255) | UNIQUE, NOT NULL | Refresh Token |
| expires_at | DATETIME | NOT NULL | 过期时间 |
| created_at | DATETIME | NOT NULL | 创建时间 |

#### 6.1.2 JWT 设计

| 项目 | 说明 |
|------|------|
| Access Token 时效 | 30 分钟（1800 秒）|
| Refresh Token 时效 | 7 天（604800 秒）|
| Payload | sub(user_id), email, role, iat(签发时间), exp(过期时间) |
| 签名算法 | HS256（HMAC-SHA256）|
| 密钥来源 | 环境变量 `JWT_SECRET` |
| Refresh 存储 | 数据库存储，支持单设备登录吊销 |

#### 6.1.3 API 设计

| 端点 | 方法 | 认证 | 请求体 | 响应 |
|------|------|------|--------|------|
| /api/auth/register | POST | 无需 | { username, email, password } | 201: { code:0, data:{...} } |
| /api/auth/login | POST | 无需 | { email, password } | 200: { code:0, data:{accessToken,refreshToken,user} } |
| /api/auth/refresh | POST | 无需 | { refreshToken } | 200: { code:0, data:{new tokens} } |
| /api/auth/me | GET | Bearer | -- | 200: { code:0, data:{user info} } |
| /api/auth/logout | POST | Bearer | { refreshToken } | 200: { code:0, message:"ok" } |

**统一响应格式**：
```
{
    "code": 0,           // 错误码，0=成功
    "message": "success", // 错误信息
    "data": { ... }      // 响应数据
}
```

**统一错误码**：

| code | message | HTTP 状态码 | 说明 |
|------|---------|-----------|------|
| 0 | success | 200/201 | 成功 |
| 1001 | invalid_input | 400 | 参数校验失败 |
| 1002 | email_already_exists | 409 | 邮箱已注册 |
| 1003 | username_already_exists | 409 | 用户名已注册 |
| 1004 | invalid_credentials | 401 | 邮箱或密码错误 |
| 1005 | account_disabled | 403 | 账号已禁用 |
| 2001 | token_expired | 401 | Token 已过期 |
| 2002 | token_invalid | 401 | Token 无效 |
| 2003 | unauthorized | 401 | 未授权访问 |

### 6.2 business-service 模块（待建）

| 职责 | 说明 |
|------|------|
| 业务编排 | 协调多个服务完成复杂业务流程 |
| 资源管理 | 管理生成的资源文件存储 |
| 数据聚合 | 聚合学习数据提供统计接口 |


## 七、Java-Python 集成方案

### 7.1 调用链路

(1) 浏览器发送 HTTPS 请求到 Nginx
(2) Nginx 根据路径转发：
    - /api/auth/* -> Java user-service
    - /api/agent/* -> Python agent-service（Nginx 直接转发，Java 先鉴权）
(3) Java 侧实现 JWT 鉴权过滤器，对 /api/* 请求校验 Token：
    - 提取 Authorization: Bearer xxx
    - 校验 JWT 签名
    - 校验 JWT 是否过期
    - 从 Payload 提取 user_id
    - 存入 SecurityContextHolder
(4) Java 调用 Python Agent（内部网络）：
    - 通过 RestTemplate/WebClient 发送 HTTP 请求
    - 在 Header 中注入 user_id
    - Python 信任内部网络，无需自行鉴权
(5) Python 处理完毕返回结果

### 7.2 Nginx 配置示例

```
# frontend/nginx.conf
server {
    listen 80;

    # 前端静态文件
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # 转发到 Java user-service
    location /api/auth/ {
        proxy_pass http://user-service:9001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 转发到 Python agent-service
    location /api/agent/ {
        proxy_pass http://agent-service:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-User-ID "";  # Java 注入用户ID
    }
}
```

### 7.3 Java 调用 Python Agent 的代码示例

```java
// 方式一：REST 调用（推荐，简单直接）
// 使用 RestTemplate
@Service
public class AgentServiceClient {

    private final RestTemplate restTemplate;

    public AgentServiceClient() {
        this.restTemplate = new RestTemplate();
    }

    public String chat(Long userId, String message) {
        // 请求体
        Map<String, Object> request = new HashMap<>();
        request.put("user_id", userId.toString());
        request.put("message", message);

        // 调用 Python Agent 服务
        ResponseEntity<String> response = restTemplate.postForEntity(
            "http://agent-service:8000/api/agent/chat",
            request,
            String.class
        );

        return response.getBody();
    }

    public String analyzeStudent(Long userId) {
        Map<String, Object> request = new HashMap<>();
        request.put("user_id", userId.toString());

        ResponseEntity<String> response = restTemplate.postForEntity(
            "http://agent-service:8000/api/agent/analyze",
            request,
            String.class
        );

        return response.getBody();
    }
}
```

```python
# Python 侧接收（示例）
# agent-service/src/api.py

from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()

class ChatRequest(BaseModel):
    user_id: str
    message: str

@app.post("/api/agent/chat")
async def chat(request: ChatRequest):
    # request.user_id 由 Java 透传
    # request.message 用户问题
    # ... 调用 LangGraph 工作流 ...
    return {"response": "AI 回答内容"}

@app.post("/api/agent/analyze")
async def analyze(request: AnalyzeRequest):
    # 分析学生画像
    return {"profile": {...}}
```


## 八、数据库设计

### 8.1 MySQL（Java 业务数据库）

| 数据库属性 | 值 |
|-----------|-----|
| 数据库名 | ouragent |
| 字符集 | utf8mb4 |
| 排序规则 | utf8mb4_unicode_ci |
| 表 | users, refresh_tokens, learning_records, resources |

### 8.2 PostgreSQL（Python Agent 数据库）

| 数据库属性 | 值 |
|-----------|-----|
| 数据库名 | agent_db |
| 字符集 | UTF8 |
| 表 | conversations, agent_logs, student_profiles, generated_resources |

### 8.3 Redis 缓存

| Key 模式 | 用途 | 过期时间 |
|---------|------|---------|
| session:{user_id} | 用户会话 | 30 分钟 |
| chat:{session_id} | 对话上下文 | 24 小时 |
| profile:{user_id} | 画像缓存 | 1 小时 |
| rate_limit:{ip} | 接口限流 | 1 分钟 |

### 8.4 Milvus 向量库

| Collection | 维度 | 用途 |
|-----------|------|------|
| knowledge_vectors | 1536 | 知识点向量 |
| resource_vectors | 1536 | 资源向量索引 |

## 九、项目目录结构

```
ouragent/                              # 项目根目录
|
+-- PROJECT.md                         # 本文档（项目手册）
+-- README.md                          # 快速入门
+-- docker-compose.yml                 # Docker 编排文件（一键启动）
|
+-- agent-service/                     # ===== [Python] Agent 智能体服务 =====
|   +-- src/
|   |   +-- api.py                     # FastAPI 应用入口
|   |   +-- core/
|   |   |   +-- agents/                # 多智能体定义
|   |   |   +-- graph/                 # LangGraph 工作流
|   |   |   +-- llm/                   # 大模型封装
|   |   |   +-- rag/                   # RAG 知识库
|   |   +-- utils/                     # 工具函数
|   |   +-- models/                    # 数据模型
|   |   +-- grpc/                      # gRPC 定义
|   +-- tests/                         # 测试
|   +-- config/                        # 配置
|   +-- migrations/                    # 数据库迁移
|   +-- requirements.txt               # Python 依赖
|   +-- Dockerfile
|   +-- docker-entrypoint.sh
|   +-- main.py                        # 启动入口
|
+-- user-service/                      # ===== [Java] 用户服务 =====
|   +-- pom.xml                        # Maven 构建文件
|   +-- src/main/java/com/ouragent/user/
|   |   +-- UserApplication.java       # 启动类
|   |   +-- config/                    # 配置
|   |   |   +-- SecurityConfig.java    # Spring Security 配置
|   |   |   +-- JwtConfig.java         # JWT 配置
|   |   |   +-- WebConfig.java         # Web 配置
|   |   +-- controller/                # API 控制器
|   |   |   +-- AuthController.java    # 认证接口
|   |   +-- service/                   # 业务服务
|   |   |   +-- UserService.java       # 用户服务
|   |   |   +-- JwtService.java        # JWT 服务
|   |   +-- repository/                # 数据访问
|   |   |   +-- UserRepository.java
|   |   |   +-- RefreshTokenRepository.java
|   |   +-- model/                     # 实体模型
|   |   |   +-- User.java
|   |   |   +-- RefreshToken.java
|   |   +-- dto/                       # 数据传输对象
|   |   |   +-- RegisterRequest.java
|   |   |   +-- LoginRequest.java
|   |   |   +-- RefreshRequest.java
|   |   |   +-- AuthResponse.java
|   |   |   +-- ApiResponse.java
|   |   +-- middleware/                # 中间件
|   |       +-- JwtAuthFilter.java     # JWT 鉴权过滤器
|   +-- src/main/resources/
|   |   +-- application.yml            # Spring 主配置
|   |   +-- schema.sql                 # SQL 初始化脚本
|   +-- Dockerfile
|
+-- business-service/                  # ===== [Java] 业务服务（待建）=====
|   +-- pom.xml
|   +-- src/
|
+-- frontend/                          # ===== [Vue3] 前端 =====
|   +-- src/
|   |   +-- views/
|   |   |   +-- Login.vue             # 登录页
|   |   |   +-- Register.vue          # 注册页
|   |   |   +-- Home.vue              # 首页
|   |   +-- api/
|   |   |   +-- index.js              # Axios 封装
|   |   +-- store/
|   |   |   +-- auth.js               # Pinia 认证状态
|   |   +-- router/
|   |       +-- index.js              # 路由守卫
|   +-- nginx.conf                     # Nginx 配置
|   +-- Dockerfile
|   +-- package.json
|
+-- docs/                              # 文档
|   +-- JAVA_INTEGRATION_GUIDE.md
|   +-- MICROSERVICE_ARCHITECTURE.md
|
+-- javaarea/                          # Java 参考示例
|   +-- pom.xml
|   +-- AgentController.java
|   +-- AgentServiceClient.java
|   +-- AgentServiceConfig.java


## 十、开发流程（傻瓜式教学版）

> 本章是全文最长的章节，每步标注了"谁来做"、"耗时"、"做什么"、"怎么做"、"怎么验证"。

---

### 阶段零：准备工作（第 0 天）

#### 步骤 Z.1：安装必需软件

| 软件 | 必须安装？| 版本要求 | 下载地址 | 验证命令 |
|------|---------|---------|---------|---------|
| Git | 是 | >=2.30 | https://git-scm.com/ | `git --version` |
| Python | 是 | >=3.10 | https://python.org/ | `python --version` |
| JDK | 是 | 17 LTS | https://adoptium.net/ | `java -version` |
| Maven | 是 | >=3.9 | https://maven.apache.org/ | `mvn --version` |
| Node.js | 是 | >=18 | https://nodejs.org/ | `node --version` |
| Docker Desktop | 是 | 最新 | https://docker.com/ | `docker --version` |

**验证**：打开终端，输入验证命令看到版本号即成功。

**如果安装失败**：Windows 勾选"Add to PATH"；Mac 用 homebrew；Linux 用 apt/yum。

#### 步骤 Z.2：进入项目目录

```bash
cd C:\Users\23705\ouragent
# 或
cd ouragent
```

#### 步骤 Z.3：创建 Python 虚拟环境

```bash
# Windows:
python -m venv .venv
.venv\Scripts\activate

# Mac/Linux:
python3 -m venv .venv
source .venv/bin/activate
```

**验证**：命令前出现 (.venv) 字样。

#### 步骤 Z.4：启动 Docker 依赖

```bash
docker-compose up -d mysql postgres redis
docker-compose ps
# 看到 mysql、postgres、redis 状态为 Up
```


---

### 阶段一：Agent 核心（第 1-4 天）

#### 【第 1 天上午】任务 1.1：搭建 FastAPI 项目

**谁来做**：你（Agent 负责人）
**做什么**：让 Python 服务能启动并返回响应。

**第 1 步**：创建目录结构

```bash
cd ouragent
mkdir -p agent-service/src/core/agents
mkdir -p agent-service/src/core/graph
mkdir -p agent-service/src/core/llm
mkdir -p agent-service/src/core/rag
mkdir -p agent-service/src/utils
mkdir -p agent-service/src/models
mkdir -p agent-service/src/grpc
mkdir -p agent-service/tests
mkdir -p agent-service/config
```

在每个目录创建 `__init__.py` 空文件（Python 要求）。

**第 2 步**：创建 src/api.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="OurAgent Agent Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "agent-service"}
```

**第 3 步**：创建 main.py（项目根目录）

```python
import uvicorn
from src.api import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**第 4 步**：创建 requirements.txt

```txt
fastapi==0.109.0
uvicorn==0.27.0
langchain==0.1.0
langgraph==0.0.34
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
redis==5.0.1
httpx==0.26.0
pydantic==2.5.3
python-dotenv==1.0.0
```

**第 5 步**：安装并启动

```bash
cd agent-service
pip install -r requirements.txt
python main.py
```

**验证**（另开终端）：
```bash
curl http://localhost:8000/health
# 应返回：{"status":"ok","service":"agent-service"}
# 浏览器打开 http://localhost:8000/docs 看到 Swagger 页面
```

#### 【第 1 天下午】任务 1.2：LLM 基类和 Spark 封装

**谁来做**：你

**base.py** - LLM 基类

```python
# agent-service/src/core/llm/base.py
from abc import ABC, abstractmethod
from typing import List, Dict

class BaseLLM(ABC):
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], stream: bool = False) -> str:
        pass

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        pass
```

**spark.py** - 星火模型封装（框架）

```python
# agent-service/src/core/llm/spark.py
from .base import BaseLLM
import os

class SparkLLM(BaseLLM):
    def __init__(self):
        self.app_id = os.getenv("SPARK_APP_ID", "")
        self.api_key = os.getenv("SPARK_API_KEY", "")
        # TODO: 按星火官方文档实现

    async def chat(self, messages, stream=False):
        return "TODO: Spark response"

    async def generate(self, prompt):
        return await self.chat([{"role": "user", "content": prompt}])
```

#### 【第 2 天】任务 1.3：Agent 基类和 Orchestrator

**谁来做**：你

**base_agent.py** - Agent 基类

```python
# agent-service/src/core/agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pass
```

**orchestrator_agent.py** - 编排 Agent

```python
# agent-service/src/core/agents/orchestrator_agent.py
from .base_agent import BaseAgent

class OrchestratorAgent(BaseAgent):
    def __init__(self):
        super().__init__("orchestrator")
        self.agents = {}

    def register_agent(self, name: str, agent: BaseAgent):
        self.agents[name] = agent

    async def process(self, state):
        # 1. 解析意图
        state["intent"] = await self._parse_intent(state["request"])
        # 2. 分解任务
        tasks = self._decompose_tasks(state["intent"])
        # 3. 执行子任务
        state["results"] = {}
        for task in tasks:
            name = task["agent"]
            if name in self.agents:
                state["results"][name] = await self.agents[name].process(state)
        # 4. 汇总
        state["summary"] = "; ".join([f"{k}: {v}" for k, v in state["results"].items()])
        return state

    async def _parse_intent(self, request):
        if "分析" in request: return "analyze"
        if "规划" in request: return "plan"
        if "生成" in request: return "generate"
        if "评估" in request: return "evaluate"
        return "chat"

    def _decompose_tasks(self, intent):
        mapping = {
            "analyze": [{"agent": "profile_agent", "action": "analyze"}],
            "plan": [{"agent": "profile_agent", "action": "load"}, {"agent": "planner_agent", "action": "plan"}],
            "generate": [{"agent": "resource_agent", "action": "generate"}],
            "chat": [{"agent": "tutor_agent", "action": "chat"}],
            "evaluate": [{"agent": "evaluator_agent", "action": "evaluate"}],
        }
        return mapping.get(intent, [{"agent": "tutor_agent", "action": "chat"}])
```


#### 【第 3 天】任务 1.4：其他 Agent 实现

**谁来做**：你

```python
# agent-service/src/core/agents/profile_agent.py
from .base_agent import BaseAgent

class ProfileAgent(BaseAgent):
    def __init__(self):
        super().__init__("profile_agent")

    async def process(self, state):
        return {"level": "beginner", "weaknesses": ["Python基础"], "strengths": []}
```

```python
# agent-service/src/core/agents/planner_agent.py
class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__("planner_agent")

    async def process(self, state):
        return {"plan": [{"order": 1, "topic": "Python基础", "duration": "3天"}]}
```

（Resource、Tutor、Evaluator Agent 结构类似，不再赘述）

#### 【第 4 天】任务 1.5：LangGraph 工作流

**谁来做**：你

```python
# agent-service/src/core/graph/state.py
from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    user_id: str
    request: str
    intent: str
    tasks: List[Dict]
    results: Dict[str, Any]
    summary: str
```

```python
# agent-service/src/core/graph/workflow.py
from langgraph.graph import StateGraph, END
from .state import AgentState

def create_workflow(orchestrator):
    workflow = StateGraph(AgentState)
    workflow.add_node("parse", orchestrator._parse_intent)
    workflow.add_node("decompose", orchestrator._decompose_tasks)
    workflow.set_entry_point("parse")
    workflow.add_edge("parse", "decompose")
    workflow.add_edge("decompose", END)
    return workflow.compile()
```


---

### 阶段二：用户服务（第 5-7 天）

#### 【第 5 天】任务 2.1：创建 Spring Boot 项目

**谁来做**：队友B（Java 负责人）
**做什么**：让 Java 项目能启动。

**第 1 步**：创建目录

```bash
cd ouragent
mkdir -p user-service/src/main/java/com/ouragent/user/{config,controller,service,repository,model,dto,middleware}
mkdir -p user-service/src/main/resources
mkdir -p user-service/src/test/java/com/ouragent/user
```

**第 2 步**：创建 pom.xml（核心依赖）

```xml
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.1</version>
    </parent>
    <groupId>com.ouragent</groupId>
    <artifactId>user-service</artifactId>
    <version>1.0.0</version>
    <properties><java.version>17</java.version></properties>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-security</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>com.mysql</groupId>
            <artifactId>mysql-connector-j</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-api</artifactId><version>0.12.3</version>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-impl</artifactId><version>0.12.3</version><scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-jackson</artifactId><version>0.12.3</version><scope>runtime</scope>
        </dependency>
    </dependencies>
    <build><plugins>
        <plugin><groupId>org.springframework.boot</groupId><artifactId>spring-boot-maven-plugin</artifactId></plugin>
    </plugins></build>
</project>
```

**第 3 步**：创建 application.yml

```yaml
# src/main/resources/application.yml
server:
  port: 9001
spring:
  datasource:
    //url: jdbc:mysql://localhost:3306/ouragent?useUnicode=true&characterEncoding=utf8mb4&createDatabaseIfNotExist=true
    username: root
    password: root
  jpa:
    hibernate:
      ddl-auto: update
    show-sql: true
app:
  jwt:
    secret: your-jwt-secret-key-must-be-at-least-256-bits
    access-expire: 1800
    refresh-expire: 604800
```

**第 4 步**：创建 UserApplication.java

```java
package com.ouragent.user;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
@SpringBootApplication
public class UserApplication {
    public static void main(String[] args) {
        SpringApplication.run(UserApplication.class, args);
    }
}
```

**第 5 步**：验证

```bash
cd user-service
mvn clean compile
# 编译成功即通过
```


#### 【第 6 天】任务 2.2：实体类和 Repository

**谁来做**：队友B

**User.java**（用户实体）

```java
package com.ouragent.user.model;
import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity @Table(name = "users")
public class User {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(nullable = false, unique = true, length = 50)
    private String username;
    @Column(nullable = false, unique = true, length = 100)
    private String email;
    @Column(name = "password_hash", nullable = false)
    private String passwordHash;
    private String avatar;
    private String role = "student";
    private Integer status = 1;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    @PrePersist
    protected void onCreate() { createdAt = LocalDateTime.now(); updatedAt = LocalDateTime.now(); }
    @PreUpdate
    protected void onUpdate() { updatedAt = LocalDateTime.now(); }

    // getter/setter（必须全部生成，或用 Lombok @Data）
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    public String getPasswordHash() { return passwordHash; }
    public void setPasswordHash(String h) { this.passwordHash = h; }
    public String getRole() { return role; }
    public void setRole(String role) { this.role = role; }
    public Integer getStatus() { return status; }
    public void setStatus(Integer s) { this.status = s; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
}
```

**RefreshToken.java**

```java
package com.ouragent.user.model;
import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity @Table(name = "refresh_tokens")
public class RefreshToken {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;
    @Column(nullable = false, unique = true)
    private String token;
    private LocalDateTime expiresAt;
    private LocalDateTime createdAt;
    @PrePersist
    protected void onCreate() { createdAt = LocalDateTime.now(); }
    // getter/setter（省略）
}
```

**UserRepository.java**

```java
package com.ouragent.user.repository;
import com.ouragent.user.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);
    boolean existsByEmail(String email);
    boolean existsByUsername(String username);
}
```

**RefreshTokenRepository.java**

```java
package com.ouragent.user.repository;
import com.ouragent.user.model.RefreshToken;
import org.springframework.data.jpa.repository.JpaRepository;
public interface RefreshTokenRepository extends JpaRepository<RefreshToken, Long> {
    java.util.Optional<RefreshToken> findByToken(String token);
}
```


#### 【第 7 天】任务 2.3：注册/登录 API

**谁来做**：队友B

**JwtService.java**

```java
package com.ouragent.user.service;
import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.UUID;

@Service
public class JwtService {
    private final SecretKey secretKey;
    private final long accessExpireMs;
    private final long refreshExpireMs;

    public JwtService(@Value("${app.jwt.secret}") String secret,
                      @Value("${app.jwt.access-expire}") long accessSec,
                      @Value("${app.jwt.refresh-expire}") long refreshSec) {
        this.secretKey = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
        this.accessExpireMs = accessSec * 1000;
        this.refreshExpireMs = refreshSec * 1000;
    }

    public String generateAccessToken(Long userId, String email, String role) {
        return Jwts.builder()
            .subject(userId.toString())
            .claim("email", email).claim("role", role)
            .issuedAt(new Date())
            .expiration(new Date(System.currentTimeMillis() + accessExpireMs))
            .signWith(secretKey).compact();
    }

    public String generateRefreshToken() { return UUID.randomUUID().toString(); }

    public Claims validateToken(String token) {
        try {
            return Jwts.parser().verifyWith(secretKey).build()
                .parseSignedClaims(token).getPayload();
        } catch (JwtException e) { return null; }
    }

    public long getRefreshExpireMs() { return refreshExpireMs; }
}
```

**UserService.java**

```java
package com.ouragent.user.service;
import com.ouragent.user.dto.*;
import com.ouragent.user.model.*;
import com.ouragent.user.repository.*;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDateTime;

@Service
public class UserService {
    private final UserRepository userRepo;
    private final RefreshTokenRepository refreshRepo;
    private final JwtService jwtService;
    private final BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();

    public UserService(UserRepository userRepo, RefreshTokenRepository refreshRepo, JwtService jwtService) {
        this.userRepo = userRepo; this.refreshRepo = refreshRepo; this.jwtService = jwtService;
    }

    @Transactional
    public ApiResponse register(RegisterRequest req) {
        if (userRepo.existsByEmail(req.getEmail()))
            return ApiResponse.error(1002, "邮箱已注册");
        if (userRepo.existsByUsername(req.getUsername()))
            return ApiResponse.error(1003, "用户名已注册");

        User user = new User();
        user.setUsername(req.getUsername());
        user.setEmail(req.getEmail());
        user.setPasswordHash(encoder.encode(req.getPassword()));
        user = userRepo.save(user);

        String accessToken = jwtService.generateAccessToken(user.getId(), user.getEmail(), user.getRole());
        String refreshToken = jwtService.generateRefreshToken();
        saveRefreshToken(user, refreshToken);

        return ApiResponse.success(new AuthResponse(accessToken, refreshToken, toUserInfo(user)));
    }

    public ApiResponse login(LoginRequest req) {
        User user = userRepo.findByEmail(req.getEmail()).orElse(null);
        if (user == null) return ApiResponse.error(1004, "邮箱或密码错误");
        if (user.getStatus() == 0) return ApiResponse.error(1005, "账号已禁用");
        if (!encoder.matches(req.getPassword(), user.getPasswordHash()))
            return ApiResponse.error(1004, "邮箱或密码错误");

        String accessToken = jwtService.generateAccessToken(user.getId(), user.getEmail(), user.getRole());
        String refreshToken = jwtService.generateRefreshToken();
        saveRefreshToken(user, refreshToken);
        return ApiResponse.success(new AuthResponse(accessToken, refreshToken, toUserInfo(user)));
    }

    public ApiResponse getMe(String authHeader) {
        String token = extractToken(authHeader);
        if (token == null) return ApiResponse.error(2003, "未授权");
        Claims claims = jwtService.validateToken(token);
        if (claims == null) return ApiResponse.error(2001, "Token无效");
        User user = userRepo.findById(Long.parseLong(claims.getSubject())).orElse(null);
        if (user == null) return ApiResponse.error(2002, "用户不存在");
        return ApiResponse.success(toUserInfo(user));
    }

    private void saveRefreshToken(User user, String token) {
        RefreshToken rt = new RefreshToken();
        rt.setUser(user); rt.setToken(token);
        rt.setExpiresAt(LocalDateTime.now().plusSeconds(604800));
        refreshRepo.save(rt);
    }

    private UserInfo toUserInfo(User u) {
        return new UserInfo(u.getId(), u.getUsername(), u.getEmail(), u.getRole(), u.getAvatar());
    }

    private String extractToken(String header) {
        if (header == null || !header.startsWith("Bearer ")) return null;
        return header.substring(7);
    }
}
```

**AuthController.java**

```java
package com.ouragent.user.controller;
import com.ouragent.user.dto.*;
import com.ouragent.user.service.UserService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
public class AuthController {
    private final UserService userService;
    public AuthController(UserService userService) { this.userService = userService; }

    @PostMapping("/register")
    public ResponseEntity<ApiResponse> register(@RequestBody RegisterRequest req) {
        return ResponseEntity.ok(userService.register(req));
    }

    @PostMapping("/login")
    public ResponseEntity<ApiResponse> login(@RequestBody LoginRequest req) {
        return ResponseEntity.ok(userService.login(req));
    }

    @GetMapping("/me")
    public ResponseEntity<ApiResponse> getMe(@RequestHeader("Authorization") String auth) {
        return ResponseEntity.ok(userService.getMe(auth));
    }
}
```

**SecurityConfig.java**（放开认证接口）

```java
package com.ouragent.user.config;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
public class SecurityConfig {
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http.csrf(c -> c.disable())
            .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(a -> a.requestMatchers("/api/auth/**").permitAll().anyRequest().authenticated());
        return http.build();
    }
}
```

**完整验证**：

```bash
# 启动依赖
docker-compose up -d mysql

# 启动服务
cd user-service
mvn spring-boot:run

# 另开终端，测试注册
curl -X POST http://localhost:9001/api/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"alice\",\"email\":\"alice@test.com\",\"password\":\"123456\"}"

# 测试登录
curl -X POST http://localhost:9001/api/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"alice@test.com\",\"password\":\"123456\"}"

# 测试获取用户
curl http://localhost:9001/api/auth/me ^
  -H "Authorization: Bearer <上面返回的accessToken>"

# 测试重复注册（应返回错误）
curl -X POST http://localhost:9001/api/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"alice\",\"email\":\"alice@test.com\",\"password\":\"123456\"}"
# 应返回：{"code":1002,"message":"邮箱已注册","data":null}
```


---

### 阶段三：前端认证（第 8-9 天）

#### 【第 8 天】任务 3.1：初始化 Vue3

**谁来做**：队友A

```bash
cd ouragent
npm create vite@latest frontend -- --template vue
cd frontend
npm install
npm install vue-router@4 pinia element-plus @element-plus/icons-vue axios
npm run dev
# 浏览器访问 http://localhost:5173 看到 Vue 默认页
```

#### 【第 9 天】任务 3.2：登录/注册页面

**谁来做**：队友A

创建 `src/views/Login.vue`、`src/views/Register.vue`、`src/api/index.js`（Axios 封装）、`src/router/index.js`（路由守卫）。

**核心逻辑**：
- 登录：输入邮箱+密码 -> POST /api/auth/login -> 存 token -> 跳首页
- 注册：输入用户名+邮箱+密码+确认密码 -> POST /api/auth/register -> 跳登录
- 路由守卫：访问需要登录的页面时检查 token，没有则跳转 /login

**验证**：
- 访问 /login 看到登录表单
- 输入错误邮箱格式，有校验提示
- 登录成功后跳转首页

---

### 阶段四至七：后续阶段概要

#### 阶段四：Agent 增强（第 10-13 天）

| 天数 | 任务 | 负责人 | 产出 |
|------|------|--------|------|
| 第10天 | Profile Agent + Planner Agent 完整逻辑 | 你 | 画像分析 + 路径规划 API |
| 第11天 | Resource Agent + Tutor Agent | 你 | 资源生成 + 对话 API |
| 第12天 | Evaluator Agent + LangGraph 完善 | 你 | 评估 API + 工作流 |
| 第13天 | RAG 知识库（Milvus 连接+检索）| 你 | RAG 检索 API |

#### 阶段五：资源生成（第 14-17 天）

| 天数 | 任务 | 负责人 | 产出 |
|------|------|--------|------|
| 第14天 | 题目生成前端页面 | 队友A | 题目展示+在线作答 |
| 第15天 | 思维导图生成+前端渲染 | 你+队友A | markmap 渲染 |
| 第16天 | 文档生成（Markdown/PDF）| 你 | 可下载文档 |
| 第17天 | PPT 生成（python-pptx）| 你 | 可下载 PPT |

#### 阶段六：评估与优化（第 18-20 天）

| 天数 | 任务 | 负责人 |
|------|------|--------|
| 第18天 | 学习评估 API + 前端展示 | 你+队友A |
| 第19天 | 首页 + 引导页 | 队友A |
| 第20天 | 错误处理 + 全局优化 | 所有人 |

#### 阶段七：测试与部署（第 21-23 天）

| 天数 | 任务 | 负责人 | 操作 |
|------|------|--------|------|
| 第21天 | 集成测试 | 所有人 | 测试完整流程 |
| 第22天 | Docker 部署 | 队友B | Dockerfile + docker-compose |
| 第23天 | 最终检查 | 所有人 | 检查比赛要求+准备演示 |

**部署检查清单**：
- [ ] agent-service 有 Dockerfile
- [ ] user-service 有 Dockerfile
- [ ] frontend 有 Dockerfile + nginx.conf
- [ ] docker-compose.yml 包含所有服务
- [ ] 执行 docker-compose up -d 正常启动
- [ ] http://localhost:3000 看到前端
- [ ] 注册/登录正常
- [ ] Agent 功能正常


---

## 十一、Docker 部署

```bash
# 一键启动所有服务
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

| 服务 | 端口映射 | 依赖 |
|------|---------|------|
| frontend | 3000:80 | user-service, agent-service |
| user-service | 9001:9001 | mysql, redis |
| business-service | 9002:9002 | mysql, redis, user-service |
| agent-service | 8000:8000 | postgres, redis, milvus |
| mysql | 3306:3306 | -- |
| postgres | 5432:5432 | -- |
| redis | 6379:6379 | -- |
| milvus | 19530:19530 | -- |

---

## 十二、环境变量

| 变量 | 默认值 | 所属服务 | 说明 |
|------|--------|---------|------|
| JWT_SECRET | -- | Java | JWT 签名密钥（至少32字符）|
| JWT_ACCESS_EXPIRE | 1800 | Java | Access Token 过期秒数 |
| JWT_REFRESH_EXPIRE | 604800 | Java | Refresh Token 过期秒数 |
| MYSQL_HOST | mysql | Java | MySQL 地址 |
| MYSQL_DB | ouragent | Java | MySQL 数据库名 |
| MYSQL_USER | root | Java | MySQL 用户名 |
| MYSQL_PASSWORD | root | Java | MySQL 密码 |
| POSTGRES_HOST | postgres | Python | PostgreSQL 地址 |
| POSTGRES_DB | agent_db | Python | PostgreSQL 数据库名 |
| REDIS_HOST | redis | 通用 | Redis 地址 |
| MILVUS_HOST | milvus | Python | Milvus 向量库地址 |
| SPARK_APP_ID | -- | Python | 星火 APP ID |
| SPARK_API_KEY | -- | Python | 星火 API Key |
| MIKO_API_KEY | -- | Python | MiMo API Key |

---

## 十三、风险与应对

| 风险 | 概率 | 影响 | 应对方案 |
|------|------|------|---------|
| 星火 API 延迟高 | 中 | 高 | 先 MiMo 跑通流程；异步任务；前端 loading |
| 时间不够 | 高 | 高 | 砍非核心功能保 demo；先实现 P0 |
| Docker 部署问题 | 中 | 中 | 备选裸机部署方案 |
| Java-Python 联调 | 中 | 中 | 先定义 API 契约，用 Swagger 同步 |
| 数据库连接失败 | 低 | 高 | Docker healthcheck + 启动等待机制 |

---

## 十四、团队分工

| 角色 | 负责内容 | 核心产出 |
|------|---------|---------|
| **你** | 架构设计 + Python Agent 层 + 后端 API + 难点攻克 | agent-service 全部、架构文档、联调 |
| **队友A** | 前端界面（Vue3）+ API 对接 + 用户体验 | frontend 全部、与后端联调 |
| **队友B** | Java 业务服务 + RAG 知识库 + 测试部署 + Docker | user-service、docker-compose、文档 |

---

> **最后更新**：2026年6月3日
> **文档版本**：v3.0（Python Agent + Java 业务微服务架构）

