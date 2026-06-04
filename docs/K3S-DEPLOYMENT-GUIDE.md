# K3s 部署完全指南

> 从零开始理解 Docker + K3s 部署的完整机理

---

## 一、核心概念速查表

| 组件 | 是什么 | 干什么 | 类比 |
|------|--------|--------|------|
| **Docker** | 容器运行时 | 把应用打包成标准化的"集装箱" |  shipping container |
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
# docker-compose.yml 结构
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

**核心概念：**
- **services** - 你要运行的服务（容器）
- **volumes** - 持久化数据，容器删了数据还在
- **networks** - 服务间通信的网络

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

#### Pod - 最小部署单位
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app
spec:
  containers:
    - name: app
      image: my-app:latest
      ports:
        - containerPort: 8000
```

#### Deployment - 管理 Pod 副本
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3              # 3个副本
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
          resources:        # 资源限制
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "200m"
          livenessProbe:    # 存活检查
            httpGet:
              path: /health
              port: 8000
          readinessProbe:   # 就绪检查
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
    app: my-app            # 选择带有 app=my-app 标签的 Pod
  ports:
    - port: 80             # Service 端口
      targetPort: 8000     # Pod 端口
  type: ClusterIP          # 类型：ClusterIP/NodePort/LoadBalancer
```

**Service 类型：**
- `ClusterIP` - 集群内部访问（默认）
- `NodePort` - 通过节点端口外部访问
- `LoadBalancer` - 云厂商负载均衡器

#### ConfigMap 和 Secret
```yaml
# ConfigMap - 非敏感配置
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_ENV: production
  LOG_LEVEL: INFO

---
# Secret - 敏感配置
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
stringData:
  DB_PASSWORD: my-password
  API_KEY: my-api-key
```

**在 Pod 中使用：**
```yaml
spec:
  containers:
    - name: app
      envFrom:
        - configMapRef:
            name: app-config
        - secretRef:
            name: app-secrets
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

**在 Pod 中使用：**
```yaml
spec:
  containers:
    - name: app
      volumeMounts:
        - name: data
          mountPath: /app/data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: my-pvc
```

#### Namespace - 命名空间隔离
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: my-project
```

---

## 四、完整部署流程

### 4.1 部署前准备

```
1. 编写 Dockerfile
   ↓
2. 编写 docker-compose.yml（本地测试）
   ↓
3. 本地测试通过
   ↓
4. 编写 K8s YAML 文件
   ↓
5. 构建 Docker 镜像
   ↓
6. 部署到 K3s 集群
   ↓
7. 验证服务
```

### 4.2 K8s YAML 文件结构

一个完整的项目通常需要这些文件：

```
k8s/
├── namespace.yaml      # 命名空间
├── configmap.yaml      # 配置
├── secrets.yaml        # 密钥（加入 .gitignore）
├── mysql.yaml          # 数据库
├── postgres.yaml       # 数据库
├── redis.yaml          # 缓存
├── app-service.yaml    # 应用服务
├── nginx.yaml          # 反向代理
└── deploy.sh           # 部署脚本
```

### 4.3 部署顺序（有依赖关系）

```
1. Namespace          ← 最先创建
2. ConfigMap + Secret ← 配置和密钥
3. PVC                ← 存储声明
4. Database (MySQL/PostgreSQL/Redis) ← 先启动基础设施
5. App Service        ← 等数据库就绪后再启动
6. Nginx/Ingress      ← 最后启动代理
```

### 4.4 部署命令流程

```bash
# 1. 创建命名空间
kubectl apply -f namespace.yaml

# 2. 创建配置和密钥
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml

# 3. 创建存储声明
kubectl apply -f mysql.yaml    # 包含 PVC
kubectl apply -f postgres.yaml
kubectl apply -f redis.yaml

# 4. 等待数据库就绪
kubectl wait --for=condition=ready pod -l app=mysql -n my-namespace --timeout=120s

# 5. 部署应用
kubectl apply -f app-service.yaml
kubectl apply -f nginx.yaml

# 6. 查看状态
kubectl get pods -n my-namespace
kubectl get svc -n my-namespace
```

