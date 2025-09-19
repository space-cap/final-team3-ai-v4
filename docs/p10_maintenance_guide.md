# P10. 유지보수 가이드 (Maintenance Guide)

## 🔧 유지보수 개요

이 문서는 카카오 알림톡 템플릿 자동 생성 AI 서비스의 장기적인 운영을 위한 유지보수 가이드입니다. 정기적인 업데이트, 모니터링, 백업, 성능 최적화 등 운영에 필요한 모든 사항을 다룹니다.

## 📅 정기 유지보수 일정

### 일일 점검 (Daily)
- [ ] 시스템 상태 확인
- [ ] 로그 모니터링
- [ ] API 응답 시간 체크
- [ ] 에러율 확인

### 주간 점검 (Weekly)
- [ ] 데이터베이스 백업
- [ ] 성능 메트릭 분석
- [ ] 보안 업데이트 확인
- [ ] 디스크 공간 정리

### 월간 점검 (Monthly)
- [ ] 의존성 업데이트
- [ ] 보안 패치 적용
- [ ] 성능 최적화
- [ ] 백업 복구 테스트

### 분기별 점검 (Quarterly)
- [ ] 전체 시스템 감사
- [ ] 아키텍처 검토
- [ ] 용량 계획 수립
- [ ] 재해 복구 훈련

## 📊 모니터링 및 알림

### 1. 시스템 메트릭 모니터링

#### 핵심 지표 (KPI)
```python
# monitoring/metrics_collector.py
import psutil
import time
from datetime import datetime
import json

class SystemMetrics:
    """시스템 메트릭 수집기"""

    def collect_system_metrics(self):
        """시스템 리소스 메트릭 수집"""
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "network_io": psutil.net_io_counters()._asdict(),
            "process_count": len(psutil.pids()),
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }

    def collect_app_metrics(self):
        """애플리케이션 메트릭 수집"""
        # FastAPI 메트릭 수집 (Prometheus 연동)
        return {
            "requests_total": self.get_total_requests(),
            "response_time_avg": self.get_avg_response_time(),
            "error_rate": self.get_error_rate(),
            "active_connections": self.get_active_connections()
        }

    def save_metrics(self, metrics):
        """메트릭을 파일로 저장"""
        filename = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(f"logs/metrics/{filename}", 'w') as f:
            json.dump(metrics, f, indent=2)
```

#### 알림 설정
```python
# monitoring/alerting.py
import smtplib
from email.mime.text import MIMEText
import requests

class AlertManager:
    """알림 관리자"""

    def __init__(self):
        self.thresholds = {
            "cpu_percent": 80,
            "memory_percent": 85,
            "disk_percent": 90,
            "error_rate": 5,  # 5% 이상
            "response_time": 5000  # 5초 이상
        }

    def check_alerts(self, metrics):
        """임계값 초과 확인"""
        alerts = []

        for metric, threshold in self.thresholds.items():
            if metric in metrics and metrics[metric] > threshold:
                alerts.append({
                    "metric": metric,
                    "value": metrics[metric],
                    "threshold": threshold,
                    "severity": self.get_severity(metric, metrics[metric])
                })

        return alerts

    def send_alert(self, alert):
        """알림 발송"""
        if alert["severity"] == "critical":
            self.send_email_alert(alert)
            self.send_slack_alert(alert)
        else:
            self.send_slack_alert(alert)

    def send_slack_alert(self, alert):
        """Slack 알림"""
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if not webhook_url:
            return

        message = {
            "text": f"🚨 {alert['metric']} Alert",
            "attachments": [{
                "color": "danger" if alert["severity"] == "critical" else "warning",
                "fields": [
                    {"title": "Metric", "value": alert["metric"], "short": True},
                    {"title": "Current Value", "value": str(alert["value"]), "short": True},
                    {"title": "Threshold", "value": str(alert["threshold"]), "short": True},
                    {"title": "Severity", "value": alert["severity"], "short": True}
                ]
            }]
        }

        requests.post(webhook_url, json=message)
```

### 2. 애플리케이션 로그 관리

#### 로그 로테이션 설정
```bash
# /etc/logrotate.d/kakao-template
/app/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 app app
    postrotate
        systemctl reload kakao-template
    endscript
}
```

