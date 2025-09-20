"""
간단한 API 테스트 스크립트
"""
import time
import requests
import json

def test_simple_api():
    """간단한 API 테스트"""

    base_url = "http://localhost:8001"

    # 테스트 케이스들
    test_cases = [
        "강의 수강 신청 완료 안내",
        "병원 예약 확인 메시지",
        "주문 상품 배송 시작 알림",
        "회원가입 완료 환영 메시지",
        "이벤트 참여 감사 인사"
    ]

    print("🚀 간단한 템플릿 API 테스트 시작")
    print("=" * 50)

    for i, user_request in enumerate(test_cases, 1):
        print(f"\n📝 테스트 {i}: {user_request}")

        # /generate 엔드포인트 테스트
        start_time = time.time()

        try:
            response = requests.post(
                f"{base_url}/generate",
                json={"user_request": user_request},
                timeout=30
            )

            end_time = time.time()
            total_time = end_time - start_time

            if response.status_code == 200:
                result = response.json()

                print(f"✅ 성공 ({total_time:.2f}초)")
                print(f"📄 템플릿: {result['template_text'][:100]}...")
                if result.get('variables'):
                    print(f"🔤 변수: {', '.join(result['variables'])}")
                if result.get('button_suggestion'):
                    print(f"🔘 버튼: {result['button_suggestion']}")

            else:
                print(f"❌ 실패 (HTTP {response.status_code})")
                print(f"📄 응답: {response.text[:200]}...")

        except Exception as e:
            print(f"❌ 오류: {str(e)}")

        # 테스트 간 간격
        if i < len(test_cases):
            time.sleep(1)

    print(f"\n🏁 테스트 완료!")

def test_quick_endpoint():
    """빠른 엔드포인트 테스트"""

    print("\n⚡ 빠른 생성 엔드포인트 테스트")
    print("-" * 30)

    test_request = "카페 주문 준비 완료 알림"

    try:
        start_time = time.time()

        response = requests.post(
            "http://localhost:8001/quick",
            json={"user_request": test_request},
            timeout=15
        )

        end_time = time.time()
        total_time = end_time - start_time

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 빠른 생성 완료 ({total_time:.2f}초)")
            print(f"📄 템플릿: {result['template']}")
        else:
            print(f"❌ 실패: {response.text}")

    except Exception as e:
        print(f"❌ 오류: {e}")

if __name__ == "__main__":
    # 서버 연결 확인
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            print("✅ 간단한 API 서버 연결됨")
            test_simple_api()
            test_quick_endpoint()
        else:
            print("❌ 서버 연결 실패")
    except Exception as e:
        print(f"❌ 서버 연결 오류: {e}")
        print("먼저 'python simple_template_api.py'로 서버를 시작해주세요.")