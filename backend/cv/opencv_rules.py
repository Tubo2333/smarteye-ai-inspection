"""
OpenCV 规则检测引擎 — 5 个传统计算机视觉规则器
用于精确测量缺陷严重度，互补 YOLO 的检测

每个规则器返回一个 Measurement 对象，包含测量值、阈值和判定结果。
"""
from dataclasses import dataclass
from typing import Optional, Tuple
import cv2
import numpy as np
from backend.config import (
    SOLDER_AREA_MIN_RATIO,
    SOLDER_CIRCULARITY_MIN,
    COMPONENT_OFFSET_MAX_RATIO,
    SCRATCH_MAX_LENGTH_MM,
    COLOR_DELTA_E_THRESHOLD,
)


@dataclass
class Measurement:
    """OpenCV 测量结果"""
    rule_name: str
    value: float
    unit: str
    threshold: float
    passed: bool
    detail: str


# ═══════════════════════════════════════════════════════════════
# 规则器 1: 焊点质量检测
# ═══════════════════════════════════════════════════════════════

def measure_solder_joint(
    roi: np.ndarray,
    expected_area_mm2: float = 0.60,
    px_to_mm: float = 0.01,
) -> Measurement:
    """
    焊点质量检测。
    方法: HSV 阈值分割锡膏区域 → 轮廓检测 → 计算面积和圆度
    判定标准:
      - 面积 < 标准面积 × SOLDER_AREA_MIN_RATIO → 少锡
      - circularity < SOLDER_CIRCULARITY_MIN → 形状不良
    """
    if roi.size == 0:
        return Measurement("焊点质量", 0.0, "mm²", expected_area_mm2 * SOLDER_AREA_MIN_RATIO, False, "ROI 为空")

    h, w = roi.shape[:2]
    if h < 5 or w < 5:
        return Measurement("焊点质量", 0.0, "mm²", expected_area_mm2 * SOLDER_AREA_MIN_RATIO, False, "ROI 过小")

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # 锡膏的 HSV 范围 — 浅灰色金属区域
    # 实际 PCB 可能需要根据光照条件调整
    lower = np.array([0, 0, 140])
    upper = np.array([180, 40, 255])
    mask = cv2.inRange(hsv, lower, upper)

    # 形态学去噪
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return Measurement("焊点质量", 0.0, "mm²", expected_area_mm2 * SOLDER_AREA_MIN_RATIO, False, "未检测到锡膏区域")

    largest = max(contours, key=cv2.contourArea)
    area_px = cv2.contourArea(largest)
    perimeter = cv2.arcLength(largest, True)

    if perimeter == 0:
        return Measurement("焊点质量", 0.0, "mm²", expected_area_mm2 * SOLDER_AREA_MIN_RATIO, False, "轮廓周长为零")

    circularity = 4 * np.pi * area_px / (perimeter * perimeter)

    area_mm2 = area_px * px_to_mm * px_to_mm
    area_min = expected_area_mm2 * SOLDER_AREA_MIN_RATIO
    area_ok = area_mm2 >= area_min
    shape_ok = circularity >= SOLDER_CIRCULARITY_MIN
    passed = area_ok and shape_ok

    issues = []
    if not area_ok:
        ratio_pct = int((area_mm2 / expected_area_mm2) * 100)
        issues.append(f"面积仅标准的{ratio_pct}%")
    if not shape_ok:
        issues.append(f"圆度不良({circularity:.2f})")

    detail = "; ".join(issues) if issues else f"面积={area_mm2:.3f}mm², 圆度={circularity:.3f}"

    return Measurement(
        rule_name="焊点质量",
        value=round(area_mm2, 4),
        unit="mm²",
        threshold=round(area_min, 4),
        passed=passed,
        detail=detail,
    )


# ═══════════════════════════════════════════════════════════════
# 规则器 2: 元件偏移检测
# ═══════════════════════════════════════════════════════════════

def measure_component_offset(
    roi: np.ndarray,
    expected_center: Optional[Tuple[float, float]] = None,
) -> Measurement:
    """
    元件偏移检测。
    方法: 阈值分割找元件轮廓 → 计算质心 → 与期望位置比较
    判定: 偏移量 / 元件短边 > COMPONENT_OFFSET_MAX_RATIO → 偏移
    """
    if roi.size == 0:
        return Measurement("元件偏移", float('inf'), "px", 0.15, False, "ROI 为空")

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return Measurement("元件偏移", float('inf'), "px", COMPONENT_OFFSET_MAX_RATIO, False, "未检测到元件")

    largest = max(contours, key=cv2.contourArea)
    M = cv2.moments(largest)

    if M["m00"] == 0:
        return Measurement("元件偏移", float('inf'), "px", COMPONENT_OFFSET_MAX_RATIO, False, "无法计算质心")

    cx = M["m10"] / M["m00"]
    cy = M["m01"] / M["m00"]

    # 如果没给期望位置，默认用 ROI 中心
    h, w = roi.shape[:2]
    if expected_center is None:
        expected_center = (w / 2, h / 2)

    dx = cx - expected_center[0]
    dy = cy - expected_center[1]
    offset = np.sqrt(dx**2 + dy**2)

    x, y, w_rect, h_rect = cv2.boundingRect(largest)
    ref_size = min(w_rect, h_rect)

    if ref_size == 0:
        return Measurement("元件偏移", float('inf'), "px", COMPONENT_OFFSET_MAX_RATIO, False, "参考尺寸为零")

    offset_ratio = offset / ref_size
    passed = offset_ratio <= COMPONENT_OFFSET_MAX_RATIO

    return Measurement(
        rule_name="元件偏移",
        value=round(offset, 1),
        unit="px",
        threshold=round(ref_size * COMPONENT_OFFSET_MAX_RATIO, 1),
        passed=passed,
        detail=f"dx={dx:.1f}, dy={dy:.1f}, 偏移={offset:.1f}px ({offset_ratio*100:.0f}% 元件尺寸)",
    )


