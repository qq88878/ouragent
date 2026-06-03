# Agent项目分阶段开发计划

> 本文档与骨架模板中的 `TODO: 阶段X` 注释一一对应，每个阶段完成后对应注释应同步清除。

项目分为两大部分并行推进：**Python Agent服务** (v3/) 和 **Java教育系统** (javaarea/)。

---

## 项目文件总览

### Python Agent服务 (v3/)

| 文件 | 角色 | 状态 |
|------|------|------|
| `v3/src/core/agent.py` | Agent核心类 | 骨架 (Echo占位) |
| `v3/src/core/tools.py` | 工具基类 + 内置工具 | 骨架 (NotImplementedError) |
| `v3/src/core/memory.py` | 记忆管理 | 已完成 (deque实现) |
| `v3/src/api.py` | FastAPI HTTP接口 | 骨架 (全501) |
| `v3/src/main.py` | 程序入口 | 骨架 (api模式可用) |
| `v3/src/utils/config.py` | 配置管理 | 已完成 |
| `v3/src/utils/logger.py` | 日志工具 | 已完成 |
| `v3/tests/test_agent.py` | Agent测试 | 骨架 (基础测试通过) |
| `v3/tests/test_tools.py` | 工具测试 | 骨架 (基础测试通过) |

### Java教育系统 (javaarea/)

| 模块 | 文件数 | 关键文件 | 状态 |
|------|--------|---------|------|
| 项目基础 | 7 | pom.xml, EduAgentApplication, application.yml, schema.sql | 骨架 |
| 通用层 (common) | 6 | Result, ResultCode, BaseEntity, BizException, GlobalExceptionHandler, RoleConstants | 骨架 |
| 配置层 (config) | 7 | SecurityConfig, MyBatisPlusConfig, RedisConfig, CorsConfig, WebMvcConfig, AsyncConfig, AgentServiceConfig | 骨架 |
| 安全层 (security) | 3 | JwtAuthenticationFilter, UserDetailsServiceImpl, LoginUser | 骨架 |
| 认证模块 (auth) | 6 | AuthController, AuthService, LoginRequest, RegisterRequest, TokenResponse | 骨架 |
| 用户模块 (user) | 6 | UserController, UserService, UserMapper, User, UserDTO, UserProfileDTO | 骨架 |
| 课程模块 (course) | 7 | CourseController, CourseService, CourseMapper, Course, CourseDTO, CourseQueryDTO | 骨架 |
| 知识库模块 (knowledge) | 7 | KnowledgeController, KnowledgeService, KnowledgeMapper, KnowledgeBase, KnowledgeUploadDTO, KnowledgeDTO | 骨架 |
| AI对话模块 (chat) | 11 | ChatController, ChatService, AgentServiceClient(新版), ChatSession, ChatMessage, DTO×3 | 骨架 |
| 学习路线模块 (learning) | 18 | LearningPathController, StudyRecordController, StudentProfileController, Entity×4, Mapper×4, Service×3, DTO×4 | 骨架 |
| 管理后台 (admin) | 5 | AdminController, AdminService, DashboardStatsDTO, SystemConfigDTO | 骨架 |
| 文档 | 4 | JAVA_EDU_SYSTEM_DESIGN, DATABASE_SCHEMA, API_REFERENCE, README | 已创建 |

### 基础设施

| 文件 | 角色 | 状态 |
|------|------|------|
| `Dockerfile` | Python Docker镜像 | 已完成 |
| `docker-compose.yml` | 容器编排 | 已完成 |
| `k8s/` | Kubernetes配置 | 已完成 |
| `DEVELOPMENT_PLAN.md` | 本文件 - 总体开发计划 | 已完成 |
| `docs/MICROSERVICE_ARCHITECTURE.md` | 微服务架构文档 | 已完成 |
| `docs/JAVA_INTEGRATION_GUIDE.md` | Java集成指南 | 已完成 |

---

## 阶段一: 框架打通 + API联通 (预计 3-5天)

**目标**: Java能通过HTTP调到Python，Python能返回真实响应，全链路跑通。

### 1.1 实现 FastAPI 基础接口

**文件**: `v3/src/api.py`

