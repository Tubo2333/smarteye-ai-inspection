"""
SmartEye 全局配置
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# ── 路径 ──
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
MODELS_DIR = ROOT_DIR / "backend" / "models"
PROMPTS_DIR = ROOT_DIR / "backend" / "prompts"

# ── API Keys ──
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")

# ── LLM 配置 ──
LLM_MODEL = "claude-sonnet-4-6"          # 默认: Sonnet (速度快, 适合路由)
LLM_MODEL_COMPLEX = "claude-opus-4-8"    # 复杂任务回退: Opus
LLM_TEMPERATURE = 0.3                     # 质检场景需要稳定性
LLM_MAX_TOKENS = 4096

# ── YOLO 配置 ──
YOLO_MODEL_PATH = str(MODELS_DIR / "yolov8_pcb.pt")
YOLO_ONNX_PATH = str(MODELS_DIR / "yolov8_pcb.onnx")
YOLO_CONF_THRESHOLD = 0.25
YOLO_IOU_THRESHOLD = 0.45
YOLO_IMG_SIZE = 640

# ── SAM 配置 ──
SAM_VARIANT = "sam2_hiera_small"          # sam2_hiera_small | vit_h | vit_t (MobileSAM)
SAM_FALLBACK_CHAIN = [
    "sam2_hiera_small",
    "vit_h",
    "vit_t",
]

# ── OpenCV 规则阈值 ──
SOLDER_AREA_MIN_RATIO = 0.7               # 焊点面积最小比例 (相对于标准值)
SOLDER_CIRCULARITY_MIN = 0.6              # 焊点圆度最小值
COMPONENT_OFFSET_MAX_RATIO = 0.15         # 元件偏移最大比例 (相对元件尺寸)
SCRATCH_MAX_LENGTH_MM = 2.0               # 划痕最大长度 (mm)
COLOR_DELTA_E_THRESHOLD = 15.0            # 色差阈值

# ── RAG 配置 ──
CHROMA_PERSIST_DIR = str(DATA_DIR / "chromadb")
CHROMA_COLLECTION_NAME = "smarteye_knowledge"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64
RAG_TOP_K_RETRIEVAL = 8
RAG_TOP_K_FINAL = 4

# ── 告警规则 ──
ALERT_RULES = {
    "critical_immediate": True,            # CRITICAL 缺陷立即告警
    "consecutive_batches": 3,              # 连续 N 批同类型缺陷触发 WARN
    "same_station_threshold": 5,           # 同工位 1 小时内 N 个缺陷触发 INFO
    "defect_rate_sigma": 3.0,              # 缺陷率超过均值 + N*σ 触发 CRITICAL
}

# ── API 配置 ──
API_HOST = "127.0.0.1"
API_PORT = 8000
CORS_ORIGINS = ["http://localhost:8501"]   # Streamlit 默认端口

# ── Streamlit 配置 ──
STREAMLIT_PORT = 8501
STREAMLIT_API_URL = f"http://{API_HOST}:{API_PORT}"
