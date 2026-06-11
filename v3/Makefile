.PHONY: help install dev test lint format clean docs run demo docker docker-up docker-down docker-logs

# 默认目标
help:
	@echo "Available commands:"
	@echo "  install       - Install dependencies"
	@echo "  dev           - Install development dependencies"
	@echo "  test          - Run tests"
	@echo "  lint          - Run linter"
	@echo "  format        - Format code"
	@echo "  clean         - Clean temporary files"
	@echo "  docs          - Generate documentation"
	@echo "  run           - Run the application"
	@echo "  demo          - Run demo mode"
	@echo ""
	@echo "Docker commands:"
	@echo "  docker        - Build Docker image"
	@echo "  docker-up     - Start services with docker-compose"
	@echo "  docker-down   - Stop services"
	@echo "  docker-logs   - View service logs"
	@echo "  docker-restart - Restart services"

# 安装依赖
install:
	pip install -r requirements.txt

# 安装开发依赖
dev:
	pip install -r requirements.txt
	pip install -e ".[dev]"

# 运行测试
test:
	pytest tests/ -v --cov=src --cov-report=term-missing

# 运行特定测试
test-agent:
	pytest tests/test_agent.py -v

test-config:
	pytest tests/test_config.py -v

# 运行linter
lint:
	flake8 src/ tests/
	mypy src/

# 格式化代码
format:
	black src/ tests/
	isort src/ tests/

# 检查代码格式
check-format:
	black --check src/ tests/
	isort --check-only src/ tests/

# 清理临时文件
clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

# 生成文档
docs:
	sphinx-build -b html docs/ docs/_build/html

# 运行应用
run:
	python src/main.py --mode interactive

# 运行演示
demo:
	python src/main.py --mode demo

# 安装pre-commit hooks
pre-commit:
	pre-commit install

# 运行pre-commit
pre-commit-run:
	pre-commit run --all-files

# 创建虚拟环境
venv:
	python -m venv venv
	@echo "Virtual environment created. Activate with:"
	@echo "  Windows: venv\\Scripts\\activate"
	@echo "  Linux/Mac: source venv/bin/activate"

# 更新依赖
update-deps:
	pip install --upgrade -r requirements.txt

# 检查依赖安全
security:
	pip-audit

# 生成requirements.txt
freeze:
	pip freeze > requirements.txt

# 代码统计
stats:
	@echo "Lines of code:"
	find src -name "*.py" | xargs wc -l
	@echo ""
	@echo "Test coverage:"
	pytest --cov=src --cov-report=term-missing | tail -20

# Docker 命令
docker:
	docker build -t agent-service .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f agent-service

docker-restart:
	docker-compose restart agent-service

docker-build:
	docker-compose build --no-cache

# 创建 .env 文件
env:
	cp config/.env.example config/.env
	@echo "Created config/.env from template. Please edit it with your settings."
