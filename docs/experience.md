# 从零部署 OurAgent 项目 —— 完整经验指南

> 本文档记录了将整个项目从代码状态部署为 Docker 容器的完整过程、踩过的坑、以及每个部分的原理说明。
> 目标读者：新手，有基础编程能力但不熟悉 Docker/微服务部署。

---

## 一、最终实现了什么

通过 `docker-compose up -d` 一条命令，启动了 **6 个服务**，全部 healthy：

| 服务 | 端口 | 作用 | 技术栈 |
|------|------|------|--------|
| **agent-service** | 8000 | Python AI Agent 微服务 | FastAPI + SQLAlchemy + PostgreSQL |
| **java-backend** | 9000 | Java 业务后端 | Spring Boot 3.2 + MyBatis-Plus + MySQL |
| **mysql** | 3307(外)/3306(内) | Java 端数据库 | MySQL 8.0 |
| **postgres** | 5432 | Python 端数据库 | PostgreSQL 15 |
| **redis** | 6379 | 共享缓存 | Redis 7 |
| **nginx** | 80 | 反向代理 | Nginx Alpine |

架构图：

```
用户浏览器
    |
    v
  Nginx (:80)
    |--- /api/auth/*  --> java-backend (:9000) --> MySQL (:3306)
    |--- /api/agent/* --> java-backend (:9000) --(内部调用)--> agent-service (:8000)
    |                                                    |--> PostgreSQL (:5432)
    |                                                    \--> Redis (:6379)
```

**职责划分**：
- **Java 后端**：唯一面向前端的入口，处理所有用户认证、业务逻辑、数据存储
- **Python Agent**：内部 AI 服务，只提供 AI 对话/工具/向量化能力，通过 `X-Service-Key` 密钥保护

验证命令：
```bash
docker-compose ps                          # 查看所有服务状态
curl http://localhost:8000/health          # Python Agent 健康检查
curl -X POST http://localhost:9000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'  # Java 登录（401=正常，DB在工作）
```

---

## 二、项目目录结构速查

```
ouragent/
├── docker-compose.yml          # 主编排文件（生产配置）
├── docker-compose.override.yml # 开发覆盖配置（自动加载，优先级高于主文件）
├── docker-compose.prod.yml     # 纯生产配置（可选）
├── Dockerfile                  # Python Agent 的 Docker 构建文件
├── nginx/nginx.conf            # Nginx 反向代理配置
├── v3/                         # Python Agent 项目
│   ├── requirements-core.txt   # 核心依赖（Docker 构建用这个）
│   ├── requirements-ml.txt     # ML/RAG 依赖（步骤5-6才需要）
│   ├── config/settings.py      # 配置文件
│   └── src/
│       ├── api.py              # FastAPI 主入口（所有端点定义）
│       ├── auth/security.py    # JWT 认证
│       ├── db/database.py      # 数据库连接
│       ├── db/models.py        # 数据模型
│       └── core/agent.py       # Agent 核心逻辑
└── javaarea/                   # Java Spring Boot 项目
    ├── Dockerfile              # Java 的 Docker 构建文件
    ├── pom.xml                 # Maven 依赖
    └── src/main/resources/
        ├── application.yml     # 共享配置
        ├── application-dev.yml # 开发环境配置
        ├── application-prod.yml# 生产环境配置
        └── db/schema.sql       # 数据库建表 SQL
```

---

## 三、从零开始：一步步配置说明

### 第 1 步：前置环境准备

你需要安装：

| 工具 | 用途 | 检查命令 |
|------|------|----------|
| Docker Desktop | 容器运行环境 | `docker --version` |
| Docker Compose | 多容器编排 | `docker-compose --version` |
| Git | 版本管理 | `git --version` |

**Windows 用户注意**：
- Docker Desktop 需要开启 WSL2 或 Hyper-V 后端
- 安装后重启电脑
- 确保 Docker Desktop 图标显示"Engine running"

