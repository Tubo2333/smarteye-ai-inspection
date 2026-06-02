"""
POST /api/inspect — 视觉质检接口
GET  /api/inspect/history — 检测历史记录
"""
import time
import uuid
from collections import deque
from fastapi import APIRouter, HTTPException
from backend.api.schemas import InspectRequest, InspectResponse, DefectItem
from backend.api.deps import get_graph
from backend.orchestrator.state import create_initial_state

router = APIRouter()

# 内存中保存最近 100 条检测记录
_history: deque = deque(maxlen=100)


@router.post("/inspect", response_model=InspectResponse)
async def inspect(req: InspectRequest):
    """
    上传 PCB 图像，执行 AI 驱动的视觉缺陷检测。
    """
    task_id = str(uuid.uuid4())[:8]
    t_start = time.time()

    initial_state = create_initial_state(
        task_id=task_id,
        task_type="inspection",
        image_b64=req.image,
        sam_point=req.sam_point,
    )

    try:
        graph = get_graph()
        config = {"configurable": {"thread_id": task_id}, "recursion_limit": 50}
        final_state = await graph.ainvoke(initial_state, config)

        error = final_state.get("error")
        if error:
            return InspectResponse(
                task_id=task_id, status="error", defects=[],
                summary={"error": str(error)},
                annotated_image_b64="", processing_time_ms=(time.time() - t_start) * 1000,
            )

        defects = []
        for det in final_state.get("detections", []) or []:
            defects.append(DefectItem(**det))

        summary = final_state.get("detection_summary", {})
        proc_ms = final_state.get("processing_time_ms", (time.time() - t_start) * 1000)

        resp = InspectResponse(
            task_id=task_id, status="completed", defects=defects,
            summary=summary, annotated_image_b64=final_state.get("annotated_image_b64", ""),
            processing_time_ms=proc_ms,
        )

        # 存入历史
        _history.appendleft({
            "task_id": task_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "defect_count": summary.get("total", 0),
            "confirmed": summary.get("confirmed", 0),
            "critical": summary.get("critical", 0),
            "severity": summary.get("overall_severity", "INFO"),
            "processing_time_ms": proc_ms,
            "defect_types": summary.get("by_type", {}),
        })

        return resp

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")


@router.get("/inspect/history")
async def get_history(limit: int = 20):
    """返回最近 N 条检测历史记录"""
    items = list(_history)[:limit]
    return {
        "total_stored": len(_history),
        "items": items,
    }