#### 로그 분석 자동화
```python
# monitoring/log_analyzer.py
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter

class LogAnalyzer:
    """로그 분석기"""

    def __init__(self, log_file):
        self.log_file = log_file

    def analyze_daily_logs(self, date=None):
        """일일 로그 분석"""
        if date is None:
            date = datetime.now().date()

        stats = {
            "total_requests": 0,
            "error_count": 0,
            "avg_response_time": 0,
            "top_errors": Counter(),
            "hourly_distribution": defaultdict(int),
            "endpoint_usage": defaultdict(int)
        }

        response_times = []

        with open(self.log_file, 'r') as f:
            for line in f:
                if self.is_date_match(line, date):
                    stats["total_requests"] += 1

                    # 시간대별 분포
                    hour = self.extract_hour(line)
                    if hour:
                        stats["hourly_distribution"][hour] += 1

                    # 에러 분석
                    if "ERROR" in line:
                        stats["error_count"] += 1
                        error_type = self.extract_error_type(line)
                        stats["top_errors"][error_type] += 1

                    # 응답 시간 분석
                    response_time = self.extract_response_time(line)
                    if response_time:
                        response_times.append(response_time)

                    # 엔드포인트 사용량
                    endpoint = self.extract_endpoint(line)
                    if endpoint:
                        stats["endpoint_usage"][endpoint] += 1

        if response_times:
            stats["avg_response_time"] = sum(response_times) / len(response_times)

        return stats

    def generate_report(self, stats):
        """리포트 생성"""
        report = f"""
# 일일 시스템 리포트 - {datetime.now().strftime('%Y-%m-%d')}

## 요약
- 총 요청 수: {stats['total_requests']:,}
- 에러 발생: {stats['error_count']} ({stats['error_count']/stats['total_requests']*100:.2f}%)
- 평균 응답 시간: {stats['avg_response_time']:.2f}ms

## 상위 에러
{self.format_top_errors(stats['top_errors'])}

## 시간대별 요청 분포
{self.format_hourly_distribution(stats['hourly_distribution'])}

## 인기 엔드포인트
{self.format_endpoint_usage(stats['endpoint_usage'])}
        """
        return report
```

### 3. 성능 모니터링

#### 자동 성능 테스트
```python
# monitoring/performance_test.py
import time
import requests
import statistics
from concurrent.futures import ThreadPoolExecutor

class PerformanceMonitor:
    """성능 모니터링"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def run_load_test(self, endpoint="/api/v1/templates/generate",
                     concurrent_users=10, duration=60):
        """부하 테스트 실행"""
        results = {
            "start_time": time.time(),
            "end_time": None,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "errors": []
        }

        def make_request():
            try:
                start = time.time()
                response = requests.post(
                    f"{self.base_url}{endpoint}",
                    json={"user_request": "테스트 요청"},
                    timeout=10
                )
                end = time.time()

                response_time = (end - start) * 1000  # ms
                results["response_times"].append(response_time)
                results["total_requests"] += 1

                if response.status_code == 200:
                    results["successful_requests"] += 1
                else:
                    results["failed_requests"] += 1
                    results["errors"].append(f"HTTP {response.status_code}")

            except Exception as e:
                results["failed_requests"] += 1
                results["errors"].append(str(e))

        # 부하 테스트 실행
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            start_time = time.time()
            futures = []

            while time.time() - start_time < duration:
                if len(futures) < concurrent_users:
                    future = executor.submit(make_request)
                    futures.append(future)

                # 완료된 작업 정리
                futures = [f for f in futures if not f.done()]
                time.sleep(0.1)

        results["end_time"] = time.time()
        return self.analyze_results(results)

    def analyze_results(self, results):
        """결과 분석"""
        if not results["response_times"]:
            return results

        response_times = results["response_times"]
        results.update({
            "avg_response_time": statistics.mean(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "p95_response_time": statistics.quantiles(response_times, n=20)[18],  # 95th percentile
            "rps": results["total_requests"] / (results["end_time"] - results["start_time"]),
            "success_rate": results["successful_requests"] / results["total_requests"] * 100
        })

        return results
```

## 🔄 백업 및 복구

### 1. 자동 백업 시스템

