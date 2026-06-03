# 项目开发手册

> **项目名称**：基于大模型的个性化资源生成与学习多智能体系统
> **版本**：v2.0（含详细需求分析）
> **更新日期**：2026年6月
> **截止时间**：2026年7月初（1个月）

---

## 一、项目概述

### 1.1 核心目标

构建一个**计算机/编程领域**的个性化学习平台，通过多智能体协作实现：
- 学生画像构建与动态更新
- 个性化学习路径规划
- 教学资源智能生成（题库、思维导图、文档/PPT）
- 智能辅导与学习效果评估

### 1.2 比赛硬性要求

| 要求 | 说明 |
|------|------|
| 必须使用星火大模型 | 核心推理引擎，不能只用其他模型 |
| 必须体现多智能体 | 清晰的Agent分工与协作流程 |
| 资源必须可交互 | 生成的内容支持下载/预览 |
| 一键启动 | docker-compose up 即可运行 |

### 1.3 我们的策略

**双模型策略**：
- **星火大模型**：核心功能（画像分析、路径规划、资源生成）
- **小米MiMo**：辅助功能（对话补全、简单问答、测试阶段）

## 二、详细需求分析

### 2.1 用户角色定义

| 角色 | 描述 | 核心诉求 |
|------|------|----------|
| **学生（主要用户）** | 计算机/编程领域的学习者 | 获得个性化学习体验，高效掌握知识 |
| **教师/管理员** | 课程内容管理者 | 查看学生学习情况，管理资源 |

### 2.2 功能需求全景图（FURPS+分类法）

#### F1 - 用户管理模块
| 编号 | 需求项 | 优先级 | 说明 |
|------|--------|--------|------|
| F1.1 | 用户注册/登录 | P0 | 邮箱/用户名+密码，JWT鉴权 |
| F1.2 | 用户信息管理 | P1 | 昵称、头像、学习偏好设置 |
| F1.3 | 学习历史记录 | P1 | 浏览、对话、资源生成历史 |

#### F2 - 智能对话模块（核心）
| 编号 | 需求项 | 优先级 | 说明 |
|------|--------|--------|------|
| F2.1 | 多轮对话交互 | P0 | 支持上下文记忆，连续对话 |
| F2.2 | 流式输出（SSE） | P0 | 打字机效果，提升体验 |
| F2.3 | Agent协作透明化 | P0 | 向用户展示当前由哪个Agent处理 |
| F2.4 | 知识库检索增强（RAG） | P1 | 对话中自动检索相关课程知识 |
| F2.5 | 代码高亮与渲染 | P1 | Markdown代码块语法高亮 |

#### F3 - 学生画像模块
| 编号 | 需求项 | 优先级 | 说明 |
|------|--------|--------|------|
| F3.1 | 知识水平评估 | P0 | 通过问答/测试评估当前水平 |
| F3.2 | 画像多维标签生成 | P0 | 知识掌握度、学习风格、薄弱点 |
| F3.3 | 画像动态更新 | P0 | 每次交互后自动更新画像 |
| F3.4 | 雷达图可视化 | P1 | 前端展示多维画像 |

#### F4 - 学习路径规划模块
| 编号 | 需求项 | 优先级 | 说明 |
|------|--------|--------|------|
| F4.1 | 基于画像的路径生成 | P0 | 根据画像生成个性化学习路线 |
| F4.2 | 路径动态调整 | P1 | 学习进度变化后自动调整路径 |
| F4.3 | 路径可视化（时间线） | P1 | 前端展示学习步骤与进度 |
| F4.4 | 里程碑与目标设定 | P2 | 设置学习目标，分阶段完成 |

#### F5 - 教学资源生成模块
| 编号 | 需求项 | 优先级 | 说明 |
|------|--------|--------|------|
| F5.1 | 智能题库生成 | P0 | 根据知识点生成选择题/编程题 |
| F5.2 | 思维导图生成（Mermaid） | P0 | 知识点结构化梳理 |
| F5.3 | 学习文档/笔记生成 | P1 | Markdown格式的结构化文档 |
| F5.4 | PPT幻灯片生成 | P1 | 可下载的PPT文件 |
| F5.5 | 资源预览与下载 | P0 | 所有资源支持在线预览和文件下载 |

