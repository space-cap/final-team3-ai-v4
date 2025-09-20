"""
상세 성능 테스트 - 다양한 시나리오로 병목 지점 정확히 측정
"""
import time
import json
import requests
import statistics
from typing import Dict, List

# 다양한 복잡도의 테스트 케이스
DETAILED_TEST_CASES = [
    {
        "name": "간단한_템플릿",
        "complexity": "low",
        "request": {
            "user_request": "수강 신청 완료 안내",
            "business_type": "교육",
            "service_type": "신청",
            "target_audience": "수강생",
            "tone": "정중한",
            "required_variables": ["수신자명", "강의명"],
            "additional_requirements": "간단명료하게"
        }
    },
    {
        "name": "중간_복잡도_템플릿",
        "complexity": "medium",
        "request": {
            "user_request": "병원 예약 확인 및 준비사항 안내 메시지",
            "business_type": "의료",
            "service_type": "예약",
            "target_audience": "환자",
            "tone": "친근한",
            "required_variables": ["환자명", "진료과", "예약일시", "담당의"],
            "additional_requirements": "준비사항 포함"
        }
    },
    {
        "name": "복잡한_템플릿",
        "complexity": "high",
        "request": {
            "user_request": "온라인 쇼핑몰 주문 완료 후 배송 정보, 교환/환불 정책, 고객센터 연락처, 적립금 안내를 포함한 상세한 메시지",
            "business_type": "쇼핑몰",
            "service_type": "주문",
            "target_audience": "고객",
            "tone": "친근한",
            "required_variables": ["고객명", "주문번호", "상품명", "배송주소", "배송예정일", "적립금"],
            "additional_requirements": "교환/환불 정책, 고객센터 정보, 적립금 상세 안내 포함"
        }
    }
]

def run_detailed_performance_test():
    """상세 성능 테스트 실행"""
    print("상세 성능 테스트 시작")
    print("=" * 60)

    results = {}

    for test_case in DETAILED_TEST_CASES:
        print(f"\n🔍 테스트 중: {test_case['name']} ({test_case['complexity']} 복잡도)")

        case_results = []

        # 각 케이스를 3회씩 실행
        for i in range(3):
            print(f"  반복 {i+1}/3...", end=" ")

            start_time = time.time()

            try:
                response = requests.post(
                    "http://localhost:8000/api/v1/templates/generate",
                    json=test_case['request'],
                    timeout=120
                )

                end_time = time.time()
                total_time = end_time - start_time

                if response.status_code == 200:
                    result_data = response.json()

                    case_result = {
                        'iteration': i + 1,
                        'success': True,
                        'total_time': total_time,
                        'template_length': len(result_data.get('template', {}).get('text', '')),
                        'compliance_score': result_data.get('compliance', {}).get('score', 0),
                        'iterations': result_data.get('workflow_info', {}).get('iterations', 0),
                        'has_performance_data': 'performance' in result_data
                    }

                    # 성능 데이터 추출 시도
                    if 'performance' in result_data:
                        perf_data = result_data['performance']
                        case_result['step_summary'] = perf_data.get('step_summary', {})
                        case_result['bottlenecks'] = perf_data.get('bottlenecks', [])

                    case_results.append(case_result)
                    print(f"✅ {total_time:.1f}초")

                else:
                    print(f"❌ HTTP {response.status_code}")
                    case_results.append({
                        'iteration': i + 1,
                        'success': False,
                        'error': f"HTTP {response.status_code}",
                        'total_time': total_time
                    })

            except Exception as e:
                end_time = time.time()
                print(f"❌ {str(e)[:50]}...")
                case_results.append({
                    'iteration': i + 1,
                    'success': False,
                    'error': str(e),
                    'total_time': end_time - start_time
                })

            # 요청 간 간격
            time.sleep(1)

        results[test_case['name']] = {
            'complexity': test_case['complexity'],
            'results': case_results
        }

    return results

def analyze_detailed_results(results: Dict) -> Dict:
    """상세 결과 분석"""
    analysis = {
        'summary': {},
        'by_complexity': {},
        'performance_trends': {},
        'recommendations': []
    }

    # 전체 요약
    all_successful = []
    for test_name, test_data in results.items():
        successful = [r for r in test_data['results'] if r.get('success', False)]
        all_successful.extend(successful)

    if all_successful:
        times = [r['total_time'] for r in all_successful]
        analysis['summary'] = {
            'total_tests': len(all_successful),
            'avg_time': statistics.mean(times),
            'median_time': statistics.median(times),
            'min_time': min(times),
            'max_time': max(times),
            'std_dev': statistics.stdev(times) if len(times) > 1 else 0
        }

    # 복잡도별 분석
    complexity_groups = {'low': [], 'medium': [], 'high': []}

    for test_name, test_data in results.items():
        complexity = test_data['complexity']
        successful = [r for r in test_data['results'] if r.get('success', False)]

        if successful:
            times = [r['total_time'] for r in successful]
            template_lengths = [r['template_length'] for r in successful]
            compliance_scores = [r['compliance_score'] for r in successful]

            complexity_groups[complexity].extend(times)

            analysis['by_complexity'][test_name] = {
                'complexity': complexity,
                'avg_time': statistics.mean(times),
                'avg_template_length': statistics.mean(template_lengths),
                'avg_compliance_score': statistics.mean(compliance_scores),
                'success_rate': len(successful) / len(test_data['results']) * 100
            }

    # 복잡도 트렌드 분석
    for complexity, times in complexity_groups.items():
        if times:
            analysis['performance_trends'][complexity] = {
                'avg_time': statistics.mean(times),
                'sample_count': len(times)
            }

    # 권장사항 생성
    recommendations = []

    # 복잡도에 따른 시간 증가 분석
    if all(complexity in analysis['performance_trends'] for complexity in ['low', 'medium', 'high']):
        low_time = analysis['performance_trends']['low']['avg_time']
        high_time = analysis['performance_trends']['high']['avg_time']

        if high_time > low_time * 2:
            recommendations.append(f"복잡한 템플릿은 간단한 템플릿보다 {high_time/low_time:.1f}배 오래 걸립니다. 복잡도별 최적화가 필요합니다.")

    # 전체 시간 분석
    if analysis['summary'].get('avg_time', 0) > 30:
        recommendations.append("평균 처리 시간이 30초를 초과합니다. LLM 호출 최적화가 시급합니다.")

    # 일관성 분석
    if analysis['summary'].get('std_dev', 0) > 10:
        recommendations.append("처리 시간의 편차가 큽니다. 안정성 개선이 필요합니다.")

    analysis['recommendations'] = recommendations

    return analysis

