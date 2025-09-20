"""
템플릿 생성 성능 모니터링 유틸리티
단계별 시간 측정 및 성능 분석을 위한 도구
"""
import time
import logging
from typing import Dict, Any, List, Optional
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class StepTiming:
    """단계별 시간 측정 결과"""
    step_name: str
    start_time: float
    end_time: float
    duration_seconds: float
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class PerformanceReport:
    """성능 측정 종합 보고서"""
    session_id: str
    total_duration: float
    total_steps: int
    successful_steps: int
    failed_steps: int
    step_timings: List[StepTiming]
    bottlenecks: List[Dict[str, Any]]
    recommendations: List[str]
    timestamp: str

class PerformanceMonitor:
    """템플릿 생성 성능 모니터링 클래스"""

    def __init__(self, session_id: str = None):
        self.session_id = session_id or f"session_{int(time.time())}"
        self.step_timings: List[StepTiming] = []
        self.current_step: Optional[str] = None
        self.current_start_time: Optional[float] = None
        self.session_start_time = time.time()

    @contextmanager
    def measure_step(self, step_name: str, metadata: Dict[str, Any] = None):
        """단계별 시간 측정 컨텍스트 매니저"""
        start_time = time.time()
        self.current_step = step_name
        self.current_start_time = start_time
        success = True
        error_message = None

        logger.info(f"[{self.session_id}] Starting step: {step_name}")

        try:
            yield
        except Exception as e:
            success = False
            error_message = str(e)
            logger.error(f"[{self.session_id}] Step failed: {step_name} - {error_message}")
            raise
        finally:
            end_time = time.time()
            duration = end_time - start_time

            timing = StepTiming(
                step_name=step_name,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=round(duration, 3),
                success=success,
                error_message=error_message,
                metadata=metadata or {}
            )

            self.step_timings.append(timing)

            if success:
                logger.info(f"[{self.session_id}] Completed step: {step_name} in {duration:.3f}s")
            else:
                logger.error(f"[{self.session_id}] Failed step: {step_name} after {duration:.3f}s")

            self.current_step = None
            self.current_start_time = None

    def add_manual_timing(self, step_name: str, duration: float, success: bool = True,
                         error_message: str = None, metadata: Dict[str, Any] = None):
        """수동으로 시간 측정 결과 추가"""
        current_time = time.time()
        timing = StepTiming(
            step_name=step_name,
            start_time=current_time - duration,
            end_time=current_time,
            duration_seconds=round(duration, 3),
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )
        self.step_timings.append(timing)

    def get_current_report(self) -> PerformanceReport:
        """현재까지의 성능 보고서 생성"""
        total_duration = time.time() - self.session_start_time
        total_steps = len(self.step_timings)
        successful_steps = sum(1 for t in self.step_timings if t.success)
        failed_steps = total_steps - successful_steps

        # 병목 지점 분석
        bottlenecks = self._analyze_bottlenecks()

        # 권장사항 생성
        recommendations = self._generate_recommendations()

        return PerformanceReport(
            session_id=self.session_id,
            total_duration=round(total_duration, 3),
            total_steps=total_steps,
            successful_steps=successful_steps,
            failed_steps=failed_steps,
            step_timings=self.step_timings,
            bottlenecks=bottlenecks,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat()
        )

    def _analyze_bottlenecks(self) -> List[Dict[str, Any]]:
        """병목 지점 분석"""
        if not self.step_timings:
            return []

        bottlenecks = []
        total_time = sum(t.duration_seconds for t in self.step_timings)

        # 가장 오래 걸린 단계들 식별 (전체 시간의 20% 이상)
        for timing in sorted(self.step_timings, key=lambda x: x.duration_seconds, reverse=True):
            percentage = (timing.duration_seconds / total_time) * 100 if total_time > 0 else 0

            if percentage >= 20.0:  # 전체 시간의 20% 이상인 경우
                bottlenecks.append({
                    'step_name': timing.step_name,
                    'duration_seconds': timing.duration_seconds,
                    'percentage_of_total': round(percentage, 1),
                    'is_bottleneck': True,
                    'severity': self._classify_bottleneck_severity(percentage)
                })

        return bottlenecks

    def _classify_bottleneck_severity(self, percentage: float) -> str:
        """병목 심각도 분류"""
        if percentage >= 50:
            return "심각"
        elif percentage >= 35:
            return "중간"
        else:
            return "경미"

    def _generate_recommendations(self) -> List[str]:
        """성능 개선 권장사항 생성"""
        recommendations = []

        if not self.step_timings:
            return recommendations

        # 전체 시간 분석
        total_time = sum(t.duration_seconds for t in self.step_timings)

        if total_time > 30:  # 30초 이상
            recommendations.append("전체 처리 시간이 30초를 초과합니다. 워크플로우 최적화가 필요합니다.")

        # 단계별 분석
        step_analysis = {}
        for timing in self.step_timings:
            step_name = timing.step_name
            if step_name not in step_analysis:
                step_analysis[step_name] = []
            step_analysis[step_name].append(timing.duration_seconds)

        # LLM 호출이 오래 걸리는 경우
        llm_steps = ['template_generation', 'compliance_check', 'request_analysis']
        for step in llm_steps:
            if step in step_analysis:
                avg_time = sum(step_analysis[step]) / len(step_analysis[step])
                if avg_time > 10:  # 10초 이상
                    recommendations.append(f"{step} 단계가 {avg_time:.1f}초로 오래 걸립니다. LLM 프롬프트 최적화나 모델 변경을 고려하세요.")

        # 정책 검색이 오래 걸리는 경우
        if 'policy_retrieval' in step_analysis:
            avg_time = sum(step_analysis['policy_retrieval']) / len(step_analysis['policy_retrieval'])
            if avg_time > 5:  # 5초 이상
                recommendations.append(f"정책 검색이 {avg_time:.1f}초로 오래 걸립니다. 벡터 데이터베이스 인덱싱이나 캐싱을 고려하세요.")

        # 실패한 단계가 많은 경우
        failed_count = sum(1 for t in self.step_timings if not t.success)
        if failed_count > 0:
            recommendations.append(f"{failed_count}개 단계가 실패했습니다. 에러 처리 및 재시도 로직을 검토하세요.")

        # 반복 횟수가 많은 경우
        iteration_steps = [t for t in self.step_timings if 'refinement' in t.step_name or 'iteration' in t.step_name]
        if len(iteration_steps) > 2:
            recommendations.append("템플릿 개선 반복이 많이 발생했습니다. 초기 생성 품질 향상을 고려하세요.")

        return recommendations

    def get_step_summary(self) -> Dict[str, Any]:
        """단계별 요약 정보"""
        if not self.step_timings:
            return {}

        summary = {}
        for timing in self.step_timings:
            step_name = timing.step_name
            if step_name not in summary:
                summary[step_name] = {
                    'total_calls': 0,
                    'total_time': 0,
                    'avg_time': 0,
                    'max_time': 0,
                    'min_time': float('inf'),
                    'success_rate': 0,
                    'failures': 0
                }

            summary[step_name]['total_calls'] += 1
            summary[step_name]['total_time'] += timing.duration_seconds
            summary[step_name]['max_time'] = max(summary[step_name]['max_time'], timing.duration_seconds)
            summary[step_name]['min_time'] = min(summary[step_name]['min_time'], timing.duration_seconds)

            if not timing.success:
                summary[step_name]['failures'] += 1

        # 평균 시간 및 성공률 계산
        for step_name, data in summary.items():
            data['avg_time'] = round(data['total_time'] / data['total_calls'], 3)
            data['success_rate'] = round((data['total_calls'] - data['failures']) / data['total_calls'] * 100, 1)
            if data['min_time'] == float('inf'):
                data['min_time'] = 0

        return summary

    def export_to_dict(self) -> Dict[str, Any]:
        """성능 데이터를 딕셔너리로 내보내기"""
        report = self.get_current_report()
        return {
            'session_info': {
                'session_id': report.session_id,
                'timestamp': report.timestamp,
                'total_duration': report.total_duration
            },
            'summary': {
                'total_steps': report.total_steps,
                'successful_steps': report.successful_steps,
                'failed_steps': report.failed_steps,
                'success_rate': round(report.successful_steps / report.total_steps * 100, 1) if report.total_steps > 0 else 0
            },
            'step_timings': [asdict(timing) for timing in report.step_timings],
            'bottlenecks': report.bottlenecks,
            'recommendations': report.recommendations,
            'step_summary': self.get_step_summary()
        }

    def log_performance_summary(self):
        """성능 요약을 로그로 출력"""
        report = self.get_current_report()

        logger.info(f"=== Performance Summary [{self.session_id}] ===")
        logger.info(f"Total Duration: {report.total_duration:.3f}s")
        logger.info(f"Steps: {report.successful_steps}/{report.total_steps} successful")

        if report.bottlenecks:
            logger.warning("Bottlenecks detected:")
            for bottleneck in report.bottlenecks:
                logger.warning(f"  - {bottleneck['step_name']}: {bottleneck['duration_seconds']}s ({bottleneck['percentage_of_total']}%)")

        if report.recommendations:
            logger.info("Recommendations:")
            for rec in report.recommendations:
                logger.info(f"  - {rec}")


