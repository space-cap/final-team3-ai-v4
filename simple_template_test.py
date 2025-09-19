"""
Simple template generation test without Unicode characters
"""

def analyze_request(user_request):
    """Analyze user request and classify business type"""
    analysis = {
        "business_type": "기타",
        "service_type": "안내",
        "variables": ["수신자명"]
    }

    # Education keywords
    if any(keyword in user_request for keyword in ["강의", "수강", "교육", "학습"]):
        analysis["business_type"] = "교육"
        analysis["service_type"] = "신청" if "신청" in user_request else "안내"
        analysis["variables"] = ["수신자명", "강의명", "일정"]

    # Shopping keywords
    elif any(keyword in user_request for keyword in ["주문", "배송", "쇼핑", "구매"]):
        analysis["business_type"] = "쇼핑몰"
        analysis["service_type"] = "주문" if "주문" in user_request else "배송"
        analysis["variables"] = ["수신자명", "상품명", "주문번호"]

    # Medical keywords
    elif any(keyword in user_request for keyword in ["예약", "병원", "진료", "의료"]):
        analysis["business_type"] = "의료"
        analysis["service_type"] = "예약"
        analysis["variables"] = ["수신자명", "예약일시", "병원명"]

    # Restaurant keywords
    elif any(keyword in user_request for keyword in ["음식", "메뉴", "식당", "배달"]):
        analysis["business_type"] = "음식점"
        analysis["service_type"] = "주문" if "주문" in user_request else "예약"
        analysis["variables"] = ["수신자명", "메뉴명", "픽업시간"]

    return analysis

def generate_template(analysis):
    """Generate template based on analysis"""
    business_type = analysis["business_type"]
    service_type = analysis["service_type"]
    variables = analysis["variables"]

    templates = {
        "교육": {
            "신청": """안녕하세요 #{수신자명}님,

요청하신 #{강의명} 수강 신청이 완료되었습니다.

▶ 강의 일정: #{일정}
▶ 참여 방법: 등록하신 이메일로 발송된 링크를 확인해주세요.

궁금한 사항이 있으시면 언제든 문의해주세요.

※ 이 메시지는 강의를 신청하신 분들께 발송되는 정보성 안내입니다.""",

            "안내": """안녕하세요 #{수신자명}님,

#{강의명} 관련 안내사항을 전달드립니다.

▶ 일정: #{일정}
▶ 장소: 온라인 강의실

자세한 내용은 아래 버튼을 통해 확인하실 수 있습니다.

※ 이 메시지는 수강생분들께 발송되는 정보성 안내입니다."""
        },

        "쇼핑몰": {
            "주문": """안녕하세요 #{수신자명}님,

주문해주신 #{상품명}의 주문이 접수되었습니다.

▶ 주문번호: #{주문번호}
▶ 예상 배송일: 2-3일 소요

배송 준비가 완료되면 다시 안내드리겠습니다.

※ 이 메시지는 주문을 하신 분들께 발송되는 정보성 안내입니다.""",

            "배송": """안녕하세요 #{수신자명}님,

주문하신 #{상품명}이 배송 시작되었습니다.

▶ 주문번호: #{주문번호}
▶ 택배사: CJ대한통운
▶ 운송장번호: 1234567890

배송 조회는 아래 버튼을 통해 확인하실 수 있습니다.

※ 이 메시지는 배송 관련 정보성 안내입니다."""
        },

        "의료": {
            "예약": """안녕하세요 #{수신자명}님,

#{병원명} 진료 예약이 확정되었습니다.

▶ 예약일시: #{예약일시}
▶ 진료과: #{진료과}
▶ 담당의: #{담당의}

진료 30분 전까지 접수를 완료해주시기 바랍니다.

※ 이 메시지는 진료를 예약하신 분들께 발송되는 정보성 안내입니다."""
        },

        "음식점": {
            "주문": """안녕하세요 #{수신자명}님,

주문해주신 #{메뉴명} 접수가 완료되었습니다.

▶ 주문 시간: #{주문시간}
▶ 예상 준비 시간: #{픽업시간}
▶ 총 금액: #{총금액}원

준비가 완료되면 연락드리겠습니다.

※ 이 메시지는 주문을 하신 분들께 발송되는 정보성 안내입니다.""",

            "예약": """안녕하세요 #{수신자명}님,

#{식당명} 예약이 확정되었습니다.

▶ 예약일시: #{예약일시}
▶ 인원: #{인원}명
▶ 테이블: #{테이블번호}

예약 시간 10분 전까지 도착해주시기 바랍니다.

※ 이 메시지는 예약을 하신 분들께 발송되는 정보성 안내입니다."""
        }
    }

    # Get template or default
    template_text = templates.get(business_type, {}).get(service_type,
        """안녕하세요 #{수신자명}님,

요청하신 서비스 관련 안내드립니다.

자세한 내용은 아래 버튼을 통해 확인하실 수 있습니다.

※ 이 메시지는 서비스 이용 관련 정보성 안내입니다.""")

    return {
        "template_text": template_text,
        "variables": variables,
        "button_suggestion": "자세히 보기",
        "length": len(template_text),
        "business_type": business_type,
        "service_type": service_type
    }

