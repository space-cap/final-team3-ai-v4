#!/usr/bin/env python3
"""
간단한 하이브리드 검색 테스트
"""

import os
import sys
import json
import time
from datetime import datetime

# 필요한 라이브러리들 확인
try:
    from rank_bm25 import BM25Okapi
    print("[OK] rank-bm25 라이브러리 사용 가능")
except ImportError:
    print("[ERROR] rank-bm25 라이브러리 설치 필요: pip install rank-bm25")
    sys.exit(1)

try:
    from konlpy.tag import Okt
    konlpy_available = True
    print("[OK] KoNLPy 라이브러리 사용 가능")
except ImportError:
    konlpy_available = False
    print("[WARNING] KoNLPy 라이브러리 없음. 기본 토큰화 사용")

try:
    import chromadb
    print("[OK] ChromaDB 사용 가능")
except ImportError:
    print("[ERROR] ChromaDB 설치 필요")

def test_korean_tokenization():
    """한국어 토큰화 테스트"""
    print("\n=== 한국어 토큰화 테스트 ===")

    # 기본 토큰화 (정규식 기반)
    import re

    def simple_tokenize(text):
        # 변수 패턴 제거
        text = re.sub(r'#\{[^}]+\}', '', text)
        # 한글 단어 추출 (2글자 이상)
        korean_tokens = re.findall(r'[가-힣]{2,}', text)
        # 영문 단어 추출 (2글자 이상)
        english_tokens = re.findall(r'[a-zA-Z]{2,}', text)
        # 숫자 추출
        number_tokens = re.findall(r'\d+', text)

        return korean_tokens + english_tokens + number_tokens

    test_texts = [
        "안녕하세요 #{고객명}님, 주문하신 상품이 배송 완료되었습니다.",
        "카카오톡 알림톡 템플릿 정책을 준수해야 합니다.",
        "영업시간은 평일 09:00~18:00입니다. 문의사항이 있으시면 연락주세요.",
        "이벤트 참여 감사합니다! 당첨자 발표는 #{발표일}에 진행됩니다."
    ]

    for i, text in enumerate(test_texts, 1):
        tokens = simple_tokenize(text)
        print(f"{i}. 원본: {text}")
        print(f"   토큰: {tokens} ({len(tokens)}개)")

    return True

def test_bm25_basic():
    """기본 BM25 테스트"""
    print("\n=== BM25 기본 테스트 ===")

    # 샘플 문서들
    documents = [
        "배송 알림 템플릿 주문 상품 배송 완료",
        "주문 확인 메시지 결제 완료 안내",
        "회원 가입 축하 메시지 환영",
        "이벤트 당첨 안내 축하 선물",
        "정책 준수 가이드라인 알림톡 템플릿",
        "금지된 내용 확인 검토 필요"
    ]

    # 간단한 토큰화
    import re
    def tokenize(text):
        return re.findall(r'[가-힣]{2,}', text)

    # 문서 토큰화
    tokenized_docs = [tokenize(doc) for doc in documents]

    # BM25 모델 생성
    try:
        bm25 = BM25Okapi(tokenized_docs)
        print(f"BM25 모델 생성 완료: {len(documents)}개 문서")

        # 테스트 쿼리
        test_queries = ["배송 알림", "주문 확인", "정책 준수"]

        for query in test_queries:
            query_tokens = tokenize(query)
            scores = bm25.get_scores(query_tokens)

            # 상위 결과
            scored_docs = list(zip(documents, scores))
            scored_docs.sort(key=lambda x: x[1], reverse=True)

            print(f"\n쿼리: '{query}' (토큰: {query_tokens})")
            for i, (doc, score) in enumerate(scored_docs[:3], 1):
                print(f"  {i}. {doc} (점수: {score:.3f})")

        return True

    except Exception as e:
        print(f"BM25 테스트 실패: {e}")
        return False

