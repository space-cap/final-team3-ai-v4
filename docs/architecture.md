# 카카오 알림톡 템플릿 자동 생성 AI 서비스 아키텍처

## 1. 시스템 개요

본 시스템은 사용자가 원하는 메시지 내용을 입력하면 AI가 카카오 알림톡 정책에 완벽하게 부합하는 템플릿을 자동으로 생성해주는 서비스입니다.

### 1.1 주요 기능
- 사용자 요구사항 분석 및 이해
- 정책 기반 컴플라이언스 체킹
- 템플릿 자동 생성 및 최적화
- 다중 에이전트 협업 시스템

## 2. 기술 스택

- **AI Framework**: LangChain, LangGraph
- **LLM**: Claude API (Anthropic)
- **Vector Database**: Chroma
- **Backend**: FastAPI
- **Language**: Python 3.11

## 3. 시스템 아키텍처

### 3.1 Multi-Agent 시스템 구조

```
User Request → Request Analyzer → Template Generator → Compliance Checker → Final Output
                     ↓                    ↓                    ↓
              Policy RAG System ←→ Vector Database ←→ Template Database
```

### 3.2 주요 컴포넌트

#### 3.2.1 Request Analyzer Agent
- **역할**: 사용자 요청 분석 및 분류
- **기능**:
  - 비즈니스 타입 분류 (교육, 서비스업, 기타)
  - 메시지 목적 분석 (공지/안내, 신청, 피드백 등)
  - 필요한 변수 식별
  - 톤앤매너 요구사항 파악

#### 3.2.2 Policy RAG System
- **역할**: 정책 문서 기반 컨텍스트 제공
- **기능**:
  - 정책 문서 벡터화 및 저장
  - 관련 정책 검색 및 제공
  - 컴플라이언스 가이드라인 제공

#### 3.2.3 Template Generator Agent
- **역할**: 정책 준수 템플릿 생성
- **기능**:
  - 기존 승인 템플릿 패턴 학습
  - 정책 기반 템플릿 생성
  - 변수 및 버튼 설정
  - 메시지 길이 및 구조 최적화

#### 3.2.4 Compliance Checker Agent
- **역할**: 생성된 템플릿의 정책 준수 검증
- **기능**:
  - 블랙리스트 위반 체크
  - 화이트리스트 패턴 매칭
  - 변수 사용 규칙 검증
  - 승인 가능성 평가

#### 3.2.5 LangGraph Workflow
- **역할**: 에이전트 간 협업 및 워크플로우 관리
- **기능**:
  - 에이전트 실행 순서 제어
  - 조건부 분기 처리
  - 피드백 루프 관리
  - 오류 처리 및 재시도

## 4. 데이터 구조

### 4.1 정책 문서 구조
```
data/cleaned_policies/
├── audit.md          # 심사 가이드
├── content-guide.md   # 작성 가이드
├── white-list.md      # 허용 템플릿 유형
├── black-list.md      # 금지 템플릿 유형
├── operations.md      # 운영 절차
└── ...
```

### 4.2 템플릿 데이터 구조
```json
{
  "id": "template_xxx",
  "text": "메시지 내용 with #{변수}",
  "metadata": {
    "category_1": "서비스이용",
    "category_2": "이용안내/공지",
    "business_type": "교육",
    "service_type": "신청",
    "variables": ["변수1", "변수2"],
    "approval_status": "approved",
    "politeness_level": "formal"
  }
}
```

## 5. API 엔드포인트 설계

### 5.1 템플릿 생성 API
```
POST /api/v1/generate-template
{
  "user_request": "수강 신청 완료 안내 메시지",
  "business_type": "교육",
  "target_audience": "수강생",
  "tone": "정중한",
  "variables": ["수신자명", "강의명", "일정"]
}
```

### 5.2 응답 구조
```json
{
  "success": true,
  "template": {
    "text": "생성된 템플릿 내용",
    "variables": ["변수 목록"],
    "compliance_score": 95,
    "recommendations": ["개선사항"],
    "approval_probability": "높음"
  },
  "metadata": {
    "category": "분류된 카테고리",
    "business_type": "교육",
    "estimated_approval_time": "2일"
  }
}
```

## 6. 프로젝트 구조

```
final-team3-ai-v4/
├── src/
│   ├── agents/
│   │   ├── request_analyzer.py
│   │   ├── template_generator.py
│   │   ├── compliance_checker.py
│   │   └── policy_rag.py
│   ├── workflow/
│   │   └── langgraph_workflow.py
│   ├── api/
│   │   ├── main.py
│   │   ├── routes/
│   │   └── models/
│   ├── database/
│   │   ├── vector_store.py
│   │   └── template_store.py
│   └── utils/
│       ├── llm_client.py
│       └── text_processing.py
├── data/
│   ├── kakao_template_vectordb_data.json
│   └── cleaned_policies/
├── docs/
│   ├── architecture.md
│   ├── api_documentation.md
│   └── deployment_guide.md
├── tests/
├── requirements.txt
└── README.md
```

## 7. 구현 단계

### Phase 1: 기본 인프라 구축
1. 의존성 설치 및 환경 설정
2. Vector Database 구축 (Chroma)
3. 기본 LLM 클라이언트 설정

### Phase 2: 에이전트 개발
1. Request Analyzer Agent 구현
2. Policy RAG System 구현
3. Template Generator Agent 구현
4. Compliance Checker Agent 구현

### Phase 3: 워크플로우 통합
1. LangGraph 워크플로우 구현
2. 에이전트 간 통신 및 데이터 흐름 구축
3. 오류 처리 및 재시도 로직

### Phase 4: API 서비스 구축
1. FastAPI 백엔드 구현
2. API 엔드포인트 개발
3. 요청/응답 검증

### Phase 5: 테스트 및 최적화
1. 단위 테스트 및 통합 테스트
2. 성능 최적화
3. 사용자 시나리오 테스트

## 8. 성공 지표

- **정확도**: 생성된 템플릿의 정책 준수율 95% 이상
- **승인율**: 실제 카카오 심사 통과율 90% 이상
- **응답시간**: 평균 템플릿 생성 시간 30초 이내
- **사용성**: 소상공인도 쉽게 사용할 수 있는 직관적 인터페이스