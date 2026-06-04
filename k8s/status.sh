#!/bin/bash
# K8s 状态查看脚本

NAMESPACE="edu-agent"

echo "=== Pods ==="
kubectl get pods -n $NAMESPACE -o wide

echo ""
echo "=== Services ==="
kubectl get svc -n $NAMESPACE

echo ""
echo "=== PersistentVolumeClaims ==="
kubectl get pvc -n $NAMESPACE

echo ""
echo "=== Deployments ==="
kubectl get deployments -n $NAMESPACE
