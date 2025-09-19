# P03. 설치 및 설정 가이드 (Installation Guide)

## 📋 시스템 요구사항

### 하드웨어 요구사항
- **CPU**: 2 코어 이상 (4 코어 권장)
- **메모리**: 4GB RAM 이상 (8GB 권장)
- **저장공간**: 2GB 이상 여유 공간
- **네트워크**: 인터넷 연결 (API 호출용)

### 소프트웨어 요구사항
- **운영체제**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **Python**: 3.11 이상 (3.11.5 권장)
- **Git**: 최신 버전
- **선택사항**: Docker Desktop (컨테이너 실행시)

### 필수 API 키
- **Anthropic API Key**: Claude AI 모델 사용
- **OpenAI API Key**: 임베딩 생성 (선택사항)

## 🚀 빠른 시작 (Quick Start)

### 1. 저장소 복제
```bash
# Git으로 프로젝트 클론
git clone https://github.com/space-cap/final-team3-ai-v4.git
cd final-team3-ai-v4

# 또는 ZIP 파일 다운로드 후 압축 해제
```

### 2. Python 환경 확인
```bash
# Python 버전 확인
python --version  # 3.11 이상이어야 함

# pip 업그레이드
python -m pip install --upgrade pip
```

### 3. 가상환경 생성 및 활성화
```bash
# 가상환경 생성
python -m venv .venv

# Windows에서 활성화
.venv\Scripts\activate

# macOS/Linux에서 활성화
source .venv/bin/activate

# 활성화 확인 (프롬프트에 (.venv) 표시됨)
```

### 4. 의존성 설치
```bash
# 기본 패키지 설치
pip install -r requirements.txt

# 또는 개별 설치
pip install fastapi uvicorn anthropic langchain chromadb openai python-dotenv
```

### 5. 환경 설정
```bash
# 환경 파일 복사
cp .env.example .env

# 에디터로 .env 파일 편집
# Windows: notepad .env
# macOS: open -e .env
# Linux: nano .env
```

**.env 파일 설정**:
```env
# Anthropic API Key (필수)
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-api-key-here

# OpenAI API Key (임베딩용, 선택사항)
OPENAI_API_KEY=sk-proj-your-openai-api-key-here

# 개발 환경 설정
ENVIRONMENT=development
LOG_LEVEL=INFO

# API 설정
API_HOST=0.0.0.0
API_PORT=8000
```

### 6. 시스템 테스트
```bash
# 간단한 기능 테스트
python simple_test.py

# 실제 API 테스트 (API 키 필요)
python test_real_api.py
```

### 7. 서버 실행
```bash
# 전체 시스템 실행 (Chroma DB 포함)
python run_server.py

# 또는 간단한 테스트 서버
python simple_api_server.py
```

### 8. 접속 확인
브라우저에서 다음 URL 접속:
- **API 문서**: http://localhost:8000/docs
- **헬스체크**: http://localhost:8000/health

## 🔧 상세 설치 가이드

### Windows 설치

#### 1. Python 설치
```powershell
# Microsoft Store에서 Python 3.11 설치
# 또는 https://python.org에서 다운로드

# 설치 확인
python --version
pip --version
```

#### 2. Git 설치
```powershell
# https://git-scm.com/download/win 에서 Git 다운로드 설치
# 또는 GitHub Desktop 사용
```

#### 3. 프로젝트 설정
```powershell
# PowerShell 관리자 권한으로 실행
git clone https://github.com/space-cap/final-team3-ai-v4.git
cd final-team3-ai-v4

# 가상환경 생성
python -m venv .venv
.venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 설정
copy .env.example .env
notepad .env  # API 키 입력
```

### macOS 설치

#### 1. 개발 도구 설치
```bash
# Xcode Command Line Tools 설치
xcode-select --install

# Homebrew 설치 (없는 경우)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 2. Python 설치
```bash
# Homebrew로 Python 설치
brew install python@3.11
brew install git

# 확인
python3.11 --version
git --version
```

#### 3. 프로젝트 설정
```bash
# 프로젝트 클론
git clone https://github.com/space-cap/final-team3-ai-v4.git
cd final-team3-ai-v4

# 가상환경 생성
python3.11 -m venv .venv
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 환경 설정
cp .env.example .env
open -e .env  # API 키 입력
```

### Ubuntu/Linux 설치

#### 1. 시스템 업데이트
```bash
# 패키지 업데이트
sudo apt update && sudo apt upgrade -y

# 필수 패키지 설치
sudo apt install -y python3.11 python3.11-venv python3.11-dev
sudo apt install -y git curl build-essential
```

#### 2. pip 설치
```bash
# pip 설치
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3.11 get-pip.py --user
rm get-pip.py

