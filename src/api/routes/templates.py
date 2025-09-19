"""
템플릿 관련 API 라우트
"""
import time
import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse

from ..models.schemas import (
    TemplateGenerationRequest,
    TemplateGenerationResponse,
    TemplateValidationRequest,
    TemplateValidationResponse,
    ErrorResponse,
    WorkflowConfig
)
from ...workflow.langgraph_workflow import KakaoTemplateWorkflow, SimpleWorkflowRunner
from ...agents.compliance_checker import ComplianceCheckerAgent
from ...utils.llm_client import ClaudeLLMClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])

# Global workflow instance (실제 운영에서는 dependency injection 사용 권장)
workflow_instance = None
simple_runner = None

def get_workflow():
    """워크플로우 인스턴스 가져오기"""
    global workflow_instance, simple_runner

    try:
        if workflow_instance is None:
            workflow_instance = KakaoTemplateWorkflow()
        return workflow_instance
    except Exception as e:
        logger.warning(f"LangGraph workflow failed, using simple runner: {e}")
        if simple_runner is None:
            simple_runner = SimpleWorkflowRunner()
        return simple_runner

@router.post(
    "/generate",
    response_model=TemplateGenerationResponse,
    summary="알림톡 템플릿 생성",
    description="사용자 요청을 분석하여 카카오 정책에 부합하는 알림톡 템플릿을 생성합니다."
)
async def generate_template(
    request: TemplateGenerationRequest,
    background_tasks: BackgroundTasks
) -> TemplateGenerationResponse:
    """
    알림톡 템플릿 생성 API

    - 사용자 요청을 분석
    - 관련 정책 검색
    - 정책에 부합하는 템플릿 생성
    - 컴플라이언스 검증
    """
    start_time = time.time()

    try:
        logger.info(f"Template generation request: {request.user_request[:100]}...")

        # 워크플로우 실행
        workflow = get_workflow()

        if isinstance(workflow, KakaoTemplateWorkflow):
            # LangGraph 워크플로우 사용
            result = workflow.run(request.user_request)
        else:
            # 단순 워크플로우 사용
            result = workflow.run_simple_workflow(request.user_request)
            result = _format_simple_result(result, request)

        # 처리 시간 추가
        processing_time = time.time() - start_time
        if 'workflow_info' in result:
            result['workflow_info']['processing_time_seconds'] = round(processing_time, 2)

        # 백그라운드 태스크로 로깅
        background_tasks.add_task(
            log_generation_result,
            request.user_request,
            result.get('success', False),
            processing_time
        )

        if not result.get('success', False):
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "GENERATION_FAILED",
                    "message": "템플릿 생성에 실패했습니다.",
                    "details": "; ".join(result.get('workflow_info', {}).get('errors', []))
                }
            )

        return TemplateGenerationResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Template generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "서버 내부 오류가 발생했습니다.",
                "details": str(e)
            }
        )

@router.post(
    "/validate",
    response_model=TemplateValidationResponse,
    summary="템플릿 정책 준수 검증",
    description="기존 템플릿이 카카오 정책을 준수하는지 검증합니다."
)
async def validate_template(
    request: TemplateValidationRequest
) -> TemplateValidationResponse:
    """
    템플릿 정책 준수 검증 API

    - 템플릿 텍스트의 정책 준수 여부 확인
    - 위반사항 및 개선사항 제안
    - 승인 가능성 평가
    """
    try:
        logger.info(f"Template validation request: {request.template_text[:50]}...")

        # 컴플라이언스 체커 초기화
        llm_client = ClaudeLLMClient()
        compliance_checker = ComplianceCheckerAgent(llm_client)

        # 템플릿 정보 구성
        template_info = {
            'template_text': request.template_text,
            'variables': request.variables or [],
            'button_suggestion': request.button_text,
            'metadata': {
                'business_type': request.business_type or '기타'
            }
        }

        # 기본 정책 컨텍스트 (실제로는 RAG에서 가져와야 함)
        policy_context = """
        알림톡은 정보성 메시지만 발송 가능하며, 광고성 내용을 포함할 수 없습니다.
        메시지는 1,000자 이내여야 하고, 변수는 #{변수명} 형태로 사용해야 합니다.
        """

        # 컴플라이언스 검증
        compliance_result = compliance_checker.check_compliance(template_info, policy_context)

        # 컴플라이언스 보고서 생성
        compliance_report = compliance_checker.get_compliance_report(compliance_result)

        # 응답 구성
        response_data = {
            'success': True,
            'compliance': {
                'is_compliant': compliance_result.get('is_compliant', False),
                'score': compliance_result.get('compliance_score', 0),
                'violations': compliance_result.get('violations', []),
                'warnings': compliance_result.get('warnings', []),
                'recommendations': compliance_result.get('recommendations', []),
                'approval_probability': compliance_result.get('approval_probability', '낮음'),
                'required_changes': compliance_result.get('required_changes', [])
            },
            'detailed_scores': compliance_result.get('detailed_scores', {
                'basic_rules': 0,
                'blacklist_check': 0,
                'variable_usage': 0,
                'llm_analysis': 0
            }),
            'compliance_report': compliance_report
        }

        return TemplateValidationResponse(**response_data)

    except Exception as e:
        logger.error(f"Template validation error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "템플릿 검증 중 오류가 발생했습니다.",
                "details": str(e)
            }
        )

