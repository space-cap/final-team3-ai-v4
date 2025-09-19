# 배포 가이드

## 개요

카카오 알림톡 템플릿 자동 생성 AI 서비스의 배포 및 운영 가이드입니다.

## 시스템 요구사항

### 최소 요구사항

- **OS**: Ubuntu 20.04 LTS 이상 또는 Windows 10 이상
- **Python**: 3.11 이상
- **메모리**: 4GB RAM 이상
- **저장공간**: 10GB 이상
- **네트워크**: 인터넷 연결 (API 호출용)

### 권장 요구사항

- **OS**: Ubuntu 22.04 LTS
- **Python**: 3.11
- **메모리**: 8GB RAM 이상
- **저장공간**: 20GB 이상 (SSD 권장)
- **CPU**: 4코어 이상

## 설치 가이드

### 1. 소스 코드 준비

```bash
# Git 클론 (실제 환경에서는 릴리즈 버전 사용)
git clone <repository_url>
cd final-team3-ai-v4

# 또는 릴리즈 아카이브 다운로드 및 압축 해제
wget <release_url>
unzip final-team3-ai-v4-v1.0.0.zip
cd final-team3-ai-v4
```

### 2. Python 환경 설정

```bash
# Python 3.11 설치 확인
python3.11 --version

# 가상환경 생성
python3.11 -m venv .venv

# 가상환경 활성화 (Linux/Mac)
source .venv/bin/activate

# 가상환경 활성화 (Windows)
.venv\Scripts\activate

# pip 업그레이드
pip install --upgrade pip
```

### 3. 의존성 설치

```bash
# 패키지 설치
pip install -r requirements.txt

# 설치 확인
pip list
```

### 4. 환경 설정

```bash
# 환경 변수 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env
```

**.env 파일 설정 예시:**

```bash
# API Keys
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
OPENAI_API_KEY=sk-your-openai-key-here  # 선택사항

# 환경 설정
ENVIRONMENT=production
LOG_LEVEL=INFO

# API 설정
API_HOST=0.0.0.0
API_PORT=8000

# 워크플로우 설정
MAX_ITERATIONS=3
MIN_COMPLIANCE_SCORE=80.0
ENABLE_AUTO_REFINEMENT=true
STRICT_COMPLIANCE=true

# 데이터베이스 설정
VECTOR_DB_PATH=/app/data/chroma_db
TEMPLATE_DATA_PATH=/app/data/kakao_template_vectordb_data.json
POLICY_DATA_PATH=/app/data/cleaned_policies
```

### 5. 디렉토리 구조 설정

```bash
# 필요한 디렉토리 생성
mkdir -p logs
mkdir -p data/chroma_db

# 권한 설정 (Linux)
chmod 755 logs
chmod 755 data
```

### 6. 데이터 초기화

```bash
# 시스템 테스트 실행
python simple_test.py

# 벡터 데이터베이스 초기화 (자동으로 수행됨)
# 첫 실행 시 정책 문서가 자동으로 로드됩니다
```

## 운영 환경 배포

### 1. Systemd 서비스 설정 (Linux)

**/etc/systemd/system/kakao-template-service.service:**

```ini
[Unit]
Description=KakaoTalk Template Generation Service
After=network.target

[Service]
Type=exec
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/kakao-template-service
Environment=PATH=/opt/kakao-template-service/.venv/bin
ExecStart=/opt/kakao-template-service/.venv/bin/python run_server.py
Restart=always
RestartSec=3

# 로그 설정
StandardOutput=journal
StandardError=journal
SyslogIdentifier=kakao-template-service

# 보안 설정
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/kakao-template-service/logs
ReadWritePaths=/opt/kakao-template-service/data

[Install]
WantedBy=multi-user.target
```

**서비스 등록 및 실행:**

```bash
# 서비스 파일 복사
sudo cp kakao-template-service.service /etc/systemd/system/

# systemd 리로드
sudo systemctl daemon-reload

# 서비스 활성화
sudo systemctl enable kakao-template-service

# 서비스 시작
sudo systemctl start kakao-template-service

# 서비스 상태 확인
sudo systemctl status kakao-template-service

# 로그 확인
sudo journalctl -u kakao-template-service -f
```

### 2. Nginx 설정 (리버스 프록시)

**/etc/nginx/sites-available/kakao-template-service:**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 보안 헤더
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    # 요청 크기 제한
    client_max_body_size 10M;

    # 프록시 설정
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 타임아웃 설정
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 정적 파일 캐싱
    location /static/ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 헬스체크 엔드포인트
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:8000/health;
    }

    # 로그 설정
    access_log /var/log/nginx/kakao-template-service.access.log;
    error_log /var/log/nginx/kakao-template-service.error.log;
}
```

**Nginx 설정 활성화:**

```bash
# 설정 파일 활성화
sudo ln -s /etc/nginx/sites-available/kakao-template-service /etc/nginx/sites-enabled/

# 설정 테스트
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx
```

### 3. Docker 배포

**Dockerfile:**

```dockerfile
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# 권한 설정
RUN chmod +x run_server.py

# 포트 노출
EXPOSE 8000

# 볼륨 설정
VOLUME ["/app/logs", "/app/data/chroma_db"]

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 사용자 생성 및 전환
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 서비스 실행
CMD ["python", "run_server.py"]
```

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  kakao-template-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - kakao-template-service
    restart: unless-stopped
```

**Docker 배포 실행:**

```bash
# 이미지 빌드
docker-compose build

# 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 상태 확인
docker-compose ps
```

## 모니터링 설정

