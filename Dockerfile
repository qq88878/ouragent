# Python Agent服务 Docker配置 (v3)
# 多阶段构建，优化镜像大小

# ==================== 构建阶段 ====================
FROM python:3.11-slim AS builder

WORKDIR /app

# 复制v3项目的依赖文件
COPY v3/requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir --user -r requirements.txt

# ==================== 运行阶段 ====================
FROM python:3.11-slim

WORKDIR /app

# 从构建阶段复制依赖
COPY --from=builder /root/.local /root/.local

# 复制v3项目的源代码
COPY v3/src/ ./src/
COPY v3/config/ ./config/
# .env 通过运行时注入 (docker run -e 或 docker-compose)

# 设置环境变量
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV APP_ENV=production
ENV PORT=8000

# 暴露端口
EXPOSE 8000

# 健康检查 (假设v3的main.py中有名为app的FastAPI实例和/health端点)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令 (假设v3的main.py中有名为app的FastAPI实例)
CMD ["python", "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]