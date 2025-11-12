# Deployment Guide
## Ollama Chat Application - Production Deployment

**Version:** 1.1.0
**Last Updated:** November 2025

---

## Table of Contents
1. [Overview](#overview)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Production Deployment](#production-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Environment Configuration](#environment-configuration)
7. [Monitoring & Logging](#monitoring--logging)
8. [Troubleshooting](#troubleshooting)

---

## Overview

This guide covers deploying the Ollama Chat Application across different environments:

| Environment | Use Case | Complexity | Resources |
|-------------|----------|-----------|-----------|
| **Local Dev** | Development, testing | Low | Single machine |
| **Docker** | Testing, staging, production | Medium | Docker host |
| **Kubernetes** | Scalable production | High | K8s cluster |

---

## Local Development

### Prerequisites
- Python 3.11+
- Ollama service running locally
- pip or uv package manager

### Setup Steps

#### 1. Clone Repository
```bash
git clone https://github.com/yourorg/ollama-chat.git
cd ollama-chat
```

#### 2. Create Virtual Environment
```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate

# Or using Python
python3.11 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Configure Environment
```bash
# Copy example configuration
cp config/.env.example .env

# Edit if needed
nano .env
```

#### 5. Start Ollama
```bash
# In a separate terminal
ollama serve

# In another terminal, pull model
ollama pull tinyllama
```

#### 6. Run Application
```bash
# Development mode with auto-reload
uv run src/main.py

# Or with uvicorn
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### 7. Access Application
```
Browser: http://localhost:8000
API Docs: http://localhost:8000/docs
```

---

## Docker Deployment

### Quick Start

#### 1. Prerequisites
- Docker installed (20.10+)
- Docker Compose installed (2.0+)
- At least 2GB free disk space

#### 2. Deploy Full Stack
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f chat-app
```

#### 3. Access Application
```
Browser: http://localhost:8000
Ollama API: http://localhost:11434
Health Check: http://localhost:8000/api/health
```

#### 4. Verify Deployment
```bash
# Check chat endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'

# Check health
curl http://localhost:8000/api/health
```

### Docker Build Options

#### Build Custom Image
```bash
# Build from Dockerfile
docker build -t ollama-chat:1.1.0 .

# Run container
docker run -p 8000:8000 \
  --env OLLAMA_API_URL=http://ollama:11434/api \
  ollama-chat:1.1.0
```

#### Multi-Stage Build (Optimized)
```bash
# Builds with minimal size (using builder stage)
docker build --target runtime -t ollama-chat:slim .
docker images | grep ollama-chat  # Check size
```

### Docker Networking

Containers communicate via `app-network` bridge:

```
┌─────────────────────────────────────┐
│        Docker Network               │
│        (app-network)                │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────┐      ┌──────────────┐│
│  │ollama    │◄────►│chat-app      ││
│  │:11434   │      │:8000         ││
│  └──────────┘      └──────────────┘│
│                                     │
└─────────────────────────────────────┘
```

### Volume Management

Ollama models are persisted in `ollama-models` volume:

```bash
# List volumes
docker volume ls | grep ollama

# Inspect volume
docker volume inspect ollama-models

# Backup models
docker run -v ollama-models:/data \
  -v ~/backups:/backup \
  alpine tar -czf /backup/ollama-models.tar.gz -C /data .

# Restore models
docker run -v ollama-models:/data \
  -v ~/backups:/backup \
  alpine tar -xzf /backup/ollama-models.tar.gz -C /data
```

---

## Production Deployment

### Architecture

```
┌──────────────────────────────────────────────────┐
│                   Internet                        │
│              (HTTPS + SSL/TLS)                    │
└────────────────────┬─────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────┐
│           Load Balancer / Reverse Proxy           │
│          (Nginx / HAProxy / CloudFront)           │
└────────────────────┬─────────────────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼──────┐  ┌──────▼──────┐  ┌─────▼────┐
│  Chat    │  │  Chat       │  │  Chat    │
│ App Pod  │  │ App Pod     │  │ App Pod  │
│ (replica1)  │ (replica2)  │  │ (replica3)
└───┬──────┘  └──────┬──────┘  └─────┬────┘
    │                │                │
    └────────────────┼────────────────┘
                     │
        ┌────────────▼────────────┐
        │   Ollama Service Pool   │
        │  (Kubernetes StatefulSet)
        └────────────────────────┘
```

### Cloud Deployment Options

#### AWS ECS (Elastic Container Service)
```bash
# Create ECS task definition
aws ecs register-task-definition \
  --cli-input-json file://task-definition.json

# Create ECS service
aws ecs create-service \
  --cluster ollama-chat-prod \
  --service-name chat-app \
  --task-definition ollama-chat:1
```

#### Google Cloud Run
```bash
# Build and push to GCR
docker build -t gcr.io/PROJECT_ID/ollama-chat:1.1.0 .
docker push gcr.io/PROJECT_ID/ollama-chat:1.1.0

# Deploy to Cloud Run
gcloud run deploy ollama-chat \
  --image gcr.io/PROJECT_ID/ollama-chat:1.1.0 \
  --platform managed \
  --region us-central1
```

#### Heroku
```bash
# Login to Heroku
heroku login

# Create app
heroku create ollama-chat-app

# Set environment variables
heroku config:set OLLAMA_API_URL=http://ollama:11434/api

# Deploy
git push heroku main
```

---

## Kubernetes Deployment

### Prerequisites
- kubectl configured for your cluster
- Helm 3+ (optional but recommended)
- Container registry access

### Basic Kubernetes Deployment

#### 1. Create Namespace
```bash
kubectl create namespace ollama-chat
kubectl set current-context --namespace=ollama-chat
```

#### 2. Create ConfigMap for Configuration
```bash
kubectl create configmap ollama-config \
  --from-file=config/.env.example \
  --namespace=ollama-chat
```

#### 3. Create Secrets for Sensitive Data
```bash
kubectl create secret generic ollama-secrets \
  --from-literal=api-key=your-api-key \
  --namespace=ollama-chat
```

#### 4. Deploy Services

**Ollama Service:**
```yaml
---
# ollama-deployment.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: ollama
  namespace: ollama-chat
spec:
  serviceName: ollama
  replicas: 1
  selector:
    matchLabels:
      app: ollama
  template:
    metadata:
      labels:
        app: ollama
    spec:
      containers:
      - name: ollama
        image: ollama/ollama:latest
        ports:
        - containerPort: 11434
        volumeMounts:
        - name: ollama-models
          mountPath: /root/.ollama
        resources:
          requests:
            memory: "4Gi"
            cpu: "2000m"
          limits:
            memory: "8Gi"
            cpu: "4000m"
        livenessProbe:
          httpGet:
            path: /api/tags
            port: 11434
          initialDelaySeconds: 30
          periodSeconds: 30
  volumeClaimTemplates:
  - metadata:
      name: ollama-models
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 50Gi
---
apiVersion: v1
kind: Service
metadata:
  name: ollama
  namespace: ollama-chat
spec:
  clusterIP: None
  selector:
    app: ollama
  ports:
  - port: 11434
    targetPort: 11434
```

**Chat App Deployment:**
```yaml
---
# chat-app-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chat-app
  namespace: ollama-chat
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chat-app
  template:
    metadata:
      labels:
        app: chat-app
    spec:
      containers:
      - name: chat-app
        image: ollama-chat:1.1.0
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
        env:
        - name: OLLAMA_API_URL
          value: http://ollama:11434/api
        - name: OLLAMA_MODEL
          value: tinyllama
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: chat-app
  namespace: ollama-chat
spec:
  type: LoadBalancer
  selector:
    app: chat-app
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
```

#### 5. Deploy with kubectl
```bash
# Deploy Ollama
kubectl apply -f ollama-deployment.yaml

# Wait for Ollama to be ready
kubectl wait --for=condition=ready pod -l app=ollama --timeout=300s

# Deploy Chat App
kubectl apply -f chat-app-deployment.yaml

# Check deployment status
kubectl get deployments
kubectl get pods
kubectl get services
```

#### 6. Access Application
```bash
# Get LoadBalancer IP
kubectl get service chat-app -o jsonpath='{.status.loadBalancer.ingress[0].ip}'

# Or use port-forward for local testing
kubectl port-forward service/chat-app 8000:80
```

### Helm Deployment

#### Install with Helm
```bash
# Add Helm repository
helm repo add ollama-chat https://charts.example.com

# Install release
helm install ollama-chat ollama-chat/chart \
  --namespace ollama-chat \
  --values values.yaml

# Upgrade release
helm upgrade ollama-chat ollama-chat/chart \
  --namespace ollama-chat \
  --values values.yaml
```

---

## Environment Configuration

### Environment Variables

```bash
# Ollama Configuration
OLLAMA_API_URL=http://ollama:11434/api
OLLAMA_MODEL=tinyllama
OLLAMA_TIMEOUT=300

# FastAPI Server
API_HOST=0.0.0.0
API_PORT=8000
API_LOG_LEVEL=info

# LLM Parameters
LLM_TEMPERATURE=0.7
LLM_TOP_P=0.9
LLM_TOP_K=40

# Health Check
HEALTH_CHECK_INTERVAL=5
HEALTH_CHECK_TIMEOUT=2

# Application Metadata
APP_NAME="Ollama Chat Application"
APP_VERSION=1.1.0
```

### Configuration Files

#### Development (.env.dev)
```
OLLAMA_API_URL=http://localhost:11434/api
API_LOG_LEVEL=debug
```

#### Staging (.env.staging)
```
OLLAMA_API_URL=http://ollama-staging:11434/api
API_LOG_LEVEL=info
```

#### Production (.env.prod)
```
OLLAMA_API_URL=http://ollama-prod:11434/api
API_LOG_LEVEL=warning
HEALTH_CHECK_TIMEOUT=10
```

---

## Monitoring & Logging

### Health Checks

```bash
# Application health
curl http://localhost:8000/api/health

# Ollama service health
curl http://localhost:11434/api/tags

# Available models
curl http://localhost:8000/api/models
```

### Logging

#### Docker Logs
```bash
# View logs
docker logs chat-app

# Follow logs
docker logs -f chat-app

# Last 100 lines
docker logs --tail 100 chat-app
```

#### Kubernetes Logs
```bash
# Pod logs
kubectl logs -f deployment/chat-app

# All pods in namespace
kubectl logs -f -n ollama-chat -l app=chat-app

# Previous pod logs (if crashed)
kubectl logs --previous pod/chat-app-xyz
```

### Monitoring Metrics

Prometheus metrics available at: `http://localhost:8000/metrics` (requires prometheus_client)

```bash
# Install prometheus client
pip install prometheus-client
```

---

## Troubleshooting

### Connection Issues

#### Ollama Connection Error
```bash
# Check Ollama service is running
docker-compose logs ollama

# Test connection
curl http://ollama:11434/api/tags

# Verify network
docker network inspect app-network
```

#### Application Won't Start
```bash
# Check logs
docker logs chat-app

# Check port availability
netstat -tulpn | grep 8000

# Check dependencies
docker-compose up ollama --wait
```

### Performance Issues

#### High Memory Usage
```bash
# Check memory allocation
docker stats

# Reduce model size (switch from Llama2 to TinyLLaMA)
docker-compose down
# Edit docker-compose.yml: OLLAMA_MODEL=tinyllama
docker-compose up
```

#### Slow Responses
```bash
# Check Ollama logs
docker logs ollama

# Monitor GPU (if available)
nvidia-smi

# Increase resources in docker-compose.yml
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Connection refused | Ollama not running | Start Ollama service |
| Port already in use | Port 8000 in use | Change port in config |
| Out of memory | Insufficient RAM | Reduce model size |
| Model not found | Model not downloaded | Run `ollama pull tinyllama` |

---

## Scaling Considerations

### Horizontal Scaling
- Stateless chat app: Add replicas via `replicas: N` in K8s
- Load balance with Nginx/HAProxy
- Session affinity: Not required (stateless)

### Vertical Scaling
- Increase memory/CPU allocations
- Switch to larger model (Llama2, Mistral)
- Use GPU acceleration (NVIDIA GPU operator)

### Cost Optimization
- Use TinyLLaMA for development
- Implement caching for common queries
- Use spot instances for non-critical workloads

---

## Security Considerations

- ✅ Run as non-root user (Dockerfile: `appuser`)
- ✅ Implement HTTPS with reverse proxy (Nginx)
- ✅ Use secrets management (K8s Secrets, Vault)
- ✅ Network policies (K8s NetworkPolicy)
- ✅ Resource limits (prevent DoS)
- ✅ Regular updates and patching

---

## Summary

| Deployment | Pros | Cons | Best For |
|-----------|------|------|----------|
| **Local** | Simple, fast iteration | Single machine only | Development |
| **Docker** | Reproducible, isolated | Single host limit | Staging, small prod |
| **Kubernetes** | Scalable, resilient | Complex setup | Large scale prod |

---

**For questions or issues, see [CONTRIBUTING.md](../CONTRIBUTING.md)**
