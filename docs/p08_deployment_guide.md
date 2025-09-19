# P08. 배포 가이드 (Deployment Guide)

## 🚀 배포 개요

이 문서는 카카오 알림톡 템플릿 자동 생성 AI 서비스를 다양한 환경에 배포하는 방법을 안내합니다. 개발, 스테이징, 프로덕션 환경별 배포 전략과 모범 사례를 다룹니다.

## 📋 배포 환경별 요구사항

### 개발 환경 (Development)
- **목적**: 로컬 개발 및 테스트
- **리소스**: 최소 2GB RAM, 2 CPU 코어
- **보안**: 기본 보안 설정
- **모니터링**: 기본 로깅

### 스테이징 환경 (Staging)
- **목적**: 프로덕션 배포 전 최종 테스트
- **리소스**: 4GB RAM, 2 CPU 코어
- **보안**: 프로덕션 수준 보안
- **모니터링**: 상세 로깅 및 메트릭

### 프로덕션 환경 (Production)
- **목적**: 실제 서비스 운영
- **리소스**: 8GB+ RAM, 4+ CPU 코어
- **보안**: 최고 수준 보안
- **모니터링**: 실시간 모니터링 및 알럿

## 🐳 Docker 배포

### 1. Dockerfile 최적화

#### 멀티스테이지 빌드 Dockerfile
```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder stage
COPY --from=builder /root/.local /home/app/.local

# Make sure scripts in .local are usable
ENV PATH=/home/app/.local/bin:$PATH

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=app:app src/ ./src/
COPY --chown=app:app data/ ./data/
COPY --chown=app:app .env.example ./.env

# Create necessary directories
RUN mkdir -p logs chroma_db && chown -R app:app logs chroma_db

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set environment variables
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

# Run application
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### .dockerignore
```dockerignore
.git
.gitignore
README.md
Dockerfile
.dockerignore
.pytest_cache
.coverage
htmlcov/
.tox
.env
.venv
venv/
.vscode
.idea
__pycache__
*.pyc
*.pyo
*.pyd
.pytest_cache
node_modules
npm-debug.log*
.nyc_output
*.log
logs/
chroma_db/
tests/
docs/
```

### 2. Docker Compose 설정

#### docker-compose.yml (개발용)
```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=DEBUG
    env_file:
      - .env
    volumes:
      - ./src:/app/src
      - ./data:/app/data
      - ./logs:/app/logs
      - ./chroma_db:/app/chroma_db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  monitoring:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    restart: unless-stopped

volumes:
  redis_data:
```

#### docker-compose.prod.yml (프로덕션용)
```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
    env_file:
      - .env.prod
    volumes:
      - ./logs:/app/logs
      - ./chroma_db:/app/chroma_db
    networks:
      - app_network
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - app
    networks:
      - app_network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - app_network
    restart: unless-stopped

  postgresql:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=${DB_NAME}
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - app_network
    restart: unless-stopped

networks:
  app_network:
    driver: bridge

volumes:
  redis_data:
  postgres_data:
```

### 3. 환경별 설정 파일

#### .env.development
```env
ENVIRONMENT=development
LOG_LEVEL=DEBUG
API_HOST=0.0.0.0
API_PORT=8000

# API Keys
ANTHROPIC_API_KEY=your-dev-api-key
OPENAI_API_KEY=your-dev-openai-key

# Database
DATABASE_URL=sqlite:///./dev.db
VECTOR_DB_PATH=./chroma_db

# Cache
REDIS_URL=redis://localhost:6379
ENABLE_CACHING=true
CACHE_TTL_MINUTES=30

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100

# Debug
DEBUG=true
ENABLE_PROFILING=true
```

#### .env.production
```env
ENVIRONMENT=production
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# API Keys (use secrets management)
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
OPENAI_API_KEY=${OPENAI_API_KEY}

# Database
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgresql:5432/${DB_NAME}
VECTOR_DB_PATH=./chroma_db

# Cache
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
ENABLE_CACHING=true
CACHE_TTL_MINUTES=60

# Rate Limiting
RATE_LIMIT_PER_MINUTE=50

