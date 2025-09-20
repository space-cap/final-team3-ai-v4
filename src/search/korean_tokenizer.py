#!/usr/bin/env python3
"""
한국어 토큰화 모듈
BM25 검색을 위한 한국어 텍스트 전처리 및 토큰화
"""

import re
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class KoreanTokenizer:
    """
    한국어 텍스트 토큰화 클래스
    KoNLPy 없이도 기본적인 한국어 토큰화 지원
    """

    def __init__(self, use_konlpy: bool = True):
        """
        토큰화 초기화

        Args:
            use_konlpy: KoNLPy 사용 여부 (False시 정규식 기반 토큰화)
        """
        self.use_konlpy = use_konlpy
        self.okt = None

        if use_konlpy:
            try:
                from konlpy.tag import Okt
                self.okt = Okt()
                logger.info("KoNLPy Okt 토큰화 엔진 초기화 완료")
            except ImportError:
                logger.warning("KoNLPy 설치되지 않음. 정규식 기반 토큰화 사용")
                self.use_konlpy = False
            except Exception as e:
                logger.warning(f"KoNLPy 초기화 실패: {e}. 정규식 기반 토큰화 사용")
                self.use_konlpy = False

    def tokenize(self, text: str) -> List[str]:
        """
        텍스트를 토큰화

        Args:
            text: 토큰화할 텍스트

        Returns:
            토큰 리스트
        """
        if not text or not text.strip():
            return []

        # 텍스트 정리
        cleaned_text = self._clean_text(text)

        if self.use_konlpy and self.okt:
            return self._konlpy_tokenize(cleaned_text)
        else:
            return self._regex_tokenize(cleaned_text)

    def _clean_text(self, text: str) -> str:
        """
        텍스트 전처리

        Args:
            text: 원본 텍스트

        Returns:
            정리된 텍스트
        """
        # 변수 패턴 제거 (#{변수명} 형태)
        text = re.sub(r'#\{[^}]+\}', '', text)

        # 특수문자 정리 (한글, 영문, 숫자, 공백만 유지)
        text = re.sub(r'[^\w\s가-힣]', ' ', text)

        # 연속된 공백을 하나로
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _konlpy_tokenize(self, text: str) -> List[str]:
        """
        KoNLPy를 사용한 형태소 분석 토큰화

        Args:
            text: 정리된 텍스트

        Returns:
            형태소 토큰 리스트
        """
        try:
            # 명사, 동사, 형용사, 부사만 추출
            morphs = self.okt.pos(text, stem=True)

            # 의미있는 형태소만 필터링
            meaningful_pos = ['Noun', 'Verb', 'Adjective', 'Adverb']
            tokens = [
                morph[0] for morph in morphs
                if morph[1] in meaningful_pos and len(morph[0]) > 1
            ]

            return tokens

        except Exception as e:
            logger.warning(f"KoNLPy 토큰화 실패: {e}. 정규식 기반으로 전환")
            return self._regex_tokenize(text)

    def _regex_tokenize(self, text: str) -> List[str]:
        """
        정규식 기반 토큰화 (KoNLPy 대안)

        Args:
            text: 정리된 텍스트

        Returns:
            토큰 리스트
        """
        # 한글 단어 (2글자 이상)
        korean_tokens = re.findall(r'[가-힣]{2,}', text)

        # 영문 단어 (2글자 이상)
        english_tokens = re.findall(r'[a-zA-Z]{2,}', text)

        # 숫자 (1글자 이상)
        number_tokens = re.findall(r'\d+', text)

        # 모든 토큰 결합
        all_tokens = korean_tokens + english_tokens + number_tokens

        # 중복 제거 및 정렬
        return list(set(all_tokens))

    def get_word_frequency(self, tokens: List[str]) -> dict:
        """
        토큰 빈도수 계산

        Args:
            tokens: 토큰 리스트

        Returns:
            토큰별 빈도수 딕셔너리
        """
        frequency = {}
        for token in tokens:
            frequency[token] = frequency.get(token, 0) + 1
        return frequency


class PolicyTextPreprocessor:
    """
    정책 문서 텍스트 전처리 클래스
    """

    def __init__(self):
        self.tokenizer = KoreanTokenizer()

    def preprocess_template(self, template_text: str) -> dict:
        """
        템플릿 텍스트 전처리

        Args:
            template_text: 템플릿 원본 텍스트

        Returns:
            전처리된 정보 딕셔너리
        """
        # 원본 텍스트 보존
        original = template_text

        # 변수 추출
        variables = re.findall(r'#\{([^}]+)\}', template_text)

        # 토큰화
        tokens = self.tokenizer.tokenize(template_text)

        # 토큰 빈도수
        word_freq = self.tokenizer.get_word_frequency(tokens)

        return {
            'original': original,
            'tokens': tokens,
            'variables': variables,
            'word_frequency': word_freq,
            'token_count': len(tokens),
            'unique_token_count': len(set(tokens))
        }

    def preprocess_policy(self, policy_text: str) -> dict:
        """
        정책 문서 전처리

        Args:
            policy_text: 정책 문서 텍스트

        Returns:
            전처리된 정보 딕셔너리
        """
        # 마크다운 헤더 제거
        text = re.sub(r'^#+\s*', '', policy_text, flags=re.MULTILINE)

        # 리스트 마커 제거
        text = re.sub(r'^\s*[-*+]\s*', '', text, flags=re.MULTILINE)

        # 토큰화
        tokens = self.tokenizer.tokenize(text)

        # 키워드 추출 (빈도수 기반)
        word_freq = self.tokenizer.get_word_frequency(tokens)
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]

        return {
            'original': policy_text,
            'cleaned': text,
            'tokens': tokens,
            'keywords': [kw[0] for kw in keywords],
            'word_frequency': word_freq,
            'token_count': len(tokens)
        }


def test_tokenizer():
    """토큰화 테스트 함수"""

    print("=== 한국어 토큰화 테스트 ===")

    # 테스트 텍스트
    test_texts = [
        "안녕하세요 #{고객명}님, 주문하신 상품이 배송 완료되었습니다.",
        "카카오톡 알림톡 템플릿 정책을 준수해야 합니다.",
        "영업시간은 평일 09:00~18:00입니다. 문의사항이 있으시면 연락주세요.",
        "Special characters !@#$%^&*() should be removed properly."
    ]

    tokenizer = KoreanTokenizer()
    preprocessor = PolicyTextPreprocessor()

    for i, text in enumerate(test_texts, 1):
        print(f"\n{i}. 원본: {text}")

        # 기본 토큰화
        tokens = tokenizer.tokenize(text)
        print(f"   토큰: {tokens}")

        # 템플릿 전처리
        result = preprocessor.preprocess_template(text)
        print(f"   변수: {result['variables']}")
        print(f"   토큰수: {result['token_count']}")


if __name__ == "__main__":
    test_tokenizer()