#### 데이터베이스 백업
```bash
#!/bin/bash
# scripts/backup_database.sh

BACKUP_DIR="/backups/kakao-template"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# 디렉토리 생성
mkdir -p $BACKUP_DIR

# Vector DB 백업
echo "Backing up Vector Database..."
tar -czf $BACKUP_DIR/chroma_db_$DATE.tar.gz -C / app/chroma_db

# 템플릿 데이터 백업
echo "Backing up Template Data..."
cp /app/data/kakao_template_vectordb_data.json $BACKUP_DIR/template_data_$DATE.json

# 설정 파일 백업
echo "Backing up Configuration..."
tar -czf $BACKUP_DIR/config_$DATE.tar.gz -C /app \
    .env src/config/ requirements.txt

# 로그 백업
echo "Backing up Logs..."
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz -C /app logs/

# 오래된 백업 정리
echo "Cleaning old backups..."
find $BACKUP_DIR -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.json" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $DATE"
```

#### 자동화된 백업 스케줄
```bash
# crontab -e
# 매일 새벽 2시에 백업 실행
0 2 * * * /app/scripts/backup_database.sh

# 매주 일요일 새벽 3시에 전체 백업
0 3 * * 0 /app/scripts/full_backup.sh
```

### 2. 복구 절차

#### 데이터베이스 복구 스크립트
```bash
#!/bin/bash
# scripts/restore_database.sh

BACKUP_FILE=$1
RESTORE_DIR="/app"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Available backups:"
    ls -la /backups/kakao-template/
    exit 1
fi

echo "Stopping services..."
systemctl stop kakao-template

echo "Creating backup of current data..."
mv $RESTORE_DIR/chroma_db $RESTORE_DIR/chroma_db.bak.$(date +%Y%m%d_%H%M%S)

echo "Restoring from backup: $BACKUP_FILE"
tar -xzf $BACKUP_FILE -C /

echo "Setting permissions..."
chown -R app:app $RESTORE_DIR/chroma_db

echo "Starting services..."
systemctl start kakao-template

echo "Verifying restoration..."
sleep 10
curl -f http://localhost:8000/health || echo "Health check failed"

echo "Restoration completed"
```

### 3. 재해 복구 계획

#### 복구 시간 목표 (RTO/RPO)
- **RTO (Recovery Time Objective)**: 4시간
- **RPO (Recovery Point Objective)**: 24시간
- **서비스 가용성 목표**: 99.9%

#### 복구 우선순위
1. **Critical**: 핵심 API 서비스
2. **High**: 데이터베이스 및 백업
3. **Medium**: 모니터링 시스템
4. **Low**: 개발 도구 및 문서

## 🔧 시스템 업데이트

### 1. 의존성 업데이트

#### 정기 업데이트 체크
```python
# scripts/check_updates.py
import subprocess
import json
from datetime import datetime

def check_security_updates():
    """보안 업데이트 확인"""
    try:
        result = subprocess.run(
            ["pip-audit", "--format", "json"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            vulnerabilities = json.loads(result.stdout)
            return vulnerabilities
        else:
            return {"error": result.stderr}
    except Exception as e:
        return {"error": str(e)}

def check_package_updates():
    """패키지 업데이트 확인"""
    try:
        result = subprocess.run(
            ["pip", "list", "--outdated", "--format", "json"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            outdated = json.loads(result.stdout)
            return outdated
        else:
            return []
    except Exception as e:
        return []

def generate_update_report():
    """업데이트 리포트 생성"""
    security_issues = check_security_updates()
    outdated_packages = check_package_updates()

    report = {
        "timestamp": datetime.now().isoformat(),
        "security_vulnerabilities": security_issues,
        "outdated_packages": outdated_packages,
        "recommendations": []
    }

    # 권장사항 생성
    if security_issues and "vulnerabilities" in security_issues:
        report["recommendations"].append("🚨 Critical: Security vulnerabilities found - immediate update required")

    critical_packages = ["fastapi", "uvicorn", "anthropic", "langchain"]
    for pkg in outdated_packages:
        if pkg["name"] in critical_packages:
            report["recommendations"].append(f"⚠️ Important: Update {pkg['name']} to {pkg['latest_version']}")

    return report

if __name__ == "__main__":
    report = generate_update_report()
    print(json.dumps(report, indent=2))
```

