# Java与Python Agent集成指南

本指南详细说明如何将Python Agent服务集成到Java后端项目中。

## 架构概览

```
前端 (Web/App)
      │
      ▼
Java后端 (Spring Boot)
      │
      ├── REST API调用 ──→ Python Agent服务
      │                         │
      │                         ▼
      │                    Agent功能
      │                    • 对话管理
      │                    • 工具调用
      │                    • AI推理
      │
      └── 数据库 + 缓存
```

## 快速开始

### 1. 启动Python Agent服务

```bash
# 方式1: Docker Compose (推荐)
cd ouragent
docker-compose up -d

# 方式2: 直接运行
pip install -r requirements.txt
python src/api.py
```

服务将在 http://localhost:8000 启动

### 2. 验证服务

```bash
# 健康检查
curl http://localhost:8000/health

# 查看API文档
open http://localhost:8000/docs
```

### 3. Java项目集成

将以下文件复制到Java项目中：

```
java-examples/
├── AgentServiceClient.java    # 客户端类
├── AgentServiceConfig.java    # 配置类
├── AgentController.java       # Controller示例
└── application-agent.yml      # 配置文件
```

## Java集成步骤

### 步骤1: 添加依赖

**Maven:**
```xml
<dependencies>
    <!-- Spring Boot Starter Web -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>

    <!-- Jackson JSON -->
    <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
    </dependency>
</dependencies>
```

**Gradle:**
```groovy
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'com.fasterxml.jackson.core:jackson-databind'
}
```

### 步骤2: 复制客户端类

将 `java-examples/AgentServiceClient.java` 复制到Java项目中：

```
src/main/java/com/yourcompany/agent/client/
└── AgentServiceClient.java
```

### 步骤3: 配置服务地址

在 `application.yml` 中添加：

```yaml
agent:
  service:
    url: http://agent-service:8000  # Docker环境
    # url: http://localhost:8000    # 本地开发
    timeout: 5000
```

### 步骤4: 使用客户端

```java
@Service
public class YourService {

    @Autowired
    private AgentServiceClient agentClient;

    public String processUserMessage(String message) {
        // 调用Agent服务
        String response = agentClient.chat(message);
        return response;
    }

    public Object calculate(String expression) {
        // 调用计算器工具
        Map<String, Object> params = Map.of("expression", expression);
        return agentClient.callTool("calculator", params);
    }
}
```

## API接口文档

### 1. 对话接口

**POST** `/agent/chat`

请求:
```json
{
  "message": "你好",
  "user_id": "user123",
  "context": {
    "session_id": "abc123"
  }
}
```

响应:
```json
{
  "response": "你好！有什么可以帮您？",
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success"
}
```

**Java调用:**
```java
String response = agentClient.chat("你好", "user123");
```

### 2. 工具调用接口

**POST** `/agent/tool`

请求:
```json
{
  "tool_name": "calculator",
  "parameters": {
    "expression": "2 + 2"
  }
}
```

响应:
```json
{
  "result": 4,
  "tool_name": "calculator",
  "status": "success"
}
```

**Java调用:**
```java
Map<String, Object> params = Map.of("expression", "2 + 2");
Object result = agentClient.callTool("calculator", params);
```

### 3. 获取状态接口

**GET** `/agent/status`

响应:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "MainAgent",
  "description": "Main Agent for handling requests",
  "available_tools": ["calculator", "search"],
  "memory_size": 50
}
```

**Java调用:**
```java
AgentStatus status = agentClient.getStatus();
System.out.println("Agent: " + status.getName());
System.out.println("工具: " + status.getAvailableTools());
```

### 4. 健康检查接口

**GET** `/health`

响应:
```json
{
  "status": "healthy",
  "agent_available": true
}
```

**Java调用:**
```java
boolean isHealthy = agentClient.isHealthy();
```

## 完整示例

### Java Controller示例

```java
@RestController
@RequestMapping("/api/chat")
public class ChatController {

    @Autowired
    private AgentServiceClient agentClient;