| 接口 | 要做的事 |
|------|---------|
| `GET /health` | 返回Agent和依赖服务的连通状态 |
| `GET /agent/status` | 调用 `agent.get_status()` 返回运行信息 |
| `POST /agent/chat` | 调用 `agent.chat(message, context)` 返回回复 |
| `POST /agent/tool` | 调用 `agent.list_tools()` + `registry.execute_tool()` |
| `GET /agent/tools` | 调用 `agent.list_tools()` 返回工具列表 |
| `GET /agent/history` | 调用 `agent.get_conversation_history()` 支持分页 |
| `DELETE /agent/memory` | 调用 `agent.clear_memory()` |

**具体步骤**:

1. 取消 `startup_event` 中的Agent实例化注释，改为全局变量 `agent`
2. 每个endpoint实现基本调用逻辑，去掉 `HTTPException(501)`
3. `/health` 检查Agent是否已初始化
4. `/agent/chat` 调用 `agent.chat()`，异常时返回500
5. `/agent/tool` 先查找工具，不存在返回404，执行异常返回500
6. `/agent/history` 增加 `limit` 查询参数

### 1.2 实现 Java 端调用

**文件**: `javaarea/AgentServiceClient.java`

| 方法 | 要做的事 |
|------|---------|
| `chat(String message)` | POST `/agent/chat`，解析ChatResponse |
| `chat(String message, Map context)` | 同上，带context字段 |
| `getStatus()` | GET `/agent/status`，解析AgentStatus |
| `isHealthy()` | GET `/health`，返回boolean |

**具体步骤**:

1. 用 `restTemplate.postForObject()` 调用Python API
2. 用Jackson反序列化响应到 `ChatResponse` / `AgentStatus`
3. 加try-catch处理 `RestClientException`，包装为业务异常
4. `isHealthy()` 捕获连接异常返回false

**文件**: `javaarea/AgentController.java`

| 接口 | 要做的事 |
|------|---------|
| `POST /api/agent/chat` | 解析请求，调用 `agentClient.chat()`，返回统一格式 |
| `GET /api/agent/health` | 调用 `agentClient.isHealthy()` |
| `GET /api/agent/status` | 调用 `agentClient.getStatus()` |

**文件**: `javaarea/AgentServiceConfig.java`

1. `restTemplate()` Bean配置超时: `connectTimeout=3s`, `readTimeout=10s`
2. `agentServiceClient()` Bean注入配置的URL和RestTemplate

### 1.3 验收标准

```
# 启动Python服务
cd v3 && python -m uvicorn src.api:app --port 8000

# 测试接口
curl http://localhost:8000/health        → {"status": "healthy"}
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "hello"}'             → {"response": "Echo: hello", ...}

# 启动Java服务 → 调用上述接口正常返回
# 运行测试: pytest v3/tests/test_agent.py → 阶段一测试全部通过
```

---

## 阶段二: LLM集成 (预计 3-5天)

**目标**: Agent从"Echo回复"变为真正的AI对话。

### 2.1 Agent接入LLM

**文件**: `v3/src/core/agent.py`

| 方法 | 要做的事 |
|------|---------|
| `__init__` | 新增参数: `llm_provider`, `api_key`, `model`, `temperature` |
| `_generate_response()` | 替换Echo为LLM API调用 |
| `chat()` | 构造prompt: system + history + user消息 |

**具体步骤**:

1. 新建 `v3/src/core/llm.py` — LLM调用抽象层
   - `LLMProvider` 基类: `chat(messages, tools=None) -> str`
   - `OpenAIProvider`: 调用OpenAI ChatCompletion API
   - `ClaudeProvider`: 调用Anthropic Messages API
   - `LocalProvider`: 调用本地模型 (Ollama/vLLM)
2. `Agent.__init__` 保存provider实例
3. `_generate_response()` 实现:
   ```
   messages = [{"role": "system", "content": system_prompt}]
   messages += self.memory.get_context_window(window_size)
   messages += [{"role": "user", "content": message}]
   return self.llm.chat(messages)
   ```
4. 错误处理: API超时/限流/无效key → 返回友好错误消息

### 2.2 配置管理增强

**文件**: `v3/src/utils/config.py`

新增配置项:
- `LLM_PROVIDER`: openai / claude / local
- `LLM_API_KEY`: API密钥
- `LLM_MODEL`: 模型名称 (gpt-4 / claude-3-sonnet / llama3)
- `LLM_TEMPERATURE`: 温度参数
- `LLM_MAX_TOKENS`: 最大输出token数

### 2.3 更新main.py和api.py

