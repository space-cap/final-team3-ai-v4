"""
간단한 성능 테스트 스크립트
"""
import time
import json
import requests

def test_single_request():
    """단일 요청 테스트"""
    url = "http://localhost:8000/api/v1/templates/generate"

    test_request = {
        "user_request": "온라인 강의 수강 신청이 완료된 후 강의 일정과 접속 방법을 안내하는 메시지",
        "business_type": "교육",
        "service_type": "신청",
        "target_audience": "수강생",
        "tone": "정중한",
        "required_variables": ["수신자명", "강의명", "강의일정", "접속링크"],
        "additional_requirements": "수강 시 주의사항도 포함하고 버튼 추가"
    }

    print("테스트 요청 전송 중...")
    start_time = time.time()

    try:
        response = requests.post(url, json=test_request, timeout=120)
        end_time = time.time()

        total_time = end_time - start_time

        print(f"총 처리 시간: {total_time:.2f}초")
        print(f"응답 상태: {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            # 성능 데이터 추출
            if 'performance' in result:
                perf_data = result['performance']
                step_summary = perf_data.get('step_summary', {})

                print("\n=== 단계별 성능 ===")
                for step_name, data in step_summary.items():
                    print(f"{step_name}: {data['avg_time']:.3f}초 (호출 {data['total_calls']}회)")

                # 병목 지점
                bottlenecks = perf_data.get('bottlenecks', [])
                if bottlenecks:
                    print("\n=== 병목 지점 ===")
                    for bn in bottlenecks:
                        print(f"{bn['step_name']}: {bn['duration_seconds']:.3f}초 ({bn['percentage_of_total']:.1f}%)")

                # 권장사항
                recommendations = perf_data.get('recommendations', [])
                if recommendations:
                    print("\n=== 권장사항 ===")
                    for rec in recommendations:
                        print(f"- {rec}")

            # 템플릿 결과
            template = result.get('template', {})
            print(f"\n생성된 템플릿 길이: {len(template.get('text', ''))}자")
            print(f"컴플라이언스 점수: {result.get('compliance', {}).get('score', 0)}")
            print(f"반복 횟수: {result.get('workflow_info', {}).get('iterations', 0)}")

        else:
            print(f"오류 응답: {response.text}")

    except Exception as e:
        print(f"요청 실패: {e}")

if __name__ == "__main__":
    # 서버 상태 확인
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=30)
        if health_response.status_code == 200:
            print("서버 연결 확인됨")
            test_single_request()
        else:
            print("서버가 응답하지 않습니다.")
    except Exception as e:
        print(f"서버 연결 실패: {e}")