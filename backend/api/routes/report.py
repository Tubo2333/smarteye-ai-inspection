"""
POST /api/report/generate — 生成质检报告
GET  /api/report/{report_id} — 获取报告内容
"""
import time
from fastapi import APIRouter, HTTPException
from backend.api.schemas import ReportGenerateRequest, ReportResponse

router = APIRouter()

# 简易内存存储
_reports: dict = {}


@router.post("/report/generate", response_model=ReportResponse)
async def generate_report(req: ReportGenerateRequest):
    """生成并导出质检报告"""
    report_id = req.task_id or f"R{int(time.time()) % 100000:05d}"
    created_at = time.strftime("%Y-%m-%d %H:%M:%S")

    # 查找已有报告
    existing = _reports.get(req.task_id, {})

    content = existing.get("content", f"# 质检报告\n\n报告 ID: {report_id}\n生成时间: {created_at}\n\n暂无检测数据。")

    _reports[report_id] = {
        "content": content,
        "format": req.format,
        "created_at": created_at,
    }

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


def save_report_content(task_id: str, content: str):
    """供其他模块调用的报告存储函数"""
    _reports[task_id] = {
        "content": content,
        "format": "md",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