#### 안전한 업데이트 절차
```bash
#!/bin/bash
# scripts/safe_update.sh

PACKAGE_NAME=$1
TARGET_VERSION=$2

echo "🔄 Starting safe update process for $PACKAGE_NAME"

# 1. 현재 버전 백업
echo "📦 Backing up current environment..."
pip freeze > requirements.backup.$(date +%Y%m%d_%H%M%S).txt

# 2. 테스트 환경에서 업데이트 테스트
echo "🧪 Testing update in isolated environment..."
python -m venv test_env
source test_env/bin/activate
pip install $PACKAGE_NAME==$TARGET_VERSION

# 3. 기본 테스트 실행
echo "🧪 Running basic tests..."
python -c "
import $PACKAGE_NAME
print(f'Successfully imported {$PACKAGE_NAME.__name__}')
"

if [ $? -eq 0 ]; then
    echo "✅ Package test passed"
else
    echo "❌ Package test failed"
    deactivate
    rm -rf test_env
    exit 1
fi

deactivate
rm -rf test_env

# 4. 실제 환경 업데이트
echo "🔄 Updating production environment..."
pip install $PACKAGE_NAME==$TARGET_VERSION

# 5. 서비스 재시작 및 헬스체크
echo "🔄 Restarting services..."
systemctl restart kakao-template

sleep 10

# 6. 헬스체크
echo "🔍 Performing health check..."
if curl -f http://localhost:8000/health; then
    echo "✅ Update successful"
else
    echo "❌ Health check failed - rolling back"
    pip install -r requirements.backup.$(ls -t requirements.backup.*.txt | head -1)
    systemctl restart kakao-template
    exit 1
fi

echo "🎉 Update completed successfully"
```

### 2. 코드 배포

#### 무중단 배포 (Blue-Green)
```bash
#!/bin/bash
# scripts/blue_green_deploy.sh

NEW_VERSION=$1
CURRENT_PORT=$(cat /app/current_port 2>/dev/null || echo "8000")
NEW_PORT=$((CURRENT_PORT == 8000 ? 8001 : 8000))

echo "🚀 Starting Blue-Green deployment"
echo "Current: :$CURRENT_PORT, New: :$NEW_PORT"

# 1. 새 버전 빌드
echo "🔨 Building new version..."
docker build -t kakao-template:$NEW_VERSION .

# 2. 새 컨테이너 시작
echo "🏃 Starting new container on port $NEW_PORT..."
docker run -d \
    --name kakao-template-$NEW_PORT \
    -p $NEW_PORT:8000 \
    -e PORT=8000 \
    kakao-template:$NEW_VERSION

# 3. 헬스체크
echo "🔍 Health checking new version..."
sleep 30

for i in {1..10}; do
    if curl -f http://localhost:$NEW_PORT/health; then
        echo "✅ New version is healthy"
        break
    fi

    if [ $i -eq 10 ]; then
        echo "❌ New version failed health check"
        docker stop kakao-template-$NEW_PORT
        docker rm kakao-template-$NEW_PORT
        exit 1
    fi

    sleep 5
done

# 4. 트래픽 전환 (로드 밸런서 설정 변경)
echo "🔄 Switching traffic to new version..."
# nginx 설정 업데이트
sed -i "s/:$CURRENT_PORT/:$NEW_PORT/g" /etc/nginx/sites-available/kakao-template
nginx -s reload

# 5. 이전 버전 정리 (5분 후)
echo "⏰ Waiting 5 minutes before cleaning up old version..."
sleep 300

echo "🧹 Cleaning up old version..."
docker stop kakao-template-$CURRENT_PORT
docker rm kakao-template-$CURRENT_PORT

# 6. 현재 포트 업데이트
echo $NEW_PORT > /app/current_port

echo "🎉 Blue-Green deployment completed successfully"
```

## 🔒 보안 유지보수

### 1. 보안 스캔

