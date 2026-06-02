"""LangGraph 编排流程集成测试（不需要 API Key）"""
import pytest
from backend.orchestrator.graph import (
    _parse_next_agent,
    _rule_based_routing,
    _format_detections_for_analysis,
    _basic_analysis,
)
from backend.orchestrator.state import create_initial_state


class TestParseNextAgent:
    """Supervisor 输出解析"""

    def test_parses_next_inspection(self):
        result = _parse_next_agent("NEXT: inspection")
        assert result == "inspection"

    def test_parses_next_end(self):
        result = _parse_next_agent("NEXT: END")
        assert result == "END"

    def test_parses_case_insensitive(self):
        result = _parse_next_agent("next: REPORT")
        assert result == "report"

    def test_fallback_scan(self):
        """没有 NEXT: 前缀时，扫描文本中的 agent 名"""
        result = _parse_next_agent("I think we should go to analysis now")
        assert result == "analysis"

    def test_default_to_end(self):
        result = _parse_next_agent("something completely unrelated")
        assert result == "END"


class TestRuleBasedRouting:
    """Fallback 路由规则"""

    def test_has_image_goes_to_inspection(self):
        """有图片无检测→inspection"""
        state = create_initial_state(task_id="t1", task_type="inspection", image_b64="fake")
        result = _rule_based_routing(state)
        assert result["next_agent"] == "inspection"

    def test_has_detections_goes_to_report(self):
        """有检测结果无报告→report"""
        state = create_initial_state(task_id="t2", task_type="inspection")
        state["detections"] = [{"class_name": "bridge"}]
        state["detection_summary"] = {"critical": 0}
        result = _rule_based_routing(state)
        assert result["next_agent"] == "report"

    def test_critical_triggers_alert(self):
        """CRITICAL 缺陷→先告警"""
        state = create_initial_state(task_id="t3", task_type="inspection")
        state["detections"] = [{"class_name": "bridge"}]
        state["detection_summary"] = {"critical": 2}
        result = _rule_based_routing(state)
        assert result["next_agent"] == "alert"

    def test_retry_limit_gives_up(self):
        """重试超过 2 次→降级"""
        state = create_initial_state(task_id="t4", task_type="inspection", image_b64="fake")
        state["retry_count"] = 3
        result = _rule_based_routing(state)
        # 应该放弃检测，直接路由到 report
        assert result["next_agent"] == "report"

    def test_completed_task_ends(self):
        """已完成→END"""
        state = create_initial_state(task_id="t5", task_type="inspection")
        state["detections"] = []
        state["report_markdown"] = "report"
        state["alert_triggered"] = True
        result = _rule_based_routing(state)
        assert result["next_agent"] == "END"


class TestFormatDetections:
    """检测结果格式化"""

    def test_formats_empty(self):
        result = _format_detections_for_analysis([])
        assert "无检测结果" in result

    def test_formats_list(self):
        detections = [
            {"class_name": "bridge", "confidence": 0.92, "verdict": "CONFIRMED", "severity": "CRITICAL"},
            {"class_name": "offset", "confidence": 0.65, "verdict": "SUSPICIOUS", "severity": "WARN"},
        ]
        result = _format_detections_for_analysis(detections)
        assert "bridge" in result
        assert "offset" in result
        assert "0.92" in result
        assert "CRITICAL" in result


class TestBasicAnalysis:
    """基本统计分析"""

    def test_empty(self):
        result = _basic_analysis([], {"total": 0, "confirmed": 0, "critical": 0})
        assert result["total"] == 0
        assert result["is_systemic"] is False

    def test_systemic_detection(self):
        """多缺陷+严重→系统性异常"""
        detections = [
            {"class_name": "bridge"}, {"class_name": "bridge"},
            {"class_name": "bridge"}, {"class_name": "bridge"},
            {"class_name": "bridge"},
        ]
        summary = {"total": 5, "confirmed": 5, "critical": 3}
        result = _basic_analysis(detections, summary)
        assert result["is_systemic"] is True
        assert "系统性异常" in result["conclusion"]

    def test_not_systemic(self):
        """少量缺陷→非系统性"""
        detections = [{"class_name": "scratch"}]
        summary = {"total": 1, "confirmed": 1, "critical": 0}
        result = _basic_analysis(detections, summary)
        assert result["is_systemic"] is False
