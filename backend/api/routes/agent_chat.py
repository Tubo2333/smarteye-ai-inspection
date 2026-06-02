"""
POST /api/agent/chat — Agent 对话接口
GET  /api/agent/chat/{session_id}/history — 对话历史
"""
import time
from fastapi import APIRouter, HTTPException
from backend.api.schemas import ChatRequest, ChatResponse, TraceEntry
from backend.api.deps import get_graph
from backend.orchestrator.state import create_initial_state
from backend.orchestrator.graph import supervisor_node

router = APIRouter()

# 简易内存存储（生产环境应用 Redis）
_chat_histories: dict = {}


@router.post("/agent/chat", response_model=ChatResponse)
async def agent_chat(req: ChatRequest):
    """
    与 AI Agent 对话。支持:
    - 纯文本问答（查标准、问处置方案）
    - 附带图片触发视觉检测
    - 多轮对话（通过 session_id 关联）
    """
    task_id = f"chat_{int(time.time())}"

    initial_state = create_initial_state(
        task_id=task_id,
        task_type=req.task_type,
        image_b64=req.image_b64,
        user_message=req.message,
    )

    try:
        graph = get_graph()
        config = {"configurable": {"thread_id": req.session_id}, "recursion_limit": 50}

        final_state = await graph.ainvoke(initial_state, config)

        # 构建 trace
        trace = [
            TraceEntry(
                agent="SupervisorAgent",
                action=f"路由到 {final_state.get('next_agent', 'END')}",
                timestamp=time.strftime("%H:%M:%S"),
            )
        ]

        # 构建回复
        reply_parts = []

        detections = final_state.get("detections")
        if detections:
            summary = final_state.get("detection_summary", {})
            reply_parts.append(
                f"检测完成：发现 {summary.get('total', 0)} 个缺陷候选，"
                f"其中确认 {summary.get('confirmed', 0)} 个，"
                f"严重缺陷 {summary.get('critical', 0)} 个。"
            )

        analysis = final_state.get("analysis_results")
        if analysis and analysis.get("conclusion"):
            reply_parts.append(f"\n分析结论：{analysis['conclusion']}")

        alert_msg = final_state.get("alert_message")
        if alert_msg:
            reply_parts.append(f"\n⚠️ {alert_msg}")

        report = final_state.get("report_markdown")
        if report:
            reply_parts.append(report)

        if not reply_parts:
            reply_parts.append("任务已完成。")

        reply = "\n".join(reply_parts)

        # 保存历史
        if req.session_id not in _chat_histories:
            _chat_histories[req.session_id] = []
        _chat_histories[req.session_id].append({"role": "user", "content": req.message})
        _chat_histories[req.session_id].append({"role": "assistant", "content": reply})

        return ChatResponse(
            reply=reply,
            agent_trace=trace,
            report_id=final_state.get("report_id"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent 对话失败: {str(e)}")


@router.get("/agent/chat/{session_id}/history")
async def get_chat_history(session_id: str):
    """获取指定会话的对话历史"""
    return {
        "session_id": session_id,
        "messages": _chat_histories.get(session_id, []),
    }