---

## 五、常用 kubectl 命令

```bash
# ========== 查看资源 ==========
kubectl get pods                    # 查看 Pod
kubectl get pods -n namespace       # 指定命名空间
kubectl get pods -o wide            # 详细信息
kubectl get svc                     # 查看 Service
kubectl get deployments             # 查看 Deployment
kubectl get pvc                     # 查看存储声明
kubectl get nodes                   # 查看节点

# ========== 查看详情 ==========
kubectl describe pod pod-name       # Pod 详情
kubectl describe svc svc-name       # Service 详情

# ========== 查看日志 ==========
kubectl logs pod-name               # 查看日志
kubectl logs -f pod-name            # 实时日志
kubectl logs -l app=my-app          # 按标签查看

# ========== 进入容器 ==========
kubectl exec -it pod-name -- bash

# ========== 删除资源 ==========
kubectl delete pod pod-name
kubectl delete -f file.yaml
kubectl delete namespace ns-name    # 删除整个命名空间

# ========== 应用配置 ==========
kubectl apply -f file.yaml          # 创建或更新
kubectl apply -f directory/         # 应用目录下所有 yaml

# ========== 调试 ==========
kubectl get events                  # 查看事件
kubectl top pods                    # 查看资源使用
```

---

## 六、配置文件模板

### 6.1 完整的项目 K8s 配置示例

```yaml
# ========== namespace.yaml ==========
apiVersion: v1
kind: Namespace
metadata:
  name: my-project

---
# ========== configmap.yaml ==========
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: my-project
data:
  APP_ENV: production
  DB_HOST: mysql
  REDIS_HOST: redis

---
# ========== secrets.yaml ==========
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: my-project
type: Opaque
stringData:
  DB_PASSWORD: your-password-here
  JWT_SECRET: your-jwt-secret-here

---
# ========== mysql.yaml ==========
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql
  namespace: my-project
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
        - name: mysql
          image: mysql:8.0
          ports:
            - containerPort: 3306
          env:
            - name: MYSQL_ROOT_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: app-secrets
                  key: DB_PASSWORD
          volumeMounts:
            - name: mysql-data
              mountPath: /var/lib/mysql
          readinessProbe:
            exec:
              command: ["mysqladmin", "ping", "-h", "localhost"]
            initialDelaySeconds: 30
            periodSeconds: 10
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
      volumes:
        - name: mysql-data
          persistentVolumeClaim:
            claimName: mysql-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: mysql
  namespace: my-project
spec:
  selector:
    app: mysql
  ports:
    - port: 3306
      targetPort: 3306
  type: ClusterIP

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-pvc
  namespace: my-project
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi

---
# ========== app.yaml ==========
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  namespace: my-project
spec:
  replicas: 2
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
          imagePullPolicy: Never   # 使用本地镜像
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef:
                name: app-config
            - secretRef:
                name: app-secrets
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "200m"

---
apiVersion: v1
kind: Service
metadata:
  name: my-app
  namespace: my-project
spec:
  selector:
    app: my-app
  ports:
    - port: 8000
      targetPort: 8000
  type: ClusterIP

---
# ========== ingress.yaml (可选) ==========
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app-ingress
  namespace: my-project
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
    - host: myapp.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: my-app
                port:
                  number: 8000
```

---

## 七、.gitignore 模板

```gitignore
# ========== IDE ==========
.idea/
*.iml
.vscode/
*.swp

# ========== OS ==========
.DS_Store
Thumbs.db
desktop.ini

# ========== Python ==========
__pycache__/
*.pyc
*.pyo
.venv/
venv/
*.egg-info/
dist/
build/

# ========== Java ==========
*.class
*.jar
*.war
target/
.gradle/

# ========== Environment ==========
.env
.env.local
.env.production

# ========== Logs ==========
*.log
logs/

# ========== Docker local overrides ==========
docker-compose.override.yml

# ========== K8s secrets (contains sensitive data) ==========
k8s/secrets.yaml

# ========== Claude Code ==========
.claude/
```

---

## 八、部署检查清单

### 部署前