def generate_detailed_report(results: Dict, analysis: Dict) -> str:
    """상세 보고서 생성"""
    report_lines = []

    report_lines.append("=" * 80)
    report_lines.append("카카오톡 템플릿 생성 상세 성능 분석 보고서")
    report_lines.append("=" * 80)
    report_lines.append(f"테스트 일시: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # 전체 요약
    if 'summary' in analysis and analysis['summary']:
        summary = analysis['summary']
        report_lines.append("📊 전체 성능 요약")
        report_lines.append("-" * 50)
        report_lines.append(f"총 테스트 수: {summary['total_tests']}")
        report_lines.append(f"평균 처리 시간: {summary['avg_time']:.2f}초")
        report_lines.append(f"중간값 처리 시간: {summary['median_time']:.2f}초")
        report_lines.append(f"최소 처리 시간: {summary['min_time']:.2f}초")
        report_lines.append(f"최대 처리 시간: {summary['max_time']:.2f}초")
        report_lines.append(f"표준편차: {summary['std_dev']:.2f}초")
        report_lines.append("")

    # 복잡도별 분석
    report_lines.append("🎯 복잡도별 성능 분석")
    report_lines.append("-" * 50)

    for test_name, data in analysis['by_complexity'].items():
        report_lines.append(f"• {test_name} ({data['complexity']} 복잡도)")
        report_lines.append(f"  평균 시간: {data['avg_time']:.2f}초")
        report_lines.append(f"  평균 템플릿 길이: {data['avg_template_length']:.0f}자")
        report_lines.append(f"  평균 컴플라이언스 점수: {data['avg_compliance_score']:.1f}점")
        report_lines.append(f"  성공률: {data['success_rate']:.1f}%")
        report_lines.append("")

    # 복잡도 트렌드
    if analysis['performance_trends']:
        report_lines.append("📈 복잡도별 처리 시간 트렌드")
        report_lines.append("-" * 50)

        for complexity, trend_data in analysis['performance_trends'].items():
            report_lines.append(f"{complexity.upper()} 복잡도: {trend_data['avg_time']:.2f}초 (샘플 {trend_data['sample_count']}개)")
        report_lines.append("")

    # 권장사항
    if analysis['recommendations']:
        report_lines.append("💡 성능 개선 권장사항")
        report_lines.append("-" * 50)
        for i, rec in enumerate(analysis['recommendations'], 1):
            report_lines.append(f"{i}. {rec}")
        report_lines.append("")

    # 세부 테스트 결과
    report_lines.append("📋 세부 테스트 결과")
    report_lines.append("-" * 50)

    for test_name, test_data in results.items():
        report_lines.append(f"\n{test_name} ({test_data['complexity']} 복잡도):")

        for result in test_data['results']:
            if result.get('success', False):
                report_lines.append(f"  반복 {result['iteration']}: {result['total_time']:.2f}초 "
                                  f"(길이: {result['template_length']}자, 점수: {result['compliance_score']})")
            else:
                report_lines.append(f"  반복 {result['iteration']}: 실패 - {result.get('error', 'Unknown error')}")

    return "\n".join(report_lines)

def main():
    """메인 실행 함수"""
    print("상세 성능 테스트를 시작합니다...")

    # 서버 연결 확인
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code != 200:
            print("❌ 서버에 연결할 수 없습니다.")
            return
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        return

    # 성능 테스트 실행
    results = run_detailed_performance_test()

    # 결과 분석
    analysis = analyze_detailed_results(results)

    # 보고서 생성
    report = generate_detailed_report(results, analysis)

    print("\n" + "="*80)
    print("상세 성능 분석 완료!")
    print("="*80)
    print(report)

    # 결과를 JSON 파일로 저장
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    filename = f"detailed_performance_results_{timestamp}.json"

    output_data = {
        'test_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'test_cases': DETAILED_TEST_CASES,
        'results': results,
        'analysis': analysis
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n📄 상세 결과가 {filename}에 저장되었습니다.")

if __name__ == "__main__":
    main()