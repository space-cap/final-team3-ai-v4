# 카카오 알림톡 템플릿 생성 API - Request Body 예제

## API 엔드포인트
`POST /api/v1/templates/generate`

## Request Schema
```json
{
  "user_request": "string (필수, 10-1000자)",
  "business_type": "교육|의료|음식점|쇼핑몰|서비스업|금융|기타 (선택)",
  "service_type": "신청|예약|주문|배송|안내|확인|피드백 (선택)",
  "target_audience": "string (선택)",
  "tone": "정중한|친근한|공식적인 (선택, 기본: 정중한)",
  "required_variables": ["string array (선택)"],
  "additional_requirements": "string (선택)"
}
```

## Request Body 예제 10개

### 1. 교육 - 온라인 강의 수강 신청 완료
```json
{
  "user_request": "온라인 강의 수강 신청이 완료된 후 강의 일정과 접속 방법을 안내하는 메시지",
  "business_type": "교육",
  "service_type": "신청",
  "target_audience": "수강생",
  "tone": "정중한",
  "required_variables": ["수신자명", "강의명", "강의일정", "접속링크"],
  "additional_requirements": "수강 시 주의사항도 포함하고 버튼 추가"
}
```

### 2. 의료 - 진료 예약 확인
```json
{
  "user_request": "병원 진료 예약이 완료되었음을 알리고 준비사항을 안내하는 메시지",
  "business_type": "의료",
  "service_type": "예약",
  "target_audience": "환자",
  "tone": "정중한",
  "required_variables": ["환자명", "진료과", "진료일시", "의사명"],
  "additional_requirements": "진료 전 준비사항과 내원 시간 명시"
}
```

### 3. 음식점 - 주문 접수 및 조리 시작
```json
{
  "user_request": "음식 주문이 접수되어 조리를 시작한다는 알림과 예상 완료 시간을 전달",
  "business_type": "음식점",
  "service_type": "주문",
  "target_audience": "고객",
  "tone": "친근한",
  "required_variables": ["고객명", "주문메뉴", "예상시간", "매장전화"],
  "additional_requirements": "주문 변경 불가 안내 포함"
}
```

### 4. 쇼핑몰 - 상품 배송 시작
```json
{
  "user_request": "주문한 상품이 출고되어 배송이 시작되었음을 알리는 메시지",
  "business_type": "쇼핑몰",
  "service_type": "배송",
  "target_audience": "구매고객",
  "tone": "정중한",
  "required_variables": ["구매자명", "상품명", "송장번호", "배송업체"],
  "additional_requirements": "배송조회 링크와 예상 도착일 포함"
}
```

### 5. 서비스업 - 상담 예약 확정
```json
{
  "user_request": "고객상담 예약이 확정되었음을 알리고 상담 장소와 담당자 정보를 안내",
  "business_type": "서비스업",
  "service_type": "예약",
  "target_audience": "상담신청자",
  "tone": "공식적인",
  "required_variables": ["신청자명", "상담일시", "상담장소", "담당자명"],
  "additional_requirements": "상담 취소 및 변경 방법 안내"
}
```

### 6. 금융 - 대출 심사 결과 안내
```json
{
  "user_request": "대출 신청 심사가 완료되어 결과를 안내하는 메시지",
  "business_type": "금융",
  "service_type": "안내",
  "target_audience": "대출신청자",
  "tone": "정중한",
  "required_variables": ["신청자명", "대출종류", "심사결과", "연락처"],
  "additional_requirements": "추가 서류 제출이 필요한 경우 안내"
}
```

### 7. 교육 - 성적 발표
```json
{
  "user_request": "시험 성적이 발표되었음을 알리고 성적 확인 방법을 안내하는 메시지",
  "business_type": "교육",
  "service_type": "안내",
  "target_audience": "학생",
  "tone": "정중한",
  "required_variables": ["학생명", "시험명", "성적확인사이트"],
  "additional_requirements": "성적 이의신청 기간과 방법 포함"
}
```