- [ ] Dockerfile 编写完成
- [ ] docker-compose.yml 本地测试通过
- [ ] K8s YAML 文件编写完成
- [ ] secrets.yaml 已加入 .gitignore
- [ ] 镜像已构建

### 部署中

- [ ] 命名空间已创建
- [ ] ConfigMap 和 Secret 已创建
- [ ] PVC 已创建
- [ ] 数据库服务已启动并就绪
- [ ] 应用服务已启动
- [ ] Ingress/代理已配置

### 部署后

- [ ] Pod 状态正常 (Running)
- [ ] Service 可访问
- [ ] 健康检查通过
- [ ] 日志无报错
- [ ] 数据持久化正常

---

## 九、常见问题排查

### Pod 状态异常

```bash
# 查看 Pod 详情
kubectl describe pod pod-name -n namespace

# 查看日志
kubectl logs pod-name -n namespace

# 常见状态：
# Pending     - 资源不足或调度失败
# CrashLoopBackOff - 应用启动失败
# ImagePullBackOff - 镜像拉取失败
# OOMKilled   - 内存不足
```

### 服务无法访问

```bash
# 检查 Service
kubectl get svc -n namespace
kubectl describe svc svc-name -n namespace

# 检查 Endpoints
kubectl get endpoints svc-name -n namespace

# 测试连通性
kubectl run test --image=busybox -it --rm -- wget -qO- http://svc-name:port
```

### 存储问题

```bash
# 检查 PVC 状态
kubectl get pvc -n namespace

# 检查 PV
kubectl get pv
```

---

## 十、部署脚本模板

```bash
#!/bin/bash
# deploy.sh - K8s 部署脚本

set -e

NAMESPACE="my-project"
K8S_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== 1. 构建镜像 ==="
docker build -t my-app:latest .

echo "=== 2. 创建命名空间 ==="
kubectl apply -f $K8S_DIR/namespace.yaml

echo "=== 3. 创建配置 ==="
kubectl apply -f $K8S_DIR/configmap.yaml
kubectl apply -f $K8S_DIR/secrets.yaml

echo "=== 4. 部署数据库 ==="
kubectl apply -f $K8S_DIR/mysql.yaml
echo "等待数据库就绪..."
kubectl wait --for=condition=ready pod -l app=mysql -n $NAMESPACE --timeout=120s

echo "=== 5. 部署应用 ==="
kubectl apply -f $K8S_DIR/app.yaml
kubectl wait --for=condition=ready pod -l app=my-app -n $NAMESPACE --timeout=120s

echo "=== 部署完成 ==="
kubectl get pods -n $NAMESPACE
kubectl get svc -n $NAMESPACE
```

---

## 十一、关键理解

### Docker vs K8s

```
Docker 解决：怎么打包应用
K8s 解决：怎么管理大量容器

类比：
- Docker = 标准化集装箱
- K8s = 港口管理系统
```

### 声明式 vs 命令式

```bash
# 命令式（告诉系统做什么）
docker run -d -p 80:80 nginx

# 声明式（告诉系统要什么状态）
# K8s YAML: 我要 3 个 nginx 副本
spec:
  replicas: 3
```

### K8s 核心逻辑

```
期望状态 → 控制器 → 实际状态
    ↑                  ↓
    └──── 不断对齐 ────┘
```

你告诉 K8s "我要 3 个 Pod"，K8s 会：
1. 如果只有 2 个 → 创建 1 个
2. 如果有 4 个 → 删除 1 个
3. 如果某个挂了 → 自动重启

---

## 十二、学习路径建议

```
1. 先掌握 Docker
   ├── Dockerfile 编写
   ├── docker build/run
   └── docker-compose.yml

2. 再学 K8s 基础
   ├── Pod、Deployment、Service
   ├── ConfigMap、Secret
   └── kubectl 命令

3. 实践部署
   ├── 本地 K3s/Docker Desktop K8s
   ├── 简单应用部署
   └── 多服务编排

4. 进阶
   ├── Ingress 配置
   ├── Helm 包管理
   ├── CI/CD 集成
   └── 监控和日志
```

---

*最后更新：2026-06-04*
