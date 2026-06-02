"""
三引擎融合检测 Pipeline

Phase 1: YOLOv8 粗检
Phase 2: OpenCV 精细测量（对每个 YOLO 检测结果）
Phase 3: OpenCV 独立扫盲区（颜色异常 + 丝印 OCR）
Phase 4: SAM 2.1 精准分割（高置信度缺陷 + 用户交互）
Phase 5: 融合判定（CONFIRMED / SUSPICIOUS / LIKELY_FP + 严重度）
"""
import time
import base64
import cv2
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from backend.cv.yolo_detector import YOLODetector, Detection
from backend.cv.sam_segmentor import SAMSegmentor
from backend.cv.opencv_rules import (
    Measurement,
    measure_solder_joint,
    measure_component_offset,
    detect_scratches,
    check_color_anomaly,
    ocr_part_number,
)
from backend.cv.registry import ModelRegistry


# ═══════════════════════════════════════════════════════════════
# 颜色常量（BGR 格式，用于标注图绘制）
# ═══════════════════════════════════════════════════════════════
COLORS = {
    "CONFIRMED": (0, 0, 255),     # 红色
    "SUSPICIOUS": (0, 165, 255),  # 橙色
    "LIKELY_FP": (128, 128, 128), # 灰色
    "INFO": (0, 255, 0),          # 绿色
    "WARN": (0, 255, 255),        # 黄色
    "CRITICAL": (0, 0, 255),      # 红色
    "user_selection": (255, 0, 255), # 紫色
}

CLASS_NAMES_ZH = {
    "missing_component": "缺件",
    "bridge": "桥接",
    "open_circuit": "开路",
    "offset": "偏移",
    "insufficient_solder": "少锡",
    "excess_solder": "多锡",
    "scratch": "划伤",
    "wrong_component": "错件",
    "color_anomaly": "颜色异常",
    "user_selection": "用户选择",
    "component": "元件",
}


@dataclass
class FusionResult:
    """融合检测完整结果"""
    defects: List[Detection]
    summary: dict
    annotated_image_b64: str
    processing_time_ms: float


def fusion_inspect(
    image: np.ndarray,
    golden_image: Optional[np.ndarray] = None,
    sam_interactive: bool = False,
    sam_point: Optional[Tuple[int, int]] = None,
    enable_sam: bool = True,
    conf_threshold: float = 0.25,
) -> FusionResult:
    """
    三引擎融合检测 pipeline。

    Args:
        image: BGR numpy array (H, W, 3)
        golden_image: 金板参考图（可选，用于颜色异常检测）
        sam_interactive: 是否为交互模式（响应用户点击）
        sam_point: 用户点击坐标 (x, y)，仅交互模式使用
        enable_sam: 是否启用 SAM
        conf_threshold: YOLO 置信度阈值

    Returns:
        FusionResult: 包含所有检测结果、汇总和标注图
    """
    t_start = time.time()
    registry = ModelRegistry()

    detections: List[Detection] = []

    # ═══ Phase 1: YOLO 粗检 ═══
    try:
        yolo = registry.get_yolo()
        if yolo.model_path and yolo.is_loaded:
            yolo_dets = yolo.detect(image, conf_threshold=conf_threshold)
        else:
            # 无微调模型 → 用预训练做通用检测
            yolo_dets = yolo.detect_with_pre_trained(image)
        detections.extend(yolo_dets)
        print(f"[Fusion] Phase 1: YOLO found {len(yolo_dets)} candidates")
    except Exception as e:
        print(f"[Fusion] Phase 1 YOLO failed: {e}")
        # YOLO 失败不阻塞，OpenCV 还能独立工作

    # ═══ Phase 2: OpenCV 精细测量 ═══
    for det in detections:
        roi = det.roi
        if roi is None or roi.size == 0:
            continue

        cls = det.class_name
        if cls in ("insufficient_solder", "excess_solder"):
            det.measurements["solder"] = measure_solder_joint(roi)
        elif cls == "offset":
            det.measurements["offset"] = measure_component_offset(roi)
        elif cls == "scratch":
            det.measurements["scratch"] = detect_scratches(roi)

        # 对所有有文字区域的元件做 OCR
        h, w = roi.shape[:2]
        if w > 30 and h > 15:  # 太小的区域做 OCR 没意义
            ocr_result = ocr_part_number(roi)
            if ocr_result.get("recognized_text"):
                det.measurements["ocr"] = ocr_result

    # ═══ Phase 3: OpenCV 独立扫盲区 ═══
    blind_spot_count = 0
    if golden_image is not None:
        try:
            color_result = check_color_anomaly(image, golden_image)
            if not color_result.passed:
                h, w = image.shape[:2]
                detections.append(Detection(
                    bbox=[0, 0, w, h],
                    class_name="color_anomaly",
                    confidence=0.6,
                    roi=image,
                    measurements={"color": color_result},
                    verdict="SUSPICIOUS",
                    severity="WARN",
                ))
                blind_spot_count += 1
        except Exception as e:
            print(f"[Fusion] Phase 3 color check failed: {e}")

    print(f"[Fusion] Phase 3: OpenCV blind spot found {blind_spot_count} issues")

    # ═══ Phase 4: SAM 2.1 精准分割 ═══
    sam = None
    try:
        if enable_sam:
            sam = registry.get_sam()
    except RuntimeError as e:
        print(f"[Fusion] SAM not available: {e}")
        sam = None

    if sam is not None:
        try:
            if sam_interactive and sam_point is not None:
                # 交互模式：用户点击 → 分割
                sam.set_image(image)
                mask = sam.segment_with_point(*sam_point)
                px, py = sam_point
                detections.append(Detection(
                    bbox=[px - 50, py - 50, px + 50, py + 50],
                    class_name="user_selection",
                    confidence=1.0,
                    roi=None,
                    measurements={"sam_segmented": True},
                    mask=mask,
                    verdict="CONFIRMED",
                    severity="INFO",
                ))
            else:
                # 自动模式：高置信度缺陷 → SAM 确认
                high_conf = [d for d in detections if d.confidence > 0.7 and d.mask is None]
                if high_conf:
                    sam.set_image(image)
                    for det in high_conf:
                        det.mask = sam.segment_with_box(det.bbox)
                        precise_area_px = int(np.sum(det.mask))
                        det.measurements["sam_area"] = {
                            "value": precise_area_px,
                            "unit": "px",
                        }
                        # SAM 确认 → 提升置信度
                        det.confidence = min(1.0, det.confidence * 1.1)
            print(f"[Fusion] Phase 4: SAM segmentation done")
        except Exception as e:
            print(f"[Fusion] Phase 4 SAM failed (non-blocking): {e}")

    # ═══ Phase 5: 融合判定 ═══
    for det in detections:
        has_yolo = det.confidence > 0.5
        has_opencv = len(det.measurements) > 0 and any(
            k not in ("ocr", "sam_area") for k in det.measurements
        )
        has_sam = det.mask is not None
        is_user_select = det.class_name == "user_selection"

        if is_user_select:
            det.verdict = "CONFIRMED"
        elif has_sam or (has_yolo and has_opencv):
            det.verdict = "CONFIRMED"
        elif has_yolo or has_opencv:
            det.verdict = "SUSPICIOUS"
        else:
            det.verdict = "LIKELY_FP"

        # 严重度评定
        if det.verdict == "CONFIRMED":
            any_measure_fail = any(
                not m.passed
                for m in det.measurements.values()
                if isinstance(m, Measurement) and not m.passed
            )
            det.severity = "CRITICAL" if any_measure_fail else "WARN"
        elif det.verdict == "SUSPICIOUS":
            det.severity = "WARN"
        else:
            det.severity = "INFO"

    # ═══ 汇总统计 ═══
    defect_types = {}
    for d in detections:
        defect_types[d.class_name] = defect_types.get(d.class_name, 0) + 1

    summary = {
        "total": len(detections),
        "confirmed": sum(1 for d in detections if d.verdict == "CONFIRMED"),
        "suspicious": sum(1 for d in detections if d.verdict == "SUSPICIOUS"),
        "likely_fp": sum(1 for d in detections if d.verdict == "LIKELY_FP"),
        "critical": sum(1 for d in detections if d.severity == "CRITICAL"),
        "by_type": defect_types,
        "overall_severity": _overall_severity(detections),
    }

    # ═══ 标注图 ═══
    annotated = draw_annotations(image, detections)

    t_end = time.time()
    result = FusionResult(
        defects=detections,
        summary=summary,
        annotated_image_b64=annotated,
        processing_time_ms=(t_end - t_start) * 1000,
    )

    print(f"[Fusion] Done in {result.processing_time_ms:.0f}ms. "
          f"Total={summary['total']}, Confirmed={summary['confirmed']}, "
          f"Severity={summary['overall_severity']}")

    # 推理完成后切回 YOLO（如果 SAM 还在显存里）
    registry.swap_to_yolo()

    return result