### 第 2 步：理解 docker-compose.yml

这是整个部署的核心文件。它定义了"要启动哪些服务、它们怎么连接"。

**关键概念**：
- **service**：一个容器化服务（如 mysql、java-backend）
- **depends_on + condition: service_healthy**：等前置服务健康后再启动
- **healthcheck**：Docker 定期检查服务是否正常工作
- **networks**：所有服务在同一个虚拟网络里，可以用服务名互相访问
- **volumes**：数据持久化，容器删了数据还在

**服务启动顺序**（由 depends_on 决定）：
```
redis, mysql, postgres  （三个数据库先启动）
        |
        v
   agent-service        （等 postgres 和 redis 健康）
        |
        v
   java-backend         （等 mysql、redis、agent-service 健康）
        |
        v
      nginx             （等 java-backend 和 agent-service）
```

### 第 3 步：理解 Dockerfile（Python Agent）

文件位置：项目根目录 `Dockerfile`

```dockerfile
# 两阶段构建：第一阶段装依赖，第二阶段只复制结果
# 好处：最终镜像不包含 gcc 等编译工具，体积小

FROM python:3.13-slim AS builder    # 第一阶段：构建
WORKDIR /build
COPY v3/requirements-core.txt .     # 先复制依赖文件（利用缓存）
RUN pip install -r requirements-core.txt

FROM python:3.13-slim               # 第二阶段：运行
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv  # 只复制装好的虚拟环境
COPY v3/ .                          # 复制源代码
ENV PYTHONPATH=/app                 # 关键！让 Python 能找到 src 模块
CMD ["python", "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

**重要**：`COPY v3/ .` 会把 v3/ 下的所有文件复制到容器的 /app/ 目录。
所以容器内的目录结构是 `/app/src/api.py`，不是 `/app/v3/src/api.py`。
这就是为什么 `PYTHONPATH=/app` 能让 `import src.api` 正常工作。

### 第 4 步：理解 Dockerfile（Java 后端）

文件位置：`javaarea/Dockerfile`

```dockerfile
FROM maven:3.9-eclipse-temurin-17 AS builder   # 构建阶段：用 Maven 编译
WORKDIR /build
COPY pom.xml .
RUN mvn dependency:go-offline -B               # 先下载依赖（缓存）
COPY src/ ./src/
RUN mvn clean package -DskipTests -B           # 编译打包

