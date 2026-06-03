# K3s 部署指南

## 架构概览

```
Internet → Ingress (Traefik) → agent-service:8000
                                    ├── redis-service:6379 (缓存)
                                    └── postgres-service:5432 (数据库)
```

三个服务的 Deployment、Service、PVC 全部定义在 `deployment.yaml` 中，用 `---` 分隔。`ingress.yaml` 负责外部访问入口。

---

## deployment.yaml 逐段讲解

### 1. agent-service (Deployment + Service)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-service          # Deployment 名称，在集群内唯一
  labels:
    app: agent-service         # 标签，用于筛选和关联
spec:
  replicas: 1                  # 副本数，1 表示只跑一个 Pod
  selector:
    matchLabels:
      app: agent-service       # 选择器：Deployment 通过这个 label 管理 Pod
  template:                    # Pod 模板
    spec:
      containers:
      - name: agent-service
        image: agent-service:latest   # 镜像名，本地构建后 k3s 可直接用
        ports:
        - containerPort: 8000         # 容器监听端口
        env:                          # 环境变量注入
        - name: APP_ENV
          value: "production"
        - name: DEBUG
          value: "false"
        - name: LOG_LEVEL
          value: "INFO"
        - name: PORT
          value: "8000"
        - name: REDIS_HOST
          value: "redis-service"      # 指向 Redis 的 Service 名称（集群内 DNS）
        - name: REDIS_PORT
          value: "6379"
        - name: DB_HOST
          value: "postgres-service"   # 指向 Postgres 的 Service 名称
        - name: DB_PORT
          value: "5432"
        - name: DB_NAME
          value: "agent_db"
        - name: DB_USER
          value: "agent"
        - name: DB_PASSWORD
          value: "agent_password"     # ⚠️ 明文密码，生产环境应改用 Secret
        resources:                    # 资源配额
          requests:
            memory: "256Mi"           # Pod 启动时申请的最低内存
            cpu: "250m"               # 0.25 核
          limits:
            memory: "512Mi"           # 内存上限，超出会被 OOMKill
            cpu: "500m"               # 0.5 核上限
        livenessProbe:                # 存活探针：失败则重启容器
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10     # 启动后等 10 秒再开始探测
          periodSeconds: 30           # 每 30 秒探测一次
        readinessProbe:               # 就绪探针：失败则从 Service 摘除
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```

**Service 部分：**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: agent-service          # 集群内 DNS 名：agent-service.<namespace>.svc.cluster.local
spec:
  selector:
    app: agent-service         # 把流量转发给带此 label 的 Pod
  ports:
  - port: 8000                 # Service 监听端口
    targetPort: 8000           # 转发到 Pod 的端口
  type: ClusterIP              # 仅集群内可访问（不暴露到节点）
```

### 2. Redis (Deployment + Service + PVC)

```yaml
# Deployment
image: redis:7-alpine          # 官方 Redis 镜像
volumeMounts:
- name: redis-data
  mountPath: /data             # Redis 持久化数据目录
volumes:
- name: redis-data
  persistentVolumeClaim:
    claimName: redis-pvc       # 绑定 PVC，数据不会随 Pod 重建丢失

# Service
name: redis-service            # agent-service 通过这个名称连接 Redis

# PVC
accessModes: [ReadWriteOnce]   # 单节点读写（k3s 默认 local-path 支持）
storage: 1Gi                   # 申请 1GB 存储
```

### 3. PostgreSQL (Deployment + Service + PVC)

```yaml
# Deployment
image: postgres:15-alpine
env:
- name: POSTGRES_DB            # 自动创建的数据库名
- name: POSTGRES_USER          # 自动创建的用户名
- name: POSTGRES_PASSWORD      # 对应用户的密码
volumeMounts:
- name: postgres-data
  mountPath: /var/lib/postgresql/data   # PG 数据目录

# PVC
storage: 10Gi                  # 申请 10GB 存储
```

---

## ingress.yaml 讲解

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: agent-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /    # URL 重写规则
    nginx.ingress.kubernetes.io/proxy-body-size: "50m" # 请求体上限 50MB
spec:
  rules:
  - host: agent.example.com    # 域名匹配
    http:
      paths:
      - path: /
        pathType: Prefix       # 前缀匹配
        backend:
          service:
            name: agent-service
            port:
              number: 8000
