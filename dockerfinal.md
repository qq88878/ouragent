# OurAgent Docker 部署文档

> 基于大模型的个性化资源生成与学习多智能体系统

---

## 1. 项目架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx (:8080)                        │
│                    反向代理 + 前端静态资源                      │
├─────────────────────────────────────────────────────────────┤
│         │                           │                       │
│         ▼                           ▼                       │
│  ┌──────────────┐          ┌──────────────┐                │
│  │ Java Backend │          │ Agent Service │                │
│  │   (:9001)    │◄────────►│   (:8001)    │                │
│  └──────────────┘          └──────────────┘                │
│         │                           │                       │
│         ▼                           ▼                       │
│  ┌──────────────┐          ┌──────────────┐                │
│  │    MySQL     │          │    Redis     │                │
│  │   (:3308)    │          │   (:6380)    │                │
│  └──────────────┘          └──────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### 服务列表

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| Nginx | edu-nginx | 8080 | 反向代理 + Vue 前端 |
| Java Backend | java-backend | 9001 | 教育系统后端 |
| Agent Service | agent-service | 8001 | Python AI Agent |
| MySQL | edu-mysql | 3308 | 数据库 |
| Redis | edu-redis | 6380 | 缓存 |

---

## 2. 环境要求

- **Docker**: >= 20.10
- **Docker Compose**: >= 2.0
- **内存**: >= 4GB
- **磁盘**: >= 10GB

---

## 3. 目录结构

```
ouragent/
├── .env                      # 环境变量配置（核心）
├── .dockerignore             # Docker 忽略文件
├── docker-compose.yml        # Docker Compose 编排
├── Dockerfile                # Python Agent 镜像构建
├── nginx/
│   └── nginx.conf            # Nginx 配置
├── javaarea/
│   ├── Dockerfile            # Java 后端镜像构建
│   └── src/main/resources/db/
│       ├── schema.sql        # 数据库表结构
│       └── seed.sql          # 初始数据
├── v3/
│   ├── config/
│   │   ├── settings.py       # Python 配置
│   │   ├── .env              # Python 环境变量
│   │   └── mysql-init.sql    # MySQL 初始化脚本
│   ├── src/                  # Python 源码
│   ├── data/                 # 向量库数据
│   └── requirements-core.txt # Python 依赖
└── frontend/
    └── dist/                 # Vue 构建产物
```

---

## 4. 配置文件详解

### 4.1 `.env` 文件（项目根目录）

这是**最核心的配置文件**，所有 API Key 和密码都在这里配置。

```bash
# ==================== MySQL 数据库 ====================
MYSQL_ROOT_PASSWORD=your_mysql_password    # 必须修改！
MYSQL_DATABASE=edu_agent

# ==================== Java 后端 ====================
SPRING_PROFILES_ACTIVE=prod
JAVA_OPTS=-Xms256m -Xmx512m -Djava.net.preferIPv4Stack=true
DB_HOST=mysql
DB_USER=root
DB_PASSWORD=your_mysql_password            # 与 MYSQL_ROOT_PASSWORD 一致
REDIS_HOST=redis
AGENT_SERVICE_URL=http://agent-service:8000
AGENT_SERVICE_KEY=internal-agent-key-2024  # 服务间认证密钥
AGENT_TIMEOUT=10000

# ==================== 邮件服务（可选） ====================
MAIL_HOST=smtp.qq.com
MAIL_PORT=587
MAIL_USERNAME=your_email@qq.com
MAIL_PASSWORD=your_email_password
APP_BASE_URL=http://localhost

# ==================== Python Agent ====================
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO
DB_NAME=edu_agent
DB_PORT=3306
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
REDIS_PORT=6379
REDIS_PASSWORD=
SECRET_KEY=your-secret-key-change-in-production  # 必须修改！

# ==================== JWT ====================
JWT_SECRET=your-jwt-secret-key-that-is-long-enough  # 必须修改！

# ==================== LLM 大模型 ====================
LLM_PROVIDER=openai
LLM_API_KEY=your_llm_api_key              # 必须填写！
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct

# ==================== Embedding 向量嵌入 ====================
EMBEDDING_API_KEY=your_embedding_api_key   # 必须填写！
EMBEDDING_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5

# ==================== 时区 ====================
TZ=Asia/Shanghai
```

**必须修改的配置项**：
1. `MYSQL_ROOT_PASSWORD` - MySQL 密码
2. `DB_PASSWORD` - 与 MySQL 密码一致
3. `SECRET_KEY` - Python Agent 密钥
4. `JWT_SECRET` - JWT 签名密钥
5. `LLM_API_KEY` - LLM API Key
6. `EMBEDDING_API_KEY` - Embedding API Key

---

### 4.2 API Key 获取指南

