"""
성능 개선 전후 비교 테스트
"""
import time
import requests
import json

def test_performance_before_after():
    """성능 개선 전후 비교"""

    # 테스트 케이스
    test_request = {
        "user_request": "온라인 강의 수강 신청이 완료된 후 강의 일정과 접속 방법을 안내하는 메시지",
        "business_type": "교육",
        "service_type": "신청",
        "target_audience": "수강생",
        "tone": "정중한",
        "required_variables": ["수신자명", "강의명", "강의일정", "접속링크"],
        "additional_requirements": "수강 시 주의사항도 포함하고 버튼 추가"
    }

    url = "http://localhost:8000/api/v1/templates/generate"

    print("성능 개선 효과 테스트 시작")
    print("=" * 50)

    results = []

    # 5회 테스트 실행
    for i in range(5):
        print(f"테스트 {i+1}/5 실행 중...", end=" ")

        start_time = time.time()

        try:
            response = requests.post(url, json=test_request, timeout=120)
            end_time = time.time()

            total_time = end_time - start_time

            if response.status_code == 200:
                result_data = response.json()

                # 캐시 사용 여부 확인 (로그에서)
                cache_used = "cached" in str(result_data).lower()

                results.append({
                    'test_number': i + 1,
                    'total_time': total_time,
                    'success': True,
                    'template_length': len(result_data.get('template', {}).get('text', '')),
                    'compliance_score': result_data.get('compliance', {}).get('score', 0),
                    'cache_used': cache_used
                })

                print(f"✅ {total_time:.2f}초")

            else:
                print(f"❌ HTTP {response.status_code}")
                results.append({
                    'test_number': i + 1,
                    'total_time': total_time,
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                })

        except Exception as e:
            end_time = time.time()
            total_time = end_time - start_time
            print(f"❌ {str(e)[:30]}...")
            results.append({
                'test_number': i + 1,
                'total_time': total_time,
                'success': False,
                'error': str(e)
            })

        # 테스트 간 간격
        if i < 4:
            time.sleep(2)

    # 결과 분석
    successful_results = [r for r in results if r.get('success', False)]

    if successful_results:
        times = [r['total_time'] for r in successful_results]

        print("\n" + "=" * 50)
        print("📊 성능 테스트 결과")
        print("=" * 50)

        print(f"성공한 테스트: {len(successful_results)}/5")
        print(f"평균 처리 시간: {sum(times)/len(times):.2f}초")
        print(f"최빠른 시간: {min(times):.2f}초")
        print(f"최느린 시간: {max(times):.2f}초")

        # 개별 결과
        print("\n📋 개별 테스트 결과:")
        for result in results:
            if result['success']:
                cache_status = "🟢 캐시됨" if result.get('cache_used', False) else "🔵 신규"
                print(f"  테스트 {result['test_number']}: {result['total_time']:.2f}초 {cache_status}")
            else:
                print(f"  테스트 {result['test_number']}: 실패 - {result.get('error', 'Unknown')}")

        # 성능 개선 분석
        baseline_time = 39.02  # 이전 평균 시간
        current_avg = sum(times) / len(times)
        improvement = ((baseline_time - current_avg) / baseline_time) * 100

        print(f"\n🚀 성능 개선 분석:")
        print(f"이전 평균: {baseline_time:.2f}초")
        print(f"현재 평균: {current_avg:.2f}초")

        if improvement > 0:
            print(f"개선율: {improvement:.1f}% (⬇️ {baseline_time - current_avg:.2f}초 단축)")
        else:
            print(f"변화: {abs(improvement):.1f}% (⬆️ {current_avg - baseline_time:.2f}초 증가)")

        # 목표 달성 여부
        if current_avg <= 25:
            print("🎯 Phase 1 목표 달성! (25초 이하)")
        elif current_avg <= 30:
            print("✅ 단기 목표에 근접 (30초 이하)")
        else:
            print("⚠️  추가 최적화 필요")

    else:
        print("❌ 모든 테스트가 실패했습니다.")

    return results

if __name__ == "__main__":
    # 서버 연결 확인
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=10)
        if health_response.status_code == 200:
            print("✅ 서버 연결 확인됨")
            test_performance_before_after()
        else:
            print("❌ 서버가 응답하지 않습니다.")
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        print("python run_server.py로 서버를 먼저 시작해주세요.")