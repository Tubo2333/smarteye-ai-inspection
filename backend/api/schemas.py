"""
Pydantic 数据模型 — 所有 API 的请求/响应 schema
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# ═══════════════════════════════════════════════════════════════
# Inspection
# ═══════════════════════════════════════════════════════════════

class InspectRequest(BaseModel):
    image: str = Field(..., description="Base64 编码的 PCB 图像")
    conf_threshold: float = Field(default=0.25, ge=0.0, le=1.0, description="YOLO 置信度阈值")
    enable_sam: bool = Field(default=True, description="是否启用 SAM 精细分割")
    sam_point: Optional[Dict[str, int]] = Field(default=None, description="SAM 交互模式点击坐标 {x, y}")

class DefectItem(BaseModel):
    bbox: List[float]
    class_name: str
    confidence: float
    verdict: str
    severity: str
    measurements: Dict[str, Any] = {}
    has_mask: bool = False

class InspectResponse(BaseModel):
    task_id: str
    status: str
    defects: List[DefectItem]
    summary: Dict[str, Any]
    annotated_image_b64: str
    processing_time_ms: float


# ═══════════════════════════════════════════════════════════════
# Agent Chat
# ═══════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    message: str = Field(..., description="用户消息")
    image_b64: Optional[str] = Field(default=None, description="可选的附带图片")
    session_id: str = Field(..., description="会话 ID")
    task_type: str = Field(default="chat", description="任务类型")

class TraceEntry(BaseModel):
    agent: str
    action: str
    tool_calls: List[str] = []
    timestamp: str

class ChatResponse(BaseModel):
    reply: str
    agent_trace: List[TraceEntry] = []
    artifacts: List[Dict[str, str]] = []
    report_id: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# Report
# ═══════════════════════════════════════════════════════════════

class ReportGenerateRequest(BaseModel):
    task_id: str
    format: str = Field(default="md", description="md | pdf | docx")

class ReportResponse(BaseModel):
    report_id: str
    content: Optional[str] = None
    format: str = "md"
    created_at: str = ""


# ═══════════════════════════════════════════════════════════════
# Knowledge
# ═══════════════════════════════════════════════════════════════

class KnowledgeSearchResult(BaseModel):
    content: str
    metadata: Dict[str, Any]
    relevance_score: float

class KnowledgeSearchResponse(BaseModel):
    results: List[KnowledgeSearchResult]
    search_time_ms: float
    total_chunks: int


class KnowledgeStatsResponse(BaseModel):
    total_chunks: int
    collection_name: str
