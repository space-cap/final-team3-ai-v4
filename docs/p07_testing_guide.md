# P07. 테스트 가이드 (Testing Guide)

## 🧪 테스트 개요

이 문서는 카카오 알림톡 템플릿 자동 생성 AI 서비스의 다양한 테스트 방법과 전략을 설명합니다. 개발자와 사용자 모두를 위한 포괄적인 테스트 가이드를 제공합니다.

## 📋 테스트 레벨

### 1. 단위 테스트 (Unit Tests)
개별 함수나 클래스의 기능을 독립적으로 테스트

### 2. 통합 테스트 (Integration Tests)
여러 컴포넌트 간의 상호작용을 테스트

### 3. 시스템 테스트 (System Tests)
전체 시스템의 End-to-End 기능을 테스트

### 4. 성능 테스트 (Performance Tests)
시스템의 성능과 확장성을 테스트

### 5. 사용자 테스트 (User Acceptance Tests)
실제 사용자 시나리오 기반 테스트

## 🛠 개발자 테스트

### 환경 설정

#### 테스트 의존성 설치
```bash
# 기본 테스트 도구
pip install pytest pytest-cov pytest-mock pytest-asyncio

# 추가 테스트 도구
pip install factory-boy faker httpx

# 성능 테스트
pip install pytest-benchmark locust
```

#### 테스트 환경 변수 설정
```bash
# .env.test 파일 생성
cp .env.example .env.test

# 테스트용 설정 수정
ENVIRONMENT=testing
ANTHROPIC_API_KEY=test-key-for-mock
DATABASE_URL=sqlite:///test.db
LOG_LEVEL=DEBUG
```

### 단위 테스트 작성

#### 1. 에이전트 테스트

**Request Analyzer 테스트**:
```python
# tests/unit/test_request_analyzer.py
import pytest
from src.agents.request_analyzer import RequestAnalyzer

class TestRequestAnalyzer:
    """요청 분석 에이전트 테스트"""

    @pytest.fixture
    def analyzer(self):
        return RequestAnalyzer()

    @pytest.mark.parametrize("request,expected_business", [
        ("피자 주문 완료 안내", "음식점"),
        ("온라인 강의 수강 신청", "교육"),
        ("치과 진료 예약 확정", "의료"),
        ("쇼핑몰 상품 배송 안내", "쇼핑몰")
    ])
    def test_business_type_classification(self, analyzer, request, expected_business):
        """업종 분류 정확성 테스트"""
        result = analyzer._classify_by_keywords({}, request)
        assert result["business_type"] == expected_business

    def test_confidence_score_calculation(self, analyzer):
        """신뢰도 점수 계산 테스트"""
        request = "온라인 파이썬 프로그래밍 강의 수강 신청 완료"
        result = analyzer.analyze_request(request)

        assert result["confidence_score"] >= 0.8
        assert result["business_type"] == "교육"
        assert "강의명" in result["required_variables"]

    def test_edge_cases(self, analyzer):
        """엣지 케이스 테스트"""
        edge_cases = [
            "",  # 빈 문자열
            "a" * 2000,  # 매우 긴 문자열
            "특수문자!@#$%^&*()",  # 특수문자
            "123456789",  # 숫자만
        ]

        for case in edge_cases:
            result = analyzer.analyze_request(case)
            # 기본값이 설정되어야 함
            assert "business_type" in result
            assert "service_type" in result
```

