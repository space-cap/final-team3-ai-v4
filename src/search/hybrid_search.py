#!/usr/bin/env python3
"""
하이브리드 검색 엔진
Dense Vector Search (Chroma) + Sparse Retrieval (BM25) 결합
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
import numpy as np

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.database.vector_store import PolicyVectorStore, TemplateStore
from src.search.bm25_policy_search import BM25PolicySearch
from src.search.korean_tokenizer import KoreanTokenizer

logger = logging.getLogger(__name__)


class HybridSearchEngine:
    """
    하이브리드 검색 엔진
    Dense Vector Search와 BM25 Sparse Retrieval을 결합하여 최적의 검색 성능 제공
    """

    def __init__(self,
                 vector_weight: float = 0.7,
                 bm25_weight: float = 0.3,
                 normalize_scores: bool = True,
                 use_konlpy: bool = True):
        """
        하이브리드 검색 엔진 초기화

        Args:
            vector_weight: Dense vector 검색 가중치 (0.0 ~ 1.0)
            bm25_weight: BM25 검색 가중치 (0.0 ~ 1.0)
            normalize_scores: 점수 정규화 여부
            use_konlpy: KoNLPy 사용 여부
        """
        # 가중치 검증
        if vector_weight + bm25_weight != 1.0:
            logger.warning(f"가중치 합이 1.0이 아닙니다: {vector_weight + bm25_weight}")
            # 정규화
            total = vector_weight + bm25_weight
            vector_weight = vector_weight / total
            bm25_weight = bm25_weight / total

        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.normalize_scores = normalize_scores

        # 검색 엔진들 초기화
        self.vector_store = PolicyVectorStore()
        self.bm25_search = BM25PolicySearch(use_konlpy=use_konlpy)
        self.template_store = TemplateStore()
        self.tokenizer = KoreanTokenizer(use_konlpy=use_konlpy)

        # 성능 통계
        self.search_stats = {
            'total_searches': 0,
            'vector_search_time': 0,
            'bm25_search_time': 0,
            'fusion_time': 0,
            'last_search_results': None
        }

        logger.info(f"하이브리드 검색 엔진 초기화 완료 (Vector:{vector_weight:.2f}, BM25:{bm25_weight:.2f})")

    def initialize_data(self,
                       template_file: str = "data/kakao_template_vectordb_data.json",
                       policy_dir: str = "data/cleaned_policies") -> bool:
        """
        검색 데이터 초기화

        Args:
            template_file: 템플릿 데이터 파일 경로
            policy_dir: 정책 문서 디렉토리 경로

        Returns:
            초기화 성공 여부
        """
        try:
            start_time = datetime.now()

            # Vector Store 초기화
            if os.path.exists(policy_dir):
                self.vector_store.load_policy_documents(policy_dir)
                logger.info("Vector store 정책 문서 로드 완료")

            # BM25 Search 초기화
            template_count = 0
            policy_count = 0

            if os.path.exists(template_file):
                template_count = self.bm25_search.load_template_data(template_file)

            if os.path.exists(policy_dir):
                policy_count = self.bm25_search.load_policy_documents(policy_dir)

            # BM25 인덱스 구축
            if not self.bm25_search.build_index():
                logger.error("BM25 인덱스 구축 실패")
                return False

            # 초기화 시간 측정
            init_time = (datetime.now() - start_time).total_seconds()

            logger.info(f"하이브리드 검색 데이터 초기화 완료")
            logger.info(f"  - 템플릿: {template_count}개")
            logger.info(f"  - 정책 문서: {policy_count}개")
            logger.info(f"  - 초기화 시간: {init_time:.2f}초")

            return True

        except Exception as e:
            logger.error(f"하이브리드 검색 데이터 초기화 실패: {e}")
            return False

    def search(self,
               query: str,
               top_k: int = 10,
               search_type: str = "hybrid",
               doc_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        하이브리드 검색 실행

        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 수
            search_type: 검색 유형 ("hybrid", "vector", "bm25")
            doc_type: 문서 유형 필터 ("template", "policy", None)

        Returns:
            검색 결과 리스트
        """
        start_time = datetime.now()
        self.search_stats['total_searches'] += 1

        try:
            if search_type == "vector":
                return self._vector_search_only(query, top_k, doc_type)
            elif search_type == "bm25":
                return self._bm25_search_only(query, top_k, doc_type)
            else:
                return self._hybrid_search(query, top_k, doc_type)

        except Exception as e:
            logger.error(f"검색 실행 실패: {e}")
            return []

        finally:
            total_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"검색 완료 시간: {total_time:.3f}초")

    def _vector_search_only(self, query: str, top_k: int, doc_type: Optional[str]) -> List[Dict[str, Any]]:
        """Vector 검색만 실행"""
        start_time = datetime.now()

        if doc_type == "policy":
            results = self.vector_store.search_relevant_policies(query, top_k)
            formatted_results = []

            for result in results:
                formatted_results.append({
                    'id': f"policy_{result['metadata'].get('source', 'unknown')}",
                    'type': 'policy',
                    'content': result['content'],
                    'metadata': result['metadata'],
                    'vector_score': float(result['relevance_score']),
                    'bm25_score': 0.0,
                    'hybrid_score': float(result['relevance_score']),
                    'search_method': 'vector_only'
                })

        elif doc_type == "template":
            # 템플릿은 별도 벡터 검색 로직 필요
            # 현재는 빈 결과 반환
            formatted_results = []

        else:
            # 전체 검색
            results = self.vector_store.search_relevant_policies(query, top_k)
            formatted_results = []

            for result in results:
                formatted_results.append({
                    'id': f"policy_{result['metadata'].get('source', 'unknown')}",
                    'type': 'policy',
                    'content': result['content'],
                    'metadata': result['metadata'],
                    'vector_score': float(result['relevance_score']),
                    'bm25_score': 0.0,
                    'hybrid_score': float(result['relevance_score']),
                    'search_method': 'vector_only'
                })

        search_time = (datetime.now() - start_time).total_seconds()
        self.search_stats['vector_search_time'] += search_time

        return formatted_results

    def _bm25_search_only(self, query: str, top_k: int, doc_type: Optional[str]) -> List[Dict[str, Any]]:
        """BM25 검색만 실행"""
        start_time = datetime.now()

        results = self.bm25_search.search(query, top_k, doc_type)
        formatted_results = []

        for result in results:
            formatted_results.append({
                'id': result['id'],
                'type': result['type'],
                'content': result['content'],
                'metadata': result['metadata'],
                'vector_score': 0.0,
                'bm25_score': result['bm25_score'],
                'hybrid_score': result['bm25_score'],
                'search_method': 'bm25_only'
            })

        search_time = (datetime.now() - start_time).total_seconds()
        self.search_stats['bm25_search_time'] += search_time

        return formatted_results

    def _hybrid_search(self, query: str, top_k: int, doc_type: Optional[str]) -> List[Dict[str, Any]]:
        """하이브리드 검색 실행"""
        fusion_start = datetime.now()

        # 1. Vector 검색
        vector_start = datetime.now()
        vector_results = {}

        if not doc_type or doc_type == "policy":
            policy_results = self.vector_store.search_relevant_policies(query, top_k * 2)
            for result in policy_results:
                doc_id = f"policy_{result['metadata'].get('source', 'unknown')}"
                vector_results[doc_id] = {
                    'id': doc_id,
                    'type': 'policy',
                    'content': result['content'],
                    'metadata': result['metadata'],
                    'vector_score': float(result['relevance_score'])
                }

        vector_time = (datetime.now() - vector_start).total_seconds()
        self.search_stats['vector_search_time'] += vector_time

        # 2. BM25 검색
        bm25_start = datetime.now()
        bm25_results = self.bm25_search.search(query, top_k * 2, doc_type)

        bm25_scores = {}
        for result in bm25_results:
            bm25_scores[result['id']] = {
                'id': result['id'],
                'type': result['type'],
                'content': result['content'],
                'metadata': result['metadata'],
                'bm25_score': result['bm25_score']
            }

        bm25_time = (datetime.now() - bm25_start).total_seconds()
        self.search_stats['bm25_search_time'] += bm25_time

        # 3. 점수 융합 (Score Fusion)
        all_doc_ids = set(vector_results.keys()) | set(bm25_scores.keys())
        fused_results = []

        for doc_id in all_doc_ids:
            # Vector 점수
            vector_score = 0.0
            if doc_id in vector_results:
                vector_score = vector_results[doc_id]['vector_score']

            # BM25 점수
            bm25_score = 0.0
            if doc_id in bm25_scores:
                bm25_score = bm25_scores[doc_id]['bm25_score']

            # 점수 정규화 (필요시)
            if self.normalize_scores:
                # Min-max 정규화 또는 z-score 정규화 적용 가능
                pass

            # 하이브리드 점수 계산
            hybrid_score = (self.vector_weight * vector_score +
                          self.bm25_weight * bm25_score)

            # 결과 객체 생성
            if doc_id in vector_results:
                base_result = vector_results[doc_id]
            else:
                base_result = bm25_scores[doc_id]

            fused_result = {
                'id': doc_id,
                'type': base_result['type'],
                'content': base_result['content'],
                'metadata': base_result['metadata'],
                'vector_score': vector_score,
                'bm25_score': bm25_score,
                'hybrid_score': hybrid_score,
                'search_method': 'hybrid'
            }

            fused_results.append(fused_result)

        # 하이브리드 점수로 정렬
        fused_results.sort(key=lambda x: x['hybrid_score'], reverse=True)

        # 상위 결과 반환
        final_results = fused_results[:top_k]

        fusion_time = (datetime.now() - fusion_start).total_seconds()
        self.search_stats['fusion_time'] += fusion_time

        # 결과 저장 (분석용)
        self.search_stats['last_search_results'] = {
            'query': query,
            'vector_results_count': len(vector_results),
            'bm25_results_count': len(bm25_scores),
            'fused_results_count': len(final_results),
            'search_time': fusion_time
        }

        logger.info(f"하이브리드 검색 완료: {len(final_results)}개 결과")
        logger.info(f"  - Vector: {len(vector_results)}개, BM25: {len(bm25_scores)}개")

        return final_results

    def get_search_stats(self) -> Dict[str, Any]:
        """검색 성능 통계 반환"""
        stats = self.search_stats.copy()

        if stats['total_searches'] > 0:
            stats['avg_vector_time'] = stats['vector_search_time'] / stats['total_searches']
            stats['avg_bm25_time'] = stats['bm25_search_time'] / stats['total_searches']
            stats['avg_fusion_time'] = stats['fusion_time'] / stats['total_searches']

        return stats

    def compare_search_methods(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        검색 방법별 비교 결과 제공

        Args:
            query: 비교할 검색 쿼리
            top_k: 각 방법별 결과 수

        Returns:
            비교 결과 딕셔너리
        """
        comparison = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'methods': {}
        }

        # 각 검색 방법별 결과
        methods = ['vector', 'bm25', 'hybrid']

        for method in methods:
            start_time = datetime.now()
            results = self.search(query, top_k, method)
            search_time = (datetime.now() - start_time).total_seconds()

            comparison['methods'][method] = {
                'results': results,
                'result_count': len(results),
                'search_time': search_time,
                'avg_score': np.mean([r['hybrid_score'] for r in results]) if results else 0
            }

        return comparison

    def explain_hybrid_score(self, query: str, doc_id: str) -> Dict[str, Any]:
        """
        하이브리드 점수 계산 과정 설명

        Args:
            query: 검색 쿼리
            doc_id: 문서 ID

        Returns:
            점수 계산 설명
        """
        explanation = {
            'query': query,
            'doc_id': doc_id,
            'weights': {
                'vector_weight': self.vector_weight,
                'bm25_weight': self.bm25_weight
            }
        }

        try:
            # BM25 검색 설명
            bm25_explanation = self.bm25_search.explain_search(query, doc_id)
            explanation['bm25_analysis'] = bm25_explanation

            # Vector 검색은 별도 설명 로직 필요
            # 현재는 기본 정보만 제공
            explanation['vector_analysis'] = {
                'embedding_model': 'text-embedding-3-small',
                'similarity_metric': 'cosine'
            }

            return explanation

        except Exception as e:
            return {'error': f'점수 설명 생성 실패: {e}'}


def test_hybrid_search():
    """하이브리드 검색 테스트 함수"""

    print("=== 하이브리드 검색 엔진 테스트 ===")

    # 검색 엔진 초기화
    hybrid_engine = HybridSearchEngine(
        vector_weight=0.7,
        bm25_weight=0.3
    )

    # 데이터 초기화
    if hybrid_engine.initialize_data():
        print("데이터 초기화 완료")

        # 테스트 검색 쿼리
        test_queries = [
            "배송 알림 템플릿",
            "주문 확인 메시지",
            "정책 준수 가이드라인",
            "금지된 내용 확인"
        ]

        for query in test_queries:
            print(f"\n검색 쿼리: '{query}'")

            # 검색 방법 비교
            comparison = hybrid_engine.compare_search_methods(query, top_k=3)

            for method, data in comparison['methods'].items():
                print(f"\n[{method.upper()}] 결과:")
                print(f"  결과 수: {data['result_count']}")
                print(f"  검색 시간: {data['search_time']:.3f}초")
                print(f"  평균 점수: {data['avg_score']:.3f}")

                for i, result in enumerate(data['results'][:2], 1):
                    print(f"    {i}. {result['type']}: {result['id']}")
                    print(f"       점수: V={result['vector_score']:.3f}, B={result['bm25_score']:.3f}, H={result['hybrid_score']:.3f}")

        # 성능 통계
        stats = hybrid_engine.get_search_stats()
        print(f"\n=== 성능 통계 ===")
        print(f"총 검색 수: {stats['total_searches']}")
        if stats['total_searches'] > 0:
            print(f"평균 Vector 시간: {stats['avg_vector_time']:.3f}초")
            print(f"평균 BM25 시간: {stats['avg_bm25_time']:.3f}초")
            print(f"평균 융합 시간: {stats['avg_fusion_time']:.3f}초")
    else:
        print("데이터 초기화 실패")


if __name__ == "__main__":
    test_hybrid_search()