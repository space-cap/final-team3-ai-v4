#!/usr/bin/env python3
"""
하이브리드 검색 성능 테스트 스크립트
실제 데이터를 사용하여 검색 성능 검증 및 분석
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

# 프로젝트 경로 추가
sys.path.append('src')

try:
    from search.hybrid_search import HybridSearchEngine
    from search.korean_tokenizer import KoreanTokenizer
    from search.bm25_policy_search import BM25PolicySearch
except ImportError as e:
    print(f"모듈 임포트 실패: {e}")
    print("src/search 디렉토리와 모듈들이 존재하는지 확인하세요.")
    sys.exit(1)

# 환경 변수 로드
load_dotenv()


class HybridSearchTester:
    """하이브리드 검색 테스트 클래스"""

    def __init__(self):
        self.results = {
            'test_start_time': datetime.now().isoformat(),
            'environment': {
                'python_version': sys.version,
                'hybrid_search_enabled': os.getenv('HYBRID_SEARCH_ENABLED', 'false'),
                'vector_weight': float(os.getenv('VECTOR_SEARCH_WEIGHT', '0.7')),
                'bm25_weight': float(os.getenv('BM25_SEARCH_WEIGHT', '0.3')),
                'use_konlpy': os.getenv('USE_KONLPY', 'true').lower() == 'true'
            },
            'tests': [],
            'performance_summary': {}
        }

    def test_tokenizer(self) -> Dict[str, Any]:
        """한국어 토큰화 테스트"""
        print("\n=== 1. 한국어 토큰화 테스트 ===")

        tokenizer = KoreanTokenizer(use_konlpy=self.results['environment']['use_konlpy'])

        test_texts = [
            "안녕하세요 #{고객명}님, 주문하신 상품이 배송 완료되었습니다.",
            "카카오톡 알림톡 템플릿 정책을 준수해야 합니다.",
            "영업시간은 평일 09:00~18:00입니다. 문의사항이 있으시면 연락주세요.",
            "이벤트 참여 감사합니다! 당첨자 발표는 #{발표일}에 진행됩니다."
        ]

        tokenization_results = []

        for i, text in enumerate(test_texts, 1):
            start_time = time.time()
            tokens = tokenizer.tokenize(text)
            tokenization_time = time.time() - start_time

            result = {
                'text_id': i,
                'original_text': text,
                'tokens': tokens,
                'token_count': len(tokens),
                'tokenization_time': tokenization_time,
                'avg_time_per_char': tokenization_time / len(text) if text else 0
            }

            tokenization_results.append(result)

            print(f"{i}. 원본: {text}")
            print(f"   토큰: {tokens}")
            print(f"   시간: {tokenization_time:.4f}초 ({len(tokens)}개 토큰)")

        return {
            'test_name': 'korean_tokenization',
            'results': tokenization_results,
            'summary': {
                'total_texts': len(test_texts),
                'avg_tokens_per_text': sum(r['token_count'] for r in tokenization_results) / len(tokenization_results),
                'avg_tokenization_time': sum(r['tokenization_time'] for r in tokenization_results) / len(tokenization_results)
            }
        }

    def test_bm25_search(self) -> Dict[str, Any]:
        """BM25 검색 테스트"""
        print("\n=== 2. BM25 검색 테스트 ===")

        try:
            bm25_search = BM25PolicySearch(use_konlpy=self.results['environment']['use_konlpy'])

            # 데이터 로드
            template_file = os.getenv('TEMPLATE_DATA_PATH', 'data/kakao_template_vectordb_data.json')
            policy_dir = os.getenv('POLICY_DATA_PATH', 'data/cleaned_policies')

            load_start = time.time()

            template_count = 0
            policy_count = 0

            if os.path.exists(template_file):
                template_count = bm25_search.load_template_data(template_file)
                print(f"템플릿 로드: {template_count}개")

            if os.path.exists(policy_dir):
                policy_count = bm25_search.load_policy_documents(policy_dir)
                print(f"정책 문서 로드: {policy_count}개")

            # 인덱스 구축
            index_success = bm25_search.build_index()
            load_time = time.time() - load_start

            if not index_success:
                return {
                    'test_name': 'bm25_search',
                    'error': 'BM25 인덱스 구축 실패',
                    'load_time': load_time
                }

            # 테스트 쿼리
            test_queries = [
                "배송 알림 템플릿",
                "주문 확인 메시지",
                "정책 준수 가이드라인",
                "금지된 내용",
                "회원 가입 축하",
                "이벤트 당첨 안내"
            ]

            query_results = []

            for query in test_queries:
                search_start = time.time()
                results = bm25_search.search(query, top_k=5)
                search_time = time.time() - search_start

                query_result = {
                    'query': query,
                    'result_count': len(results),
                    'search_time': search_time,
                    'top_scores': [r['bm25_score'] for r in results[:3]],
                    'avg_score': sum(r['bm25_score'] for r in results) / len(results) if results else 0
                }

                query_results.append(query_result)

                print(f"쿼리: '{query}' -> {len(results)}개 결과 ({search_time:.4f}초)")
                for i, result in enumerate(results[:2], 1):
                    print(f"  {i}. {result['type']}: {result['id']} (점수: {result['bm25_score']:.3f})")

            return {
                'test_name': 'bm25_search',
                'data_loading': {
                    'template_count': template_count,
                    'policy_count': policy_count,
                    'load_time': load_time,
                    'index_success': index_success
                },
                'query_results': query_results,
                'summary': {
                    'total_queries': len(test_queries),
                    'avg_search_time': sum(r['search_time'] for r in query_results) / len(query_results),
                    'avg_results_per_query': sum(r['result_count'] for r in query_results) / len(query_results)
                }
            }

        except Exception as e:
            return {
                'test_name': 'bm25_search',
                'error': f'BM25 검색 테스트 실패: {e}'
            }

    def test_hybrid_search(self) -> Dict[str, Any]:
        """하이브리드 검색 테스트"""
        print("\n=== 3. 하이브리드 검색 테스트 ===")

        try:
            # 환경 설정에서 가중치 로드
            vector_weight = self.results['environment']['vector_weight']
            bm25_weight = self.results['environment']['bm25_weight']

            hybrid_engine = HybridSearchEngine(
                vector_weight=vector_weight,
                bm25_weight=bm25_weight,
                use_konlpy=self.results['environment']['use_konlpy']
            )

            # 데이터 초기화
            init_start = time.time()
            init_success = hybrid_engine.initialize_data()
            init_time = time.time() - init_start

            if not init_success:
                return {
                    'test_name': 'hybrid_search',
                    'error': '하이브리드 검색 데이터 초기화 실패',
                    'init_time': init_time
                }

            print(f"데이터 초기화 완료 ({init_time:.2f}초)")

            # 검색 방법별 비교 테스트
            test_queries = [
                "배송 알림 템플릿",
                "주문 확인 메시지",
                "정책 준수 가이드라인"
            ]

            comparison_results = []

            for query in test_queries:
                print(f"\n비교 테스트: '{query}'")

                comparison = hybrid_engine.compare_search_methods(query, top_k=5)
                comparison_results.append(comparison)

                # 결과 출력
                for method, data in comparison['methods'].items():
                    print(f"  [{method.upper()}] {data['result_count']}개 결과, {data['search_time']:.4f}초, 평균점수: {data['avg_score']:.3f}")

            # 성능 통계
            stats = hybrid_engine.get_search_stats()

            return {
                'test_name': 'hybrid_search',
                'initialization': {
                    'success': init_success,
                    'init_time': init_time
                },
                'comparison_results': comparison_results,
                'performance_stats': stats,
                'configuration': {
                    'vector_weight': vector_weight,
                    'bm25_weight': bm25_weight
                }
            }

        except Exception as e:
            return {
                'test_name': 'hybrid_search',
                'error': f'하이브리드 검색 테스트 실패: {e}'
            }

    def run_performance_benchmark(self) -> Dict[str, Any]:
        """성능 벤치마크 테스트"""
        print("\n=== 4. 성능 벤치마크 테스트 ===")

        try:
            # 대량 쿼리 테스트
            benchmark_queries = [
                "배송", "주문", "결제", "회원", "이벤트", "쿠폰", "적립", "혜택",
                "안내", "알림", "공지", "변경", "취소", "환불", "교환", "문의",
                "서비스", "상품", "할인", "특가", "신규", "기존", "VIP", "등급"
            ]

            vector_weight = self.results['environment']['vector_weight']
            bm25_weight = self.results['environment']['bm25_weight']

            hybrid_engine = HybridSearchEngine(
                vector_weight=vector_weight,
                bm25_weight=bm25_weight
            )

            if not hybrid_engine.initialize_data():
                return {
                    'test_name': 'performance_benchmark',
                    'error': '데이터 초기화 실패'
                }

            # 각 검색 방법별 성능 측정
            methods = ['vector', 'bm25', 'hybrid']
            benchmark_results = {}

            for method in methods:
                print(f"\n{method.upper()} 성능 테스트...")

                method_start = time.time()
                total_results = 0
                search_times = []

                for query in benchmark_queries:
                    search_start = time.time()
                    results = hybrid_engine.search(query, top_k=10, search_type=method)
                    search_time = time.time() - search_start

                    total_results += len(results)
                    search_times.append(search_time)

                method_total_time = time.time() - method_start

                benchmark_results[method] = {
                    'total_queries': len(benchmark_queries),
                    'total_results': total_results,
                    'total_time': method_total_time,
                    'avg_time_per_query': method_total_time / len(benchmark_queries),
                    'min_search_time': min(search_times),
                    'max_search_time': max(search_times),
                    'avg_search_time': sum(search_times) / len(search_times),
                    'avg_results_per_query': total_results / len(benchmark_queries)
                }

                print(f"  총 시간: {method_total_time:.3f}초")
                print(f"  평균 쿼리당: {benchmark_results[method]['avg_time_per_query']:.4f}초")
                print(f"  평균 결과수: {benchmark_results[method]['avg_results_per_query']:.1f}개")

            return {
                'test_name': 'performance_benchmark',
                'benchmark_results': benchmark_results,
                'query_count': len(benchmark_queries)
            }

        except Exception as e:
            return {
                'test_name': 'performance_benchmark',
                'error': f'성능 벤치마크 실패: {e}'
            }

    def run_all_tests(self) -> None:
        """모든 테스트 실행"""
        print("🔍 하이브리드 검색 성능 테스트 시작")
        print(f"환경 설정: Vector({self.results['environment']['vector_weight']}) + BM25({self.results['environment']['bm25_weight']})")

        # 개별 테스트 실행
        tests = [
            self.test_tokenizer,
            self.test_bm25_search,
            self.test_hybrid_search,
            self.run_performance_benchmark
        ]

        for test_func in tests:
            try:
                test_result = test_func()
                self.results['tests'].append(test_result)
            except Exception as e:
                error_result = {
                    'test_name': test_func.__name__,
                    'error': f'테스트 실행 실패: {e}'
                }
                self.results['tests'].append(error_result)
                print(f"❌ {test_func.__name__} 실패: {e}")

        # 종합 성능 요약
        self._create_performance_summary()

        # 결과 저장
        self._save_results()

    def _create_performance_summary(self) -> None:
        """성능 요약 생성"""
        summary = {
            'test_completion_time': datetime.now().isoformat(),
            'total_tests': len(self.results['tests']),
            'successful_tests': len([t for t in self.results['tests'] if 'error' not in t]),
            'failed_tests': len([t for t in self.results['tests'] if 'error' in t])
        }

        # 하이브리드 검색 성능 요약
        hybrid_test = next((t for t in self.results['tests'] if t.get('test_name') == 'hybrid_search'), None)
        if hybrid_test and 'error' not in hybrid_test:
            perf_stats = hybrid_test.get('performance_stats', {})
            if perf_stats:
                summary['hybrid_performance'] = {
                    'total_searches': perf_stats.get('total_searches', 0),
                    'avg_vector_time': perf_stats.get('avg_vector_time', 0),
                    'avg_bm25_time': perf_stats.get('avg_bm25_time', 0),
                    'avg_fusion_time': perf_stats.get('avg_fusion_time', 0)
                }

        # 벤치마크 성능 요약
        benchmark_test = next((t for t in self.results['tests'] if t.get('test_name') == 'performance_benchmark'), None)
        if benchmark_test and 'error' not in benchmark_test:
            benchmark_results = benchmark_test.get('benchmark_results', {})
            summary['benchmark_comparison'] = {}

            for method, data in benchmark_results.items():
                summary['benchmark_comparison'][method] = {
                    'avg_time_per_query': data.get('avg_time_per_query', 0),
                    'avg_results_per_query': data.get('avg_results_per_query', 0)
                }

        self.results['performance_summary'] = summary

    def _save_results(self) -> None:
        """테스트 결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"hybrid_search_test_results_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)

            print(f"\n✅ 테스트 결과 저장: {filename}")

            # 간단한 요약 출력
            summary = self.results['performance_summary']
            print(f"\n📊 테스트 요약:")
            print(f"  - 총 테스트: {summary['total_tests']}개")
            print(f"  - 성공: {summary['successful_tests']}개")
            print(f"  - 실패: {summary['failed_tests']}개")

            if 'hybrid_performance' in summary:
                hp = summary['hybrid_performance']
                print(f"  - 하이브리드 검색 수행: {hp['total_searches']}회")
                print(f"  - 평균 융합 시간: {hp['avg_fusion_time']:.4f}초")

        except Exception as e:
            print(f"❌ 결과 저장 실패: {e}")


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🔍 하이브리드 검색 시스템 성능 테스트")
    print("=" * 60)

    # 필수 데이터 파일 확인
    template_file = os.getenv('TEMPLATE_DATA_PATH', 'data/kakao_template_vectordb_data.json')
    policy_dir = os.getenv('POLICY_DATA_PATH', 'data/cleaned_policies')

    missing_files = []
    if not os.path.exists(template_file):
        missing_files.append(template_file)
    if not os.path.exists(policy_dir):
        missing_files.append(policy_dir)

    if missing_files:
        print(f"❌ 필수 데이터 파일이 없습니다:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        print("\n데이터 파일을 확인한 후 다시 실행하세요.")
        return

    # 테스트 실행
    tester = HybridSearchTester()
    tester.run_all_tests()

    print("\n🎉 하이브리드 검색 테스트 완료!")


if __name__ == "__main__":
    main()