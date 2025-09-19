# P09. 문제 해결 가이드 (Troubleshooting Guide)

## 🔧 문제 해결 개요

이 문서는 카카오 알림톡 템플릿 자동 생성 AI 서비스 사용 중 발생할 수 있는 다양한 문제들과 해결 방법을 제공합니다. 문제 유형별로 체계적인 진단 및 해결 방법을 안내합니다.

## 📋 문제 분류 체계

### 1. 설치 및 환경 문제
- Python 환경 관련
- 의존성 설치 문제
- 환경 변수 설정 오류

### 2. API 연결 문제
- Claude API 연결 실패
- 네트워크 연결 문제
- 인증 오류

### 3. 서비스 실행 문제
- 서버 시작 실패
- 포트 충돌
- 메모리 부족

### 4. 기능 관련 문제
- 템플릿 생성 실패
- 정책 검증 오류
- 응답 속도 저하

### 5. 데이터베이스 문제
- 벡터 DB 연결 실패
- 데이터 로딩 오류
- 검색 결과 없음

## 🐍 설치 및 환경 문제

### Python 버전 문제

#### 문제: "Python 3.11 이상이 필요합니다"
```bash
# 증상
ERROR: Python 3.11 or higher is required

# 원인 진단
python --version  # 현재 버전 확인
```

**해결 방법**:
```bash
# Windows (Microsoft Store)
1. Microsoft Store에서 "Python 3.11" 검색
2. 최신 버전 설치
3. 시스템 재시작

# macOS (Homebrew)
brew install python@3.11
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
```

#### 문제: 가상환경 생성 실패
```bash
# 증상
ModuleNotFoundError: No module named 'venv'
```

**해결 방법**:
```bash
# Windows
python -m pip install --user virtualenv
python -m virtualenv .venv

# Linux/macOS
sudo apt install python3.11-venv  # Ubuntu
python3.11 -m venv .venv
```

### 의존성 설치 문제

#### 문제: pip 설치 실패
```bash
# 증상
ERROR: Could not install packages due to an EnvironmentError
```

**해결 방법**:
```bash
# 1. pip 업그레이드
python -m pip install --upgrade pip

# 2. 권한 문제 해결
pip install --user -r requirements.txt

# 3. 캐시 정리
pip cache purge
pip install --no-cache-dir -r requirements.txt

# 4. 개별 패키지 설치
pip install fastapi uvicorn anthropic langchain chromadb
```

#### 문제: 특정 패키지 충돌
```bash
# 증상
ERROR: Package conflicts with existing installation
```

**해결 방법**:
```bash
# 1. 가상환경 재생성
rm -rf .venv
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# 2. 의존성 강제 설치
pip install --force-reinstall -r requirements.txt

# 3. 호환성 있는 버전 설치
pip install "langchain==0.2.16" "chromadb==0.4.15"
```

### 환경 변수 설정 문제

#### 문제: .env 파일을 찾을 수 없음
```bash
# 증상
Warning: .env file not found
```

**해결 방법**:
```bash
# 1. .env 파일 생성
cp .env.example .env

# 2. 필수 환경 변수 설정
echo "ANTHROPIC_API_KEY=your-actual-api-key" >> .env

# 3. 파일 권한 확인
chmod 600 .env  # Linux/macOS
```

#### 문제: API 키 인식 안됨
```bash
# 증상
ValueError: ANTHROPIC_API_KEY must be provided
```

**해결 방법**:
```bash
# 1. 환경 변수 직접 확인
cat .env | grep ANTHROPIC_API_KEY

# 2. 환경 변수 직접 설정
export ANTHROPIC_API_KEY=your-api-key  # Linux/macOS
set ANTHROPIC_API_KEY=your-api-key     # Windows CMD
$env:ANTHROPIC_API_KEY="your-api-key"  # Windows PowerShell

# 3. Python에서 확인
python -c "import os; print(os.getenv('ANTHROPIC_API_KEY'))"
```

## 🌐 API 연결 문제

### Claude API 연결 실패

#### 문제: API 키 인증 실패
```bash
# 증상
AuthenticationError: Invalid API key
```

**해결 방법**:
```bash
# 1. API 키 형식 확인
# 올바른 형식: sk-ant-api03-xxxxx

# 2. API 키 유효성 테스트
python -c "
from anthropic import Anthropic
client = Anthropic(api_key='your-api-key')
print('API key is valid')
"

# 3. 새 API 키 발급
# https://console.anthropic.com/에서 새 키 생성
```

#### 문제: 네트워크 연결 실패
```bash
# 증상
ConnectionError: Unable to connect to API
```

