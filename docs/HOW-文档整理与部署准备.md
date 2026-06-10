# How：文档整理与 Docker 部署准备过程

> 本文档记录了 Claude 是如何完成文档合并优化和 Docker 部署准备的，以及新手需要注意的坑。

---

## 一、文档整理做了什么

### 1.1 分析阶段

首先用命令扫描了项目里所有的 `.md` 文件：

```bash
find /d/ouragent -name "*.md" -type f
```

然后逐个读取每个文件的内容，对比它们之间的重叠部分。

### 1.2 发现的冗余问题

| 冗余文件 | 被谁覆盖了 | 具体重叠内容 |
|----------|-----------|-------------|
| `K8S-CHEATSHEET.md` | `K3S-DEPLOYMENT-GUIDE.md` | K8s 组件解释、kubectl 命令、YAML 模板都重复了 |
| `MICROSERVICE_ARCHITECTURE.md` | `PROJECT.md` + `JAVA_INTEGRATION_GUIDE.md` | 架构图、技术栈、通信方式、Docker Compose 配置全重复 |
| `k8s/README.md` | `K3S-DEPLOYMENT-GUIDE.md` | K8s 文件结构、部署命令、健康检查表重复 |
| `v3/docs/README.md` | 无（太简单） | 只有 3 行链接，没有实质内容 |

### 1.3 执行的命令

```bash
# 删除冗余文件
rm docs/K8S-CHEATSHEET.md
rm docs/MICROSERVICE_ARCHITECTURE.md
rm k8s/README.md
rm v3/docs/README.md
```

然后把被删文件中的**独有内容**合并到了保留的文件里。比如：
- K8S-CHEATSHEET 中的"一句话理解每个组件"表格 → 合并到 K3S-DEPLOYMENT-GUIDE
- k8s/README 中的项目 K8s 配置详情（PVC、资源限制、健康检查）→ 合并到 K3S-DEPLOYMENT-GUIDE

### 1.4 新建的文件

- `docs/README.md` — 文档索引，告诉用户每个文档是干什么的
- `CLAUDE.md` — 项目开发步骤指南，8 步实施计划

### 新手注意

- **先读后删**：删文件前一定要确认内容已经被其他文件覆盖，不能只看标题
- **git 记录**：删文件前最好先 commit 当前状态，万一删错了可以恢复
- **不要删错**：`rm` 命令没有回收站，删了就没了（Windows 上可以用 `del` 代替，会进回收站）

---

## 二、Docker 部署准备做了什么

### 2.1 发现的问题

打开 Dockerfile 和 docker-compose.yml 逐行检查，发现 3 个问题：

**问题 1：Dockerfile 启动命令写错了**

```dockerfile
# 错误：main.py 里没有 app 变量
CMD ["python", "-m", "uvicorn", "src.main:app", ...]

# 正确：app 在 api.py 里
CMD ["python", "-m", "uvicorn", "src.api:app", ...]
```

**问题 2：没有 .env 文件**

docker-compose 需要 `.env` 文件来读取环境变量，但项目里只有 `.env.example`。

```bash
cp .env.example .env   # 从模板复制一份
```

**问题 3：requirements.txt 包含重型 ML 库**

`torch`、`transformers` 这些库加起来好几个 GB，Docker 构建要 10-30 分钟。但当前只是验证框架跑通，根本用不到这些库。

### 2.2 解决方案：拆分依赖

```
v3/
├── requirements.txt        # 原始完整依赖（保留不动）
├── requirements-core.txt   # 新建：核心依赖（轻量，1-2分钟构建）
└── requirements-ml.txt     # 新建：ML/RAG 依赖（步骤5-6才需要）
```

Dockerfile 改为使用 `requirements-core.txt`。

### 2.3 去掉了 Milvus

docker-compose 里原来有 Milvus 向量数据库服务，agent-service 依赖它才能启动。但 Milvus 是步骤 6（RAG 知识库）才需要的，当前不需要。

