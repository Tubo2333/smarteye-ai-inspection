"""
POST /api/inspect — 视觉质检接口
"""
import time
import uuid
from fastapi import APIRouter, HTTPException
from backend.api.schemas import InspectRequest, InspectResponse, DefectItem
from backend.api.deps import get_graph
from backend.orchestrator.state import create_initial_state

router = APIRouter()


@router.post("/inspect", response_model=InspectResponse)
async def inspect(req: InspectRequest):
    """
    上传 PCB 图像，执行 AI 驱动的视觉缺陷检测。

    流程: Supervisor → InspectionAgent (YOLO+OpenCV+SAM) → ReportAgent → 返回结果
    """
    task_id = str(uuid.uuid4())[:8]
    t_start = time.time()

    # 构建初始 State
    initial_state = create_initial_state(
        task_id=task_id,
        task_type="inspection",
        image_b64=req.image,
        sam_point=req.sam_point,
    )

    try:
        graph = get_graph()
        config = {"configurable": {"thread_id": task_id}}

        # 运行 LangGraph — 阻塞直到 END
        final_state = await graph.ainvoke(initial_state, config)

        error = final_state.get("error")
        if error:
            return InspectResponse(
                task_id=task_id,
                status="error",
                defects=[],
                summary={"error": str(error)},
                annotated_image_b64="",
                processing_time_ms=(time.time() - t_start) * 1000,
            )

        # 构建响应
        defects = []
        for det in final_state.get("detections", []) or []:
            defects.append(DefectItem(**det))

        return InspectResponse(
            task_id=task_id,
            status="completed",
            defects=defects,
            summary=final_state.get("detection_summary", {}),
            annotated_image_b64=final_state.get("annotated_image_b64", ""),
            processing_time_ms=final_state.get("processing_time_ms", (time.time() - t_start) * 1000),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")
