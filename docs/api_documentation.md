# API 문서

## 개요

카카오 알림톡 템플릿 자동 생성 AI 서비스의 REST API 문서입니다.

## 기본 정보

- **Base URL**: `http://localhost:8000`
- **API 버전**: v1
- **인증**: 없음 (내부 서비스)
- **Content-Type**: `application/json`

## 엔드포인트 목록

### 1. 템플릿 생성

#### POST `/api/v1/templates/generate`

사용자 요청을 분석하여 카카오 정책에 부합하는 알림톡 템플릿을 생성합니다.

**요청 예시:**

```json
{
  "user_request": "온라인 강의 수강 신청 완료 후 강의 일정을 안내하는 메시지",
  "business_type": "교육",
  "service_type": "신청",
  "target_audience": "수강생",
  "tone": "정중한",
  "required_variables": ["수신자명", "강의명", "일정"],
  "additional_requirements": "버튼 포함 필요"
}
```

**응답 예시:**

```json
{
  "success": true,
  "template": {
    "text": "안녕하세요 #{수신자명}님,\n\n요청하신 #{강의명} 강의 신청이 완료되었습니다.\n\n▶ 강의 일정: #{일정}\n▶ 참여 방법: 등록하신 이메일로 발송된 링크를 확인해주세요.\n\n※ 이 메시지는 강의를 신청하신 분들께 발송되는 정보성 안내입니다.",
    "variables": ["수신자명", "강의명", "일정"],
    "button_suggestion": "강의 보기",
    "metadata": {
      "category_1": "서비스이용",
      "category_2": "이용안내/공지",
      "business_type": "교육",
      "service_type": "신청",
      "estimated_length": 145,
      "variable_count": 3,
      "target_audience": "수강생",
      "tone": "정중한",
      "generation_method": "ai_generated"
    }
  },
  "compliance": {
    "is_compliant": true,
    "score": 92.5,
    "violations": [],
    "warnings": [],
    "recommendations": ["정보성 메시지 표시가 포함되어 우수함"],
    "approval_probability": "높음",
    "required_changes": []
  },
  "analysis": {
    "business_type": "교육",
    "service_type": "신청",
    "message_purpose": "강의 신청 확인",
    "estimated_category": {
      "category_1": "서비스이용",
      "category_2": "이용안내/공지"
    },
    "compliance_concerns": []
  },
  "workflow_info": {
    "iterations": 1,
    "errors": [],
    "policy_sources": ["content-guide.md", "audit.md"],
    "processing_time_seconds": 3.2
  }
}
```

### 2. 템플릿 검증

#### POST `/api/v1/templates/validate`

기존 템플릿이 카카오 정책을 준수하는지 검증합니다.

**요청 예시:**

```json
{
  "template_text": "안녕하세요 #{수신자명}님, 강의 신청이 완료되었습니다.",
  "variables": ["수신자명"],
  "business_type": "교육",
  "button_text": "강의 보기"
}
```

**응답 예시:**

```json
{
  "success": true,
  "compliance": {
    "is_compliant": false,
    "score": 75.0,
    "violations": ["정보성 메시지 표시가 없습니다"],
    "warnings": ["메시지가 너무 간단할 수 있습니다"],
    "recommendations": ["메시지 하단에 정보성 메시지 표시를 추가하세요"],
    "approval_probability": "보통",
    "required_changes": ["정보성 메시지 표시가 없습니다"]
  },
  "detailed_scores": {
    "basic_rules": 80.0,
    "blacklist_check": 100.0,
    "variable_usage": 90.0,
    "llm_analysis": 70.0
  },
  "compliance_report": "## 카카오 알림톡 정책 준수 검증 결과\n\n### 종합 평가\n- **준수 여부**: ❌ 위반\n- **준수 점수**: 75.0/100점\n- **승인 가능성**: 보통\n\n### 위반사항 (1건)\n1. 정보성 메시지 표시가 없습니다\n\n### 개선 권장사항\n1. 메시지 하단에 정보성 메시지 표시를 추가하세요"
}
```

### 3. 템플릿 예시 조회

#### GET `/api/v1/templates/examples/{business_type}`

특정 비즈니스 유형의 승인된 템플릿 예시를 조회합니다.

**요청 예시:**
```
GET /api/v1/templates/examples/교육?limit=3
```

**응답 예시:**

```json
{
  "business_type": "교육",
  "total_found": 15,
  "returned_count": 3,
  "examples": [
    {
      "id": "template_002",
      "text": "안녕하세요, #{수신자명}님 강의에 신청해주셔서 감사합니다.",
      "category": "서비스이용 > 이용안내/공지",
      "service_type": "신청",
      "variables": ["수신자명", "일정", "참여방법"]
    }
  ]
}
```

### 4. 카테고리 목록 조회

#### GET `/api/v1/templates/categories`

사용 가능한 템플릿 카테고리 목록을 조회합니다.

**응답 예시:**