**文件**: `v3/src/main.py`

- `create_agent()` 从Config读取LLM参数，传入Agent构造函数

**文件**: `v3/src/api.py`

- `startup_event` 用配置创建带LLM的Agent
- `/health` 增加LLM连通性检查

### 2.4 启用阶段二测试

**文件**: `v3/tests/test_agent.py`

取消 `TestAgentLLM` 中skip标记，实现:
- `test_chat_calls_llm`: mock LLM API，验证chat()正确调用
- `test_chat_error_handling`: mock API返回错误，验证降级处理
- `test_chat_with_system_prompt`: 验证系统提示正确传递

### 2.5 验收标准

```
# 配置.env
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxx
LLM_MODEL=gpt-4

# 启动服务，对话不再是Echo
curl -X POST http://localhost:8000/agent/chat \
  -d '{"message": "你好"}'    → {"response": "你好！有什么可以帮助你的？"}

# 测试通过
pytest v3/tests/test_agent.py → 阶段二测试全部通过
```

---

## 阶段三: 工具调用 (预计 5-7天)

**目标**: Agent能根据对话自动调用工具，实现ReAct推理模式。

### 3.1 实现内置工具

**文件**: `v3/src/core/tools.py`

**CalculatorTool**:
```python
def execute(self, expression: str = "", **kwargs) -> Any:
    # 1. 使用ast.literal_eval或安全的数学表达式解析
    # 2. 支持基本运算: +, -, *, /, **, %
    # 3. 支持科学函数: sin, cos, log, sqrt (math模块)
    # 4. 拒绝危险表达式 (import, exec, eval等)
```

**SearchTool**:
```python
def execute(self, query: str = "", **kwargs) -> Any:
    # 1. 调用搜索API (DuckDuckGo API优先，无需key)
    # 2. 返回top-5结果的title + snippet + url
    # 3. 异常处理: API不可用时返回错误信息
```

### 3.2 Agent实现ReAct循环

**文件**: `v3/src/core/agent.py`

`chat()` 方法改造为ReAct模式:

```
1. 构造prompt，注入可用工具的schema
2. 调用LLM
3. 如果LLM返回 tool_call:
   a. 解析工具名和参数
   b. 执行工具，获取结果
   c. 将工具结果作为tool消息追加到conversation
   d. 再次调用LLM (带工具结果)
   e. 重复直到LLM返回纯文本回复 (最多N轮)
4. 如果LLM直接返回文本 → 作为最终回复
```

关键设计:
- `max_tool_rounds = 5` 防止无限循环
- 工具执行超时控制 (默认30s)
- 工具调用失败时将错误信息返回LLM，让LLM决定如何处理

### 3.3 LLM Function Calling适配

**文件**: `v3/src/core/llm.py` (新建)

- `OpenAIProvider.chat()` 支持 `tools` 参数 → OpenAI function calling格式
- `ClaudeProvider.chat()` 支持 `tools` 参数 → Anthropic tool_use格式
- `LocalProvider.chat()` 支持 `tools` 参数 → 本地模型格式 (或prompt注入)

### 3.4 API层适配

**文件**: `v3/src/api.py`

- `/agent/tool` 接口: 直接调用指定工具 (Java侧主动调用)
- `/agent/tools` 接口: 返回工具schema (含参数定义)

### 3.5 启用阶段三测试

**文件**: `v3/tests/test_tools.py`

取消skip标记，实现:
- `test_basic_operations`: 2+2=4, 10/3≈3.33, sin(0)=0
- `test_complex_expressions`: (2+3)*4=20
- `test_invalid_input`: 除零、非法表达式 → 抛出适当异常
- `test_search_returns_results`: mock搜索API验证返回格式

**文件**: `v3/tests/test_agent.py`

取消skip标记，实现:
- `test_agent_registers_tools`: 验证工具注册到Agent
- `test_agent_calls_calculator`: mock LLM返回tool_call → 验证工具被执行
- `test_agent_tool_error_handling`: 工具抛异常 → Agent返回友好错误

### 3.6 验收标准

```
# 对话触发工具调用
curl -X POST http://localhost:8000/agent/chat \
  -d '{"message": "计算 (15 + 27) * 3"}'
→ {"response": "计算结果是 126"}

# 直接调用工具
curl -X POST http://localhost:8000/agent/tool \
  -d '{"tool_name": "calculator", "parameters": {"expression": "2**10"}}'
→ {"result": 1024, "tool_name": "calculator"}

# 测试通过
pytest v3/tests/ → 阶段三测试全部通过
```

