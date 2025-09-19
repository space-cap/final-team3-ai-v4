# P02. 시스템 아키텍처 (System Architecture)

## 🏗 전체 아키텍처 개요

### 아키텍처 설계 철학
본 시스템은 **모듈화**, **확장성**, **신뢰성**을 핵심 원칙으로 설계되었습니다.

```
┌─────────────────────────────────────────────────────────┐
│                    사용자 인터페이스                      │
├─────────────────────────────────────────────────────────┤
│  Web UI  │  REST API  │  CLI Tool  │  Interactive Mode  │
├─────────────────────────────────────────────────────────┤
│                    FastAPI Gateway                     │
├─────────────────────────────────────────────────────────┤
│                  LangGraph Workflow                    │
├─────────────────┬──────────────┬────────────────────────┤
│ Request Analyzer│Template Gen. │ Compliance Checker     │
├─────────────────┼──────────────┼────────────────────────┤
│                 Policy RAG Agent                       │
├─────────────────┬──────────────┬────────────────────────┤
│   Vector DB     │   Template   │     LLM Client         │
│  (Chroma DB)    │     Store    │   (Claude API)         │
└─────────────────┴──────────────┴────────────────────────┘
```

## 🧩 핵심 컴포넌트 상세

### 1. FastAPI Gateway Layer

#### 역할 및 책임
- HTTP 요청 라우팅 및 처리
- 인증 및 권한 관리
- 요청/응답 검증
- 에러 핸들링 및 로깅

#### 주요 엔드포인트
```python
# 템플릿 생성
POST /api/v1/templates/generate
{
    "user_request": "강의 수강 신청 완료 안내",
    "business_type": "교육",
    "tone": "정중한"
}

# 템플릿 검증
POST /api/v1/templates/validate
{
    "template_text": "생성된 템플릿 내용",
    "business_type": "교육"
}

# 시스템 상태
GET /health
GET /stats
```

#### 미들웨어 구성
- **CORS Middleware**: 브라우저 Cross-Origin 요청 허용
- **Trusted Host Middleware**: 허용된 호스트만 접근 가능
- **Request Logging**: 모든 요청 로깅
- **Rate Limiting**: API 사용량 제한

### 2. LangGraph Workflow Engine

#### 워크플로우 설계
```python
# 워크플로우 상태 정의
class WorkflowState(TypedDict):
    user_request: str
    request_analysis: Dict[str, Any]
    policy_context: str
    generated_template: Dict[str, Any]
    compliance_result: Dict[str, Any]
    iterations: int
    final_result: Dict[str, Any]
```

#### 노드 구성
1. **분석 노드** (analyze_request)
   - 사용자 요청 분석
   - 업종 및 서비스 분류
   - 필요 변수 추출

2. **정책 검색 노드** (search_policies)
   - 관련 정책 문서 검색
   - 컨텍스트 구성
   - 예시 템플릿 제공

3. **생성 노드** (generate_template)
   - 정책 기반 템플릿 생성
   - 변수 및 버튼 설정
   - 초기 최적화

4. **검증 노드** (check_compliance)
   - 정책 준수 검증
   - 위반사항 식별
   - 개선점 제안

5. **개선 노드** (refine_template)
   - 피드백 기반 개선
   - 재생성 로직
   - 품질 향상

#### 조건부 라우팅
```python
def should_refine(state: WorkflowState) -> str:
    """개선 필요 여부 판단"""
    compliance = state.get("compliance_result", {})
    score = compliance.get("score", 0)
    iterations = state.get("iterations", 0)

    if score >= 85 or iterations >= 3:
        return "finish"
    else:
        return "refine"
```

### 3. Multi-Agent System

#### Agent 설계 원칙
- **단일 책임 원칙**: 각 에이전트는 특정 작업에 특화
- **느슨한 결합**: 에이전트 간 독립적 동작
- **재사용 가능성**: 다양한 워크플로우에서 활용

#### 3.1 Request Analyzer Agent
```python
class RequestAnalyzer:
    """사용자 요청 분석 에이전트"""

    def analyze_request(self, user_request: str) -> Dict[str, Any]:
        """
        요청 분석 수행

        출력:
        - business_type: 업종 분류
        - service_type: 서비스 유형
        - message_purpose: 메시지 목적
        - required_variables: 필요 변수
        - tone: 권장 톤앤매너
        """
```

**분류 알고리즘**:
1. **키워드 기반 1차 분류**
2. **LLM 기반 정밀 분석**
3. **신뢰도 점수 계산**
4. **예외 상황 처리**

#### 3.2 Policy RAG Agent
```python
class PolicyRAGAgent:
    """정책 문서 검색 및 컨텍스트 제공 에이전트"""

    def search_relevant_policies(self, query: str) -> str:
        """관련 정책 검색"""

    def get_template_examples(self, business_type: str) -> List[Dict]:
        """업종별 예시 템플릿 제공"""

    def validate_against_blacklist(self, content: str) -> Dict[str, Any]:
        """금지 항목 검증"""
```

**검색 전략**:
- **의미적 유사도**: 벡터 임베딩 기반 검색
- **키워드 매칭**: 정확한 용어 매칭
- **카테고리 필터링**: 업종/정책 유형별 필터
- **스코어 기반 랭킹**: 관련도 순 정렬