    @PostMapping
    public ResponseEntity<Map<String, Object>> chat(
            @RequestBody ChatRequest request) {

        try {
            // 调用Agent服务
            String response = agentClient.chat(
                request.getMessage(),
                request.getUserId()
            );

            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            result.put("response", response);

            return ResponseEntity.ok(result);
        } catch (Exception e) {
            Map<String, Object> error = new HashMap<>();
            error.put("success", false);
            error.put("error", e.getMessage());

            return ResponseEntity.internalServerError().body(error);
        }
    }
}
```

### 前端调用示例

```javascript
// JavaScript
async function chat(message) {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: message,
      userId: 'user123'
    })
  });

  const data = await response.json();
  return data.response;
}

// 使用
const response = await chat("你好");
console.log(response);
```

## 高级功能

### 1. 异步调用

```java
@Async
public CompletableFuture<String> chatAsync(String message) {
    return CompletableFuture.supplyAsync(() -> {
        return agentClient.chat(message);
    });
}

// 使用
CompletableFuture<String> future = chatAsync("处理这个任务");
future.thenAccept(response -> {
    System.out.println("Agent回复: " + response);
});
```

### 2. 批量处理

```java
public List<String> batchChat(List<String> messages) {
    List<String> responses = new ArrayList<>();

    for (String message : messages) {
        try {
            String response = agentClient.chat(message);
            responses.add(response);
        } catch (Exception e) {
            responses.add("Error: " + e.getMessage());
        }
    }

    return responses;
}
```

### 3. 缓存集成

```java
@Service
public class CachedAgentService {

    @Autowired
    private AgentServiceClient agentClient;

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    public String chatWithCache(String message) {
        String cacheKey = "agent:chat:" + message.hashCode();

        // 检查缓存
        String cached = redisTemplate.opsForValue().get(cacheKey);
        if (cached != null) {
            return cached;
        }

        // 调用Agent
        String response = agentClient.chat(message);

        // 缓存结果（5分钟过期）
        redisTemplate.opsForValue().set(
            cacheKey, response, 5, TimeUnit.MINUTES
        );

        return response;
    }
}
```

### 4. 熔断器集成

```java
@Service
public class ResilientAgentService {

    @Autowired
    private AgentServiceClient agentClient;

    @CircuitBreaker(name = "agentService", fallbackMethod = "fallback")
    @Retry(name = "agentService")
    public String chat(String message) {
        return agentClient.chat(message);
    }

    public String fallback(String message, Exception e) {
        // 记录错误
        log.error("Agent服务调用失败: {}", e.getMessage());

        // 返回默认响应
        return "抱歉，AI服务暂时不可用，请稍后重试。";
    }
}
```

## 错误处理

### 常见错误码

| HTTP状态码 | 说明 | 处理方式 |
|-----------|------|---------|
| 200 | 成功 | 正常处理 |
| 400 | 请求参数错误 | 检查请求参数 |
| 404 | 工具不存在 | 检查工具名称 |
| 500 | 服务器内部错误 | 重试或降级 |
| 503 | 服务不可用 | 熔断或降级 |

### 错误处理最佳实践

```java
public String chatWithErrorHandling(String message) {
    try {
        return agentClient.chat(message);
    } catch (HttpClientErrorException e) {
        // 4xx错误
        log.warn("客户端错误: {}", e.getStatusCode());
        return "请求参数错误，请检查输入。";
    } catch (HttpServerErrorException e) {
        // 5xx错误
        log.error("服务器错误: {}", e.getStatusCode());
        return "服务暂时不可用，请稍后重试。";
    } catch (ResourceAccessException e) {
        // 连接错误
        log.error("连接失败: {}", e.getMessage());
        return "无法连接到AI服务，请检查网络。";
    }
}
```

## 性能优化

### 1. 连接池配置

```java
@Bean
public RestTemplate restTemplate() {
    HttpComponentsClientHttpRequestFactory factory =
        new HttpComponentsClientHttpRequestFactory();

    // 连接池配置
    PoolingHttpClientConnectionManager connectionManager =
        new PoolingHttpClientConnectionManager();
    connectionManager.setMaxTotal(100);
    connectionManager.setDefaultMaxPerRoute(20);

    CloseableHttpClient httpClient = HttpClients.custom()
        .setConnectionManager(connectionManager)
        .build();

    factory.setHttpClient(httpClient);
    factory.setConnectTimeout(5000);
    factory.setReadTimeout(10000);

    return new RestTemplate(factory);
}
```

### 2. 异步处理

```java
@Configuration
@EnableAsync
public class AsyncConfig {