---

## 阶段四: 企业级增强 (预计 5-7天)

**目标**: 生产可用 — 安全、可靠、可观测。

### 4.1 扩展工具集

**文件**: `v3/src/core/tools.py` — 新增工具类

| 工具 | 用途 |
|------|------|
| `WebBrowserTool` | 网页内容获取与解析 |
| `DatabaseTool` | SQL查询执行 (只读) |
| `FileTool` | 文件读写操作 |
| `CodeInterpreterTool` | 安全的Python代码执行 (沙箱) |
| `APICallTool` | 通用HTTP API调用 |

每个工具都继承 `Tool` 基类，实现 `execute()` 和参数schema。

### 4.2 Java端增强

**文件**: `javaarea/AgentServiceClient.java`

- 超时配置: 从 `application.yml` 读取
- 重试机制: 指数退避 (1s, 2s, 4s)
- 熔断器: 接入Resilience4j，连续失败5次熔断30s
- 异步调用: 可选的WebClient替代RestTemplate

**文件**: `javaarea/AgentController.java`

- `@Valid` 请求参数校验
- `@ControllerAdvice` 统一异常处理
- RateLimiter 请求限流 (如100次/分钟)
- 请求链路追踪 (Micrometer/Sleuth)
- SSE流式响应 (支持打字机效果)

**文件**: `javaarea/AgentServiceConfig.java`

- 连接池配置 (最大连接数、空闲超时)
- 熔断器配置 (Resilience4j Bean)
- 重试策略配置 (指数退避参数)

### 4.3 持久化记忆

**文件**: `v3/src/core/memory.py`

- 新增 `PersistentMemory` 类:
  - Redis存储 (短期会话记忆)
  - 向量数据库存储 (长期记忆，支持语义检索)
  - 记忆摘要压缩 (超过阈值自动摘要)

### 4.4 认证与安全

**文件**: `v3/src/api.py`

- API Key认证中间件
- 请求速率限制 (SlowAPI)
- 输入清洗 (防注入)
- HTTPS支持

### 4.5 可观测性

- 结构化日志 (JSON格式)
- Prometheus指标暴露 (`/metrics`端点)
- 请求链路追踪 (OpenTelemetry)

### 4.6 验收标准

```
# Java端有重试和熔断
# 模拟Python服务宕机 → Java端优雅降级
# Python服务恢复 → Java端自动恢复调用

# 记忆持久化
# 对话后重启Python服务 → 历史记忆仍在 (从Redis恢复)

# 安全
# 无API Key → 401 Unauthorized
# 超过限流 → 429 Too Many Requests
```

---

## 阶段五: 打磨与优化 (预计 3-5天)

**目标**: 体验优化、性能调优、文档完善。

### 5.1 交互体验

**文件**: `v3/src/main.py`

- `interactive_mode` 增强:
  - 多行输入支持
  - 内置命令: `/clear`, `/history`, `/tools`, `/save`
  - 输入历史 (上下键翻阅)
  - 输出Markdown渲染 (rich库)
  - 流式输出 (打字机效果)

### 5.2 流式响应

**文件**: `v3/src/api.py`

- 新增 `POST /agent/chat/stream` — SSE流式接口
- `agent.py` 新增 `chat_stream()` 方法
- Java端SSE消费实现

### 5.3 多Agent支持

**文件**: `v3/src/core/agent.py`

- Agent可动态创建子Agent
- Agent间消息传递协议
- 任务分发与结果汇总

### 5.4 性能优化

- LLM响应缓存 (相同输入短时间不重复调用)
- 工具执行结果缓存
- 连接池优化 (httpx async)
- 异步工具并发执行

### 5.5 文档与示例

- API文档完善 (FastAPI自动生成的Swagger)
- Java端SDK使用文档
- Docker部署指南
- `v3/examples/` 下的示例更新为真实可运行版本

### 5.6 验收标准

```
# 交互模式体验流畅
# 流式回复实时输出
# API文档 localhost:8000/docs 可直接测试所有接口
# Docker一键部署: docker-compose up → 全部服务可用
```

---

## 实施顺序建议

