# ============================================================
# Agent Service Dockerfile
# 多阶段构建，优化镜像大小
# ============================================================

# --- 基础镜像 ---
FROM python:3.11-slim AS base

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# --- 依赖安装阶段 ---
FROM base AS deps

WORKDIR /app

# 先复制依赖文�?
COPY requirements.txt ./

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# --- 运行阶段 ---
FROM base AS runtime

WORKDIR /app

# 从依赖阶段复制已安装的包
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# 复制应用代码
COPY config/ ./config/
COPY src/ ./src/
COPY data/ ./data/
COPY docs/ ./docs/
COPY __init__.py pyproject.toml ./

# 创建日志和数据目�?
RUN mkdir -p logs data

# 健康检�?
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