```

> **注意**：k3s 默认的 Ingress Controller 是 **Traefik**，不是 nginx。这个 YAML 的 annotations 写的是 nginx ingress 的配置，在 Traefik 下会被忽略但不会报错。如果需要精确控制，应改用 Traefik 的 annotations（见下方问题说明）。

---

## YAML 完整性检查

### 已覆盖的部分

| 组件 | Deployment | Service | PVC | Ingress |
|------|-----------|---------|-----|---------|
| agent-service | ✅ | ✅ | 不需要 | ✅ |
| Redis | ✅ | ✅ | ✅ | 不需要 |
| PostgreSQL | ✅ | ✅ | ✅ | 不需要 |

**结论：三个服务的 YAML 都已包含，不需要额外文件。** 所有定义集中在两个文件里即可。

### 存在的问题

| # | 问题 | 严重程度 | 说明 |
|---|------|---------|------|
| 1 | **数据库密码明文** | 🔴 高 | `DB_PASSWORD` 和 `POSTGRES_PASSWORD` 硬编码在 YAML 里。生产环境应改用 `Secret` |
| 2 | **Ingress annotations 不匹配** | 🟡 中 | k3s 默认用 Traefik，`nginx.ingress.kubernetes.io/*` 注解无效 |
| 3 | **缺少 namespace 定义** | 🟡 中 | 所有资源会部署到 default namespace，建议加 `namespace: agent` |
| 4 | **镜像拉取策略** | 🟡 中 | 本地构建的镜像需设置 `imagePullPolicy: IfNotPresent`，否则 k8s 会尝试从远程仓库拉取 |
| 5 | **Dockerfile 有拼写错误** | 🔴 高 | `-a_no-cache-dir` 应为 `--no-cache-dir`，`HEALTHCHECK -a_interval` 应为 `--interval` |
| 6 | **副本数为 1** | 🟢 低 | 开发环境没问题，生产环境 redis 和 postgres 建议配合 StatefulSet |

### 建议修复

**1. 用 Secret 存密码（推荐）：**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
stringData:
  DB_PASSWORD: "your-secure-password"
  POSTGRES_PASSWORD: "your-secure-password"
```
然后在 Deployment 中引用：
```yaml
env:
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: db-credentials
      key: DB_PASSWORD
```

**2. 修复 Ingress annotations（如果用 Traefik）：**
```yaml
annotations:
  traefik.ingress.kubernetes.io/router.entrypoints: web
  traefik.ingress.kubernetes.io/router.middlewares: default-redirect-https@kubernetescrd
```

**3. 添加 imagePullPolicy：**
```yaml
containers:
- name: agent-service
  image: agent-service:latest
  imagePullPolicy: IfNotPresent    # 本地构建的镜像用这个
```

---

## 完整部署流程

### 前置条件

- k3s 已安装并运行
- Docker 已安装
- `kubectl` 可正常连接集群

### Step 0：修复 Dockerfile 中的拼写错误

Dockerfile 第 13 行和第 38 行有拼写错误，先修复：

```bash
# 第 13 行：-a_no-cache-dir → --no-cache-dir
# 第 38 行：-a_interval → --interval
```

### Step 1：构建 Docker 镜像

```bash
# 在项目根目录执行
docker build -t agent-service:latest .
```

> 如果 k3s 使用 containerd 而非 Docker，需要将镜像导入 k3s：
> ```bash
> docker save agent-service:latest | sudo k3s ctr images import -
> ```

### Step 2：（可选）创建命名空间

```bash
kubectl create namespace agent
```

如果使用命名空间，所有 kubectl 命令加 `-n agent`，或切换默认命名空间：
```bash
kubectl config set-context --current --namespace=agent
```

### Step 3：（可选）创建 Secret

```bash
kubectl create secret generic db-credentials \
  --from-literal=DB_PASSWORD='your-secure-password' \
  --from-literal=POSTGRES_PASSWORD='your-secure-password'
```

### Step 4：部署所有资源

```bash
kubectl apply -f k8s/deployment.yaml
```

### Step 5：部署 Ingress

```bash
kubectl apply -f k8s/ingress.yaml
```

### Step 6：验证部署

```bash
# 查看 Pod 状态（等待全部 Running）
kubectl get pods -w

# 查看 Service
kubectl get svc

# 查看 PVC 绑定状态
kubectl get pvc

# 查看 Ingress
kubectl get ingress

# 查看 Pod 日志
kubectl logs -l app=agent-service --tail=50
```

### Step 7：访问服务

**方式一：端口转发（推荐开发调试）**
```bash
kubectl port-forward service/agent-service 8000:8000
# 访问 http://localhost:8000
```

**方式二：NodePort（临时暴露到节点 IP）**
```bash
kubectl patch service agent-service -p '{"spec":{"type":"NodePort"}}'
kubectl get service agent-service   # 查看分配的 NodePort
# 访问 http://<节点IP>:<NodePort>
```

**方式三：Ingress（需要配置 DNS）**
```bash
# 查看 Ingress Controller 的外部 IP
kubectl get svc -n kube-system traefik
# 将 agent.example.com DNS 解析到该 IP
# 访问 http://agent.example.com
```

### 清理

```bash
kubectl delete -f k8s/ingress.yaml
kubectl delete -f k8s/deployment.yaml
# 如果创建了命名空间
kubectl delete namespace agent
```
