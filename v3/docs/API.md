# Agent Service API 对接文档

> Python Agent 微服务接口规范，供 Java 后端 `AgentServiceClient` 调用
>
> Base URL: `http://agent-service:8000`（Docker 内部） / `http://localhost:8000`（本地开发）

---

## 通用说明

### 鉴权

除 `/health` 和 `/agent/status` 外，所有接口需要在请求头中携带服务间密钥：

```
X-Service-Key: <密钥>
```

密钥通过环境变量 `AGENT_SERVICE_KEY` 配置，默认值 `default-dev-key`。

### 响应格式

成功响应直接返回 JSON 对象。错误响应格式：

```json
{
  "detail": "错误描述"
}
```

HTTP 状态码：
- `200` 成功
- `403` 密钥无效
- `404` 资源不存在（如工具名错误）
- `422` 请求参数校验失败
- `500` 服务内部错误
- `503` Agent 未初始化

---

## 1. 基础接口

### 1.1 健康检查

```
GET /health
```

无需鉴权。

**响应：**
```json
{
  "status": "healthy",
  "agent_available": true,
  "rag_available": true
}
```

**Java 对应：** `AgentServiceClient.isHealthy()`

---

### 1.2 Agent 状态

```
GET /agent/status
```

无需鉴权。

**响应：**
```json
{
  "agents": ["profile_agent", "planner_agent", "resource_agent", "evaluator_agent"],
  "tools": ["knowledge_retrieval", "web_search", "question_generator", "mindmap_generator", "study_plan"],
  "rag": {
    "total_chunks": 42,
    "embedding_provider": "LocalEmbeddingProvider",
    "chunk_size": 500
  },
  "llm": "OpenAIProvider"
}
```

**Java 对应：** `AgentServiceClient.getStatus()`

---

## 2. 对话接口

### 2.1 基础对话

```
POST /agent/chat
Content-Type: application/json
X-Service-Key: <key>
```

