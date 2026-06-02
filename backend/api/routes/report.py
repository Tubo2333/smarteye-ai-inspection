"""
POST /api/report/generate — 生成质检报告
GET  /api/report/{report_id} — 获取报告内容
GET  /api/report/history — 报告历史列表
"""
import time
from collections import deque
from fastapi import APIRouter, HTTPException
from backend.api.schemas import ReportGenerateRequest, ReportResponse

router = APIRouter()

# 内存存储
_reports: dict = {}
_history: deque = deque(maxlen=50)


@router.post("/report/generate", response_model=ReportResponse)
async def generate_report(req: ReportGenerateRequest):
    """生成并存储质检报告"""
    report_id = req.task_id if req.task_id else f"R{int(time.time()) % 100000:05d}"
    created_at = time.strftime("%Y-%m-%d %H:%M:%S")

    existing = _reports.get(req.task_id, {})
    content = existing.get("content", f"# 质检报告\n\n报告 ID: {report_id}\n生成时间: {created_at}")

    entry = {
        "content": content,
        "format": req.format,
        "created_at": created_at,
    }
    _reports[report_id] = entry

    # 存入历史列表
    _history.appendleft({
        "report_id": report_id,
        "created_at": created_at,
    })

    return ReportResponse(
        report_id=report_id,
        content=content if req.format == "md" else None,
        format=req.format,
        created_at=created_at,
    )


@router.get("/report/{report_id}", response_model=ReportResponse)
async def get_report(report_id: str):
    """获取指定报告"""
    report = _reports.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"报告 {report_id} 不存在")
    return ReportResponse(
        report_id=report_id,
        content=report["content"],
        format=report.get("format", "md"),
        created_at=report["created_at"],
    )


@router.get("/report/history")
async def get_report_history(limit: int = 20):
    """返回最近 N 条报告历史"""
    items = list(_history)[:limit]
    return {
        "total_stored": len(_history),
        "items": items,
    }


def save_report_content(task_id: str, content: str):
    """供其他模块调用：存储报告内容"""
    entry = {
        "content": content,
        "format": "md",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    _reports[task_id] = entry
    _history.appendleft({
        "report_id": task_id,
        "created_at": entry["created_at"],
    })
