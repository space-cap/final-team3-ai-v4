"""
카카오 알림톡 템플릿 자동 생성 AI 서비스 - FastAPI 메인 애플리케이션
"""
import os
import time
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from .routes import templates
from .models.schemas import HealthStatus, SystemStats, ErrorResponse
from ..database.vector_store import PolicyVectorStore

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 전역 변수
app_start_time = None
request_count = 0
successful_generations = 0
total_compliance_score = 0.0
total_processing_time = 0.0

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    global app_start_time

    # Startup
    logger.info("Starting KakaoTalk Template Generation Service...")
    app_start_time = time.time()

    try:
        # 로그 디렉토리 생성
        os.makedirs('logs', exist_ok=True)

        # 벡터 데이터베이스 초기화
        logger.info("Initializing vector database...")
        vector_store = PolicyVectorStore()

        # 정책 문서가 로드되어 있는지 확인
        try:
            # 테스트 검색으로 데이터 존재 확인
            test_results = vector_store.search_relevant_policies("알림톡", k=1)
            if not test_results:
                logger.info("Loading policy documents...")
                vector_store.load_policy_documents()
            else:
                logger.info("Policy documents already loaded")
        except Exception as e:
            logger.warning(f"Error checking/loading policies: {e}")

        logger.info("Service startup completed successfully")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down KakaoTalk Template Generation Service...")

# FastAPI 앱 생성
app = FastAPI(
    title="카카오 알림톡 템플릿 자동 생성 AI 서비스",
    description="""
    소상공인을 위한 카카오 알림톡 템플릿 자동 생성 서비스입니다.

    ## 주요 기능
    - 사용자 요청 분석 및 분류
    - 정책 기반 템플릿 자동 생성
    - 컴플라이언스 검증 및 개선사항 제안
    - 승인 가능성 평가

    ## 사용 방법
    1. `/api/v1/templates/generate` 엔드포인트로 템플릿 생성 요청
    2. 생성된 템플릿과 컴플라이언스 결과 확인
    3. 필요 시 `/api/v1/templates/validate`로 추가 검증
    """,
    version="1.0.0",
    contact={
        "name": "Final Team 3 AI",
        "email": "team3@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 운영 환경에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 신뢰할 수 있는 호스트 미들웨어
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # 운영 환경에서는 특정 호스트로 제한
)

# 요청 로깅 미들웨어
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """요청 로깅 및 통계 수집"""
    global request_count
    start_time = time.time()

    # 요청 카운트 증가
    request_count += 1

    # 요청 로깅
    logger.info(f"Request: {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # 응답 로깅
        logger.info(f"Response: {response.status_code} - {process_time:.3f}s")

        # 응답 헤더에 처리 시간 추가
        response.headers["X-Process-Time"] = str(process_time)

        return response

    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Request failed: {e} - {process_time:.3f}s")
        raise

# 라우터 등록
app.include_router(templates.router)

# 기본 엔드포인트들

@app.get("/", summary="서비스 정보", tags=["기본"])
async def root():
    """서비스 기본 정보"""
    return {
        "service": "카카오 알림톡 템플릿 자동 생성 AI 서비스",
        "version": "1.0.0",
        "description": "소상공인을 위한 정책 준수 알림톡 템플릿 자동 생성",
        "docs_url": "/docs",
        "health_check": "/health"
    }

@app.get(
    "/health",
    response_model=HealthStatus,
    summary="서비스 상태 확인",
    tags=["시스템"]
)
async def health_check():
    """서비스 상태 및 구성 요소 확인"""
    try:
        # 각 구성 요소 상태 확인
        components = {}

        # LLM 클라이언트 상태
        try:
            from ..utils.llm_client import ClaudeLLMClient
            llm_client = ClaudeLLMClient()
            components["llm_client"] = "healthy"
        except Exception as e:
            components["llm_client"] = f"error: {str(e)}"

        # 벡터 데이터베이스 상태
        try:
            vector_store = PolicyVectorStore()
            test_results = vector_store.search_relevant_policies("test", k=1)
            components["vector_database"] = "healthy"
        except Exception as e:
            components["vector_database"] = f"error: {str(e)}"

        # 워크플로우 상태
        try:
            from ..workflow.langgraph_workflow import KakaoTemplateWorkflow
            workflow = KakaoTemplateWorkflow()
            components["workflow"] = "healthy"
        except Exception as e:
            components["workflow"] = f"fallback: {str(e)}"

        # 전체 상태 결정
        overall_status = "healthy" if all(
            "healthy" in status for status in components.values()
        ) else "degraded"

        return HealthStatus(
            status=overall_status,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            version="1.0.0",
            components=components
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "HEALTH_CHECK_FAILED",
                "message": "상태 확인 중 오류가 발생했습니다.",
                "details": str(e)
            }
        )

@app.get(
    "/stats",
    response_model=SystemStats,
    summary="시스템 통계",
    tags=["시스템"]
)
async def get_system_stats():
    """시스템 사용 통계 조회"""
    global request_count, successful_generations, total_compliance_score, total_processing_time

    try:
        uptime_seconds = time.time() - app_start_time if app_start_time else 0

        avg_compliance_score = (
            total_compliance_score / successful_generations
            if successful_generations > 0 else 0
        )

        avg_processing_time = (
            total_processing_time / successful_generations
            if successful_generations > 0 else 0
        )

        return SystemStats(
            total_requests=request_count,
            successful_generations=successful_generations,
            average_compliance_score=round(avg_compliance_score, 2),
            average_processing_time=round(avg_processing_time, 3),
            most_common_business_types=["교육", "서비스업", "쇼핑몰"]  # 실제로는 DB에서 조회
        )

    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "STATS_ERROR",
                "message": "통계 조회 중 오류가 발생했습니다.",
                "details": str(e)
            }
        )