**Template Generator 테스트**:
```python
# tests/unit/test_template_generator.py
import pytest
from unittest.mock import Mock, patch
from src.agents.template_generator import TemplateGenerator

class TestTemplateGenerator:
    """템플릿 생성 에이전트 테스트"""

    @pytest.fixture
    def mock_llm_client(self):
        mock_client = Mock()
        mock_client.generate_template.return_value = {
            "template_text": "안녕하세요 #{수신자명}님...",
            "variables": ["수신자명", "상품명"]
        }
        return mock_client

    @pytest.fixture
    def mock_template_store(self):
        mock_store = Mock()
        mock_store.find_similar_templates.return_value = [
            {
                "text": "참고 템플릿",
                "metadata": {"business_type": "교육"}
            }
        ]
        return mock_store

    def test_template_generation_success(self, mock_llm_client, mock_template_store):
        """템플릿 생성 성공 테스트"""
        generator = TemplateGenerator(mock_llm_client, mock_template_store)

        analysis = {
            "business_type": "교육",
            "service_type": "신청",
            "required_variables": ["수신자명", "강의명"]
        }

        result = generator.generate_template(analysis, "정책 컨텍스트")

        assert result["success"] is True
        assert "template_text" in result
        assert len(result["variables"]) > 0

    def test_template_optimization(self, mock_llm_client, mock_template_store):
        """템플릿 최적화 테스트"""
        generator = TemplateGenerator(mock_llm_client, mock_template_store)

        original_template = "안녕하세요. 주문이 완료되었습니다."
        feedback = {"missing_variables": ["수신자명"]}

        optimized = generator._optimize_template(original_template, feedback)

        assert "#{수신자명}" in optimized
        assert "안녕하세요" in optimized

    @patch('src.agents.template_generator.time.time')
    def test_generation_timeout(self, mock_time, mock_llm_client, mock_template_store):
        """생성 타임아웃 테스트"""
        # 타임아웃 시뮬레이션
        mock_time.side_effect = [0, 10, 20, 35]  # 35초 경과

        generator = TemplateGenerator(mock_llm_client, mock_template_store)

        with pytest.raises(TimeoutError):
            generator.generate_template({}, "", timeout=30)
```

#### 2. 유틸리티 테스트

**LLM Client 테스트**:
```python
# tests/unit/test_llm_client.py
import pytest
from unittest.mock import Mock, patch
from src.utils.llm_client import ClaudeLLMClient

class TestClaudeLLMClient:
    """Claude LLM 클라이언트 테스트"""

    @pytest.fixture
    def mock_anthropic(self):
        with patch('src.utils.llm_client.ChatAnthropic') as mock:
            mock_instance = Mock()
            mock.return_value = mock_instance
            mock_instance.invoke.return_value.content = "테스트 응답"
            yield mock_instance

    def test_client_initialization(self):
        """클라이언트 초기화 테스트"""
        client = ClaudeLLMClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.model == "claude-3-5-haiku-latest"

    def test_api_key_validation(self):
        """API 키 검증 테스트"""
        with pytest.raises(ValueError, match="API key must be provided"):
            ClaudeLLMClient(api_key=None)

    def test_generate_response(self, mock_anthropic):
        """응답 생성 테스트"""
        client = ClaudeLLMClient(api_key="test-key")

        response = client.generate_response(
            "시스템 프롬프트",
            "사용자 프롬프트"
        )

        assert response == "테스트 응답"
        mock_anthropic.invoke.assert_called_once()

    def test_retry_mechanism(self, mock_anthropic):
        """재시도 메커니즘 테스트"""
        # 첫 번째와 두 번째 호출은 실패, 세 번째는 성공
        mock_anthropic.invoke.side_effect = [
            Exception("API Error"),
            Exception("Network Error"),
            Mock(content="성공 응답")
        ]

        client = ClaudeLLMClient(api_key="test-key")
        response = client.generate_response("system", "user")

        assert response == "성공 응답"
        assert mock_anthropic.invoke.call_count == 3
```

### 통합 테스트

#### 1. API 통합 테스트

