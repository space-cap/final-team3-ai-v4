#!/usr/bin/env python3
"""
Claude 모델 성능 벤치마크 테스트 스크립트
Claude 3.5 Haiku vs Claude 4 모델 비교
"""

import os
import time
import json
from typing import Dict, List, Any
from dotenv import load_dotenv
import anthropic
from datetime import datetime

# .env 파일 로드
load_dotenv()

class ClaudeBenchmark:
    """Claude 모델 성능 벤치마크 테스트"""

    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.results = {
            "test_date": datetime.now().isoformat(),
            "models": {},
            "test_categories": []
        }

    def test_model(self, model_name: str, test_cases: List[Dict]) -> Dict[str, Any]:
        """특정 모델에 대해 테스트 케이스 실행"""
        print(f"\n테스트 중: {model_name}")
        print("=" * 50)

        model_results = {
            "model": model_name,
            "total_tests": len(test_cases),
            "passed_tests": 0,
            "failed_tests": 0,
            "average_response_time": 0,
            "total_tokens": 0,
            "test_results": []
        }

        total_time = 0
        total_tokens = 0

        for i, test_case in enumerate(test_cases, 1):
            print(f"테스트 {i}/{len(test_cases)}: {test_case['name']}")

            try:
                start_time = time.time()

                response = self.client.messages.create(
                    model=model_name,
                    max_tokens=test_case.get('max_tokens', 1000),
                    temperature=test_case.get('temperature', 0.3),
                    messages=[
                        {
                            "role": "user",
                            "content": test_case['prompt']
                        }
                    ]
                )

                end_time = time.time()
                response_time = end_time - start_time
                total_time += response_time

                # 토큰 사용량 계산
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                total_test_tokens = input_tokens + output_tokens
                total_tokens += total_test_tokens

                # 응답 품질 평가
                quality_score = self.evaluate_response_quality(
                    test_case, response.content[0].text
                )

                test_result = {
                    "test_name": test_case['name'],
                    "category": test_case['category'],
                    "response_time": round(response_time, 2),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_test_tokens,
                    "quality_score": quality_score,
                    "response_preview": response.content[0].text[:200] + "...",
                    "success": True
                }

                model_results["test_results"].append(test_result)
                model_results["passed_tests"] += 1

                print(f"  성공 - 응답시간: {response_time:.2f}s, 토큰: {total_test_tokens}, 품질: {quality_score}/5")

                # API 호출 제한을 위한 짧은 대기
                time.sleep(1)

            except Exception as e:
                print(f"  실패: {str(e)}")
                model_results["test_results"].append({
                    "test_name": test_case['name'],
                    "category": test_case['category'],
                    "error": str(e),
                    "success": False
                })
                model_results["failed_tests"] += 1

        # 평균 계산
        if model_results["passed_tests"] > 0:
            model_results["average_response_time"] = round(total_time / model_results["passed_tests"], 2)
            model_results["total_tokens"] = total_tokens
            model_results["average_tokens_per_request"] = round(total_tokens / model_results["passed_tests"], 2)

        return model_results

    def evaluate_response_quality(self, test_case: Dict, response: str) -> int:
        """응답 품질 평가 (1-5점)"""
        score = 3  # 기본 점수

        # 기본 평가 기준
        if len(response) < 50:
            score -= 1  # 너무 짧은 응답
        elif len(response) > 1000:
            score += 1  # 충분히 상세한 응답

        # 카테고리별 평가
        category = test_case.get('category', '')

        if category == 'korean_generation':
            # 한국어 생성 품질 평가
            if '알림톡' in response and '템플릿' in response:
                score += 1
            if '#{' in response:  # 변수 사용
                score += 1

        elif category == 'policy_compliance':
            # 정책 준수 평가
            if '준수' in response or '적합' in response:
                score += 1
            if '점검' in response or '검토' in response:
                score += 1

        elif category == 'business_analysis':
            # 비즈니스 분석 평가
            if '비즈니스' in response or '업종' in response:
                score += 1
            if '분류' in response or '카테고리' in response:
                score += 1

        return min(5, max(1, score))

    def run_benchmark(self):
        """벤치마크 테스트 실행"""
        print("Claude 모델 성능 벤치마크 테스트 시작")
        print(f"테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 테스트 케이스 정의
        test_cases = self.get_test_cases()

        # 테스트할 모델들
        models_to_test = [
            "claude-3-5-haiku-latest",
            "claude-3-5-sonnet-latest"
        ]

        for model in models_to_test:
            try:
                results = self.test_model(model, test_cases)
                self.results["models"][model] = results
            except Exception as e:
                print(f"{model} 테스트 실패: {e}")
                self.results["models"][model] = {"error": str(e)}

        # 결과 저장
        self.save_results()
        self.print_summary()

    def get_test_cases(self) -> List[Dict]:
        """테스트 케이스 정의"""
        return [
            {
                "name": "한국어 알림톡 템플릿 생성",
                "category": "korean_generation",
                "prompt": "음식점 주문 완료 후 픽업 안내를 위한 카카오톡 알림톡 템플릿을 생성해주세요. 고객명과 픽업시간 변수를 포함해야 합니다.",
                "max_tokens": 1000,
                "temperature": 0.3
            },
            {
                "name": "정책 준수 검사",
                "category": "policy_compliance",
                "prompt": "다음 알림톡 템플릿이 카카오톡 정책에 준수하는지 검토해주세요: '할인쿠폰 지금 주문하면 50% 할인! 클릭하세요'",
                "max_tokens": 800,
                "temperature": 0.1
            },
            {
                "name": "비즈니스 유형 분석",
                "category": "business_analysis",
                "prompt": "고객이 '수강신청 마감 안내 메시지를 만들어주세요'라고 요청했습니다. 이 요청의 비즈니스 유형과 서비스 유형을 분석해주세요.",
                "max_tokens": 600,
                "temperature": 0.2
            },
            {
                "name": "복잡한 한국어 문맥 이해",
                "category": "korean_comprehension",
                "prompt": "병원에서 진료 예약 변경을 안내하는 메시지를 만들어야 합니다. 기존 예약일시, 변경된 예약일시, 담당의사명을 변수로 포함하고 정중한 존댓말을 사용해주세요.",
                "max_tokens": 1200,
                "temperature": 0.2
            },
            {
                "name": "창의적 템플릿 생성",
                "category": "creativity",
                "prompt": "카페에서 신메뉴 출시를 알리는 창의적이면서도 정책에 준수하는 알림톡 템플릿을 만들어주세요. 고객의 흥미를 끌면서도 과도하지 않은 표현을 사용해야 합니다.",
                "max_tokens": 1000,
                "temperature": 0.5
            },
            {
                "name": "긴 컨텍스트 처리",
                "category": "long_context",
                "prompt": """다음은 카카오톡 알림톡 정책의 일부입니다:

1. 광고성 문구 금지
2. 이모지 과도한 사용 금지
3. 변수 형식: #{변수명}
4. 존댓말 사용 권장
5. 명확한 발신자 정보 필요

이 정책을 바탕으로 온라인 쇼핑몰의 배송 완료 안내 템플릿을 만들어주세요.""",
                "max_tokens": 1000,
                "temperature": 0.3
            }
        ]

    def save_results(self):
        """결과를 JSON 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_results_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        print(f"\n결과 저장됨: {filename}")

    def print_summary(self):
        """결과 요약 출력"""
        print("\n" + "="*70)
        print("벤치마크 테스트 결과 요약")
        print("="*70)

        for model_name, results in self.results["models"].items():
            if "error" in results:
                print(f"\n{model_name}: 테스트 실패 - {results['error']}")
                continue

            print(f"\n{model_name}")
            print("-" * 50)
            print(f"성공한 테스트: {results['passed_tests']}/{results['total_tests']}")
            print(f"평균 응답 시간: {results['average_response_time']}초")
            print(f"총 토큰 사용량: {results['total_tokens']}")

            if results['passed_tests'] > 0:
                print(f"테스트당 평균 토큰: {results['average_tokens_per_request']}")

                # 카테고리별 성능
                categories = {}
                for test in results['test_results']:
                    if test['success']:
                        cat = test['category']
                        if cat not in categories:
                            categories[cat] = {'count': 0, 'avg_time': 0, 'avg_quality': 0}
                        categories[cat]['count'] += 1
                        categories[cat]['avg_time'] += test['response_time']
                        categories[cat]['avg_quality'] += test['quality_score']

                print("\n카테고리별 성능:")
                for cat, data in categories.items():
                    avg_time = data['avg_time'] / data['count']
                    avg_quality = data['avg_quality'] / data['count']
                    print(f"  {cat}: 평균 {avg_time:.2f}초, 품질 {avg_quality:.1f}/5")

if __name__ == "__main__":
    benchmark = ClaudeBenchmark()
    benchmark.run_benchmark()