```yaml
# 从 agent-service 的 depends_on 中移除了 milvus
# 删除了整个 milvus 服务定义
# 删除了 milvus-data 卷
```

### 新手注意

- **环境变量不要提交到 git**：`.env` 文件包含密码，已经在 `.gitignore` 中排除了
- **docker-compose 的 depends_on**：如果某个依赖服务起不来，主服务也会卡住。暂时不需要的服务要去掉依赖
- **Dockerfile 的 COPY 路径**：`COPY v3/ .` 是把 v3 目录的内容复制到容器的 /app/，不是把 v3 目录本身复制进去
- **PYTHONPATH**：Dockerfile 里设置了 `PYTHONPATH=/app`，这样 Python 才能找到 `config.settings`、`src.core.agent` 这些模块
- **端口冲突**：如果本机已经运行了 MySQL/Redis 等服务，Docker 启动会失败，因为端口被占了

---

## 三、Docker 部署时会遇到的常见坑

### 3.1 Docker Desktop 没启动

```
unable to get image 'mysql:8.0': failed to connect to the docker API
```

**解决**：打开 Docker Desktop，等托盘图标变绿再执行命令。

### 3.2 端口被占用

```
Error starting userland proxy: listen tcp4 0.0.0.0:3306: bind: address already in use
```

**解决**：关掉占用端口的程序，或者改 docker-compose.yml 里的端口映射：

```yaml
ports:
  - "3307:3306"   # 把宿主机端口改成 3307
```

### 3.3 镜像拉取慢

国内网络拉取 Docker 镜像很慢。配置镜像加速器：

```json
// Docker Desktop → Settings → Docker Engine
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.xuanyuan.me"
  ]
}
```

### 3.4 Java 构建慢

Java 第一次构建需要下载 Maven 依赖，可能要 5-10 分钟。后续构建有缓存会快很多。

### 3.5 数据库初始化失败

如果之前用 `docker-compose down -v` 删除过数据卷，再次启动时 MySQL 会重新执行 `schema.sql`。但如果数据卷还在，不会重复执行。

### 3.6 服务启动顺序

docker-compose 用了 `depends_on` + `condition: service_healthy` 来控制启动顺序：

```
MySQL/PostgreSQL/Redis 先启动（等 healthcheck 通过）
    ↓
agent-service 启动（等 postgres + redis 健康）
    ↓
java-backend 启动（等 mysql + redis + agent-service 健康）
    ↓
nginx 启动（等 java-backend + agent-service）
```

如果某个服务一直不健康，后面的都会卡住。用 `docker-compose logs <服务名>` 查看原因。

---

## 四、验证部署是否成功的命令

```bash
# 查看所有服务状态（应该全是 Up 或 healthy）
docker-compose ps

# 查看服务日志（排查问题用）
docker-compose logs -f agent-service
docker-compose logs -f java-backend

# 测试 Python Agent
curl http://localhost:8000/health

# 测试 Java 后端
curl http://localhost:9000/api/auth/me

# 测试 Nginx 代理
curl http://localhost/health
curl http://localhost/api/auth/me
```

---

## 五、关键文件速查

| 文件 | 作用 | 你可能会改的场景 |
|------|------|----------------|
| `docker-compose.yml` | 服务编排 | 加新服务、改端口、改环境变量 |
| `Dockerfile` | Python 镜像构建 | 改依赖、改启动命令 |
| `javaarea/Dockerfile` | Java 镜像构建 | 改 Maven 配置、改启动参数 |
| `nginx/nginx.conf` | 反向代理路由 | 加新路由规则 |
| `.env` | 环境变量（不提交 git） | 改数据库密码、JWT 密钥 |
| `.env.example` | 环境变量模板（提交 git） | 新增配置项时同步更新 |
| `v3/requirements-core.txt` | Python 核心依赖 | 加新 Python 包 |
| `v3/requirements-ml.txt` | Python ML 依赖 | 步骤 5-6 时才需要 |