```python
# tests/integration/test_api_integration.py
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

class TestAPIIntegration:
    """API 통합 테스트"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_health_endpoint(self, client):
        """헬스체크 엔드포인트 테스트"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_template_generation_flow(self, client):
        """템플릿 생성 플로우 테스트"""
        request_data = {
            "user_request": "피자 주문 완료 안내 메시지",
            "business_type": "음식점",
            "tone": "친근한"
        }

        response = client.post("/api/v1/templates/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "template" in data
        assert "compliance" in data

    def test_error_handling(self, client):
        """에러 처리 테스트"""
        # 잘못된 요청 데이터
        invalid_data = {"user_request": ""}

        response = client.post("/api/v1/templates/generate", json=invalid_data)

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client):
        """동시 요청 처리 테스트"""
        import asyncio
        import httpx

        async def make_request():
            async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/api/v1/templates/generate",
                    json={"user_request": "테스트 요청"}
                )
                return response.status_code

        # 10개의 동시 요청
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # 모든 요청이 성공적으로 처리되어야 함
        assert all(status == 200 for status in results)
```

#### 2. 데이터베이스 통합 테스트

```python
# tests/integration/test_database_integration.py
import pytest
import tempfile
import shutil
from src.database.vector_store import PolicyVectorStore, TemplateStore

class TestDatabaseIntegration:
    """데이터베이스 통합 테스트"""

    @pytest.fixture
    def temp_db_dir(self):
        """임시 데이터베이스 디렉토리"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def vector_store(self, temp_db_dir):
        """벡터 스토어 인스턴스"""
        return PolicyVectorStore(persist_directory=temp_db_dir)

    def test_policy_document_loading(self, vector_store):
        """정책 문서 로딩 테스트"""
        # 테스트용 정책 문서 생성
        test_policy_dir = "tests/fixtures/test_policies"

        vector_store.load_policy_documents(test_policy_dir)

        # 검색 테스트
        results = vector_store.search_relevant_policies("알림톡 승인", k=3)

        assert len(results) > 0
        assert all("content" in result for result in results)

    def test_template_store_operations(self):
        """템플릿 스토어 연산 테스트"""
        template_store = TemplateStore("tests/fixtures/test_templates.json")

        # 업종별 템플릿 검색
        education_templates = template_store.get_templates_by_business_type("교육")
        assert len(education_templates) > 0

        # 승인된 템플릿만 필터링
        approved_templates = template_store.get_approved_templates()
        assert all(
            t["metadata"]["approval_status"] == "approved"
            for t in approved_templates
        )

    def test_data_consistency(self, vector_store):
        """데이터 일관성 테스트"""
        # 동일한 검색어로 여러 번 검색
        query = "알림톡 템플릿"

        results1 = vector_store.search_relevant_policies(query, k=5)
        results2 = vector_store.search_relevant_policies(query, k=5)

        # 결과가 일관되어야 함
        assert len(results1) == len(results2)
        assert results1[0]["content"] == results2[0]["content"]
```

### 시스템 테스트

#### End-to-End 테스트

```python
# tests/e2e/test_complete_workflow.py
import pytest
from src.workflow.langgraph_workflow import TemplateGenerationWorkflow

class TestCompleteWorkflow:
    """완전한 워크플로우 E2E 테스트"""

    @pytest.fixture
    def workflow(self):
        return TemplateGenerationWorkflow()

    @pytest.mark.slow
    def test_education_template_workflow(self, workflow):
        """교육업 템플릿 생성 워크플로우"""
        input_data = {
            "user_request": "온라인 파이썬 프로그래밍 강의 수강 신청 완료 안내",
            "business_type": "교육"
        }

        result = workflow.run(input_data)

        # 워크플로우 완료 확인
        assert result["success"] is True
        assert result["final_result"]["compliance"]["score"] >= 80

        # 템플릿 품질 확인
        template_text = result["final_result"]["template"]["text"]
        assert "안녕하세요" in template_text
        assert "#{" in template_text  # 변수 포함
        assert "정보성" in template_text or "안내" in template_text

    @pytest.mark.slow
    def test_multiple_iterations_workflow(self, workflow):
        """다중 반복 개선 워크플로우"""
        input_data = {
            "user_request": "모호한 요청",  # 의도적으로 모호한 요청
            "auto_refine": True
        }

        result = workflow.run(input_data)

        # 반복 개선 확인
        assert result["iterations"] > 1
        final_score = result["final_result"]["compliance"]["score"]
        initial_score = result["history"][0]["compliance"]["score"]
        assert final_score > initial_score

    @pytest.mark.parametrize("business_type,expected_keywords", [
        ("교육", ["강의", "수강", "학습"]),
        ("의료", ["진료", "예약", "병원"]),
        ("음식점", ["주문", "메뉴", "픽업"]),
        ("쇼핑몰", ["주문", "배송", "상품"])
    ])
    def test_business_specific_templates(self, workflow, business_type, expected_keywords):
        """업종별 특화 템플릿 테스트"""
        input_data = {
            "user_request": f"{business_type} 서비스 완료 안내",
            "business_type": business_type
        }

        result = workflow.run(input_data)
        template_text = result["final_result"]["template"]["text"]

        # 업종 관련 키워드 포함 확인
        assert any(keyword in template_text for keyword in expected_keywords)
```

