# AI教育系统 -- 系统设计文档

## 1. 系统概述

本系统是一个AI驱动的智能教育平台，核心目标是连接教师与学生，通过大语言模型技术提升教学质量与学习效率。

**核心业务流程：**

- **教师端**：教师创建课程，上传教学资料（PDF、Word、Markdown等）作为知识库，系统自动进行文档解析、向量化入库，为AI问答提供精准的领域知识支撑。
- **学生端**：学生选课后，可基于课程知识库进行AI智能问答（RAG模式），系统结合学习记录和学生画像，利用AI生成个性化学习路线，实现因材施教。
- **管理端**：平台管理员对用户、课程、系统健康进行全面管控。

**技术亮点：**

- RAG（检索增强生成）确保AI回答基于教师上传的真实教学资料，降低幻觉风险
- 学生画像与学习记录驱动的个性化学习路线规划
- 向量检索实现语义级知识匹配

---

## 2. 技术栈

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 后端框架 | Spring Boot | 3.2.x | Web应用主框架 |
| ORM | MyBatis-Plus | 3.5.5 | 数据库访问与通用CRUD |
| 数据库 | MySQL | 8.x | 业务数据持久化 |
| 缓存 | Redis | 7.x | Token黑名单、会话缓存、限流 |
| 安全框架 | Spring Security | 6.x | 认证授权 |
| JWT | JJWT | 0.12.3 | 无状态Token认证 |
| 工具 | Lombok | - | 简化实体类代码 |
| 语言 | Java | 17 | 后端开发语言 |
| 构建工具 | Maven | 3.9+ | 依赖管理与构建 |
| AI服务 | Python Agent | - | 向量化、RAG问答、学习路线生成 |
| 容器化 | Docker | - | 部署与编排 |

---

## 3. 系统架构图

```
                        +-------------------+
                        |     前端应用       |
                        | Vue / React / App |
                        +--------+----------+
                                 |
                          HTTP (REST API)
                                 |
                                 v
+-----------------------------------------------------------------------+
|                        Java 后端 (端口 9000)                            |
|                                                                       |
|  +------------+  +-----------+  +-----------+  +-------------------+  |
|  | Auth模块   |  | User模块  |  | Course模块|  | Knowledge模块     |  |
|  +------------+  +-----------+  +-----------+  +-------------------+  |
|                                                                       |
|  +------------+  +-----------+  +-----------+  +-------------------+  |
|  | Chat模块   |  | Learning  |  | Study     |  | Admin模块         |  |
|  |            |  | Path模块  |  | Record模块|  |                   |  |
|  +------------+  +-----------+  +-----------+  +-------------------+  |
|                                                                       |
|  +---------------------------------------------------------------+   |
|  |           Security (JWT) + Global Exception Handler           |   |
|  +---------------------------------------------------------------+   |
|                                                                       |
+-------+--------------------------+------------------------------------+
        |                          |
        v                          v
+---------------+          +---------------+
|   MySQL 8.x   |          |  Redis 7.x    |
|  业务数据      |          | Token黑名单   |
|  9张核心表     |          | 会话缓存      |
+---------------+          | 限流计数      |
                           +---------------+
        |
        | HTTP REST (内部调用)
        v
+-----------------------------------------------------------------------+
|                   Python Agent 服务 (端口 8000)                        |
|                                                                       |
|  +----------------+  +----------------+  +-----------------------+   |
|  | 文档解析服务    |  | RAG问答引擎    |  | 学习路线生成引擎      |   |
|  | PDF/DOCX/MD    |  | 向量检索+LLM  |  | 画像分析+路线规划     |   |
|  +----------------+  +----------------+  +-----------------------+   |
|                                                                       |
|  +----------------+  +----------------+                               |
|  | 向量数据库      |  | LLM服务       |                               |
|  | (Embedding)    |  | (ChatGPT等)  |                               |
|  +----------------+  +----------------+                               |
|                                                                       |
+-----------------------------------------------------------------------+
```