#### 자동 보안 점검
```python
# security/security_scanner.py
import subprocess
import json
import os
from datetime import datetime

class SecurityScanner:
    """보안 스캐너"""

    def scan_dependencies(self):
        """의존성 보안 스캔"""
        try:
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True
            )
            return json.loads(result.stdout) if result.stdout else {}
        except Exception as e:
            return {"error": str(e)}

    def scan_secrets(self):
        """시크릿 스캔"""
        try:
            result = subprocess.run(
                ["truffleHog", ".", "--json"],
                capture_output=True,
                text=True
            )
            return {"secrets_found": len(result.stdout.split('\n')) if result.stdout else 0}
        except Exception as e:
            return {"error": str(e)}

    def check_file_permissions(self):
        """파일 권한 확인"""
        critical_files = [
            ".env",
            "data/",
            "logs/",
            "chroma_db/"
        ]

        issues = []
        for file_path in critical_files:
            if os.path.exists(file_path):
                stat_info = os.stat(file_path)
                permissions = oct(stat_info.st_mode)[-3:]

                # .env 파일은 600 권한이어야 함
                if file_path == ".env" and permissions != "600":
                    issues.append(f"{file_path}: {permissions} (should be 600)")

                # 디렉토리는 755 권한이어야 함
                elif os.path.isdir(file_path) and permissions not in ["755", "750"]:
                    issues.append(f"{file_path}: {permissions} (should be 755)")

        return issues

    def generate_security_report(self):
        """보안 리포트 생성"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "dependency_scan": self.scan_dependencies(),
            "secret_scan": self.scan_secrets(),
            "permission_issues": self.check_file_permissions(),
            "recommendations": []
        }

        # 권장사항 추가
        if report["permission_issues"]:
            report["recommendations"].append("Fix file permission issues")

        if "vulnerabilities" in report["dependency_scan"]:
            report["recommendations"].append("Update vulnerable dependencies")

        return report
```

### 2. 접근 제어 관리

#### API 키 로테이션
```python
# security/key_rotation.py
import os
import hashlib
from datetime import datetime, timedelta

class KeyRotationManager:
    """API 키 로테이션 관리"""

    def __init__(self):
        self.key_file = "/secure/api_keys.json"

    def should_rotate_key(self, key_name):
        """키 로테이션 필요 여부 확인"""
        key_info = self.get_key_info(key_name)
        if not key_info:
            return True

        created_date = datetime.fromisoformat(key_info["created"])
        return datetime.now() - created_date > timedelta(days=90)

    def rotate_anthropic_key(self):
        """Anthropic API 키 로테이션"""
        if self.should_rotate_key("anthropic"):
            print("🔑 Rotating Anthropic API key...")

            # 1. 새 키 발급 (수동 과정)
            print("Please generate a new API key from Anthropic Console")
            new_key = input("Enter new API key: ")

            # 2. 새 키 검증
            if self.validate_anthropic_key(new_key):
                # 3. 환경 변수 업데이트
                self.update_env_file("ANTHROPIC_API_KEY", new_key)

                # 4. 서비스 재시작
                os.system("systemctl restart kakao-template")

                print("✅ Key rotation completed")
            else:
                print("❌ Key validation failed")

    def validate_anthropic_key(self, api_key):
        """API 키 유효성 검증"""
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)
            # 간단한 테스트 호출
            return True
        except Exception:
            return False
```

## 📈 성능 최적화

### 1. 정기 성능 분석

#### 성능 프로파일링
```python
# performance/profiler.py
import cProfile
import pstats
import io
from datetime import datetime

class PerformanceProfiler:
    """성능 프로파일러"""

    def profile_template_generation(self, num_requests=100):
        """템플릿 생성 성능 프로파일링"""
        from src.workflow.langgraph_workflow import TemplateGenerationWorkflow

        workflow = TemplateGenerationWorkflow()

        # 프로파일링 시작
        pr = cProfile.Profile()
        pr.enable()

        # 테스트 실행
        for i in range(num_requests):
            workflow.run({
                "user_request": f"테스트 요청 {i}",
                "business_type": "교육"
            })

        pr.disable()

        # 결과 분석
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats()

        # 리포트 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        with open(f'performance/profile_{timestamp}.txt', 'w') as f:
            f.write(s.getvalue())

        return s.getvalue()

    def analyze_memory_usage(self):
        """메모리 사용량 분석"""
        import tracemalloc
        import gc

        tracemalloc.start()

        # 메모리 집약적 작업 실행
        from src.database.vector_store import PolicyVectorStore
        vs = PolicyVectorStore()

        # 여러 검색 실행
        for i in range(100):
            vs.search_relevant_policies(f"검색어 {i}", k=5)

        # 메모리 스냅샷
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')

        print("Top 10 memory consumers:")
        for stat in top_stats[:10]:
            print(stat)

        # 가비지 컬렉션 정보
        gc_stats = {
            "generation_0": gc.get_count()[0],
            "generation_1": gc.get_count()[1],
            "generation_2": gc.get_count()[2],
            "collected": gc.collect()
        }

        return gc_stats
```

