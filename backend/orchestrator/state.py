"""
SmartEyeState — LangGraph 全局状态定义

所有 Agent 通过读写这个状态对象来通信。
使用 TypedDict 定义字段，LangGraph 的 add_messages reducer 处理消息追加。
"""
from typing import TypedDict, List, Optional, Annotated, Any, Dict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class SmartEyeState(TypedDict, total=False):
    """
    全局状态对象。

    字段说明:
    - task_id: 任务唯一标识
    - task_type: inspection | analysis | report | chat
    - image_b64: Base64 编码的输入图像
    - user_message: 用户输入的消息文本
    - sam_point: 用户点击坐标 {"x": int, "y": int}
    - detections: 检测结果列表
    - detection_summary: 检测汇总
    - annotated_image_b64: 标注后的图像
    - analysis_results: 分析结果
    - report_markdown: Markdown 报告
    - report_id: 报告 ID
    - alert_triggered: 是否触发告警
    - alert_level: INFO | WARN | CRITICAL
    - alert_message: 告警消息文本
    - rag_documents: RAG 检索结果
    - messages: 对话消息历史 (add_messages reducer 自动追加)
    - next_agent: Supervisor 的路由决策
    - error: 当前错误信息
    - error_history: 错误历史记录
    - retry_count: 当前步骤重试次数
    - status: pending | running | completed | error
    - processing_time_ms: 总处理时间
    """

    # ── 任务标识 ──
    task_id: str
    task_type: str  # inspection | analysis | report | chat

    # ── 输入 ──
    image_b64: Optional[str]
    user_message: Optional[str]
    sam_point: Optional[Dict[str, int]]

    # ── CV 检测结果 ──
    detections: Optional[List[Dict[str, Any]]]
    detection_summary: Optional[Dict[str, Any]]
    annotated_image_b64: Optional[str]

    # ── 分析结果 ──
    analysis_results: Optional[Dict[str, Any]]

    # ── 报告 ──
    report_markdown: Optional[str]
    report_id: Optional[str]

    # ── 告警 ──
    alert_triggered: bool
    alert_level: Optional[str]
    alert_message: Optional[str]

    # ── RAG ──
    rag_documents: Optional[List[Dict[str, Any]]]

    # ── 消息与路由 ──
    messages: Annotated[List[BaseMessage], add_messages]
    next_agent: str

    # ── 错误处理 ──
    error: Optional[str]
    error_history: List[Dict[str, Any]]
    retry_count: int
    status: str

    # ── 元信息 ──
    processing_time_ms: float


def create_initial_state(
    task_id: str,
    task_type: str = "inspection",
    image_b64: Optional[str] = None,
    user_message: Optional[str] = None,
    sam_point: Optional[Dict[str, int]] = None,
) -> SmartEyeState:
    """创建初始状态对象"""
    return SmartEyeState(
        task_id=task_id,
        task_type=task_type,
        image_b64=image_b64,
        user_message=user_message,
        sam_point=sam_point,
        detections=None,
        detection_summary=None,
        annotated_image_b64=None,
        analysis_results=None,
        report_markdown=None,
        report_id=None,
        alert_triggered=False,
        alert_level=None,
        alert_message=None,
        rag_documents=None,
        messages=[],
        next_agent="supervisor",
        error=None,
        error_history=[],
        retry_count=0,
        status="pending",
        processing_time_ms=0.0,
    )