# PATH 추가 (필요시)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

#### 3. 프로젝트 설정
```bash
# 프로젝트 클론
git clone https://github.com/space-cap/final-team3-ai-v4.git
cd final-team3-ai-v4

# 가상환경 생성
python3.11 -m venv .venv
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 환경 설정
cp .env.example .env
nano .env  # API 키 입력
```

## 🐳 Docker 설치 (선택사항)

### 1. Dockerfile 확인
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "run_server.py"]
```

### 2. Docker 이미지 빌드
```bash
# 이미지 빌드
docker build -t kakao-template-service .

# 이미지 확인
docker images
```

### 3. 컨테이너 실행
```bash
# 환경 변수와 함께 실행
docker run -d \
  --name kakao-template \
  -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your-api-key \
  kakao-template-service

# 로그 확인
docker logs kakao-template

# 컨테이너 중지
docker stop kakao-template
```

### 4. Docker Compose 사용
```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
      - ./chroma_db:/app/chroma_db
```

```bash
# 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down
```

## ⚠️ 문제 해결 (Troubleshooting)

### 일반적인 문제들

#### 1. Python 버전 문제
```bash
# 오류: Python 3.11 미만 버전
Error: Python 3.11 or higher is required

# 해결: Python 업그레이드
# Windows: Microsoft Store나 python.org에서 재설치
# macOS: brew install python@3.11
# Ubuntu: sudo apt install python3.11
```

#### 2. 의존성 설치 오류
```bash
# 오류: pip install 실패
ERROR: Could not install packages

# 해결 방법들:
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir -r requirements.txt
pip install --user -r requirements.txt
```

#### 3. API 키 오류
```bash
# 오류: API 키 없음
Error: ANTHROPIC_API_KEY not found

# 해결:
# 1. .env 파일이 있는지 확인
ls -la .env

# 2. API 키가 올바른지 확인
cat .env | grep ANTHROPIC

# 3. 환경 변수 직접 설정
export ANTHROPIC_API_KEY=your-api-key
```

#### 4. 포트 충돌
```bash
# 오류: 포트 8000 이미 사용 중
Error: Port 8000 is already in use

# 해결: 다른 포트 사용
python run_server.py --port 8001

# 또는 기존 프로세스 종료 (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID번호> /F

# Linux/macOS
lsof -i :8000
kill -9 <PID번호>
```

#### 5. 가상환경 문제
```bash
# 오류: 가상환경이 활성화되지 않음
(venv) 표시가 없음

# 해결:
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# 가상환경 재생성
rm -rf .venv
python -m venv .venv
```

### 성능 최적화

#### 1. 메모리 사용량 최적화
```python
# src/config.py에서 설정 조정
VECTOR_DB_CACHE_SIZE = 100  # 캐시 크기 조정
MAX_CONCURRENT_REQUESTS = 10  # 동시 요청 수 제한
```

#### 2. API 응답 시간 개선
```bash
# 환경 변수로 모델 변경
export CLAUDE_MODEL=claude-3-haiku-20240307  # 더 빠른 모델
```

#### 3. 디스크 공간 절약
```bash
# 불필요한 캐시 정리
pip cache purge
rm -rf .venv/lib/python*/site-packages/__pycache__
```

## 🔄 업데이트 가이드

### 1. 코드 업데이트
```bash
# Git으로 최신 코드 받기
git pull origin main

# 의존성 업데이트
pip install -r requirements.txt --upgrade
```

### 2. 데이터베이스 마이그레이션
```bash
# 벡터 데이터베이스 재생성 (필요시)
rm -rf chroma_db
python -c "
from src.database.vector_store import PolicyVectorStore
vs = PolicyVectorStore()
vs.load_policy_documents()
"
```

### 3. 설정 파일 업데이트
```bash
# 새 설정 확인
diff .env .env.example

# 필요한 설정 추가
```

## 📞 지원 및 문의

### 설치 관련 문의
- **GitHub Issues**: https://github.com/space-cap/final-team3-ai-v4/issues
- **이메일**: team3-ai@example.com
- **문서**: 각 섹션별 문제 해결 가이드 참조

### 추가 리소스
- **Python 설치**: https://python.org
- **Git 가이드**: https://git-scm.com/docs
- **Docker 문서**: https://docs.docker.com
- **FastAPI 문서**: https://fastapi.tiangolo.com

---

**📅 작성일**: 2024년 9월 19일
**✍️ 작성자**: Final Team 3 AI
**📄 문서 버전**: 1.0
**🔄 최종 수정**: 2024년 9월 19일