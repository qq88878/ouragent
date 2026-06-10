# 项目文档索引

> 本文件是所有文档的导航中心，告诉你每个文档是干什么的、什么时候该看它。

---

## 文档总览

| 文档 | 位置 | 一句话说明 | 什么时候看 |
|------|------|-----------|-----------|
| **项目开发手册** | `PROJECT.md` | 项目的"百科全书"——架构、需求、技术栈、开发流程全覆盖 | 新人入门、了解全局 |
| **分阶段开发计划** | `DEVELOPMENT_PLAN.md` | 每个阶段做什么、改哪些文件、验收标准是什么 | 开始新阶段前必读 |
| **Docker 部署指南** | `DOCKER.md` | Docker Compose 本地开发和生产部署的完整说明 | 本地跑服务、部署上线 |
| **K3s 部署指南** | `docs/K3S-DEPLOYMENT-GUIDE.md` | Docker + K8s 基础概念 + 本项目 K8s 配置详解 | 学习容器化、K8s 部署 |
| **Java 集成指南** | `docs/JAVA_INTEGRATION_GUIDE.md` | Java 怎么调用 Python Agent 服务，含完整代码示例 | 写 Java 端代码时参考 |
| **Java 后端 README** | `javaarea/README.md` | Java 项目的结构、技术栈、快速启动、开发指南 | 写 Java 代码时参考 |
| **系统设计文档** | `javaarea/docs/JAVA_EDU_SYSTEM_DESIGN.md` | Java 教育系统的架构、模块划分、权限设计、数据流 | 理解 Java 端业务逻辑 |
| **数据库设计** | `javaarea/docs/DATABASE_SCHEMA.md` | 9 张表的 ER 图、字段说明、索引设计 | 改数据库、写 SQL 时参考 |
| **API 接口文档** | `javaarea/docs/API_REFERENCE.md` | 全部 REST API 的请求/响应格式 | 前后端联调、写接口时参考 |
| **Python Agent README** | `v3/README.md` | Python Agent 项目的结构、配置、开发命令 | 写 Python 代码时参考 |
| **部署经验指南** | `docs/experience.md` | Docker 部署全过程、踩坑记录、配置详解 | 部署出问题时必读 |

---

## 按场景速查

### "我是新人，想了解这个项目"
1. 先读 `PROJECT.md` — 了解项目是做什么的、整体架构
2. 再读 `DEVELOPMENT_PLAN.md` — 了解当前进度和下一步计划

### "我想本地跑起来"
1. 读 `DOCKER.md` — `docker-compose up -d` 一键启动
2. Python 端参考 `v3/README.md`
3. Java 端参考 `javaarea/README.md`

### "我要写 Java 代码"
1. `javaarea/README.md` — 项目结构和开发指南
2. `javaarea/docs/API_REFERENCE.md` — 接口格式
3. `javaarea/docs/DATABASE_SCHEMA.md` — 数据库表结构
4. `docs/JAVA_INTEGRATION_GUIDE.md` — 怎么调 Python Agent

### "我要写 Python Agent 代码"
1. `v3/README.md` — 项目结构和开发命令
2. `PROJECT.md` 第六章 — Agent 服务详解和扩展设计

### "我要部署到服务器"
1. `DOCKER.md` — Docker Compose 生产部署
2. `docs/K3S-DEPLOYMENT-GUIDE.md` — K8s 部署

### "我想知道数据库长什么样"
1. `javaarea/docs/DATABASE_SCHEMA.md` — ER 图 + 9 张表字段详解

### "我想知道有哪些 API"
1. `javaarea/docs/API_REFERENCE.md` — 全部接口文档

### "Docker 部署出问题了"
1. `docs/experience.md` — 踩坑记录、排错流程、配置速查表
2. `DOCKER.md` — Docker Compose 基础用法
