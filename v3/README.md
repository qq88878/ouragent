# ouragent - Agent编程项目

基于大模型的个性化资源生成与学习多智能体系统，面向计算机/编程领域的学生，支持比赛和教学应用。

## 快速开始

```bash
# 克隆项目
git clone <repository-url>
cd ouragent/v3

# 创建虚拟环境并安装依赖
python -m venv venv
venv\Scripts\activate  # Linux/Mac: source venv/bin/activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入API密钥

# 运行示例
python examples/basic_agent.py

# 运行测试
pytest tests/
```

## 项目结构

```
ouragent/
├── src/                    # 源代码
│   ├── core/              # 核心模块
│   │   ├── agent.py       # Agent核心类
│   │   ├── memory.py      # 内存管理
│   │   └── tools.py       # 工具接口
│   ├── auth/              # 服务间认证
│   │   └── security.py    # X-Service-Key 密钥验证
│   ├── db/                # 数据库连接
│   │   ├── database.py    # SQLAlchemy 异步连接
│   │   └── models.py      # 数据模型
│   └── api.py             # FastAPI 主入口（所有端点定义）
├── config/                # 配置文件
│   └── settings.py        # 环境变量配置
├── tests/                 # 测试
├── examples/              # 示例代码
├── docs/                  # 文档
├── requirements-core.txt  # 核心依赖（Docker 构建用）
├── requirements-ml.txt    # ML/RAG 依赖（步骤5-6才需要）
├── pyproject.toml         # 项目配置
└── Makefile               # 常用命令
```

## API 端点

本服务是**内部服务**，仅供 Java 后端通过服务间密钥调用，不面向终端用户。

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| GET | `/health` | 无 | 健康检查 |
| GET | `/agent/status` | 无 | Agent 运行状态 |
| GET | `/agent/tools` | 无 | 可用工具列表 |
| POST | `/agent/chat` | X-Service-Key | AI 对话 |
| POST | `/agent/tool` | X-Service-Key | 调用指定工具 |
| DELETE | `/agent/memory` | X-Service-Key | 清除 Agent 记忆 |

**认证方式**：需要鉴权的端点必须在请求头中携带 `X-Service-Key`，密钥通过环境变量 `AGENT_SERVICE_KEY` 配置。

```bash
# 示例：调用 Agent 对话
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -H "X-Service-Key: internal-agent-key-2024" \
  -d '{"message": "你好"}'
```

## 配置说明

所有配置通过环境变量管理，参考 `.env.example`：

- `APP_ENV` — 运行环境（development/staging/production）
- `DEBUG` — 调试模式开关
- `LOG_LEVEL` — 日志级别
- `AGENT_SERVICE_KEY` — 服务间密钥（Java 调用时必须匹配）

## 开发命令

```bash
make test       # 运行测试
make format     # 代码格式化 (black)
make lint       # 代码检查 (flake8)
make demo       # 运行演示
```

## 文档

- **[文档目录](docs/README.md)** — 文档索引

## 许可证

MIT License - 详见 [LICENSE](LICENSE)