# Security
SECRET_KEY=${SECRET_KEY}
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Monitoring
SENTRY_DSN=${SENTRY_DSN}
```

## ☁️ 클라우드 배포

### 1. AWS 배포

#### ECS (Elastic Container Service) 배포

**Task Definition (task-definition.json)**:
```json
{
  "family": "kakao-template-service",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::YOUR_ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::YOUR_ACCOUNT:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "kakao-template-app",
      "image": "YOUR_ACCOUNT.dkr.ecr.YOUR_REGION.amazonaws.com/kakao-template:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "ANTHROPIC_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:YOUR_REGION:YOUR_ACCOUNT:secret:anthropic-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/kakao-template-service",
          "awslogs-region": "YOUR_REGION",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

**ECS 서비스 생성**:
```bash
# ECR 리포지토리 생성
aws ecr create-repository --repository-name kakao-template

# 이미지 빌드 및 푸시
docker build -t kakao-template .
docker tag kakao-template:latest YOUR_ACCOUNT.dkr.ecr.YOUR_REGION.amazonaws.com/kakao-template:latest
docker push YOUR_ACCOUNT.dkr.ecr.YOUR_REGION.amazonaws.com/kakao-template:latest

# 태스크 정의 등록
aws ecs register-task-definition --cli-input-json file://task-definition.json

# 서비스 생성
aws ecs create-service \
  --cluster your-cluster \
  --service-name kakao-template-service \
  --task-definition kakao-template-service:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
```

#### Lambda 배포 (서버리스)

**serverless.yml**:
```yaml
service: kakao-template-serverless

provider:
  name: aws
  runtime: python3.11
  region: us-east-1
  environment:
    ANTHROPIC_API_KEY: ${ssm:/kakao-template/anthropic-api-key}
    ENVIRONMENT: production
  iamRoleStatements:
    - Effect: Allow
      Action:
        - secretsmanager:GetSecretValue
      Resource: "*"

functions:
  api:
    handler: src.lambda_handler.handler
    timeout: 30
    memorySize: 1024
    events:
      - http:
          path: /{proxy+}
          method: ANY
          cors: true
      - http:
          path: /
          method: ANY
          cors: true

plugins:
  - serverless-python-requirements
  - serverless-plugin-warmup

custom:
  pythonRequirements:
    dockerizePip: true
    slim: true
  warmup:
    enabled: true
    events:
      - schedule: rate(5 minutes)
```

**Lambda Handler**:
```python
# src/lambda_handler.py
from mangum import Mangum
from src.api.main import app

handler = Mangum(app, lifespan="off")
```

### 2. Google Cloud Platform 배포

#### Cloud Run 배포

**cloudbuild.yaml**:
```yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/kakao-template:$BUILD_ID', '.']

  # Push the container image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/kakao-template:$BUILD_ID']

  # Deploy container image to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
    - 'run'
    - 'deploy'
    - 'kakao-template'
    - '--image'
    - 'gcr.io/$PROJECT_ID/kakao-template:$BUILD_ID'
    - '--region'
    - 'us-central1'
    - '--platform'
    - 'managed'
    - '--allow-unauthenticated'
    - '--memory'
    - '2Gi'
    - '--cpu'
    - '2'
    - '--set-env-vars'
    - 'ENVIRONMENT=production'

images:
  - 'gcr.io/$PROJECT_ID/kakao-template:$BUILD_ID'
```

**배포 명령어**:
```bash
# 프로젝트 설정
gcloud config set project YOUR_PROJECT_ID

# 빌드 및 배포
gcloud builds submit --config cloudbuild.yaml

# 환경 변수 설정
gcloud run services update kakao-template \
  --set-env-vars ANTHROPIC_API_KEY=your-api-key \
  --region us-central1
```

### 3. Microsoft Azure 배포

#### Container Instances 배포

**azure-deploy.yml** (GitHub Actions):
```yaml
name: Deploy to Azure

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Login to Azure
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}

    - name: Build and push Docker image
      run: |
        az acr build \
          --registry ${{ secrets.REGISTRY_NAME }} \
          --image kakao-template:${{ github.sha }} \
          .

    - name: Deploy to Container Instances
      uses: azure/aci-deploy@v1
      with:
        resource-group: kakao-template-rg
        dns-name-label: kakao-template-${{ github.sha }}
        image: ${{ secrets.REGISTRY_NAME }}.azurecr.io/kakao-template:${{ github.sha }}
        registry-login-server: ${{ secrets.REGISTRY_NAME }}.azurecr.io
        registry-username: ${{ secrets.REGISTRY_USERNAME }}
        registry-password: ${{ secrets.REGISTRY_PASSWORD }}
        name: kakao-template-ci
        location: 'east us'
        cpu: 2
        memory: 4
        environment-variables: |
          ENVIRONMENT=production
        secure-environment-variables: |
          ANTHROPIC_API_KEY=${{ secrets.ANTHROPIC_API_KEY }}
```

## 🏗 Kubernetes 배포

### 1. Kubernetes 매니페스트

#### deployment.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kakao-template-deployment
  labels:
    app: kakao-template
spec:
  replicas: 3
  selector:
    matchLabels:
      app: kakao-template
  template:
    metadata:
      labels:
        app: kakao-template
    spec:
      containers:
      - name: kakao-template
        image: kakao-template:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: anthropic-api-key
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: chroma-storage
          mountPath: /app/chroma_db
        - name: logs-storage
          mountPath: /app/logs
      volumes:
      - name: chroma-storage
        persistentVolumeClaim:
          claimName: chroma-pvc
      - name: logs-storage
        persistentVolumeClaim:
          claimName: logs-pvc
```

#### service.yaml
```yaml
apiVersion: v1
kind: Service
metadata:
  name: kakao-template-service
spec:
  selector:
    app: kakao-template
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
```

#### ingress.yaml
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: kakao-template-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - api.yourservice.com
    secretName: kakao-template-tls
  rules:
  - host: api.yourservice.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: kakao-template-service
            port:
              number: 80
```

#### configmap.yaml
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kakao-template-config
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
  RATE_LIMIT_PER_MINUTE: "50"
```

#### secret.yaml
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-secrets
type: Opaque
data:
  anthropic-api-key: <base64-encoded-api-key>
  openai-api-key: <base64-encoded-openai-key>
  secret-key: <base64-encoded-secret-key>
```

### 2. Helm 차트

#### Chart.yaml
```yaml
apiVersion: v2
name: kakao-template
description: KakaoTalk Template Generation AI Service
type: application
version: 1.0.0
appVersion: "1.0.0"

dependencies:
  - name: redis
    version: 17.11.3
    repository: https://charts.bitnami.com/bitnami
    condition: redis.enabled
  - name: postgresql
    version: 12.6.6
    repository: https://charts.bitnami.com/bitnami
    condition: postgresql.enabled
```

#### values.yaml
```yaml
replicaCount: 3

image:
  repository: kakao-template
  pullPolicy: IfNotPresent
  tag: "latest"

service:
  type: LoadBalancer
  port: 80
  targetPort: 8000

ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: api.yourservice.com
      paths:
        - path: /
          pathType: ImplementationSpecific
  tls:
    - secretName: kakao-template-tls
      hosts:
        - api.yourservice.com

resources:
  limits:
    cpu: 1000m
    memory: 2Gi
  requests:
    cpu: 500m
    memory: 1Gi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

persistence:
  enabled: true
  storageClass: "gp2"
  size: 10Gi

redis:
  enabled: true
  auth:
    enabled: true

postgresql:
  enabled: true
  auth:
    postgresPassword: "your-password"
    database: "kakao_template"

secrets:
  anthropicApiKey: ""
  openaiApiKey: ""
  secretKey: ""
```

**배포 명령어**:
```bash
# Helm 차트 설치
helm install kakao-template ./helm-chart -f values.production.yaml

# 업그레이드
helm upgrade kakao-template ./helm-chart -f values.production.yaml

# 상태 확인
helm status kakao-template
kubectl get pods -l app=kakao-template
```

## 🔄 CI/CD 파이프라인

### GitHub Actions 워크플로우

#### .github/workflows/deploy.yml
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha

    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}

  deploy-staging:
    needs: build
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    environment: staging

    steps:
    - name: Deploy to staging
      run: |
        echo "Deploying to staging environment..."
        # 스테이징 배포 스크립트 실행

  deploy-production:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production

    steps:
    - name: Deploy to production
      run: |
        echo "Deploying to production environment..."
        # 프로덕션 배포 스크립트 실행
