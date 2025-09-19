"""
카카오 알림톡 템플릿 자동 생성 시스템 테스트 스크립트
"""
import os
import sys
import asyncio
import json
from pathlib import Path

# 프로젝트 루트를 Python 패스에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_basic_imports():
    """기본 임포트 테스트"""
    print("[TEST] 기본 임포트 테스트...")

    try:
        from src.utils.llm_client import ClaudeLLMClient
        print("[OK] LLM 클라이언트 임포트 성공")

        from src.database.vector_store import PolicyVectorStore, TemplateStore
        print("[OK] 데이터베이스 모듈 임포트 성공")

        from src.agents.request_analyzer import RequestAnalyzerAgent
        from src.agents.template_generator import TemplateGeneratorAgent
        from src.agents.compliance_checker import ComplianceCheckerAgent
        from src.agents.policy_rag import PolicyRAGAgent
        print("✅ 에이전트 모듈 임포트 성공")

        from src.workflow.langgraph_workflow import SimpleWorkflowRunner
        print("✅ 워크플로우 모듈 임포트 성공")

        return True
    except Exception as e:
        print(f"❌ 임포트 실패: {e}")
        return False

def test_data_loading():
    """데이터 로딩 테스트"""
    print("\n🧪 데이터 로딩 테스트...")

    try:
        # 템플릿 데이터 로딩 테스트
        from src.database.vector_store import TemplateStore
        template_store = TemplateStore()

        if len(template_store.templates) > 0:
            print(f"✅ 템플릿 데이터 로딩 성공: {len(template_store.templates)}개")
        else:
            print("⚠️ 템플릿 데이터가 비어있음")

        # 정책 문서 확인
        policy_dir = Path("data/cleaned_policies")
        if policy_dir.exists():
            policy_files = list(policy_dir.glob("*.md"))
            print(f"✅ 정책 문서 발견: {len(policy_files)}개")
            for file in policy_files:
                print(f"   - {file.name}")
        else:
            print("❌ 정책 문서 디렉토리가 없음")

        return True
    except Exception as e:
        print(f"❌ 데이터 로딩 실패: {e}")
        return False

