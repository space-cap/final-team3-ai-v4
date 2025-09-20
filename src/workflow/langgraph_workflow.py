"""
LangGraph Workflow - Multi-Agent 협업 워크플로우
"""
import logging
from typing import Dict, Any, List, TypedDict
from dataclasses import dataclass
from enum import Enum

try:
    from langgraph.graph import Graph, END
    from langgraph.checkpoint.memory import MemorySaver
except ImportError:
    # Fallback if LangGraph is not available
    print("LangGraph not available, using manual workflow")

from ..agents.request_analyzer import RequestAnalyzerAgent
from ..agents.template_generator import TemplateGeneratorAgent
from ..agents.compliance_checker import ComplianceCheckerAgent
from ..agents.policy_rag import PolicyRAGAgent
from ..utils.llm_client import ClaudeLLMClient
from ..utils.performance_monitor import WorkflowPerformanceMonitor, get_performance_monitor, cleanup_performance_monitor
from ..database.vector_store import PolicyVectorStore, TemplateStore

logger = logging.getLogger(__name__)

class WorkflowState(TypedDict):
    """워크플로우 상태 정의"""
    user_request: str
    analysis_result: Dict[str, Any]
    policy_context: Dict[str, Any]
    generated_template: Dict[str, Any]
    compliance_result: Dict[str, Any]
    final_result: Dict[str, Any]
    iteration_count: int
    errors: List[str]

class WorkflowStage(Enum):
    """워크플로우 단계"""
    REQUEST_ANALYSIS = "request_analysis"
    POLICY_RETRIEVAL = "policy_retrieval"
    TEMPLATE_GENERATION = "template_generation"
    COMPLIANCE_CHECK = "compliance_check"
    REFINEMENT = "refinement"
    COMPLETION = "completion"

@dataclass
class WorkflowConfig:
    """워크플로우 설정"""
    max_iterations: int = 3
    min_compliance_score: float = 80.0
    enable_auto_refinement: bool = True
    strict_compliance: bool = True