---

## 4. 模块划分

系统共划分为 **7个业务模块**，按包路径 `com.edu.agent.module.*` 组织：

| 模块 | 包路径 | 核心职责 | 涉及角色 |
|------|--------|----------|----------|
| **认证模块 (auth)** | `module.auth` | 用户注册、登录、登出、Token管理 | 全部 |
| **用户模块 (user)** | `module.user` | 用户信息管理、状态管理、分页查询 | 全部/ADMIN |
| **课程模块 (course)** | `module.course` | 课程CRUD、选课、课程发布 | TEACHER/STUDENT |
| **知识库模块 (knowledge)** | `module.knowledge` | 知识文件上传、入库、向量化触发、重处理 | TEACHER |
| **对话模块 (chat)** | `module.chat` | AI对话会话管理、消息发送（RAG）、历史查询 | STUDENT |
| **学习路线模块 (learning)** | `module.learning` | AI生成学习路线、路线步骤管理、进度跟踪 | STUDENT |
| **管理模块 (admin)** | `module.admin` | 仪表盘统计、系统健康监控 | ADMIN |

**公共模块 (common)**：提供 `BaseEntity`、`Result`统一响应、`BizException`全局异常、`RoleConstants`角色常量等基础设施。

**安全模块 (security)**：`JwtAuthenticationFilter`、`LoginUser`、`UserDetailsServiceImpl`，基于Spring Security + JWT实现无状态认证。

---

## 5. 三角色权限设计

### 角色定义

| 角色 | 常量值 | 定位 |
|------|--------|------|
| **ADMIN** | `RoleConstants.ROLE_ADMIN` | 平台管理员，拥有全局管理权限 |
| **TEACHER** | `RoleConstants.ROLE_TEACHER` | 教师，管理自己的课程和知识库 |
| **STUDENT** | `RoleConstants.ROLE_STUDENT` | 学生，学习、对话、查看学习路线 |

### 权限矩阵

| 功能 | ADMIN | TEACHER | STUDENT |
|------|:-----:|:-------:|:-------:|
| 用户注册/登录/登出 | v | v | v |
| 查看/编辑个人信息 | v | v | v |
| 查看用户列表 | v | - | - |
| 启用/禁用用户 | v | - | - |
| 创建/编辑课程 | v | v (仅自己的) | - |
| 删除课程 | v | v (仅自己的) | - |
| 发布课程 | v | v | - |
| 选课 | - | - | v |
| 上传知识文件 | v | v (仅自己课程) | - |
| 删除/重处理知识库 | v | v (仅自己课程) | - |
| 创建AI对话会话 | - | - | v |
| 发送AI消息 | - | - | v |
| 生成学习路线 | - | - | v (AI生成) |
| 查看学习路线 | - | - | v (仅自己的) |
| 记录学习数据 | - | - | v |
| 查看管理仪表盘 | v | - | - |
| 系统健康监控 | v | - | - |

### 权限控制实现

通过Spring Security的 `@PreAuthorize` 注解 + JWT中携带的角色信息实现：

```java
@PreAuthorize("hasRole('TEACHER')")
public Result<Long> create(@RequestBody CourseDTO courseDTO) { ... }

@PreAuthorize("hasRole('ADMIN')")
public Result<IPage<UserDTO>> listUsers(...) { ... }
```

---

## 6. Agent集成设计

Java后端通过 `AgentServiceClient`（基于 `RestTemplate`）与Python Agent服务通信，配置从 `application.yml` 中读取：

```yaml
agent:
  service:
    url: http://agent-service:8000
    timeout: 5000
    retry:
      max-attempts: 3
      delay: 1000
```

### 核心流程一：知识库入库（教师上传 -> 向量化）

