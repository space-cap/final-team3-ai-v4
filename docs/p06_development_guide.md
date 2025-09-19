# P06. 개발자 가이드 (Development Guide)

## 👩‍💻 개발자를 위한 안내

이 문서는 카카오 알림톡 템플릿 자동 생성 AI 서비스의 코드베이스를 이해하고 기여하고자 하는 개발자들을 위한 가이드입니다.

## 🏗 프로젝트 구조

### 디렉토리 구조
```
final-team3-ai-v4/
├── src/                          # 메인 소스 코드
│   ├── agents/                   # AI 에이전트들
│   │   ├── request_analyzer.py   # 요청 분석 에이전트
│   │   ├── policy_rag.py         # 정책 RAG 에이전트
│   │   ├── template_generator.py # 템플릿 생성 에이전트
│   │   └── compliance_checker.py # 정책 준수 검증 에이전트
│   ├── api/                      # FastAPI 애플리케이션
│   │   ├── main.py              # 메인 애플리케이션
│   │   ├── models/              # Pydantic 모델들
│   │   └── routes/              # API 라우트들
│   ├── database/                 # 데이터베이스 관련
│   │   └── vector_store.py      # 벡터 데이터베이스
│   ├── utils/                    # 유틸리티
│   │   └── llm_client.py        # LLM 클라이언트
│   └── workflow/                 # 워크플로우
│       └── langgraph_workflow.py # LangGraph 워크플로우
├── data/                         # 데이터 파일들
│   ├── cleaned_policies/         # 정책 문서들
│   └── kakao_template_vectordb_data.json # 템플릿 데이터
├── docs/                         # 문서들
├── tests/                        # 테스트 파일들
├── requirements.txt              # Python 의존성
├── .env.example                  # 환경 변수 예시
└── README.md                     # 프로젝트 설명
```

### 코드 아키텍처 패턴

#### 1. Agent Pattern
각 AI 에이전트는 단일 책임 원칙을 따르며 독립적으로 동작합니다.

```python
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """기본 에이전트 인터페이스"""

    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """에이전트 처리 로직"""
        pass

    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """입력 데이터 검증"""
        pass

class RequestAnalyzer(BaseAgent):
    """요청 분석 에이전트 구현"""

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        user_request = input_data.get("user_request")
        # 분석 로직 구현
        return analysis_result
```

#### 2. Factory Pattern
LLM 클라이언트 생성에 팩토리 패턴을 사용합니다.

```python
class LLMClientFactory:
    """LLM 클라이언트 팩토리"""

    @staticmethod
    def create_client(provider: str, **kwargs) -> BaseLLMClient:
        if provider == "anthropic":
            return ClaudeLLMClient(**kwargs)
        elif provider == "openai":
            return OpenAIClient(**kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
```

#### 3. Strategy Pattern
다양한 템플릿 생성 전략을 구현합니다.

```python
class TemplateGenerationStrategy(ABC):
    """템플릿 생성 전략 인터페이스"""

    @abstractmethod
    def generate(self, context: Dict[str, Any]) -> str:
        pass

class EducationTemplateStrategy(TemplateGenerationStrategy):
    """교육업 특화 템플릿 생성 전략"""

    def generate(self, context: Dict[str, Any]) -> str:
        # 교육업 특화 로직
        return template
```

## 🔧 개발 환경 설정

### 1. 개발 도구 설치
```bash
# 필수 도구들
pip install black isort flake8 mypy pytest pytest-cov
pip install pre-commit jupyter notebook

# 개발용 의존성 설치
pip install -r requirements-dev.txt
```

### 2. Pre-commit Hook 설정
```bash
# Pre-commit 설치
pre-commit install

# 모든 파일에 대해 실행
pre-commit run --all-files
```

#### .pre-commit-config.yaml
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=100, --ignore=E203,W503]
```

### 3. IDE 설정

#### VS Code 설정 (.vscode/settings.json)
```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

#### PyCharm 설정
- Code Style → Python → Black 설정
- Inspections → Python → PEP 8 활성화
- External Tools → isort 설정

## 📝 코딩 표준

### 1. Python 코딩 스타일

#### 네이밍 컨벤션
```python
# 클래스: PascalCase
class TemplateGenerator:
    pass

# 함수/변수: snake_case
def generate_template():
    user_request = "example"

# 상수: UPPER_SNAKE_CASE
MAX_TEMPLATE_LENGTH = 1000

# 프라이빗: underscore prefix
def _internal_method():
    pass
```

