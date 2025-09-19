"""
LLM Client for Claude API integration
"""
import os
from typing import Dict, List, Any, Optional
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, SystemMessage
import logging

logger = logging.getLogger(__name__)

class ClaudeLLMClient:
    """Claude LLM client for template generation and analysis"""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided or set in environment")

        self.model = model
        self.llm = ChatAnthropic(
            anthropic_api_key=self.api_key,
            model=self.model,
            temperature=0.7,
            max_tokens=2000
        )

    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        """Generate response using Claude"""
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = self.llm.invoke(messages)
            return response.content

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return ""

    def analyze_user_request(self, user_request: str) -> Dict[str, Any]:
        """Analyze user request and extract structured information"""
        system_prompt = """
당신은 카카오 알림톡 템플릿 요구사항 분석 전문가입니다.
사용자의 요청을 분석하여 다음 정보를 JSON 형태로 추출해주세요:

- business_type: 비즈니스 유형 (교육, 서비스업, 기타 등)
- service_type: 서비스 유형 (공지/안내, 신청, 피드백 등)
- message_purpose: 메시지 목적 (회원가입, 주문확인, 배송안내 등)
- target_audience: 대상 고객층
- required_variables: 필요한 변수들 (#{변수명} 형태)
- tone: 톤앤매너 (정중한, 친근한, 공식적인 등)
- urgency: 긴급도 (높음, 보통, 낮음)
- estimated_category: 예상 카테고리

응답은 반드시 유효한 JSON 형태로만 제공해주세요.
"""

        user_prompt = f"다음 사용자 요청을 분석해주세요:\n\n{user_request}"

        try:
            response = self.generate_response(system_prompt, user_prompt)
            # JSON 파싱 시도
            import json
            return json.loads(response)
        except:
            # 파싱 실패 시 기본값 반환
            return {
                "business_type": "기타",
                "service_type": "공지/안내",
                "message_purpose": "일반 안내",
                "target_audience": "고객",
                "required_variables": ["수신자명"],
                "tone": "정중한",
                "urgency": "보통",
                "estimated_category": "서비스이용"
            }

    def generate_template(self, request_info: Dict[str, Any], policy_context: str,
                         similar_templates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate KakaoTalk template based on analysis and context"""

        system_prompt = f"""
당신은 카카오 알림톡 템플릿 생성 전문가입니다.
주어진 정보를 바탕으로 카카오 정책에 완벽히 부합하는 알림톡 템플릿을 생성해주세요.

**정책 컨텍스트:**
{policy_context}

**참고할 승인된 템플릿들:**
{self._format_templates_for_prompt(similar_templates)}

**생성 규칙:**
1. 반드시 정보성 메시지여야 함
2. 광고성 내용 금지
3. 변수는 #{{변수명}} 형태로 사용
4. 메시지는 1000자 이내
5. 정중한 톤 유지
6. 필수 정보만 포함
7. 버튼 사용 시 명확한 설명 포함

응답 형태:
{{
  "template_text": "생성된 템플릿 내용",
  "variables": ["변수1", "변수2"],
  "metadata": {{
    "category_1": "분류1",
    "category_2": "분류2",
    "business_type": "비즈니스 유형",
    "service_type": "서비스 유형",
    "estimated_length": 템플릿 길이,
    "compliance_notes": "준수 사항 설명"
  }},
  "button_suggestion": "제안 버튼명 (선택사항)",
  "compliance_score": 95
}}
"""

        user_prompt = f"""
다음 요구사항에 맞는 알림톡 템플릿을 생성해주세요:

**요구사항:**
- 비즈니스 유형: {request_info.get('business_type', '기타')}
- 서비스 유형: {request_info.get('service_type', '공지/안내')}
- 메시지 목적: {request_info.get('message_purpose', '일반 안내')}
- 대상 고객: {request_info.get('target_audience', '고객')}
- 필요 변수: {request_info.get('required_variables', ['수신자명'])}
- 톤앤매너: {request_info.get('tone', '정중한')}

사용자 원본 요청: {request_info.get('original_request', '')}
"""

        try:
            response = self.generate_response(system_prompt, user_prompt)
            import json
            return json.loads(response)
        except:
            return {
                "template_text": "템플릿 생성에 실패했습니다.",
                "variables": [],
                "metadata": {},
                "compliance_score": 0
            }

    def check_compliance(self, template_text: str, policy_context: str) -> Dict[str, Any]:
        """Check template compliance against policies"""

        system_prompt = f"""
당신은 카카오 알림톡 정책 준수 검증 전문가입니다.
주어진 템플릿이 카카오 정책을 준수하는지 철저히 검증해주세요.

**정책 기준:**
{policy_context}

검증 항목:
1. 정보성 메시지 여부
2. 광고성 내용 포함 여부
3. 블랙리스트 위반 여부
4. 변수 사용 규칙 준수
5. 메시지 길이 적절성
6. 필수 안내사항 포함 여부

응답 형태:
{{
  "is_compliant": true/false,
  "compliance_score": 0-100,
  "violations": ["위반사항1", "위반사항2"],
  "recommendations": ["개선사항1", "개선사항2"],
  "approval_probability": "높음/보통/낮음",
  "required_changes": ["필수 수정사항1", "필수 수정사항2"]
}}
"""

        user_prompt = f"다음 템플릿을 검증해주세요:\n\n{template_text}"

        try:
            response = self.generate_response(system_prompt, user_prompt)
            import json
            return json.loads(response)
        except:
            return {
                "is_compliant": False,
                "compliance_score": 0,
                "violations": ["검증 실패"],
                "recommendations": ["전문가 검토 필요"],
                "approval_probability": "낮음",
                "required_changes": ["수동 검토 필요"]
            }

    def _format_templates_for_prompt(self, templates: List[Dict[str, Any]]) -> str:
        """Format templates for prompt context"""
        if not templates:
            return "참고할 템플릿이 없습니다."

        formatted = []
        for i, template in enumerate(templates[:3]):  # 최대 3개만
            formatted.append(f"""
템플릿 {i+1}:
내용: {template.get('text', '')}
카테고리: {template.get('metadata', {}).get('category_1', '')} > {template.get('metadata', {}).get('category_2', '')}
비즈니스 유형: {template.get('metadata', {}).get('business_type', '')}
""")

        return "\n".join(formatted)


if __name__ == "__main__":
    # Test the LLM client
    client = ClaudeLLMClient()

    # Test request analysis
    test_request = "수강 신청 완료 후 강의 일정을 안내하는 메시지를 만들어주세요"
    analysis = client.analyze_user_request(test_request)
    print("Request Analysis:", analysis)