**해결 방법**:
```bash
# 1. 네트워크 연결 확인
ping api.anthropic.com
curl -I https://api.anthropic.com

# 2. 프록시 설정 (필요시)
export HTTPS_PROXY=http://proxy.company.com:8080

# 3. 방화벽 설정 확인
# Windows: Windows Defender 방화벽에서 Python 허용
# Linux: iptables 규칙 확인

# 4. DNS 설정 확인
nslookup api.anthropic.com
```

### 요청 제한 문제

#### 문제: Rate Limit 초과
```bash
# 증상
RateLimitError: Too Many Requests
```

**해결 방법**:
```python
# 1. 재시도 로직 구현
import time
from anthropic import RateLimitError

def api_call_with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt  # 지수 백오프
            time.sleep(wait_time)

# 2. 요청 간격 조정
import asyncio

async def delayed_api_call():
    await asyncio.sleep(1)  # 1초 대기
    return api_call()
```

## 🖥 서비스 실행 문제

### 서버 시작 실패

#### 문제: 포트 이미 사용 중
```bash
# 증상
OSError: [Errno 98] Address already in use
```

**해결 방법**:
```bash
# 1. 사용 중인 프로세스 확인
# Linux/macOS
lsof -i :8000
netstat -tulpn | grep :8000

# Windows
netstat -ano | findstr :8000

# 2. 프로세스 종료
kill -9 <PID>        # Linux/macOS
taskkill /PID <PID> /F  # Windows

# 3. 다른 포트 사용
python run_server.py --port 8001
uvicorn src.api.main:app --port 8001
```

#### 문제: 모듈을 찾을 수 없음
```bash
# 증상
ModuleNotFoundError: No module named 'src'
```

**해결 방법**:
```bash
# 1. PYTHONPATH 설정
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Linux/macOS
set PYTHONPATH=%PYTHONPATH%;%CD%          # Windows

# 2. 상대 경로로 실행
python -m src.api.main

# 3. 패키지 설치 모드
pip install -e .
```

### 메모리 부족 문제

#### 문제: Out of Memory 오류
```bash
# 증상
MemoryError: Unable to allocate memory
```

**해결 방법**:
```bash
# 1. 메모리 사용량 확인
# Linux/macOS
free -h
top

# Windows
tasklist /fi "imagename eq python.exe"
wmic computersystem get TotalPhysicalMemory

# 2. 메모리 최적화 설정
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1

# 3. 가비지 컬렉션 강제 실행
python -c "import gc; gc.collect()"
```

**코드 레벨 최적화**:
```python
# 메모리 효율적인 설정
import gc
import os

# 환경 변수 설정
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['OMP_NUM_THREADS'] = '1'

# 주기적 가비지 컬렉션
def cleanup_memory():
    gc.collect()

# 벡터 DB 캐시 크기 제한
vector_store = PolicyVectorStore(cache_size=100)
```

## 🤖 기능 관련 문제

### 템플릿 생성 실패

#### 문제: 생성 결과가 빈 값
```bash
# 증상
{"success": false, "error": "Empty response from AI"}
```

**진단 및 해결**:
```python
# 1. 입력 데이터 검증
def diagnose_input(user_request):
    print(f"Request length: {len(user_request)}")
    print(f"Request content: {repr(user_request)}")

    if len(user_request.strip()) == 0:
        return "Empty request"
    if len(user_request) > 1000:
        return "Request too long"
    return "Valid"

# 2. LLM 응답 로깅
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_llm_call(prompt):
    logger.debug(f"Sending prompt: {prompt[:100]}...")
    response = llm_client.generate_response(prompt)
    logger.debug(f"Received response: {response[:100]}...")
    return response
```

#### 문제: JSON 파싱 오류
```bash
# 증상
JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**해결 방법**:
```python
import json
import re

def safe_json_parse(text):
    """안전한 JSON 파싱"""
    try:
        # 1. 직접 파싱 시도
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            # 2. JSON 부분만 추출
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass

        # 3. 기본값 반환
        return {
            "template_text": "템플릿 생성 중 오류가 발생했습니다.",
            "variables": ["수신자명"],
            "error": "JSON parsing failed"
        }
```

### 정책 검증 오류

#### 문제: 컴플라이언스 점수가 항상 낮음
```bash
# 증상
Compliance score consistently below 70
```

**해결 방법**:
```python
# 1. 정책 문서 로딩 확인
def check_policy_loading():
    from src.database.vector_store import PolicyVectorStore

    vs = PolicyVectorStore()
    results = vs.search_relevant_policies("테스트", k=1)

    if not results:
        print("❌ 정책 문서가 로드되지 않았습니다")
        vs.load_policy_documents()
        print("✅ 정책 문서를 다시 로드했습니다")
    else:
        print("✅ 정책 문서가 정상적으로 로드되어 있습니다")

