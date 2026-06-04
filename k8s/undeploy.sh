#!/bin/bash
# K8s 卸载脚本

set -e

NAMESPACE="edu-agent"

echo "=== 删除 K8s 资源 ==="

# 删除所有资源
echo "删除命名空间 (包含所有资源)..."
kubectl delete namespace $NAMESPACE --ignore-not-found

echo "=== 卸载完成 ==="
