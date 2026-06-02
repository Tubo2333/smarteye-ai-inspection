"""
SAM 分割器 — 支持 SAM 2.1 → SAM 1 → MobileSAM 三级 fallback

所有变体通过统一接口 (set_image / segment_with_box / segment_with_point) 暴露，
切换对调用者完全透明。
"""
from typing import List, Optional, Tuple
import numpy as np
from backend.config import SAM_VARIANT, SAM_FALLBACK_CHAIN


class SAMSegmentor:
    """
    SAM 分割器，三级 fallback 链。
    使用方式:
        seg = SAMSegmentor()
        seg.load()                    # 按 fallback 链尝试加载
        seg.set_image(image)
        mask = seg.segment_with_box([x1, y1, x2, y2])
        # 或
        mask = seg.segment_with_point(x, y)
        seg.unload()
    """

    FALLBACK_VARIANTS = [
        {
            "name": "SAM 2.1",
            "build_method": "_build_sam2",
            "model_file": "sam2_hiera_small.pt",
            "config_file": "sam2_hiera_small.yaml",
        },
        {
            "name": "SAM 1 (vit_h)",
            "build_method": "_build_sam1",
            "model_file": "sam_vit_h_4b8939.pth",
            "model_type": "vit_h",
        },
        {
            "name": "MobileSAM",
            "build_method": "_build_mobile_sam",
            "model_file": "mobile_sam.pt",
            "model_type": "vit_t",
        },
    ]

    def __init__(self):
        self.model = None
        self.predictor = None
        self.active_variant: Optional[str] = None
        self._image_set = False

    def load(self) -> str:
        """按 fallback 链尝试加载模型，返回实际加载的变体名"""
        for variant in self.FALLBACK_VARIANTS:
            try:
                build_method = getattr(self, variant["build_method"])
                build_method(variant)
                self.active_variant = variant["name"]
                print(f"[SAM] Loaded: {variant['name']}")
                return variant["name"]
            except (ImportError, FileNotFoundError, OSError, RuntimeError) as e:
                print(f"[SAM] {variant['name']} 不可用: {e}")
                continue

        raise RuntimeError(
            "所有 SAM 变体加载失败。请确保至少安装了以下之一:\n"
            "  pip install sam2  (SAM 2.1)\n"
            "  pip install segment-anything  (SAM 1)\n"
            "  pip install mobile-sam  (MobileSAM)"
        )

    def unload(self):
        """从 GPU 卸载"""
        del self.model
        del self.predictor
        self.model = None
        self.predictor = None
        self._image_set = False
        import torch
        torch.cuda.empty_cache()
        print(f"[SAM] Unloaded")

    def set_image(self, image: np.ndarray):
        """设置当前图像（编码一次，多次分割）"""
        if self.predictor is None:
            raise RuntimeError("SAM 模型未加载，请先调用 load()")
        self.predictor.set_image(image)
        self._image_set = True

    def segment_with_box(self, bbox: List[float]) -> np.ndarray:
        """
        用 bbox 作为 prompt 进行分割。

        Args:
            bbox: [x1, y1, x2, y2] 像素坐标

        Returns:
            bool numpy array (H, W)，True = 分割区域
        """
        if not self._image_set:
            raise RuntimeError("请先调用 set_image()")
        masks, scores, _ = self.predictor.predict(
            box=np.array(bbox),
            multimask_output=True,
        )
        best_idx = np.argmax(scores)
        return masks[best_idx].astype(bool)

    def segment_with_point(self, x: int, y: int) -> np.ndarray:
        """
        用点击坐标作为 prompt 进行交互式分割。

        Args:
            x, y: 图像上的点击坐标

        Returns:
            bool numpy array (H, W)
        """
        if not self._image_set:
            raise RuntimeError("请先调用 set_image()")
        masks, scores, _ = self.predictor.predict(
            point_coords=np.array([[x, y]]),
            point_labels=np.array([1]),  # 1 = 前景点
            multimask_output=True,
        )
        best_idx = np.argmax(scores)
        return masks[best_idx].astype(bool)

    # ═══════ 内部构建方法 ═══════

    def _build_sam2(self, variant: dict):
        """构建 SAM 2.1"""
        from sam2.build_sam import build_sam2
        from sam2.sam2_image_predictor import SAM2ImagePredictor

        self.model = build_sam2(
            variant["config_file"],
            variant["model_file"],
            device="cuda",
        )
        self.predictor = SAM2ImagePredictor(self.model)

    def _build_sam1(self, variant: dict):
        """构建 SAM 1"""
        from segment_anything import sam_model_registry, SamPredictor

        self.model = sam_model_registry[variant["model_type"]](
            checkpoint=variant["model_file"]
        )
        self.model.to("cuda")
        self.predictor = SamPredictor(self.model)

    def _build_mobile_sam(self, variant: dict):
        """构建 MobileSAM"""
        from mobile_sam import sam_model_registry, SamPredictor

        self.model = sam_model_registry["vit_t"](
            checkpoint=variant["model_file"]
        )
        self.model.to("cuda")
        self.predictor = SamPredictor(self.model)
