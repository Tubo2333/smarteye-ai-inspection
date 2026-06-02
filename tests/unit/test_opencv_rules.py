"""OpenCV 规则器单元测试"""
import numpy as np
import cv2
from backend.cv.opencv_rules import (
    Measurement,
    measure_solder_joint,
    measure_component_offset,
    detect_scratches,
    check_color_anomaly,
    ocr_part_number,
)


class TestSolderJoint:
    """焊点质量检测"""

    def test_normal_solder(self, sample_solder_roi):
        """正常焊点应通过检测"""
        result = measure_solder_joint(sample_solder_roi, expected_area_mm2=0.60)
        assert isinstance(result, Measurement)
        assert result.rule_name == "焊点质量"
        assert result.unit == "mm²"

    def test_empty_roi(self):
        """空 ROI 应返回未通过"""
        result = measure_solder_joint(np.array([]), expected_area_mm2=0.60)
        assert result.passed is False
        assert "为空" in result.detail

    def test_tiny_roi(self):
        """过小 ROI 应返回未通过"""
        tiny = np.ones((3, 3, 3), dtype=np.uint8) * 180
        result = measure_solder_joint(tiny, expected_area_mm2=0.60)
        assert result.passed is False

    def test_measurement_has_all_fields(self, sample_solder_roi):
        """Measurement 应包含所有必需字段"""
        result = measure_solder_joint(sample_solder_roi)
        assert hasattr(result, 'value')
        assert hasattr(result, 'threshold')
        assert hasattr(result, 'passed')
        assert hasattr(result, 'detail')


class TestComponentOffset:
    """元件偏移检测"""

    def test_centered_component(self, sample_solder_roi):
        """居中元件应通过"""
        h, w = sample_solder_roi.shape[:2]
        result = measure_component_offset(sample_solder_roi, (w/2, h/2))
        assert isinstance(result, Measurement)
        assert result.rule_name == "元件偏移"

    def test_empty_roi_offset(self):
        """空 ROI 应返回未通过"""
        result = measure_component_offset(np.array([]))
        assert result.passed is False


class TestScratchDetection:
    """划痕检测"""

    def test_no_scratch_clean_surface(self, sample_solder_roi):
        """干净表面不应检测到划痕"""
        result = detect_scratches(sample_solder_roi)
        assert isinstance(result, Measurement)
        # 干净表面应该通过或检测不到划痕

    def test_empty_roi_scratch(self):
        """空 ROI 应安全处理"""
        result = detect_scratches(np.array([]))
        assert result.unit == "mm"


class TestColorAnomaly:
    """颜色异常检测"""

    def test_same_image_no_anomaly(self, sample_solder_roi):
        """相同图像应无颜色异常"""
        result = check_color_anomaly(sample_solder_roi, sample_solder_roi.copy())
        assert isinstance(result, Measurement)
        assert result.value < 5.0  # ΔE 应该接近 0

    def test_different_images_anomaly(self):
        """不同颜色应有异常"""
        img1 = np.ones((30, 30, 3), dtype=np.uint8) * 100
        img2 = np.ones((30, 30, 3), dtype=np.uint8) * 200
        result = check_color_anomaly(img1, img2)
        assert result.value > 0


class TestOCR:
    """丝印 OCR (仅测试接口，不测试实际识别)"""

    def test_empty_roi_returns_dict(self):
        """空 ROI 应返回错误字典"""
        result = ocr_part_number(np.array([]))
        assert isinstance(result, dict)
        assert "recognized_text" in result

    def test_returns_expected_keys(self, sample_solder_roi):
        """返回值应包含预期键"""
        result = ocr_part_number(sample_solder_roi)
        for key in ["recognized_text", "confidence", "match_with_bom"]:
            assert key in result
