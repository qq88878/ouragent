# ============================================================
# Python Agent 服务 - 多阶段构建
# 优化镜像大小，加快构建速度
# ============================================================

# ==================== 第一阶段: 构建依赖 ====================
FROM python:3.13-slim AS builder

# 设置工作目录
WORKDIR /build

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY v3/requirements-core.txt .

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 使用清华镜像源安装依赖
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --prefer-binary \
    -r requirements-core.txt

# ==================== 第二阶段: 运行环境 ====================
FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制应用代码
COPY v3/ .

# 创建必要的目录
RUN mkdir -p logs data uploads

# 设置环境变量
ENV PYTHONPATH=/app
ENV APP_ENV=production
ENV DEBUG=false
ENV LOG_LEVEL=INFO
ENV PORT=8000

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
