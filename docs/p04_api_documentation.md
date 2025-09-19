# P04. API 문서 (API Documentation)

## 📋 API 개요

### 기본 정보
- **Base URL**: `http://localhost:8000`
- **API 버전**: v1
- **프로토콜**: HTTP/HTTPS
- **데이터 형식**: JSON
- **인증**: API Key (선택사항)

### API 설계 원칙
- **RESTful**: 표준 HTTP 메서드 사용
- **직관적**: 명확한 엔드포인트 구조
- **일관성**: 동일한 응답 형식
- **확장성**: 버전 관리 지원

## 🔑 인증 및 권한

### API 키 인증 (선택사항)
```http
# 헤더에 API 키 포함
Authorization: Bearer your-api-key-here
```

### 사용량 제한
- **분당 요청**: 100회
- **시간당 요청**: 1,000회
- **일일 요청**: 10,000회

## 📚 엔드포인트 목록

### 1. 시스템 상태 API

#### GET /
**기본 서비스 정보 조회**

```http
GET /
```

**응답 예시**:
```json
{
    "service": "KakaoTalk Template Auto Generator API",
    "version": "1.0.0",
    "status": "running",
    "endpoints": {
        "docs": "/docs",
        "health": "/health",
        "generate": "/api/v1/templates/generate",
        "validate": "/api/v1/templates/validate"
    }
}
```

#### GET /health
**서비스 상태 확인**

```http
GET /health
```

**응답 예시**:
```json
{
    "status": "healthy",
    "timestamp": "2024-09-19T20:00:00Z",
    "anthropic_api": "connected",
    "vector_db": "operational",
    "uptime_seconds": 3600,
    "version": "1.0.0"
}
```

#### GET /stats
**시스템 통계 정보**

```http
GET /stats
```

**응답 예시**:
```json
{
    "total_requests": 1250,
    "successful_generations": 1180,
    "success_rate": 94.4,
    "average_response_time_ms": 2300,
    "average_compliance_score": 87.5,
    "uptime_hours": 24.5,
    "cached_policies": 45,
    "template_database_size": 1543
}
```

### 2. 템플릿 생성 API

#### POST /api/v1/templates/generate
**새 템플릿 자동 생성**

**요청 형식**:
```http
POST /api/v1/templates/generate
Content-Type: application/json

{
    "user_request": "string",
    "business_type": "string (optional)",
    "service_type": "string (optional)",
    "tone": "string (optional)",
    "auto_refine": "boolean (optional)"
}
```

**요청 매개변수**:
| 매개변수 | 타입 | 필수 | 설명 | 예시 |
|---------|------|------|------|------|
| `user_request` | string | ✅ | 생성하려는 템플릿 요청 | "피자 주문 완료 안내 메시지" |
| `business_type` | string | ❌ | 업종 분류 | "음식점", "교육", "의료" |
| `service_type` | string | ❌ | 서비스 유형 | "주문", "예약", "신청" |
| `tone` | string | ❌ | 톤앤매너 | "정중한", "친근한", "공식적인" |
| `auto_refine` | boolean | ❌ | 자동 개선 여부 | true, false |

**응답 예시**:
```json
{
    "success": true,
    "request_id": "req_20240919_001",
    "timestamp": "2024-09-19T20:00:00Z",
    "template": {
        "text": "안녕하세요 #{수신자명}님,\n\n주문해주신 #{상품명}의 접수가 완료되었습니다.\n\n▶ 주문번호: #{주문번호}\n▶ 예상 준비시간: #{준비시간}\n\n준비가 완료되면 연락드리겠습니다.\n\n※ 이 메시지는 주문하신 분들께 발송되는 정보성 안내입니다.",
        "variables": ["수신자명", "상품명", "주문번호", "준비시간"],
        "character_count": 156,
        "button_suggestion": "주문 상세보기"
    },
    "analysis": {
        "business_type": "음식점",
        "service_type": "주문",
        "message_purpose": "주문 접수 확인",
        "target_audience": "고객",
        "confidence_score": 0.95
    },
    "compliance": {
        "score": 95,
        "is_compliant": true,
        "approval_probability": "높음",
        "violations": [],
        "warnings": [],
        "recommendations": [
            "템플릿이 모든 정책을 준수합니다",
            "승인 가능성이 높습니다"
        ]
    },
    "processing_info": {
        "processing_time_ms": 2300,
        "model_used": "claude-3-haiku-20240307",
        "iterations": 1,
        "policy_documents_used": 3
    }
}
```