#### 타입 힌트 사용
```python
from typing import Dict, List, Optional, Union

def analyze_request(
    user_request: str,
    business_type: Optional[str] = None
) -> Dict[str, Any]:
    """요청 분석 함수

    Args:
        user_request: 사용자 요청 문자열
        business_type: 업종 정보 (선택사항)

    Returns:
        분석 결과 딕셔너리
    """
    return {}
```

#### Docstring 작성 (Google Style)
```python
def generate_template(
    request_analysis: Dict[str, Any],
    policy_context: str
) -> Dict[str, Any]:
    """정책 기반 템플릿 생성

    Args:
        request_analysis: 요청 분석 결과
            - business_type: 업종 정보
            - service_type: 서비스 유형
            - required_variables: 필요한 변수들
        policy_context: 관련 정책 컨텍스트

    Returns:
        생성된 템플릿 정보
            - template_text: 템플릿 내용
            - variables: 사용된 변수들
            - metadata: 메타데이터

    Raises:
        ValueError: 입력 데이터가 유효하지 않은 경우
        APIError: LLM API 호출 실패 시

    Example:
        >>> analysis = {"business_type": "교육", "service_type": "신청"}
        >>> context = "정책 컨텍스트"
        >>> result = generate_template(analysis, context)
        >>> print(result["template_text"])
    """
    pass
```

### 2. 에러 처리

#### 커스텀 예외 정의
```python
class KakaoTemplateError(Exception):
    """기본 예외 클래스"""
    pass

class TemplateGenerationError(KakaoTemplateError):
    """템플릿 생성 실패"""
    pass

class PolicyViolationError(KakaoTemplateError):
    """정책 위반"""
    pass

class APIConnectionError(KakaoTemplateError):
    """API 연결 실패"""
    pass
```

#### 에러 처리 패턴
```python
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def safe_api_call(
    func: callable,
    *args,
    **kwargs
) -> Optional[Any]:
    """안전한 API 호출 래퍼"""
    try:
        return func(*args, **kwargs)
    except APIConnectionError as e:
        logger.error(f"API 연결 실패: {e}")
        return None
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise
```

### 3. 로깅 표준

#### 로그 설정
```python
import logging
from datetime import datetime

# 로거 설정
def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """로거 설정"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # 포맷터
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러
    file_handler = logging.FileHandler(f'logs/{name}.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
```

#### 로그 레벨 가이드
- **DEBUG**: 개발 중 상세 정보
- **INFO**: 일반적인 동작 정보
- **WARNING**: 주의가 필요한 상황
- **ERROR**: 에러 발생 시
- **CRITICAL**: 시스템 중단 위험

## 🧪 테스트 가이드

### 1. 테스트 구조
```
tests/
├── unit/                    # 단위 테스트
│   ├── test_agents/        # 에이전트 테스트
│   ├── test_utils/         # 유틸리티 테스트
│   └── test_workflow/      # 워크플로우 테스트
├── integration/            # 통합 테스트
│   ├── test_api/          # API 테스트
│   └── test_database/     # 데이터베이스 테스트
├── e2e/                    # End-to-End 테스트
└── fixtures/               # 테스트 데이터
```

### 2. 단위 테스트 작성

#### pytest 기본 사용법
```python
import pytest
from src.agents.request_analyzer import RequestAnalyzer

class TestRequestAnalyzer:
    """요청 분석기 테스트"""

    @pytest.fixture
    def analyzer(self):
        """분석기 인스턴스"""
        return RequestAnalyzer()

    def test_analyze_education_request(self, analyzer):
        """교육업 요청 분석 테스트"""
        request = "온라인 강의 수강 신청 완료 안내"
        result = analyzer.analyze_request(request)

        assert result["business_type"] == "교육"
        assert result["service_type"] == "신청"
        assert "수신자명" in result["required_variables"]

    @pytest.mark.parametrize("request,expected_type", [
        ("피자 주문 완료", "음식점"),
        ("진료 예약 확정", "의료"),
        ("상품 배송 시작", "쇼핑몰")
    ])
    def test_business_type_classification(self, analyzer, request, expected_type):
        """업종 분류 테스트"""
        result = analyzer.analyze_request(request)
        assert result["business_type"] == expected_type
```