```
教师                    Java后端                   Python Agent服务
 |                        |                           |
 |-- 上传教学文件 ------->|                           |
 |   (PDF/DOCX/MD)       |                           |
 |                        |-- 保存文件到磁盘 -------->|
 |                        |-- 创建knowledge_base记录  |
 |                        |   (status=PENDING)        |
 |                        |-- POST /agent/process ---->|
 |                        |   {file_path, file_type}  |
 |                        |                           |-- 解析文档内容
 |                        |                           |-- 文本分块 (Chunking)
 |                        |                           |-- 向量嵌入 (Embedding)
 |                        |                           |-- 存入向量数据库
 |                        |<-- 返回 {doc_id, status} -|
 |                        |                           |
 |                        |-- 更新记录:                |
 |                        |   vector_doc_id = doc_id   |
 |                        |   status = INDEXED          |
 |<-- 返回上传成功 --------|                           |
```

### 核心流程二：AI问答（RAG + LLM）

```
学生                    Java后端                   Python Agent服务
 |                        |                           |
 |-- 发送问题 ----------->|                           |
 |   {session_id, msg}    |                           |
 |                        |-- 保存用户消息到          |
 |                        |   chat_message表          |
 |                        |                           |
 |                        |-- 查询课程关联的           |
 |                        |   knowledge_base           |
 |                        |                           |
 |                        |-- POST /agent/chat ------->|
 |                        |   {message, context:       |
 |                        |    {course_id,             |
 |                        |     knowledge_ids,         |
 |                        |     chat_history}}         |
 |                        |                           |
 |                        |                           |-- 向量检索相关知识片段
 |                        |                           |-- 构建Prompt (知识+历史+问题)
 |                        |                           |-- 调用LLM生成回答
 |                        |                           |-- 后处理 (引用标注等)
 |                        |                           |
 |                        |<-- 返回 {response} --------|
 |                        |                           |
 |                        |-- 保存AI回复到             |
 |                        |   chat_message表           |
 |                        |-- 更新study_record         |
 |<-- 返回AI回答 ----------|                           |
```

### 核心流程三：学习路线生成（AI规划）

```
学生                    Java后端                   Python Agent服务
 |                        |                           |
 |-- 请求生成学习路线 ---->|                           |
 |   {course_id}          |                           |
 |                        |-- 收集学生数据:            |
 |                        |   student_profile          |
 |                        |   study_record (历史)      |
 |                        |   knowledge_base (课程)    |
 |                        |                           |
 |                        |-- POST /agent/learning ---->|
 |                        |    /generate               |
 |                        |   {student_profile,        |
 |                        |    study_records,          |
 |                        |    course_info,            |
 |                        |    knowledge_list}         |
 |                        |                           |
 |                        |                           |-- 分析学生画像
 |                        |                           |-- 评估学习水平
 |                        |                           |-- 规划学习步骤
 |                        |                           |-- 生成路线JSON
 |                        |                           |
 |                        |<-- 返回 {steps: [...]} ----|
 |                        |                           |
 |                        |-- 创建learning_path记录    |
 |                        |-- 批量创建step记录         |
 |<-- 返回学习路线 --------|                           |
```

---

## 7. 数据流说明

### 7.1 知识库入库完整调用链

```
KnowledgeController.upload()
  -> KnowledgeService.upload(file, dto)
    -> 1. 保存文件到磁盘 (本地/OSS)
    -> 2. 创建 KnowledgeBase 记录 (status=PENDING)
    -> 3. 调用 AgentServiceClient.processDocument(file_path, file_type)
       -> POST http://agent-service:8000/agent/process
          Body: {"file_path": "...", "file_type": "pdf"}
       -> Python服务解析、分块、向量化、入库
       -> Response: {"doc_id": "vec_xxx", "status": "success"}
    -> 4. 更新 KnowledgeBase 记录
       -> vector_doc_id = "vec_xxx"
       -> status = INDEXED
    -> 5. 返回 KnowledgeDTO
```

### 7.2 AI问答完整调用链

