# K8s 速查卡

## 一句话理解每个组件

| 组件 | 一句话 |
|------|--------|
| Pod | 跑容器的"小房间" |
| Deployment | 管理 Pod 的"宿管"，确保数量对 |
| Service | 给 Pod 发"电话号码"，让其他服务能找到它 |
| ConfigMap | 存配置的"公告栏" |
| Secret | 存密码的"保险箱" |
| PVC | 申请存储空间的"租房合同" |
| Namespace | 隔离项目的"楼层" |
| Ingress | 外部访问的"前台" |

## 部署顺序口诀

```
空间 → 配置 → 存储 → 数据库 → 应用 → 代理
```

## 最小部署模板

```yaml
# 1. 命名空间
apiVersion: v1
kind: Namespace
metadata:
  name: my-app

---
# 2. 部署
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  namespace: my-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: app
          image: my-app:latest
          ports:
            - containerPort: 8000

---
# 3. 服务
apiVersion: v1
kind: Service
metadata:
  name: my-app
  namespace: my-app
spec:
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 8000
  type: NodePort
```

## 常用命令

```bash
# 看状态
kubectl get pods -n ns
kubectl get svc -n ns

# 看日志
kubectl logs -f pod-name -n ns

# 进容器
kubectl exec -it pod-name -n ns -- bash

# 部署
kubectl apply -f file.yaml

# 删除
kubectl delete -f file.yaml
kubectl delete namespace ns
```

## .gitignore 记得加

```gitignore
k8s/secrets.yaml
docker-compose.override.yml
```

## 排错三板斧

```bash
# 1. 看 Pod 状态
kubectl describe pod pod-name -n ns

# 2. 看日志
kubectl logs pod-name -n ns

# 3. 看事件
kubectl get events -n ns
```
