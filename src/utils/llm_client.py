"""
LLM Client for Claude API integration
"""
import os
import time
from typing import Dict, List, Any, Optional
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, SystemMessage
import logging
from .optimized_prompts import OptimizedPrompts
from .performance_cache import SpecificCaches

logger = logging.getLogger(__name__)

class ClaudeLLMClient:
    """Claude LLM client for template generation and analysis"""

    def __init__(
        self, api_key: Optional[str] = None, model: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided or set in environment")

        # .env에서 모델 설정 로드
        self.model = model or os.getenv("CLAUDE_MODEL", "claude-3-5-haiku-latest")
        temperature = float(os.getenv("CLAUDE_TEMPERATURE", "0.3"))
        max_tokens = int(os.getenv("CLAUDE_MAX_TOKENS", "2000"))

        self.llm = ChatAnthropic(
            anthropic_api_key=self.api_key,
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens
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
        """Analyze user request with caching and optimized prompts"""

        # 캐시 확인
        cached_result = SpecificCaches.get_request_analysis(user_request)
        if cached_result:
            logger.info("Using cached request analysis")
            return cached_result

        start_time = time.time()

        # 최적화된 프롬프트 사용
        system_prompt = OptimizedPrompts.get_request_analysis_prompt()
        user_prompt = f"요청: {user_request}"

        try:
            response = self.generate_response(system_prompt, user_prompt)
            # JSON 파싱 시도
            import json
            result = json.loads(response)

            # 캐시에 저장
            SpecificCaches.set_request_analysis(user_request, result)

            elapsed_time = time.time() - start_time
            logger.info(f"Request analysis completed in {elapsed_time:.2f}s (optimized)")

            return result
        except Exception as e:
            logger.error(f"Error parsing request analysis: {e}")
            # 파싱 실패 시 기본값 반환
            result = {
                "business_type": "기타",
                "service_type": "공지/안내",
                "message_purpose": "일반 안내",
                "target_audience": "고객",
                "required_variables": ["수신자명"],
                "tone": "정중한",
                "urgency": "보통",
                "estimated_category": "서비스이용"
            }

            # 기본값도 캐시에 저장
            SpecificCaches.set_request_analysis(user_request, result)
            return result

    def generate_template(self, request_info: Dict[str, Any], policy_context: str,
                         similar_templates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate KakaoTalk template with optimization and caching"""

        # 캐시 키 생성
        analysis_key = str(hash(str(request_info)))
        policy_key = str(hash(policy_context[:500]))  # 정책 컨텍스트 일부만 해시

        # 캐시 확인
        cached_result = SpecificCaches.get_template_generation(analysis_key, policy_key)
        if cached_result:
            logger.info("Using cached template generation")
            return cached_result

        start_time = time.time()

        # 정책 요약 생성
        policy_summary = self._summarize_policy(policy_context)

        # 최적화된 프롬프트 사용
        business_type = request_info.get('business_type', '기타')
        service_type = request_info.get('service_type', '안내')
        user_request = request_info.get('message_purpose', '일반 안내')

        system_prompt = OptimizedPrompts.get_template_generation_prompt(
            business_type, service_type, user_request, policy_summary
        )

        user_prompt = f"""대상: {request_info.get('target_audience', '고객')}
톤: {request_info.get('tone', '정중한')}
변수: {request_info.get('required_variables', ['수신자명'])}"""

        try:
            response = self.generate_response(system_prompt, user_prompt)
            import json
            result = json.loads(response)

            # 캐시에 저장
            SpecificCaches.set_template_generation(analysis_key, policy_key, result)

            elapsed_time = time.time() - start_time
            logger.info(f"Template generation completed in {elapsed_time:.2f}s (optimized)")

            return result
        except Exception as e:
            logger.error(f"Error generating template: {e}")
            result = {
                "template_text": "템플릿 생성에 실패했습니다.",
                "variables": [],
                "metadata": {},
                "compliance_score": 0
            }
            return result

    def check_compliance(self, template_text: str, policy_context: str) -> Dict[str, Any]:
        """Check template compliance with optimization"""

        start_time = time.time()

        # 최적화된 프롬프트 사용
        system_prompt = OptimizedPrompts.get_compliance_check_prompt(template_text)

        try:
            response = self.generate_response(system_prompt, "")
            import json
            result = json.loads(response)

            elapsed_time = time.time() - start_time
            logger.info(f"Compliance check completed in {elapsed_time:.2f}s (optimized)")

            return result
        except Exception as e:
            logger.error(f"Error checking compliance: {e}")
            return {
                "is_compliant": False,
                "compliance_score": 0,
                "violations": ["컴플라이언스 검사 실패"],
                "recommendations": ["수동 검토 필요"],
                "approval_probability": "낮음",
                "required_changes": []
            }

    def _summarize_policy(self, policy_context: str) -> str:
        """정책 컨텍스트를 요약"""
        if len(policy_context) <= 200:
            return policy_context

        # 간단한 요약 - 처음 200자 + 핵심 키워드
        summary = policy_context[:200]
        keywords = ["1000자", "정보성", "#{변수}", "광고금지"]
        return summary + " 핵심: " + ", ".join(keywords)

    def _format_templates_for_prompt(self, templates: List[Dict[str, Any]]) -> str:
        """템플릿을 프롬프트용으로 포맷"""
        if not templates:
            return "참고 템플릿 없음"

        formatted = []
        for i, template in enumerate(templates[:2]):  # 최대 2개만
            text = template.get('text', '')[:100]  # 100자로 제한
            formatted.append(f"{i+1}. {text}...")

        return "\n".join(formatted)


if __name__ == "__main__":
    # Test the LLM client
    client = ClaudeLLMClient()

    # Test request analysis
    test_request = "수강 신청 완료 후 강의 일정을 안내하는 메시지를 만들어주세요"
    analysis = client.analyze_user_request(test_request)
    print("Request Analysis:", analysis)