# 2. 검증 로직 디버깅
def debug_compliance_check(template_text):
    from src.agents.compliance_checker import ComplianceChecker

    checker = ComplianceChecker()

    # 개별 규칙 체크
    rules = {
        "has_greeting": "안녕하세요" in template_text,
        "has_info_notice": "정보성" in template_text or "안내" in template_text,
        "length_ok": len(template_text) <= 1000,
        "no_ads": not any(kw in template_text for kw in ["할인", "이벤트", "특가"])
    }

    for rule, passed in rules.items():
        print(f"{rule}: {'✅' if passed else '❌'}")

    return rules
```

### 응답 속도 저하

#### 문제: API 응답이 너무 느림 (30초 이상)
```bash
# 증상
Request timeout after 30 seconds
```

**해결 방법**:
```python
# 1. 타임아웃 설정 조정
from anthropic import Anthropic
import httpx

client = Anthropic(
    api_key="your-key",
    timeout=httpx.Timeout(60.0)  # 60초로 증가
)

# 2. 모델 변경 (더 빠른 모델 사용)
# claude-3-haiku-20240307 (빠름) vs claude-3-sonnet (느림)

# 3. 프롬프트 최적화
def optimize_prompt(user_request):
    # 간결한 프롬프트 사용
    return f"Generate template for: {user_request[:100]}"

# 4. 캐싱 구현
import functools
import time

@functools.lru_cache(maxsize=100)
def cached_template_generation(request_hash):
    return generate_template(request_hash)
```

## 💾 데이터베이스 문제

### 벡터 DB 연결 실패

#### 문제: Chroma DB 초기화 오류
```bash
# 증상
RuntimeError: Chroma requires sqlite3 >= 3.35.0
```

**해결 방법**:
```bash
# 1. SQLite 버전 확인
python -c "import sqlite3; print(sqlite3.sqlite_version)"

# 2. SQLite 업그레이드
# Linux
sudo apt update && sudo apt upgrade sqlite3

# macOS
brew upgrade sqlite

# Windows (Anaconda 사용시)
conda install sqlite

# 3. Python sqlite3 재설치
pip uninstall pysqlite3-binary
pip install pysqlite3-binary
```

#### 문제: 벡터 DB 데이터 손상
```bash
# 증상
DatabaseError: database disk image is malformed
```

**해결 방법**:
```bash
# 1. 백업 및 재생성
cp -r chroma_db chroma_db_backup
rm -rf chroma_db

# 2. 새 벡터 DB 생성
python -c "
from src.database.vector_store import PolicyVectorStore
vs = PolicyVectorStore()
vs.load_policy_documents()
print('Vector DB rebuilt successfully')
"

# 3. 데이터 무결성 확인
python -c "
from src.database.vector_store import PolicyVectorStore
vs = PolicyVectorStore()
results = vs.search_relevant_policies('알림톡', k=5)
print(f'Found {len(results)} results')
"
```

### 데이터 로딩 오류

#### 문제: 정책 문서 로딩 실패
```bash
# 증상
FileNotFoundError: Policy directory not found
```

**해결 방법**:
```bash
# 1. 파일 구조 확인
ls -la data/cleaned_policies/
find . -name "*.md" -type f

# 2. 권한 확인
chmod -R 755 data/
chown -R $USER:$USER data/

