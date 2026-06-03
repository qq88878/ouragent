# OurAgent 项目开发手册

> **项目名称**：基于大模型的个性化资源生成与学习多智能体系统
> **架构版本**：v3.0（Java + Python 微服务架构）
> **更新日期**：2026年6月

## 一、项目概述

### 1.1 核心目标

构建一个 **计算机/编程领域** 的个性化学习平台，通过多智能体协作实现：
- 学生画像构建与动态更新
- 个性化学习路径规划
- 教学资源智能生成（题库、思维导图、文档、PPT）
- 智能辅导与学习效果评估

### 1.2 比赛硬性要求

| 要求 | 说明 |
|------|------|
| 必须使用星火大模型 | 核心推理引擎 |
| 必须体现多智能体 | 清晰的Agent分工与协作流程 |
| 资源必须可交互 | 生成的内容支持下载/预览 |
| 一键启动 | docker-compose up 即可运行 |

### 1.3 架构策略

**双语言微服务架构**：
- **Python（Agent 服务）**：专注 AI 推理、多智能体协作、RAG 知识库
- **Java（业务服务）**：用户管理、认证授权、业务编排、API 网关

**双模型策略**：
- **星火大模型**：核心功能（画像分析、路径规划、资源生成）
- **小米MiMo**：辅助功能（对话补全、简单问答、测试阶段）


## 二、系统架构

### 2.1 服务拆分

| 服务名 | 语言 | 职责 | 端口 |
|--------|------|------|------|
| user-service | Java | 用户注册/登录/JWT鉴权/用户管理 | 9001 |
| business-service | Java | 业务编排、资源管理、数据聚合 | 9002 |
| agent-service | Python | 多智能体推理、对话、工具调用 | 8000 |
| frontend | Vue3 + Nginx | 前端 SPA 页面 | 3000 |
| mysql | - | 业务数据库 | 3306 |
| redis | - | 缓存/会话 | 6379 |
| milvus | - | 向量数据库 | 19530 |

### 2.2 架构图

`
[Vue3 SPA] -> [Nginx]
                  |
     +------------+------------+
     |                         |
 /api/auth/*             /api/agent/*
     |                         |
[User Service (Java)]   [Agent Service (Python)]
     |                         |
[MySQL + Redis]         [Milvus + Redis]
`

### 2.3 服务间通信

- Java -> Python: REST API (同步) + gRPC (高性能)
- Java -> Java: OpenFeign
- Java -> DB: Spring Data JPA / MyBatis
- Python -> DB: SQLAlchemy


## 三、技术栈

### 3.1 Java 技术栈

| 组件 | 选型 |
|------|------|
| 框架 | Spring Boot 3.2.x |
| JDK | Java 17 |
| 认证 | Spring Security + JWT (jjwt) |
| 加密 | BCryptPasswordEncoder |
| ORM | Spring Data JPA |
| 数据库 | MySQL 8.0 |
| 缓存 | Redis + Spring Cache |
| 构建 | Maven |

### 3.2 Python 技术栈

| 组件 | 选型 |
|------|------|
| 框架 | FastAPI |
| AI框架 | LangChain + LangGraph |
| 大模型 | 星火大模型 + MiMo |
| 向量库 | Milvus / ChromaDB |
| ORM | SQLAlchemy + Alembic |
| 通信 | gRPC / REST |

### 3.3 前端技术栈

| 组件 | 选型 |
|------|------|
| 框架 | Vue 3 + Composition API |
| UI库 | Element Plus |
| 构建 | Vite |
| HTTP | Axios |
| 路由 | Vue Router |
| 状态管理 | Pinia |


## 四、用户模块详细设计（本次任务）

### 4.1 模块定位

用户模块归属于 **Java user-service**，作为独立微服务部署。

### 4.2 数据库设计

**users 表（MySQL）**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | 用户ID |
| username | VARCHAR(50) | UNIQUE, NOT NULL | 用户名 |
| email | VARCHAR(100) | UNIQUE, NOT NULL | 邮箱（登录凭证） |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt 哈希 |
| avatar | VARCHAR(255) | DEFAULT NULL | 头像URL |
| role | VARCHAR(20) | DEFAULT student | 角色 |
| status | TINYINT | DEFAULT 1 | 状态 1=正常 0=禁用 |
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

### 4.3 JWT 设计

- Access Token 时效: 30分钟
  - Payload: sub(user_id), email, role, iat, exp
  - 签名算法: HS256
  - 密钥: 环境变量 JWT_SECRET
- Refresh Token 时效: 7天
  - 用于静默续期 Access Token
  - 存储于数据库，支持吊销
### 4.4 API 设计

#### 注册

`
POST /api/auth/register
Response (201): code 0 + user data
`

#### 登录

`
POST /api/auth/login
Response (200): code 0 + accessToken + refreshToken + user
`

#### 刷新 Token

`
POST /api/auth/refresh
Response (200): code 0 + new tokens
`

#### 获取当前用户

`
GET /api/auth/me
Header: Authorization: Bearer <accessToken>
Response (200): code 0 + user info
`

#### 统一错误码

| code | message | 说明 |
|------|---------|------|
| 0 | success | 成功 |
| 1001 | invalid_input | 参数校验失败 |
| 1002 | email_already_exists | 邮箱已注册 |
| 1003 | username_already_exists | 用户名已注册 |
| 1004 | invalid_credentials | 邮箱或密码错误 |
| 1005 | account_disabled | 账号已禁用 |
| 2001 | token_expired | Token 已过期 |
| 2002 | token_invalid | Token 无效 |
| 2003 | unauthorized | 未授权访问 |