#### 方案一：硅基流动（推荐，免费额度）

1. 访问 https://siliconflow.cn 注册
2. 获取 API Key
3. 配置：
```bash
LLM_API_KEY=sk-xxxxxxxx
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct

EMBEDDING_API_KEY=sk-xxxxxxxx
EMBEDDING_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
```

#### 方案二：星火大模型（比赛要求）

1. 访问 https://xinghuo.xfyun.cn 注册
2. 获取 APP_ID、API_KEY、API_SECRET
3. 配置：
```bash
LLM_PROVIDER=spark
SPARK_APP_ID=your_app_id
SPARK_API_KEY=your_api_key
SPARK_API_SECRET=your_api_secret
SPARK_MODEL=generalv3.5
SPARK_BASE_URL=https://spark-api-open.xf-yun.com/v1
```

#### 方案三：OpenAI / DeepSeek

```bash
LLM_API_KEY=sk-xxxxxxxx
LLM_BASE_URL=https://api.openai.com/v1  # 或 https://api.deepseek.com/v1
LLM_MODEL=gpt-3.5-turbo  # 或 deepseek-chat
```

---

### 4.3 `docker-compose.yml` 说明

```yaml
services:
  # Nginx 反向代理 + 前端
  nginx:
    image: nginx:alpine
    ports:
      - "8080:80"              # 前端访问端口
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./frontend/dist:/usr/share/nginx/html:ro

  # Java 后端
  java-backend:
    build:
      context: ./javaarea
      dockerfile: Dockerfile
    ports:
      - "9001:9000"            # Java API 端口
    environment:
      - DB_PASSWORD=${MYSQL_ROOT_PASSWORD}  # 从 .env 读取
      - AGENT_SERVICE_KEY=${AGENT_SERVICE_KEY}
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
      agent-service:
        condition: service_healthy

  # Python Agent 服务
  agent-service:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8001:8000"            # Agent API 端口
    environment:
      - LLM_API_KEY=${LLM_API_KEY}          # 从 .env 读取
      - EMBEDDING_API_KEY=${EMBEDDING_API_KEY}
    volumes:
      - agent-uploads:/app/uploads
      - agent-logs:/app/logs

  # MySQL 数据库
  mysql:
    image: mysql:8.0
    ports:
      - "3308:3306"            # MySQL 端口
    volumes:
      - mysql-data:/var/lib/mysql
      - ./javaarea/src/main/resources/db/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql:ro
      - ./v3/config/mysql-init.sql:/docker-entrypoint-initdb.d/02-agent.sql:ro
      - ./javaarea/src/main/resources/db/seed.sql:/docker-entrypoint-initdb.d/03-seed.sql:ro

  # Redis 缓存
  redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"            # Redis 端口
    volumes:
      - redis-data:/data
```

---

### 4.4 `nginx/nginx.conf` 说明

```nginx
# 路由规则
location /api/ {
    proxy_pass http://java-backend:9000;    # Java API
}

location /agent/ {
    proxy_pass http://agent-service:8000;   # Python Agent
}

location /health {
    proxy_pass http://agent-service:8000/health;  # 健康检查
}

location / {
    root /usr/share/nginx/html;             # Vue 前端
    try_files $uri $uri/ /index.html;
}
```

---

## 5. 部署步骤

### 5.1 克隆项目

```bash
git clone <repository_url>
cd ouragent
```

### 5.2 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置文件
# Windows: notepad .env
# Linux/Mac: vim .env 或 nano .env
```

**必须修改**：
1. `MYSQL_ROOT_PASSWORD` - 设置 MySQL 密码
2. `DB_PASSWORD` - 与上面相同
3. `SECRET_KEY` - 随机字符串
4. `JWT_SECRET` - 随机字符串
5. `LLM_API_KEY` - LLM API Key
6. `EMBEDDING_API_KEY` - Embedding API Key

### 5.3 构建前端（可选）

如果需要前端页面：

```bash
cd frontend
npm install
npm run build
cd ..
```

### 5.4 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看启动日志
docker-compose logs -f

# 检查服务状态
docker-compose ps
```

### 5.5 验证服务

```bash
# 检查 Agent 服务
curl http://localhost:8001/health

# 检查 Java 服务
curl -X POST http://localhost:9001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 检查 Nginx
curl http://localhost:8080
```

---

## 6. 常用命令

### 服务管理

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 重启单个服务
docker-compose restart agent-service

# 查看日志
docker-compose logs -f
docker-compose logs -f agent-service

# 查看服务状态
docker-compose ps
```

### 重新构建

```bash
# 重新构建所有服务
docker-compose build

# 重新构建单个服务
docker-compose build --no-cache agent-service

