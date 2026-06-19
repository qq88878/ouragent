# AGENTS.md - OurAgent 项目开发指南

> 基于大模型的个性化资源生成与学习多智能体系统
> 比赛要求：星火大模型 + 多智能体 + 资源可交互 + docker-compose 一键启动

---

## 执行前必读

**每次接到任务时，先确认当前处于哪一步，再开始执行。** 不要跳步，不要同时做多步。

用以下命令快速定位当前进度：
```bash
# 检查 Python Agent 是否还在 Echo 模式（LLM 未配置时会 fallback 到 Echo）
curl -s http://localhost:8000/agent/status | grep llm_provider

# 检查 Java 哪些 Service 还是骨架
grep -rn "throw new UnsupportedOperationException" javaarea/src/

# 检查工具是否还是 NotImplementedError
grep -rn "NotImplementedError" v3/src/core/tools.py

# 检查 Python 是否还有重复的 auth 端点（不应该有）
grep -rn "/auth/" v3/src/api.py

# 检查前端是否存在
ls frontend/ 2>/dev/null || echo "前端未创建"
```

---

## 项目现状（2026-06-09）

| 模块 | 状态 | 说明 |
|------|------|------|
| Docker/部署 | **已完成** | docker-compose.yml、Dockerfile、K8s 配置齐全 |
| 数据库 Schema | **已完成** | 9 张表 DDL 在 `javaarea/src/main/resources/db/schema.sql` |
| Python Agent 核心 | **已完成** | `agent.py` 已接入 LLM（星火/OpenAI），`tools.py` 骨架 |
| Python LLM 集成 | **已完成** | `llm.py` 支持星火和 OpenAI 兼容接口，需配置 API Key |
| Python 服务间认证 | **已完成** | X-Service-Key 密钥验证，供 Java 内部调用 |
| Java auth/security/common/config | **已完成** | 注册登录、JWT、统一响应、异常处理可用 |
| Java 6 个业务模块 | **骨架** | user/course/chat/knowledge/learning/admin 全部 throw |
| 前端 | **未创建** | 无 frontend 目录 |
| LLM 集成 | **未实现** | 无星火/OpenAI 调用代码 |
| RAG/向量检索 | **未实现** | 无 embedding 和向量检索代码 |

---

## 完整步骤划分

### 第一步：让现有框架跑通（验证基础设施）

**目标**：docker-compose up 后所有服务健康，现有 API 可调用。

**做什么**：
- 启动 docker-compose，确认 mysql/postgres/redis/agent-service 全部 healthy
- 验证 Python `/health` 端点返回正常
- 验证 Java auth 端点（register/login）可调用
- 确认数据库表已自动创建

**验证**：
```bash
docker-compose up -d
curl http://localhost:8000/health        # Python Agent
curl http://localhost:9000/api/auth/me   # Java 后端
```

**完成后**：进入第二步

---

### 第二步：Python Agent 接入 LLM（从 Echo 变真 AI）

**目标**：Agent.chat() 调用真实 LLM，不再返回 Echo。

**改什么文件**：
- `v3/src/core/llm.py` — **新建**，LLM 调用抽象层
- `v3/src/core/agent.py` — `_generate_response()` 替换为 LLM 调用
- `v3/config/settings.py` — 新增 LLM 配置项（provider、api_key、model）
- `.env.example` — 新增 LLM 相关环境变量

**具体实现**：
1. 创建 `llm.py`，定义 `LLMProvider` 基类 + `SparkProvider`（星火）+ `OpenAIProvider`（备用）
2. `Agent.__init__` 新增 `llm` 参数
3. `_generate_response()` 构造 messages 列表（system prompt + history + user），调用 LLM
4. 错误处理：API 超时/限流/无效 key → 返回友好错误

**验证**：
```bash
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'
# 期望：返回真实 AI 回复，不是 Echo
```

**完成后**：进入第三步

---

### 第三步：实现 Python 工具系统

**目标**：CalculatorTool 和 SearchTool 可用，Agent 能通过 ReAct 模式调用工具。

**改什么文件**：
- `v3/src/core/tools.py` — 实现 CalculatorTool.execute() 和 SearchTool.execute()
- `v3/src/core/agent.py` — chat() 增加 ReAct 循环（LLM 决定调用工具 → 执行 → 反馈 → 最终回复）

**具体实现**：
1. `CalculatorTool`：用 `ast.literal_eval` 安全计算数学表达式
2. `SearchTool`：调用 DuckDuckGo API（无需 key）
3. `agent.py` chat() 改造：构造 prompt 包含工具 schema → LLM 返回 tool_call → 执行 → 结果回传 → 最终回复
4. `max_tool_rounds = 5` 防止无限循环

