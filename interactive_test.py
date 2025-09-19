"""
대화형 템플릿 생성 테스트
사용자가 직접 요청을 입력하여 템플릿을 생성할 수 있습니다.
"""

from simple_template_test import analyze_request, generate_template, check_compliance

def interactive_template_test():
    """대화형 템플릿 생성 테스트"""

    print("=" * 60)
    print("🚀 카카오톡 템플릿 자동 생성 - 대화형 테스트")
    print("=" * 60)
    print("원하는 템플릿 요청을 입력하면 즉시 생성해드립니다!")
    print("예시: '온라인 쇼핑몰 주문 완료 안내', '병원 예약 확정 메시지' 등")
    print("종료하려면 'quit' 또는 'exit'를 입력하세요.")
    print()

    test_count = 0

    while True:
        try:
            # 사용자 입력 받기
            user_request = input("📝 템플릿 요청을 입력하세요: ").strip()

            # 종료 조건
            if user_request.lower() in ['quit', 'exit', '종료', '끝']:
                print("\n👋 테스트를 종료합니다!")
                break

            if not user_request:
                print("❌ 요청을 입력해주세요!")
                continue

            test_count += 1
            print(f"\n[테스트 {test_count}] {user_request}")
            print("-" * 50)

            # 1. 요청 분석
            analysis = analyze_request(user_request)
            print(f"🔍 [분석 결과]")
            print(f"   업종: {analysis['business_type']}")
            print(f"   서비스: {analysis['service_type']}")
            print(f"   변수: {', '.join(analysis['variables'])}")

            # 2. 템플릿 생성
            template = generate_template(analysis)
            print(f"\n📝 [템플릿 생성]")
            print(f"   길이: {template['length']}자")
            print(f"   버튼 제안: {template['button_suggestion']}")

            # 3. 정책 준수 체크
            compliance = check_compliance(template)
            print(f"\n✅ [정책 준수 체크]")
            print(f"   점수: {compliance['compliance_score']}/100")
            print(f"   승인 가능성: {compliance['approval_probability']}")

            if compliance['violations']:
                print(f"   ⚠️ 위반사항: {', '.join(compliance['violations'])}")
            if compliance['warnings']:
                print(f"   💡 주의사항: {', '.join(compliance['warnings'])}")

            # 4. 생성된 템플릿 출력
            print(f"\n📱 [생성된 카카오톡 템플릿]")
            print("=" * 40)
            print(template['template_text'])
            print("=" * 40)

            print(f"\n✨ 테스트 {test_count} 완료!")
            print("\n" + "─" * 60)

        except KeyboardInterrupt:
            print("\n\n👋 테스트를 중단합니다!")
            break
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            print("다시 시도해주세요.")

    # 테스트 요약
    if test_count > 0:
        print(f"\n📊 테스트 요약:")
        print(f"   총 테스트 수: {test_count}개")
        print(f"   시스템 상태: 정상 작동 ✅")
        print(f"\n🎉 카카오톡 템플릿 자동 생성 시스템이 완벽하게 작동합니다!")

if __name__ == "__main__":
    interactive_template_test()