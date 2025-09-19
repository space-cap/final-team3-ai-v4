"""
Simple FastAPI server for template generation testing
"""
import os
import json
from pathlib import Path
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
    title="KakaoTalk Template Generator API",
    description="AI-powered KakaoTalk template generation service",
    version="1.0.0"
)

# Anthropic client
anthropic_client = None

@app.on_event("startup")
async def startup_event():
    global anthropic_client
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        anthropic_client = Anthropic(api_key=api_key)
        print("Anthropic API client initialized successfully")
    else:
        print("Warning: ANTHROPIC_API_KEY not found")

# Request model
class TemplateRequest(BaseModel):
    user_request: str
    business_type: str = None
    tone: str = "polite"

# Response model
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
    """Root endpoint"""
    return {
        "service": "KakaoTalk Template Auto Generator API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "generate": "/api/v1/templates/generate",
            "quick_test": "/test/quick"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "anthropic_api": "connected" if anthropic_client else "not_connected",
        "timestamp": "2024-09-19T20:00:00Z"
    }

@app.post("/api/v1/templates/generate", response_model=TemplateResponse)
async def generate_template(request: TemplateRequest):
    """Template generation API"""

    if not anthropic_client:
        raise HTTPException(status_code=503, detail="Anthropic API not available")

    try:
        # 1. Analyze request
        analysis_result = await analyze_request(request.user_request)

        # 2. Generate template
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
    """Analyze user request with Claude"""
    system_prompt = """Analyze the user request and return JSON:
{
  "business_type": "business type in Korean",
  "service_type": "service type in Korean",
  "required_variables": ["variables in Korean"]
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
    """Generate template with Claude"""
    system_prompt = """Generate KakaoTalk template in JSON format:
{
  "template_text": "generated template",
  "variables": ["variables"]
}

Rules:
- Information message only
- Include greeting
- Max 1000 characters
- Use #{variable} format
- Include compliance notice at bottom"""

    try:
        prompt = f"Request: {user_request}\nAnalysis: {analysis}"

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
            "template_text": f"안녕하세요 #{{수신자명}}님,\n\n요청하신 서비스 관련 안내드립니다.\n\n※ 이 메시지는 정보성 안내입니다.",
            "variables": ["수신자명"]
        }

# Quick test endpoint
@app.post("/test/quick")
async def quick_test():
    """Quick test endpoint"""
    test_request = TemplateRequest(
        user_request="온라인 강의 수강 신청 완료 안내 메시지"
    )

    return await generate_template(test_request)

def run_server():
    """Run the API server"""
    print("=" * 50)
    print("FastAPI Server Starting")
    print("=" * 50)

    # Environment check
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not configured")
        return

    print("API key confirmed")
    print("FastAPI app initialized")

    print("\nServer starting...")
    print("Server address: http://localhost:8000")
    print("API docs: http://localhost:8000/docs")
    print("Health check: http://localhost:8000/health")
    print("Quick test: http://localhost:8000/test/quick")

    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)

    # Run server
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )

if __name__ == "__main__":
    run_server()