# 微服务架构文档

## 架构概述

本项目采用**Java + Python微服务架构**，Java负责主要业务逻辑和页面请求，Python Agent作为独立服务提供AI能力。

## 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      客户端 (Web/App)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Nginx (反向代理)                         │
│                     负载均衡 & 路由                          │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
            ▼                 ▼                 ▼
┌───────────────────┐ ┌───────────────┐ ┌───────────────┐
│   Java Backend    │ │ Agent Service │ │  其他服务      │
│   (主要业务)      │ │ (Python AI)   │ │              │
│                   │ │               │ │              │
│ • 页面请求        │ │ • Agent对话   │ │ • 用户服务   │
│ • 业务逻辑        │ │ • 工具调用    │ │ • 订单服务   │
│ • 数据处理        │ │ • AI推理     │ │ • 支付服务   │
│ • 认证授权        │ │ • 知识库     │ │              │
└───────────────────┘ └───────────────┘ └───────────────┘
            │                 │                 │
            └─────────────────┼─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    数据层                                    │
├───────────────────┬───────────────────┬───────────────────┤
│    PostgreSQL     │      Redis        │   Message Queue   │
│    (主数据库)      │     (缓存)        │    (消息队列)      │
└───────────────────┴───────────────────┴───────────────────┘
```

## 技术栈

### Java后端
- **框架**: Spring Boot 2.7+ / 3.0+
- **构建**: Maven / Gradle
- **数据库**: MyBatis / JPA
- **缓存**: Spring Data Redis
- **消息**: RabbitMQ / Kafka
- **安全**: Spring Security + JWT

### Python Agent服务
- **框架**: FastAPI
- **AI**: LangChain / OpenAI
- **数据库**: SQLAlchemy
- **缓存**: Redis
- **部署**: Docker + Uvicorn

### 基础设施
- **容器**: Docker + Docker Compose
- **反向代理**: Nginx
- **监控**: Prometheus + Grafana
- **日志**: ELK Stack

## 服务划分

### 1. Java后端服务 (主要)
**职责**: 处理主要业务逻辑

```
├── 用户管理
│   ├── 注册/登录
│   ├── 权限管理
│   └── 用户信息
│
├── 页面请求
│   ├── Web页面渲染
│   ├── API接口
│   └── 静态资源
│
├── 业务逻辑
│   ├── 订单处理
│   ├── 支付处理
│   └── 数据分析
│
└── 系统管理
    ├── 配置管理
    ├── 日志管理
    └── 监控告警
```

**端口**: 9000

### 2. Python Agent服务
**职责**: 提供AI能力

```
├── Agent对话
│   ├── 自然语言理解
│   ├── 对话管理
│   └── 响应生成
│
├── 工具调用
│   ├── 计算器
│   ├── 搜索引擎
│   └── 自定义工具
│
├── 知识库
│   ├── 文档检索
│   ├── 问答匹配
│   └── 知识更新
│
└── AI推理
    ├── 模型调用
    ├── 结果处理
    └── 缓存优化
```

**端口**: 8000

## 通信方式

### 1. REST API (推荐)
```java
// Java调用Python Agent
RestTemplate restTemplate = new RestTemplate();
String response = restTemplate.postForObject(
    "http://agent-service:8000/agent/chat",
    new ChatRequest("你好"),
    String.class
);
```

**优点**:
- 简单易用
- 跨语言支持
- 易于调试

**适用场景**:
- 大部分业务场景
- 同步请求
- 简单的数据交换

### 2. gRPC (高性能)
```java
// Java调用Python Agent (gRPC)
ManagedChannel channel = ManagedChannelBuilder
    .forAddress("agent-service", 50051)
    .usePlaintext()
    .build();

AgentServiceGrpc.AgentServiceBlockingStub stub =
    AgentServiceGrpc.newBlockingStub(channel);

ChatResponse response = stub.chat(
    ChatRequest.newBuilder()
        .setMessage("你好")
        .build()
);
```

**优点**:
- 高性能
- 强类型
- 双向流

**适用场景**:
- 高并发场景
- 实时通信
- 性能要求高

### 3. 消息队列 (异步)
```java
// Java发送消息到队列
rabbitTemplate.convertAndSend(
    "agent.exchange",
    "agent.chat",
    new ChatMessage("你好", "user123")
);

// Python消费消息
@rabbit_consumer(queue="agent.chat")
def handle_chat(message):
    response = agent.chat(message.content)
    # 发送响应到另一个队列