def test_data_files():
    """데이터 파일 존재 확인"""
    print("\n=== 데이터 파일 확인 ===")

    files_to_check = [
        "data/kakao_template_vectordb_data.json",
        "data/cleaned_policies/audit.md",
        "data/cleaned_policies/content-guide.md"
    ]

    available_files = []

    for file_path in files_to_check:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"[OK] {file_path} ({size:,} bytes)")
            available_files.append(file_path)
        else:
            print(f"[MISSING] {file_path} (없음)")

    # 템플릿 데이터 로드 테스트
    template_file = "data/kakao_template_vectordb_data.json"
    if os.path.exists(template_file):
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            template_count = len(data) if isinstance(data, list) else 0
            print(f"템플릿 데이터: {template_count}개")

            if template_count > 0:
                # 첫 번째 템플릿 확인
                first_template = data[0] if isinstance(data, list) else data
                print(f"첫 번째 템플릿 구조: {list(first_template.keys()) if isinstance(first_template, dict) else 'Unknown'}")

        except Exception as e:
            print(f"템플릿 데이터 로드 실패: {e}")

    # 정책 파일 개수 확인
    policy_dir = "data/cleaned_policies"
    if os.path.exists(policy_dir):
        policy_files = [f for f in os.listdir(policy_dir) if f.endswith('.md')]
        print(f"정책 파일: {len(policy_files)}개 ({', '.join(policy_files)})")

    return len(available_files)

def performance_test():
    """간단한 성능 테스트"""
    print("\n=== 성능 테스트 ===")

    # 대량 문서 생성 (시뮬레이션)
    doc_templates = [
        "배송 알림 주문 상품 완료",
        "결제 확인 메시지 안내",
        "회원 가입 환영 축하",
        "이벤트 당첨 선물 안내",
        "쿠폰 할인 혜택 제공",
        "적립금 포인트 적립"
    ]

    # 1000개 문서 생성
    documents = []
    for i in range(1000):
        base_doc = doc_templates[i % len(doc_templates)]
        documents.append(f"{base_doc} {i}번째 문서")

    # 토큰화
    import re
    def tokenize(text):
        return re.findall(r'[가-힣a-zA-Z0-9]{2,}', text)

    start_time = time.time()
    tokenized_docs = [tokenize(doc) for doc in documents]
    tokenize_time = time.time() - start_time

    print(f"1000개 문서 토큰화: {tokenize_time:.3f}초")

    # BM25 인덱스 구축
    start_time = time.time()
    bm25 = BM25Okapi(tokenized_docs)
    index_time = time.time() - start_time

    print(f"BM25 인덱스 구축: {index_time:.3f}초")

    # 검색 성능 테스트
    test_queries = ["배송", "결제", "회원", "이벤트", "쿠폰"]

    total_search_time = 0
    for query in test_queries:
        query_tokens = tokenize(query)

        start_time = time.time()
        scores = bm25.get_scores(query_tokens)
        search_time = time.time() - start_time

        total_search_time += search_time

        # 상위 5개 결과
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:5]
        avg_top_score = sum(scores[i] for i in top_indices) / 5

        print(f"쿼리 '{query}': {search_time*1000:.2f}ms, 평균 점수: {avg_top_score:.3f}")

    print(f"평균 검색 시간: {total_search_time/len(test_queries)*1000:.2f}ms")

    return True

def main():
    """메인 테스트 실행"""
    print("하이브리드 검색 시스템 기본 테스트")
    print("=" * 50)

    test_results = {}

    # 1. 한국어 토큰화 테스트
    try:
        test_results['tokenization'] = test_korean_tokenization()
    except Exception as e:
        print(f"토큰화 테스트 실패: {e}")
        test_results['tokenization'] = False

    # 2. BM25 기본 테스트
    try:
        test_results['bm25_basic'] = test_bm25_basic()
    except Exception as e:
        print(f"BM25 테스트 실패: {e}")
        test_results['bm25_basic'] = False

    # 3. 데이터 파일 확인
    try:
        test_results['data_files'] = test_data_files()
    except Exception as e:
        print(f"데이터 파일 테스트 실패: {e}")
        test_results['data_files'] = 0

    # 4. 성능 테스트
    try:
        test_results['performance'] = performance_test()
    except Exception as e:
        print(f"성능 테스트 실패: {e}")
        test_results['performance'] = False

    # 결과 요약
    print("\n" + "=" * 50)
    print("테스트 결과 요약")
    print("=" * 50)

    for test_name, result in test_results.items():
        status = "[OK] 성공" if result else "[FAIL] 실패"
        if test_name == 'data_files':
            status = f"[INFO] {result}개 파일 사용 가능"
        print(f"{test_name}: {status}")

    # 환경 정보
    print(f"\n환경 정보:")
    print(f"  - Python: {sys.version}")
    print(f"  - KoNLPy: {'사용 가능' if konlpy_available else '사용 불가'}")
    print(f"  - 현재 디렉토리: {os.getcwd()}")

    print("\n기본 테스트 완료!")

if __name__ == "__main__":
    main()