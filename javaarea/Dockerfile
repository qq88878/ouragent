# Java教育系统 Docker配置
# 多阶段构�? Maven编译 �?JRE运行

# ==================== 构建阶段 ====================
FROM maven:3.9-eclipse-temurin-17 AS builder

WORKDIR /build

# 先复制pom.xml，利用Docker缓存加速依赖下�?
COPY settings.xml /root/.m2/settings.xml
COPY pom.xml .
RUN mvn dependency:go-offline -B

# 复制源代码并编译打包
COPY src/ ./src/
RUN mvn clean package -DskipTests -B

# ==================== 运行阶段 ====================
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app

# 安装运行时依�?
RUN apk add --no-cache curl tzdata && \
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

# 从构建阶段复制jar�?
COPY --from=builder /build/target/*.jar app.jar

# Create upload directory
RUN mkdir -p /data/uploads/knowledge

# 环境变量 (可通过docker-compose覆盖)
ENV JAVA_OPTS="-Xms256m -Xmx512m" \
    SPRING_PROFILES_ACTIVE=prod \
    SERVER_PORT=9000

# 暴露端口
EXPOSE 9000

# 健康检�?
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:9000/api/auth/me || exit 1

# 启动命令
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
