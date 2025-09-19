"""
Policy RAG Agent - 정책 문서 기반 검색 및 컨텍스트 제공
"""
import logging
from typing import Dict, Any, List
from ..database.vector_store import PolicyVectorStore

logger = logging.getLogger(__name__)

class PolicyRAGAgent:
    """정책 문서를 기반으로 관련 정보를 검색하고 컨텍스트를 제공하는 에이전트"""

    def __init__(self, vector_store: PolicyVectorStore):
        self.vector_store = vector_store

    def get_relevant_policies(self, query: str, context_type: str = "general") -> Dict[str, Any]:
        """
        쿼리에 관련된 정책 정보를 검색하여 반환

        Args:
            query: 검색 쿼리
            context_type: 컨텍스트 유형 (template_generation, compliance_check, general)

        Returns:
            관련 정책 정보와 컨텍스트
        """
        logger.info(f"Searching for policies related to: {query[:100]}...")

        try:
            # 1. 기본 검색
            search_results = self.vector_store.search_relevant_policies(query, k=8)

            # 2. 컨텍스트 유형별 추가 검색
            additional_results = self._get_context_specific_policies(context_type)

            # 3. 결과 통합 및 정리
            combined_results = self._combine_and_deduplicate(search_results, additional_results)

            # 4. 컨텍스트 생성
            formatted_context = self._format_policy_context(combined_results, context_type)

            logger.info(f"Found {len(combined_results)} relevant policy chunks")

            return {
                'context': formatted_context,
                'sources': self._extract_sources(combined_results),
                'policy_types': self._extract_policy_types(combined_results),
                'relevance_scores': [r.get('relevance_score', 0) for r in combined_results],
                'total_chunks': len(combined_results)
            }

        except Exception as e:
            logger.error(f"Error retrieving policies: {e}")
            return self._get_fallback_context(context_type)

    def _get_context_specific_policies(self, context_type: str) -> List[Dict[str, Any]]:
        """컨텍스트 유형별 추가 정책 검색"""

        additional_searches = {
            'template_generation': [
                "알림톡 템플릿 작성 가이드",
                "메시지 유형별 작성 방법",
                "변수 사용 규칙"
            ],
            'compliance_check': [
                "알림톡 심사 기준",
                "블랙리스트 위반 사항",
                "승인 반려 사유"
            ],
            'general': [
                "알림톡 기본 규칙",
                "정보성 메시지 정의"
            ]
        }

        results = []
        searches = additional_searches.get(context_type, additional_searches['general'])

        for search_query in searches:
            search_results = self.vector_store.search_relevant_policies(search_query, k=3)
            results.extend(search_results)

        return results

    def _combine_and_deduplicate(self, primary_results: List[Dict[str, Any]],
                                additional_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """결과 통합 및 중복 제거"""

        all_results = primary_results + additional_results
        seen_contents = set()
        unique_results = []

        for result in all_results:
            content = result.get('content', '')
            content_hash = hash(content[:100])  # 내용의 처음 100자로 해시 생성

            if content_hash not in seen_contents and content.strip():
                seen_contents.add(content_hash)
                unique_results.append(result)

        # 관련도 점수 기준으로 정렬
        unique_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

        return unique_results[:10]  # 최대 10개로 제한

    def _format_policy_context(self, results: List[Dict[str, Any]], context_type: str) -> str:
        """정책 컨텍스트 포맷팅"""

        if not results:
            return self._get_basic_policy_context()

        context_parts = []

        # 컨텍스트 유형별 헤더
        headers = {
            'template_generation': "## 카카오 알림톡 템플릿 작성 가이드",
            'compliance_check': "## 카카오 알림톡 정책 준수 기준",
            'general': "## 카카오 알림톡 정책 정보"
        }

        context_parts.append(headers.get(context_type, headers['general']))

        # 정책 유형별 그룹화
        grouped_policies = self._group_by_policy_type(results)

        for policy_type, policy_results in grouped_policies.items():
            if policy_results:
                context_parts.append(f"\n### {self._get_policy_type_title(policy_type)}")

                for i, result in enumerate(policy_results[:3]):  # 각 유형당 최대 3개
                    content = result.get('content', '').strip()
                    if content:
                        context_parts.append(f"\n{content}")

                        # 구분선 추가 (마지막이 아닌 경우)
                        if i < len(policy_results[:3]) - 1:
                            context_parts.append("\n---")

        return '\n'.join(context_parts)

    def _group_by_policy_type(self, results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """정책 유형별 그룹화"""

        grouped = {}
        for result in results:
            policy_type = result.get('metadata', {}).get('policy_type', 'general')
            if policy_type not in grouped:
                grouped[policy_type] = []
            grouped[policy_type].append(result)

        return grouped

    def _get_policy_type_title(self, policy_type: str) -> str:
        """정책 유형 제목 매핑"""

        titles = {
            'review_guidelines': '심사 가이드라인',
            'content_guidelines': '콘텐츠 작성 가이드',
            'allowed_templates': '허용 템플릿 유형',
            'prohibited_templates': '금지 템플릿 유형',
            'operational_procedures': '운영 절차',
            'image_guidelines': '이미지 가이드라인',
            'infotalk_guidelines': '인포톡 가이드라인',
            'public_template_guidelines': '공용 템플릿 가이드라인',
            'general': '일반 정책'
        }

        return titles.get(policy_type, '기타 정책')

    def _extract_sources(self, results: List[Dict[str, Any]]) -> List[str]:
        """소스 파일 추출"""

        sources = set()
        for result in results:
            source = result.get('metadata', {}).get('source', '')
            if source:
                sources.add(source)

        return list(sources)

    def _extract_policy_types(self, results: List[Dict[str, Any]]) -> List[str]:
        """정책 유형 추출"""

        policy_types = set()
        for result in results:
            policy_type = result.get('metadata', {}).get('policy_type', '')
            if policy_type:
                policy_types.add(policy_type)

        return list(policy_types)

    def _get_basic_policy_context(self) -> str:
        """기본 정책 컨텍스트"""

        return """
## 카카오 알림톡 기본 정책

### 기본 원칙
1. 알림톡은 정보성 메시지만 발송 가능합니다.
2. 광고성 내용은 포함할 수 없습니다.
3. 수신자가 서비스를 이용하거나 계약을 체결한 경우에만 발송 가능합니다.

### 필수 요구사항
- 메시지는 1,000자 이내로 작성해야 합니다.
- 변수는 #{변수명} 형태로 사용하며 40개를 초과할 수 없습니다.
- 정중한 어조를 유지해야 합니다.
- 정보성 메시지임을 명시해야 합니다.

### 금지사항
- 광고성 표현 (할인, 이벤트, 특가 등)
- 변수만으로 구성된 메시지
- 과도한 연락처 정보
- 블랙리스트에 해당하는 내용
"""

    def _get_fallback_context(self, context_type: str) -> Dict[str, Any]:
        """검색 실패 시 기본 컨텍스트"""

        return {
            'context': self._get_basic_policy_context(),
            'sources': ['fallback'],
            'policy_types': ['general'],
            'relevance_scores': [1.0],
            'total_chunks': 1
        }

    def get_specific_policy(self, policy_type: str) -> Dict[str, Any]:
        """특정 정책 유형의 정보 검색"""

        logger.info(f"Retrieving specific policy: {policy_type}")

        try:
            results = self.vector_store.get_policy_by_type(policy_type, k=5)

            if not results:
                return self._get_fallback_context('general')

            formatted_context = self._format_specific_policy(results, policy_type)

            return {
                'context': formatted_context,
                'sources': self._extract_sources(results),
                'policy_types': [policy_type],
                'total_chunks': len(results)
            }

        except Exception as e:
            logger.error(f"Error retrieving specific policy {policy_type}: {e}")
            return self._get_fallback_context('general')

    def _format_specific_policy(self, results: List[Dict[str, Any]], policy_type: str) -> str:
        """특정 정책 포맷팅"""

        context_parts = [f"## {self._get_policy_type_title(policy_type)}"]

        for i, result in enumerate(results):
            content = result.get('content', '').strip()
            if content:
                context_parts.append(f"\n### 섹션 {i + 1}")
                context_parts.append(f"\n{content}")

                if i < len(results) - 1:
                    context_parts.append("\n---")

        return '\n'.join(context_parts)

    def search_policy_examples(self, business_type: str, service_type: str) -> Dict[str, Any]:
        """비즈니스/서비스 유형별 정책 예시 검색"""

        query = f"{business_type} {service_type} 템플릿 예시 가이드"
        logger.info(f"Searching policy examples for: {query}")

        try:
            # 화이트리스트에서 예시 검색
            whitelist_results = self.vector_store.get_policy_by_type('allowed_templates', k=10)

            # 관련 예시 필터링
            relevant_examples = []
            for result in whitelist_results:
                content = result.get('content', '')
                if any(keyword in content for keyword in [business_type, service_type]):
                    relevant_examples.append(result)

            if not relevant_examples:
                # 일반적인 예시 검색
                general_results = self.vector_store.search_relevant_policies(query, k=5)
                relevant_examples = general_results

            formatted_examples = self._format_policy_examples(relevant_examples)

            return {
                'context': formatted_examples,
                'sources': self._extract_sources(relevant_examples),
                'total_examples': len(relevant_examples)
            }

        except Exception as e:
            logger.error(f"Error searching policy examples: {e}")
            return {
                'context': "관련 예시를 찾을 수 없습니다.",
                'sources': [],
                'total_examples': 0
            }

    def _format_policy_examples(self, results: List[Dict[str, Any]]) -> str:
        """정책 예시 포맷팅"""

        if not results:
            return "관련 예시가 없습니다."

        context_parts = ["## 관련 템플릿 예시"]

        for i, result in enumerate(results[:5]):  # 최대 5개 예시
            content = result.get('content', '').strip()
            if content and '예시' in content:
                context_parts.append(f"\n### 예시 {i + 1}")
                context_parts.append(f"\n{content}")

        if len(context_parts) == 1:  # 헤더만 있는 경우
            context_parts.append("\n적절한 예시를 찾을 수 없습니다.")

        return '\n'.join(context_parts)

    def get_compliance_guidelines(self, violation_types: List[str] = None) -> Dict[str, Any]:
        """컴플라이언스 가이드라인 검색"""

        if not violation_types:
            query = "알림톡 정책 준수 가이드라인 심사 기준"
        else:
            query = f"알림톡 {' '.join(violation_types)} 위반 해결 방법"

        logger.info(f"Retrieving compliance guidelines for: {query}")

        try:
            # 심사 가이드라인 검색
            audit_results = self.vector_store.get_policy_by_type('review_guidelines', k=5)

            # 블랙리스트 정보 검색
            blacklist_results = self.vector_store.get_policy_by_type('prohibited_templates', k=3)

            # 결과 통합
            all_results = audit_results + blacklist_results
            formatted_guidelines = self._format_compliance_guidelines(all_results)

            return {
                'context': formatted_guidelines,
                'sources': self._extract_sources(all_results),
                'total_guidelines': len(all_results)
            }

        except Exception as e:
            logger.error(f"Error retrieving compliance guidelines: {e}")
            return self._get_fallback_context('compliance_check')


    def _format_compliance_guidelines(self, results: List[Dict[str, Any]]) -> str:
        """컴플라이언스 가이드라인 포맷팅"""

        context_parts = ["## 컴플라이언스 가이드라인"]

        # 심사 기준 섹션
        context_parts.append("\n### 심사 기준")
        audit_content = []
        for result in results:
            if result.get('metadata', {}).get('policy_type') == 'review_guidelines':
                content = result.get('content', '').strip()
                if content:
                    audit_content.append(content)

        if audit_content:
            context_parts.extend(audit_content[:2])  # 최대 2개
        else:
            context_parts.append("심사 기준 정보를 찾을 수 없습니다.")

        # 금지사항 섹션
        context_parts.append("\n### 주요 금지사항")
        blacklist_content = []
        for result in results:
            if result.get('metadata', {}).get('policy_type') == 'prohibited_templates':
                content = result.get('content', '').strip()
                if content:
                    blacklist_content.append(content)

        if blacklist_content:
            context_parts.extend(blacklist_content[:2])  # 최대 2개
        else:
            context_parts.append("금지사항 정보를 찾을 수 없습니다.")

        return '\n'.join(context_parts)


if __name__ == "__main__":
    # Test the Policy RAG agent
    from ..database.vector_store import PolicyVectorStore

    vector_store = PolicyVectorStore()
    vector_store.load_policy_documents()  # 정책 문서 로드

    rag_agent = PolicyRAGAgent(vector_store)

    # Test general policy search
    result = rag_agent.get_relevant_policies("교육 서비스 강의 신청 템플릿", "template_generation")
    print("Policy Context Length:", len(result['context']))
    print("Sources:", result['sources'])

    # Test specific policy
    specific_result = rag_agent.get_specific_policy('review_guidelines')
    print("Specific Policy Length:", len(specific_result['context']))