class WorkflowPerformanceMonitor(PerformanceMonitor):
    """워크플로우 특화 성능 모니터"""

    def __init__(self, session_id: str = None):
        super().__init__(session_id)
        self.workflow_stage_times = {}

    def start_workflow_stage(self, stage_name: str):
        """워크플로우 단계 시작"""
        self.workflow_stage_times[stage_name] = time.time()
        logger.info(f"[{self.session_id}] Workflow stage started: {stage_name}")

    def end_workflow_stage(self, stage_name: str, success: bool = True, metadata: Dict[str, Any] = None):
        """워크플로우 단계 종료"""
        if stage_name in self.workflow_stage_times:
            start_time = self.workflow_stage_times[stage_name]
            duration = time.time() - start_time

            self.add_manual_timing(
                step_name=f"workflow_{stage_name}",
                duration=duration,
                success=success,
                metadata=metadata
            )

            del self.workflow_stage_times[stage_name]
            logger.info(f"[{self.session_id}] Workflow stage completed: {stage_name} in {duration:.3f}s")


# 전역 성능 모니터 인스턴스 관리
_active_monitors: Dict[str, PerformanceMonitor] = {}

def get_performance_monitor(session_id: str) -> PerformanceMonitor:
    """세션별 성능 모니터 가져오기"""
    if session_id not in _active_monitors:
        _active_monitors[session_id] = WorkflowPerformanceMonitor(session_id)
    return _active_monitors[session_id]

def cleanup_performance_monitor(session_id: str):
    """성능 모니터 정리"""
    if session_id in _active_monitors:
        _active_monitors[session_id].log_performance_summary()
        del _active_monitors[session_id]

def get_all_performance_data() -> Dict[str, Any]:
    """모든 활성 세션의 성능 데이터 조회"""
    return {
        session_id: monitor.export_to_dict()
        for session_id, monitor in _active_monitors.items()
    }