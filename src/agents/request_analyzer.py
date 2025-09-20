"""
Request Analyzer Agent - 사용자 요청 분석 및 분류
"""
import logging
from typing import Dict, Any, List
from ..utils.llm_client import ClaudeLLMClient

logger = logging.getLogger(__name__)

class RequestAnalyzerAgent:
    """사용자 요청을 분석하고 구조화된 정보로 변환하는 에이전트"""

    def __init__(self, llm_client: ClaudeLLMClient):
        self.llm_client = llm_client

    def analyze_request(self, user_request: str) -> Dict[str, Any]:
        """
        사용자 요청을 분석하여 구조화된 정보 추출

        Args:
            user_request: 사용자의 원본 요청

        Returns:
            분석된 구조화된 정보
        """
        logger.info(f"Analyzing user request: {user_request[:100]}...")

        try:
            # LLM을 통한 기본 분석
            analysis = self.llm_client.analyze_user_request(user_request)

            # 추가 분석 및 검증
            enhanced_analysis = self._enhance_analysis(analysis, user_request)

            # 비즈니스 규칙 적용
            final_analysis = self._apply_business_rules(enhanced_analysis)

            logger.info("Request analysis completed successfully")
            return final_analysis

        except Exception as e:
            logger.error(f"Error analyzing request: {e}")
            return self._get_default_analysis(user_request)

    def _enhance_analysis(self, base_analysis: Dict[str, Any], user_request: str) -> Dict[str, Any]:
        """기본 분석 결과를 향상시킴"""

        enhanced = base_analysis.copy()
        enhanced['original_request'] = user_request

        # 키워드 기반 분류 보완
        enhanced = self._classify_by_keywords(enhanced, user_request)

        # 변수 추출 보완
        enhanced = self._extract_variables(enhanced, user_request)

        # 우선순위 설정
        enhanced = self._set_priority(enhanced)

        return enhanced

    def _classify_by_keywords(self, analysis: Dict[str, Any], user_request: str) -> Dict[str, Any]:
        """키워드 기반으로 분류 보완"""

        # 비즈니스 유형 키워드 매핑
        business_keywords = {
            '교육': ['강의', '수강', '교육', '학습', '코스', '강좌', '교실', '학원'],
            '의료': ['병원', '진료', '예약', '치료', '의료', '건강', '상담'],
            '음식점': ['주문', '배달', '음식', '식당', '메뉴', '예약'],
            '쇼핑몰': ['구매', '주문', '배송', '상품', '결제', '쇼핑'],
            '서비스업': ['예약', '상담', '서비스', '이용', '문의'],
            '금융': ['결제', '송금', '계좌', '카드', '대출', '보험']
        }

        # 서비스 유형 키워드 매핑
        service_keywords = {
            '신청': ['신청', '등록', '가입', '접수'],
            '예약': ['예약', '예정', '일정'],
            '주문': ['주문', '구매', '결제'],
            '배송': ['배송', '발송', '택배', '출고'],
            '안내': ['안내', '공지', '알림', '정보'],
            '확인': ['확인', '승인', '완료'],
            '피드백': ['후기', '평가', '리뷰', '만족도']
        }

        # 키워드 기반 분류
        for business_type, keywords in business_keywords.items():
            if any(keyword in user_request for keyword in keywords):
                analysis['business_type'] = business_type
                break

        for service_type, keywords in service_keywords.items():
            if any(keyword in user_request for keyword in keywords):
                analysis['service_type'] = service_type
                break

        return analysis

    def _extract_variables(self, analysis: Dict[str, Any], user_request: str) -> Dict[str, Any]:
        """필요한 변수들을 추출"""

        # 기본 변수
        variables = ['수신자명']

        # 컨텍스트 기반 변수 추가
        variable_patterns = {
            '날짜': ['일정', '날짜', '시간', '예약'],
            '금액': ['금액', '가격', '비용', '요금'],
            '상품명': ['상품', '제품', '서비스명'],
            '주소': ['주소', '위치', '장소'],
            '연락처': ['전화', '연락처', '번호'],
            '코드': ['코드', '번호', '인증']
        }

        for var_name, keywords in variable_patterns.items():
            if any(keyword in user_request for keyword in keywords):
                variables.append(var_name)

        # 중복 제거
        analysis['required_variables'] = list(set(variables))

        return analysis

    def _set_priority(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """우선순위 설정"""

        urgency_keywords = {
            '높음': ['긴급', '즉시', '빠른', 'urgent'],
            '낮음': ['일반', '정기', '안내']
        }

        urgency = '보통'  # 기본값

        user_request = analysis.get('original_request', '')
        for level, keywords in urgency_keywords.items():
            if any(keyword in user_request for keyword in keywords):
                urgency = level
                break

        analysis['urgency'] = urgency

        return analysis

    def _apply_business_rules(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """비즈니스 규칙 적용"""

        # 카테고리 매핑
        category_mapping = {
            ('교육', '신청'): ('서비스이용', '이용안내/공지'),
            ('교육', '안내'): ('서비스이용', '이용안내/공지'),
            ('쇼핑몰', '주문'): ('거래', '주문/결제'),
            ('쇼핑몰', '배송'): ('거래', '배송'),
            ('의료', '예약'): ('서비스이용', '예약/신청'),
            ('서비스업', '예약'): ('서비스이용', '예약/신청')
        }

        business_type = analysis.get('business_type', '기타')
        service_type = analysis.get('service_type', '안내')

        category_key = (business_type, service_type)
        if category_key in category_mapping:
            category_1, category_2 = category_mapping[category_key]
            analysis['estimated_category'] = {
                'category_1': category_1,
                'category_2': category_2
            }
        else:
            analysis['estimated_category'] = {
                'category_1': '서비스이용',
                'category_2': '이용안내/공지'
            }

        # 컴플라이언스 우려사항 식별
        analysis['compliance_concerns'] = self._identify_compliance_concerns(analysis)

        return analysis

    def _identify_compliance_concerns(self, analysis: Dict[str, Any]) -> List[str]:
        """컴플라이언스 우려사항 식별"""

        concerns = []
        user_request = analysis.get('original_request', '')

        # 광고성 키워드 체크
        ad_keywords = ['할인', '이벤트', '프로모션', '혜택', '특가']
        if any(keyword in user_request for keyword in ad_keywords):
            concerns.append('광고성 내용 포함 가능성')

        # 금지 키워드 체크
        prohibited_keywords = ['무료', '쿠폰', '포인트', '적립']
        if any(keyword in user_request for keyword in prohibited_keywords):
            concerns.append('금지 키워드 포함')

        return concerns

    def _get_default_analysis(self, user_request: str) -> Dict[str, Any]:
        """분석 실패 시 기본값 반환"""

        return {
            'original_request': user_request,
            'business_type': '기타',
            'service_type': '공지/안내',
            'message_purpose': '일반 안내',
            'target_audience': '고객',
            'required_variables': ['수신자명'],
            'tone': '정중한',
            'urgency': '보통',
            'estimated_category': {
                'category_1': '서비스이용',
                'category_2': '이용안내/공지'
            },
            'compliance_concerns': ['분석 실패로 인한 수동 검토 필요']
        }

    def get_analysis_summary(self, analysis: Dict[str, Any]) -> str:
        """분석 결과 요약"""

        summary = f"""
## 요청 분석 결과

**비즈니스 정보:**
- 업종: {analysis.get('business_type', 'N/A')}
- 서비스 유형: {analysis.get('service_type', 'N/A')}
- 메시지 목적: {analysis.get('message_purpose', 'N/A')}

**메시지 설정:**
- 대상: {analysis.get('target_audience', 'N/A')}
- 톤앤매너: {analysis.get('tone', 'N/A')}
- 긴급도: {analysis.get('urgency', 'N/A')}

**필요 변수:** {', '.join(analysis.get('required_variables', []))}

**예상 카테고리:** {analysis.get('estimated_category', {}).get('category_1', 'N/A')} > {analysis.get('estimated_category', {}).get('category_2', 'N/A')}

**주의사항:** {', '.join(analysis.get('compliance_concerns', ['없음']))}
"""

        return summary


if __name__ == "__main__":
    # Test the request analyzer
    from ..utils.llm_client import ClaudeLLMClient

    llm_client = ClaudeLLMClient()
    analyzer = RequestAnalyzerAgent(llm_client)

    test_request = "온라인 강의 수강 신청 완료 후 강의 일정과 접속 방법을 안내하는 메시지"
    result = analyzer.analyze_request(test_request)

    print("Analysis Result:")
    print(analyzer.get_analysis_summary(result))