### 성능 테스트

#### 1. 응답 시간 테스트

```python
# tests/performance/test_response_time.py
import pytest
import time
from src.api.main import app
from fastapi.testclient import TestClient

class TestPerformance:
    """성능 테스트"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_template_generation_speed(self, client):
        """템플릿 생성 속도 테스트"""
        request_data = {
            "user_request": "피자 주문 완료 안내",
            "business_type": "음식점"
        }

        start_time = time.time()
        response = client.post("/api/v1/templates/generate", json=request_data)
        end_time = time.time()

        response_time = end_time - start_time

        # 5초 이내 응답
        assert response_time < 5.0
        assert response.status_code == 200

    @pytest.mark.benchmark
    def test_concurrent_performance(self, client):
        """동시 처리 성능 테스트"""
        import concurrent.futures

        def make_request():
            return client.post(
                "/api/v1/templates/generate",
                json={"user_request": "테스트 요청"}
            )

        # 50개 동시 요청
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            start_time = time.time()
            futures = [executor.submit(make_request) for _ in range(50)]
            responses = [future.result() for future in futures]
            end_time = time.time()

        total_time = end_time - start_time
        successful_requests = sum(1 for r in responses if r.status_code == 200)

        # 성능 기준
        assert total_time < 60.0  # 1분 이내
        assert successful_requests >= 45  # 90% 이상 성공
```

#### 2. 메모리 사용량 테스트

```python
# tests/performance/test_memory_usage.py
import pytest
import psutil
import os
from src.workflow.langgraph_workflow import TemplateGenerationWorkflow

class TestMemoryUsage:
    """메모리 사용량 테스트"""

    def test_memory_consumption(self):
        """메모리 소비량 테스트"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 대량 템플릿 생성
        workflow = TemplateGenerationWorkflow()

        for i in range(100):
            result = workflow.run({
                "user_request": f"테스트 요청 {i}",
                "business_type": "교육"
            })

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # 메모리 증가량이 500MB 이하
        assert memory_increase < 500

    def test_memory_leak_detection(self):
        """메모리 누수 감지 테스트"""
        import gc

        process = psutil.Process(os.getpid())
        workflow = TemplateGenerationWorkflow()

        memory_readings = []

        for cycle in range(10):
            # 50개 요청 처리
            for i in range(50):
                workflow.run({"user_request": f"테스트 {i}"})

            # 가비지 컬렉션 강제 실행
            gc.collect()

            # 메모리 사용량 기록
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_readings.append(current_memory)

        # 메모리 사용량이 지속적으로 증가하지 않아야 함
        memory_trend = memory_readings[-1] - memory_readings[0]
        assert memory_trend < 50  # 50MB 미만 증가
```

## 👥 사용자 테스트

### 수동 테스트 시나리오

#### 1. 기본 기능 테스트