# 전역 예외 처리기

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외 처리기"""
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")

    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.detail
            }
        )
    else:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": "HTTP_ERROR",
                    "message": str(exc.detail),
                    "details": None
                }
            }
        )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 처리기"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "서버 내부 오류가 발생했습니다.",
                "details": str(exc) if app.debug else None
            }
        }
    )

# OpenAPI 스키마 커스터마이징

def custom_openapi():
    """커스텀 OpenAPI 스키마"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # API 예제 추가
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# 개발 모드에서만 활성화되는 엔드포인트들

if os.getenv("ENVIRONMENT") == "development":
    @app.get("/debug/reset", summary="시스템 리셋 (개발용)", tags=["개발"])
    async def debug_reset():
        """개발용 시스템 리셋"""
        global request_count, successful_generations, total_compliance_score, total_processing_time

        request_count = 0
        successful_generations = 0
        total_compliance_score = 0.0
        total_processing_time = 0.0

        return {"message": "System statistics reset"}

    @app.get("/debug/test-workflow", summary="워크플로우 테스트 (개발용)", tags=["개발"])
    async def debug_test_workflow():
        """개발용 워크플로우 테스트"""
        try:
            from ..workflow.langgraph_workflow import SimpleWorkflowRunner

            runner = SimpleWorkflowRunner()
            result = runner.run_simple_workflow("테스트 메시지 생성 요청")

            return {
                "test_completed": True,
                "result_success": result.get('success', False),
                "workflow_type": "SimpleWorkflowRunner"
            }

        except Exception as e:
            return {
                "test_completed": False,
                "error": str(e)
            }

# 통계 업데이트 함수 (라우터에서 호출)

def update_generation_stats(success: bool, compliance_score: float = 0, processing_time: float = 0):
    """템플릿 생성 통계 업데이트"""
    global successful_generations, total_compliance_score, total_processing_time

    if success:
        successful_generations += 1
        total_compliance_score += compliance_score
        total_processing_time += processing_time

# 애플리케이션 메타데이터
app.state.service_info = {
    "name": "KakaoTalk Template Generator",
    "version": "1.0.0",
    "authors": ["Final Team 3 AI"],
    "description": "AI-powered KakaoTalk template generation service"
}

if __name__ == "__main__":
    import uvicorn

    # 개발 서버 실행
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )