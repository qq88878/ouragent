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
│   ├── utils/             # 工具函数
│   │   ├── config.py      # 配置管理
│   │   └── logger.py      # 日志管理
│   └── main.py            # 主程序入口
├── tests/                 # 测试
├── examples/              # 示例代码
├── docs/                  # 文档
├── config/                # 配置文件
├── .env.example           # 环境配置示例
├── requirements.txt       # Python依赖
├── pyproject.toml         # 项目配置
└── Makefile               # 常用命令
```

## 配置说明

所有配置通过环境变量管理，参考 `.env.example`：

- `APP_ENV` — 运行环境（development/staging/production）
- `DEBUG` — 调试模式开关
- `LOG_LEVEL` — 日志级别
- `API_KEY` — API密钥

## 开发命令

```bash
make test       # 运行测试
make format     # 代码格式化 (black)
make lint       # 代码检查 (flake8)
make demo       # 运行演示
```

## 文档

- **[项目开发手册](PROJECT.md)** — 完整需求分析、技术架构、开发计划、验收标准
- **[文档目录](docs/README.md)** — 文档索引

## 许可证

MIT License - 详见 [LICENSE](LICENSE)