### 1. 로그 모니터링

**Logrotate 설정 (/etc/logrotate.d/kakao-template-service):**

```
/opt/kakao-template-service/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
    postrotate
        systemctl reload kakao-template-service
    endscript
}
```

### 2. 시스템 모니터링

**모니터링 스크립트 (monitor.sh):**

```bash
#!/bin/bash

# 서비스 상태 확인
check_service() {
    if systemctl is-active --quiet kakao-template-service; then
        echo "✓ Service is running"
    else
        echo "✗ Service is down"
        # 알림 전송 (예: Slack, 이메일 등)
    fi
}

# API 헬스체크
check_api() {
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
    if [ "$response" = "200" ]; then
        echo "✓ API is healthy"
    else
        echo "✗ API is unhealthy (HTTP $response)"
    fi
}

# 디스크 사용량 확인
check_disk() {
    usage=$(df /opt/kakao-template-service | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$usage" -gt 80 ]; then
        echo "⚠ Disk usage is high: ${usage}%"
    else
        echo "✓ Disk usage is normal: ${usage}%"
    fi
}

# 실행
echo "=== KakaoTalk Template Service Monitor ==="
echo "$(date)"
check_service
check_api
check_disk
echo ""
```

**Cron 작업 설정:**

```bash
# crontab 편집
crontab -e

# 5분마다 모니터링 실행
*/5 * * * * /opt/kakao-template-service/monitor.sh >> /var/log/kakao-template-monitor.log 2>&1
```

## 백업 및 복구

### 1. 데이터 백업

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/kakao-template-service/$(date +%Y%m%d_%H%M%S)"
SOURCE_DIR="/opt/kakao-template-service"

mkdir -p "$BACKUP_DIR"

# 벡터 데이터베이스 백업
tar -czf "$BACKUP_DIR/chroma_db.tar.gz" -C "$SOURCE_DIR" data/chroma_db

# 로그 백업
tar -czf "$BACKUP_DIR/logs.tar.gz" -C "$SOURCE_DIR" logs

# 설정 파일 백업
cp "$SOURCE_DIR/.env" "$BACKUP_DIR/"
cp "$SOURCE_DIR/requirements.txt" "$BACKUP_DIR/"

echo "Backup completed: $BACKUP_DIR"
```

### 2. 복구 절차

```bash
#!/bin/bash
# restore.sh

BACKUP_DIR="$1"
TARGET_DIR="/opt/kakao-template-service"

if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: $0 <backup_directory>"
    exit 1
fi

# 서비스 중지
systemctl stop kakao-template-service

# 데이터 복구
tar -xzf "$BACKUP_DIR/chroma_db.tar.gz" -C "$TARGET_DIR"
tar -xzf "$BACKUP_DIR/logs.tar.gz" -C "$TARGET_DIR"

# 설정 파일 복구
cp "$BACKUP_DIR/.env" "$TARGET_DIR/"

# 권한 복구
chown -R ubuntu:ubuntu "$TARGET_DIR"

# 서비스 시작
systemctl start kakao-template-service

echo "Restore completed from: $BACKUP_DIR"
```

## 성능 최적화

### 1. 환경 변수 최적화

```bash
# .env 파일에 추가
ENABLE_CACHING=true
CACHE_TTL_MINUTES=60
RATE_LIMIT_PER_MINUTE=100

# 워크플로우 최적화
MAX_ITERATIONS=2  # 응답 속도 향상
STRICT_COMPLIANCE=false  # 성능 향상
```

### 2. 시스템 최적화

```bash
# /etc/sysctl.conf에 추가
net.core.somaxconn = 65536
net.ipv4.tcp_max_syn_backlog = 65536
net.ipv4.ip_local_port_range = 1024 65000

# 적용
sysctl -p
```

## 보안 설정

### 1. 방화벽 설정

```bash
# UFW 활성화
ufw enable

# 필요한 포트만 허용
ufw allow 22/tcp  # SSH
ufw allow 80/tcp  # HTTP
ufw allow 443/tcp # HTTPS

# 내부 통신만 허용 (옵션)
ufw allow from 10.0.0.0/8 to any port 8000
```

### 2. SSL/TLS 설정

```bash
# Let's Encrypt 인증서 설치
certbot --nginx -d your-domain.com

# 자동 갱신 설정
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

## 트러블슈팅

### 일반적인 문제 해결

1. **서비스가 시작되지 않는 경우:**
   ```bash
   # 로그 확인
   journalctl -u kakao-template-service -n 50

   # 설정 검증
   python simple_test.py
   ```

2. **API 응답이 느린 경우:**
   ```bash
   # 리소스 사용량 확인
   htop

   # 로그 분석
   tail -f logs/app.log | grep "slow"
   ```

3. **메모리 부족 오류:**
   ```bash
   # 메모리 사용량 확인
   free -h

   # 프로세스 재시작
   systemctl restart kakao-template-service
   ```

## 업데이트 절차

### 1. 백업 생성

```bash
./backup.sh
```

### 2. 새 버전 배포

```bash
# 서비스 중지
systemctl stop kakao-template-service

# 코드 업데이트
git pull origin main

# 의존성 업데이트
pip install -r requirements.txt

# 테스트 실행
python simple_test.py

# 서비스 시작
systemctl start kakao-template-service
```

### 3. 검증

```bash
# API 상태 확인
curl http://localhost:8000/health

# 로그 모니터링
tail -f logs/app.log
```

이 가이드를 따라 안정적이고 확장 가능한 서비스를 배포할 수 있습니다.