#### 3.3 Template Generator Agent
```python
class TemplateGenerator:
    """템플릿 생성 에이전트"""

    def generate_template(self, analysis: Dict, context: str) -> Dict[str, Any]:
        """기본 템플릿 생성"""

    def optimize_template(self, template: str, feedback: Dict) -> str:
        """피드백 기반 최적화"""

    def extract_variables(self, template: str) -> List[str]:
        """변수 자동 추출"""
```

**생성 전략**:
1. **구조 기반 생성**: 승인된 템플릿 구조 활용
2. **컨텍스트 주입**: 정책 정보 반영
3. **변수 최적화**: 적절한 변수 사용
4. **길이 조절**: 1000자 이내 제한 준수

#### 3.4 Compliance Checker Agent
```python
class ComplianceChecker:
    """정책 준수 검증 에이전트"""

    def check_compliance(self, template: Dict) -> Dict[str, Any]:
        """종합 컴플라이언스 검증"""

    def calculate_score(self, violations: List, warnings: List) -> int:
        """점수 계산"""

    def suggest_improvements(self, issues: List) -> List[str]:
        """개선점 제안"""
```

**검증 항목**:
- **기본 규칙**: 길이, 인사말, 정보성 표시
- **금지 항목**: 광고성 키워드, 부적절한 표현
- **변수 사용**: 변수 개수, 형식 검증
- **구조 검증**: 메시지 구조 적절성

### 4. 데이터 레이어

#### 4.1 Vector Database (Chroma DB)
```python
class PolicyVectorStore:
    """정책 문서 벡터 스토어"""

    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = Chroma(
            persist_directory="./chroma_db",
            embedding_function=self.embeddings
        )
```

**데이터 구조**:
```json
{
    "content": "정책 문서 내용",
    "metadata": {
        "source": "audit.md",
        "policy_type": "review_guidelines",
        "chunk_id": 0,
        "category": "compliance"
    }
}
```

#### 4.2 Template Store
```python
class TemplateStore:
    """승인된 템플릿 저장소"""

    def find_similar_templates(self, business_type: str, service_type: str):
        """유사 템플릿 검색"""

    def get_approval_patterns(self, category: str):
        """승인 패턴 분석"""
```

**템플릿 메타데이터**:
```json
{
    "id": "template_001",
    "text": "템플릿 내용",
    "metadata": {
        "business_type": "교육",
        "service_type": "신청",
        "approval_status": "approved",
        "category_1": "교육/학습",
        "category_2": "수강신청",
        "variables": ["수신자명", "강의명"],
        "compliance_score": 95
    }
}
```

## 🔄 데이터 흐름 (Data Flow)

### 1. 요청 처리 흐름
```
사용자 요청 → FastAPI → 요청 검증 → LangGraph 워크플로우
    ↓
Request Analyzer → 요청 분석 결과
    ↓
Policy RAG → 관련 정책 검색 → 컨텍스트 구성
    ↓
Template Generator → 템플릿 생성
    ↓
Compliance Checker → 정책 준수 검증
    ↓
[점수 < 85] → Template Refiner → 개선된 템플릿
    ↓
[점수 ≥ 85] → 최종 결과 반환 → FastAPI → 사용자
```

### 2. 에러 처리 흐름
```
에러 발생 → Exception Handler → 로깅
    ↓
에러 분류 (시스템/사용자/외부)
    ↓
적절한 응답 코드 및 메시지 생성
    ↓
사용자에게 친화적 에러 메시지 반환
```

## 🔧 기술 스택 상세

### Backend Framework
- **FastAPI 0.115.0**: 고성능 웹 프레임워크
- **Uvicorn**: ASGI 웹 서버
- **Pydantic**: 데이터 검증 및 시리얼라이제이션

### AI/ML Framework
- **LangChain 0.2.16**: LLM 애플리케이션 프레임워크
- **LangGraph**: 워크플로우 관리
- **Anthropic Claude API**: 대화형 AI 모델

### Database & Storage
- **Chroma DB**: 벡터 데이터베이스
- **OpenAI Embeddings**: 텍스트 임베딩
- **JSON**: 템플릿 및 설정 저장

### Development & Operations
- **Python 3.11**: 프로그래밍 언어
- **Poetry/pip**: 의존성 관리
- **Docker**: 컨테이너화
- **GitHub Actions**: CI/CD

## 📊 성능 및 확장성

### 성능 최적화
- **비동기 처리**: FastAPI async/await 활용
- **연결 풀링**: 데이터베이스 연결 최적화
- **캐싱 전략**: 자주 사용되는 정책 캐싱
- **배치 처리**: 벡터 검색 최적화

### 확장성 고려사항
- **마이크로서비스**: 각 에이전트 독립 배포 가능
- **로드 밸런싱**: 다중 인스턴스 지원
- **수평 확장**: 추가 서버 증설 용이
- **모니터링**: 성능 메트릭 실시간 추적

## 🔒 보안 고려사항

### API 보안
- **인증**: API 키 기반 인증
- **권한 부여**: 역할 기반 접근 제어
- **요청 제한**: Rate limiting 적용
- **입력 검증**: 모든 입력 데이터 검증

### 데이터 보안
- **암호화**: 민감한 데이터 암호화 저장
- **마스킹**: 로그에서 개인정보 마스킹
- **백업**: 정기적 데이터 백업
- **감사**: 모든 작업 로그 기록

---

**📅 작성일**: 2024년 9월 19일
**✍️ 작성자**: Final Team 3 AI
**📄 문서 버전**: 1.0
**🔄 최종 수정**: 2024년 9월 19일