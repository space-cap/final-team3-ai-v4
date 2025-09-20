"""
초간단 템플릿 생성 API
user_request 하나만 입력하면 템플릿 생성
"""
import os
import time
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn
    from anthropic import Anthropic
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Please install: pip install fastapi uvicorn anthropic")
    exit(1)

# FastAPI app
app = FastAPI(
    title="Simple KakaoTalk Template API",
    description="간단한 카카오톡 템플릿 생성 서비스",
    version="2.0.0"
)

# Anthropic client
try:
    anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    print("Claude API client initialized successfully")
except Exception as e:
    print(f"Claude API initialization failed: {e}")
    anthropic_client = None

# Request model - 매우 간단!
class SimpleTemplateRequest(BaseModel):
    user_request: str  # 이것만 입력하면 됨!

# Response model
class SimpleTemplateResponse(BaseModel):
    success: bool
    template_text: str
    processing_time: float
    variables: list = []
    button_suggestion: str = ""
    compliance_note: str = ""

def create_simple_prompt(user_request: str) -> str:
    """매우 간단한 프롬프트 생성"""
    return f"""카카오톡 알림톡 템플릿을 생성해주세요.

사용자 요청: {user_request}

규칙:
- 1000자 이내
- 정보성 내용만 (광고 금지)
- 변수는 #{{"변수명"}} 형식
- 정중하고 명확한 톤

JSON 형태로 응답:
{{
  "template_text": "생성된 템플릿 내용",
  "variables": ["변수1", "변수2"],
  "button_suggestion": "버튼명 (선택사항)",
  "compliance_note": "정책 준수 참고사항"
}}"""

@app.get("/")
async def root():
    """API 소개"""
    return {
        "message": "Simple KakaoTalk Template Generator",
        "usage": "POST /generate with user_request",
        "example": {
            "user_request": "강의 수강 신청 완료 안내 메시지"
        },
        "api_docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """헬스체크"""
    return {
        "status": "healthy",
        "claude_api": "connected" if anthropic_client else "disconnected",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

@app.post("/generate", response_model=SimpleTemplateResponse)
async def generate_simple_template(request: SimpleTemplateRequest):
    """
    초간단 템플릿 생성 API

    user_request 하나만 입력하면 됩니다!

    예시:
    {
      "user_request": "온라인 강의 수강 신청 완료 안내"
    }
    """
    start_time = time.time()

    try:
        if not anthropic_client:
            raise HTTPException(
                status_code=500,
                detail="Claude API가 초기화되지 않았습니다. ANTHROPIC_API_KEY를 확인해주세요."
            )

        if not request.user_request.strip():
            raise HTTPException(
                status_code=400,
                detail="user_request는 비어있을 수 없습니다."
            )

        print(f"Template generation request: {request.user_request}")

        # 간단한 프롬프트로 Claude 호출
        prompt = create_simple_prompt(request.user_request)

        response = anthropic_client.messages.create(
            model="claude-3-5-haiku-20241022",  # 빠른 모델 사용
            max_tokens=1000,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # 응답 파싱
        try:
            result = json.loads(response.content[0].text)
            template_text = result.get("template_text", "Template generation failed.")
            variables = result.get("variables", [])
            button_suggestion = result.get("button_suggestion", "")
            compliance_note = result.get("compliance_note", "")
        except json.JSONDecodeError:
            # JSON 파싱 실패시 원문 그대로 사용
            template_text = response.content[0].text
            variables = []
            button_suggestion = ""
            compliance_note = "JSON parsing failed - raw response"

        processing_time = time.time() - start_time

        print(f"Template generated successfully ({processing_time:.2f}s)")
        print(f"Generated template: {template_text[:100]}...")

        return SimpleTemplateResponse(
            success=True,
            template_text=template_text,
            processing_time=round(processing_time, 2),
            variables=variables,
            button_suggestion=button_suggestion,
            compliance_note=compliance_note
        )

    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"Template generation failed: {e}")

        return SimpleTemplateResponse(
            success=False,
            template_text=f"Error occurred during template generation: {str(e)}",
            processing_time=round(processing_time, 2),
            variables=[],
            button_suggestion="",
            compliance_note="Error occurred"
        )

@app.post("/quick")
async def quick_template(request: SimpleTemplateRequest):
    """
    더욱 빠른 템플릿 생성 (최소한의 처리)
    """
    start_time = time.time()

    try:
        if not anthropic_client:
            return {"error": "Claude API not available"}

        # 매우 간단한 프롬프트
        simple_prompt = f"""알림톡 템플릿 생성: {request.user_request}

정보성 메시지, 1000자 이내, #{{"변수"}} 형식으로 생성:"""

        response = anthropic_client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=500,  # 더 적은 토큰
            temperature=0.1,  # 더 일관된 결과
            messages=[{"role": "user", "content": simple_prompt}]
        )

        template_text = response.content[0].text.strip()
        processing_time = time.time() - start_time

        return {
            "template": template_text,
            "time": round(processing_time, 2),
            "status": "success"
        }

    except Exception as e:
        processing_time = time.time() - start_time
        return {
            "template": f"생성 실패: {str(e)}",
            "time": round(processing_time, 2),
            "status": "error"
        }

# 사용 예시 엔드포인트
@app.get("/examples")
async def get_examples():
    """사용 예시"""
    return {
        "examples": [
            {
                "user_request": "온라인 강의 수강 신청 완료 안내",
                "description": "교육 관련 신청 완료 메시지"
            },
            {
                "user_request": "병원 예약 확인 및 준비사항 안내",
                "description": "의료 예약 확인 메시지"
            },
            {
                "user_request": "주문 상품 배송 시작 알림",
                "description": "배송 시작 알림 메시지"
            },
            {
                "user_request": "회원 가입 완료 환영 메시지",
                "description": "회원가입 완료 안내"
            },
            {
                "user_request": "이벤트 당첨 결과 발표",
                "description": "이벤트 결과 안내"
            }
        ],
        "usage_note": "위 예시 중 하나를 user_request에 입력하면 됩니다!"
    }

if __name__ == "__main__":
    print("Simple KakaoTalk Template API Starting...")
    print("API Docs: http://localhost:8001/docs")
    print("Health Check: http://localhost:8001/health")
    print("Examples: http://localhost:8001/examples")
    print()
    print("Simple Usage:")
    print('curl -X POST "http://localhost:8001/generate" -H "Content-Type: application/json" -d \'{"user_request": "course registration completed"}\'')
    print()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,  # 기존 서버와 포트 충돌 방지
        log_level="info"
    )