```
ChatController.sendMessage(sessionId, request)
  -> ChatService.sendMessage(sessionId, request)
    -> 1. 保存用户消息到 chat_message 表
    -> 2. 查询 chat_session 获取 course_id
    -> 3. 查询 course 关联的所有 knowledge_base (status=INDEXED)
    -> 4. 查询最近N条 chat_message 作为历史上下文
    -> 5. 调用 AgentServiceClient.chat(message, context)
       -> POST http://agent-service:8000/agent/chat
          Body: {"message": "...", "context": {
            "course_id": 1,
            "knowledge_ids": [1, 2, 3],
            "chat_history": [...]
          }}
       -> Python服务执行RAG流程: 向量检索 -> Prompt构建 -> LLM生成
       -> Response: {"response": "...", "sources": [...]}
    -> 6. 保存AI回复到 chat_message 表 (含 token_count)
    -> 7. 更新或创建 study_record (累计交互次数、时长)
    -> 8. 返回 AI回复内容
```

### 7.3 学习路线生成完整调用链

```
LearningPathController.generate(request)
  -> LearningPathService.generate(courseId)
    -> 1. 获取当前学生 student_profile
    -> 2. 获取该课程历史 study_record 列表
    -> 3. 获取课程信息 (course)
    -> 4. 获取课程下所有 knowledge_base 列表
    -> 5. 调用 AgentServiceClient.generateLearningPath(data)
       -> POST http://agent-service:8000/agent/learning/generate
          Body: {"student_profile": {...}, "study_records": [...],
                 "course_info": {...}, "knowledge_list": [...]}
       -> Python服务分析画像、评估水平、规划步骤
       -> Response: {"title": "...", "steps": [
           {"order": 1, "title": "...", "description": "...", "kb_id": 1},
           ...
       ]}
    -> 6. 创建 learning_path 记录
    -> 7. 批量创建 learning_path_step 记录
    -> 8. 返回完整学习路线 (含步骤)
```

---

## 8. 分阶段实施计划

### 阶段一：基础框架搭建

**目标：** 项目能编译运行，认证体系打通，基础CRUD可用

- 项目骨架搭建：Maven配置、目录结构、配置文件
- 公共模块：BaseEntity、Result、GlobalExceptionHandler、BizException
- 安全模块：JWT工具类、JwtAuthenticationFilter、SecurityConfig、UserDetailsServiceImpl
- 认证模块：注册、登录、登出、获取当前用户
- 用户模块：个人信息CRUD、管理员用户管理
- 基础测试：AuthController + UserController 单元测试

### 阶段二：课程与知识库

**目标：** 教师能创建课程并上传知识文件

- 课程模块：课程CRUD、选课、分页查询、权限校验
- 知识库模块：文件上传、知识记录CRUD、与Python Agent对接（文档处理）
- 文件存储服务：本地文件/OSS上传抽象
- AgentServiceClient实现：processDocument()、chat()、isHealthy()

### 阶段三：AI对话与RAG

**目标：** 学生能基于课程知识库进行AI问答

- 对话模块：会话CRUD、消息发送（调用Agent的chat接口）、历史消息查询
- AgentServiceClient增强：chat()完整实现（带上下文传递）
- study_record自动记录：每次对话自动更新学习记录
- 流式响应支持（SSE）：打字机效果，提升用户体验

### 阶段四：学习路线与画像

**目标：** AI根据学生画像生成个性化学习路线

- 学生画像模块：画像CRUD、雷达图数据接口
- 学习路线模块：AI生成路线、路线步骤管理、进度更新
- 学习记录模块：统计数据、学习时长追踪
- AgentServiceClient增强：generateLearningPath()

### 阶段五：管理与优化

**目标：** 管理后台完善，系统可观测、可运维

- 管理后台模块：仪表盘数据统计、系统健康监控
- 性能优化：Redis缓存策略、数据库索引优化、慢查询治理
- 可靠性增强：Agent调用重试机制、熔断器（Resilience4j）、降级策略
- 监控告警：接入Micrometer/Prometheus指标、日志链路追踪
- 部署优化：Docker Compose编排、多环境配置、健康检查
