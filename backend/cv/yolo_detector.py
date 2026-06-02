"""
YOLOv8 目标检测器 — 负责快速定位 PCB 缺陷区域
"""
from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np
from backend.config import (
    YOLO_MODEL_PATH, YOLO_CONF_THRESHOLD, YOLO_IOU_THRESHOLD, YOLO_IMG_SIZE
)


@dataclass
class Detection:
    """单个检测结果"""
    bbox: List[float]          # [x1, y1, x2, y2] 绝对像素坐标
    class_name: str            # 缺陷类别名
    confidence: float          # 置信度 [0, 1]
    roi: Optional[np.ndarray] = None       # 裁剪的 ROI 区域
    measurements: dict = field(default_factory=dict)  # OpenCV 测量值
    mask: Optional[np.ndarray] = None      # SAM 分割 mask
    verdict: str = "SUSPICIOUS"            # CONFIRMED | SUSPICIOUS | LIKELY_FP
    severity: str = "INFO"                 # INFO | WARN | CRITICAL


class YOLODetector:
    """YOLOv8 封装，支持 PyTorch 和 ONNX 推理"""

    def __init__(self, model_path: str = YOLO_MODEL_PATH):
        self.model_path = model_path
        self.model = None

    def load(self):
        """加载模型到 GPU"""
        from ultralytics import YOLO
        self.model = YOLO(self.model_path)
        self.model.to("cuda")
        print(f"[YOLO] Model loaded: {self.model_path}")

    def unload(self):
        """从 GPU 卸载"""
        if self.model is not None:
            del self.model
            self.model = None
            import torch
            torch.cuda.empty_cache()
            print("[YOLO] Model unloaded")

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    def detect(
        self,
        image: np.ndarray,
        conf_threshold: float = YOLO_CONF_THRESHOLD,
        iou_threshold: float = YOLO_IOU_THRESHOLD,
    ) -> List[Detection]:
        """
        对单张图像执行目标检测。

        Args:
            image: BGR numpy array (H, W, 3)
            conf_threshold: 置信度阈值
            iou_threshold: NMS IoU 阈值

        Returns:
            Detection 列表，按置信度降序排列
        """
        if self.model is None:
            self.load()

        results = self.model(
            image,
            conf=conf_threshold,
            iou=iou_threshold,
            imgsz=YOLO_IMG_SIZE,
            verbose=False,
        )

        detections = []
        for r in results:
            boxes = r.boxes
            if boxes is None:
                continue
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                class_name = self.model.names.get(cls_id, f"class_{cls_id}")

                detections.append(Detection(
                    bbox=[x1, y1, x2, y2],
                    class_name=class_name,
                    confidence=conf,
                    roi=image[y1:y2, x1:x2].copy(),
                ))

        return sorted(detections, key=lambda d: d.confidence, reverse=True)

    def detect_with_pre_trained(
        self,
        image: np.ndarray,
        conf_threshold: float = YOLO_CONF_THRESHOLD,
    ) -> List[Detection]:
        """
        使用预训练 YOLOv8 做通用检测（不针对 PCB 微调时用）。
        检测 PCB 上通用元件区域，不区分缺陷类型。
        """
        if self.model is None:
            self.load()

        results = self.model(
            image,
            conf=conf_threshold,
            iou=YOLO_IOU_THRESHOLD,
            imgsz=YOLO_IMG_SIZE,
            verbose=False,
        )

        detections = []
        for r in results:
            boxes = r.boxes
            if boxes is None:
                continue
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])

                detections.append(Detection(
                    bbox=[x1, y1, x2, y2],
                    class_name="component",  # 通用标签
                    confidence=conf,
                    roi=image[y1:y2, x1:x2].copy(),
                ))

        return sorted(detections, key=lambda d: d.confidence, reverse=True)
