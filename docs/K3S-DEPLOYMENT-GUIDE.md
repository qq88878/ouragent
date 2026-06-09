# K3s 部署完全指南

> 从零开始理解 Docker + K3s 部署的完整机理

---

## 一、核心概念速查表

| 组件 | 是什么 | 干什么 | 类比 |
|------|--------|--------|------|
| **Docker** | 容器运行时 | 把应用打包成标准化的"集装箱" | shipping container |
| **Dockerfile** | 构建配方 | 告诉 Docker 怎么打包应用 | 菜谱 |
| **Docker Compose** | 本地编排工具 | 一键启动多个容器 | 乐团指挥 |
| **Kubernetes (K8s)** | 容器编排平台 | 管理大量容器的调度、扩缩、自愈 | 交通指挥中心 |
| **K3s** | 轻量 K8s | 资源占用更少的 K8s 发行版 | 迷你指挥中心 |
| **kubectl** | K8s 命令行工具 | 和 K8s 集群对话 | 翻译官 |
| **Pod** | K8s 最小单位 | 包含一个或多个容器 | 一间宿舍 |
| **Deployment** | 部署控制器 | 管理 Pod 的副本数和更新 | 宿管 |
| **Service** | 服务发现/负载均衡 | 让 Pod 之间能互相访问 | 电话簿 |
| **Ingress** | 入口控制器 | 管理外部访问（域名/路径路由） | 前台接待 |
| **ConfigMap** | 配置存储 | 存放非敏感配置 | 公告栏 |
| **Secret** | 密钥存储 | 存放密码、证书等敏感信息 | 保险箱 |
| **PersistentVolume (PV)** | 持久化存储 | 容器重启后数据不丢失 | 硬盘 |
| **PersistentVolumeClaim (PVC)** | 存储申请 | Pod 申请使用多少存储 | 租房合同 |
| **Namespace** | 命名空间 | 隔离不同项目/环境 | 楼层 |

---

## 二、Docker 基础

### 2.1 Dockerfile 详解

```dockerfile
# 基础镜像（相当于操作系统 + 预装软件）
FROM python:3.11-slim

# 工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install -r requirements.txt

# 复制源代码
COPY src/ ./src/

# 环境变量
ENV APP_ENV=production

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

**关键指令：**
- `FROM` - 基础镜像
- `COPY` - 复制文件到容器
- `RUN` - 构建时执行命令
- `ENV` - 设置环境变量
- `EXPOSE` - 声明端口（文档作用）
- `CMD` - 容器启动时执行的命令

### 2.2 Docker Compose 详解

```yaml
services:          # 服务列表
  web:             # 服务名
    image: nginx   # 使用的镜像
    ports:         # 端口映射
      - "80:80"
    volumes:       # 数据卷
      - ./data:/data
    environment:   # 环境变量
      - ENV=prod
    depends_on:    # 依赖关系
      - db
  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: password

volumes:           # 卷定义
  db-data:
networks:          # 网络定义
  app-network:
```

### 2.3 Docker 常用命令

```bash
# 构建镜像
docker build -t 镜像名:标签 .

# 运行容器
docker run -d -p 8000:8000 --name 容器名 镜像名

# 查看容器
docker ps              # 运行中
docker ps -a           # 所有

# 查看日志
docker logs -f 容器名

# 进入容器
docker exec -it 容器名 bash

# 停止/删除
docker stop 容器名
docker rm 容器名