**오류 응답 예시**:
```json
{
    "success": false,
    "error": {
        "code": "INVALID_REQUEST",
        "message": "사용자 요청이 비어있습니다",
        "details": "user_request 필드는 필수입니다"
    },
    "request_id": "req_20240919_002",
    "timestamp": "2024-09-19T20:00:00Z"
}
```

### 3. 템플릿 검증 API

#### POST /api/v1/templates/validate
**기존 템플릿 정책 준수 검증**

**요청 형식**:
```http
POST /api/v1/templates/validate
Content-Type: application/json

{
    "template_text": "string",
    "variables": ["string"],
    "business_type": "string (optional)",
    "check_blacklist": "boolean (optional)"
}
```

**요청 매개변수**:
| 매개변수 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `template_text` | string | ✅ | 검증할 템플릿 내용 |
| `variables` | array | ✅ | 템플릿에 사용된 변수 목록 |
| `business_type` | string | ❌ | 업종 정보 (정확한 검증용) |
| `check_blacklist` | boolean | ❌ | 금지 항목 체크 여부 |

**응답 예시**:
```json
{
    "success": true,
    "validation_result": {
        "is_compliant": true,
        "compliance_score": 88,
        "approval_probability": "높음",
        "violations": [],
        "warnings": [
            "인사말이 포함되지 않았습니다"
        ],
        "recommendations": [
            "메시지 시작 부분에 '안녕하세요' 등의 인사말을 추가하세요",
            "정보성 메시지 표시를 하단에 추가하는 것을 권장합니다"
        ]
    },
    "analysis": {
        "character_count": 145,
        "variable_count": 3,
        "structure_valid": true,
        "has_greeting": false,
        "has_information_notice": true,
        "blacklist_violations": []
    },
    "suggestions": {
        "improved_template": "안녕하세요 #{수신자명}님,\n\n주문해주신 #{상품명}의 접수가 완료되었습니다...",
        "score_improvement": 7
    }
}
```

### 4. 템플릿 개선 API

#### POST /api/v1/templates/refine
**기존 템플릿 개선**

**요청 형식**:
```http
POST /api/v1/templates/refine
Content-Type: application/json

{
    "template_text": "string",
    "feedback": "string",
    "target_score": "number (optional)",
    "business_type": "string (optional)"
}
```

**응답 예시**:
```json
{
    "success": true,
    "refined_template": {
        "text": "개선된 템플릿 내용",
        "improvements": [
            "인사말 추가",
            "정보성 메시지 표시 개선",
            "변수 사용 최적화"
        ],
        "score_improvement": 12
    },
    "compliance": {
        "original_score": 75,
        "refined_score": 87,
        "improvement": 12
    }
}
```

### 5. 정책 검색 API

#### GET /api/v1/policies/search
**관련 정책 문서 검색**

**쿼리 매개변수**:
- `q`: 검색 키워드
- `type`: 정책 유형 (audit, content, whitelist, blacklist)
- `limit`: 결과 개수 (기본값: 5)

```http
GET /api/v1/policies/search?q=알림톡 승인 기준&type=audit&limit=3
```

**응답 예시**:
```json
{
    "success": true,
    "results": [
        {
            "content": "알림톡 템플릿 승인 기준...",
            "policy_type": "review_guidelines",
            "source": "audit.md",
            "relevance_score": 0.92
        }
    ],
    "total_results": 3,
    "search_time_ms": 150
}
```

### 6. 템플릿 예시 API

#### GET /api/v1/templates/examples
**업종별 승인된 템플릿 예시 조회**

**쿼리 매개변수**:
- `business_type`: 업종 (교육, 의료, 음식점, 쇼핑몰 등)
- `service_type`: 서비스 유형 (주문, 예약, 신청 등)
- `limit`: 결과 개수

```http
GET /api/v1/templates/examples?business_type=교육&service_type=신청&limit=5
```

**응답 예시**:
```json
{
    "success": true,
    "examples": [
        {
            "template_id": "edu_001",
            "text": "안녕하세요 #{수신자명}님...",
            "variables": ["수신자명", "강의명"],
            "approval_status": "approved",
            "compliance_score": 95,
            "usage_count": 342
        }
    ],
    "total_examples": 15,
    "business_type": "교육",
    "service_type": "신청"
}
```

## 🔧 SDK 및 클라이언트 라이브러리