# ═══════════════════════════════════════════════════════════════
# 规则器 3: 划痕检测
# ═══════════════════════════════════════════════════════════════

def detect_scratches(
    roi: np.ndarray,
    px_to_mm: float = 0.01,
) -> Measurement:
    """
    划痕检测。
    方法: Canny 边缘检测 → Hough 直线检测 → 统计最长划痕长度
    判定: 划痕长度 > SCRATCH_MAX_LENGTH_MM
    """
    if roi.size == 0:
        return Measurement("划痕", 0.0, "mm", SCRATCH_MAX_LENGTH_MM, True, "ROI 为空")

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    # Hough 直线检测
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=50,
        minLineLength=30,
        maxLineGap=10,
    )

    if lines is None:
        return Measurement("划痕", 0.0, "mm", SCRATCH_MAX_LENGTH_MM, True, "未检测到划痕")

    max_len_px = 0
    for line in lines:
        x1, y1, x2, y2 = line[0]
        length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        max_len_px = max(max_len_px, length)

    length_mm = max_len_px * px_to_mm
    passed = length_mm <= SCRATCH_MAX_LENGTH_MM

    return Measurement(
        rule_name="划痕",
        value=round(length_mm, 2),
        unit="mm",
        threshold=SCRATCH_MAX_LENGTH_MM,
        passed=passed,
        detail=f"最长划痕={length_mm:.2f}mm",
    )


# ═══════════════════════════════════════════════════════════════
# 规则器 4: 颜色异常检测
# ═══════════════════════════════════════════════════════════════

def check_color_anomaly(
    roi: np.ndarray,
    golden_roi: np.ndarray,
) -> Measurement:
    """
    颜色异常检测。
    方法: Lab 色彩空间 → 与金板比对 ΔE
    判定: 平均 ΔE > COLOR_DELTA_E_THRESHOLD
    """
    if roi.size == 0 or golden_roi.size == 0:
        return Measurement("颜色异常", 0.0, "ΔE", COLOR_DELTA_E_THRESHOLD, True, "ROI 或金板为空")

    # 统一尺寸
    if roi.shape != golden_roi.shape:
        golden_roi = cv2.resize(golden_roi, (roi.shape[1], roi.shape[0]))

    lab_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2Lab).astype(np.float32)
    lab_golden = cv2.cvtColor(golden_roi, cv2.COLOR_BGR2Lab).astype(np.float32)

    diff = cv2.absdiff(lab_roi, lab_golden)
    delta_e = float(np.mean(np.sqrt(np.sum(diff ** 2, axis=2))))

    passed = delta_e <= COLOR_DELTA_E_THRESHOLD

    return Measurement(
        rule_name="颜色异常",
        value=round(delta_e, 1),
        unit="ΔE",
        threshold=COLOR_DELTA_E_THRESHOLD,
        passed=passed,
        detail=f"平均色差={delta_e:.1f} ΔE",
    )


# ═══════════════════════════════════════════════════════════════
# 规则器 5: 丝印 OCR
# ═══════════════════════════════════════════════════════════════

def ocr_part_number(
    roi: np.ndarray,
    expected_text: Optional[str] = None,
) -> dict:
    """
    丝印文字识别。
    方法: PaddleOCR 识别 → 与 BOM 表预期文字比对
    返回: {recognized_text, confidence, match_with_bom}

    注意: PaddleOCR 首次调用会下载模型 (~100MB)，需要联网。
    """
    if roi.size == 0:
        return {"recognized_text": "", "confidence": 0.0, "match_with_bom": False, "error": "ROI 为空"}

    try:
        from paddleocr import PaddleOCR
        # 使用全局单例避免重复加载
        ocr = _get_ocr_instance()
        results = ocr.ocr(roi, cls=False)

        if not results or not results[0]:
            return {"recognized_text": "", "confidence": 0.0, "match_with_bom": False}

        text = " ".join([line[1][0] for line in results[0]])
        confidences = [line[1][1] for line in results[0]]
        confidence = float(np.mean(confidences)) if confidences else 0.0

        match = False
        if expected_text:
            match = text.strip().upper() == expected_text.strip().upper()

        return {
            "recognized_text": text,
            "confidence": round(confidence, 3),
            "match_with_bom": match,
        }
    except ImportError:
        return {"recognized_text": "", "confidence": 0.0, "match_with_bom": False, "error": "PaddleOCR 未安装"}
    except Exception as e:
        return {"recognized_text": "", "confidence": 0.0, "match_with_bom": False, "error": str(e)}


_ocr_instance = None

def _get_ocr_instance():
    """PaddleOCR 全局单例"""
    global _ocr_instance
    if _ocr_instance is None:
        from paddleocr import PaddleOCR
        _ocr_instance = PaddleOCR(lang='en', use_angle_cls=False, show_log=False)
    return _ocr_instance