#### Mock 사용법
```python
from unittest.mock import Mock, patch
import pytest

class TestTemplateGenerator:
    """템플릿 생성기 테스트"""

    @patch('src.utils.llm_client.ClaudeLLMClient')
    def test_generate_template_success(self, mock_llm):
        """템플릿 생성 성공 테스트"""
        # Mock 설정
        mock_llm.return_value.generate_response.return_value = "Generated template"

        generator = TemplateGenerator(mock_llm.return_value)
        result = generator.generate_template({}, "context")

        assert result["success"] is True
        assert "template_text" in result
```

### 3. 통합 테스트

#### API 테스트
```python
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_generate_template_endpoint():
    """템플릿 생성 엔드포인트 테스트"""
    response = client.post(
        "/api/v1/templates/generate",
        json={
            "user_request": "피자 주문 완료 안내",
            "business_type": "음식점"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "template" in data
```

### 4. 테스트 실행

#### 기본 테스트 실행
```bash
# 모든 테스트 실행
pytest

# 특정 디렉토리만
pytest tests/unit/

# 커버리지 포함
pytest --cov=src tests/

# 상세 출력
pytest -v tests/
```

#### 성능 테스트
```python
import time
import pytest

class TestPerformance:
    """성능 테스트"""

    def test_template_generation_speed(self):
        """템플릿 생성 속도 테스트"""
        start_time = time.time()

        # 템플릿 생성 코드
        generator = TemplateGenerator()
        result = generator.generate_template({}, "context")

        end_time = time.time()
        duration = end_time - start_time

        # 3초 이내 응답
        assert duration < 3.0
        assert result["success"] is True
```

## 🔌 API 개발

### 1. 새로운 엔드포인트 추가

#### 라우터 생성
```python
from fastapi import APIRouter, Depends, HTTPException
from ..models.schemas import NewRequest, NewResponse

router = APIRouter(prefix="/api/v1/new-feature", tags=["new-feature"])

@router.post("/process", response_model=NewResponse)
async def process_new_feature(
    request: NewRequest,
    current_user: str = Depends(get_current_user)
) -> NewResponse:
    """새 기능 처리"""
    try:
        # 처리 로직
        result = process_feature(request)
        return NewResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### 스키마 정의
```python
from pydantic import BaseModel, Field
from typing import Optional, List

class NewRequest(BaseModel):
    """새 기능 요청 모델"""

    input_data: str = Field(..., description="입력 데이터")
    options: Optional[Dict[str, Any]] = Field(None, description="옵션")

    class Config:
        schema_extra = {
            "example": {
                "input_data": "예시 입력",
                "options": {"key": "value"}
            }
        }

class NewResponse(BaseModel):
    """새 기능 응답 모델"""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
```

### 2. 미들웨어 개발

#### 커스텀 미들웨어
```python
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time