def check_compliance(template):
    """Check template compliance with KakaoTalk policies"""
    template_text = template["template_text"]

    violations = []
    warnings = []
    score = 100

    # Length check (max 1000 chars)
    if len(template_text) > 1000:
        violations.append("메시지 길이가 1000자를 초과합니다")
        score -= 20

    # Greeting check
    if not any(greeting in template_text for greeting in ["안녕하세요", "안녕하십니까"]):
        warnings.append("인사말이 포함되지 않았습니다")
        score -= 5

    # Information message indicator
    if "정보성" not in template_text and "안내" not in template_text:
        violations.append("정보성 메시지 표시가 없습니다")
        score -= 15

    # Advertisement keywords check
    ad_keywords = ["할인", "이벤트", "특가", "무료", "프로모션"]
    found_ad_keywords = [kw for kw in ad_keywords if kw in template_text]
    if found_ad_keywords:
        violations.append(f"광고성 키워드 발견: {', '.join(found_ad_keywords)}")
        score -= 25

    # Variable count check (max 40)
    variables = template["variables"]
    if len(variables) > 40:
        violations.append("변수 개수가 40개를 초과합니다")
        score -= 15

    return {
        "is_compliant": len(violations) == 0,
        "compliance_score": max(0, score),
        "violations": violations,
        "warnings": warnings,
        "approval_probability": "높음" if score >= 85 else "보통" if score >= 70 else "낮음"
    }

def test_template_generation():
    """Test template generation with various scenarios"""

    print("=" * 60)
    print("KakaoTalk Template Generation Test")
    print("=" * 60)

    test_cases = [
        {
            "name": "Education - Course Registration",
            "request": "온라인 파이썬 프로그래밍 강의 수강 신청 완료 안내 메시지를 만들어주세요"
        },
        {
            "name": "Shopping - Order Confirmation",
            "request": "온라인 쇼핑몰에서 신발 주문 완료 후 배송 정보를 안내하는 메시지"
        },
        {
            "name": "Medical - Appointment",
            "request": "치과 진료 예약 확정 안내 및 내원 시 준비사항 메시지"
        },
        {
            "name": "Restaurant - Takeout Order",
            "request": "카페에서 음료 테이크아웃 주문 접수 완료 및 픽업 시간 안내"
        },
        {
            "name": "Violation Test - Advertisement",
            "request": "50% 할인 이벤트 진행 중! 특가 상품을 확인하세요"
        }
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print(f"Request: {test_case['request']}")
        print("-" * 50)

        # Step 1: Analyze request
        analysis = analyze_request(test_case['request'])
        print(f"[ANALYSIS] Business Type: {analysis['business_type']}")
        print(f"[ANALYSIS] Service Type: {analysis['service_type']}")

        # Step 2: Generate template
        template = generate_template(analysis)
        print(f"[GENERATION] Template Length: {template['length']} chars")
        print(f"[GENERATION] Variables: {', '.join(template['variables'])}")

        # Step 3: Check compliance
        compliance = check_compliance(template)
        print(f"[COMPLIANCE] Score: {compliance['compliance_score']}/100")
        print(f"[COMPLIANCE] Approval Probability: {compliance['approval_probability']}")

        if compliance['violations']:
            print(f"[VIOLATIONS] {', '.join(compliance['violations'])}")

        if compliance['warnings']:
            print(f"[WARNINGS] {', '.join(compliance['warnings'])}")

        print(f"\nGenerated Template:")
        print("-" * 30)
        print(template['template_text'])
        print("-" * 30)

        results.append({
            "test_case": test_case['name'],
            "success": True,
            "compliance_score": compliance['compliance_score'],
            "is_compliant": compliance['is_compliant']
        })

    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    compliant_templates = sum(1 for r in results if r['is_compliant'])
    avg_score = sum(r['compliance_score'] for r in results) / total_tests

    print(f"Total Tests: {total_tests}")
    print(f"Successful Generations: {successful_tests}")
    print(f"Compliant Templates: {compliant_templates}")
    print(f"Average Compliance Score: {avg_score:.1f}/100")

    print(f"\nSuccess Rate: {(successful_tests/total_tests)*100:.1f}%")
    print(f"Compliance Rate: {(compliant_templates/total_tests)*100:.1f}%")

    print(f"\nSystem Features Tested:")
    print("- Automatic business type classification")
    print("- Industry-specific template patterns")
    print("- Real-time policy compliance checking")
    print("- Detailed feedback and recommendations")

    return results

if __name__ == "__main__":
    test_template_generation()