**시나리오 1: 교육업 템플릿 생성**
```
1. 웹 브라우저에서 http://localhost:8000/docs 접속
2. POST /api/v1/templates/generate 엔드포인트 클릭
3. "Try it out" 버튼 클릭
4. 다음 데이터 입력:
   {
     "user_request": "온라인 영어 강의 수강 신청 완료 안내",
     "business_type": "교육",
     "tone": "정중한"
   }
5. Execute 버튼 클릭
6. 응답 확인:
   - success: true
   - compliance.score >= 85
   - template.text에 인사말 포함
   - variables 배열에 적절한 변수들 포함
```

**시나리오 2: 의료업 템플릿 생성**
```
1. 동일한 인터페이스에서
2. 다음 데이터 입력:
   {
     "user_request": "치과 진료 예약 확정 및 내원 시 준비사항 안내",
     "business_type": "의료"
   }
3. 결과 확인:
   - 의료업 특화 용어 사용
   - 예약 관련 변수 포함
   - 준비사항 안내 내용 포함
```

#### 2. 오류 처리 테스트

**시나리오 3: 잘못된 입력 처리**
```
1. 빈 요청으로 테스트:
   {"user_request": ""}
2. 예상 결과:
   - 400 Bad Request
   - 적절한 오류 메시지

3. 매우 긴 요청으로 테스트:
   {"user_request": "a" * 2000}
4. 예상 결과:
   - 정상 처리 또는 적절한 길이 제한 메시지
```

### 자동화된 사용자 테스트

#### Selenium을 이용한 웹 UI 테스트

```python
# tests/user/test_web_interface.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestWebInterface:
    """웹 인터페이스 사용자 테스트"""

    @pytest.fixture
    def driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # CI 환경용
        driver = webdriver.Chrome(options=options)
        yield driver
        driver.quit()

    def test_swagger_ui_accessibility(self, driver):
        """Swagger UI 접근성 테스트"""
        driver.get("http://localhost:8000/docs")

        # 페이지 로딩 대기
        wait = WebDriverWait(driver, 10)

        # Swagger UI 로딩 확인
        swagger_ui = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "swagger-ui"))
        )
        assert swagger_ui is not None

    def test_api_endpoint_interaction(self, driver):
        """API 엔드포인트 상호작용 테스트"""
        driver.get("http://localhost:8000/docs")
        wait = WebDriverWait(driver, 10)

        # generate 엔드포인트 클릭
        generate_endpoint = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), '/api/v1/templates/generate')]"))
        )
        generate_endpoint.click()

        # Try it out 버튼 클릭
        try_it_out = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Try it out')]"))
        )
        try_it_out.click()

        # 요청 데이터 입력
        request_body = driver.find_element(By.CLASS_NAME, "body-param__text")
        test_data = '{"user_request": "피자 주문 완료 안내"}'
        request_body.clear()
        request_body.send_keys(test_data)

        # Execute 버튼 클릭
        execute_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Execute')]")
        execute_button.click()

        # 응답 확인
        response_body = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "response-col_description"))
        )
        assert "success" in response_body.text
```

### 부하 테스트

#### Locust를 이용한 부하 테스트

```python
# tests/load/locustfile.py
from locust import HttpUser, task, between
import json

class TemplateGenerationUser(HttpUser):
    """템플릿 생성 사용자 시뮬레이션"""

    wait_time = between(1, 3)  # 1-3초 대기

    def on_start(self):
        """테스트 시작 시 실행"""
        self.test_requests = [
            "피자 주문 완료 안내",
            "온라인 강의 수강 신청 완료",
            "치과 진료 예약 확정",
            "쇼핑몰 상품 배송 시작",
            "헬스장 회원권 등록 완료"
        ]

    @task(3)
    def generate_template(self):
        """템플릿 생성 작업 (가중치 3)"""
        import random

        request_data = {
            "user_request": random.choice(self.test_requests),
            "tone": random.choice(["정중한", "친근한", "공식적인"])
        }

        with self.client.post(
            "/api/v1/templates/generate",
            json=request_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("success"):
                    response.success()
                else:
                    response.failure("API returned success=false")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)
    def health_check(self):
        """헬스체크 작업 (가중치 1)"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(1)
    def validate_template(self):
        """템플릿 검증 작업 (가중치 1)"""
        template_data = {
            "template_text": "안녕하세요 #{수신자명}님, 주문이 완료되었습니다.",
            "variables": ["수신자명"],
            "business_type": "음식점"
        }

        with self.client.post(
            "/api/v1/templates/validate",
            json=template_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Validation failed: {response.status_code}")
```

