"""Pytest fixtures — 共享测试资源"""
import sys
import os
import pytest
import numpy as np
import cv2
from pathlib import Path

# 确保项目根目录在 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_pcb_image():
    """生成一张简单的模拟 PCB 图像 (BGR)"""
    img = np.zeros((300, 400, 3), dtype=np.uint8)
    img[:, :] = (47, 107, 47)  # PCB 绿色基板

    # 画几个焊盘
    cv2.rectangle(img, (50, 50), (120, 80), (66, 170, 255), -1)   # 金色焊盘
    cv2.rectangle(img, (50, 90), (120, 120), (66, 170, 255), -1)
    cv2.rectangle(img, (200, 50), (270, 80), (66, 170, 255), -1)
    cv2.rectangle(img, (200, 90), (270, 120), (66, 170, 255), -1)

    # 画几个芯片
    cv2.rectangle(img, (55, 55), (115, 115), (30, 30, 30), -1)
    cv2.rectangle(img, (205, 55), (265, 115), (30, 30, 30), -1)

    return img


@pytest.fixture
def sample_solder_roi():
    """生成一个模拟的焊点 ROI（正常焊点）"""
    roi = np.ones((60, 80, 3), dtype=np.uint8) * 47  # PCB 绿色背景
    roi[10:50, 15:65] = (180, 180, 180)  # 锡膏灰色矩形
    return roi


@pytest.fixture
def sample_defect_roi():
    """生成一个模拟的缺陷焊点 ROI（少锡）"""
    roi = np.ones((60, 80, 3), dtype=np.uint8) * 47
    roi[20:40, 20:50] = (180, 180, 180)  # 锡膏区域较小
    return roi


@pytest.fixture
def sample_detections():
    """生成模拟的 YOLO 检测结果列表"""
    from backend.cv.yolo_detector import Detection
    return [
        Detection(bbox=[50, 50, 120, 120], class_name="bridge", confidence=0.92,
                  roi=np.ones((70, 70, 3), dtype=np.uint8) * 100),
        Detection(bbox=[200, 50, 270, 120], class_name="offset", confidence=0.78,
                  roi=np.ones((70, 70, 3), dtype=np.uint8) * 100),
        Detection(bbox=[300, 200, 350, 250], class_name="insufficient_solder", confidence=0.65,
                  roi=np.ones((50, 50, 3), dtype=np.uint8) * 100),
    ]
