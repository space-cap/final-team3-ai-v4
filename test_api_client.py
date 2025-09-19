"""
API 클라이언트를 사용한 FastAPI 테스트
"""
import requests
import json

def test_api_server():
    """FastAPI 서버 테스트"""
    base_url = "http://localhost:8000"

    print("=" * 60)
    print("FastAPI + Claude API 연동 테스트")
    print("=" * 60)

    # 1. 서버 상태 확인
    print("1. 서버 상태 확인...")
    try:
        response = requests.get(f"{base_url}/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
        return

    # 2. 헬스체크
    print("\n2. 헬스체크...")
    try:
        response = requests.get(f"{base_url}/health")
        health_data = response.json()
        print(f"   Status: {health_data.get('status')}")
        print(f"   Claude API: {health_data.get('anthropic_api')}")
    except Exception as e:
        print(f"   Error: {e}")
        return

    # 3. 빠른 테스트
    print("\n3. 빠른 테스트 (미리 정의된 요청)...")
    try:
        response = requests.post(f"{base_url}/test/quick")
        quick_result = response.json()
        print(f"   Success: {quick_result.get('success')}")
        print(f"   Business Type: {quick_result.get('business_type')}")
        print(f"   Service Type: {quick_result.get('service_type')}")
        print(f"   Template Length: {len(quick_result.get('template_text', ''))}")
    except Exception as e:
        print(f"   Error: {e}")

    # 4. 실제 Claude API 템플릿 생성 테스트
    test_cases = [
        {
            "name": "피자 배달 주문",
            "request": "피자 배달 주문 완료 안내 메시지를 만들어주세요"
        },
        {
            "name": "헬스장 회원권",
            "request": "헬스장 회원권 등록 완료 안내 메시지"
        },
        {
            "name": "온라인 쇼핑",
            "request": "온라인 쇼핑몰 주문 완료 후 배송 안내 메시지"
        }
    ]

    print("\n4. 실제 Claude API 템플릿 생성 테스트...")

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n   Test {i}: {test_case['name']}")
        print(f"   Request: {test_case['request']}")
        print("   " + "-" * 40)

        try:
            payload = {
                "user_request": test_case['request'],
                "tone": "polite"
            }

            response = requests.post(
                f"{base_url}/api/v1/templates/generate",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()

                if result.get('success'):
                    print(f"   ✅ Success!")
                    print(f"   Business Type: {result.get('business_type')}")
                    print(f"   Service Type: {result.get('service_type')}")
                    print(f"   Variables: {', '.join(result.get('variables', []))}")
                    print(f"   Compliance Score: {result.get('compliance_score')}/100")
                    print(f"   Template Length: {len(result.get('template_text', ''))} chars")

                    # 템플릿 미리보기 (처음 100자)
                    template_preview = result.get('template_text', '')[:100]
                    print(f"   Template Preview: {template_preview}...")
                else:
                    print(f"   ❌ Failed: {result.get('error')}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                print(f"   Response: {response.text}")

        except Exception as e:
            print(f"   ❌ Exception: {e}")

    print("\n" + "=" * 60)
    print("FastAPI + Claude API 테스트 완료")
    print("=" * 60)
    print("\n💡 웹 브라우저에서 테스트:")
    print("   - API 문서: http://localhost:8000/docs")
    print("   - 빠른 테스트: http://localhost:8000/test/quick")
    print("   - 헬스체크: http://localhost:8000/health")

if __name__ == "__main__":
    test_api_server()