**验证**：
```bash
curl -X POST http://localhost:8000/agent/tool \
  -d '{"tool_name": "calculator", "parameters": {"expression": "2**10"}}'
# 期望：{"result": 1024}

curl -X POST http://localhost:8000/agent/chat \
  -d '{"message": "计算 (15+27)*3"}'
# 期望：Agent 自动调用 calculator 工具，返回 126
```

**完成后**：进入第四步

---

### 第四步：Java 端业务模块实现（核心业务逻辑）

**目标**：Java 6 个骨架模块全部可用，前端可以调用完整 API。

**按顺序实现**（有依赖关系）：

#### 4.1 User 模块
- **文件**：`UserServiceImpl.java`
- **实现**：getUserById、updateProfile、listUsers（分页）、updateUserStatus
- **依赖**：无

#### 4.2 Course 模块
- **文件**：`CourseServiceImpl.java`
- **实现**：createCourse、listCourses（分页+筛选）、getCourseDetail、updateCourse、deleteCourse、enrollCourse
- **依赖**：User 模块

#### 4.3 Knowledge 模块
- **文件**：`KnowledgeServiceImpl.java`
- **实现**：uploadFile（保存文件+创建记录）、listKnowledge、getKnowledgeDetail、deleteKnowledge、reprocessKnowledge
- **依赖**：Course 模块

#### 4.4 Chat 模块
- **文件**：`ChatServiceImpl.java` + `AgentServiceClient.java`
- **实现**：
  - AgentServiceClient：实现 chat()、chatWithContext()、isHealthy() — 用 RestTemplate 调 Python
  - ChatService：createSession、sendMessage（存消息→查知识库→调Agent→存回复）、getMessages、deleteSession
- **依赖**：Knowledge 模块、Python Agent（第二步完成）

#### 4.5 Learning 模块
- **文件**：`LearningPathServiceImpl.java` + `StudyRecordServiceImpl.java` + `StudentProfileServiceImpl.java`
- **实现**：
  - StudentProfile：getProfile、updateProfile、getRadarData
  - LearningPath：generatePath（调 Agent）、listPaths、getPathDetail、updateStepStatus、deletePath
  - StudyRecord：createRecord、listRecords、getStats
- **依赖**：Chat 模块

#### 4.6 Admin 模块
- **文件**：`AdminServiceImpl.java`
- **实现**：getDashboard（统计各模块数据）、getSystemHealth（检查各服务状态）
- **依赖**：以上所有模块

**验证**（每实现一个模块就测一个）：
```bash
# User
curl http://localhost:9000/api/users/me -H "Authorization: Bearer <token>"

# Course
curl -X POST http://localhost:9000/api/courses \
  -H "Authorization: Bearer <token>" \
  -d '{"title":"Python入门","category":"编程","difficulty":"BEGINNER"}'

# Chat
curl -X POST http://localhost:9000/api/chat/sessions/1/messages \
  -d '{"content":"Python列表和元组的区别？"}'
```

**完成后**：进入第五步

---

### 第五步：扩展多智能体系统

**目标**：从单 Agent 扩展为多 Agent 协作，满足比赛"至少 3 个 Agent"要求。

**新建文件**（在 `v3/src/core/` 下）：
- `agents/profile_agent.py` — ProfileAgent：学生画像分析
- `agents/planner_agent.py` — PlannerAgent：学习路径规划
- `agents/resource_agent.py` — ResourceAgent：教学资源生成（题目/思维导图/文档）
- `agents/evaluator_agent.py` — EvaluatorAgent：学习效果评估
- `agents/orchestrator.py` — Orchestrator：任务调度，协调多个 Agent

**改什么文件**：
- `v3/src/api.py` — 新增端点：`/agent/analyze`、`/agent/plan`、`/agent/generate`、`/agent/evaluate`
- `javaarea/.../AgentServiceClient.java` — 新增对应调用方法

**验证**：
```bash
# 画像分析
curl -X POST http://localhost:8000/agent/analyze \
  -d '{"user_id":"1", "course_id":1}'

# 资源生成
curl -X POST http://localhost:8000/agent/generate \
  -d '{"type":"question", "topic":"Python基础", "difficulty":"easy"}'
```

**完成后**：进入第六步

---

### 第六步：RAG 知识库集成

**目标**：教师上传文档后自动向量化，学生问答时基于知识库回答。

