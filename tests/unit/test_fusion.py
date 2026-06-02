"""融合 Pipeline 逻辑测试（不需要 GPU）"""
import numpy as np
from backend.cv.fusion import (
    _overall_severity,
    draw_annotations,
    CLASS_NAMES_ZH,
    COLORS,
)
from backend.cv.yolo_detector import Detection


class TestSeverityLogic:
    """严重度判定逻辑"""

    def test_no_defects_info(self):
        """无缺陷→INFO"""
        assert _overall_severity([]) == "INFO"

    def test_only_info_defects(self):
        """只有 INFO→INFO"""
        dets = [
            Detection(bbox=[0,0,10,10], class_name="test", confidence=0.3, severity="INFO"),
            Detection(bbox=[20,20,30,30], class_name="test", confidence=0.4, severity="INFO"),
        ]
        assert _overall_severity(dets) == "INFO"

    def test_one_critical_escalates(self):
        """有 CRITICAL→CRITICAL"""
        dets = [
            Detection(bbox=[0,0,10,10], class_name="test", confidence=0.3, severity="INFO"),
            Detection(bbox=[20,20,30,30], class_name="test", confidence=0.9, severity="CRITICAL"),
        ]
        assert _overall_severity(dets) == "CRITICAL"

    def test_warn_without_critical(self):
        """只有 WARN→WARN"""
        dets = [
            Detection(bbox=[0,0,10,10], class_name="test", confidence=0.3, severity="INFO"),
            Detection(bbox=[20,20,30,30], class_name="test", confidence=0.7, severity="WARN"),
        ]
        assert _overall_severity(dets) == "WARN"


class TestDrawAnnotations:
    """标注图绘制"""

    def test_returns_base64_string(self, sample_pcb_image):
        """应返回有效的 base64 字符串"""
        detections = [
            Detection(bbox=[50,50,120,120], class_name="bridge", confidence=0.92,
                      severity="CRITICAL", verdict="CONFIRMED", mask=None),
        ]
        result = draw_annotations(sample_pcb_image, detections)
        assert isinstance(result, str)
        assert len(result) > 100  # base64 应该有内容

    def test_with_mask(self, sample_pcb_image):
        """带 mask 的检测应正常绘制"""
        h, w = 70, 70
        mask = np.zeros((h, w), dtype=bool)
        mask[10:50, 10:50] = True
        detections = [
            Detection(bbox=[50,50,120,120], class_name="offset", confidence=0.85,
                      severity="WARN", verdict="CONFIRMED", mask=mask),
        ]
        result = draw_annotations(sample_pcb_image, detections)
        assert isinstance(result, str)
        assert len(result) > 100

    def test_empty_detections(self, sample_pcb_image):
        """空检测列表应返回无标注图"""
        result = draw_annotations(sample_pcb_image, [])
        assert isinstance(result, str)


class TestClassNames:
    """类别名映射"""

    def test_all_classes_have_chinese(self):
        """所有已知类别应有中文翻译"""
        known = ["bridge", "offset", "scratch", "missing_component",
                 "insufficient_solder", "excess_solder",
                 "open_circuit", "wrong_component", "color_anomaly", "user_selection"]
        for cls in known:
            assert cls in CLASS_NAMES_ZH, f"Missing Chinese name for {cls}"


class TestColors:
    """颜色定义"""

    def test_all_verdicts_have_colors(self):
        """所有判定应有对应颜色"""
        for verdict in ["CONFIRMED", "SUSPICIOUS", "LIKELY_FP"]:
            assert verdict in COLORS, f"Missing color for {verdict}"

    def test_severity_levels_have_colors(self):
        """所有严重度应有对应颜色"""
        for sev in ["INFO", "WARN", "CRITICAL"]:
            assert sev in COLORS, f"Missing color for {sev}"
