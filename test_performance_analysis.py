"""
템플릿 생성 성능 테스트 및 분석 스크립트
실제 API 요청을 통해 단계별 성능을 측정하고 병목 지점을 식별합니다.
"""
import time
import json
import requests
import statistics
from datetime import datetime
from typing import List, Dict, Any
import asyncio
import aiohttp

# 테스트 케이스 정의
TEST_CASES = [
    {
        "name": "간단한_교육_템플릿",
        "request": {
            "user_request": "온라인 강의 수강 신청이 완료되었음을 알리는 메시지",
            "business_type": "교육",
            "service_type": "신청",
            "target_audience": "수강생",
            "tone": "정중한",
            "required_variables": ["수신자명", "강의명"],
            "additional_requirements": "간단하고 명확하게"
        }
    },
    {
        "name": "복잡한_의료_템플릿",
        "request": {
            "user_request": "병원 예약 확인 및 진료 전 준비사항, 주의사항, 위치 안내를 포함한 상세한 메시지",
            "business_type": "의료",
            "service_type": "예약",
            "target_audience": "환자",
            "tone": "친근한",
            "required_variables": ["환자명", "진료과", "예약일시", "담당의", "병원주소"],
            "additional_requirements": "진료 전 준비사항과 주의사항 포함, 버튼 추가 필요"
        }
    },
    {
        "name": "쇼핑몰_주문_템플릿",
        "request": {
            "user_request": "온라인 쇼핑몰 주문 완료 후 배송 정보와 교환/환불 정책을 안내하는 메시지",
            "business_type": "쇼핑몰",
            "service_type": "주문",
            "target_audience": "고객",
            "tone": "친근한",
            "required_variables": ["고객명", "주문번호", "상품명", "배송주소"],
            "additional_requirements": "교환/환불 정책 포함"
        }
    },
    {
        "name": "금융_서비스_템플릿",
        "request": {
            "user_request": "대출 신청 승인 결과와 다음 단계 안내를 포함한 메시지",
            "business_type": "금융",
            "service_type": "신청",
            "target_audience": "고객",
            "tone": "정중한",
            "required_variables": ["고객명", "대출상품명", "승인금액", "금리"],
            "additional_requirements": "다음 단계 안내 포함"
        }
    },
    {
        "name": "음식점_예약_템플릿",
        "request": {
            "user_request": "레스토랑 예약 확인 및 방문 시 주의사항 안내 메시지",
            "business_type": "음식점",
            "service_type": "예약",
            "target_audience": "고객",
            "tone": "친근한",
            "required_variables": ["고객명", "예약일시", "인원수", "매장명"],
            "additional_requirements": "주차 정보 및 방문 시 주의사항 포함"
        }
    }
]