**부하 테스트 실행**:
```bash
# 10명 사용자, 초당 2명씩 증가, 60초간 테스트
locust -f tests/load/locustfile.py --host=http://localhost:8000 -u 10 -r 2 -t 60s --headless

# 웹 UI로 실행
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

## 📊 테스트 실행 및 리포팅

### 테스트 실행 명령어

#### 기본 테스트 실행
```bash
# 모든 테스트 실행
pytest

# 특정 디렉토리만
pytest tests/unit/

# 특정 파일만
pytest tests/unit/test_request_analyzer.py

# 특정 테스트 함수만
pytest tests/unit/test_request_analyzer.py::TestRequestAnalyzer::test_business_type_classification

# 마커 기반 실행
pytest -m "not slow"  # slow 마커가 없는 테스트만
pytest -m "integration"  # integration 마커가 있는 테스트만
```

#### 커버리지 포함 실행
```bash
# 커버리지 측정
pytest --cov=src tests/

# HTML 리포트 생성
pytest --cov=src --cov-report=html tests/

# 커버리지 임계값 설정
pytest --cov=src --cov-fail-under=80 tests/
```

#### 병렬 테스트 실행
```bash
# pytest-xdist 설치
pip install pytest-xdist

# 병렬 실행
pytest -n auto  # CPU 코어 수만큼
pytest -n 4     # 4개 프로세스
```

### 테스트 설정

#### pytest.ini
```ini
[tool:pytest]
minversion = 6.0
addopts =
    -ra
    --strict-markers
    --strict-config
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80
testpaths = tests
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    e2e: marks tests as end-to-end tests
    benchmark: marks tests as performance benchmarks
```

#### conftest.py
```python
# tests/conftest.py
import pytest
import asyncio
from unittest.mock import Mock

@pytest.fixture(scope="session")
def event_loop():
    """세션 범위 이벤트 루프"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_api_key():
    """테스트용 API 키"""
    return "test-api-key-for-testing"

@pytest.fixture
def sample_template_data():
    """샘플 템플릿 데이터"""
    return {
        "text": "안녕하세요 #{수신자명}님...",
        "variables": ["수신자명", "상품명"],
        "metadata": {
            "business_type": "교육",
            "approval_status": "approved"
        }
    }

@pytest.fixture
def mock_vector_store():
    """모킹된 벡터 스토어"""
    mock_store = Mock()
    mock_store.search_relevant_policies.return_value = [
        {
            "content": "정책 내용",
            "metadata": {"source": "test.md"},
            "relevance_score": 0.9
        }
    ]
    return mock_store
```

### CI/CD 통합

#### GitHub Actions 워크플로우
```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run unit tests
      run: |
        pytest tests/unit/ -v

    - name: Run integration tests
      run: |
        pytest tests/integration/ -v
      env:
        ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

    - name: Run E2E tests
      run: |
        pytest tests/e2e/ -v --timeout=300
      env:
        ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### 테스트 리포팅

#### HTML 커버리지 리포트
```bash
# 커버리지 리포트 생성
pytest --cov=src --cov-report=html tests/

# 리포트 확인
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

#### JUnit XML 리포트
```bash
# JUnit 형식 리포트 생성
pytest --junitxml=test-results.xml tests/
```

#### 성능 리포트
```bash
# 벤치마크 리포트
pytest --benchmark-only --benchmark-save=baseline tests/
pytest --benchmark-compare=baseline tests/
```

---

**📅 작성일**: 2024년 9월 19일
**✍️ 작성자**: Final Team 3 AI
**📄 문서 버전**: 1.0
**🔄 최종 수정**: 2024년 9월 19일