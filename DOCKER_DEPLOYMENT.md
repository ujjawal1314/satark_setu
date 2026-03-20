# 🐳 Docker Deployment Guide

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Access:**
- Dashboard: http://localhost:8501
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Docker Only

```bash
# Build image
docker build -t satarksetu-fusion .

# Run dashboard
docker run -p 8501:8501 --name satarksetu-dashboard satarksetu-fusion

# Run backend
docker run -p 8000:8000 --name satarksetu-backend \
  --entrypoint python satarksetu-fusion backend.py
```

---

## Configuration

### Environment Variables

Create `.env` file:
```bash
GEMINI_API_KEY=your_api_key_here
```

### With Docker Compose

The `.env` file is automatically loaded.

### With Docker Run

```bash
docker run -p 8501:8501 \
  -e GEMINI_API_KEY=your_key_here \
  satarksetu-fusion
```

---

## Data Management

### Option 1: Generate in Container (Default)

Data is generated when container starts.

### Option 2: Mount Existing Data

```bash
docker run -p 8501:8501 \
  -v $(pwd)/cyber_events.csv:/app/cyber_events.csv \
  -v $(pwd)/transactions.csv:/app/transactions.csv \
  satarksetu-fusion
```

### Option 3: Persistent Volume

```yaml
# In docker-compose.yml
volumes:
  - satarksetu-data:/app/data
```

---

## Production Deployment

### 1. Build Optimized Image

```bash
docker build -t satarksetu-fusion:prod \
  --target application \
  --build-arg PYTHON_VERSION=3.13-slim .
```

### 2. Security Hardening

```dockerfile
# Run as non-root user
RUN useradd -m -u 1000 satarksetu
USER satarksetu
```

### 3. Resource Limits

```yaml
# docker-compose.yml
services:
  dashboard:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### 4. Health Checks

Already configured in Dockerfile and docker-compose.yml

### 5. Logging

```yaml
services:
  dashboard:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## Kubernetes Deployment

### Basic Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: satarksetu-dashboard
spec:
  replicas: 3
  selector:
    matchLabels:
      app: satarksetu
  template:
    metadata:
      labels:
        app: satarksetu
    spec:
      containers:
      - name: dashboard
        image: satarksetu-fusion:latest
        ports:
        - containerPort: 8501
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: satarksetu-secrets
              key: gemini-api-key
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2"
---
apiVersion: v1
kind: Service
metadata:
  name: satarksetu-service
spec:
  selector:
    app: satarksetu
  ports:
  - port: 80
    targetPort: 8501
  type: LoadBalancer
```

---

## Cloud Deployment

### AWS ECS

```bash
# Push to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

docker tag satarksetu-fusion:latest <account>.dkr.ecr.us-east-1.amazonaws.com/satarksetu:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/satarksetu:latest

# Create ECS task definition and service
```

### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/satarksetu

# Deploy
gcloud run deploy satarksetu \
  --image gcr.io/PROJECT_ID/satarksetu \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Azure Container Instances

```bash
# Push to ACR
az acr build --registry myregistry --image satarksetu:latest .

# Deploy
az container create \
  --resource-group myResourceGroup \
  --name satarksetu \
  --image myregistry.azurecr.io/satarksetu:latest \
  --dns-name-label satarksetu \
  --ports 8501
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs satarksetu-dashboard

# Interactive shell
docker exec -it satarksetu-dashboard /bin/bash
```

### Port Already in Use

```bash
# Use different port
docker run -p 8502:8501 satarksetu-fusion
```

### Data Not Persisting

```bash
# Use named volume
docker volume create satarksetu-data
docker run -v satarksetu-data:/app/data satarksetu-fusion
```

### Memory Issues

```bash
# Increase memory limit
docker run --memory=4g satarksetu-fusion
```

---

## Monitoring

### Prometheus Metrics

Add to Dockerfile:
```dockerfile
RUN pip install prometheus-client
```

### Grafana Dashboard

Import dashboard JSON for Streamlit metrics.

### Health Checks

```bash
# Check dashboard health
curl http://localhost:8501/_stcore/health

# Check backend health
curl http://localhost:8000/
```

---

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml
services:
  dashboard:
    deploy:
      replicas: 3
```

### Load Balancing

Use nginx or cloud load balancer:

```nginx
upstream satarksetu {
    server dashboard1:8501;
    server dashboard2:8501;
    server dashboard3:8501;
}

server {
    listen 80;
    location / {
        proxy_pass http://satarksetu;
    }
}
```

---

## Best Practices

1. **Use multi-stage builds** (already implemented)
2. **Run as non-root user** (add to Dockerfile)
3. **Scan for vulnerabilities**: `docker scan satarksetu-fusion`
4. **Use specific tags**: `satarksetu-fusion:v1.0.0` not `:latest`
5. **Implement health checks** (already done)
6. **Set resource limits** (see examples above)
7. **Use secrets management** (not .env in production)
8. **Enable logging** (configure log drivers)
9. **Regular updates**: Rebuild with latest base images
10. **Monitor performance**: Use APM tools

---

## Commands Reference

```bash
# Build
docker build -t satarksetu-fusion .

# Run dashboard
docker run -d -p 8501:8501 --name dashboard satarksetu-fusion

# Run backend
docker run -d -p 8000:8000 --name backend \
  --entrypoint python satarksetu-fusion backend.py

# View logs
docker logs -f dashboard

# Stop
docker stop dashboard backend

# Remove
docker rm dashboard backend

# Clean up
docker system prune -a

# With compose
docker-compose up -d
docker-compose down
docker-compose logs -f
docker-compose ps
docker-compose restart
```

---

## Next Steps

1. Test locally with Docker
2. Push to container registry
3. Deploy to staging environment
4. Configure monitoring and logging
5. Set up CI/CD pipeline
6. Deploy to production
7. Configure auto-scaling
8. Set up backup and disaster recovery

---

**Status:** Docker configuration ready for deployment!

See `Dockerfile`, `docker-compose.yml`, and `.dockerignore` for implementation details.