@router.get(
    "/examples/{business_type}",
    summary="비즈니스 유형별 템플릿 예시",
    description="특정 비즈니스 유형의 승인된 템플릿 예시를 조회합니다."
)
async def get_template_examples(
    business_type: str,
    limit: int = 5
) -> dict:
    """비즈니스 유형별 템플릿 예시 조회"""
    try:
        # 템플릿 스토어에서 예시 검색
        from ...database.vector_store import TemplateStore

        template_store = TemplateStore()
        examples = template_store.get_templates_by_business_type(business_type)

        # 승인된 템플릿만 필터링
        approved_examples = [
            t for t in examples
            if t.get('metadata', {}).get('approval_status') == 'approved'
        ]

        # 제한된 수량만 반환
        limited_examples = approved_examples[:limit]

        # 응답용 데이터 구성
        formatted_examples = []
        for example in limited_examples:
            formatted_examples.append({
                'id': example.get('id'),
                'text': example.get('text'),
                'category': f"{example.get('metadata', {}).get('category_1', '')} > {example.get('metadata', {}).get('category_2', '')}",
                'service_type': example.get('metadata', {}).get('service_type', ''),
                'variables': example.get('metadata', {}).get('variables', [])
            })

        return {
            'business_type': business_type,
            'total_found': len(approved_examples),
            'returned_count': len(formatted_examples),
            'examples': formatted_examples
        }

    except Exception as e:
        logger.error(f"Error getting template examples: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "EXAMPLES_ERROR",
                "message": "템플릿 예시 조회 중 오류가 발생했습니다.",
                "details": str(e)
            }
        )

@router.get(
    "/categories",
    summary="템플릿 카테고리 목록",
    description="사용 가능한 템플릿 카테고리 목록을 조회합니다."
)
async def get_template_categories() -> dict:
    """템플릿 카테고리 목록 조회"""
    try:
        categories = {
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
                "거래": ["주문/결제", "취소/환불", "영수증/세금계산서"],
                "배송": ["배송안내", "배송완료", "배송지연"],
                "예약": ["예약확인", "예약변경", "예약취소"],
                "회원관리": ["회원가입", "정보변경", "탈퇴"],
                "고객지원": ["문의답변", "상담안내", "공지사항"]
            },
            "business_types": [
                "교육", "의료", "음식점", "쇼핑몰",
                "서비스업", "금융", "기타"
            ],
            "service_types": [
                "신청", "예약", "주문", "배송",
                "안내", "확인", "피드백"
            ]
        }

        return categories

    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "CATEGORIES_ERROR",
                "message": "카테고리 조회 중 오류가 발생했습니다.",
                "details": str(e)
            }
        )