```

**优点**:
- 异步处理
- 解耦
- 削峰填谷

**适用场景**:
- 耗时任务
- 批量处理
- 事件驱动

## 数据流示例

### 场景1: 用户与Agent对话

```
1. 用户 → Java后端: POST /api/chat {"message": "你好"}
2. Java后端 → Python Agent: POST /agent/chat {"message": "你好"}
3. Python Agent → Java后端: {"response": "你好！有什么可以帮您？"}
4. Java后端 → 用户: {"success": true, "response": "你好！有什么可以帮您？"}
```

### 场景2: 调用Agent工具

```
1. 用户 → Java后端: POST /api/tool {"tool": "calculator", "expr": "2+2"}
2. Java后端 → Python Agent: POST /agent/tool {"tool_name": "calculator", "parameters": {...}}
3. Python Agent → Java后端: {"result": 4}
4. Java后端 → 用户: {"success": true, "result": 4}
```

### 场景3: 异步任务处理

```
1. 用户 → Java后端: POST /api/task {"task": "analyze", "data": {...}}
2. Java后端 → 消息队列: 发送任务消息
3. 消息队列 → Python Agent: 消费任务
4. Python Agent处理任务...
5. Python Agent → 消息队列: 发送结果
6. 消息队列 → Java后端: 消费结果
7. Java后端 → 用户: WebSocket推送结果
```

## 部署架构

### Docker Compose (本地开发)
```yaml
services:
  java-backend:
    build: ./java-backend
    ports:
      - "9000:9000"
    depends_on:
      - agent-service
      - postgres
      - redis

  agent-service:
    build: ./agent-service
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15

  redis:
    image: redis:7-alpine

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### Kubernetes (生产环境)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agent-service
  template:
    spec:
      containers:
      - name: agent-service
        image: agent-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: APP_ENV
          value: "production"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## Nginx配置

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    # Java后端
    upstream java_backend {
        server java-backend:9000;
    }

    # Python Agent服务
    upstream agent_service {
        server agent-service:8000;
    }

    server {
        listen 80;

        # Java后端路由
        location /api/ {
            proxy_pass http://java_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Agent服务路由
        location /agent/ {
            proxy_pass http://agent_service;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # 静态资源
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
        }
    }
}
```

## 监控和日志

### 监控指标
```yaml
# Prometheus配置
scrape_configs:
  - job_name: 'java-backend'
    static_configs:
      - targets: ['java-backend:9000']

  - job_name: 'agent-service'
    static_configs:
      - targets: ['agent-service:8000']
```

### 日志收集
```yaml
# ELK Stack配置
filebeat.inputs:
- type: container
  paths:
    - '/var/lib/docker/containers/*/*.log'

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
```

## 安全考虑

### 1. 认证授权
- Java后端统一处理用户认证
- Agent服务通过内部API密钥认证
- JWT token传递用户身份

### 2. 网络隔离
- 服务间通过内部网络通信
- 只暴露必要的端口
- 使用HTTPS

### 3. 数据加密
- 敏感数据加密存储
- 传输层使用TLS
- API密钥安全存储

## 性能优化

### 1. 缓存策略
```
Redis缓存
├── 热点数据缓存
├── 会话缓存
├── Agent响应缓存
└── 配置缓存
```

### 2. 连接池
```java
// RestTemplate连接池配置
@Bean
public RestTemplate restTemplate() {
    HttpComponentsClientHttpRequestFactory factory =
        new HttpComponentsClientHttpRequestFactory();
    factory.setConnectTimeout(5000);
    factory.setReadTimeout(10000);
    return new RestTemplate(factory);
}
```

### 3. 异步处理
```java
// 异步调用Agent
@Async
public CompletableFuture<String> chatAsync(String message) {
    return CompletableFuture.supplyAsync(() -> {
        return agentClient.chat(message);
    });
}
```

## 故障处理

### 1. 熔断器
```java
// 使用Resilience4j
@CircuitBreaker(name = "agentService", fallbackMethod = "fallback")
public String chat(String message) {
    return agentClient.chat(message);
}

public String fallback(String message, Exception e) {
    return "Agent服务暂时不可用，请稍后重试";
}
```

### 2. 重试机制
```java
@Retry(name = "agentService", maxAttempts = 3)
public String chat(String message) {
    return agentClient.chat(message);
}
```

### 3. 降级策略
- Agent服务不可用时返回默认响应
- 缓存最近的成功响应
- 记录失败请求用于后续处理

## 扩展性

### 1. 水平扩展
```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agent-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agent-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 2. 负载均衡
- Nginx轮询
- Kubernetes Service
- Consul服务发现

## 最佳实践

### 1. 开发规范
- 统一的API响应格式
- 完善的错误处理
- 详细的日志记录
- 完整的单元测试

### 2. 部署规范
- CI/CD自动化
- 蓝绿部署
- 金丝雀发布
- 回滚机制

### 3. 运维规范
- 监控告警
- 日志收集
- 性能优化
- 安全审计

## 总结

这种Java + Python微服务架构具有以下优势：

1. **职责清晰**: Java处理业务，Python处理AI
2. **技术匹配**: 各自发挥语言优势
3. **独立部署**: 服务独立，互不影响
4. **易于扩展**: 可以独立扩展各个服务
5. **团队协作**: 不同团队可以并行开发

这种架构非常适合您的项目需求，既保证了系统的稳定性，又提供了灵活的AI能力。
