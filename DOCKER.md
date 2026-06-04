# Docker部署指南

## 项目架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │  Nginx  │───▶│ Java Backend│───▶│    MySQL    │          │
│  │  :80    │    │   :9000     │    │   :3306     │          │
│  └─────────┘    └─────────────┘    └─────────────┘          │
│       │                │                                    │
│       │                ▼                                    │
│       │         ┌─────────────┐    ┌─────────────┐          │
│       └────────▶│Python Agent │───▶│  PostgreSQL │          │
│                 │   :8000     │    │   :5432     │          │
│                 └─────────────┘    └─────────────┘          │
│                        │                                    │
│                        ▼                                    │
│                 ┌─────────────┐                              │
│                 │    Redis    │                              │
│                 │   :6379     │                              │
│                 └─────────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 环境准备

确保已安装：
- Docker Desktop (Windows/Mac) 或 Docker Engine (Linux)
- Docker Compose

### 2. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑.env文件，配置您的环境变量
# 主要配置项：
# - MYSQL_ROOT_PASSWORD: MySQL root密码
# - MYSQL_PASSWORD: 应用数据库密码
# - POSTGRES_PASSWORD: PostgreSQL密码
# - JWT_SECRET: JWT密钥（生产环境必须修改）
```

### 3. 启动服务

#### 开发环境
```bash
# Windows
docker-deploy.bat dev

# Linux/Mac
./docker-deploy.sh dev

# 或直接使用docker-compose
docker-compose up -d --build
```

#### 生产环境
```bash
# Windows
docker-deploy.bat prod

# Linux/Mac
./docker-deploy.sh prod

# 或直接使用docker-compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 4. 访问服务

| 服务 | 开发环境 | 生产环境 |
|------|----------|----------|
| Nginx代理 | http://localhost:80 | http://localhost:80 |
| Java后端 | http://localhost:9000 | 内部访问 |
| Python Agent | http://localhost:8000 | 内部访问 |
| MySQL | localhost:3306 | 内部访问 |
| PostgreSQL | localhost:5432 | 内部访问 |
| Redis | localhost:6379 | 内部访问 |

## 常用命令

### 服务管理

```bash
# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f java-backend
docker-compose logs -f agent-service

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 停止并删除所有数据
docker-compose down -v
```

### 开发调试

```bash
# 进入容器
docker-compose exec java-backend bash
docker-compose exec agent-service bash

# 查看容器资源使用
docker stats

# 查看网络
docker network ls
docker network inspect ouragent_edu-network
```

### 数据库操作

```bash
# 连接MySQL
docker-compose exec mysql mysql -u edu_agent -p edu_agent

# 连接PostgreSQL
docker-compose exec postgres psql -U agent -d agent_db

# 连接Redis
docker-compose exec redis redis-cli
```

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| MYSQL_ROOT_PASSWORD | MySQL root密码 | root_password |
| MYSQL_DATABASE | 应用数据库名 | edu_agent |
| MYSQL_USER | 应用数据库用户 | edu_agent |
| MYSQL_PASSWORD | 应用数据库密码 | edu_agent_password |
| POSTGRES_DB | PostgreSQL数据库名 | agent_db |
| POSTGRES_USER | PostgreSQL用户 | agent |
| POSTGRES_PASSWORD | PostgreSQL密码 | agent_password |
| REDIS_PASSWORD | Redis密码 | (空) |
| JWT_SECRET | JWT密钥 | change-this-in-production |
| SPRING_PROFILES_ACTIVE | Spring配置文件 | prod |
| APP_ENV | 应用环境 | production |
| DEBUG | 调试模式 | false |
| LOG_LEVEL | 日志级别 | INFO |

### 端口配置

| 服务 | 端口 | 说明 |
|------|------|------|
| Nginx | 80 | HTTP代理 |
| Java后端 | 9000 | Spring Boot应用 |
| Python Agent | 8000 | FastAPI应用 |
| MySQL | 3306 | 数据库 |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存 |

### 数据卷

| 卷名 | 说明 |
|------|------|
| mysql-data | MySQL数据持久化 |
| postgres-data | PostgreSQL数据持久化 |
| redis-data | Redis数据持久化 |
| agent-uploads | Agent上传文件 |

## 生产环境优化

### 资源限制

生产环境配置了资源限制：

```yaml
# Java后端
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M

# Python Agent
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.25'
      memory: 256M
```

### 日志配置

生产环境使用JSON日志格式：

```yaml
logging:
  driver: json-file
  options:
    max-size: "50m"
    max-file: "5"
```

### 健康检查

所有服务都配置了健康检查：

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  start_period: 15s
  retries: 3
```

## 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 检查端口占用
   netstat -ano | findstr :80
   # 修改docker-compose.yml中的端口映射
   ```

2. **数据库连接失败**
   ```bash
   # 检查数据库容器状态
   docker-compose ps
   # 查看数据库日志
   docker-compose logs mysql
   docker-compose logs postgres
   ```

3. **服务启动失败**
   ```bash
   # 查看服务日志
   docker-compose logs java-backend
   docker-compose logs agent-service
   ```

4. **磁盘空间不足**
   ```bash
   # 清理未使用的Docker资源
   docker system prune -af
   ```

### 重置环境

```bash
# 停止并删除所有容器和数据
docker-compose down -v

# 重新构建并启动
docker-compose up -d --build
```

## 安全建议

1. **修改默认密码**
   - 修改MySQL root密码
   - 修改应用数据库密码
   - 修改Redis密码（如果需要）

2. **生产环境配置**
   - 修改JWT密钥
   - 配置HTTPS
   - 限制数据库访问IP
   - 启用Redis密码认证

3. **网络安全**
   - 使用Docker网络隔离
   - 只暴露必要的端口
   - 配置防火墙规则

## 扩展部署

### 水平扩展

```bash
# 扩展Python Agent服务
docker-compose up -d --scale agent-service=3

# 扩展Java后端服务
docker-compose up -d --scale java-backend=2
```

### 负载均衡

Nginx配置了负载均衡：

```nginx
upstream agent_service {
    server agent-service:8000;
    # 添加更多实例
    # server agent-service-2:8000;
    # server agent-service-3:8000;
}
```

## 监控和日志

### 查看资源使用

```bash
# 查看容器资源使用
docker stats

# 查看特定容器资源
docker stats agent-service
```

### 日志管理

```bash
# 查看实时日志
docker-compose logs -f

# 查看历史日志
docker-compose logs --tail=100

# 导出日志
docker-compose logs > app.log
```

## 备份和恢复

### 数据库备份

```bash
# 备份MySQL
docker-compose exec mysql mysqldump -u root -p edu_agent > backup.sql

# 备份PostgreSQL
docker-compose exec postgres pg_dump -U agent agent_db > backup.sql
```

### 数据库恢复

```bash
# 恢复MySQL
docker-compose exec -T mysql mysql -u root -p edu_agent < backup.sql

# 恢复PostgreSQL
docker-compose exec -T postgres psql -U agent -d agent_db < backup.sql
```
