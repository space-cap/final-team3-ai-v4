#!/usr/bin/env python3
"""
BM25 기반 정책 문서 검색 모듈
한국어 특화 BM25 검색 엔진
"""

import json
import os
from typing import List, Dict, Tuple, Optional, Any
import logging
from pathlib import Path

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    logging.warning("rank-bm25 라이브러리가 설치되지 않았습니다.")

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.search.korean_tokenizer import KoreanTokenizer, PolicyTextPreprocessor

logger = logging.getLogger(__name__)


class BM25PolicySearch:
    """
    BM25 알고리즘 기반 정책 문서 검색 클래스
    한국어 토큰화와 정책 문서 특화 기능 지원
    """

    def __init__(self,
                 k1: float = 1.2,
                 b: float = 0.75,
                 use_konlpy: bool = True):
        """
        BM25 검색 엔진 초기화

        Args:
            k1: BM25 k1 파라미터 (term frequency saturation)
            b: BM25 b 파라미터 (field length normalization)
            use_konlpy: KoNLPy 사용 여부
        """
        if not BM25_AVAILABLE:
            raise ImportError("rank-bm25 라이브러리가 필요합니다: pip install rank-bm25")

        self.k1 = k1
        self.b = b
        self.tokenizer = KoreanTokenizer(use_konlpy=use_konlpy)
        self.preprocessor = PolicyTextPreprocessor()

        # 검색 데이터
        self.documents: List[Dict] = []
        self.tokenized_docs: List[List[str]] = []
        self.bm25_model: Optional[BM25Okapi] = None

        # 문서 유형별 인덱스
        self.template_indices: List[int] = []
        self.policy_indices: List[int] = []

        logger.info(f"BM25 검색 엔진 초기화 완료 (k1={k1}, b={b})")

    def load_template_data(self, data_file: str) -> int:
        """
        템플릿 데이터 로드

        Args:
            data_file: 템플릿 데이터 파일 경로

        Returns:
            로드된 템플릿 수
        """
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            count = 0
            for item in data:
                if 'text' in item:
                    # 템플릿 텍스트 전처리
                    processed = self.preprocessor.preprocess_template(item['text'])

                    doc = {
                        'id': item.get('id', f'template_{count}'),
                        'type': 'template',
                        'content': item['text'],
                        'tokens': processed['tokens'],
                        'metadata': item.get('metadata', {}),
                        'variables': processed['variables'],
                        'processed': processed
                    }

                    self.documents.append(doc)
                    self.tokenized_docs.append(processed['tokens'])
                    self.template_indices.append(len(self.documents) - 1)
                    count += 1

            logger.info(f"템플릿 데이터 로드 완료: {count}개")
            return count

        except Exception as e:
            logger.error(f"템플릿 데이터 로드 실패: {e}")
            return 0

    def load_policy_documents(self, policy_dir: str) -> int:
        """
        정책 문서 로드

        Args:
            policy_dir: 정책 문서 디렉토리 경로

        Returns:
            로드된 정책 문서 수
        """
        try:
            policy_path = Path(policy_dir)
            if not policy_path.exists():
                logger.warning(f"정책 디렉토리가 존재하지 않습니다: {policy_dir}")
                return 0

            count = 0
            for file_path in policy_path.glob('*.md'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 정책 문서 전처리
                processed = self.preprocessor.preprocess_policy(content)

                doc = {
                    'id': file_path.stem,
                    'type': 'policy',
                    'content': content,
                    'tokens': processed['tokens'],
                    'metadata': {
                        'file_name': file_path.name,
                        'file_path': str(file_path),
                        'keywords': processed['keywords']
                    },
                    'processed': processed
                }

                self.documents.append(doc)
                self.tokenized_docs.append(processed['tokens'])
                self.policy_indices.append(len(self.documents) - 1)
                count += 1

            logger.info(f"정책 문서 로드 완료: {count}개")
            return count

        except Exception as e:
            logger.error(f"정책 문서 로드 실패: {e}")
            return 0

    def build_index(self) -> bool:
        """
        BM25 인덱스 구축

        Returns:
            구축 성공 여부
        """
        try:
            if not self.tokenized_docs:
                logger.warning("인덱싱할 문서가 없습니다.")
                return False

            # BM25 모델 생성
            self.bm25_model = BM25Okapi(self.tokenized_docs, k1=self.k1, b=self.b)

            logger.info(f"BM25 인덱스 구축 완료: {len(self.documents)}개 문서")
            return True

        except Exception as e:
            logger.error(f"BM25 인덱스 구축 실패: {e}")
            return False

    def search(self,
               query: str,
               top_k: int = 10,
               doc_type: Optional[str] = None) -> List[Dict]:
        """
        BM25 검색 실행

        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 수
            doc_type: 문서 유형 필터 ('template', 'policy', None)

        Returns:
            검색 결과 리스트
        """
        if not self.bm25_model:
            logger.error("BM25 인덱스가 구축되지 않았습니다.")
            return []

        try:
            # 쿼리 토큰화
            query_tokens = self.tokenizer.tokenize(query)
            if not query_tokens:
                logger.warning("쿼리에서 유효한 토큰을 찾을 수 없습니다.")
                return []

            # BM25 점수 계산
            scores = self.bm25_model.get_scores(query_tokens)

            # 문서 유형 필터링
            if doc_type:
                filtered_indices = []
                if doc_type == 'template':
                    filtered_indices = self.template_indices
                elif doc_type == 'policy':
                    filtered_indices = self.policy_indices

                # 필터링된 인덱스만 고려
                filtered_scores = []
                for i in filtered_indices:
                    if i < len(scores):
                        filtered_scores.append((scores[i], i))
            else:
                filtered_scores = [(score, i) for i, score in enumerate(scores)]

            # 점수 기준 정렬
            filtered_scores.sort(key=lambda x: x[0], reverse=True)

            # 상위 결과 반환
            results = []
            for score, doc_idx in filtered_scores[:top_k]:
                if score > 0:  # 0점 초과 결과만
                    doc = self.documents[doc_idx].copy()
                    doc['bm25_score'] = float(score)
                    doc['rank'] = len(results) + 1
                    results.append(doc)

            logger.info(f"BM25 검색 완료: {len(results)}개 결과 (쿼리: '{query}')")
            return results

        except Exception as e:
            logger.error(f"BM25 검색 실패: {e}")
            return []

    def get_document_stats(self) -> Dict:
        """
        문서 통계 정보 반환

        Returns:
            문서 통계 딕셔너리
        """
        return {
            'total_documents': len(self.documents),
            'template_count': len(self.template_indices),
            'policy_count': len(self.policy_indices),
            'total_tokens': sum(len(tokens) for tokens in self.tokenized_docs),
            'average_tokens_per_doc': (
                sum(len(tokens) for tokens in self.tokenized_docs) / len(self.tokenized_docs)
                if self.tokenized_docs else 0
            ),
            'index_built': self.bm25_model is not None
        }

    def explain_search(self, query: str, doc_id: str) -> Dict:
        """
        검색 결과 설명

        Args:
            query: 검색 쿼리
            doc_id: 문서 ID

        Returns:
            검색 결과 설명
        """
        try:
            # 문서 찾기
            doc_idx = None
            for i, doc in enumerate(self.documents):
                if doc['id'] == doc_id:
                    doc_idx = i
                    break

            if doc_idx is None:
                return {'error': f'문서 ID {doc_id}를 찾을 수 없습니다.'}

            # 쿼리 토큰화
            query_tokens = self.tokenizer.tokenize(query)
            doc_tokens = self.tokenized_docs[doc_idx]

            # 매칭 토큰 찾기
            matching_tokens = list(set(query_tokens) & set(doc_tokens))

            # BM25 점수 계산
            if self.bm25_model:
                scores = self.bm25_model.get_scores(query_tokens)
                bm25_score = scores[doc_idx] if doc_idx < len(scores) else 0
            else:
                bm25_score = 0

            return {
                'query_tokens': query_tokens,
                'doc_tokens': doc_tokens,
                'matching_tokens': matching_tokens,
                'match_ratio': len(matching_tokens) / len(query_tokens) if query_tokens else 0,
                'bm25_score': float(bm25_score),
                'doc_length': len(doc_tokens),
                'doc_type': self.documents[doc_idx]['type']
            }

        except Exception as e:
            return {'error': f'검색 설명 생성 실패: {e}'}


def test_bm25_search():
    """BM25 검색 테스트 함수"""

    print("=== BM25 정책 검색 테스트 ===")

    # 검색 엔진 초기화
    search_engine = BM25PolicySearch()

    # 테스트 데이터 로드
    data_file = "data/kakao_template_vectordb_data.json"
    policy_dir = "data/cleaned_policies"

    if os.path.exists(data_file):
        template_count = search_engine.load_template_data(data_file)
        print(f"템플릿 로드: {template_count}개")

    if os.path.exists(policy_dir):
        policy_count = search_engine.load_policy_documents(policy_dir)
        print(f"정책 문서 로드: {policy_count}개")

    # 인덱스 구축
    if search_engine.build_index():
        print("BM25 인덱스 구축 완료")

        # 통계 정보
        stats = search_engine.get_document_stats()
        print(f"통계: {stats}")

        # 테스트 검색
        test_queries = [
            "배송 알림 템플릿",
            "주문 확인 메시지",
            "정책 준수 가이드라인",
            "금지된 내용"
        ]

        for query in test_queries:
            print(f"\n검색 쿼리: '{query}'")
            results = search_engine.search(query, top_k=3)

            for result in results:
                print(f"  - {result['type']}: {result['id']} (점수: {result['bm25_score']:.3f})")
                content_preview = result['content'][:100].replace('\n', ' ')
                print(f"    내용: {content_preview}...")
    else:
        print("BM25 인덱스 구축 실패")


if __name__ == "__main__":
    test_bm25_search()