### Python SDK 예시
```python
import requests

class KakaoTemplateClient:
    def __init__(self, base_url="http://localhost:8000", api_key=None):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    def generate_template(self, user_request, **kwargs):
        """템플릿 생성"""
        data = {"user_request": user_request, **kwargs}
        response = requests.post(
            f"{self.base_url}/api/v1/templates/generate",
            json=data,
            headers=self.headers
        )
        return response.json()

    def validate_template(self, template_text, variables):
        """템플릿 검증"""
        data = {
            "template_text": template_text,
            "variables": variables
        }
        response = requests.post(
            f"{self.base_url}/api/v1/templates/validate",
            json=data,
            headers=self.headers
        )
        return response.json()

# 사용 예시
client = KakaoTemplateClient()
result = client.generate_template("피자 주문 완료 안내")
print(result["template"]["text"])
```

### JavaScript SDK 예시
```javascript
class KakaoTemplateClient {
    constructor(baseUrl = 'http://localhost:8000', apiKey = null) {
        this.baseUrl = baseUrl;
        this.headers = { 'Content-Type': 'application/json' };
        if (apiKey) {
            this.headers['Authorization'] = `Bearer ${apiKey}`;
        }
    }

    async generateTemplate(userRequest, options = {}) {
        const response = await fetch(`${this.baseUrl}/api/v1/templates/generate`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({ user_request: userRequest, ...options })
        });
        return await response.json();
    }

    async validateTemplate(templateText, variables) {
        const response = await fetch(`${this.baseUrl}/api/v1/templates/validate`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                template_text: templateText,
                variables: variables
            })
        });
        return await response.json();
    }
}

// 사용 예시
const client = new KakaoTemplateClient();
const result = await client.generateTemplate("온라인 강의 수강 신청 완료");
console.log(result.template.text);
```

### cURL 예시
```bash
# 템플릿 생성
curl -X POST "http://localhost:8000/api/v1/templates/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "카페 음료 주문 완료 안내",
    "business_type": "음식점",
    "tone": "친근한"
  }'

# 헬스체크
curl -X GET "http://localhost:8000/health"

# 시스템 통계
curl -X GET "http://localhost:8000/stats"
```

## ⚠️ 오류 코드 및 처리

### HTTP 상태 코드
- `200`: 성공
- `400`: 잘못된 요청
- `401`: 인증 실패
- `403`: 권한 없음
- `404`: 리소스 없음
- `429`: 요청 한도 초과
- `500`: 서버 내부 오류
- `503`: 서비스 일시 중단

### 오류 응답 형식
```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "사용자 친화적 오류 메시지",
        "details": "상세 오류 정보",
        "field": "문제가 있는 필드 (해당시)"
    },
    "request_id": "req_20240919_003",
    "timestamp": "2024-09-19T20:00:00Z"
}
```

### 주요 오류 코드
| 코드 | 설명 | 해결 방법 |
|------|------|-----------|
| `INVALID_REQUEST` | 잘못된 요청 형식 | 요청 형식 확인 |
| `MISSING_REQUIRED_FIELD` | 필수 필드 누락 | 필수 필드 추가 |
| `API_KEY_INVALID` | 잘못된 API 키 | API 키 확인 |
| `RATE_LIMIT_EXCEEDED` | 요청 한도 초과 | 잠시 후 재시도 |
| `TEMPLATE_GENERATION_FAILED` | 템플릿 생성 실패 | 요청 내용 수정 후 재시도 |
| `SERVICE_UNAVAILABLE` | 서비스 일시 중단 | 잠시 후 재시도 |

## 📊 성능 최적화

### 캐싱 전략
- 자주 검색되는 정책: 1시간 캐싱
- 업종별 템플릿 예시: 30분 캐싱
- 시스템 상태: 5분 캐싱

### 배치 요청
```http
POST /api/v1/templates/batch-generate
Content-Type: application/json

{
    "requests": [
        {"user_request": "첫 번째 요청"},
        {"user_request": "두 번째 요청"}
    ]
}
```

### 비동기 처리
```http
POST /api/v1/templates/generate-async
Content-Type: application/json

{
    "user_request": "템플릿 요청",
    "callback_url": "https://your-server.com/callback"
}
```

## 🔒 보안 고려사항

### API 키 관리
- API 키는 환경 변수로 관리
- HTTPS 연결 필수 (프로덕션)
- 키 정기 교체 권장

### 데이터 보안
- 개인정보는 로그에 기록하지 않음
- 요청 데이터는 암호화 전송
- 24시간 후 요청 로그 자동 삭제

---

**📅 작성일**: 2024년 9월 19일
**✍️ 작성자**: Final Team 3 AI
**📄 문서 버전**: 1.0
**🔄 최종 수정**: 2024년 9월 19일