```
阶段一 ──→ 阶段二 ──→ 阶段三 ──→ 阶段四 ──→ 阶段五
(打通)     (智能)     (工具)     (生产)     (打磨)
3-5天      3-5天      5-7天      5-7天      3-5天
```

**阶段一和二是独立的**: 阶段二不依赖阶段一的Java端实现，可以并行开发。
**阶段三依赖阶段二**: 工具调用需要LLM的function calling能力。
**阶段四和五相对独立**: 可以根据优先级灵活安排。

## 每阶段开工清单

每个阶段开始前:

1. 搜索代码中 `TODO: 阶段N` 标记，确认本阶段要改哪些文件
2. 确认上一阶段的测试全部通过
3. 创建分支: `git checkout -b feat/phase-N`
4. 按上述文件清单逐个实现
5. 实现完一个文件就运行相关测试
6. 全部完成后提PR，合并到main

## 搜索TODO标记速查

```bash
# 查看某个阶段的所有待办 (Python端)
grep -rn "TODO: 阶段一" v3/
grep -rn "TODO: 阶段二" v3/

# 查看某个阶段的所有待办 (Java端)
grep -rn "TODO: 阶段一" javaarea/src/
grep -rn "TODO: 阶段二" javaarea/src/

# 查看所有待办总数
grep -rn "TODO:" v3/ javaarea/src/ | wc -l
```

---

## Java教育系统分阶段开发计划

> 以下为 `javaarea/` 教育系统的实施计划，与 Python Agent 服务并行推进。

### Java阶段一: 项目骨架 + 认证 (预计 5-7天)

**目标**: Spring Boot项目可编译运行，用户注册登录和角色权限打通。

**涉及文件** (~30个):
- `pom.xml` — Maven依赖
- `EduAgentApplication.java` — 启动类
- `common/` 全部6个文件 — Result, BaseEntity, 异常处理等
- `config/` 全部7个文件 — Security, MyBatisPlus, Redis等配置
- `security/` 全部3个文件 — JWT过滤器, UserDetailsService, LoginUser
- `module/auth/` 全部6个文件 — 注册登录登出
- `module/user/` 全部6个文件 — 用户CRUD
- `application.yml`, `application-dev.yml` — 配置文件
- `db/schema.sql` — 9张表DDL

**具体步骤**:

1. 配置 `pom.xml` 依赖，确保 `mvn clean compile` 通过
2. 实现 `BaseEntity` + `Result` + `ResultCode` — 通用基础
3. 实现 `SecurityConfig` + `JwtAuthenticationFilter` — JWT认证链
4. 实现 `AuthController` + `AuthServiceImpl` — 注册(BCrypt加密)、登录(生成JWT)、登出(Redis黑名单)
5. 实现 `UserController` + `UserServiceImpl` — 用户信息CRUD
6. 实现 `MyBatisPlusConfig` — 分页和自动填充
7. 创建MySQL数据库，执行 `schema.sql`
8. 运行 `mvn spring-boot:run`，测试注册登录流程

**验收标准**:
```bash
# 注册
curl -X POST http://localhost:9000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"student1","password":"123456","role":"STUDENT"}'
→ {"code":200, "message":"success"}

# 登录
curl -X POST http://localhost:9000/api/auth/login \
  -d '{"username":"student1","password":"123456"}'
→ {"code":200, "data":{"accessToken":"eyJ...", "expiresIn":86400}}

# 访问受保护接口
curl http://localhost:9000/api/users/me \
  -H "Authorization: Bearer eyJ..."
→ {"code":200, "data":{"username":"student1", "role":"STUDENT", ...}}
```

---

### Java阶段二: 课程 + 知识库管理 (预计 4-5天)

**目标**: 教师可创建课程和上传知识库材料，学生可浏览和选课。

**涉及文件** (~14个):
- `module/course/` 全部7个文件
- `module/knowledge/` 全部7个文件

**具体步骤**:

1. 实现 `CourseServiceImpl` — 课程CRUD，教师只能操作自己的课程
2. 实现 `KnowledgeServiceImpl` — 文件上传保存、知识库元数据管理
3. 集成文件上传 — 解析PDF/DOCX提取文本内容
4. `AgentServiceClient.ingestKnowledge()` — 异步调用Python Agent进行向量化
5. 知识库处理状态跟踪 — PENDING→PROCESSING→COMPLETED/FAILED

