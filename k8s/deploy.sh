#!/bin/bash
# K8s 部署脚本

set -e

NAMESPACE="ed-agent"
K8S_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$K8S_DIR")"

echo "=== 构建 Docker 镜像 ==="

# 构建 Agent Service 镜像
echo "构建 Agent Service 镜像..."
docker build -t ouragent-agent-service:latest -f "$PROJECT_DIR/Dockerfile" "$PROJECT_DIR"

# 构建 Java Backend 镜像
echo "构建 Java Backend 镜像..."
docker build -t ouragent-java-backend:latest -f "$PROJECT_DIR/javaarea/Dockerfile" "$PROJECT_DIR/javaarea"

echo "=== 创建 K8s 资源 ==="

# 创建命名空间
echo "创建命名空间..."
kubectl apply -f "$K8S_DIR/namespace.yaml"

# 创建 Secrets 和 ConfigMap
echo "创建 Secrets 和 ConfigMap..."
kubectl apply -f "$K8S_DIR/secrets.yaml"
kubectl apply -f "$K8S_DIR/configmap.yaml"

# 创建 MySQL 初始化 SQL ConfigMap
echo "创建 MySQL 初始化 SQL ConfigMap..."
kubectl create configmap mysql-init-sql \
  --from-file="$PROJECT_DIR/javaarea/src/main/resources/db/schema.sql" \
  -n $NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# 部署数据库服务
echo "部署数据库服务..."
kubectl apply -f "$K8S_DIR/mysql.yaml"
kubectl apply -f "$K8S_DIR/postgres.yaml"
kubectl apply -f "$K8S_DIR/redis.yaml"

# 等待数据库就绪
echo "等待数据库服务就绪..."
kubectl wait --for=condition=ready pod -l app=mysql -n $NAMESPACE --timeout=120s
kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=120s
kubectl wait --for=condition=ready pod -l app=redis -n $NAMESPACE --timeout=60s

# 部署应用服务
echo "部署应用服务..."
kubectl apply -f "$K8S_DIR/agent-service.yaml"
kubectl apply -f "$K8S_DIR/java-backend.yaml"
kubectl apply -f "$K8S_DIR/nginx.yaml"

# 等待应用就绪
echo "等待应用服务就绪..."
kubectl wait --for=condition=ready pod -l app=agent-service -n $NAMESPACE --timeout=120s
kubectl wait --for=condition=ready pod -l app=java-backend -n $NAMESPACE --timeout=120s
kubectl wait --for=condition=ready pod -l app=nginx -n $NAMESPACE --timeout=60s

echo "=== 部署完成 ==="
echo ""
echo "查看服务状态:"
echo "  kubectl get pods -n $NAMESPACE"
echo "  kubectl get svc -n $NAMESPACE"
echo ""
echo "访问服务:"
echo "  Nginx: http://localhost:30080"
echo "  Java Backend: http://localhost:30080/api/"
echo "  Agent Service: http://localhost:30080/agent/"
echo ""
echo "查看日志:"
echo "  kubectl logs -f deployment/agent-service -n $NAMESPACE"
echo "  kubectl logs -f deployment/java-backend -n $NAMESPACE"