**新建/改什么文件**：
- `v3/src/core/rag/` — **新建目录**
  - `document_loader.py` — 文档解析（PDF/DOCX/MD/TXT）
  - `chunker.py` — 文本分块
  - `embedder.py` — 向量嵌入（调星火 Embedding API 或本地模型）
  - `vector_store.py` — 向量存储/检索（Milvus 或 FAISS）
  - `rag_chain.py` — RAG 流程：检索 → 构建 prompt → LLM 生成
- `v3/src/api.py` — 新增 `/agent/process`（文档入库）和改造 `/agent/chat`（支持 context 中的 knowledge_ids）
- `javaarea/.../AgentServiceClient.java` — 新增 processDocument() 方法

**验证**：
```bash
# 上传文档
curl -X POST http://localhost:9000/api/knowledge/upload \
  -F "file=@test.pdf" -F "courseId=1"

# 基于知识库问答
curl -X POST http://localhost:8000/agent/chat \
  -d '{"message":"根据课程资料，Python列表的特点是什么？", \
       "context":{"knowledge_ids":[1,2]}}'
```

**完成后**：进入第七步

---

### 第七步：前端开发

**目标**：Vue3 前端可登录、可对话、可查看学习路线。

**新建目录**：`frontend/`

**核心页面**：
| 页面 | 路由 | 功能 |
|------|------|------|
| 登录/注册 | `/login`, `/register` | 邮箱+密码，JWT 存储 |
| 首页仪表盘 | `/` | 学习概览、推荐路径 |
| 智能对话 | `/chat` | 聊天界面，调用 `/api/chat/sessions/*/messages` |
| 学习路径 | `/learning` | 展示 AI 生成的学习路线 |
| 资源管理 | `/resources` | 查看/下载生成的资源 |
| 知识库管理 | `/knowledge` | 教师上传/管理知识文件（教师角色） |
| 管理后台 | `/admin` | 用户管理、系统统计（管理员角色） |

**技术栈**：Vue 3 + Vite + Element Plus + Axios + Vue Router + Pinia

**验证**：
```bash
cd frontend && npm run dev
# 访问 http://localhost:5173，能登录、对话、查看路线
```

**完成后**：进入第八步

---

### 第八步：集成测试与部署完善

**目标**：docker-compose up 一键启动全部服务，端到端流程跑通。

**做什么**：
- 更新 `docker-compose.yml` 加入 frontend 服务
- 更新 `nginx.conf` 路由规则（前端 /、API /api/auth → Java、/api/agent → Python）
- 端到端测试：注册 → 登录 → 选课 → 上传知识库 → AI 对话 → 生成学习路线
- 资源可交互：生成的思维导图/文档/PPT 可预览和下载

**验证**：
```bash
docker-compose up -d
# 访问 http://localhost — 前端页面
# 完成注册→登录→对话→查看路线 完整流程
```

**完成后**：准备比赛演示

---

## 关键文件速查

| 你想改什么 | 看这个文件 |
|-----------|-----------|
| Agent 核心逻辑 | `v3/src/core/agent.py` |
| LLM 调用 | `v3/src/core/llm.py`（第二步新建） |
| 工具实现 | `v3/src/core/tools.py` |
| Python API 端点 | `v3/src/api.py` |
| Python 配置 | `v3/config/settings.py` |
| Java 业务逻辑 | `javaarea/src/main/java/com/edu/agent/module/*/service/impl/` |
| Java 调 Python | `javaarea/.../chat/service/client/AgentServiceClient.java` |
| 数据库表 | `javaarea/src/main/resources/db/schema.sql` |
| Docker 编排 | `docker-compose.yml` |
| Nginx 路由 | `nginx/nginx.conf` |

---

## 代码规范

- **Python**：函数/变量 `snake_case`，类 `PascalCase`，常量 `UPPER_SNAKE_CASE`
- **Java**：遵循 Spring Boot 标准，`camelCase` 方法名，`PascalCase` 类名
- **Git commit**：`type(scope): message`，如 `feat(agent): 接入星火大模型`
- **注释**：只注释"为什么"，不注释"做什么"
- **每次改动**：改完跑一下相关测试或 curl 验证，不要积攒到后面

---

## 环境变量速查

```bash
# LLM（第二步需要）
SPARK_APP_ID=xxx
SPARK_API_KEY=xxx
SPARK_API_SECRET=xxx

# 数据库（已配置）
MYSQL_HOST=mysql
POSTGRES_HOST=postgres
REDIS_HOST=redis

# JWT（已配置）
JWT_SECRET=your-secret-key
```