### 4.5 前端页面设计

**登录页 /login**
- 邮箱输入框 + 密码输入框
- 记住我 复选框
- 登录按钮 + 加载状态
- 没有账号？去注册 链接
- 表单校验（邮箱格式、密码非空）
- 登录成功 -> 存储 token -> 跳转首页
- 登录失败 -> 显示错误提示

**注册页 /register**
- 用户名 + 邮箱 + 密码 + 确认密码输入框
- 注册按钮 + 加载状态
- 已有账号？去登录 链接
- 表单校验（用户名长度、邮箱格式、密码强度、两次密码一致）
- 注册成功 -> 自动登录或跳转登录页
- 注册失败 -> 显示错误提示

**路由守卫**
- 未登录 -> 重定向到 /login
- Token 过期 -> 自动 refresh -> 失败则跳转登录页
- Axios 拦截器统一添加 Authorization Header

### 4.6 与 Agent 服务的集成

前端调用 Agent API 时，JWT Token 通过 Nginx 透传：

`
前端 -> Nginx -> Java (校验JWT) -> 提取用户ID -> 内部Header传给 Python Agent
`

Java 侧实现 JWT 鉴权过滤器，对所有 /api/* 请求校验 Token 并注入用户上下文。Python Agent 无需自行鉴权。


## 五、开发计划

| 阶段 | 时间 | 内容 |
|------|------|------|
| 阶段一：用户服务 | 3天 | user-service 脚手架 + 注册/登录 API |
| 阶段二：前端认证 | 2天 | Vue3 登录/注册页面 + Axios + 路由守卫 |
| 阶段三：Agent 增强 | 4天 | 多智能体协作 + LangGraph |
| 阶段四：资源生成 | 4天 | 题库/思维导图/文档/PPT 生成 |
| 阶段五：评估与RAG | 3天 | 评估API + Milvus 知识库 |
| 阶段六：前端优化 | 3天 | 首页 + 引导 + 错误处理 |
| 阶段七：测试部署 | 4天 | 集成测试 + Docker 部署 |
| **总计** | **23天** | |

## 六、目录结构

`
ouragent/
+-- PROJECT.md              # 本文件
+-- docker-compose.yml      # 服务编排
+-- user-service/           # [Java] 用户服务
|   +-- pom.xml
|   +-- src/main/java/com/ouragent/user/
|   |   +-- UserApplication.java
|   |   +-- config/(SecurityConfig|JwtConfig|WebConfig).java
|   |   +-- controller/AuthController.java
|   |   +-- service/(UserService|JwtService).java
|   |   +-- repository/(UserRepository|RefreshTokenRepository).java
|   |   +-- model/(User|RefreshToken).java
|   |   +-- dto/(RegisterRequest|LoginRequest|RefreshRequest|AuthResponse|ApiResponse).java
|   |   +-- middleware/JwtAuthFilter.java
|   +-- src/main/resources/(application.yml|schema.sql)
|   +-- Dockerfile
+-- agent-service/          # [Python] Agent 服务（已有）
|   +-- src/(api.py|core/|utils/)
|   +-- requirements.txt
|   +-- Dockerfile
+-- frontend/               # [Vue3] 前端
|   +-- src/(views/Login.vue|views/Register.vue|api/|store/|router/)
|   +-- nginx.conf
|   +-- Dockerfile
+-- docs/                   # 文档
+-- javaarea/               # Java 参考示例
`

## 七、Docker 部署

| 服务 | 端口映射 | 依赖 |
|------|---------|------|
| frontend | 3000:80 | user-service, agent-service |
| user-service | 9001:9001 | mysql, redis |
| agent-service | 8000:8000 | mysql, redis, milvus |
| mysql | 3306:3306 | - |
| redis | 6379:6379 | - |
| milvus | 19530:19530 | - |

## 八、环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| JWT_SECRET | - | JWT 签名密钥 |
| JWT_ACCESS_EXPIRE | 1800 | Access Token 过期秒数 |
| JWT_REFRESH_EXPIRE | 604800 | Refresh Token 过期秒数 |
| MYSQL_HOST | mysql | 数据库地址 |
| MYSQL_PORT | 3306 | 数据库端口 |
| MYSQL_DB | ouragent | 数据库名 |
| REDIS_HOST | redis | Redis 地址 |
| SPARK_APP_ID | - | 星火 APP ID |
| SPARK_API_KEY | - | 星火 API Key |
| MILVUS_HOST | milvus | 向量库地址 |

## 九、风险与应对

| 风险 | 应对 |
|------|------|
| 星火API 延迟 | 先用 MiMo 跑通流程 |
| 时间不够 | 砍非核心功能保 demo |
| Docker 部署问题 | 备选裸机部署方案 |
| Java-Python 联调 | 先定义 API 契约再开发 |

## 十、团队分工

- **你**：架构设计 + Agent 层 + 后端 API + 难点攻克
- **队友A**：前端界面 + API 对接 + 用户体验
- **队友B（如有）**：RAG 知识库 + 测试部署 + Docker

---

> **最后更新**：2026年6月3日
> **文档版本**：v3.0（Java + Python 微服务架构）
