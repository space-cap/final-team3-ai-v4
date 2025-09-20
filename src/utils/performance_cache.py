"""
성능 향상을 위한 캐싱 시스템
"""
import hashlib
import json
import time
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class PerformanceCache:
    """메모리 기반 성능 캐시"""

    def __init__(self, max_items: int = 1000, ttl_seconds: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_items = max_items
        self.ttl_seconds = ttl_seconds

        # 통계
        self.hits = 0
        self.misses = 0
        self.cache_saves = 0

    def _generate_key(self, prefix: str, **kwargs) -> str:
        """캐시 키 생성"""
        key_data = json.dumps(kwargs, sort_keys=True, ensure_ascii=False)
        hash_key = hashlib.md5(key_data.encode()).hexdigest()
        return f"{prefix}:{hash_key[:16]}"

    def _is_expired(self, item: Dict[str, Any]) -> bool:
        """캐시 만료 확인"""
        return time.time() - item['timestamp'] > self.ttl_seconds

    def _cleanup_expired(self):
        """만료된 캐시 항목 정리"""
        current_time = time.time()
        expired_keys = [
            key for key, item in self.cache.items()
            if current_time - item['timestamp'] > self.ttl_seconds
        ]
        for key in expired_keys:
            del self.cache[key]

    def _enforce_max_items(self):
        """최대 항목 수 제한"""
        if len(self.cache) > self.max_items:
            # LRU: 가장 오래된 항목부터 제거
            sorted_items = sorted(
                self.cache.items(),
                key=lambda x: x[1]['timestamp']
            )
            items_to_remove = len(self.cache) - self.max_items + 100  # 여유분
            for key, _ in sorted_items[:items_to_remove]:
                del self.cache[key]

    def get(self, prefix: str, **kwargs) -> Optional[Any]:
        """캐시에서 데이터 조회"""
        key = self._generate_key(prefix, **kwargs)

        if key in self.cache:
            item = self.cache[key]
            if not self._is_expired(item):
                self.hits += 1
                item['last_accessed'] = time.time()  # 액세스 시간 업데이트
                logger.debug(f"Cache hit for {prefix}")
                return item['data']
            else:
                # 만료된 항목 제거
                del self.cache[key]

        self.misses += 1
        logger.debug(f"Cache miss for {prefix}")
        return None

    def set(self, prefix: str, data: Any, **kwargs):
        """캐시에 데이터 저장"""
        key = self._generate_key(prefix, **kwargs)

        self.cache[key] = {
            'data': data,
            'timestamp': time.time(),
            'last_accessed': time.time()
        }

        self.cache_saves += 1
        logger.debug(f"Cache set for {prefix}")

        # 정리 작업
        if len(self.cache) % 100 == 0:  # 100개마다 정리
            self._cleanup_expired()
            self._enforce_max_items()

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'total_items': len(self.cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.1f}%",
            'cache_saves': self.cache_saves
        }

    def clear(self):
        """캐시 전체 삭제"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        self.cache_saves = 0

# 전역 캐시 인스턴스
_global_cache = PerformanceCache()

def get_cache() -> PerformanceCache:
    """전역 캐시 인스턴스 반환"""
    return _global_cache

# 캐시 데코레이터
def cache_result(prefix: str, ttl_seconds: int = 3600):
    """함수 결과를 캐시하는 데코레이터"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache = get_cache()

            # 캐시 키 생성용 파라미터
            cache_params = {
                'func_name': func.__name__,
                'args': str(args),
                'kwargs': str(kwargs)
            }

            # 캐시 조회
            cached_result = cache.get(prefix, **cache_params)
            if cached_result is not None:
                return cached_result

            # 캐시 미스 - 함수 실행
            result = func(*args, **kwargs)

            # 결과 캐싱
            cache.set(prefix, result, **cache_params)

            return result
        return wrapper
    return decorator

# 특정 용도별 캐시 함수들
class SpecificCaches:
    """특정 용도별 캐시 유틸리티"""

    @staticmethod
    def get_policy_search_result(business_type: str, service_type: str, query: str) -> Optional[Dict]:
        """정책 검색 결과 캐시 조회"""
        cache = get_cache()
        return cache.get('policy_search',
                        business_type=business_type,
                        service_type=service_type,
                        query=query[:100])  # 쿼리 길이 제한

    @staticmethod
    def set_policy_search_result(business_type: str, service_type: str, query: str, result: Dict):
        """정책 검색 결과 캐시 저장"""
        cache = get_cache()
        cache.set('policy_search', result,
                 business_type=business_type,
                 service_type=service_type,
                 query=query[:100])

    @staticmethod
    def get_request_analysis(user_request: str) -> Optional[Dict]:
        """요청 분석 결과 캐시 조회"""
        cache = get_cache()
        request_hash = hashlib.md5(user_request.encode()).hexdigest()
        return cache.get('request_analysis', request_hash=request_hash)

    @staticmethod
    def set_request_analysis(user_request: str, analysis: Dict):
        """요청 분석 결과 캐시 저장"""
        cache = get_cache()
        request_hash = hashlib.md5(user_request.encode()).hexdigest()
        cache.set('request_analysis', analysis, request_hash=request_hash)

    @staticmethod
    def get_template_generation(analysis_key: str, policy_key: str) -> Optional[Dict]:
        """템플릿 생성 결과 캐시 조회"""
        cache = get_cache()
        return cache.get('template_generation',
                        analysis_key=analysis_key,
                        policy_key=policy_key)

    @staticmethod
    def set_template_generation(analysis_key: str, policy_key: str, template: Dict):
        """템플릿 생성 결과 캐시 저장"""
        cache = get_cache()
        cache.set('template_generation', template,
                 analysis_key=analysis_key,
                 policy_key=policy_key)