class PerformanceTestRunner:
    """성능 테스트 실행기"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_endpoint = f"{base_url}/api/v1/templates/generate"
        self.results = []

    def run_single_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """단일 테스트 케이스 실행"""
        print(f"테스트 실행 중: {test_case['name']}")

        start_time = time.time()

        try:
            response = requests.post(
                self.api_endpoint,
                json=test_case['request'],
                headers={'Content-Type': 'application/json'},
                timeout=120  # 2분 타임아웃
            )

            end_time = time.time()
            total_time = end_time - start_time

            if response.status_code == 200:
                result_data = response.json()

                # 성능 데이터 추출
                performance_data = result_data.get('performance', {})

                return {
                    'test_name': test_case['name'],
                    'success': True,
                    'total_time': total_time,
                    'status_code': response.status_code,
                    'template_length': len(result_data.get('template', {}).get('text', '')),
                    'compliance_score': result_data.get('compliance', {}).get('score', 0),
                    'iterations': result_data.get('workflow_info', {}).get('iterations', 0),
                    'performance_data': performance_data,
                    'step_timings': performance_data.get('step_timings', []),
                    'bottlenecks': performance_data.get('bottlenecks', []),
                    'recommendations': performance_data.get('recommendations', [])
                }
            else:
                return {
                    'test_name': test_case['name'],
                    'success': False,
                    'total_time': total_time,
                    'status_code': response.status_code,
                    'error': response.text
                }

        except Exception as e:
            end_time = time.time()
            return {
                'test_name': test_case['name'],
                'success': False,
                'total_time': end_time - start_time,
                'error': str(e)
            }

    def run_all_tests(self, iterations: int = 3) -> List[Dict[str, Any]]:
        """모든 테스트 케이스를 여러 번 실행"""
        print(f"성능 테스트 시작 - {len(TEST_CASES)}개 케이스 x {iterations}회 반복")

        all_results = []

        for i in range(iterations):
            print(f"\n=== 반복 {i+1}/{iterations} ===")

            for test_case in TEST_CASES:
                result = self.run_single_test(test_case)
                result['iteration'] = i + 1
                all_results.append(result)

                # 간격 두기 (서버 부하 방지)
                time.sleep(2)

        self.results = all_results
        return all_results

    def analyze_results(self) -> Dict[str, Any]:
        """테스트 결과 분석"""
        if not self.results:
            return {}

        # 성공한 테스트만 분석
        successful_results = [r for r in self.results if r.get('success', False)]

        if not successful_results:
            return {'error': 'No successful tests to analyze'}

        # 전체 통계
        total_times = [r['total_time'] for r in successful_results]

        analysis = {
            'test_summary': {
                'total_tests': len(self.results),
                'successful_tests': len(successful_results),
                'success_rate': len(successful_results) / len(self.results) * 100,
                'average_total_time': statistics.mean(total_times),
                'median_total_time': statistics.median(total_times),
                'max_total_time': max(total_times),
                'min_total_time': min(total_times),
                'std_dev_total_time': statistics.stdev(total_times) if len(total_times) > 1 else 0
            }
        }

        # 테스트 케이스별 분석
        analysis['by_test_case'] = {}
        for test_case in TEST_CASES:
            case_results = [r for r in successful_results if r['test_name'] == test_case['name']]
            if case_results:
                case_times = [r['total_time'] for r in case_results]
                analysis['by_test_case'][test_case['name']] = {
                    'avg_time': statistics.mean(case_times),
                    'min_time': min(case_times),
                    'max_time': max(case_times),
                    'avg_compliance_score': statistics.mean([r.get('compliance_score', 0) for r in case_results]),
                    'avg_iterations': statistics.mean([r.get('iterations', 0) for r in case_results])
                }

        # 단계별 분석
        step_analysis = {}
        for result in successful_results:
            step_timings = result.get('step_timings', [])
            for step in step_timings:
                step_name = step.get('step_name', 'unknown')
                duration = step.get('duration_seconds', 0)

                if step_name not in step_analysis:
                    step_analysis[step_name] = []
                step_analysis[step_name].append(duration)

        analysis['step_performance'] = {}
        for step_name, durations in step_analysis.items():
            if durations:
                analysis['step_performance'][step_name] = {
                    'avg_time': statistics.mean(durations),
                    'min_time': min(durations),
                    'max_time': max(durations),
                    'call_count': len(durations),
                    'total_time': sum(durations),
                    'percentage_of_total': 0  # 나중에 계산
                }

        # 각 단계의 전체 시간 대비 비율 계산
        total_step_time = sum(sum(durations) for durations in step_analysis.values())
        for step_name in analysis['step_performance']:
            step_total = analysis['step_performance'][step_name]['total_time']
            analysis['step_performance'][step_name]['percentage_of_total'] = (step_total / total_step_time * 100) if total_step_time > 0 else 0

        # 병목 지점 식별
        bottlenecks = []
        for step_name, data in analysis['step_performance'].items():
            if data['percentage_of_total'] > 20:  # 전체의 20% 이상
                bottlenecks.append({
                    'step_name': step_name,
                    'avg_time': data['avg_time'],
                    'percentage': data['percentage_of_total'],
                    'severity': 'high' if data['percentage_of_total'] > 40 else 'medium'
                })

        analysis['bottlenecks'] = sorted(bottlenecks, key=lambda x: x['percentage'], reverse=True)

        # 권장사항 생성
        recommendations = []

        # 전체 시간이 긴 경우
        if analysis['test_summary']['average_total_time'] > 30:
            recommendations.append("평균 처리 시간이 30초를 초과합니다. 전반적인 성능 최적화가 필요합니다.")

        # 특정 단계가 병목인 경우
        for bottleneck in analysis['bottlenecks']:
            if bottleneck['step_name'] in ['template_generation', 'compliance_check']:
                recommendations.append(f"{bottleneck['step_name']} 단계가 {bottleneck['percentage']:.1f}%의 시간을 차지합니다. LLM 호출 최적화를 고려하세요.")
            elif bottleneck['step_name'] == 'policy_retrieval':
                recommendations.append(f"정책 검색이 {bottleneck['percentage']:.1f}%의 시간을 차지합니다. 벡터 데이터베이스 최적화나 캐싱을 고려하세요.")

        # 성공률이 낮은 경우
        if analysis['test_summary']['success_rate'] < 90:
            recommendations.append(f"성공률이 {analysis['test_summary']['success_rate']:.1f}%로 낮습니다. 에러 처리 및 안정성 개선이 필요합니다.")

        analysis['recommendations'] = recommendations

        return analysis

    def generate_report(self) -> str:
        """성능 분석 보고서 생성"""
        analysis = self.analyze_results()

        if 'error' in analysis:
            return f"분석 실패: {analysis['error']}"

        report = []
        report.append("=" * 80)
        report.append("템플릿 생성 성능 분석 보고서")
        report.append("=" * 80)
        report.append(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # 전체 요약
        summary = analysis['test_summary']
        report.append("📊 전체 테스트 요약")
        report.append("-" * 50)
        report.append(f"총 테스트 수: {summary['total_tests']}")
        report.append(f"성공한 테스트: {summary['successful_tests']}")
        report.append(f"성공률: {summary['success_rate']:.1f}%")
        report.append(f"평균 처리 시간: {summary['average_total_time']:.2f}초")
        report.append(f"최대 처리 시간: {summary['max_total_time']:.2f}초")
        report.append(f"최소 처리 시간: {summary['min_total_time']:.2f}초")
        report.append(f"표준편차: {summary['std_dev_total_time']:.2f}초")
        report.append("")

        # 테스트 케이스별 성능
        report.append("📋 테스트 케이스별 성능")
        report.append("-" * 50)
        for test_name, data in analysis['by_test_case'].items():
            report.append(f"• {test_name}")
            report.append(f"  평균 시간: {data['avg_time']:.2f}초")
            report.append(f"  범위: {data['min_time']:.2f}초 ~ {data['max_time']:.2f}초")
            report.append(f"  평균 컴플라이언스 점수: {data['avg_compliance_score']:.1f}")
            report.append(f"  평균 반복 횟수: {data['avg_iterations']:.1f}")
            report.append("")

        # 단계별 성능
        report.append("⚡ 단계별 성능 분석")
        report.append("-" * 50)
        step_perf = analysis['step_performance']
        sorted_steps = sorted(step_perf.items(), key=lambda x: x[1]['percentage_of_total'], reverse=True)

        for step_name, data in sorted_steps:
            report.append(f"• {step_name}")
            report.append(f"  평균 시간: {data['avg_time']:.3f}초")
            report.append(f"  전체 대비: {data['percentage_of_total']:.1f}%")
            report.append(f"  호출 횟수: {data['call_count']}")
            report.append(f"  범위: {data['min_time']:.3f}초 ~ {data['max_time']:.3f}초")
            report.append("")

        # 병목 지점
        if analysis['bottlenecks']:
            report.append("🚫 주요 병목 지점")
            report.append("-" * 50)
            for bottleneck in analysis['bottlenecks']:
                severity_emoji = "🔴" if bottleneck['severity'] == 'high' else "🟡"
                report.append(f"{severity_emoji} {bottleneck['step_name']}")
                report.append(f"  평균 시간: {bottleneck['avg_time']:.3f}초")
                report.append(f"  전체 대비: {bottleneck['percentage']:.1f}%")
                report.append("")

        # 권장사항
        if analysis['recommendations']:
            report.append("💡 성능 개선 권장사항")
            report.append("-" * 50)
            for i, rec in enumerate(analysis['recommendations'], 1):
                report.append(f"{i}. {rec}")
            report.append("")

        return "\n".join(report)

    def save_detailed_results(self, filename: str = None):
        """상세 결과를 JSON 파일로 저장"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"performance_test_results_{timestamp}.json"

        analysis = self.analyze_results()

        output_data = {
            'metadata': {
                'test_date': datetime.now().isoformat(),
                'test_cases_count': len(TEST_CASES),
                'total_tests': len(self.results)
            },
            'raw_results': self.results,
            'analysis': analysis
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"상세 결과가 {filename}에 저장되었습니다.")
        return filename

def main():
    """메인 실행 함수"""
    print("카카오 템플릿 생성 성능 테스트 시작")

    # 서버 상태 확인
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code != 200:
            print("❌ 서버가 응답하지 않습니다. 서버를 먼저 시작해주세요.")
            return
        print("✅ 서버 연결 확인됨")
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        print("python run_server.py 명령으로 서버를 먼저 시작해주세요.")
        return

    # 성능 테스트 실행
    test_runner = PerformanceTestRunner()

    print(f"\n테스트 케이스:")
    for i, case in enumerate(TEST_CASES, 1):
        print(f"{i}. {case['name']} - {case['request']['business_type']}")

    # 테스트 실행
    results = test_runner.run_all_tests(iterations=2)  # 각 케이스를 2회씩 실행

    # 결과 분석 및 출력
    print("\n" + "="*80)
    print("📊 성능 테스트 완료!")
    print("="*80)

    report = test_runner.generate_report()
    print(report)

    # 상세 결과 저장
    json_file = test_runner.save_detailed_results()

    print(f"\n✅ 성능 테스트가 완료되었습니다.")
    print(f"📄 상세 결과: {json_file}")

if __name__ == "__main__":
    main()