class KakaoTemplateWorkflow:
    """카카오 알림톡 템플릿 생성 워크플로우"""

    def __init__(self, config: WorkflowConfig = None):
        self.config = config or WorkflowConfig()
        self.performance_monitor = None
        self.setup_agents()
        self.setup_workflow()

    def setup_agents(self):
        """에이전트 초기화"""
        try:
            # LLM 클라이언트
            self.llm_client = ClaudeLLMClient()

            # 데이터 스토어
            self.vector_store = PolicyVectorStore()
            self.template_store = TemplateStore()

            # 에이전트들
            self.request_analyzer = RequestAnalyzerAgent(self.llm_client)
            self.policy_rag = PolicyRAGAgent(self.vector_store)
            self.template_generator = TemplateGeneratorAgent(self.llm_client, self.template_store)
            self.compliance_checker = ComplianceCheckerAgent(self.llm_client)

            logger.info("All agents initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing agents: {e}")
            raise

    def setup_workflow(self):
        """워크플로우 그래프 설정"""
        try:
            # LangGraph 사용 가능한 경우
            if 'langgraph' in globals():
                self.workflow_graph = Graph()

                # 노드 추가
                self.workflow_graph.add_node("analyze_request", self.analyze_request_node)
                self.workflow_graph.add_node("retrieve_policies", self.retrieve_policies_node)
                self.workflow_graph.add_node("generate_template", self.generate_template_node)
                self.workflow_graph.add_node("check_compliance", self.check_compliance_node)
                self.workflow_graph.add_node("refine_template", self.refine_template_node)

                # 엣지 추가
                self.workflow_graph.add_edge("analyze_request", "retrieve_policies")
                self.workflow_graph.add_edge("retrieve_policies", "generate_template")
                self.workflow_graph.add_edge("generate_template", "check_compliance")

                # 조건부 엣지
                self.workflow_graph.add_conditional_edges(
                    "check_compliance",
                    self.should_refine,
                    {
                        "refine": "refine_template",
                        "complete": END
                    }
                )

                self.workflow_graph.add_edge("refine_template", "generate_template")

                # 시작 노드 설정
                self.workflow_graph.set_entry_point("analyze_request")

                # 메모리 체크포인트
                self.checkpointer = MemorySaver()
                self.workflow = self.workflow_graph.compile(checkpointer=self.checkpointer)

                logger.info("LangGraph workflow initialized")
            else:
                self.workflow = None
                logger.info("Using manual workflow (LangGraph not available)")

        except Exception as e:
            logger.error(f"Error setting up workflow: {e}")
            self.workflow = None

    def run(self, user_request: str, session_id: str = "default") -> Dict[str, Any]:
        """워크플로우 실행"""
        logger.info(f"Starting workflow for request: {user_request[:100]}...")

        # 성능 모니터 초기화
        self.performance_monitor = get_performance_monitor(session_id)

        initial_state = WorkflowState(
            user_request=user_request,
            analysis_result={},
            policy_context={},
            generated_template={},
            compliance_result={},
            final_result={},
            iteration_count=0,
            errors=[]
        )

        try:
            with self.performance_monitor.measure_step("total_workflow", {"request_length": len(user_request)}):
                if self.workflow:
                    # LangGraph 사용
                    config = {"configurable": {"thread_id": session_id}}
                    result = self.workflow.invoke(initial_state, config)
                    final_result = self._format_final_result(result)
                else:
                    # 수동 워크플로우
                    final_result = self._run_manual_workflow(initial_state)

                # 성능 데이터를 결과에 포함
                final_result['performance'] = self.performance_monitor.export_to_dict()
                return final_result

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return self._get_error_result(str(e))
        finally:
            # 성능 모니터 정리
            cleanup_performance_monitor(session_id)

    def _run_manual_workflow(self, state: WorkflowState) -> Dict[str, Any]:
        """수동 워크플로우 실행"""
        try:
            # 1. 요청 분석
            state = self.analyze_request_node(state)
            if state.get('errors'):
                return self._format_final_result(state)

            # 2. 정책 검색
            state = self.retrieve_policies_node(state)

            # 3. 템플릿 생성 및 개선 루프
            for iteration in range(self.config.max_iterations):
                state['iteration_count'] = iteration + 1

                # 템플릿 생성
                state = self.generate_template_node(state)

                # 컴플라이언스 검사
                state = self.check_compliance_node(state)

                # 개선 필요 여부 확인
                if not self._needs_refinement(state):
                    break

                # 개선
                if iteration < self.config.max_iterations - 1:
                    state = self.refine_template_node(state)

            return self._format_final_result(state)

        except Exception as e:
            logger.error(f"Manual workflow failed: {e}")
            state['errors'].append(str(e))
            return self._format_final_result(state)

    def analyze_request_node(self, state: WorkflowState) -> WorkflowState:
        """요청 분석 노드"""
        logger.info("Analyzing user request...")

        try:
            with self.performance_monitor.measure_step("request_analysis",
                                                     {"request_length": len(state['user_request'])}):
                analysis_result = self.request_analyzer.analyze_request(state['user_request'])
                state['analysis_result'] = analysis_result

                logger.info(f"Request analysis completed: {analysis_result.get('business_type', 'Unknown')}")

        except Exception as e:
            error_msg = f"Request analysis failed: {str(e)}"
            logger.error(error_msg)
            state['errors'].append(error_msg)

        return state

    def retrieve_policies_node(self, state: WorkflowState) -> WorkflowState:
        """정책 검색 노드"""
        logger.info("Retrieving relevant policies...")

        try:
            analysis_result = state.get('analysis_result', {})
            business_type = analysis_result.get('business_type', '기타')
            service_type = analysis_result.get('service_type', '안내')

            with self.performance_monitor.measure_step("policy_retrieval",
                                                     {"business_type": business_type, "service_type": service_type}):
                # 정책 컨텍스트 검색
                query = f"{business_type} {service_type} 알림톡 템플릿 정책"
                policy_context = self.policy_rag.get_relevant_policies(query, "template_generation")

                # 예시 검색
                examples = self.policy_rag.search_policy_examples(business_type, service_type)

                state['policy_context'] = {
                    'main_context': policy_context,
                    'examples': examples
                }

                logger.info(f"Retrieved {policy_context.get('total_chunks', 0)} policy chunks")

        except Exception as e:
            error_msg = f"Policy retrieval failed: {str(e)}"
            logger.error(error_msg)
            state['errors'].append(error_msg)

        return state

    def generate_template_node(self, state: WorkflowState) -> WorkflowState:
        """템플릿 생성 노드"""
        logger.info("Generating template...")

        try:
            analysis_result = state.get('analysis_result', {})
            policy_context = state.get('policy_context', {}).get('main_context', {}).get('context', '')
            iteration = state.get('iteration_count', 0)

            with self.performance_monitor.measure_step("template_generation",
                                                     {"iteration": iteration, "has_previous_feedback": iteration > 1}):
                # 이전 컴플라이언스 결과가 있으면 반영
                previous_compliance = state.get('compliance_result', {})
                if previous_compliance and iteration > 1:
                    analysis_result['previous_violations'] = previous_compliance.get('violations', [])
                    analysis_result['previous_recommendations'] = previous_compliance.get('recommendations', [])

                generated_template = self.template_generator.generate_template(
                    analysis_result, policy_context
                )

                state['generated_template'] = generated_template

                logger.info("Template generation completed")

        except Exception as e:
            error_msg = f"Template generation failed: {str(e)}"
            logger.error(error_msg)
            state['errors'].append(error_msg)

        return state

    def check_compliance_node(self, state: WorkflowState) -> WorkflowState:
        """컴플라이언스 검사 노드"""
        logger.info("Checking compliance...")

        try:
            generated_template = state.get('generated_template', {})
            policy_context = state.get('policy_context', {}).get('main_context', {}).get('context', '')
            template_length = len(generated_template.get('template_text', ''))

            with self.performance_monitor.measure_step("compliance_check",
                                                     {"template_length": template_length}):
                compliance_result = self.compliance_checker.check_compliance(
                    generated_template, policy_context
                )

                state['compliance_result'] = compliance_result

                logger.info(f"Compliance check completed. Score: {compliance_result.get('compliance_score', 0)}")

        except Exception as e:
            error_msg = f"Compliance check failed: {str(e)}"
            logger.error(error_msg)
            state['errors'].append(error_msg)

        return state

    def refine_template_node(self, state: WorkflowState) -> WorkflowState:
        """템플릿 개선 노드"""
        logger.info("Refining template based on compliance feedback...")

        try:
            compliance_result = state.get('compliance_result', {})
            generated_template = state.get('generated_template', {})
            violations_count = len(compliance_result.get('violations', []))

            with self.performance_monitor.measure_step("template_refinement",
                                                     {"violations_count": violations_count}):
                # 개선사항 적용
                if compliance_result.get('recommendations'):
                    # 권장사항을 분석 결과에 추가하여 재생성 시 반영
                    analysis_result = state.get('analysis_result', {})
                    analysis_result['compliance_feedback'] = {
                        'violations': compliance_result.get('violations', []),
                        'recommendations': compliance_result.get('recommendations', []),
                        'required_changes': compliance_result.get('required_changes', [])
                    }
                    state['analysis_result'] = analysis_result

                logger.info(f"Template refinement prepared for iteration {state.get('iteration_count', 0)}")

        except Exception as e:
            error_msg = f"Template refinement failed: {str(e)}"
            logger.error(error_msg)
            state['errors'].append(error_msg)

        return state

    def should_refine(self, state: WorkflowState) -> str:
        """개선 필요 여부 결정 (LangGraph 조건부 엣지용)"""
        return "refine" if self._needs_refinement(state) else "complete"

    def _needs_refinement(self, state: WorkflowState) -> bool:
        """개선 필요 여부 판단"""
        if not self.config.enable_auto_refinement:
            return False

        compliance_result = state.get('compliance_result', {})
        iteration_count = state.get('iteration_count', 0)

        # 최대 반복 횟수 확인
        if iteration_count >= self.config.max_iterations:
            return False

        # 컴플라이언스 점수 확인
        compliance_score = compliance_result.get('compliance_score', 0)
        if compliance_score < self.config.min_compliance_score:
            return True

        # 심각한 위반사항 확인
        if self.config.strict_compliance:
            required_changes = compliance_result.get('required_changes', [])
            if required_changes:
                return True

        return False

    def _format_final_result(self, state: WorkflowState) -> Dict[str, Any]:
        """최종 결과 포맷팅"""
        generated_template = state.get('generated_template', {})
        compliance_result = state.get('compliance_result', {})
        analysis_result = state.get('analysis_result', {})

        return {
            'success': len(state.get('errors', [])) == 0,
            'template': {
                'text': generated_template.get('template_text', ''),
                'variables': generated_template.get('variables', []),
                'button_suggestion': generated_template.get('button_suggestion', ''),
                'metadata': {
                    'category_1': generated_template.get('metadata', {}).get('category_1', '서비스이용'),
                    'category_2': generated_template.get('metadata', {}).get('category_2', '이용안내/공지'),
                    'business_type': analysis_result.get('business_type', '기타'),
                    'service_type': analysis_result.get('service_type', '안내'),
                    'estimated_length': len(generated_template.get('template_text', '')),
                    'variable_count': len(generated_template.get('variables', [])),
                    'target_audience': generated_template.get('metadata', {}).get('target_audience', '일반'),
                    'tone': generated_template.get('metadata', {}).get('tone', '정중한'),
                    'generation_method': 'ai_generated'
                }
            },
            'compliance': {
                'is_compliant': compliance_result.get('is_compliant', False),
                'score': compliance_result.get('compliance_score', 0),
                'violations': compliance_result.get('violations', []),
                'warnings': compliance_result.get('warnings', []),
                'recommendations': compliance_result.get('recommendations', []),
                'approval_probability': compliance_result.get('approval_probability', '낮음'),
                'required_changes': compliance_result.get('required_changes', [])
            },
            'analysis': {
                'business_type': analysis_result.get('business_type', '기타'),
                'service_type': analysis_result.get('service_type', '안내'),
                'message_purpose': analysis_result.get('message_purpose', '사용자 요청 메시지'),
                'estimated_category': analysis_result.get('estimated_category', {}),
                'compliance_concerns': analysis_result.get('compliance_concerns', [])
            },
            'workflow_info': {
                'iterations': state.get('iteration_count', 0),
                'errors': state.get('errors', []),
                'policy_sources': state.get('policy_context', {}).get('main_context', {}).get('sources', [])
            }
        }

    def _get_error_result(self, error_message: str) -> Dict[str, Any]:
        """오류 결과 생성"""
        return {
            'success': False,
            'template': {
                'text': '',
                'variables': [],
                'button_suggestion': '',
                'metadata': {
                    'category_1': '서비스이용',
                    'category_2': '이용안내/공지',
                    'business_type': '기타',
                    'service_type': '안내',
                    'estimated_length': 0,
                    'variable_count': 0,
                    'target_audience': '일반',
                    'tone': '정중한',
                    'generation_method': 'error'
                }
            },
            'compliance': {
                'is_compliant': False,
                'score': 0,
                'violations': [error_message],
                'warnings': [],
                'recommendations': ['시스템 오류로 인한 수동 검토 필요'],
                'approval_probability': '낮음',
                'required_changes': []
            },
            'analysis': {
                'business_type': '기타',
                'service_type': '안내',
                'message_purpose': '시스템 오류',
                'estimated_category': {},
                'compliance_concerns': [error_message]
            },
            'workflow_info': {
                'iterations': 0,
                'errors': [error_message],
                'policy_sources': []
            }
        }

    def get_workflow_status(self, session_id: str = "default") -> Dict[str, Any]:
        """워크플로우 상태 조회"""
        try:
            if self.workflow and hasattr(self.workflow, 'get_state'):
                config = {"configurable": {"thread_id": session_id}}
                state = self.workflow.get_state(config)
                return {
                    'current_step': state.next,
                    'completed_steps': list(state.metadata.get('steps', [])),
                    'errors': state.values.get('errors', [])
                }
            else:
                return {'status': 'Manual workflow - status tracking not available'}
        except Exception as e:
            return {'error': str(e)}

    def reset_workflow(self, session_id: str = "default"):
        """워크플로우 리셋"""
        try:
            if self.workflow and hasattr(self.checkpointer, 'delete'):
                config = {"configurable": {"thread_id": session_id}}
                self.checkpointer.delete(config)
                logger.info(f"Workflow session {session_id} reset")
        except Exception as e:
            logger.error(f"Error resetting workflow: {e}")