# 3. 파일 인코딩 확인
file data/cleaned_policies/*.md
```

**파일 복구 스크립트**:
```python
# check_data_integrity.py
import os
from pathlib import Path

def check_data_integrity():
    data_dir = Path("data/cleaned_policies")

    required_files = [
        "audit.md",
        "content-guide.md",
        "white-list.md",
        "black-list.md",
        "operations.md"
    ]

    missing_files = []
    for file in required_files:
        file_path = data_dir / file
        if not file_path.exists():
            missing_files.append(file)
        else:
            # 파일 크기 확인
            if file_path.stat().st_size == 0:
                missing_files.append(f"{file} (empty)")

    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All policy files are present")
        return True

if __name__ == "__main__":
    check_data_integrity()
```

## 🔍 진단 도구

### 시스템 상태 체크 스크립트

```python
# system_health_check.py
#!/usr/bin/env python3

import os
import sys
import subprocess
import pkg_resources
from pathlib import Path

def check_python_version():
    """Python 버전 확인"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} (3.11+ required)")
        return False

def check_dependencies():
    """의존성 확인"""
    required_packages = [
        "fastapi",
        "uvicorn",
        "anthropic",
        "langchain",
        "chromadb",
        "python-dotenv"
    ]

    missing = []
    for package in required_packages:
        try:
            pkg_resources.get_distribution(package)
            print(f"✅ {package}")
        except pkg_resources.DistributionNotFound:
            print(f"❌ {package}")
            missing.append(package)

    return len(missing) == 0

def check_environment():
    """환경 변수 확인"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        return False

    required_vars = ["ANTHROPIC_API_KEY"]
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    else:
        print("✅ Environment variables configured")
        return True

def check_api_connectivity():
    """API 연결 확인"""
    try:
        from anthropic import Anthropic
        client = Anthropic()
        # 간단한 테스트 호출
        print("✅ Claude API connection successful")
        return True
    except Exception as e:
        print(f"❌ Claude API connection failed: {e}")
        return False

def check_data_files():
    """데이터 파일 확인"""
    data_dir = Path("data/cleaned_policies")
    if not data_dir.exists():
        print("❌ Policy data directory not found")
        return False

    policy_files = list(data_dir.glob("*.md"))
    if len(policy_files) < 5:
        print(f"❌ Insufficient policy files ({len(policy_files)} found)")
        return False
    else:
        print(f"✅ Policy files ({len(policy_files)} files)")
        return True

def check_ports():
    """포트 사용 확인"""
    import socket

    port = 8000
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        result = s.connect_ex(('localhost', port))
        if result == 0:
            print(f"❌ Port {port} is already in use")
            return False
        else:
            print(f"✅ Port {port} is available")
            return True

def main():
    """메인 체크 함수"""
    print("🔍 System Health Check")
    print("=" * 50)

    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment", check_environment),
        ("API Connectivity", check_api_connectivity),
        ("Data Files", check_data_files),
        ("Port Availability", check_ports)
    ]

    passed = 0
    total = len(checks)

    for name, check_func in checks:
        print(f"\n{name}:")
        if check_func():
            passed += 1

    print("\n" + "=" * 50)
    print(f"Results: {passed}/{total} checks passed")

    if passed == total:
        print("🎉 System is ready!")
        return 0
    else:
        print("⚠️ Some issues need to be resolved")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### 로그 분석 도구

```python
# log_analyzer.py
import re
from datetime import datetime
from collections import Counter

def analyze_logs(log_file="logs/app.log"):
    """로그 파일 분석"""

    if not os.path.exists(log_file):
        print(f"Log file not found: {log_file}")
        return

    error_patterns = {
        "api_errors": r"ERROR.*API",
        "connection_errors": r"ERROR.*Connection",
        "timeout_errors": r"ERROR.*timeout",
        "memory_errors": r"ERROR.*Memory"
    }

    errors = Counter()

    with open(log_file, 'r') as f:
        for line in f:
            for error_type, pattern in error_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    errors[error_type] += 1

    print("📊 Log Analysis Results:")
    for error_type, count in errors.most_common():
        print(f"  {error_type}: {count} occurrences")

    return errors
```

## 📞 지원 요청 가이드

### 이슈 리포팅 템플릿

```markdown
## 🐛 버그 리포트

**문제 설명**
간단하고 명확한 문제 설명

**재현 단계**
1. '...' 으로 이동
2. '....' 클릭
3. '....' 까지 스크롤
4. 오류 발생

**예상 결과**
예상했던 결과 설명

**실제 결과**
실제로 발생한 결과 설명

**스크린샷**
해당되는 경우 스크린샷 첨부

**환경 정보**
- OS: [예: iOS]
- 브라우저: [예: chrome, safari]
- 버전: [예: 22]
- Python 버전: [예: 3.11.5]

**추가 정보**
문제와 관련된 추가 컨텍스트나 정보
```

### 성능 이슈 리포팅

```markdown
## ⚡ 성능 이슈

**문제 유형**
- [ ] 느린 응답 시간
- [ ] 높은 메모리 사용량
- [ ] CPU 과부하
- [ ] 기타: ___

**측정 데이터**
- 응답 시간: ___ 초
- 메모리 사용량: ___ MB
- CPU 사용량: ___%

**재현 조건**
- 동시 사용자 수: ___
- 요청 유형: ___
- 데이터 크기: ___

**시스템 사양**
- CPU: ___
- RAM: ___
- 저장공간: ___
```

---

**📅 작성일**: 2024년 9월 19일
**✍️ 작성자**: Final Team 3 AI
**📄 문서 버전**: 1.0
**🔄 최종 수정**: 2024년 9월 19일