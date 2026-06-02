"""
ModelRegistry — GPU 显存管理单例

管理 YOLO 和 SAM 模型的加载/卸载，确保:
1. 同一时间只有一个大模型在 GPU 上
2. 推理请求串行化（通过信号量）
3. 全局唯一实例（线程安全单例）
"""
import asyncio
import threading
from typing import Optional
from backend.cv.yolo_detector import YOLODetector
from backend.cv.sam_segmentor import SAMSegmentor


class ModelRegistry:
    """
    全局单例模型注册表。

    使用方式:
        registry = ModelRegistry()
        yolo = registry.get_yolo()   # 加载 YOLO
        sam  = registry.get_sam()    # 卸载 YOLO，加载 SAM
        registry.swap_to_yolo()      # 卸载 SAM，重新加载 YOLO
    """
    _instance: Optional["ModelRegistry"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ModelRegistry":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.yolo: Optional[YOLODetector] = None
        self.sam: Optional[SAMSegmentor] = None
        self._semaphore = asyncio.Semaphore(1)

    def get_yolo(self) -> YOLODetector:
        """获取 YOLO 检测器（如果还没加载则加载）"""
        if self.yolo is None:
            self.yolo = YOLODetector()
            try:
                self.yolo.load()
            except FileNotFoundError:
                print("[Registry] YOLO model file not found. "
                      "Will fall back to pre-trained weights.")
                # 即使模型文件不存在也创建实例，detect 时会用预训练
        return self.yolo

    def get_sam(self) -> SAMSegmentor:
        """
        获取 SAM 分割器。
        加载前自动卸载 YOLO 以释放显存。
        """
        # 先卸载 YOLO
        if self.yolo is not None and self.yolo.is_loaded:
            self.yolo.unload()

        if self.sam is None:
            self.sam = SAMSegmentor()
            self.sam.load()

        return self.sam

    def swap_to_yolo(self):
        """卸载 SAM，重新加载 YOLO"""
        if self.sam is not None:
            self.sam.unload()
        if self.yolo is None:
            self.yolo = YOLODetector()
        if not self.yolo.is_loaded:
            try:
                self.yolo.load()
            except FileNotFoundError:
                pass  # 允许无模型运行
        return self.yolo

    async def inference_guard(self, coro):
        """信号量保护：同一时间只允许一个 GPU 推理任务"""
        async with self._semaphore:
            return await coro

    def clear(self):
        """清理所有模型"""
        if self.yolo is not None and self.yolo.is_loaded:
            self.yolo.unload()
        if self.sam is not None:
            self.sam.unload()
        import torch
        torch.cuda.empty_cache()