**验收标准**:
```bash
# 教师创建课程
curl -X POST http://localhost:9000/api/courses \
  -H "Authorization: Bearer <teacher_token>" \
  -d '{"title":"Python基础","category":"编程","difficulty":"BEGINNER"}'

# 教师上传知识库材料
curl -X POST http://localhost:9000/api/knowledge/upload \
  -H "Authorization: Bearer <teacher_token>" \
  -F "file=@textbook.pdf" -F "courseId=1" -F "title=Python教材"

# 学生浏览课程
curl http://localhost:9000/api/courses?category=编程
```

---

### Java阶段三: AI对话集成 (预计 4-5天)

**目标**: 学生可通过知识库驱动的AI对话获取帮助。

**涉及文件** (~11个):
- `module/chat/` 全部文件 — ChatController, ChatService, ChatSession, ChatMessage, DTOs, Mappers

**具体步骤**:

1. 实现 `ChatServiceImpl.createSession()` — 创建对话会话
2. 实现 `ChatServiceImpl.sendMessage()` — 核心流程:
   - 存储用户消息
   - 加载课程知识库ID列表
   - 调用 `AgentServiceClient.chatWithContext()`
   - 存储Agent回复
   - 异步记录学习时间
3. 实现 `AgentServiceClient.chatWithContext()` — 带RAG上下文的AI对话
4. 会话历史管理 — 分页查询、会话列表

**验收标准**:
```bash
# 创建会话
curl -X POST http://localhost:9000/api/chat/sessions \
  -H "Authorization: Bearer <student_token>" \
  -d '{"courseId":1, "sessionType":"LEARNING"}'

# 发送消息 (带知识库上下文)
curl -X POST http://localhost:9000/api/chat/sessions/1/messages \
  -d '{"message":"Python的列表和元组有什么区别？"}'
→ {"response":"根据课程资料，列表和元组的主要区别是...", "sessionId":1}
```

---

### Java阶段四: 学习路线 + 画像 + 数据分析 (预计 5-7天)

**目标**: AI生成个性化学习路线，学生画像跟踪学习进度，管理后台统计。

**涉及文件** (~26个):
- `module/learning/` 全部文件 — LearningPath, StudyRecord, StudentProfile相关
- `module/admin/` 全部文件 — 仪表盘、系统健康

**具体步骤**:

1. 实现 `LearningPathServiceImpl.generatePath()` — 调用Agent生成路线
2. 实现学习路线CRUD — 步骤状态更新、进度计算
3. 实现 `StudyRecordServiceImpl` — 记录学习时长和成绩
4. 实现 `StudentProfileServiceImpl` — 学生画像管理、雷达图数据
5. 实现 `AdminServiceImpl` — 仪表盘统计、系统健康检查

**验收标准**:
```bash
# 生成学习路线
curl -X POST http://localhost:9000/api/learning/paths/generate \
  -d '{"courseId":1, "goal":"掌握Python基础", "currentLevel":"BEGINNER"}'
→ {"title":"Python基础学习路线", "totalSteps":5, "steps":[...]}

# 查看仪表盘 (管理员)
curl http://localhost:9000/api/admin/dashboard \
  -H "Authorization: Bearer <admin_token>"
→ {"totalUsers":100, "totalCourses":20, "activeStudentsToday":15}
```

---

### Java阶段五: 生产化 (预计 3-5天)

**目标**: 生产可用 — 熔断、限流、监控、SSE流式。

**增强内容**:
- `AgentServiceClient` — Resilience4j熔断器、重试机制、连接池
- `ChatController` — SSE流式响应端点
- 全局 — `@Valid`参数校验、Micrometer指标、请求日志拦截器
- Redis — 缓存课程列表、用户画像、热门问答
- 限流 — AI对话端点速率限制

---

### Java + Python 联调节点

| 节点 | Java端 | Python端 | 说明 |
|------|--------|---------|------|
| 阶段一末 | `AgentServiceClient.chat()` | `POST /agent/chat` | 基础HTTP联通 |
| 阶段二末 | `AgentServiceClient.ingestKnowledge()` | `POST /agent/knowledge/ingest` | 知识库入库 |
| 阶段三末 | `AgentServiceClient.chatWithContext()` | `POST /agent/chat` (带context) | RAG问答 |
| 阶段四末 | `AgentServiceClient.generateLearningPath()` | `POST /agent/learning-path/generate` | 路线生成 |