class SimpleWorkflowRunner:
    """LangGraph 없이 사용할 수 있는 간단한 워크플로우 러너"""

    def __init__(self):
        self.setup_agents()

    def setup_agents(self):
        """에이전트 초기화"""
        self.llm_client = ClaudeLLMClient()
        self.vector_store = PolicyVectorStore()
        self.template_store = TemplateStore()

        self.request_analyzer = RequestAnalyzerAgent(self.llm_client)
        self.policy_rag = PolicyRAGAgent(self.vector_store)
        self.template_generator = TemplateGeneratorAgent(self.llm_client, self.template_store)
        self.compliance_checker = ComplianceCheckerAgent(self.llm_client)

    def run_simple_workflow(self, user_request: str) -> Dict[str, Any]:
        """간단한 워크플로우 실행"""
        try:
            # 1. 요청 분석
            analysis = self.request_analyzer.analyze_request(user_request)

            # 2. 정책 검색
            business_type = analysis.get('business_type', '기타')
            service_type = analysis.get('service_type', '안내')
            query = f"{business_type} {service_type} 알림톡 템플릿"
            policies = self.policy_rag.get_relevant_policies(query, "template_generation")

            # 3. 템플릿 생성
            template = self.template_generator.generate_template(
                analysis, policies.get('context', '')
            )

            # 4. 컴플라이언스 체크
            compliance = self.compliance_checker.check_compliance(
                template, policies.get('context', '')
            )

            return {
                'success': True,
                'template': template,
                'compliance': compliance,
                'analysis': analysis
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


if __name__ == "__main__":
    # Test the workflow
    try:
        workflow = KakaoTemplateWorkflow()
        result = workflow.run("온라인 강의 수강 신청 완료 안내 메시지를 만들어주세요")
        print("Workflow Result:")
        print(f"Success: {result['success']}")
        print(f"Template: {result['template']['text'][:100]}...")
        print(f"Compliance Score: {result['compliance']['score']}")
    except Exception as e:
        print(f"Testing simple runner due to error: {e}")
        simple_runner = SimpleWorkflowRunner()
        result = simple_runner.run_simple_workflow("온라인 강의 수강 신청 완료 안내 메시지")
        print("Simple Workflow Result:")
        print(f"Success: {result['success']}")
        if result.get('template'):
            print(f"Template: {result['template']['template_text'][:100]}...")