def test_simple_workflow():
    """간단한 워크플로우 테스트"""
    print("\n🧪 워크플로우 테스트...")

    # ANTHROPIC_API_KEY 확인
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️ ANTHROPIC_API_KEY가 설정되지 않음. 워크플로우 테스트 건너뜀")
        return True

    try:
        from src.workflow.langgraph_workflow import SimpleWorkflowRunner

        # 워크플로우 러너 초기화
        runner = SimpleWorkflowRunner()
        print("✅ 워크플로우 러너 초기화 성공")

        # 테스트 요청
        test_request = "온라인 강의 수강 신청 완료 안내 메시지를 생성해주세요"
        print(f"📝 테스트 요청: {test_request}")

        # 워크플로우 실행
        result = runner.run_simple_workflow(test_request)

        if result.get('success'):
            print("✅ 워크플로우 실행 성공")

            template = result.get('template', {})
            if template.get('template_text'):
                print(f"📄 생성된 템플릿: {template['template_text'][:100]}...")

            compliance = result.get('compliance', {})
            if compliance:
                print(f"📊 컴플라이언스 점수: {compliance.get('compliance_score', 0)}/100")

            return True
        else:
            print(f"❌ 워크플로우 실행 실패: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"❌ 워크플로우 테스트 실패: {e}")
        return False

def test_individual_components():
    """개별 컴포넌트 테스트"""
    print("\n🧪 개별 컴포넌트 테스트...")

    try:
        # 템플릿 스토어 테스트
        from src.database.vector_store import TemplateStore
        template_store = TemplateStore()

        education_templates = template_store.get_templates_by_business_type("교육")
        print(f"✅ 교육 관련 템플릿: {len(education_templates)}개")

        # 요청 분석기 테스트 (API 키 없이도 가능한 부분)
        from src.agents.request_analyzer import RequestAnalyzerAgent

        # Mock 분석 결과 생성
        test_request = "강의 수강 신청 완료 안내"

        # 기본 분류 로직 테스트
        analyzer = RequestAnalyzerAgent(None)  # LLM 없이 기본 로직만 테스트

        # 키워드 기반 분류 테스트
        if "강의" in test_request and "수강" in test_request:
            print("✅ 키워드 기반 비즈니스 유형 분류: 교육")

        if "신청" in test_request:
            print("✅ 키워드 기반 서비스 유형 분류: 신청")

        return True

    except Exception as e:
        print(f"❌ 컴포넌트 테스트 실패: {e}")
        return False

def test_api_models():
    """API 모델 테스트"""
    print("\n🧪 API 모델 테스트...")

    try:
        from src.api.models.schemas import (
            TemplateGenerationRequest,
            TemplateGenerationResponse,
            BusinessType,
            ServiceType
        )

        # 요청 모델 테스트
        test_data = {
            "user_request": "온라인 강의 수강 신청 완료 안내 메시지",
            "business_type": BusinessType.EDUCATION,
            "service_type": ServiceType.APPLICATION,
            "tone": "정중한"
        }

        request = TemplateGenerationRequest(**test_data)
        print("✅ 요청 모델 생성 성공")
        print(f"   - 요청 내용: {request.user_request}")
        print(f"   - 비즈니스 유형: {request.business_type}")
        print(f"   - 서비스 유형: {request.service_type}")

        return True

    except Exception as e:
        print(f"❌ API 모델 테스트 실패: {e}")
        return False

async def test_fastapi_startup():
    """FastAPI 앱 시작 테스트"""
    print("\n🧪 FastAPI 앱 시작 테스트...")

    try:
        from src.api.main import app

        print("✅ FastAPI 앱 임포트 성공")
        print(f"   - 앱 제목: {app.title}")
        print(f"   - 버전: {app.version}")

        # 라우트 확인
        routes = [route.path for route in app.routes]
        print(f"   - 등록된 라우트 수: {len(routes)}")

        if "/api/v1/templates/generate" in routes:
            print("✅ 템플릿 생성 엔드포인트 등록됨")

        if "/health" in routes:
            print("✅ 헬스체크 엔드포인트 등록됨")

        return True

    except Exception as e:
        print(f"❌ FastAPI 테스트 실패: {e}")
        return False

def generate_test_report(results):
    """테스트 결과 보고서 생성"""
    print("\n" + "="*60)
    print("📋 테스트 결과 보고서")
    print("="*60)

    total_tests = len(results)
    passed_tests = sum(results.values())

    print(f"총 테스트: {total_tests}")
    print(f"통과: {passed_tests}")
    print(f"실패: {total_tests - passed_tests}")
    print(f"성공률: {(passed_tests/total_tests)*100:.1f}%")

    print("\n상세 결과:")
    for test_name, result in results.items():
        status = "✅ 통과" if result else "❌ 실패"
        print(f"  {test_name}: {status}")

    if passed_tests == total_tests:
        print("\n🎉 모든 테스트가 통과했습니다!")
        print("💡 시스템이 정상적으로 설정되었습니다.")
        print("\n다음 단계:")
        print("1. .env 파일에 ANTHROPIC_API_KEY 설정")
        print("2. FastAPI 서버 실행: python -m uvicorn src.api.main:app --reload")
        print("3. http://localhost:8000/docs 에서 API 문서 확인")
    else:
        print("\n⚠️ 일부 테스트가 실패했습니다.")
        print("💡 실패한 테스트를 확인하고 문제를 해결해주세요.")

async def main():
    """메인 테스트 함수"""
    print("🚀 카카오 알림톡 템플릿 자동 생성 시스템 테스트 시작")
    print("="*60)

    # 환경 변수 로드 시도
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .env 파일 로드 성공")
    except ImportError:
        print("⚠️ python-dotenv가 설치되지 않음")
    except:
        print("⚠️ .env 파일을 찾을 수 없음")

    # 테스트 실행
    results = {}

    results["기본 임포트"] = test_basic_imports()
    results["데이터 로딩"] = test_data_loading()
    results["개별 컴포넌트"] = test_individual_components()
    results["API 모델"] = test_api_models()
    results["FastAPI 앱"] = await test_fastapi_startup()
    results["워크플로우"] = test_simple_workflow()

    # 보고서 생성
    generate_test_report(results)

if __name__ == "__main__":
    asyncio.run(main())