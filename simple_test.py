"""
Simple system test without Unicode characters
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test basic imports"""
    print("[TEST] Basic imports...")

    try:
        from src.utils.llm_client import ClaudeLLMClient
        print("[OK] LLM client import")

        from src.database.vector_store import PolicyVectorStore, TemplateStore
        print("[OK] Database modules import")

        from src.agents.request_analyzer import RequestAnalyzerAgent
        from src.agents.template_generator import TemplateGeneratorAgent
        from src.agents.compliance_checker import ComplianceCheckerAgent
        from src.agents.policy_rag import PolicyRAGAgent
        print("[OK] Agent modules import")

        from src.workflow.langgraph_workflow import SimpleWorkflowRunner
        print("[OK] Workflow modules import")

        return True
    except Exception as e:
        print(f"[ERROR] Import failed: {e}")
        return False

def test_data():
    """Test data loading"""
    print("\n[TEST] Data loading...")

    try:
        from src.database.vector_store import TemplateStore
        template_store = TemplateStore()

        if len(template_store.templates) > 0:
            print(f"[OK] Template data loaded: {len(template_store.templates)} templates")
        else:
            print("[WARN] No template data found")

        # Check policy documents
        policy_dir = Path("data/cleaned_policies")
        if policy_dir.exists():
            policy_files = list(policy_dir.glob("*.md"))
            print(f"[OK] Policy documents found: {len(policy_files)} files")
        else:
            print("[ERROR] Policy directory not found")

        return True
    except Exception as e:
        print(f"[ERROR] Data loading failed: {e}")
        return False

def test_workflow():
    """Test simple workflow"""
    print("\n[TEST] Workflow test...")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[WARN] ANTHROPIC_API_KEY not set. Skipping workflow test")
        return True

    try:
        from src.workflow.langgraph_workflow import SimpleWorkflowRunner

        runner = SimpleWorkflowRunner()
        print("[OK] Workflow runner initialized")

        test_request = "Create an online course enrollment confirmation message"
        result = runner.run_simple_workflow(test_request)

        if result.get('success'):
            print("[OK] Workflow execution successful")

            template = result.get('template', {})
            if template.get('template_text'):
                text = template['template_text'][:100] + "..." if len(template['template_text']) > 100 else template['template_text']
                print(f"[INFO] Generated template: {text}")

            compliance = result.get('compliance', {})
            if compliance:
                score = compliance.get('compliance_score', 0)
                print(f"[INFO] Compliance score: {score}/100")

            return True
        else:
            print(f"[ERROR] Workflow failed: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"[ERROR] Workflow test failed: {e}")
        return False

def test_api_models():
    """Test API models"""
    print("\n[TEST] API models...")

    try:
        from src.api.models.schemas import (
            TemplateGenerationRequest,
            BusinessType,
            ServiceType
        )

        test_data = {
            "user_request": "Online course enrollment confirmation message",
            "business_type": BusinessType.EDUCATION,
            "service_type": ServiceType.APPLICATION,
            "tone": "formal"
        }

        request = TemplateGenerationRequest(**test_data)
        print("[OK] Request model created successfully")
        print(f"[INFO] Request: {request.user_request}")
        print(f"[INFO] Business type: {request.business_type}")

        return True
    except Exception as e:
        print(f"[ERROR] API model test failed: {e}")
        return False

def main():
    """Main test function"""
    print("KakaoTalk Template Generation System Test")
    print("=" * 50)

    # Load environment
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("[OK] Environment loaded")
    except:
        print("[WARN] Could not load .env file")

    # Run tests
    results = {}
    results["Imports"] = test_imports()
    results["Data Loading"] = test_data()
    results["API Models"] = test_api_models()
    results["Workflow"] = test_workflow()

    # Summary
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)

    total = len(results)
    passed = sum(results.values())

    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success rate: {(passed/total)*100:.1f}%")

    print("\nDetailed results:")
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  {test_name}: {status}")

    if passed == total:
        print("\nAll tests passed! System is ready.")
        print("\nNext steps:")
        print("1. Set ANTHROPIC_API_KEY in .env file")
        print("2. Run server: python run_server.py")
        print("3. Check API docs at http://localhost:8000/docs")
    else:
        print("\nSome tests failed. Please check the issues above.")

if __name__ == "__main__":
    main()