# 重建并启动
docker-compose up -d --build
```

### 数据管理

```bash
# 进入容器
docker-compose exec agent-service bash
docker-compose exec mysql mysql -uroot -p

# 导出数据库
docker-compose exec mysql mysqldump -uroot -p edu_agent > backup.sql

# 导入数据库
docker-compose exec -T mysql mysql -uroot -p edu_agent < backup.sql
```

### 向量库管理

```bash
# 进入 Agent 容器
docker-compose exec agent-service bash

# 查看向量库状态
python -c "from src.core.rag import VectorStore; vs = VectorStore(); vs.load('data/vector_store.json'); print(f'文档数: {vs.count()}')"

# 重新导入数据
python import_education_data.py --source local --provider api
```

---

## 7. 端口汇总

| 服务 | 容器内端口 | 宿主机端口 | 说明 |
|------|-----------|-----------|------|
| Nginx | 80 | 8080 | 前端访问 |
| Java Backend | 9000 | 9001 | Java API |
| Agent Service | 8000 | 8001 | Python API |
| MySQL | 3306 | 3308 | 数据库 |
| Redis | 6379 | 6380 | 缓存 |

---

## 8. API 接口

### Agent Service (http://localhost:8001)

```
GET  /health                    - 健康检查
GET  /agent/status              - Agent 状态
POST /agent/chat                - 对话
POST /agent/chat/stream         - 流式对话
POST /agent/analyze             - 学生画像分析
POST /agent/plan                - 生成学习路径
POST /agent/generate            - 生成教学资源
POST /agent/evaluate            - 评估学生答案
POST /agent/knowledge/ingest    - 知识文档入库
GET  /agent/knowledge/status    - 知识库状态
```

### Java Backend (http://localhost:9001)

```
POST /api/auth/register         - 用户注册
POST /api/auth/login            - 用户登录
GET  /api/users/me              - 当前用户信息
GET  /api/courses               - 课程列表
POST /api/chat/sessions         - 创建对话会话
POST /api/chat/sessions/{id}/messages - 发送消息
GET  /api/knowledge             - 知识库列表
POST /api/knowledge/upload      - 上传知识文档
```

---

## 9. 故障排查

### 服务启动失败

```bash
# 查看详细日志
docker-compose logs agent-service

# 检查健康状态
docker-compose ps

# 重建服务
docker-compose down
docker-compose build --no-cache agent-service
docker-compose up -d
```

### 数据库连接失败

```bash
# 检查 MySQL 状态
docker-compose logs mysql

# 进入 MySQL 检查
docker-compose exec mysql mysql -uroot -p

# 检查密码配置
grep MYSQL_ROOT_PASSWORD .env
```

### LLM 调用失败

```bash
# 检查 API Key 配置
docker-compose exec agent-service env | grep LLM

# 测试 API 连通性
curl -H "Authorization: Bearer your_api_key" \
  https://api.siliconflow.cn/v1/models
```

### 向量库检索无结果

```bash
# 检查向量库状态
docker-compose exec agent-service python -c "
from config.settings import settings
print('Embedding API:', settings.EMBEDDING_BASE_URL)
print('Model:', settings.EMBEDDING_MODEL)
"

# 重新导入数据
docker-compose exec agent-service python import_education_data.py --source local --provider api
```

---

## 10. 生产环境建议

### 安全配置

1. **修改所有默认密码**
2. **使用强随机字符串**作为 SECRET_KEY 和 JWT_SECRET
3. **限制 CORS_ORIGINS** 为实际域名
4. **启用 HTTPS**（修改 nginx.conf）

### 性能优化

1. **增加 MySQL 连接池**：`DB_POOL_SIZE=20`
2. **增加 Redis 内存**：在 docker-compose.yml 添加 `command: redis-server --maxmemory 256mb`
3. **启用 Nginx 缓存**

### 备份策略

```bash
# 定期备份数据库
docker-compose exec mysql mysqldump -uroot -p edu_agent > backup_$(date +%Y%m%d).sql

# 备份向量库
docker cp agent-service:/app/data/vector_store.json ./backup/
```

---

## 11. 快速启动（一键命令）

```bash
# 1. 配置环境变量
cat > .env << 'EOF'
MYSQL_ROOT_PASSWORD=your_password
DB_PASSWORD=your_password
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)
LLM_API_KEY=your_llm_key
EMBEDDING_API_KEY=your_embedding_key
EOF

# 2. 启动服务
docker-compose up -d

# 3. 等待服务就绪
sleep 30

# 4. 验证
curl http://localhost:8001/health
```

---

## 12. 联系与支持

如有问题，请检查：
1. `.env` 配置是否正确
2. API Key 是否有效
3. 端口是否被占用
4. Docker 日志中的错误信息

---

*文档版本: 1.0*
*更新日期: 2026-06-15*
