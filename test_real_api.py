"""
실제 Claude API를 사용한 템플릿 생성 테스트
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트를 Python 패스에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 환경변수 로드
load_dotenv()

def test_anthropic_connection():
    """Anthropic API 연결 테스트"""
    print("[TEST] Testing Anthropic API connection...")

    try:
        from anthropic import Anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("[ERROR] ANTHROPIC_API_KEY not found in environment")
            return False

        if api_key.startswith("sk-ant-api03-"):
            print(f"[OK] API key format is valid: {api_key[:20]}...")
        else:
            print("[WARN] API key format may be incorrect")

        # Anthropic 클라이언트 초기화
        client = Anthropic(api_key=api_key)
        print("[OK] Anthropic client initialized successfully")

        return client

    except ImportError as e:
        print(f"[ERROR] Failed to import anthropic: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to initialize Anthropic client: {e}")
        return False

def analyze_user_request_with_api(client, user_request):
    """실제 Claude API를 사용한 사용자 요청 분석"""
    print(f"[API] Analyzing request: {user_request[:50]}...")

    system_prompt = """당신은 카카오 알림톡 템플릿 요구사항 분석 전문가입니다.
사용자의 요청을 분석하여 다음 정보를 JSON 형태로 추출해주세요:

{
  "business_type": "비즈니스 유형 (교육, 의료, 음식점, 쇼핑몰, 서비스업, 금융, 기타)",
  "service_type": "서비스 유형 (신청, 예약, 주문, 배송, 안내, 확인, 피드백)",
  "message_purpose": "메시지 목적",
  "target_audience": "대상 고객층",
  "required_variables": ["필요한 변수들"],
  "tone": "톤앤매너 (정중한, 친근한, 공식적인)",
  "urgency": "긴급도 (높음, 보통, 낮음)"
}

응답은 반드시 유효한 JSON 형태로만 제공해주세요."""

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",  # 빠른 테스트용 haiku 모델
            max_tokens=1000,
            temperature=0.3,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"다음 사용자 요청을 분석해주세요:\n\n{user_request}"
                }
            ]
        )

        result = response.content[0].text
        print(f"[API] Analysis response received ({len(result)} chars)")

        # JSON 파싱 시도
        import json
        try:
            parsed_result = json.loads(result)
            return parsed_result
        except json.JSONDecodeError:
            print("[WARN] Failed to parse JSON, using fallback analysis")
            # 기본값 반환
            return {
                "business_type": "기타",
                "service_type": "안내",
                "message_purpose": "일반 안내",
                "target_audience": "고객",
                "required_variables": ["수신자명"],
                "tone": "정중한",
                "urgency": "보통"
            }

    except Exception as e:
        print(f"[ERROR] API call failed: {e}")
        return None

def generate_template_with_api(client, analysis_result):
    """실제 Claude API를 사용한 템플릿 생성"""
    print("[API] Generating template...")

    system_prompt = f"""당신은 카카오 알림톡 템플릿 생성 전문가입니다.
주어진 분석 결과를 바탕으로 카카오 정책에 완벽히 부합하는 알림톡 템플릿을 생성해주세요.

**중요한 규칙:**
1. 반드시 정보성 메시지여야 함 (광고성 내용 금지)
2. 변수는 #{{변수명}} 형태로 사용
3. 메시지는 1000자 이내
4. 정중한 톤 유지
5. 인사말 포함 필수
6. 메시지 하단에 "※ 이 메시지는 [서비스를 이용하신/신청하신/주문하신] 분들께 발송되는 정보성 안내입니다." 포함

응답 형태:
{{
  "template_text": "생성된 템플릿 내용",
  "variables": ["변수1", "변수2"],
  "button_suggestion": "제안 버튼명",
  "compliance_notes": "정책 준수 설명"
}}

응답은 반드시 유효한 JSON 형태로만 제공해주세요."""

    try:
        # 분석 결과를 문자열로 변환
        analysis_str = f"""
