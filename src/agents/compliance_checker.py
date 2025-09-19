"""
Compliance Checker Agent - 정책 준수 검증
"""
import logging
import re
from typing import Dict, Any, List, Tuple
from ..utils.llm_client import ClaudeLLMClient

logger = logging.getLogger(__name__)

class ComplianceCheckerAgent:
    """생성된 템플릿의 카카오 알림톡 정책 준수를 검증하는 에이전트"""

    def __init__(self, llm_client: ClaudeLLMClient):
        self.llm_client = llm_client
        self.black_list_patterns = self._load_blacklist_patterns()
        self.required_patterns = self._load_required_patterns()

    def check_compliance(self, template: Dict[str, Any],
                        policy_context: str) -> Dict[str, Any]:
        """
        템플릿의 정책 준수 여부를 종합적으로 검증

        Args:
            template: 검증할 템플릿 정보
            policy_context: 관련 정책 컨텍스트

        Returns:
            검증 결과 및 개선사항
        """
        logger.info("Starting compliance check for template")

        template_text = template.get('template_text', '')
        if not template_text:
            return self._get_failed_result("템플릿 텍스트가 없습니다.")

        try:
            # 1. 기본 규칙 검증
            basic_check = self._check_basic_rules(template_text, template)

            # 2. 블랙리스트 검증
            blacklist_check = self._check_blacklist_violations(template_text)

            # 3. 변수 사용 규칙 검증
            variable_check = self._check_variable_usage(template_text, template)

            # 4. LLM 기반 심화 검증
            llm_check = self.llm_client.check_compliance(template_text, policy_context)

            # 5. 종합 평가
            final_result = self._combine_results(
                basic_check, blacklist_check, variable_check, llm_check, template
            )

            logger.info(f"Compliance check completed. Score: {final_result.get('compliance_score', 0)}")
            return final_result

        except Exception as e:
            logger.error(f"Error in compliance check: {e}")
            return self._get_failed_result(f"검증 중 오류 발생: {str(e)}")

    def _check_basic_rules(self, template_text: str, template: Dict[str, Any]) -> Dict[str, Any]:
        """기본 규칙 검증"""

        violations = []
        warnings = []
        score = 100

        # 1. 길이 검증 (1000자 제한)
        if len(template_text) > 1000:
            violations.append(f"메시지 길이 초과 ({len(template_text)}/1000자)")
            score -= 20

        # 2. 인사말 확인
        if not self._has_greeting(template_text):
            warnings.append("인사말이 포함되지 않았습니다")
            score -= 5

        # 3. 정보성 메시지 표시 확인
        if not self._has_info_indication(template_text):
            violations.append("정보성 메시지 표시가 없습니다")
            score -= 15

        # 4. 광고성 키워드 검증
        ad_keywords = self._find_advertising_keywords(template_text)
        if ad_keywords:
            violations.append(f"광고성 키워드 발견: {', '.join(ad_keywords)}")
            score -= 25

        # 5. 연락처 정보 검증
        contact_violations = self._check_contact_info(template_text)
        if contact_violations:
            violations.extend(contact_violations)
            score -= 10

        return {
            'category': 'basic_rules',
            'score': max(0, score),
            'violations': violations,
            'warnings': warnings
        }

    def _check_blacklist_violations(self, template_text: str) -> Dict[str, Any]:
        """블랙리스트 위반 검증"""

        violations = []
        score = 100

        for pattern_name, patterns in self.black_list_patterns.items():
            for pattern in patterns:
                if re.search(pattern, template_text, re.IGNORECASE):
                    violations.append(f"블랙리스트 위반: {pattern_name}")
                    score -= 30  # 블랙리스트 위반은 심각한 문제

        return {
            'category': 'blacklist',
            'score': max(0, score),
            'violations': violations,
            'warnings': []
        }

    def _check_variable_usage(self, template_text: str, template: Dict[str, Any]) -> Dict[str, Any]:
        """변수 사용 규칙 검증"""

        violations = []
        warnings = []
        score = 100

        # 변수 추출
        variables = re.findall(r'#\{([^}]+)\}', template_text)

        # 1. 변수 개수 제한 (40개 초과 금지)
        if len(variables) > 40:
            violations.append(f"변수 개수 초과 ({len(variables)}/40개)")
            score -= 25

        # 2. 변수만으로 구성된 내용 금지
        text_without_variables = re.sub(r'#\{[^}]+\}', '', template_text)
        if len(text_without_variables.strip()) < 10:
            violations.append("변수만으로 구성된 템플릿입니다")
            score -= 30

        # 3. 변수 형식 검증
        invalid_variables = []
        for var in variables:
            if not self._is_valid_variable_name(var):
                invalid_variables.append(var)

        if invalid_variables:
            violations.append(f"잘못된 변수명: {', '.join(invalid_variables)}")
            score -= 10

        # 4. 버튼명에 변수 사용 금지
        button_suggestion = template.get('button_suggestion', '')
        if button_suggestion and '#{' in button_suggestion:
            violations.append("버튼명에 변수 사용 금지")
            score -= 15

        return {
            'category': 'variables',
            'score': max(0, score),
            'violations': violations,
            'warnings': warnings
        }

    def _combine_results(self, basic_check: Dict[str, Any], blacklist_check: Dict[str, Any],
                        variable_check: Dict[str, Any], llm_check: Dict[str, Any],
                        template: Dict[str, Any]) -> Dict[str, Any]:
        """검증 결과 종합"""

        # 점수 계산 (가중평균)
        weights = {
            'basic': 0.3,
            'blacklist': 0.4,  # 블랙리스트가 가장 중요
            'variables': 0.2,
            'llm': 0.1
        }

        total_score = (
            basic_check['score'] * weights['basic'] +
            blacklist_check['score'] * weights['blacklist'] +
            variable_check['score'] * weights['variables'] +
            llm_check.get('compliance_score', 80) * weights['llm']
        )

        # 위반사항 종합
        all_violations = (
            basic_check['violations'] +
            blacklist_check['violations'] +
            variable_check['violations'] +
            llm_check.get('violations', [])
        )

        # 경고사항 종합
        all_warnings = (
            basic_check['warnings'] +
            variable_check['warnings']
        )

        # 개선사항 생성
        recommendations = self._generate_recommendations(
            all_violations, all_warnings, template
        )

        # 승인 가능성 평가
        approval_probability = self._assess_approval_probability(total_score, all_violations)

        # 필수 수정사항
        required_changes = [v for v in all_violations if self._is_critical_violation(v)]

        return {
            'is_compliant': len(required_changes) == 0 and total_score >= 80,
            'compliance_score': round(total_score, 1),
            'violations': all_violations,
            'warnings': all_warnings,
            'recommendations': recommendations,
            'approval_probability': approval_probability,
            'required_changes': required_changes,
            'detailed_scores': {
                'basic_rules': basic_check['score'],
                'blacklist_check': blacklist_check['score'],
                'variable_usage': variable_check['score'],
                'llm_analysis': llm_check.get('compliance_score', 80)
            }
        }

    def _load_blacklist_patterns(self) -> Dict[str, List[str]]:
        """블랙리스트 패턴 로드"""

        return {
            '무료_서비스': [
                r'무료.*뉴스레터',
                r'무료.*구독',
                r'무료.*멤버십'
            ],
            '포인트_적립': [
                r'포인트.*적립(?!.*동의)',
                r'적립금.*지급(?!.*동의)',
                r'마일리지.*적립(?!.*동의)'
            ],
            '쿠폰_발급': [
                r'쿠폰.*발급.*소멸',
                r'빠른.*소멸.*쿠폰',
                r'한정.*쿠폰'
            ],
            '광고성_내용': [
                r'할인.*이벤트',
                r'특가.*행사',
                r'프로모션.*혜택'
            ],
            '스팸_패턴': [
                r'지금.*클릭',
                r'놓치지.*마세요',
                r'단.*\d+일'
            ]
        }

    def _load_required_patterns(self) -> Dict[str, List[str]]:
        """필수 포함 패턴"""

        return {
            '정보성_표시': [
                r'정보성.*메시지',
                r'안내.*메시지',
                r'발송.*메시지',
                r'신청.*분들께',
                r'요청.*분들께'
            ],
            '인사말': [
                r'안녕하세요',
                r'안녕하십니까',
                r'반갑습니다'
            ]
        }

    def _has_greeting(self, text: str) -> bool:
        """인사말 포함 여부"""
        greetings = ['안녕하세요', '안녕하십니까', '반갑습니다']
        return any(greeting in text for greeting in greetings)

    def _has_info_indication(self, text: str) -> bool:
        """정보성 메시지 표시 여부"""
        patterns = self.required_patterns.get('정보성_표시', [])
        return any(re.search(pattern, text) for pattern in patterns)

    def _find_advertising_keywords(self, text: str) -> List[str]:
        """광고성 키워드 찾기"""
        ad_keywords = [
            '할인', '특가', '이벤트', '프로모션', '혜택', '무료',
            '선착순', '한정', '특별', '기회', '놓치지'
        ]

        found_keywords = []
        for keyword in ad_keywords:
            if keyword in text:
                found_keywords.append(keyword)

        return found_keywords

    def _check_contact_info(self, text: str) -> List[str]:
        """연락처 정보 검증"""
        violations = []

        # 전화번호 패턴 (과도한 연락처 정보 금지)
        phone_patterns = [
            r'\d{2,3}-\d{3,4}-\d{4}',
            r'\d{10,11}',
            r'1\d{3}-\d{4}'
        ]

        phone_count = 0
        for pattern in phone_patterns:
            phone_count += len(re.findall(pattern, text))

        if phone_count > 2:
            violations.append("과도한 연락처 정보 포함")

        return violations

    def _is_valid_variable_name(self, var_name: str) -> bool:
        """변수명 유효성 검증"""
        # 한글, 영문, 숫자, 특정 기호만 허용
        pattern = r'^[가-힣a-zA-Z0-9_\s]+$'
        return bool(re.match(pattern, var_name)) and len(var_name) <= 20

    def _generate_recommendations(self, violations: List[str], warnings: List[str],
                                template: Dict[str, Any]) -> List[str]:
        """개선사항 생성"""
        recommendations = []

        # 위반사항 기반 권장사항
        for violation in violations:
            if '광고성' in violation:
                recommendations.append("광고성 표현을 제거하고 순수 정보성 내용으로 수정하세요")
            elif '길이 초과' in violation:
                recommendations.append("메시지 길이를 1000자 이내로 줄이세요")
            elif '변수' in violation:
                recommendations.append("변수 사용 규칙을 확인하고 수정하세요")
            elif '정보성 메시지' in violation:
                recommendations.append("메시지 하단에 정보성 메시지 표시를 추가하세요")

        # 경고사항 기반 권장사항
        for warning in warnings:
            if '인사말' in warning:
                recommendations.append("메시지 시작에 적절한 인사말을 추가하세요")

        # 중복 제거
        return list(set(recommendations))

    def _assess_approval_probability(self, score: float, violations: List[str]) -> str:
        """승인 가능성 평가"""
        critical_violations = [v for v in violations if self._is_critical_violation(v)]

        if critical_violations:
            return "낮음"
        elif score >= 90:
            return "높음"
        elif score >= 75:
            return "보통"
        else:
            return "낮음"

    def _is_critical_violation(self, violation: str) -> bool:
        """심각한 위반 여부 판단"""
        critical_keywords = [
            '블랙리스트', '광고성', '변수만으로', '길이 초과'
        ]
        return any(keyword in violation for keyword in critical_keywords)

    def _get_failed_result(self, error_message: str) -> Dict[str, Any]:
        """검증 실패 시 기본 결과"""
        return {
            'is_compliant': False,
            'compliance_score': 0,
            'violations': [error_message],
            'warnings': [],
            'recommendations': ['전문가 검토 필요'],
            'approval_probability': '낮음',
            'required_changes': [error_message],
            'detailed_scores': {
                'basic_rules': 0,
                'blacklist_check': 0,
                'variable_usage': 0,
                'llm_analysis': 0
            }
        }

    def get_compliance_report(self, result: Dict[str, Any]) -> str:
        """컴플라이언스 검증 보고서 생성"""

        report = f"""
## 카카오 알림톡 정책 준수 검증 결과

### 종합 평가
- **준수 여부**: {'✅ 준수' if result['is_compliant'] else '❌ 위반'}
- **준수 점수**: {result['compliance_score']}/100점
- **승인 가능성**: {result['approval_probability']}

### 세부 점수
- 기본 규칙: {result['detailed_scores']['basic_rules']}/100점
- 블랙리스트 검증: {result['detailed_scores']['blacklist_check']}/100점
- 변수 사용: {result['detailed_scores']['variable_usage']}/100점
- AI 분석: {result['detailed_scores']['llm_analysis']}/100점

### 위반사항 ({len(result['violations'])}건)
"""

        for i, violation in enumerate(result['violations'], 1):
            report += f"{i}. {violation}\n"

        if result['warnings']:
            report += f"\n### 경고사항 ({len(result['warnings'])}건)\n"
            for i, warning in enumerate(result['warnings'], 1):
                report += f"{i}. {warning}\n"

        if result['recommendations']:
            report += f"\n### 개선 권장사항\n"
            for i, rec in enumerate(result['recommendations'], 1):
                report += f"{i}. {rec}\n"

        if result['required_changes']:
            report += f"\n### 필수 수정사항\n"
            for i, change in enumerate(result['required_changes'], 1):
                report += f"{i}. {change}\n"

        return report


if __name__ == "__main__":
    # Test the compliance checker
    from ..utils.llm_client import ClaudeLLMClient

    llm_client = ClaudeLLMClient()
    checker = ComplianceCheckerAgent(llm_client)

    # Test template
    test_template = {
        'template_text': '안녕하세요 #{수신자명}님, 강의 신청이 완료되었습니다. 일정: #{일정}',
        'variables': ['수신자명', '일정'],
        'button_suggestion': '강의 보기'
    }

    policy_context = "알림톡은 정보성 메시지여야 합니다."

    result = checker.check_compliance(test_template, policy_context)
    print(checker.get_compliance_report(result))