#### F6 - 学习评估模块
| 编号 | 需求项 | 优先级 | 说明 |
|------|--------|--------|------|
| F6.1 | 知识点测验 | P0 | 自动出题并批改 |
| F6.2 | 学习效果报告 | P1 | 生成阶段性学习报告 |
| F6.3 | 薄弱点诊断 | P1 | 分析错误模式，定位薄弱环节 |

#### F7 - 多智能体协作（系统级功能）
| 编号 | 需求项 | 优先级 | 说明 |
|------|--------|--------|------|
| F7.1 | 至少3个Agent协作 | P0 | 硬性要求，清晰的分工 |
| F7.2 | Agent间通信可见 | P1 | 用户可看到Agent思考过程 |
| F7.3 | 状态持久化 | P1 | Agent状态在会话间保持 |

#### U - Usability（可用性）
| 编号 | 需求项 | 优先级 | 说明 |
|------|--------|--------|------|
| U1 | 响应时间 ≤ 3s（非流式） | P0 | API响应需在合理时间内 |
| U2 | 流式输出延迟 ≤ 500ms | P0 | 首字延迟控制在半秒内 |
| U3 | 移动端适配 | P2 | 响应式布局，支持手机访问 |
| U4 | 操作引导 | P1 | 首次使用有引导提示 |
| U5 | 错误提示友好 | P1 | 网络错误、API错误的用户提示 |

#### R - Reliability（可靠性）
| 编号 | 需求项 | 优先级 | 说明 |
|------|--------|--------|------|
| R1 | API调用失败重试（3次） | P0 | LLM调用失败自动重试 |
| R2 | 会话数据不丢失 | P0 | Redis缓存+MySQL持久化 |
| R3 | Agent超时兜底 | P1 | 单Agent超过30s超时提示 |
| R4 | 输入校验防注入 | P0 | 所有用户输入做安全校验 |

#### P - Performance（性能）
| 编号 | 需求项 | 优先级 | 说明 |
|------|--------|--------|------|
| P1 | 并发支持 ≥ 10用户 | P1 | Docker部署下同时使用 |
| P2 | 知识库检索 ≤ 2s | P1 | Milvus向量检索效率 |
| P3 | 资源生成 ≤ 30s | P0 | 单次资源生成时间上限 |
| P4 | 数据库连接池 ≥ 10 | P1 | MySQL连接池配置 |

#### S - Security（安全）
| 编号 | 需求项 | 优先级 | 说明 |
|------|--------|--------|------|
| S1 | 密码加密存储（bcrypt） | P0 | 用户密码不可逆加密 |
| S2 | JWT Token鉴权 | P0 | API接口需携带Token |
| S3 | API密钥不泄露 | P0 | 星火/MiMo密钥存储在环境变量 |
| S4 | 输入XSS过滤 | P1 | 用户输入内容做安全过滤 |

### 2.3 业务流程需求（Use Cases）

**UC1 - 学生首次使用流程**：用户注册登录 → 选择方向 → 水平评估 → ProfileAgent画像 → PlannerAgent路径 → 展示路径 → 进入对话

**UC2 - 日常学习流程**：用户提问 → RAG检索 → 多Agent处理 → ProfileAgent更新画像 → WriterAgent回答 → 展示结果 → 用户反馈

**UC3 - 资源生成流程**：请求生成资源 → ResearcherAgent搜集知识 → WriterAgent生成内容 → ReviewerAgent审查 → 预览 → 下载

**UC4 - 学习评估流程**：完成学习 → EvaluatorAgent出题 → 用户作答 → 批改 → ProfileAgent更新画像 → 学习报告 → 推荐

### 2.4 数据需求

MySQL核心表：users, learning_profiles, learning_paths, generated_resources, chat_history

Milvus集合：course_knowledge（字段：id, embedding(768d), content, metadata）

### 2.5 API契约需求