**请求体：**
```json
{
  "message": "什么是Python列表？",
  "context": {
    "knowledge_ids": [1, 2]
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `message` | string | 是 | 用户消息 |
| `context` | object | 否 | 上下文信息 |
| `context.knowledge_ids` | int[] | 否 | 限定 RAG 检索范围的知识库 ID 列表 |
| `context.student_profile` | object | 否 | 学生画像，用于个性化回答 |
| `context.history` | array | 否 | 对话历史（如果提供 session_id，优先使用 Redis 中的历史） |
| `session_id` | string | 否 | 会话 ID，用于记忆对话历史 |

**响应：**
```json
{
  "response": "Python列表是...",
  "session_id": "xxx",
  "status": "success"
}
```

**Java 对应：** `AgentServiceClient.chat(message)`

---

### 2.2 带上下文对话

```
POST /agent/chat/context
Content-Type: application/json
X-Service-Key: <key>
```

**请求体：**
```json
{
  "message": "Python列表和元组的区别？",
  "context": {
    "knowledge_ids": [1, 2, 3],
    "student_profile": {
      "learning_style": "visual",
      "weaknesses": ["数据结构"],
      "grade_level": "beginner"
    },
    "history": [
      {"role": "user", "content": "什么是Python列表？"},
      {"role": "assistant", "content": "Python列表是..."}
    ]
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `message` | string | 是 | 用户消息 |
| `context` | object | 是 | 完整上下文 |
| `context.knowledge_ids` | int[] | 否 | 知识库 ID 列表 |
| `context.student_profile` | object | 否 | 学生画像 |
| `context.student_profile.learning_style` | string | 否 | `visual` / `auditory` / `reading` / `kinesthetic` |
| `context.student_profile.weaknesses` | string[] | 否 | 薄弱点列表 |
| `context.student_profile.strengths` | string[] | 否 | 强项列表 |
| `context.student_profile.grade_level` | string | 否 | `beginner` / `intermediate` / `advanced` |
| `context.history` | array | 否 | 对话历史 |

**响应：**
```json
{
  "response": "Python列表和元组的主要区别...",
  "status": "success"
}
```

**Java 对应：** `AgentServiceClient.chatWithContext(message, context)`

---

## 3. 知识库接口

### 3.1 文件上传入库

```
POST /agent/knowledge/ingest
Content-Type: multipart/form-data
X-Service-Key: <key>
```

**表单字段：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | file | 是 | 上传的文件（PDF/DOCX/MD/TXT） |
| `knowledge_id` | int | 是 | 知识库记录 ID（对应 `knowledge_base` 表） |
| `course_id` | int | 是 | 所属课程 ID |

**响应：**
```json
{
  "knowledge_id": 1,
  "chunks": 12,
  "status": "indexed"
}
```

`status` 取值：`indexed`（成功）/ `failed`（失败，chunks=0）

**Java 对应：** `AgentServiceClient.ingestKnowledge(knowledgeId, courseId, content, fileType)`

---

### 3.2 文本内容入库

```
POST /agent/knowledge/ingest-text
Content-Type: application/json
X-Service-Key: <key>
```

**请求体：**
```json
{
  "knowledge_id": 1,
  "course_id": 1,
  "content": "文档的纯文本内容...",
  "file_type": "txt"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `knowledge_id` | int | 是 | 知识库记录 ID |
| `course_id` | int | 是 | 所属课程 ID |
| `content` | string | 是 | 纯文本内容 |
| `file_type` | string | 否 | 文件类型，默认 `txt` |

**响应：** 同 3.1

---

### 3.3 知识库状态

```
GET /agent/knowledge/status
X-Service-Key: <key>
```

**响应：**
```json
{
  "total_chunks": 42,
  "embedding_provider": "LocalEmbeddingProvider",
  "chunk_size": 500
}
```

**Java 对应：** `AgentServiceClient.getKnowledgeStatus(knowledgeId)`

---

## 4. 多 Agent 接口

### 4.1 学生画像分析

```
POST /agent/analyze
Content-Type: application/json
X-Service-Key: <key>
```

**请求体：**
```json
{
  "user_id": "123",
  "course_id": 1,
  "chat_history": [
    {"role": "user", "content": "我不太理解递归"},
    {"role": "assistant", "content": "递归是指..."}
  ],
  "study_records": [
    {"topic": "递归", "score": 45, "duration": 30},
    {"topic": "循环", "score": 85, "duration": 20}
  ],
  "current_profile": {
    "learning_style": "visual",
    "weaknesses": ["递归"]
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | string | 是 | 用户 ID |
| `course_id` | int | 否 | 课程 ID |
| `chat_history` | array | 否 | 聊天记录 |
| `study_records` | array | 否 | 学习记录 |
| `current_profile` | object | 否 | 现有画像（增量更新） |

**响应：**
```json
{
  "learning_style": "visual",
  "strengths": ["循环", "条件语句"],
  "weaknesses": ["递归", "数据结构"],
  "interests": ["Web开发"],
  "grade_level": "beginner",
  "recommended_strategy": "多用流程图和示意图解释递归过程",
  "confidence": 0.85
}
```

---

### 4.2 生成学习路径

```
POST /agent/plan
Content-Type: application/json
X-Service-Key: <key>
```

**请求体：**
```json
{
  "student_profile": {
    "learning_style": "visual",
    "weaknesses": ["递归"],
    "grade_level": "beginner"
  },
  "course_title": "Python基础",
  "course_knowledge": [
    {"id": 1, "title": "变量与数据类型"},
    {"id": 2, "title": "控制流"},
    {"id": 3, "title": "函数"}
  ],
  "goal": "掌握Python基础语法"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `student_profile` | object | 是 | 学生画像 |
| `course_title` | string | 是 | 课程名称 |
| `course_knowledge` | array | 否 | 课程知识条目列表 |
| `goal` | string | 否 | 学习目标，默认 "掌握课程核心知识" |

**响应：**
```json
{
  "title": "Python基础个性化学习路径",
  "description": "根据你的学习风格定制...",
  "total_steps": 5,
  "estimated_total_hours": 15,
  "steps": [
    {
      "order": 1,
      "title": "变量与数据类型",
      "description": "从基础概念开始...",
      "knowledge_ids": [1],
      "estimated_hours": 3,
      "checkpoint": "能独立声明变量并进行类型转换"
    }
  ]
}
```

**Java 对应：** `AgentServiceClient.generateLearningPath(studentProfile, courseId, goal)`

---

### 4.3 生成教学资源

```
POST /agent/generate
Content-Type: application/json
X-Service-Key: <key>
```

**请求体：**
```json
{
  "type": "question",
  "topic": "Python列表",
  "knowledge_ids": [1, 2],
  "difficulty": "medium",
  "count": 5
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 是 | 资源类型：`question` / `mindmap` / `summary` |
| `topic` | string | 是 | 主题 |
| `knowledge_ids` | int[] | 否 | 限定知识库范围 |
| `difficulty` | string | 否 | 难度：`easy` / `medium` / `hard`，默认 `medium` |
| `count` | int | 否 | 题目数量，默认 5（仅 `type=question` 时有效） |

**响应（type=question）：**
```json
{
  "topic": "Python列表",
  "questions": [
    {
      "type": "choice",
      "difficulty": "medium",
      "question": "以下哪个是Python列表的正确创建方式？",
      "options": ["A. [1,2,3]", "B. (1,2,3)", "C. {1,2,3}", "D. <1,2,3>"],
      "answer": "A",
      "explanation": "Python列表使用方括号[]创建..."
    }
  ]
}
```

**响应（type=mindmap）：**
```json
{
  "topic": "Python列表",
  "children": [
    {
      "name": "创建方式",
      "children": [
        {"name": "字面量 []", "children": []},
        {"name": "list() 构造", "children": []}
      ]
    }
  ]
}
```

**响应（type=summary）：**
```json
{
  "topic": "Python列表",
  "summary": "Python列表是一种有序、可变的数据结构..."
}
```

---

### 4.4 评估学生答案

```
POST /agent/evaluate
Content-Type: application/json
X-Service-Key: <key>
```

**请求体：**
```json
{
  "question": "什么是Python列表？",
  "student_answer": "Python列表是一种数据结构",
  "reference_answer": "Python列表是一种有序、可变的序列类型，用方括号表示",
  "knowledge_context": "Python列表是..."
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `question` | string | 是 | 题目 |
| `student_answer` | string | 是 | 学生回答 |
| `reference_answer` | string | 否 | 参考答案 |
| `knowledge_context` | string | 否 | 相关知识上下文 |

**响应：**
```json
{
  "score": 65,
  "is_correct": true,
  "completeness": "partial",
  "correct_points": ["正确指出Python列表是数据结构"],
  "errors": [],
  "suggestions": ["补充说明列表是有序、可变的"],
  "encouragement": "回答方向正确，继续完善细节",
  "related_knowledge": ["有序序列", "可变类型"]
}
```

**Java 对应：** `AgentServiceClient.evaluateAnswer(question, answer)`

---

## 5. 工具接口

### 5.1 列出工具

```
GET /agent/tools
```

无需鉴权。

**响应：**
```json
{
  "tools": ["knowledge_retrieval", "web_search", "question_generator", "mindmap_generator", "study_plan"]
}
```

---

### 5.2 调用工具

```
POST /agent/tool
Content-Type: application/json
X-Service-Key: <key>
```

**请求体：**
```json
{
  "tool_name": "knowledge_retrieval",
  "parameters": {
    "query": "Python列表",
    "top_k": 5
  }
}
```

**响应：**
```json
{
  "result": [
    {
      "content": "Python列表是...",
      "score": 0.92,
      "source": "knowledge_1",
      "knowledge_id": 1
    }
  ],
  "tool_name": "knowledge_retrieval",
  "status": "success"
}
```

---

## 6. 会话管理接口（Redis 记忆）

### 6.1 创建会话

```
POST /agent/sessions
Content-Type: application/json
X-Service-Key: <key>
```

**请求体：**
```json
{
  "user_id": "123",
  "course_id": 1
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | string | 是 | 用户 ID |
| `course_id` | int | 否 | 课程 ID |

**响应：**
```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "created"
}
```

**说明：** 创建会话后，后续对话请求携带 `session_id` 即可自动记忆对话历史。

---

### 6.2 获取会话信息

```
GET /agent/sessions/{session_id}
X-Service-Key: <key>
```

**响应：**
```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": "123",
  "course_id": 1,
  "created_at": "2026-06-11T10:30:00",
  "last_active": "2026-06-11T11:45:00",
  "message_count": 12
}
```

---

### 6.3 删除会话

```
DELETE /agent/sessions/{session_id}
X-Service-Key: <key>
```

**响应：**
```json
{
  "status": "deleted",
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**说明：** 同时清除该会话的所有对话历史。

---

### 6.4 获取对话历史

```
GET /agent/sessions/{session_id}/history?limit=50
X-Service-Key: <key>
```

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `limit` | int | 否 | 返回条数，默认 50 |

**响应：**
```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "messages": [
    {"role": "user", "content": "什么是Python列表？"},
    {"role": "assistant", "content": "Python列表是..."}
  ],
  "count": 2
}
```

---

### 6.5 列出用户会话

```
GET /agent/users/{user_id}/sessions?limit=20
X-Service-Key: <key>
```

**响应：**
```json
{
  "user_id": "123",
  "sessions": [
    {
      "session_id": "a1b2c3d4-...",
      "user_id": "123",
      "course_id": 1,
      "created_at": "2026-06-11T10:30:00",
      "last_active": "2026-06-11T11:45:00",
      "message_count": 12
    }
  ],
  "count": 1
}
```

---

### 6.6 使用会话的对话示例

**第一步：创建会话**
```json
POST /agent/sessions
{"user_id": "123", "course_id": 1}
→ {"session_id": "abc-123", "status": "created"}
```

**第二步：带 session_id 对话**
```json
POST /agent/chat
{"message": "什么是Python列表？", "session_id": "abc-123"}
→ {"response": "Python列表是...", "session_id": "abc-123", "status": "success"}
```

**第三步：继续对话（自动携带历史）**
```json
POST /agent/chat
{"message": "它和元组有什么区别？", "session_id": "abc-123"}
→ {"response": "Python列表和元组的主要区别...", "session_id": "abc-123", "status": "success"}
```

**说明：** 携带 `session_id` 后，系统会自动从 Redis 加载最近 10 条对话历史作为上下文，无需手动传递 `history`。

---

## 7. Java AgentServiceClient 方法映射

| Java 方法 | HTTP 接口 | 说明 |
|-----------|----------|------|
| `isHealthy()` | `GET /health` | 检查 `status == "healthy"` |
| `getStatus()` | `GET /agent/status` | 获取 Agent 运行状态 |
| `chat(message)` | `POST /agent/chat` | `{"message": message}` |
| `chatWithContext(message, context)` | `POST /agent/chat/context` | `{"message": message, "context": context}` |
| `chatWithSession(message, sessionId)` | `POST /agent/chat` | `{"message": message, "session_id": sessionId}` |
| `createSession(userId, courseId)` | `POST /agent/sessions` | 创建会话 |
| `getSession(sessionId)` | `GET /agent/sessions/{sessionId}` | 获取会话信息 |
| `deleteSession(sessionId)` | `DELETE /agent/sessions/{sessionId}` | 删除会话 |
| `getConversationHistory(sessionId, limit)` | `GET /agent/sessions/{sessionId}/history` | 获取对话历史 |
| `listUserSessions(userId, limit)` | `GET /agent/users/{userId}/sessions` | 列出用户会话 |
| `ingestKnowledge(knowledgeId, courseId, content, fileType)` | `POST /agent/knowledge/ingest-text` | 文本入库 |
| `getKnowledgeStatus(knowledgeId)` | `GET /agent/knowledge/status` | 查知识库状态 |
| `generateLearningPath(studentProfile, courseId, goal)` | `POST /agent/plan` | 生成学习路径 |
| `evaluateAnswer(question, answer)` | `POST /agent/evaluate` | 评估答案 |

---

## 7. Java 调用示例

```java
// 基础对话
public String chat(String message) {
    HttpHeaders headers = createHeaders();
    Map<String, Object> body = Map.of("message", message);
    HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, headers);

    ResponseEntity<Map> resp = restTemplate.postForEntity(
        agentServiceUrl + "/agent/chat", entity, Map.class);

    return (String) resp.getBody().get("response");
}

// 带上下文对话
public String chatWithContext(String message, Map<String, Object> context) {
    HttpHeaders headers = createHeaders();
    Map<String, Object> body = Map.of("message", message, "context", context);
    HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, headers);

    ResponseEntity<Map> resp = restTemplate.postForEntity(
        agentServiceUrl + "/agent/chat/context", entity, Map.class);

    return (String) resp.getBody().get("response");
}

// 知识入库
public Map ingestKnowledge(Long knowledgeId, Long courseId, String content, String fileType) {
    HttpHeaders headers = createHeaders();
    Map<String, Object> body = Map.of(
        "knowledge_id", knowledgeId,
        "course_id", courseId,
        "content", content,
        "file_type", fileType
    );
    HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, headers);

    ResponseEntity<Map> resp = restTemplate.postForEntity(
        agentServiceUrl + "/agent/knowledge/ingest-text", entity, Map.class);

    return resp.getBody();
}

// 生成学习路径
public Map generateLearningPath(Map<String, Object> studentProfile, String courseTitle, String goal) {
    HttpHeaders headers = createHeaders();
    Map<String, Object> body = Map.of(
        "student_profile", studentProfile,
        "course_title", courseTitle,
        "goal", goal
    );
    HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, headers);

    ResponseEntity<Map> resp = restTemplate.postForEntity(
        agentServiceUrl + "/agent/plan", entity, Map.class);

    return resp.getBody();
}

// 评估答案
public Map evaluateAnswer(String question, String studentAnswer, String referenceAnswer) {
    HttpHeaders headers = createHeaders();
    Map<String, Object> body = new HashMap<>();
    body.put("question", question);
    body.put("student_answer", studentAnswer);
    body.put("reference_answer", referenceAnswer);
    HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, headers);

    ResponseEntity<Map> resp = restTemplate.postForEntity(
        agentServiceUrl + "/agent/evaluate", entity, Map.class);

    return resp.getBody();
}