# Docker Compose 命令
docker-compose up -d        # 启动（后台）
docker-compose down         # 停止
docker-compose ps           # 查看状态
docker-compose logs -f      # 查看日志
docker-compose build        # 构建镜像
```

---

## 三、Kubernetes (K3s) 基础

### 3.1 K8s 架构

```
┌─────────────────────────────────────────────────────────┐
│                    K8s 集群                              │
├─────────────────────────────────────────────────────────┤
│  Master Node (控制节点)                                  │
│  ├── API Server    - 接收命令的入口                       │
│  ├── Scheduler     - 决定 Pod 跑在哪个节点                │
│  ├── Controller    - 确保实际状态=期望状态                 │
│  └── etcd          - 存储集群状态的数据库                  │
├─────────────────────────────────────────────────────────┤
│  Worker Node (工作节点)                                  │
│  ├── kubelet       - 管理本节点的容器                     │
│  ├── kube-proxy    - 网络代理                            │
│  └── Pod           - 运行你的应用                         │
└─────────────────────────────────────────────────────────┘
```

### 3.2 K8s 核心资源

#### Deployment - 管理 Pod 副本
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: app
          image: my-app:latest
          ports:
            - containerPort: 8000
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "200m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
```

#### Service - 服务发现和负载均衡
```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app-svc
spec:
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 8000
  type: ClusterIP  # ClusterIP / NodePort / LoadBalancer
```

#### ConfigMap 和 Secret
```yaml
# ConfigMap - 非敏感配置
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_ENV: production
  DB_HOST: mysql

---
# Secret - 敏感配置
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
stringData:
  DB_PASSWORD: my-password
```

#### PersistentVolumeClaim - 持久化存储
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

---

## 四、本项目 K8s 配置

### 4.1 文件结构

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

### 4.2 服务架构

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

### 4.3 快速部署

```bash
# 1. 构建镜像
docker build -t ouragent-agent-service:latest -f Dockerfile .
docker build -t ouragent-java-backend:latest -f javaarea/Dockerfile javaarea

# 2. 创建 secrets.yaml (从 secrets.yaml.example 复制)
cp k8s/secrets.yaml.example k8s/secrets.yaml

# 3. 部署
cd k8s && chmod +x deploy.sh && ./deploy.sh

# 4. 访问 http://localhost:30080
```

### 4.4 部署顺序（有依赖关系）

```
1. Namespace          <- 最先创建
2. ConfigMap + Secret <- 配置和密钥
3. PVC                <- 存储声明
4. Database (MySQL/PostgreSQL/Redis) <- 先启动基础设施
5. App Service        <- 等数据库就绪后再启动
6. Nginx/Ingress      <- 最后启动代理
```

### 4.5 环境变量

**ConfigMap (非敏感):** APP_ENV, DEBUG, LOG_LEVEL, PORT, DB_HOST, DB_PORT, DB_NAME, DB_USER, REDIS_HOST, REDIS_PORT, SPRING_PROFILES_ACTIVE, JAVA_OPTS

**Secret (敏感):** MYSQL_ROOT_PASSWORD, MYSQL_PASSWORD, POSTGRES_PASSWORD, JWT_SECRET

### 4.6 存储

| PVC | 用途 | 大小 |
|-----|------|------|
| mysql-pvc | MySQL 数据 | 5Gi |
| postgres-pvc | PostgreSQL 数据 | 5Gi |
| redis-pvc | Redis 数据 | 1Gi |
| agent-uploads-pvc | Agent 上传文件 | 2Gi |

### 4.7 健康检查

| 服务 | 检查路径 | 初始延迟 |
|------|----------|----------|
| agent-service | /health | 15s |
| java-backend | /api/auth/me | 40s |
| mysql | mysqladmin ping | 30s |
| postgres | pg_isready | 15s |
| redis | redis-cli ping | 5s |
| nginx | /health | 5s |

### 4.8 资源限制

| 服务 | CPU Request | CPU Limit | Memory Request | Memory Limit |
|------|-------------|-----------|----------------|--------------|
| agent-service | 250m | 500m | 256Mi | 512Mi |
| java-backend | 500m | 1000m | 512Mi | 1Gi |
| mysql | 250m | 500m | 256Mi | 512Mi |
| postgres | 100m | 250m | 128Mi | 256Mi |
| redis | 50m | 100m | 64Mi | 128Mi |
| nginx | 50m | 100m | 64Mi | 128Mi |

---

## 五、常用 kubectl 命令

