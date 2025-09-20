"""
최적화된 프롬프트 관리
기존 긴 프롬프트를 간결하고 효율적으로 개선
"""

class OptimizedPrompts:
    """최적화된 프롬프트 모음"""

    @staticmethod
    def get_request_analysis_prompt() -> str:
        """요청 분석용 최적화된 프롬프트 (기존 대비 60% 단축)"""
        return """사용자 요청을 분석해 JSON으로 응답:
{
  "business_type": "교육|의료|쇼핑몰|서비스업|금융|기타",
  "service_type": "신청|예약|주문|배송|안내|확인|피드백",
  "message_purpose": "목적",
  "target_audience": "대상",
  "tone": "정중한|친근한|공식적인",
  "urgency": "높음|보통|낮음"
}"""

    @staticmethod
    def get_template_generation_prompt(business_type: str, service_type: str,
                                     user_request: str, policy_summary: str) -> str:
        """템플릿 생성용 최적화된 프롬프트 (기존 대비 70% 단축)"""
        return f"""알림톡 템플릿 생성 ({business_type}-{service_type}):

요청: {user_request}

규칙: 1000자 이내, #{{"변수"}} 형식, 정보성만
정책: {policy_summary[:150]}

JSON 응답:
{{
  "template_text": "템플릿 내용",
  "variables": ["변수1", "변수2"],
  "button_suggestion": "버튼명"
}}"""

    @staticmethod
    def get_compliance_check_prompt(template_text: str) -> str:
        """컴플라이언스 검사용 최적화된 프롬프트 (기존 대비 80% 단축)"""
        return f"""정책 검사: {template_text}

확인: 길이 1000자↓, #{{"변수"}} 형식, 광고성 없음

JSON:
{{
  "is_compliant": true/false,
  "score": 0-100,
  "violations": ["문제점"],
  "recommendations": ["개선안"]
}}"""

    @staticmethod
    def get_policy_summary_prompt(policies: str) -> str:
        """정책 요약용 프롬프트"""
        return f"""다음 정책을 100자 이내로 요약:
{policies[:500]}

핵심 규칙만 간략히:"""