FROM eclipse-temurin:17-jre-alpine             # 运行阶段：只有 JRE
WORKDIR /app
COPY --from=builder /build/target/*.jar app.jar
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
```

**注意**：`ENTRYPOINT` 用的是 `sh -c`，所以 `$JAVA_OPTS` 会被 shell 展开。
这意味着 docker-compose.yml 里的 `JAVA_OPTS` 环境变量能生效。

### 第 5 步：理解数据库配置

**MySQL（给 Java 用）**：
- 服务名：`mysql`（Docker 内部 DNS 解析用这个名字）
- 数据库名：`edu`
- 用户名/密码：`edu` / `edu_password`
- 对外端口：3307（避免和本机 MySQL 冲突）

**PostgreSQL（给 Python 用）**：
- 服务名：`postgres`
- 数据库名：`agent_db`
- 用户名/密码：`agent` / `agent_password`
- 对外端口：5432

**Redis（共享缓存）**：
- 服务名：`redis`
- 无密码
- 对外端口：6379

### 第 6 步：理解环境变量如何传递

docker-compose.yml 里的 `environment` 会注入到容器中。

**Java 后端的环境变量传递链**：
```
docker-compose.yml          application-prod.yml         Java 代码
─────────────────          ────────────────────         ─────────
DB_HOST=mysql        -->   ${DB_HOST:mysql}        -->   连接 mysql:3306
DB_USER=edu    -->   ${DB_USER:edu}    -->   用 edu 登录
DB_PASSWORD=xxx      -->   ${DB_PASSWORD:}         -->   密码 xxx
```

`${DB_HOST:mysql}` 的意思是：如果环境变量 `DB_HOST` 存在就用它的值，否则用 `mysql` 作为默认值。

### 第 7 步：理解 docker-compose.override.yml

**这是新手最容易踩坑的地方！**

`docker-compose.override.yml` 会**自动加载**，并且**覆盖** `docker-compose.yml` 中的同名配置。

```yaml
# docker-compose.yml 里写的是：
java-backend:
  environment:
    - SPRING_PROFILES_ACTIVE=prod    # 生产环境

# docker-compose.override.yml 里写的是：
java-backend:
  environment:
    - SPRING_PROFILES_ACTIVE=dev     # 开发环境 ← 这个会覆盖上面的！
```

**最终生效的是 `dev`**，因为 override 优先级更高。

我们实际部署时遇到的问题：Java 后端一直连不上 MySQL，排查了很久才发现是 override 文件把 profile 改成了 dev，导致 Java 去连 `localhost:3306`（容器内没有 MySQL）而不是 `mysql:3306`。

**教训**：部署前一定要检查 override 文件，确认里面的配置是你想要的。

### 第 8 步：理解 healthcheck

healthcheck 是 Docker 判断"服务是否正常"的机制。

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s      # 每 30 秒检查一次
  timeout: 10s       # 单次检查超时时间
  start_period: 15s  # 启动后等 15 秒再开始检查
  retries: 3         # 连续失败 3 次才标记为 unhealthy
```

`-f` 参数让 curl 在 HTTP 错误（4xx/5xx）时返回非零退出码。
如果服务返回 401/403，curl -f 也会判定为失败。

**Java 后端的 healthcheck 特殊处理**：
Java 后端的所有 GET 请求都需要认证（返回 403），所以 healthcheck 用的是 POST 登录接口：
```yaml
test: ["CMD", "curl", "-f", "-X", "POST", "-H", "Content-Type: application/json",
       "-d", '{"username":"health","password":"check"}',
       "http://localhost:9000/api/auth/login"]
```
登录接口即使用户名密码错误也会返回 200（或 401），不会返回 403，所以能通过 `-f` 检查。

### 第 9 步：启动部署

```bash
# 在项目根目录执行
docker-compose up -d

# 查看启动状态
docker-compose ps

# 查看某个服务的日志
docker-compose logs -f agent-service
docker-compose logs -f java-backend

# 如果某个服务 unhealthy，看详细日志
docker-compose logs --tail 50 java-backend
```

### 第 10 步：验证各端点

```bash
# Python Agent
curl http://localhost:8000/health
curl http://localhost:8000/agent/tools
curl http://localhost:8000/docs            # Swagger API 文档

# Java 后端
curl -X POST http://localhost:9000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'
# 期望：{"code":401,"message":"用户名或密码无效"} ← 说明 DB 连接正常

# Nginx（如果配置了路由规则）
curl http://localhost:80
```

---

## 四、踩过的坑和解决方案

### 坑 1：Python 模块导入失败（ModuleNotFoundError）

**现象**：agent-service 启动后报 `ModuleNotFoundError: No module named 'db'`

**原因**：源代码里写的是 `from db.database import ...`，但容器内目录结构是 `/app/src/db/`。
Python 在 `PYTHONPATH=/app` 下找不到 `/app/db/`，只能找到 `/app/src/db/`。

**解决**：改导入路径为 `from src.db.database import ...`，或者用相对导入 `from .database import ...`。

**涉及文件**：
- `v3/src/api.py`：`from db.database` → `from src.db.database`
- `v3/src/api.py`：`from auth.security` → `from src.auth.security`
- `v3/src/db/init_db.py`：`from db.database` → `from .database`（相对导入）
- `v3/src/db/models.py`：`from db.database` → `from .database`（相对导入）

### 坑 2：MySQL 端口冲突

**现象**：`docker-compose up` 报端口 3306 已被占用

**原因**：本机已经运行了 MySQL 服务（mysqld.exe），占用了 3306 端口。

**解决**：把 MySQL 的对外端口改为 3307：
```yaml
mysql:
  ports:
    - "3307:3306"    # 外部 3307 -> 容器内 3306
```

**注意**：要同时检查 `docker-compose.yml` 和 `docker-compose.override.yml` 两个文件里的端口配置。

### 坑 3：MySQL 8 认证方式不兼容

**现象**：Java 后端连 MySQL 报 `Communications link failure` 或认证错误

**原因**：MySQL 8 默认用 `caching_sha2_password` 认证，某些 JDBC 驱动不支持。

**解决**：
```bash
# 进入 MySQL 容器，改认证方式
docker exec edu-mysql mysql -u root -proot_password -e \
  "ALTER USER 'edu'@'%' IDENTIFIED WITH mysql_native_password BY 'edu_password'; FLUSH PRIVILEGES;"
```

同时在 JDBC URL 里加参数：
```yaml
url: jdbc:mysql://mysql:3306/edu_agent?...&useSSL=false&allowPublicKeyRetrieval=true
```

### 坑 4：schema.sql 没有自动执行

**现象**：MySQL 启动了但表是空的

**原因**：docker-compose.yml 里挂载了 init 脚本：
```yaml
volumes:
  - ./javaarea/src/main/resources/db/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql:ro
```
但在 Windows 上，路径解析有时会失败（Docker Desktop 的已知问题）。

**解决**：手动执行建表 SQL：
```bash
docker exec -i edu-mysql mysql -u root -proot_password edu < javaarea/src/main/resources/db/schema.sql
```

**注意**：schema.sql 里有 `CREATE DATABASE edu; USE edu;`，但实际数据库名是 `edu_agent`。
需要去掉这两行，或者直接在 `edu` 库里执行建表语句。

### 坑 5：Spring Profile 不生效

**现象**：Java 后端日志显示 `The following 1 profile is active: "dev"`，但 docker-compose.yml 里写了 `SPRING_PROFILES_ACTIVE=prod`

**原因**：`docker-compose.override.yml` 里有：
```yaml
java-backend:
  environment:
    - SPRING_PROFILES_ACTIVE=dev    # 覆盖了主文件的 prod！
```

**解决**：把 override 文件里的 profile 也改成 `prod`，或者直接删掉 override 文件中 java-backend 的 environment 配置。

**验证方法**：
```bash
# 检查容器内实际的环境变量
docker exec java-backend sh -c "echo \$SPRING_PROFILES_ACTIVE"
```

### 坑 6：Dockerfile CMD 写错

**现象**：agent-service 启动后立即退出

**原因**：CMD 写的是 `src.main:app`，但 app 变量定义在 `src/api.py` 里，不在 `src/main.py` 里。

**解决**：改为 `src.api:app`。

---

## 五、常用 Docker 命令速查

```bash
# 启动所有服务
docker-compose up -d

# 重新构建并启动（代码改了之后）
docker-compose up -d --build

# 只重建某个服务
docker-compose up -d --build agent-service

# 查看所有服务状态
docker-compose ps

# 查看日志（实时跟踪）
docker-compose logs -f java-backend
docker-compose logs -f agent-service

# 查看最近 50 行日志
docker-compose logs --tail 50 java-backend

# 进入容器内部（调试用）
docker exec -it agent-service sh        # Python 容器（Debian）
docker exec -it java-backend sh         # Java 容器（Alpine）
docker exec -it edu-mysql mysql -u root -proot_password  # 进入 MySQL

# 停止所有服务
docker-compose down

# 停止并删除数据卷（慎用！会清空数据库）
docker-compose down -v

# 查看容器的环境变量
docker exec java-backend env | grep DB_

# 查看容器的网络
docker network inspect ouragent_edu-network
```

---

## 六、配置文件修改速查表

| 你想改什么 | 改哪个文件 | 具体位置 |
|-----------|-----------|---------|
| Python Agent 端口 | `Dockerfile` | `EXPOSE 8000` 和 `CMD` 里的 `--port 8000` |
| Java 后端端口 | `docker-compose.yml` | `java-backend.ports` 和 `server.port` |
| MySQL 密码 | `docker-compose.yml` | `mysql.environment.MYSQL_PASSWORD` |
| MySQL 对外端口 | `docker-compose.override.yml` | `mysql.ports` |
| PostgreSQL 密码 | `docker-compose.yml` | `postgres.environment.POSTGRES_PASSWORD` |
| Redis 密码 | `docker-compose.yml` | `redis` 服务 + `agent-service.environment.REDIS_PASSWORD` |
| Java 连哪个数据库 | `application-prod.yml` | `spring.datasource.url` |
| Python 连哪个数据库 | `docker-compose.yml` | `agent-service.environment.DB_HOST` |
| JWT 密钥 | `docker-compose.yml` | `java-backend.environment.JWT_SECRET` |
| Nginx 路由规则 | `nginx/nginx.conf` | `location` 块 |
| 开发/生产环境切换 | `docker-compose.override.yml` | `SPRING_PROFILES_ACTIVE` |

---

## 七、排错流程图

```
服务 unhealthy？
    |
    ├── docker-compose logs <服务名> 看日志
    |       |
    |       ├── Connection refused → 检查目标服务是否启动、网络是否通
    |       ├── ModuleNotFoundError → 检查 Python 导入路径
    |       ├── Port already in use → 改端口或停掉占用端口的进程
    |       └── Authentication failed → 检查用户名密码、认证插件
    |
    ├── docker-compose ps 看所有服务状态
    |       |
    |       ├── 某个服务 unhealthy → 看它的 healthcheck 配置
    |       └── 某个服务 Exit → 看它的启动日志
    |
    └── 进容器调试
            |
            ├── docker exec -it <容器名> sh
            ├── ping <目标服务名>        # 测试 DNS 和网络
            ├── nc -zv <目标服务名> <端口>  # 测试 TCP 连接
            └── env | grep <变量名>      # 检查环境变量
```

---

## 八、数据持久化说明

Docker volume 保证数据不会因为容器重启而丢失：

```yaml
volumes:
  mysql-data:       # MySQL 数据 → /var/lib/mysql
  postgres-data:    # PostgreSQL 数据 → /var/lib/postgresql/data
  redis-data:       # Redis 数据 → /data
  agent-uploads:    # Agent 上传文件 → /app/uploads
  agent-logs:       # Agent 日志 → /app/logs
```

**查看 volume**：`docker volume ls`
**删除 volume**：`docker volume rm <名字>`（会丢数据！）
**清空所有**：`docker-compose down -v`（会丢所有数据！）

---

## 九、开发模式 vs 生产模式

| 配置项 | 开发模式（override） | 生产模式（主文件） |
|--------|---------------------|-------------------|
| Spring Profile | `prod`（已改为 prod） | `prod` |
| Java JVM 内存 | 128m-256m | 256m-512m |
| Python 日志级别 | DEBUG | INFO |
| Python 热重载 | 有（--reload） | 无 |
| 数据卷挂载 | 注释掉了 | 无 |

**切换方法**：
- 开发时用 `docker-compose up`（自动加载 override）
- 生产部署用 `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d`

---

## 十、下一步要做什么

当前状态：框架跑通，所有服务 healthy，但功能还是骨架。

按 CLAUDE.md 中的步骤继续：
1. ~~第一步：让框架跑通~~ ← **已完成**
2. 第二步：Python Agent 接入 LLM（从 Echo 变真 AI）
3. 第三步：实现 Python 工具系统
4. 第四步：Java 端业务模块实现
5. 第五步：扩展多智能体系统
6. 第六步：RAG 知识库集成
7. 第七步：前端开发
8. 第八步：集成测试与部署完善