```

### GitLab CI/CD

#### .gitlab-ci.yml
```yaml
stages:
  - test
  - build
  - deploy

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: "/certs"

before_script:
  - docker info

test:
  stage: test
  image: python:3.11
  services:
    - docker:dind
  script:
    - pip install -r requirements.txt
    - pip install -r requirements-dev.txt
    - pytest tests/ --cov=src
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  only:
    - main
    - develop

deploy-staging:
  stage: deploy
  image: alpine:latest
  before_script:
    - apk add --no-cache curl
  script:
    - echo "Deploying to staging..."
    - curl -X POST "$STAGING_WEBHOOK_URL"
  only:
    - develop
  environment:
    name: staging
    url: https://staging.yourservice.com

deploy-production:
  stage: deploy
  image: alpine:latest
  before_script:
    - apk add --no-cache curl
  script:
    - echo "Deploying to production..."
    - curl -X POST "$PRODUCTION_WEBHOOK_URL"
  only:
    - main
  environment:
    name: production
    url: https://api.yourservice.com
  when: manual
```

## 🔧 배포 스크립트

### 자동 배포 스크립트

#### deploy.sh
```bash
#!/bin/bash

set -e

# 설정
ENVIRONMENT=${1:-staging}
IMAGE_TAG=${2:-latest}
CONFIG_FILE="config/${ENVIRONMENT}.env"

