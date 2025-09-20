"""
API 스키마 모델 정의
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum

class BusinessType(str, Enum):
    """비즈니스 유형"""
    EDUCATION = "교육"
    MEDICAL = "의료"
    RESTAURANT = "음식점"
    ECOMMERCE = "쇼핑몰"
    SERVICE = "서비스업"
    FINANCE = "금융"
    OTHER = "기타"

class ServiceType(str, Enum):
    """서비스 유형"""
    APPLICATION = "신청"
    RESERVATION = "예약"
    ORDER = "주문"
    DELIVERY = "배송"
    NOTIFICATION = "안내"
    CONFIRMATION = "확인"
    FEEDBACK = "피드백"

class Tone(str, Enum):
    """톤앤매너"""
    FORMAL = "정중한"
    FRIENDLY = "친근한"
    OFFICIAL = "공식적인"

class Urgency(str, Enum):
    """긴급도"""
    HIGH = "높음"
    MEDIUM = "보통"
    LOW = "낮음"

class ApprovalProbability(str, Enum):
    """승인 가능성"""
    HIGH = "높음"
    MEDIUM = "보통"
    LOW = "낮음"

# Request Models

class TemplateGenerationRequest(BaseModel):
    """템플릿 생성 요청"""
    user_request: str = Field(..., description="사용자 요청 내용", min_length=10, max_length=1000)
    business_type: Optional[BusinessType] = Field(None, description="비즈니스 유형 (선택사항)")
    service_type: Optional[ServiceType] = Field(None, description="서비스 유형 (선택사항)")
    target_audience: Optional[str] = Field(None, description="대상 고객층")
    tone: Optional[Tone] = Field(Tone.FORMAL, description="톤앤매너")
    required_variables: Optional[List[str]] = Field(None, description="필수 변수 목록")
    additional_requirements: Optional[str] = Field(None, description="추가 요구사항")

    class Config:
        json_schema_extra = {
            "example": {
                "user_request": "온라인 강의 수강 신청 완료 후 강의 일정을 안내하는 메시지",
                "business_type": "교육",
                "service_type": "신청",
                "target_audience": "수강생",
                "tone": "정중한",
                "required_variables": ["수신자명", "강의명", "일정"],
                "additional_requirements": "버튼 포함 필요"
            }
        }

class TemplateValidationRequest(BaseModel):
    """템플릿 검증 요청"""
    template_text: str = Field(..., description="검증할 템플릿 텍스트", min_length=10, max_length=1000)
    variables: Optional[List[str]] = Field(None, description="사용된 변수 목록")
    business_type: Optional[BusinessType] = Field(None, description="비즈니스 유형")
    button_text: Optional[str] = Field(None, description="버튼 텍스트")

    class Config:
        json_schema_extra = {
            "example": {
                "template_text": "안녕하세요 #{수신자명}님, 강의 신청이 완료되었습니다.",
                "variables": ["수신자명"],
                "business_type": "교육",
                "button_text": "강의 보기"
            }
        }

# Response Models

class TemplateMetadata(BaseModel):
    """템플릿 메타데이터"""
    category_1: str = Field(..., description="1차 카테고리")
    category_2: str = Field(..., description="2차 카테고리")
    business_type: str = Field(..., description="비즈니스 유형")
    service_type: str = Field(..., description="서비스 유형")
    estimated_length: int = Field(..., description="예상 길이")
    variable_count: int = Field(..., description="변수 개수")
    target_audience: str = Field(..., description="대상 고객")
    tone: str = Field(..., description="톤앤매너")
    generation_method: str = Field(..., description="생성 방법")

class TemplateInfo(BaseModel):
    """템플릿 정보"""
    text: str = Field(..., description="템플릿 텍스트")
    variables: List[str] = Field(..., description="사용된 변수 목록")
    button_suggestion: Optional[str] = Field(None, description="제안 버튼명")
    metadata: TemplateMetadata = Field(..., description="템플릿 메타데이터")

class ComplianceInfo(BaseModel):
    """컴플라이언스 정보"""
    is_compliant: bool = Field(..., description="정책 준수 여부")
    score: float = Field(..., description="준수 점수 (0-100)")
    violations: List[str] = Field(..., description="위반사항 목록")
    warnings: List[str] = Field(..., description="경고사항 목록")
    recommendations: List[str] = Field(..., description="개선 권장사항")
    approval_probability: ApprovalProbability = Field(..., description="승인 가능성")
    required_changes: List[str] = Field(..., description="필수 수정사항")

class DetailedScores(BaseModel):
    """세부 점수"""
    basic_rules: float = Field(..., description="기본 규칙 점수")
    blacklist_check: float = Field(..., description="블랙리스트 검사 점수")
    variable_usage: float = Field(..., description="변수 사용 점수")
    llm_analysis: float = Field(..., description="AI 분석 점수")

class AnalysisInfo(BaseModel):
    """분석 정보"""
    business_type: str = Field(..., description="분석된 비즈니스 유형")
    service_type: str = Field(..., description="분석된 서비스 유형")
    message_purpose: str = Field(..., description="메시지 목적")
    estimated_category: Dict[str, str] = Field(..., description="예상 카테고리")
    compliance_concerns: List[str] = Field(..., description="컴플라이언스 우려사항")

class WorkflowInfo(BaseModel):
    """워크플로우 정보"""
    iterations: int = Field(..., description="반복 횟수")
    errors: List[str] = Field(..., description="발생한 오류")
    policy_sources: List[str] = Field(..., description="참조한 정책 문서")
    processing_time_seconds: Optional[float] = Field(None, description="처리 시간(초)")

class TemplateGenerationResponse(BaseModel):
    """템플릿 생성 응답"""
    success: bool = Field(..., description="성공 여부")
    template: TemplateInfo = Field(..., description="생성된 템플릿 정보")
    compliance: ComplianceInfo = Field(..., description="컴플라이언스 정보")
    analysis: AnalysisInfo = Field(..., description="요청 분석 정보")
    workflow_info: WorkflowInfo = Field(..., description="워크플로우 정보")
    detailed_scores: Optional[DetailedScores] = Field(None, description="세부 점수")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "template": {
                    "text": "안녕하세요 #{수신자명}님, 요청하신 #{강의명} 강의 신청이 완료되었습니다.",
                    "variables": ["수신자명", "강의명"],
                    "button_suggestion": "강의 보기",
                    "metadata": {
                        "category_1": "서비스이용",
                        "category_2": "이용안내/공지",
                        "business_type": "교육",
                        "service_type": "신청",
                        "estimated_length": 95,
                        "variable_count": 2,
                        "target_audience": "수강생",
                        "tone": "정중한",
                        "generation_method": "ai_generated"
                    }
                },
                "compliance": {
                    "is_compliant": True,
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
        }

class TemplateValidationResponse(BaseModel):
    """템플릿 검증 응답"""
    success: bool = Field(..., description="성공 여부")
    compliance: ComplianceInfo = Field(..., description="컴플라이언스 정보")
    detailed_scores: DetailedScores = Field(..., description="세부 점수")
    compliance_report: str = Field(..., description="컴플라이언스 보고서")

# Error Models

class ErrorDetail(BaseModel):
    """오류 상세 정보"""
    code: str = Field(..., description="오류 코드")
    message: str = Field(..., description="오류 메시지")
    details: Optional[str] = Field(None, description="오류 상세 설명")

class ErrorResponse(BaseModel):
    """오류 응답"""
    success: bool = Field(False, description="성공 여부")
    error: ErrorDetail = Field(..., description="오류 정보")

# Health Check Models

class HealthStatus(BaseModel):
    """시스템 상태"""
    status: str = Field(..., description="서비스 상태")
    timestamp: str = Field(..., description="확인 시각")
    version: str = Field(..., description="버전")
    components: Dict[str, str] = Field(..., description="컴포넌트 상태")

# Statistics Models

class SystemStats(BaseModel):
    """시스템 통계"""
    total_requests: int = Field(..., description="총 요청 수")
    successful_generations: int = Field(..., description="성공한 생성 수")
    average_compliance_score: float = Field(..., description="평균 컴플라이언스 점수")
    average_processing_time: float = Field(..., description="평균 처리 시간")
    most_common_business_types: List[str] = Field(..., description="가장 많은 비즈니스 유형")

# Configuration Models

class WorkflowConfig(BaseModel):
    """워크플로우 설정"""
    max_iterations: int = Field(3, description="최대 반복 횟수", ge=1, le=5)
    min_compliance_score: float = Field(80.0, description="최소 컴플라이언스 점수", ge=0, le=100)
    enable_auto_refinement: bool = Field(True, description="자동 개선 활성화")
    strict_compliance: bool = Field(True, description="엄격한 컴플라이언스 모드")

class ServiceConfig(BaseModel):
    """서비스 설정"""
    workflow: WorkflowConfig = Field(..., description="워크플로우 설정")
    enable_caching: bool = Field(True, description="캐싱 활성화")
    cache_ttl_minutes: int = Field(60, description="캐시 TTL (분)")
    rate_limit_per_minute: int = Field(100, description="분당 요청 제한")

# Utility Models

class PaginationParams(BaseModel):
    """페이지네이션 파라미터"""
    page: int = Field(1, description="페이지 번호", ge=1)
    size: int = Field(20, description="페이지 크기", ge=1, le=100)

class SortParams(BaseModel):
    """정렬 파라미터"""
    field: str = Field("created_at", description="정렬 필드")
    direction: str = Field("desc", description="정렬 방향", pattern="^(asc|desc)$")