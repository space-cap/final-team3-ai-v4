"""
캐시 통계 확인 스크립트
"""
from src.utils.performance_cache import get_cache

def check_cache_stats():
    """캐시 통계 확인"""
    cache = get_cache()
    stats = cache.get_stats()

    print("성능 캐시 통계:")
    print("=" * 30)
    print(f"총 캐시 항목: {stats['total_items']}")
    print(f"캐시 히트: {stats['hits']}")
    print(f"캐시 미스: {stats['misses']}")
    print(f"히트율: {stats['hit_rate']}")
    print(f"저장된 항목: {stats['cache_saves']}")

    if stats['total_items'] > 0:
        print("\n캐시 효과:")
        if stats['hits'] > 0:
            print(f"- {stats['hits']}번의 캐시 히트로 LLM 호출 절약")
        else:
            print("- 아직 캐시 효과 없음 (모든 요청이 새로운 요청)")
    else:
        print("\n캐시 항목이 없습니다.")

if __name__ == "__main__":
    check_cache_stats()