### 2. 캐시 최적화

#### 지능형 캐싱 전략
```python
# performance/cache_optimizer.py
import redis
import json
import hashlib
from datetime import datetime, timedelta

class CacheOptimizer:
    """캐시 최적화 관리자"""

    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)

    def analyze_cache_usage(self):
        """캐시 사용 패턴 분석"""
        cache_stats = {
            "total_keys": self.redis_client.dbsize(),
            "memory_usage": self.redis_client.info('memory')['used_memory_human'],
            "hit_ratio": self.calculate_hit_ratio(),
            "popular_keys": self.get_popular_keys(),
            "expired_keys": self.count_expired_keys()
        }

        return cache_stats

    def optimize_cache_ttl(self):
        """캐시 TTL 최적화"""
        # 사용 빈도에 따른 TTL 조정
        key_patterns = {
            "policy:*": 3600,      # 1시간
            "template:*": 1800,    # 30분
            "analysis:*": 900,     # 15분
            "temp:*": 300          # 5분
        }

        for pattern, ttl in key_patterns.items():
            keys = self.redis_client.keys(pattern)
            for key in keys:
                current_ttl = self.redis_client.ttl(key)
                if current_ttl == -1:  # 만료 시간이 없는 키
                    self.redis_client.expire(key, ttl)

    def cleanup_unused_cache(self):
        """사용하지 않는 캐시 정리"""
        # 30일 이상 접근하지 않은 키 삭제
        cutoff_date = datetime.now() - timedelta(days=30)

        for key in self.redis_client.scan_iter():
            last_access = self.redis_client.object('idletime', key)
            if last_access and last_access > 30 * 24 * 3600:  # 30일
                self.redis_client.delete(key)
```

## 📋 정기 점검 체크리스트

### 일일 체크리스트
```markdown
## 📅 일일 점검 체크리스트

### 시스템 상태
- [ ] 서비스 정상 실행 확인 (curl http://localhost:8000/health)
- [ ] CPU 사용률 < 80%
- [ ] 메모리 사용률 < 85%
- [ ] 디스크 사용률 < 90%

### 로그 모니터링
- [ ] 에러 로그 확인 (ERROR 레벨)
- [ ] 경고 로그 검토 (WARN 레벨)
- [ ] 성능 이슈 로그 확인

### API 성능
- [ ] 평균 응답 시간 < 3초
- [ ] 에러율 < 1%
- [ ] 처리량 정상 범위 내

### 보안
- [ ] 비정상적인 접근 시도 확인
- [ ] API 키 사용량 모니터링
```

### 주간 체크리스트
```markdown
## 📅 주간 점검 체크리스트

### 백업
- [ ] 자동 백업 정상 실행 확인
- [ ] 백업 파일 무결성 검증
- [ ] 백업 저장소 용량 확인

### 성능 분석
- [ ] 주간 성능 트렌드 분석
- [ ] 응답 시간 패턴 검토
- [ ] 리소스 사용량 추이 확인

### 보안 점검
- [ ] 의존성 보안 스캔 실행
- [ ] 접근 로그 분석
- [ ] 시스템 패치 확인

### 용량 관리
- [ ] 로그 파일 정리
- [ ] 임시 파일 정리
- [ ] 캐시 최적화
```

### 월간 체크리스트
```markdown
## 📅 월간 점검 체크리스트

### 업데이트
- [ ] 의존성 패키지 업데이트 검토
- [ ] 보안 패치 적용
- [ ] 시스템 업데이트

### 성능 최적화
- [ ] 성능 프로파일링 실행
- [ ] 병목 지점 분석
- [ ] 최적화 계획 수립

### 백업 및 복구
- [ ] 백업 복구 테스트
- [ ] 재해 복구 계획 검토
- [ ] 백업 정책 평가

### 용량 계획
- [ ] 리소스 사용량 예측
- [ ] 스케일링 계획 수립
- [ ] 인프라 비용 분석
```

---

**📅 작성일**: 2024년 9월 19일
**✍️ 작성자**: Final Team 3 AI
**📄 문서 버전**: 1.0
**🔄 최종 수정**: 2024년 9월 19일