echo "🚀 Deploying to ${ENVIRONMENT} environment..."

# 환경 확인
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# 이전 컨테이너 정리
echo "🧹 Cleaning up previous containers..."
docker-compose -f docker-compose.${ENVIRONMENT}.yml down

# 이미지 풀
echo "📥 Pulling latest images..."
docker-compose -f docker-compose.${ENVIRONMENT}.yml pull

# 새 컨테이너 시작
echo "🏃 Starting new containers..."
docker-compose -f docker-compose.${ENVIRONMENT}.yml up -d

# 헬스체크
echo "🔍 Performing health check..."
sleep 10

for i in {1..30}; do
    if curl -f http://localhost:8000/health; then
        echo "✅ Deployment successful!"
        break
    fi

    if [ $i -eq 30 ]; then
        echo "❌ Health check failed"
        docker-compose -f docker-compose.${ENVIRONMENT}.yml logs
        exit 1
    fi

    echo "⏳ Waiting for service to be ready... (${i}/30)"
    sleep 2
done

echo "🎉 Deployment completed successfully!"
```

#### 롤백 스크립트 (rollback.sh)
```bash
#!/bin/bash

set -e

ENVIRONMENT=${1:-staging}
PREVIOUS_TAG=${2}

echo "🔄 Rolling back ${ENVIRONMENT} environment..."

if [ -z "$PREVIOUS_TAG" ]; then
    echo "❌ Previous tag not specified"
    exit 1
fi

# 이전 버전으로 롤백
docker-compose -f docker-compose.${ENVIRONMENT}.yml down
docker tag kakao-template:${PREVIOUS_TAG} kakao-template:latest
docker-compose -f docker-compose.${ENVIRONMENT}.yml up -d

# 헬스체크
sleep 10
if curl -f http://localhost:8000/health; then
    echo "✅ Rollback successful!"
else
    echo "❌ Rollback failed"
    exit 1
fi
```

## 📊 모니터링 및 로깅

### 1. Prometheus 메트릭

#### prometheus.yml
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'kakao-template'
    static_configs:
      - targets: ['app:8000']
    metrics_path: /metrics
    scrape_interval: 5s
```

### 2. Grafana 대시보드

#### 메트릭 대시보드 설정
- **응답 시간**: 평균, P95, P99 응답 시간
- **처리량**: 초당 요청 수 (RPS)
- **에러율**: 4xx, 5xx 에러 비율
- **리소스 사용량**: CPU, 메모리, 디스크

### 3. 로그 집계

#### ELK Stack 설정
```yaml
# docker-compose.logging.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.8.0
    volumes:
      - ./logstash/config:/usr/share/logstash/pipeline

  kibana:
    image: docker.elastic.co/kibana/kibana:8.8.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200

volumes:
  elasticsearch_data:
```

## 🔒 보안 설정

### 1. TLS/SSL 설정

#### nginx.conf
```nginx
server {
    listen 80;
    server_name api.yourservice.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourservice.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256;

    location / {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. 보안 헤더

#### security_middleware.py
```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # 보안 헤더 추가
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response
```

---

**📅 작성일**: 2024년 9월 19일
**✍️ 작성자**: Final Team 3 AI
**📄 문서 버전**: 1.0
**🔄 최종 수정**: 2024년 9월 19일