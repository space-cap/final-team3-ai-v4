"""
간단한 FastAPI 서버 테스트
"""
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트를 Python 패스에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 환경변수 로드
load_dotenv()

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn
    from anthropic import Anthropic
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Please install: pip install fastapi uvicorn anthropic")
    sys.exit(1)

# FastAPI 앱 생성
app = FastAPI(
    title="카카오 알림톡 템플릿 생성 API",
    description="Claude AI를 사용한 알림톡 템플릿 자동 생성 서비스",
    version="1.0.0"
)

# Anthropic 클라이언트 초기화
anthropic_client = None

@app.on_event("startup")
async def startup_event():
    global anthropic_client
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        anthropic_client = Anthropic(api_key=api_key)
        print("✅ Anthropic API client initialized")
    else:
        print("⚠️ ANTHROPIC_API_KEY not found")

# 요청 모델
class TemplateRequest(BaseModel):
    user_request: str
    business_type: str = None
    tone: str = "정중한"

# 응답 모델
class TemplateResponse(BaseModel):
    success: bool
    template_text: str = None
    variables: list = None
    business_type: str = None
    service_type: str = None
    compliance_score: int = None
    error: str = None

@app.get("/")
async def root():
    """기본 엔드포인트"""
    return {
        "service": "카카오 알림톡 템플릿 자동 생성 API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "generate": "/api/v1/templates/generate"
        }
    }

@app.get("/health")
async def health_check():
    """헬스체크"""
    return {
        "status": "healthy",
        "anthropic_api": "connected" if anthropic_client else "not_connected",
        "timestamp": "2024-09-19T20:00:00Z"
    }

@app.post("/api/v1/templates/generate", response_model=TemplateResponse)
async def generate_template(request: TemplateRequest):
    """템플릿 생성 API"""

    if not anthropic_client:
        raise HTTPException(status_code=503, detail="Anthropic API not available")

    try:
        # 1. 요청 분석
        analysis_result = await analyze_request(request.user_request)

        # 2. 템플릿 생성
        template_result = await generate_template_with_claude(analysis_result, request.user_request)

        return TemplateResponse(
            success=True,
            template_text=template_result.get("template_text"),
            variables=template_result.get("variables", []),
            business_type=analysis_result.get("business_type"),
            service_type=analysis_result.get("service_type"),
            compliance_score=90  # Mock score
        )

    except Exception as e:
        return TemplateResponse(
            success=False,
            error=str(e)
        )

async def analyze_request(user_request: str):
    """요청 분석"""
    system_prompt = """사용자 요청을 분석하여 JSON으로 반환하세요:
{
  "business_type": "비즈니스 유형",
  "service_type": "서비스 유형",
  "required_variables": ["변수들"]
}"""

    try:
        response = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            temperature=0.3,
            system=system_prompt,
            messages=[{"role": "user", "content": user_request}]
        )

        result = response.content[0].text
        return json.loads(result)
    except:
        return {
            "business_type": "기타",
            "service_type": "안내",
            "required_variables": ["수신자명"]
        }

async def generate_template_with_claude(analysis, user_request):
    """Claude를 사용한 템플릿 생성"""
    system_prompt = """카카오 알림톡 정책에 맞는 템플릿을 JSON으로 생성하세요:
{
  "template_text": "생성된 템플릿",
  "variables": ["변수들"]
}

규칙:
- 정보성 메시지만 생성
- 인사말 포함
- 1000자 이내
- 변수는 #{변수명} 형태
- 하단에 정보성 메시지 표시 포함"""

    try:
        prompt = f"요청: {user_request}\n분석: {analysis}"

        response = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            temperature=0.5,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )

        result = response.content[0].text
        return json.loads(result)
    except:
        return {
            "template_text": "안녕하세요 #{수신자명}님,\n\n요청하신 서비스 관련 안내드립니다.\n\n※ 이 메시지는 정보성 안내입니다.",
            "variables": ["수신자명"]
        }

# 테스트용 엔드포인트
@app.post("/test/quick")
async def quick_test():
    """빠른 테스트"""
    test_request = TemplateRequest(
        user_request="온라인 강의 수강 신청 완료 안내 메시지"
    )

    return await generate_template(test_request)

def run_api_test():
    """API 서버 테스트 실행"""
    print("🚀 FastAPI 서버 테스트 시작")
    print("=" * 50)

    # 환경 확인
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY가 설정되지 않았습니다")
        return

    print("✅ API 키 확인됨")
    print("✅ FastAPI 앱 초기화됨")

    print("\n📡 서버 시작 중...")
    print("서버 주소: http://localhost:8000")
    print("API 문서: http://localhost:8000/docs")
    print("헬스체크: http://localhost:8000/health")
    print("빠른 테스트: http://localhost:8000/test/quick")

    print("\n서버를 중지하려면 Ctrl+C를 누르세요")
    print("=" * 50)

    # 서버 실행
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )

if __name__ == "__main__":
    run_api_test()