| 端点 | 方法 | 描述 | 认证 |
|------|------|------|------|
| /api/v1/auth/register | POST | 用户注册 | 否 |
| /api/v1/auth/login | POST | 用户登录返回JWT | 否 |
| /api/v1/chat/session | POST | 创建对话Session | 是 |
| /api/v1/chat/stream | POST/SSE | 流式对话 | 是 |
| /api/v1/profile/get | GET | 获取学生画像 | 是 |
| /api/v1/path/generate | POST | 生成学习路径 | 是 |
| /api/v1/resource/generate | POST | 生成教学资源 | 是 |
| /api/v1/resource/list | GET | 资源列表 | 是 |
| /api/v1/resource/download/{id} | GET | 下载资源文件 | 是 |
| /api/v1/evaluate/quiz | POST | 出题测验 | 是 |
| /api/v1/evaluate/submit | POST | 提交答案批改 | 是 |
| /api/v1/evaluate/report | GET | 学习报告 | 是 |

---

## 三、技术架构

### 3.1 架构总览

`
前端层：Vue 3 + TypeScript + Element Plus + Vite
后端层：Python 3.11 + FastAPI + Uvicorn
Agent层：LangGraph StateGraph（6个Agent：Planner/Profile/Researcher/Writer/Reviewer/Evaluator）
数据层：Milvus(向量) + MySQL(结构化) + Redis(缓存)
`

### 3.2 技术选型

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 前端 | Vue 3 + TypeScript | 3.4+ | 学习平台界面 |
| UI库 | Element Plus | 2.x | 组件库 |
| 构建 | Vite | 5.x | 快速开发构建 |
| 后端 | Python + FastAPI | 3.11+ | API服务、流式输出 |
| Agent | LangGraph | 0.0.40 | 多智能体状态机 |
| LLM | 讯飞星火 + 小米MiMo | - | 核心推理 + 辅助 |
| RAG | LangChain | 0.1.5 | 文档加载、切分、检索 |
| 向量库 | Milvus | 2.x | 课程知识库向量存储 |
| 数据库 | MySQL | 8.x | 学生画像、学习记录 |
| 缓存 | Redis | 7.x | 会话缓存、状态管理 |
| 部署 | Docker Compose | - | 一键启动 |

---

## 四、详细开发流程（需求分析驱动）

> 每个阶段拆分为：需求分析→接口设计→实现→验证
> 前一阶段验收通过后才进入下一阶段

---

### 阶段一：项目脚手架与基础框架（3天）

#### 对应需求
- 硬性要求：Docker一键启动 → 需搭建完整项目骨架
- 安全需求：S1密码加密、S2 JWT鉴权 → 需用户模块
- 性能需求：P4连接池 → 需数据库配置

#### 需求分析确认清单
- [x] Docker Compose能一键拉起所有服务
- [x] 前端Vue3项目能正常启动并访问
- [x] 后端FastAPI能正常启动并响应
- [x] MySQL/Milvus/Redis能正常连接
- [x] 项目目录结构清晰，可扩展

#### 开发任务

1) 创建项目目录结构（backend/ frontend/ docker/ knowledge_base/）
2) 后端基础搭建：FastAPI入口、CORS中间件、Config管理、DB连接池
3) 数据库模型：SQLAlchemy定义User等模型 + Alembic迁移
4) 前端基础：Vue3 + Vite + Element Plus + 路由配置（6个页面）
5) Docker Compose配置：6个服务（frontend/backend/mysql/milvus/redis）
6) 用户模块：注册API(bcrypt) + 登录API(JWT) + 前端登录/注册页面

#### 验收标准
- [ ] docker-compose up -d 后6个容器正常运行
- [ ] 访问localhost:3000显示前端登录页
- [ ] 访问localhost:8000/docs显示Swagger文档
- [ ] 注册新用户→登录→获取Token→访问受保护接口成功
- [ ] 容器重启后数据不丢失
- [ ] 前端路由切换正常

---

### 阶段二：多智能体核心框架与基础对话（5天）

#### 对应需求
- 硬性要求：至少3个Agent协作 + 使用星火大模型
- 核心功能：F2智能对话
- 可用性需求：U2流式输出延迟

#### 需求分析确认清单
- [x] 星火大模型API调用成功
- [x] 至少3个Agent能协作完成一个任务
- [x] 支持流式输出（SSE打字机效果）
- [x] MiMo模型作为备选正常运行

#### 开发任务

1) LLM集成层：llm_spark.py（星火WebSocket流式/非流式/重试3次）+ llm_mimo.py + llm_base.py（抽象类）+ prompts.py
2) LangGraph框架：AgentState定义（user_input/user_profile/agent_memory/current_agent等）
3) 三个核心Agent：ProfileAgent（画像分析）、PlannerAgent（路径规划）、WriterAgent（内容生成）
4) Agent编排器orchestrator.py：意图识别→选择工作流（chat流程：Profile→Planner→Writer）
5) 意图分类器intent_classifier.py：chat/generate_resource/evaluate/show_profile等
6) 流式对话API：POST /chat/session（创建会话）+ POST /chat/stream（SSE流）
7) SSE事件格式：agent_update/token/complete/error
8) 前端ChatBox.vue：消息列表+输入框+Agent指示器+SSE渲染+Markdown

#### 验收标准
- [ ] 星火大模型API调用成功（流式+非流式）
- [ ] SSE流返回，前端逐字渲染
- [ ] ProfileAgent生成画像JSON（含knowledge_level字段）
- [ ] PlannerAgent生成学习路径（含步骤和时长）
- [ ] WriterAgent生成教学回答（含代码示例）
- [ ] Agent切换时前端显示指示器
- [ ] 前端ChatBox正确渲染Markdown
- [ ] intent_classifier正确区分意图

---

### 阶段三：学生画像与学习路径模块（3天）

#### 对应需求
- F3学生画像（评估、标签生成、动态更新、可视化）
- F4学习路径（生成、调整、可视化）

#### 开发任务

1) 画像API：profile.py - GET /profile/get, POST /profile/update
2) 画像服务：profile_service.py - 画像CRUD + knowledge_level计算 + weak_points识别
3) ProfileAgent增强：知识掌握度(5+维) + 学习风格 + 强弱项 + 学习节奏
4) 路径API：path.py - POST /path/generate, GET /path/current, PUT /path/progress
5) 路径服务：path_service.py - generate_path + update_progress
6) PlannerAgent增强：路径含steps(id/title/type/duration/status) + milestones
7) 前端可视化：ProfileRadar.vue（ECharts雷达图）+ LearningTimeline.vue（时间线）
8) 前端页面：ProfileView.vue + PathView.vue

#### 验收标准
- [ ] 画像API返回完整JSON（5个维度以上）
- [ ] 对话后画像自动更新
- [ ] 路径API返回结构化JSON（3个步骤以上）
- [ ] 路径进度更新功能正常
- [ ] 雷达图正常渲染
- [ ] 时间线状态颜色正确

---

### 阶段四：教学资源生成模块（4天）

#### 对应需求
- F5题库生成、思维导图、文档、PPT
- 硬性要求：资源必须可交互（预览+下载）

#### 开发任务

1) ResearcherAgent（新增）：搜集和组织知识点，输出结构化知识大纲
2) ReviewerAgent（新增）：审查内容质量（准确性/完整性/难度匹配）
3) 资源API：POST /resource/generate, GET /resource/list, GET /resource/download/{id}
4) 题库生成器resource_quiz.py：选择题(题目+4选项+答案+解析) + 编程题(题目+示例+思路+代码)
5) 思维导图生成器resource_mindmap.py：Mermaid格式
6) 文档生成器resource_document.py：Markdown格式结构化文档
7) PPT生成器resource_ppt.py：python-pptx生成可下载PPT
8) 前端组件：ResourcePreview.vue + ResourceCard.vue
9) 前端页面：ResourceView.vue（类型筛选+搜索+新建+列表）

#### 验收标准
- [ ] ResearcherAgent输出知识大纲 + ReviewerAgent审查
- [ ] 选择题生成含完整题目+选项+答案+解析
- [ ] 编程题生成含示例+思路+参考代码
- [ ] 思维导图Mermaid格式正确
- [ ] 文档Markdown格式正确
- [ ] PPT生成可下载pptx文件
- [ ] 资源预览+下载功能正常

---
### 阶段五：学习评估与RAG知识库（3天）

#### 对应需求
- F6学习评估（出题、批改、报告）
- F2.4 RAG知识库检索增强

#### 开发任务

1) EvaluatorAgent：出题测验、批改答案、生成评估报告
2) 评估API：POST /evaluate/quiz, POST /evaluate/submit, GET /evaluate/report
3) RAG知识库：文档加载(PDF/TXT/MD) → LangChain切分(chunk=500, overlap=50) → sentence-transformers嵌入(768d) → Milvus存储 → Top-3检索
4) RAG集成到对话：Orchestrator中chat工作流添加RAG步骤
5) 评估服务：evaluate_service.py - generate_quiz/grade_answer/generate_report
6) 学习报告：基本信息+知识点掌握度+薄弱点诊断+建议

#### 验收标准
- [ ] EvaluatorAgent根据薄弱点出题
- [ ] 批改API正确判断答案并给出解析
- [ ] 学习报告返回结构化报告
- [ ] Milvus导入知识库数据
- [ ] RAG检索返回语义相关片段
- [ ] 对话自动触发RAG检索

---

### 阶段六：前端完善与体验优化（3天）

#### 对应需求
- U1响应时间、U3移动端适配、U4操作引导、U5错误提示
- S4 XSS过滤

#### 开发任务

1) 全局UI优化：Element Plus主题定制 + 侧边栏图标 + 顶栏用户信息
2) 首页HomeView.vue：统计卡片(学习天数/资源数/知识点/进度) + 快捷操作 + 最近活动
3) 错误处理：HTTP拦截器统一处理（401跳转登录/500友好提示）
4) 操作引导：首次登录遮罩引导 + 新手任务
5) 加载优化：Skeleton组件 + 分页加载
6) 响应式适配：移动端布局 + 侧边栏折叠

#### 验收标准
- [ ] 首页统计卡片数据真实
- [ ] 全局错误提示不暴露技术细节
- [ ] Token过期自动跳转登录
- [ ] 所有API调用有loading状态
- [ ] 引导流程对新用户友好

---
### 阶段七：集成测试与Docker部署（4天）

#### 对应需求
- 硬性要求：一键启动
- 可靠性需求：R1重试、R2持久化、R3超时

#### 开发任务

1) 集成测试：test_chat.py / test_profile.py / test_path.py / test_resource.py / test_evaluate.py / test_agents.py
2) Dockerfile优化：多阶段构建 + 生产模式
3) docker-compose完善：健康检查 + 服务依赖等待 + 日志轮转
4) 端到端测试：注册→登录→对话→画像→路径→资源→测验→报告
5) 文档完善：README.md + .env.example + API文档

#### 验收标准
- [ ] docker-compose up -d 一键启动
- [ ] 端到端流程完整走通
- [ ] 核心API测试通过
- [ ] README完整可上手

---

## 五、开发计划甘特图

| 阶段 | 天数 | 产出 |
|------|------|------|
| 阶段一：项目脚手架 | 3天 | 项目骨架+用户模块+Docker |
| 阶段二：Agent框架 | 5天 | LLM集成+3个Agent+SSE对话 |
| 阶段三：画像与路径 | 3天 | 画像API+路径API+可视化 |
| 阶段四：资源生成 | 4天 | 4种资源生成+预览下载 |
| 阶段五：评估与RAG | 3天 | 评估API+Milvus知识库 |
| 阶段六：前端优化 | 3天 | 首页+引导+错误处理 |
| 阶段七：测试部署 | 4天 | 集成测试+Docker部署 |
| **总计** | **25天** | 完整平台 |

---

## 六、详细验收检查清单

### 阶段一
- [ ] 项目目录结构完整
- [ ] Docker Compose启动全部服务
- [ ] FastAPI+Swagger可访问
- [ ] Vue3前端启动+路由正常
- [ ] MySQL/Redis/Milvus连接正常
- [ ] 用户注册/登录功能正常
- [ ] JWT鉴权保护接口正常

### 阶段二
- [ ] 星火大模型API调用成功（流式+非流式）
- [ ] MiMo API调用成功
- [ ] LangGraph状态定义完整
- [ ] 3个以上Agent协作工作
- [ ] SSE流式对话接口正常
- [ ] 前端ChatBox流式渲染
- [ ] Markdown代码高亮
- [ ] Agent切换前端指示器

### 阶段三
- [ ] 画像API返回完整多维数据
- [ ] 对话后画像自动更新
- [ ] 雷达图前端渲染
- [ ] 路径生成API正常
- [ ] 路径进度更新正常
- [ ] 时间线前端渲染

### 阶段四
- [ ] ResearcherAgent+ReviewerAgent正常协作
- [ ] 选择题生成（含解析）
- [ ] 编程题生成（含参考代码）
- [ ] 思维导图Mermaid生成
- [ ] 文档Markdown生成
- [ ] PPT生成可下载
- [ ] 资源预览+下载功能正常

### 阶段五
- [ ] EvaluatorAgent出题测验
- [ ] 自动批改+解析
- [ ] 学习报告生成
- [ ] Milvus知识库导入
- [ ] RAG检索正常

### 阶段六
- [ ] 首页统计卡片
- [ ] 全局错误提示
- [ ] Token过期处理
- [ ] Loading状态覆盖
- [ ] 新手引导流程
- [ ] 响应式适配

### 阶段七
- [ ] Docker Compose一键启动
- [ ] 端到端完整流程
- [ ] 核心API测试通过
- [ ] README完整

---

## 七、Docker部署方案

6个服务：frontend(nginx+Vue3,3000) backend(FastAPI,8000) mysql(8.0,3306) milvus(latest,19530) redis(7-alpine,6379)

关键配置：backend依赖mysql(healthcheck)/milvus/redis；持久化数据卷mysql_data/milvus_data

启动：docker-compose up -d

---

## 八、环境变量

核心变量：SPARK_APP_ID/API_KEY/SECRET, MIMO_API_KEY/BASE_URL, MYSQL_ROOT_PASSWORD/HOST/PORT, MILVUS_HOST/PORT, REDIS_HOST/PORT, JWT_SECRET_KEY/ALGORITHM, DEBUG/LOG_LEVEL

---

## 九、风险与应对

| 风险 | 应对 |
|------|------|
| 星火API申请延迟 | 先用MiMo跑通流程 |
| LangGraph学习曲线 | 先用简单Chain+条件路由 |
| 时间不够 | 砍非核心功能保Demo |
| 前端耗时 | 用Element Plus模板 |
| Docker部署问题 | 准备无Docker备选方案 |
| Milvus资源高 | 备选ChromaDB |
| 双模型切换 | 统一LLM抽象层 |

---

## 十、团队分工

**你**：架构设计 + Agent层 + 后端API + 技术难点 + 需求分析与验收
**队友A**：前端界面 + API对接 + 用户体验 + 组件测试
**队友B（如有）**：RAG知识库 + 文档处理 + 测试部署 + Docker

---

## 十一、附录：关键代码参考

FastAPI主入口：CORS中间件 + 6个路由模块注册 + 健康检查

Agent模板：system_prompt + run方法(构造Prompt→调用LLM→解析→返回状态)

SSE流式对话：StreamingResponse + event_generator(agent_update/token/complete/error)

前端SSE处理：fetch POST → reader读取流 → 按行解析 → 回调渲染

---

## 十二、快速开始

`ash
git clone <repo_url>
cd v3
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# 编辑.env填入API密钥

# 本地开发
cd backend && uvicorn app.main:app --reload --port 8000
cd frontend && npm install && npm run dev

# Docker部署
docker-compose up -d
# 访问 http://localhost:3000
`

---

**文档维护者**：项目主导者
**最后更新**：2026年6月3日
**文档版本**：v2.0（含详细需求分析）