// 通用请求头
private HttpHeaders createHeaders() {
    HttpHeaders headers = new HttpHeaders();
    headers.setContentType(MediaType.APPLICATION_JSON);
    headers.set("X-Service-Key", agentServiceKey);
    return headers;
}
```

---

## 8. 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `AGENT_SERVICE_KEY` | `default-dev-key` | 服务间共享密钥 |
| `LLM_PROVIDER` | `openai` | LLM 提供商 |
| `LLM_API_KEY` | — | LLM API Key |
| `LLM_BASE_URL` | — | LLM API 地址 |
| `LLM_MODEL` | — | 模型名称 |
| `EMBEDDING_API_KEY` | — | Embedding API Key（可选，不配则降级为 TF-IDF） |
| `EMBEDDING_BASE_URL` | — | Embedding API 地址 |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding 模型 |
| `REDIS_HOST` | `localhost` | Redis 主机 |
| `REDIS_PORT` | `6379` | Redis 端口 |
| `REDIS_PASSWORD` | — | Redis 密码（可选） |
| `REDIS_DB` | `0` | Redis 数据库编号 |

---

## 9. Redis 记忆系统说明

### 记忆功能

| 功能 | 说明 | TTL |
|------|------|-----|
| 对话历史 | 每个会话的消息存储在 Redis List 中 | 7 天 |
| 用户画像缓存 | 分析结果缓存，避免重复调用 LLM | 24 小时 |
| RAG 检索缓存 | 相同查询的检索结果缓存 | 1 小时 |
| 会话元数据 | 会话创建时间、用户ID、消息计数等 | 7 天 |

### 使用流程

1. **创建会话** → 获得 `session_id`
2. **对话时携带 `session_id`** → 自动加载历史、保存新消息
3. **查询历史** → 可随时查看会话内的所有消息
4. **删除会话** → 同时清除所有关联数据

### 缓存策略

- **对话历史**：自动保存，无需手动管理
- **用户画像**：首次分析后缓存，后续请求直接返回缓存（可传 `force_refresh` 强制刷新）
- **RAG 结果**：相同 query + knowledge_ids 组合会缓存 1 小时