    @Bean(name = "agentExecutor")
    public Executor agentExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(10);
        executor.setQueueCapacity(25);
        executor.setThreadNamePrefix("Agent-");
        executor.initialize();
        return executor;
    }
}

@Service
public class AsyncAgentService {

    @Async("agentExecutor")
    public CompletableFuture<String> chatAsync(String message) {
        String response = agentClient.chat(message);
        return CompletableFuture.completedFuture(response);
    }
}
```

## 监控和日志

### 1. 日志配置

```java
@Aspect
@Component
public class AgentServiceLogger {

    private static final Logger log = LoggerFactory.getLogger(AgentServiceLogger.class);

    @Around("execution(* com.yourcompany.agent.client.AgentServiceClient.*(..))")
    public Object logMethodCall(ProceedingJoinPoint joinPoint) throws Throwable {
        String methodName = joinPoint.getSignature().getName();
        Object[] args = joinPoint.getArgs();

        log.info("调用Agent服务: {} 参数: {}", methodName, args);

        long start = System.currentTimeMillis();
        Object result = joinPoint.proceed();
        long duration = System.currentTimeMillis() - start;

        log.info("Agent服务响应: {} 耗时: {}ms", methodName, duration);

        return result;
    }
}
```

### 2. 指标收集

```java
@Component
public class AgentServiceMetrics {

    private final MeterRegistry meterRegistry;

    public AgentServiceMetrics(MeterRegistry meterRegistry) {
        this.meterRegistry = meterRegistry;
    }

    public void recordChatCall(boolean success, long duration) {
        meterRegistry.counter("agent.chat.calls",
            "success", String.valueOf(success)
        ).increment();

        meterRegistry.timer("agent.chat.duration")
            .record(duration, TimeUnit.MILLISECONDS);
    }
}
```

## 部署配置

### Docker Compose (完整环境)

```yaml
version: '3.8'

services:
  java-backend:
    build: ./java-backend
    ports:
      - "9000:9000"
    environment:
      - AGENT_SERVICE_URL=http://agent-service:8000
    depends_on:
      - agent-service
      - postgres
      - redis

  agent-service:
    build: ./ouragent
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
      - DEBUG=false
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: app_db
      POSTGRES_USER: app
      POSTGRES_PASSWORD: password
    volumes:
      - postgres-data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - java-backend
      - agent-service

volumes:
  postgres-data:
  redis-data:
```

### 环境变量配置

```bash
# .env
AGENT_SERVICE_URL=http://agent-service:8000
AGENT_SERVICE_TIMEOUT=5000
AGENT_SERVICE_RETRY_MAX=3
```

## 常见问题

### Q: Agent服务连接超时
A: 检查网络连接和防火墙设置，增加超时时间。

### Q: 响应格式不匹配
A: 确保Java客户端使用正确的JSON解析库。

### Q: 并发性能问题
A: 使用连接池和异步调用优化性能。

### Q: 服务发现
A: 使用Consul或Eureka进行服务注册和发现。

## 总结

通过以上配置，Java后端可以轻松调用Python Agent服务。关键点：

1. **简单集成**: 使用REST API，无需复杂配置
2. **灵活调用**: 支持同步、异步、批量调用
3. **高可用**: 支持熔断、重试、降级
4. **易于监控**: 完整的日志和指标收集

这种架构既保证了Java后端的稳定性，又充分利用了Python在AI领域的优势。
