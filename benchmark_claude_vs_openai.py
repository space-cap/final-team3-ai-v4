#!/usr/bin/env python3
"""
Claude vs OpenAI 모델 성능 비교 벤치마크
한국어 처리, 비즈니스 분석, 템플릿 생성 능력 종합 평가
"""

import os
import time
import json
from typing import Dict, List, Any, Tuple
from dotenv import load_dotenv
import anthropic
import openai
from datetime import datetime
import statistics

# .env 파일 로드
load_dotenv()

class AIModelComparison:
    """Claude vs OpenAI 모델 성능 비교 벤치마크"""

    def __init__(self):
        # API 클라이언트 초기화
        self.claude_client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.openai_client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )

        self.results = {
            "test_date": datetime.now().isoformat(),
            "models_tested": {},
            "comparison_metrics": {},
            "detailed_analysis": {}
        }

    def test_claude_model(self, model_name: str, test_cases: List[Dict]) -> Dict[str, Any]:
        """Claude 모델 테스트"""
        print(f"\nClaude 모델 테스트: {model_name}")
        print("=" * 50)

        model_results = {
            "provider": "Anthropic",
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

                response = self.claude_client.messages.create(
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

                # 토큰 사용량
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
                    "response_text": response.content[0].text,
                    "response_preview": response.content[0].text[:200] + "...",
                    "success": True
                }

                model_results["test_results"].append(test_result)
                model_results["passed_tests"] += 1

                print(f"  성공 - 응답시간: {response_time:.2f}s, 토큰: {total_test_tokens}, 품질: {quality_score}/5")
                time.sleep(1)  # API 제한 고려

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

    def test_openai_model(self, model_name: str, test_cases: List[Dict]) -> Dict[str, Any]:
        """OpenAI 모델 테스트"""
        print(f"\nOpenAI 모델 테스트: {model_name}")
        print("=" * 50)

        model_results = {
            "provider": "OpenAI",
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

                response = self.openai_client.chat.completions.create(
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

                # 토큰 사용량
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                total_test_tokens = input_tokens + output_tokens
                total_tokens += total_test_tokens

                # 응답 품질 평가
                response_text = response.choices[0].message.content
                quality_score = self.evaluate_response_quality(test_case, response_text)

                test_result = {
                    "test_name": test_case['name'],
                    "category": test_case['category'],
                    "response_time": round(response_time, 2),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_test_tokens,
                    "quality_score": quality_score,
                    "response_text": response_text,
                    "response_preview": response_text[:200] + "...",
                    "success": True
                }

                model_results["test_results"].append(test_result)
                model_results["passed_tests"] += 1

                print(f"  성공 - 응답시간: {response_time:.2f}s, 토큰: {total_test_tokens}, 품질: {quality_score}/5")
                time.sleep(1)  # API 제한 고려

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

        if not response or len(response.strip()) < 20:
            return 1  # 너무 짧거나 빈 응답

        # 길이 기반 평가
        if len(response) < 100:
            score -= 1
        elif len(response) > 500:
            score += 1

        # 카테고리별 평가
        category = test_case.get('category', '')

        if category == 'korean_generation':
            # 한국어 생성 품질 평가
            korean_indicators = ['님', '습니다', '해주세요', '감사합니다', '안녕하세요']
            korean_score = sum(1 for indicator in korean_indicators if indicator in response)
            score += min(2, korean_score // 2)

            # 변수 사용 확인
            if '#{' in response or '{' in response:
                score += 1

        elif category == 'policy_compliance':
            # 정책 준수 평가
            policy_terms = ['준수', '정책', '규정', '금지', '허용', '제한']
            policy_score = sum(1 for term in policy_terms if term in response)
            score += min(2, policy_score // 2)

        elif category == 'business_analysis':
            # 비즈니스 분석 평가
            business_terms = ['비즈니스', '업종', '서비스', '분석', '유형', '카테고리']
            business_score = sum(1 for term in business_terms if term in response)
            score += min(2, business_score // 2)

        elif category == 'korean_comprehension':
            # 한국어 이해도 평가
            comprehension_indicators = ['변경', '안내', '예약', '일정', '시간']
            comp_score = sum(1 for indicator in comprehension_indicators if indicator in response)
            score += min(2, comp_score // 2)

        elif category == 'creativity':
            # 창의성 평가
            creative_elements = ['특별', '새로운', '독특', '창의', '혁신']
            creative_score = sum(1 for element in creative_elements if element in response)
            score += min(1, creative_score // 2)

        elif category == 'long_context':
            # 긴 컨텍스트 처리 평가
            context_indicators = ['정책', '규정', '준수', '템플릿', '변수']
            context_score = sum(1 for indicator in context_indicators if indicator in response)
            score += min(1, context_score // 2)

        return min(5, max(1, score))

    def run_comprehensive_comparison(self):
        """포괄적인 모델 비교 테스트 실행"""
        print("AI 모델 성능 비교 분석 시작")
        print(f"테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        # 테스트 케이스 정의
        test_cases = self.get_enhanced_test_cases()

        # 테스트할 모델들
        models_to_test = [
            ("claude", "claude-3-5-haiku-latest"),
            ("claude", "claude-3-5-sonnet-latest"),
            ("openai", "gpt-4o-mini"),
            ("openai", "gpt-4o")
        ]

        for provider, model in models_to_test:
            try:
                if provider == "claude":
                    results = self.test_claude_model(model, test_cases)
                else:  # openai
                    results = self.test_openai_model(model, test_cases)

                self.results["models_tested"][f"{provider}_{model}"] = results

            except Exception as e:
                print(f"{provider} {model} 테스트 실패: {e}")
                self.results["models_tested"][f"{provider}_{model}"] = {"error": str(e)}

        # 비교 분석 수행
        self.perform_detailed_analysis()

        # 결과 저장
        self.save_results()
        self.print_comprehensive_summary()

    def get_enhanced_test_cases(self) -> List[Dict]:
        """향상된 테스트 케이스"""
        return [
            {
                "name": "한국어 알림톡 템플릿 생성",
                "category": "korean_generation",
                "prompt": "음식점에서 주문 완료 후 픽업 안내를 위한 카카오톡 알림톡 템플릿을 생성해주세요. 고객명(#{고객명})과 픽업시간(#{픽업시간}) 변수를 포함하고, 정중한 존댓말을 사용해주세요.",
                "max_tokens": 800,
                "temperature": 0.3
            },
            {
                "name": "정책 준수 검사 및 개선안 제시",
                "category": "policy_compliance",
                "prompt": "다음 알림톡 템플릿이 카카오톡 정책에 준수하는지 분석하고 개선안을 제시해주세요: '할인쿠폰 지금 주문하면 50% 할인! 클릭하세요 👆 마감임박!'",
                "max_tokens": 1000,
                "temperature": 0.1
            },
            {
                "name": "복합 비즈니스 시나리오 분석",
                "category": "business_analysis",
                "prompt": "온라인 교육 플랫폼에서 '수강신청 마감 연장 안내'와 '환불 정책 변경 공지'를 동시에 전달해야 합니다. 이 상황에서 적절한 커뮤니케이션 전략과 메시지 구조를 분석해주세요.",
                "max_tokens": 1200,
                "temperature": 0.2
            },
            {
                "name": "의료진 전문 용어 포함 한국어 처리",
                "category": "korean_comprehension",
                "prompt": "종합병원에서 MRI 검사 예약이 변경되어 환자에게 안내해야 합니다. 기존 예약(#{기존날짜} #{기존시간}), 변경 예약(#{변경날짜} #{변경시간}), 담당 의료진(#{의사명} 전문의)을 포함하여 의료 환경에 적합한 정중하고 전문적인 톤의 메시지를 작성해주세요.",
                "max_tokens": 900,
                "temperature": 0.2
            },
            {
                "name": "창의적이면서 정책 준수하는 마케팅 메시지",
                "category": "creativity",
                "prompt": "프리미엄 카페에서 계절 한정 신메뉴 '제주 감귤 라떼'를 출시합니다. 고객의 관심을 끌면서도 카카오톡 알림톡 정책을 완전히 준수하는 창의적인 마케팅 메시지를 작성해주세요. 과도한 이모지나 광고성 문구 없이 우아하고 세련된 톤을 유지해야 합니다.",
                "max_tokens": 1000,
                "temperature": 0.4
            },
            {
                "name": "다중 정책 문서 기반 복합 템플릿 생성",
                "category": "long_context",
                "prompt": """다음 카카오톡 알림톡 정책들을 모두 준수하여 온라인 쇼핑몰의 주문 확인 템플릿을 생성해주세요:

1. 광고성 문구 금지 (할인, 이벤트 직접 언급 제한)
2. 이모지 최소 사용 (1-2개 이내)
3. 변수 형식: #{변수명}
4. 명확한 발신자 정보 필요
5. 존댓말 사용 필수
6. 개인정보 보호 준수
7. 명확한 안내 목적 명시

포함할 변수: #{고객명}, #{주문번호}, #{상품명}, #{배송예정일}, #{쇼핑몰명}""",
                "max_tokens": 1200,
                "temperature": 0.3
            },
            {
                "name": "실시간 상황 대응 메시지",
                "category": "real_time_response",
                "prompt": "택배 배송 중 예상치 못한 지연이 발생했습니다. 고객에게 상황을 투명하게 안내하면서도 불안감을 최소화하고 신뢰를 유지할 수 있는 메시지를 작성해주세요. 지연 사유(#{지연사유}), 새로운 배송 예정일(#{신배송일}), 고객명(#{고객명}) 변수를 포함해주세요.",
                "max_tokens": 900,
                "temperature": 0.25
            },
            {
                "name": "다국어 고객 대상 한국어 메시지",
                "category": "cross_cultural",
                "prompt": "한국어를 배우는 외국인 고객들이 많이 이용하는 온라인 한국어 학습 플랫폼에서 수업 일정 변경을 안내해야 합니다. 한국어 초보자도 이해하기 쉽게 간단명료하면서도 정중한 메시지를 작성해주세요.",
                "max_tokens": 800,
                "temperature": 0.2
            }
        ]

    def perform_detailed_analysis(self):
        """상세 비교 분석 수행"""
        print("\n상세 비교 분석 수행 중...")

        models = self.results["models_tested"]

        # 성능 메트릭 계산
        performance_metrics = {}

        for model_key, model_data in models.items():
            if "error" in model_data:
                continue

            # 카테고리별 성능 분석
            category_performance = {}
            for test in model_data.get("test_results", []):
                if test["success"]:
                    category = test["category"]
                    if category not in category_performance:
                        category_performance[category] = {
                            "response_times": [],
                            "quality_scores": [],
                            "token_usage": []
                        }

                    category_performance[category]["response_times"].append(test["response_time"])
                    category_performance[category]["quality_scores"].append(test["quality_score"])
                    category_performance[category]["token_usage"].append(test["total_tokens"])

            # 통계 계산
            for category, data in category_performance.items():
                if data["response_times"]:
                    category_performance[category]["avg_response_time"] = statistics.mean(data["response_times"])
                    category_performance[category]["avg_quality"] = statistics.mean(data["quality_scores"])
                    category_performance[category]["avg_tokens"] = statistics.mean(data["token_usage"])

            performance_metrics[model_key] = {
                "overall": {
                    "avg_response_time": model_data.get("average_response_time", 0),
                    "avg_tokens": model_data.get("average_tokens_per_request", 0),
                    "success_rate": model_data.get("passed_tests", 0) / model_data.get("total_tests", 1)
                },
                "by_category": category_performance
            }

        self.results["comparison_metrics"] = performance_metrics

    def save_results(self):
        """결과를 JSON 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"claude_vs_openai_comparison_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        print(f"\n결과 저장됨: {filename}")

    def print_comprehensive_summary(self):
        """포괄적인 결과 요약 출력"""
        print("\n" + "="*80)
        print("AI 모델 성능 비교 분석 결과")
        print("="*80)

        models = self.results["models_tested"]

        # 전체 성능 요약
        print("\n전체 성능 요약:")
        print("-" * 60)

        for model_key, model_data in models.items():
            if "error" in model_data:
                print(f"{model_key}: 테스트 실패 - {model_data['error']}")
                continue

            provider = model_data.get("provider", "Unknown")
            model_name = model_data.get("model", "Unknown")

            print(f"\n{provider} - {model_name}")
            print(f"  성공률: {model_data['passed_tests']}/{model_data['total_tests']}")
            print(f"  평균 응답시간: {model_data['average_response_time']}초")
            print(f"  평균 토큰 사용: {model_data.get('average_tokens_per_request', 0)}")

            # 품질 점수 계산
            quality_scores = [test['quality_score'] for test in model_data['test_results'] if test['success']]
            if quality_scores:
                avg_quality = statistics.mean(quality_scores)
                print(f"  평균 품질 점수: {avg_quality:.2f}/5")

        # 카테고리별 최고 성능 모델
        print(f"\n카테고리별 최고 성능:")
        print("-" * 60)

        categories = set()
        for model_data in models.values():
            if "test_results" in model_data:
                for test in model_data["test_results"]:
                    if test["success"]:
                        categories.add(test["category"])

        for category in categories:
            best_model = None
            best_score = 0

            for model_key, model_data in models.items():
                if "test_results" in model_data:
                    category_scores = [test['quality_score'] for test in model_data['test_results']
                                     if test['success'] and test['category'] == category]
                    if category_scores:
                        avg_score = statistics.mean(category_scores)
                        if avg_score > best_score:
                            best_score = avg_score
                            best_model = model_key

            if best_model:
                print(f"  {category}: {best_model} (점수: {best_score:.2f})")

if __name__ == "__main__":
    comparison = AIModelComparison()
    comparison.run_comprehensive_comparison()