def _overall_severity(detections: List[Detection]) -> str:
    """计算整体严重度"""
    has_critical = any(d.severity == "CRITICAL" for d in detections)
    has_warn = any(d.severity == "WARN" for d in detections)
    if has_critical:
        return "CRITICAL"
    if has_warn:
        return "WARN"
    return "INFO"


# ═══════════════════════════════════════════════════════════════
# 标注图绘制
# ═══════════════════════════════════════════════════════════════

def draw_annotations(image: np.ndarray, detections: List[Detection]) -> str:
    """
    在图像上绘制检测标注（bbox + mask + 标签），返回 base64 PNG。
    """
    img = image.copy()
    overlay = img.copy()

    for det in detections:
        color = COLORS.get(det.severity, (128, 128, 128))
        x1, y1, x2, y2 = map(int, det.bbox)

        # 绘制 SAM mask（半透明）
        if det.mask is not None:
            mask_resized = cv2.resize(
                det.mask.astype(np.uint8),
                (x2 - x1, y2 - y1),
                interpolation=cv2.INTER_NEAREST,
            )
            colored_mask = np.zeros((y2 - y1, x2 - x1, 3), dtype=np.uint8)
            colored_mask[mask_resized > 0] = color
            overlay[y1:y2, x1:x2] = cv2.addWeighted(
                overlay[y1:y2, x1:x2], 0.6,
                colored_mask, 0.4, 0,
            )

        # 绘制 bbox
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

    # 融合 overlay
    img = cv2.addWeighted(overlay, 0.5, img, 0.5, 0)

    # 绘制标签
    for det in detections:
        x1, y1, x2, y2 = map(int, det.bbox)
        label = f"{CLASS_NAMES_ZH.get(det.class_name, det.class_name)} {det.confidence:.2f}"
        label_y = y1 - 10 if y1 > 20 else y1 + 20
        cv2.putText(img, label, (x1, label_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS.get(det.severity), 2)

    # 编码为 base64
    _, buffer = cv2.imencode('.png', img)
    b64_str = base64.b64encode(buffer).decode('utf-8')
    return b64_str
