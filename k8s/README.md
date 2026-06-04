# K8s 配置使用指南

> 本项目 K8s 配置的完整使用说明

## 文件结构

```
k8s/
├── namespace.yaml        # 命名空间 (edu-agent)
├── configmap.yaml        # 非敏感配置
├── secrets.yaml          # 密钥配置 (已加入 .gitignore)
├── secrets.yaml.example  # 密钥配置示例
├── mysql.yaml            # MySQL 数据库
├── postgres.yaml         # PostgreSQL 数据库
├── redis.yaml            # Redis 缓存
├── agent-service.yaml    # Python Agent 服务
├── java-backend.yaml     # Java 后端服务
├── nginx.yaml            # Nginx 反向代理
├── deploy.sh             # 部署脚本
├── undeploy.sh           # 卸载脚本
└── status.sh             # 状态查看脚本
```

## 快速部署

```bash
# 1. 确保 Docker Desktop Kubernetes 已启用

# 2. 构建镜像
docker build -t ouragent-agent-service:latest -f Dockerfile .
docker build -t ouragent-java-backend:latest -f javaarea/Dockerfile javaarea

# 3. 创建 secrets.yaml (从 secrets.yaml.example 复制)
cp secrets.yaml.example secrets.yaml
# 编辑 secrets.yaml 修改密码

# 4. 部署
cd k8s
chmod +x deploy.sh
./deploy.sh

# 5. 访问
# http://localhost:30080
```

## 服务架构

```
                    ┌─────────────┐
                    │   Nginx     │ :30080 (NodePort)
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
    ┌─────────────────┐       ┌─────────────────┐
    │  Java Backend   │       │  Agent Service  │
    │     :9000       │       │     :8000       │
    └────────┬────────┘       └────────┬────────┘
             │                         │
    ┌────────┴────────┐       ┌────────┴────────┐
    │     MySQL       │       │   PostgreSQL    │
    │     :3306       │       │     :5432       │
    └─────────────────┘       └─────────────────┘
              │                         │
              └────────────┬────────────┘
                           │
                    ┌──────┴──────┐
                    │    Redis    │
                    │    :6379    │
                    └─────────────┘
```

## 命名空间

所有资源都在 `edu-agent` 命名空间中，使用 `-n edu-agent` 参数。

## 环境变量

### ConfigMap (非敏感)
- APP_ENV, DEBUG, LOG_LEVEL, PORT
- DB_HOST, DB_PORT, DB_NAME, DB_USER
- REDIS_HOST, REDIS_PORT
- SPRING_PROFILES_ACTIVE, JAVA_OPTS

### Secret (敏感)
- MYSQL_ROOT_PASSWORD, MYSQL_PASSWORD
- POSTGRES_PASSWORD
- JWT_SECRET

## 常用命令

```bash
# 查看所有资源
kubectl get all -n edu-agent

# 查看 Pod 状态
kubectl get pods -n edu-agent

# 查看服务
kubectl get svc -n edu-agent

# 查看日志
kubectl logs -f deployment/agent-service -n edu-agent
kubectl logs -f deployment/java-backend -n edu-agent

# 进入容器
kubectl exec -it deployment/agent-service -n edu-agent -- bash

# 查看配置
kubectl get configmap edu-config -n edu-agent -o yaml
kubectl get secret edu-secrets -n edu-agent -o yaml

# 重启服务
kubectl rollout restart deployment/agent-service -n edu-agent

# 扩缩容
kubectl scale deployment/agent-service --replicas=3 -n edu-agent
```

## 存储

| PVC | 用途 | 大小 |
|-----|------|------|
| mysql-pvc | MySQL 数据 | 5Gi |
| postgres-pvc | PostgreSQL 数据 | 5Gi |
| redis-pvc | Redis 数据 | 1Gi |
| agent-uploads-pvc | Agent 上传文件 | 2Gi |

## 健康检查

所有服务都配置了健康检查：

| 服务 | 检查路径 | 初始延迟 |
|------|----------|----------|
| agent-service | /health | 15s |
| java-backend | /api/auth/me | 40s |
| mysql | mysqladmin ping | 30s |
| postgres | pg_isready | 15s |
| redis | redis-cli ping | 5s |
| nginx | /health | 5s |

## 资源限制

| 服务 | CPU Request | CPU Limit | Memory Request | Memory Limit |
|------|-------------|-----------|----------------|--------------|
| agent-service | 250m | 500m | 256Mi | 512Mi |
| java-backend | 500m | 1000m | 512Mi | 1Gi |
| mysql | 250m | 500m | 256Mi | 512Mi |
| postgres | 100m | 250m | 128Mi | 256Mi |
| redis | 50m | 100m | 64Mi | 128Mi |
| nginx | 50m | 100m | 64Mi | 128Mi |

## 故障排查

```bash
# 1. 查看 Pod 事件
kubectl describe pod <pod-name> -n edu-agent

# 2. 查看日志
kubectl logs <pod-name> -n edu-agent

# 3. 查看集群事件
kubectl get events -n edu-agent --sort-by='.lastTimestamp'

# 4. 检查资源使用
kubectl top pods -n edu-agent
```

## 修改配置

1. 修改 `configmap.yaml` 或 `secrets.yaml`
2. 应用更改：`kubectl apply -f configmap.yaml`
3. 重启相关服务：`kubectl rollout restart deployment/<name> -n edu-agent`

## 清理

```bash
# 删除所有资源
kubectl delete namespace edu-agent

# 或使用脚本
./undeploy.sh
```