```json
{
  "category_1_options": [
    "서비스이용",
    "거래",
    "배송",
    "예약",
    "회원관리",
    "고객지원"
  ],
  "category_2_options": {
    "서비스이용": ["이용안내/공지", "예약/신청", "피드백 요청"],
    "거래": ["주문/결제", "취소/환불", "영수증/세금계산서"]
  },
  "business_types": [
    "교육", "의료", "음식점", "쇼핑몰", "서비스업", "금융", "기타"
  ],
  "service_types": [
    "신청", "예약", "주문", "배송", "안내", "확인", "피드백"
  ]
}
```

### 5. 일괄 검증

#### POST `/api/v1/templates/batch-validate`

여러 템플릿을 한 번에 검증합니다. (최대 10개)

**요청 예시:**

```json
[
  {
    "template_text": "첫 번째 템플릿",
    "variables": ["수신자명"]
  },
  {
    "template_text": "두 번째 템플릿",
    "variables": ["수신자명", "상품명"]
  }
]
```

**응답 예시:**

```json
{
  "total_templates": 2,
  "successful_validations": 2,
  "compliant_templates": 1,
  "results": [
    {
      "index": 0,
      "success": true,
      "result": {
        "compliance": {
          "is_compliant": true,
          "score": 85.0
        }
      }
    },
    {
      "index": 1,
      "success": true,
      "result": {
        "compliance": {
          "is_compliant": false,
          "score": 70.0
        }
      }
    }
  ]
}
```

### 6. 시스템 상태 확인

#### GET `/health`

서비스 상태 및 구성 요소 확인

**응답 예시:**

```json
{
  "status": "healthy",
  "timestamp": "2024-09-19 20:00:00",
  "version": "1.0.0",
  "components": {
    "llm_client": "healthy",
    "vector_database": "healthy",
    "workflow": "healthy"
  }
}
```

### 7. 시스템 통계

#### GET `/stats`

시스템 사용 통계 조회

**응답 예시:**

```json
{
  "total_requests": 1250,
  "successful_generations": 1180,
  "average_compliance_score": 87.3,
  "average_processing_time": 2.8,
  "most_common_business_types": ["교육", "서비스업", "쇼핑몰"]
}
```

## 오류 응답

모든 API는 오류 발생 시 다음 형식으로 응답합니다:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "사용자 친화적 오류 메시지",
    "details": "상세 오류 정보 (개발용)"
  }
}
```

### 주요 오류 코드

- `GENERATION_FAILED`: 템플릿 생성 실패
- `VALIDATION_ERROR`: 템플릿 검증 오류
- `TOO_MANY_TEMPLATES`: 일괄 검증 시 템플릿 수 초과
- `INTERNAL_ERROR`: 서버 내부 오류

## 사용 예시

### Python 클라이언트 예시

```python
import requests

# 템플릿 생성
def generate_template(user_request):
    url = "http://localhost:8000/api/v1/templates/generate"
    data = {
        "user_request": user_request,
        "business_type": "교육",
        "tone": "정중한"
    }

    response = requests.post(url, json=data)

    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            print("생성된 템플릿:", result["template"]["text"])
            print("컴플라이언스 점수:", result["compliance"]["score"])
        else:
            print("오류:", result["error"]["message"])
    else:
        print("HTTP 오류:", response.status_code)

# 사용 예시
generate_template("강의 수강 신청 완료 안내 메시지")
```

### JavaScript 클라이언트 예시

```javascript
async function generateTemplate(userRequest) {
    const url = 'http://localhost:8000/api/v1/templates/generate';
    const data = {
        user_request: userRequest,
        business_type: '교육',
        tone: '정중한'
    };

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            console.log('생성된 템플릿:', result.template.text);
            console.log('컴플라이언스 점수:', result.compliance.score);
        } else {
            console.error('오류:', result.error.message);
        }
    } catch (error) {
        console.error('네트워크 오류:', error);
    }
}

// 사용 예시
generateTemplate('강의 수강 신청 완료 안내 메시지');
```

## 개발 및 테스트

### 개발 서버 실행

```bash
python run_server.py
```

### API 문서 확인

서버 실행 후 다음 URL에서 대화형 API 문서를 확인할 수 있습니다:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 시스템 테스트

```bash
python simple_test.py
```

## 성능 및 제한사항

### 응답 시간

- 템플릿 생성: 평균 2-5초
- 템플릿 검증: 평균 1-3초
- 일괄 검증: 템플릿당 1-2초

### 제한사항

- 동시 요청: 50개 제한
- 요청 크기: 최대 1MB
- 일괄 검증: 최대 10개 템플릿
- 템플릿 길이: 최대 1,000자

### 캐시

- 정책 검색 결과: 60분 캐시
- 유사 템플릿: 30분 캐시

## 보안

- 모든 요청은 로그에 기록됩니다
- 민감한 정보는 로그에서 마스킹됩니다
- CORS는 개발 환경에서만 허용됩니다

## 버전 관리

현재 버전: v1.0.0

API 버전은 URL 경로에 포함됩니다 (`/api/v1/`). 새 버전 출시 시 기존 버전은 최소 6개월간 지원됩니다.