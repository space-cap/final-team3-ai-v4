"""
Template Generator Agent - 정책 준수 템플릿 생성
"""
import logging
from typing import Dict, Any, List
from ..utils.llm_client import ClaudeLLMClient
from ..database.vector_store import TemplateStore

logger = logging.getLogger(__name__)

class TemplateGeneratorAgent:
    """정책에 부합하는 알림톡 템플릿을 생성하는 에이전트"""

    def __init__(self, llm_client: ClaudeLLMClient, template_store: TemplateStore):
        self.llm_client = llm_client
        self.template_store = template_store

    def generate_template(self, request_analysis: Dict[str, Any],
                         policy_context: str) -> Dict[str, Any]:
        """
        분석된 요청과 정책 컨텍스트를 바탕으로 템플릿 생성

        Args:
            request_analysis: RequestAnalyzerAgent의 분석 결과
            policy_context: PolicyRAGSystem에서 검색된 관련 정책

        Returns:
            생성된 템플릿과 메타데이터
        """
        logger.info("Generating template based on analysis and policies")

        try:
            # 유사 템플릿 검색
            similar_templates = self._find_similar_templates(request_analysis)

            # 템플릿 생성
            generated_template = self.llm_client.generate_template(
                request_analysis, policy_context, similar_templates
            )

            # 템플릿 후처리 및 검증
            processed_template = self._post_process_template(
                generated_template, request_analysis
            )

            logger.info("Template generation completed successfully")
            return processed_template

        except Exception as e:
            logger.error(f"Error generating template: {e}")
            return self._get_fallback_template(request_analysis)

    def _find_similar_templates(self, request_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """유사한 승인된 템플릿 검색"""

        business_type = request_analysis.get('business_type', '기타')
        service_type = request_analysis.get('service_type', '안내')

        # 1. 정확한 매칭 시도
        exact_matches = self.template_store.find_similar_templates(
            business_type, service_type, k=3
        )

        if len(exact_matches) >= 2:
            return exact_matches

        # 2. 비즈니스 타입으로 확장 검색
        business_matches = self.template_store.get_templates_by_business_type(
            business_type
        )[:3]

        if len(business_matches) >= 2:
            return business_matches

        # 3. 카테고리 기반 검색
        estimated_category = request_analysis.get('estimated_category', {})
        category_1 = estimated_category.get('category_1', '')
        category_2 = estimated_category.get('category_2', '')

        category_matches = self.template_store.get_templates_by_category(
            category_1, category_2
        )[:3]

        if category_matches:
            return category_matches

        # 4. 최후 수단: 모든 승인된 템플릿에서 무작위 선택
        approved_templates = self.template_store.get_approved_templates()
        return approved_templates[:3] if approved_templates else []

    def _post_process_template(self, generated_template: Dict[str, Any],
                              request_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """생성된 템플릿 후처리"""

        # 기본 검증
        template_text = generated_template.get('template_text', '')
        if not template_text:
            return self._get_fallback_template(request_analysis)

        # 변수 형식 검증 및 수정
        template_text = self._fix_variable_format(template_text)

        # 길이 검증
        if len(template_text) > 1000:
            template_text = self._truncate_template(template_text)

        # 필수 요소 검증
        template_text = self._ensure_required_elements(template_text, request_analysis)

        # 메타데이터 보완
        metadata = self._enhance_metadata(
            generated_template.get('metadata', {}), request_analysis
        )

        return {
            'template_text': template_text,
            'variables': self._extract_variables_from_text(template_text),
            'metadata': metadata,
            'button_suggestion': generated_template.get('button_suggestion', ''),
            'compliance_score': generated_template.get('compliance_score', 85),
            'generation_notes': self._generate_notes(request_analysis)
        }

    def _fix_variable_format(self, template_text: str) -> str:
        """변수 형식을 #{변수명} 형태로 통일"""
        import re

        # ${변수명}, {변수명} 등을 #{변수명}으로 변환
        template_text = re.sub(r'\$\{([^}]+)\}', r'#{\1}', template_text)
        template_text = re.sub(r'(?<![#$])\{([^}]+)\}', r'#{\1}', template_text)

        return template_text

    def _truncate_template(self, template_text: str, max_length: int = 1000) -> str:
        """템플릿 길이 조정"""
        if len(template_text) <= max_length:
            return template_text

        # 문장 단위로 자르기
        sentences = template_text.split('.')
        truncated = ""

        for sentence in sentences:
            if len(truncated + sentence + '.') <= max_length - 50:  # 여유분 확보
                truncated += sentence + '.'
            else:
                break

        # 마지막에 적절한 마무리 추가
        if not truncated.endswith('.'):
            truncated += '.'

        return truncated.strip()

    def _ensure_required_elements(self, template_text: str,
                                 request_analysis: Dict[str, Any]) -> str:
        """필수 요소 확인 및 추가"""

        # 인사말 확인
        if not self._has_greeting(template_text):
            greeting = self._get_appropriate_greeting(request_analysis)
            template_text = greeting + " " + template_text

        # 정보성 메시지 표시 추가 (필요한 경우)
        if not self._has_info_notice(template_text):
            info_notice = self._get_info_notice(request_analysis)
            if info_notice:
                template_text += "\n\n" + info_notice

        return template_text

    def _has_greeting(self, template_text: str) -> bool:
        """인사말 포함 여부 확인"""
        greetings = ['안녕하세요', '안녕하십니까', '반갑습니다']
        return any(greeting in template_text for greeting in greetings)

    def _get_appropriate_greeting(self, request_analysis: Dict[str, Any]) -> str:
        """적절한 인사말 생성"""
        tone = request_analysis.get('tone', '정중한')

        if tone == '친근한':
            return "안녕하세요"
        elif tone == '공식적인':
            return "안녕하십니까"
        else:
            return "안녕하세요"

    def _has_info_notice(self, template_text: str) -> bool:
        """정보성 메시지 표시 확인"""
        info_patterns = [
            "정보성 메시지", "안내 메시지", "발송되는 메시지",
            "요청하신 분들께", "신청하신 분들께"
        ]
        return any(pattern in template_text for pattern in info_patterns)

    def _get_info_notice(self, request_analysis: Dict[str, Any]) -> str:
        """정보성 메시지 표시 생성"""
        service_type = request_analysis.get('service_type', '안내')

        notices = {
            '신청': "※ 이 메시지는 서비스를 신청하신 분들께 발송되는 정보성 안내입니다.",
            '예약': "※ 이 메시지는 예약을 하신 분들께 발송되는 정보성 안내입니다.",
            '주문': "※ 이 메시지는 주문을 하신 분들께 발송되는 정보성 안내입니다.",
            '안내': "※ 이 메시지는 서비스 이용 관련 정보성 안내입니다."
        }

        return notices.get(service_type, notices['안내'])

    def _extract_variables_from_text(self, template_text: str) -> List[str]:
        """템플릿 텍스트에서 변수 추출"""
        import re

        # #{변수명} 패턴 찾기
        variables = re.findall(r'#\{([^}]+)\}', template_text)
        return list(set(variables))  # 중복 제거

    def _enhance_metadata(self, metadata: Dict[str, Any],
                         request_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """메타데이터 보완"""

        enhanced_metadata = metadata.copy()

        # 분석 결과로 보완
        enhanced_metadata.update({
            'business_type': request_analysis.get('business_type', '기타'),
            'service_type': request_analysis.get('service_type', '안내'),
            'target_audience': request_analysis.get('target_audience', '고객'),
            'urgency': request_analysis.get('urgency', '보통'),
            'generation_timestamp': self._get_timestamp(),
            'generation_method': 'ai_generated'
        })

        # 카테고리 정보
        estimated_category = request_analysis.get('estimated_category', {})
        enhanced_metadata.update({
            'category_1': estimated_category.get('category_1', '서비스이용'),
            'category_2': estimated_category.get('category_2', '이용안내/공지')
        })

        return enhanced_metadata

    def _generate_notes(self, request_analysis: Dict[str, Any]) -> List[str]:
        """생성 노트 작성"""

        notes = []

        # 컴플라이언스 우려사항
        concerns = request_analysis.get('compliance_concerns', [])
        if concerns:
            notes.append(f"주의사항: {', '.join(concerns)}")

        # 생성 기준
        notes.append(f"기준: {request_analysis.get('business_type')} 업종, {request_analysis.get('service_type')} 유형")

        # 변수 안내
        variables = request_analysis.get('required_variables', [])
        if variables:
            notes.append(f"필요 변수: {', '.join(variables)}")

        return notes

    def _get_timestamp(self) -> str:
        """현재 시간 반환"""
        from datetime import datetime
        return datetime.now().isoformat()

    def _get_fallback_template(self, request_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """생성 실패 시 기본 템플릿"""

        fallback_text = f"""안녕하세요 #{{수신자명}}님,

요청하신 {request_analysis.get('service_type', '서비스')} 관련 안내드립니다.

자세한 내용은 아래 버튼을 통해 확인하실 수 있습니다.

※ 이 메시지는 서비스 이용 관련 정보성 안내입니다."""

        return {
            'template_text': fallback_text,
            'variables': ['수신자명'],
            'metadata': {
                'category_1': '서비스이용',
                'category_2': '이용안내/공지',
                'business_type': request_analysis.get('business_type', '기타'),
                'generation_method': 'fallback'
            },
            'button_suggestion': '자세히 보기',
            'compliance_score': 75,
            'generation_notes': ['기본 템플릿 사용 (생성 실패로 인함)']
        }

    def optimize_template(self, template: Dict[str, Any],
                         optimization_goals: List[str] = None) -> Dict[str, Any]:
        """템플릿 최적화"""

        if not optimization_goals:
            optimization_goals = ['compliance', 'readability', 'length']

        optimized = template.copy()

        for goal in optimization_goals:
            if goal == 'compliance':
                optimized = self._optimize_for_compliance(optimized)
            elif goal == 'readability':
                optimized = self._optimize_for_readability(optimized)
            elif goal == 'length':
                optimized = self._optimize_for_length(optimized)

        return optimized

    def _optimize_for_compliance(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """컴플라이언스 최적화"""
        # 추가 컴플라이언스 규칙 적용
        template_text = template.get('template_text', '')

        # 광고성 표현 제거
        ad_words = ['할인', '특가', '이벤트', '혜택']
        for word in ad_words:
            if word in template_text:
                template_text = template_text.replace(word, '안내')

        template['template_text'] = template_text
        return template

    def _optimize_for_readability(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """가독성 최적화"""
        # 문장 구조 개선, 띄어쓰기 정리 등
        template_text = template.get('template_text', '')

        # 기본적인 정리
        template_text = template_text.replace('  ', ' ')  # 이중 공백 제거
        template_text = template_text.replace('\n\n\n', '\n\n')  # 과도한 줄바꿈 제거

        template['template_text'] = template_text
        return template

    def _optimize_for_length(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """길이 최적화"""
        template_text = template.get('template_text', '')

        if len(template_text) > 800:  # 800자 초과 시 축약
            template_text = self._truncate_template(template_text, 800)

        template['template_text'] = template_text
        return template


if __name__ == "__main__":
    # Test the template generator
    from ..utils.llm_client import ClaudeLLMClient
    from ..database.vector_store import TemplateStore

    llm_client = ClaudeLLMClient()
    template_store = TemplateStore()
    generator = TemplateGeneratorAgent(llm_client, template_store)

    # Mock request analysis
    test_analysis = {
        'business_type': '교육',
        'service_type': '신청',
        'message_purpose': '강의 신청 확인',
        'required_variables': ['수신자명', '강의명', '일정'],
        'tone': '정중한'
    }

    # Mock policy context
    policy_context = "알림톡은 정보성 메시지여야 하며 광고성 내용을 포함할 수 없습니다."

    result = generator.generate_template(test_analysis, policy_context)
    print("Generated Template:")
    print(result['template_text'])