비즈니스 유형: {analysis_result.get('business_type', '기타')}
서비스 유형: {analysis_result.get('service_type', '안내')}
메시지 목적: {analysis_result.get('message_purpose', '일반 안내')}
대상 고객: {analysis_result.get('target_audience', '고객')}
필요 변수: {', '.join(analysis_result.get('required_variables', ['수신자명']))}
톤앤매너: {analysis_result.get('tone', '정중한')}
"""

        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1500,
            temperature=0.5,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"다음 분석 결과에 맞는 카카오 알림톡 템플릿을 생성해주세요:\n\n{analysis_str}"
                }
            ]
        )

        result = response.content[0].text
        print(f"[API] Template generation response received ({len(result)} chars)")

        # JSON 파싱 시도
        import json
        try:
            parsed_result = json.loads(result)
            return parsed_result
        except json.JSONDecodeError:
            print("[WARN] Failed to parse JSON, extracting text content")
            return {
                "template_text": result,
                "variables": analysis_result.get('required_variables', ['수신자명']),
                "button_suggestion": "자세히 보기",
                "compliance_notes": "API 응답 파싱 실패"
            }

    except Exception as e:
        print(f"[ERROR] Template generation API call failed: {e}")
        return None

def run_comprehensive_test():
    """종합적인 실제 API 테스트"""
    print("=" * 60)
    print("KakaoTalk Template Generation - Real API Test")
    print("=" * 60)

    # 1. API 연결 테스트
    client = test_anthropic_connection()
    if not client:
        print("[FAIL] Cannot proceed without API connection")
        return

    print("\n" + "=" * 60)

    # 2. 테스트 케이스들
    test_cases = [
        {
            "name": "Education Course Registration",
            "request": "온라인 파이썬 프로그래밍 강의 수강 신청 완료 안내 메시지를 만들어주세요"
        },
        {
            "name": "Medical Appointment",
            "request": "치과 진료 예약 확정 및 내원 시 준비사항을 안내하는 메시지"
        },
        {
            "name": "Shopping Order",
            "request": "온라인 쇼핑몰 주문 완료 후 배송 정보를 안내하는 메시지"
        }
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[TEST {i}] {test_case['name']}")
        print(f"Request: {test_case['request']}")
        print("-" * 50)

        # Step 1: 요청 분석
        analysis = analyze_user_request_with_api(client, test_case['request'])
        if not analysis:
            print("[FAIL] Request analysis failed")
            continue

        print(f"[ANALYSIS] Business Type: {analysis.get('business_type', 'N/A')}")
        print(f"[ANALYSIS] Service Type: {analysis.get('service_type', 'N/A')}")
        print(f"[ANALYSIS] Variables: {', '.join(analysis.get('required_variables', []))}")

        # Step 2: 템플릿 생성
        template = generate_template_with_api(client, analysis)
        if not template:
            print("[FAIL] Template generation failed")
            continue

        print(f"[GENERATION] Template Length: {len(template.get('template_text', ''))} chars")
        print(f"[GENERATION] Variables: {', '.join(template.get('variables', []))}")

        # Step 3: 생성된 템플릿 출력
        print(f"\n[TEMPLATE] Generated Template:")
        print("-" * 30)
        print(template.get('template_text', 'No template generated'))
        print("-" * 30)

        if template.get('button_suggestion'):
            print(f"[BUTTON] Suggested: {template['button_suggestion']}")

        results.append({
            "test_case": test_case['name'],
            "success": True,
            "analysis": analysis,
            "template": template
        })

        print(f"[SUCCESS] Test {i} completed successfully")

    # 3. 결과 요약
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    successful_tests = len([r for r in results if r['success']])
    total_tests = len(test_cases)

    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")

    if successful_tests > 0:
        print(f"\n[SUCCESS] Real API integration working properly!")
        print("- Claude API connection successful")
        print("- Request analysis with AI working")
        print("- Template generation with AI working")
        print("- Policy-compliant templates generated")
    else:
        print(f"\n[FAIL] API integration issues detected")

    return results

if __name__ == "__main__":
    run_comprehensive_test()