### 8. 의료 - 검사 결과 안내
```json
{
  "user_request": "건강검진 결과가 나왔음을 알리고 결과 수령 방법을 안내",
  "business_type": "의료",
  "service_type": "안내",
  "target_audience": "검진자",
  "tone": "정중한",
  "required_variables": ["환자명", "검진날짜", "결과수령방법"],
  "additional_requirements": "추가 상담이 필요한 경우 예약 안내"
}
```

### 9. 음식점 - 배달 완료
```json
{
  "user_request": "주문하신 음식이 배달 완료되었음을 알리는 메시지",
  "business_type": "음식점",
  "service_type": "배송",
  "target_audience": "주문고객",
  "tone": "친근한",
  "required_variables": ["고객명", "주문메뉴", "배달시간"],
  "additional_requirements": "맛있게 드시라는 인사와 리뷰 요청"
}
```

### 10. 서비스업 - 정기점검 일정 안내
```json
{
  "user_request": "계약고객의 정기점검 일정을 사전에 안내하는 메시지",
  "business_type": "서비스업",
  "service_type": "안내",
  "target_audience": "계약고객",
  "tone": "정중한",
  "required_variables": ["고객명", "점검일시", "점검내용", "담당기사"],
  "additional_requirements": "점검 당일 주의사항과 일정 변경 방법 안내"
}
```

## 추가 참고사항

### 사용 가능한 변수 형태
- `#{수신자명}`, `#{고객명}`, `#{환자명}` 등
- 변수는 `#{변수명}` 형태로 사용
- 한글 변수명 권장

### 톤앤매너 가이드
- **정중한**: 공식적이고 정중한 어조 (은/는, 습니다 체)
- **친근한**: 친근하고 편안한 어조 (요/어요 체)
- **공식적인**: 매우 공식적인 어조 (법적 문서 스타일)

### 비즈니스 타입별 특징
- **교육**: 학습자, 교육기관 대상
- **의료**: 환자, 의료서비스 대상
- **음식점**: 주문고객, 음식 관련
- **쇼핑몰**: 구매고객, 상품/배송 관련
- **서비스업**: 서비스 이용고객 대상
- **금융**: 금융상품 이용고객 대상

### 메시지 작성 시 주의사항
1. 알림톡은 정보성 메시지만 가능 (광고성 내용 금지)
2. 1,000자 이내 제한
3. 명확하고 구체적인 정보 포함
4. 수신자에게 도움이 되는 내용 위주
5. 개인정보 보호 준수

## API 호출 예제

### curl 예제
```bash
curl -X POST "http://localhost:8000/api/v1/templates/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "온라인 강의 수강 신청이 완료된 후 강의 일정과 접속 방법을 안내하는 메시지",
    "business_type": "교육",
    "service_type": "신청",
    "target_audience": "수강생",
    "tone": "정중한",
    "required_variables": ["수신자명", "강의명", "강의일정"],
    "additional_requirements": "버튼 포함 필요"
  }'
```

### Python 예제
```python
import requests

url = "http://localhost:8000/api/v1/templates/generate"
data = {
    "user_request": "병원 진료 예약이 완료되었음을 알리고 준비사항을 안내하는 메시지",
    "business_type": "의료",
    "service_type": "예약",
    "target_audience": "환자",
    "tone": "정중한",
    "required_variables": ["환자명", "진료과", "진료일시"],
    "additional_requirements": "진료 전 준비사항 포함"
}

response = requests.post(url, json=data)
result = response.json()
print(result)
```

## API 응답 예제
성공적인 요청 시 다음과 같은 형태의 응답을 받을 수 있습니다:

```json
{
  "success": true,
  "template": {
    "text": "안녕하세요 #{수신자명}님, 요청하신 #{강의명} 강의 신청이 완료되었습니다. 강의 일정은 #{강의일정}입니다.",
    "variables": ["수신자명", "강의명", "강의일정"],
    "button_suggestion": "강의 보기",
    "metadata": {
      "category_1": "서비스이용",
      "category_2": "이용안내/공지",
      "business_type": "교육",
      "service_type": "신청",
      "estimated_length": 95,
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
    "recommendations": ["정보성 메시지 표시 추가 권장"],
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