class TimingMiddleware(BaseHTTPMiddleware):
    """요청 처리 시간 측정 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        return response
```

### 3. 의존성 주입

#### 의존성 함수
```python
from fastapi import Depends, HTTPException
from ..utils.llm_client import ClaudeLLMClient

def get_llm_client() -> ClaudeLLMClient:
    """LLM 클라이언트 의존성"""
    try:
        return ClaudeLLMClient()
    except Exception as e:
        raise HTTPException(status_code=503, detail="LLM service unavailable")

def get_current_user(token: str = Depends(get_token)) -> str:
    """현재 사용자 정보"""
    # 토큰 검증 로직
    return user_id
```

## 🔄 워크플로우 개발

### 1. LangGraph 노드 생성

#### 새 노드 추가
```python
from langgraph.graph import StateGraph, Node
from typing import Dict, Any

def new_processing_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """새로운 처리 노드"""
    input_data = state.get("input_data")

    # 처리 로직
    result = process_data(input_data)

    # 상태 업데이트
    state["processed_data"] = result
    state["processing_complete"] = True

    return state
```

#### 조건부 라우팅
```python
def routing_condition(state: Dict[str, Any]) -> str:
    """라우팅 조건 함수"""
    score = state.get("quality_score", 0)

    if score >= 90:
        return "high_quality_path"
    elif score >= 70:
        return "medium_quality_path"
    else:
        return "improvement_path"
```

### 2. 워크플로우 확장

#### 새 워크플로우 생성
```python
class CustomWorkflow:
    """커스텀 워크플로우"""

    def __init__(self):
        self.graph = StateGraph(WorkflowState)
        self._build_graph()

    def _build_graph(self):
        """그래프 구성"""
        # 노드 추가
        self.graph.add_node("start", self.start_node)
        self.graph.add_node("process", self.process_node)
        self.graph.add_node("end", self.end_node)

        # 엣지 추가
        self.graph.add_edge("start", "process")
        self.graph.add_conditional_edges(
            "process",
            self.routing_condition,
            {
                "continue": "end",
                "retry": "process"
            }
        )

        # 시작/종료 노드 설정
        self.graph.set_entry_point("start")
        self.graph.set_finish_point("end")
```

## 📦 패키지 관리

### 1. 의존성 관리

#### requirements.txt 업데이트
```bash
# 새 패키지 설치
pip install new-package

# requirements.txt 업데이트
pip freeze > requirements.txt

# 또는 pipreqs 사용 (더 정확함)
pipreqs . --force
```

#### 보안 취약점 검사
```bash
# 보안 취약점 검사
pip-audit

# 패키지 업데이트
pip-review --local --auto
```

### 2. 버전 관리

#### 시맨틱 버저닝
- **Major (X.0.0)**: 호환되지 않는 API 변경
- **Minor (0.X.0)**: 호환되는 기능 추가
- **Patch (0.0.X)**: 호환되는 버그 수정

#### 버전 업데이트 체크리스트
1. CHANGELOG.md 업데이트
2. 버전 번호 변경 (src/__init__.py)
3. 테스트 실행 및 통과 확인
4. 문서 업데이트
5. Git 태그 생성

## 🚀 배포 및 CI/CD

### 1. GitHub Actions 설정

#### .github/workflows/ci.yml
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

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
        pytest --cov=src tests/

    - name: Run linting
      run: |
        flake8 src/
        black --check src/
        isort --check src/

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### 2. Docker 배포

#### Dockerfile 최적화
```dockerfile
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사
COPY requirements.txt .

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY src/ ./src/
COPY data/ ./data/

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

# 포트 노출
EXPOSE 8000

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# 애플리케이션 실행
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📊 모니터링 및 로깅

### 1. 성능 모니터링

#### 메트릭 수집
```python
import time
from functools import wraps
from typing import Dict, Any

class PerformanceMonitor:
    """성능 모니터링 클래스"""

    def __init__(self):
        self.metrics = {}

    def track_execution_time(self, func_name: str):
        """실행 시간 추적 데코레이터"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()

                execution_time = end_time - start_time
                self.metrics[func_name] = {
                    "execution_time": execution_time,
                    "timestamp": time.time()
                }

                return result
            return wrapper
        return decorator
```

### 2. 구조화된 로깅

#### JSON 로깅
```python
import json
import logging
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """JSON 형태 로그 포맷터"""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # 추가 정보가 있으면 포함
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id

        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id

        return json.dumps(log_entry)
```

## 🔐 보안 개발 가이드

### 1. 입력 검증

#### 데이터 검증
```python
from pydantic import BaseModel, validator
import re

class SecureRequest(BaseModel):
    """보안이 강화된 요청 모델"""

    user_input: str

    @validator('user_input')
    def validate_user_input(cls, v):
        # SQL 인젝션 방지
        forbidden_patterns = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP']
        if any(pattern in v.upper() for pattern in forbidden_patterns):
            raise ValueError('Invalid input detected')

        # XSS 방지
        if '<script>' in v.lower() or 'javascript:' in v.lower():
            raise ValueError('Script content not allowed')

        # 길이 제한
        if len(v) > 1000:
            raise ValueError('Input too long')

        return v
```

### 2. API 키 보안

#### 환경 변수 관리
```python
import os
from typing import Optional

class SecureConfig:
    """보안 설정 클래스"""

    @property
    def api_key(self) -> str:
        """API 키 가져오기"""
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("API key not configured")
        return key

    @property
    def database_url(self) -> str:
        """데이터베이스 URL (마스킹됨)"""
        url = os.getenv("DATABASE_URL")
        if url:
            # 로그에서는 마스킹
            return url.replace(url[10:30], "*" * 20)
        return ""
```

---

**📅 작성일**: 2024년 9월 19일
**✍️ 작성자**: Final Team 3 AI
**📄 문서 버전**: 1.0
**🔄 최종 수정**: 2024년 9월 19일