```bash
# ========== 查看资源 ==========
kubectl get pods -n edu-agent         # 查看 Pod
kubectl get pods -o wide              # 详细信息
kubectl get svc -n edu-agent          # 查看 Service
kubectl get deployments -n edu-agent  # 查看 Deployment
kubectl get pvc -n edu-agent          # 查看存储声明
kubectl get nodes                     # 查看节点

# ========== 查看详情 ==========
kubectl describe pod pod-name -n edu-agent

# ========== 查看日志 ==========
kubectl logs -f deployment/agent-service -n edu-agent

# ========== 进入容器 ==========
kubectl exec -it deployment/agent-service -n edu-agent -- bash

# ========== 应用配置 ==========
kubectl apply -f file.yaml

# ========== 删除资源 ==========
kubectl delete -f file.yaml
kubectl delete namespace edu-agent    # 删除整个命名空间

# ========== 扩缩容 ==========
kubectl scale deployment/agent-service --replicas=3 -n edu-agent

# ========== 重启服务 ==========
kubectl rollout restart deployment/agent-service -n edu-agent

# ========== 调试 ==========
kubectl get events -n edu-agent --sort-by='.lastTimestamp'
kubectl top pods -n edu-agent
```

---

## 六、完整部署脚本模板

```bash
#!/bin/bash
# deploy.sh - K8s 部署脚本
set -e
NAMESPACE="edu-agent"
K8S_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== 1. 构建镜像 ==="
docker build -t ouragent-agent-service:latest -f Dockerfile ..
docker build -t ouragent-java-backend:latest -f javaarea/Dockerfile javaarea

echo "=== 2. 创建命名空间 ==="
kubectl apply -f $K8S_DIR/namespace.yaml

echo "=== 3. 创建配置 ==="
kubectl apply -f $K8S_DIR/configmap.yaml
kubectl apply -f $K8S_DIR/secrets.yaml

echo "=== 4. 部署数据库 ==="
kubectl apply -f $K8S_DIR/mysql.yaml
kubectl apply -f $K8S_DIR/postgres.yaml
kubectl apply -f $K8S_DIR/redis.yaml
echo "等待数据库就绪..."
kubectl wait --for=condition=ready pod -l app=mysql -n $NAMESPACE --timeout=120s

echo "=== 5. 部署应用 ==="
kubectl apply -f $K8S_DIR/agent-service.yaml
kubectl apply -f $K8S_DIR/java-backend.yaml
kubectl apply -f $K8S_DIR/nginx.yaml

echo "=== 部署完成 ==="
kubectl get pods -n $NAMESPACE
kubectl get svc -n $NAMESPACE
```

---

## 七、常见问题排查

### Pod 状态异常

```bash
kubectl describe pod pod-name -n edu-agent
kubectl logs pod-name -n edu-agent

# 常见状态：
# Pending     - 资源不足或调度失败
# CrashLoopBackOff - 应用启动失败
# ImagePullBackOff - 镜像拉取失败
# OOMKilled   - 内存不足
```

### 服务无法访问

```bash
kubectl get svc -n edu-agent
kubectl describe svc svc-name -n edu-agent
kubectl get endpoints svc-name -n edu-agent
```

### 存储问题

```bash
kubectl get pvc -n edu-agent
kubectl get pv
```

### 修改配置

1. 修改 `configmap.yaml` 或 `secrets.yaml`
2. `kubectl apply -f configmap.yaml`
3. `kubectl rollout restart deployment/<name> -n edu-agent`

---

## 八、.gitignore 记得加

```gitignore
k8s/secrets.yaml
docker-compose.override.yml
```

---

## 九、关键理解

### Docker vs K8s

```
Docker 解决：怎么打包应用
K8s 解决：怎么管理大量容器
```

### 声明式 vs 命令式

```bash
# 命令式
docker run -d -p 80:80 nginx

# 声明式 (K8s YAML)
spec:
  replicas: 3
```

### K8s 核心逻辑

```
期望状态 -> 控制器 -> 实际状态
    ^                  |
    +--- 不断对齐 -----+
```

---

*最后更新：2026-06-09*
