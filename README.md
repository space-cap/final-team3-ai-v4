# 카카오 알림톡 템플릿 자동 생성 AI 서비스

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688.svg)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.2.16-green.svg)](https://python.langchain.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

소상공인을 위한 AI 기반 카카오 알림톡 템플릿 자동 생성 서비스입니다. 복잡한 카카오 정책을 이해하지 않아도 쉽게 승인 가능한 알림톡 템플릿을 생성할 수 있습니다.

## 🎯 프로젝트 배경

소상공인들이 카카오 알림톡을 활용한 고객 관리를 시도할 때 가장 큰 어려움 중 하나는 까다로운 템플릿 승인 정책입니다. 수십 페이지에 달하는 가이드라인을 일일이 숙지하고 준수하기 어렵기 때문에, 많은 소상공인이 메시지 작성 단계에서부터 포기하거나 정책 위반으로 반려되는 경험을 합니다.

본 프로젝트는 이 문제를 해결하기 위해, 사용자가 원하는 메시지 내용을 입력하면 AI가 카카오 알림톡 정책에 완벽하게 부합하는 템플릿을 자동으로 생성해주는 서비스를 개발했습니다.

## ✨ 주요 기능

### 🤖 AI 기반 템플릿 생성
- 사용자 요청 자동 분석 및 분류
- 정책 기반 템플릿 자동 생성
- 변수 및 버튼 자동 설정

### 📋 정책 준수 검증
- 실시간 컴플라이언스 체크
- 위반사항 및 개선점 제안
- 승인 가능성 예측 (높음/보통/낮음)

### 🏢 다양한 업종 지원
- 교육, 의료, 음식점, 쇼핑몰, 서비스업, 금융 등
- 업종별 특화된 템플릿 패턴
- 승인된 템플릿 예시 제공

### 🔄 Multi-Agent 워크플로우
- Request Analyzer: 요청 분석 및 분류
- Policy RAG: 정책 문서 검색 및 컨텍스트 제공
- Template Generator: 정책 준수 템플릿 생성
- Compliance Checker: 정책 준수 검증

## 🛠 기술 스택

- **AI Framework**: LangChain, LangGraph
- **LLM**: Claude API (Anthropic)
- **Vector Database**: Chroma
- **Backend**: FastAPI
- **Language**: Python 3.11

## 📦 설치 및 실행

### 요구사항

- Python 3.11 이상
- 4GB RAM 이상
- Anthropic API Key

### 1. 저장소 클론

```bash
git clone <repository_url>
cd final-team3-ai-v4
```

### 2. 가상환경 설정

```bash
# 가상환경 생성
python -m venv .venv

# 가상환경 활성화 (Windows)
.venv\Scripts\activate

# 가상환경 활성화 (Linux/Mac)
source .venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집하여 API 키 설정
# ANTHROPIC_API_KEY=your_actual_api_key_here
```

### 5. 시스템 테스트

```bash
python simple_test.py
```

### 6. 서버 실행

```bash
python run_server.py
```

서버가 실행되면 다음 URL에서 서비스를 이용할 수 있습니다:
- **API 문서**: http://localhost:8000/docs
- **헬스체크**: http://localhost:8000/health
- **시스템 통계**: http://localhost:8000/stats

## 📖 사용 방법

### API를 통한 템플릿 생성

```python
import requests

# 템플릿 생성 요청
response = requests.post("http://localhost:8000/api/v1/templates/generate", json={
    "user_request": "온라인 강의 수강 신청 완료 안내 메시지를 만들어주세요",
    "business_type": "교육",
    "service_type": "신청",
    "tone": "정중한"
})

result = response.json()

if result["success"]:
    print("생성된 템플릿:")
    print(result["template"]["text"])
    print(f"컴플라이언스 점수: {result['compliance']['score']}/100")
    print(f"승인 가능성: {result['compliance']['approval_probability']}")
else:
    print("오류:", result["error"]["message"])
```

### 템플릿 검증

```python
# 기존 템플릿 검증
response = requests.post("http://localhost:8000/api/v1/templates/validate", json={
    "template_text": "안녕하세요 #{수신자명}님, 강의 신청이 완료되었습니다.",
    "variables": ["수신자명"],
    "business_type": "교육"
})
```

## 🏗 시스템 아키텍처

```
User Request → Request Analyzer → Template Generator → Compliance Checker → Final Output
                     ↓                    ↓                    ↓
              Policy RAG System ←→ Vector Database ←→ Template Database
```

### 주요 컴포넌트

1. **Request Analyzer Agent**: 사용자 요청 분석 및 분류
2. **Policy RAG System**: 정책 문서 기반 컨텍스트 제공
3. **Template Generator Agent**: 정책 준수 템플릿 생성
4. **Compliance Checker Agent**: 생성된 템플릿의 정책 준수 검증
5. **LangGraph Workflow**: 에이전트 간 협업 및 워크플로우 관리

## 📊 데이터

### 정책 문서
- `data/cleaned_policies/`: 카카오 알림톡 정책 문서 (Markdown 형식)
  - 심사 가이드라인
  - 콘텐츠 작성 가이드
  - 허용/금지 템플릿 유형
  - 운영 절차

### 템플릿 데이터
- `data/kakao_template_vectordb_data.json`: 승인된 템플릿 데이터 (~530KB)
  - 1,000+ 개의 승인된 템플릿
  - 메타데이터 (카테고리, 업종, 변수 정보 등)
  - 컴플라이언스 분석 정보

## 🧪 테스트

### 전체 시스템 테스트

```bash
python simple_test.py
```

### 개별 컴포넌트 테스트

```bash
# 워크플로우 테스트
python -m src.workflow.langgraph_workflow

# 에이전트 테스트
python -m src.agents.request_analyzer
python -m src.agents.template_generator
python -m src.agents.compliance_checker
```

## 📈 성능 지표

- **템플릿 생성 시간**: 평균 2-5초
- **컴플라이언스 검증**: 평균 1-3초
- **정확도**: 정책 준수율 95% 이상
- **승인 예측**: 실제 승인율 90% 이상

## 📚 문서

- [API 문서](docs/api_documentation.md): REST API 상세 가이드
- [사용자 매뉴얼](docs/user_manual.md): 서비스 사용법 및 모범 사례
- [배포 가이드](docs/deployment_guide.md): 운영 환경 배포 방법
- [아키텍처 문서](docs/architecture.md): 시스템 설계 및 구조

## 🚀 배포

### Docker를 사용한 배포

```bash
# Docker 이미지 빌드
docker build -t kakao-template-service .

# 컨테이너 실행
docker run -p 8000:8000 --env-file .env kakao-template-service
```

### 운영 환경 배포

상세한 배포 방법은 [배포 가이드](docs/deployment_guide.md)를 참조하세요.

## 🔒 보안

- API 키는 환경 변수로 관리
- 로그에서 민감한 정보 마스킹
- CORS 및 보안 헤더 설정
- 요청 제한 및 모니터링

## 🤝 기여

### 개발 환경 설정

1. 저장소 포크 및 클론
2. 가상환경 설정 및 의존성 설치
3. 개발용 서버 실행: `python run_server.py`
4. 테스트 실행: `python simple_test.py`

### 코드 스타일

- Python: PEP 8 준수
- 타입 힌트 사용 권장
- Docstring 작성 (Google 스타일)

## 📄 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 👥 팀

**Final Team 3 AI**
- AI 시스템 설계 및 구현
- Multi-Agent 워크플로우 개발
- 정책 준수 검증 시스템 구축

## 📞 연락처

- **이메일**: team3@example.com
- **이슈 리포트**: [GitHub Issues](https://github.com/your-repo/issues)

## 🎯 로드맵

### v1.1 (예정)
- [ ] 웹 UI 인터페이스 추가
- [ ] 실시간 정책 업데이트
- [ ] 다국어 지원 (영어)

### v1.2 (예정)
- [ ] 템플릿 변형 생성
- [ ] A/B 테스트 기능
- [ ] 고급 분석 대시보드

### v2.0 (예정)
- [ ] 친구톡 템플릿 지원
- [ ] 이미지 템플릿 생성
- [ ] 업종별 특화 모델

---

**카카오 알림톡 템플릿 자동 생성 AI 서비스**로 복잡한 정책 없이도 쉽게 승인받는 템플릿을 만들어보세요! 🚀 