@router.post(
    "/batch-validate",
    summary="여러 템플릿 일괄 검증",
    description="여러 템플릿을 한 번에 검증합니다."
)
async def batch_validate_templates(
    templates: List[TemplateValidationRequest]
) -> dict:
    """여러 템플릿 일괄 검증"""
    if len(templates) > 10:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "TOO_MANY_TEMPLATES",
                "message": "한 번에 최대 10개의 템플릿만 검증할 수 있습니다.",
                "details": f"요청된 템플릿 수: {len(templates)}"
            }
        )

    try:
        results = []

        for i, template_request in enumerate(templates):
            try:
                # 개별 템플릿 검증
                result = await validate_template(template_request)
                results.append({
                    'index': i,
                    'success': True,
                    'result': result
                })
            except Exception as e:
                results.append({
                    'index': i,
                    'success': False,
                    'error': str(e)
                })

        # 통계 정보 계산
        successful_count = sum(1 for r in results if r['success'])
        compliant_count = sum(
            1 for r in results
            if r['success'] and r['result'].compliance.is_compliant
        )

        return {
            'total_templates': len(templates),
            'successful_validations': successful_count,
            'compliant_templates': compliant_count,
            'results': results
        }

    except Exception as e:
        logger.error(f"Batch validation error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "BATCH_VALIDATION_ERROR",
                "message": "일괄 검증 중 오류가 발생했습니다.",
                "details": str(e)
            }
        )

# Utility functions

def _format_simple_result(simple_result: dict, request: TemplateGenerationRequest) -> dict:
    """SimpleWorkflowRunner 결과를 표준 형식으로 변환"""
    if not simple_result.get('success', False):
        return {
            'success': False,
            'template': {
                'text': '',
                'variables': [],
                'button_suggestion': '',
                'metadata': {
                    'category_1': '',
                    'category_2': '',
                    'business_type': '',
                    'service_type': '',
                    'estimated_length': 0,
                    'variable_count': 0,
                    'target_audience': '',
                    'tone': '',
                    'generation_method': 'simple_workflow'
                }
            },
            'compliance': {
                'is_compliant': False,
                'score': 0,
                'violations': [simple_result.get('error', 'Unknown error')],
                'warnings': [],
                'recommendations': [],
                'approval_probability': '낮음',
                'required_changes': []
            },
            'analysis': {
                'business_type': request.business_type or '',
                'service_type': request.service_type or '',
                'message_purpose': '',
                'estimated_category': {},
                'compliance_concerns': []
            },
            'workflow_info': {
                'iterations': 0,
                'errors': [simple_result.get('error', 'Unknown error')],
                'policy_sources': []
            }
        }

    template = simple_result.get('template', {})
    compliance = simple_result.get('compliance', {})
    analysis = simple_result.get('analysis', {})

    return {
        'success': True,
        'template': {
            'text': template.get('template_text', ''),
            'variables': template.get('variables', []),
            'button_suggestion': template.get('button_suggestion', ''),
            'metadata': {
                'category_1': analysis.get('estimated_category', {}).get('category_1', ''),
                'category_2': analysis.get('estimated_category', {}).get('category_2', ''),
                'business_type': analysis.get('business_type', ''),
                'service_type': analysis.get('service_type', ''),
                'estimated_length': len(template.get('template_text', '')),
                'variable_count': len(template.get('variables', [])),
                'target_audience': analysis.get('target_audience', ''),
                'tone': analysis.get('tone', ''),
                'generation_method': 'simple_workflow'
            }
        },
        'compliance': {
            'is_compliant': compliance.get('is_compliant', False),
            'score': compliance.get('compliance_score', 0),
            'violations': compliance.get('violations', []),
            'warnings': compliance.get('warnings', []),
            'recommendations': compliance.get('recommendations', []),
            'approval_probability': compliance.get('approval_probability', '낮음'),
            'required_changes': compliance.get('required_changes', [])
        },
        'analysis': {
            'business_type': analysis.get('business_type', ''),
            'service_type': analysis.get('service_type', ''),
            'message_purpose': analysis.get('message_purpose', ''),
            'estimated_category': analysis.get('estimated_category', {}),
            'compliance_concerns': analysis.get('compliance_concerns', [])
        },
        'workflow_info': {
            'iterations': 1,
            'errors': [],
            'policy_sources': []
        }
    }

async def log_generation_result(user_request: str, success: bool, processing_time: float):
    """템플릿 생성 결과 로깅 (백그라운드 태스크)"""
    try:
        logger.info(f"Template generation completed - Success: {success}, Time: {processing_time:.2f}s, Request: {user_request[:50]}...")
        # 여기에 DB 저장, 모니터링 등의 로직 추가 가능
    except Exception as e:
        logger.error(f"Error logging generation result: {e}")