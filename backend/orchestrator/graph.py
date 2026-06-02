"""
LangGraph 编排引擎 — SmartEye 的心脏

构建 SupervisorAgent 模式的 StateGraph:
    START → supervisor ⇄ {inspection, analysis, report, alert} → END

每个 Worker Agent 执行完后回到 Supervisor，由 Supervisor 决定下一步。
"""
import time
from pathlib import Path
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage

from backend.orchestrator.state import SmartEyeState, create_initial_state
from backend.config import LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS, PROMPTS_DIR

# ═══════════════════════════════════════════════════════════════
# Graph 构建
# ═══════════════════════════════════════════════════════════════

def build_graph() -> StateGraph:
    """构建并编译 SmartEye 的 LangGraph 应用"""
    workflow = StateGraph(SmartEyeState)

    # 添加节点
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("inspection", inspection_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("report", report_node)
    workflow.add_node("alert", alert_node)

    # 入口 → Supervisor
    workflow.set_entry_point("supervisor")

    # Supervisor 条件路由
    workflow.add_conditional_edges(
        "supervisor",
        _route_decision,
        {
            "inspection": "inspection",
            "analysis": "analysis",
            "report": "report",
            "alert": "alert",
            "END": END,
        }
    )

    # 所有 Worker 回到 Supervisor
    for agent in ["inspection", "analysis", "report", "alert"]:
        workflow.add_edge(agent, "supervisor")

    # 编译（内存 checkpoint 支持对话历史）
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


def _route_decision(state: SmartEyeState) -> Literal["inspection", "analysis", "report", "alert", "END"]:
    """从状态中提取 Supervisor 的路由决策"""
    return state.get("next_agent", "END")


# ═══════════════════════════════════════════════════════════════
# Node 实现 (Agent 的入口函数)
# ═══════════════════════════════════════════════════════════════

def supervisor_node(state: SmartEyeState) -> dict:
    """
    SupervisorAgent: 根据 state 做路由决策。

    LLM 驱动的动态路由——不是硬编码 if-else。
    分析 task_type 和当前 state，输出 next_agent。
    """
    import os
    from langchain_anthropic import ChatAnthropic

    # 加载 prompt
    prompt_path = Path(PROMPTS_DIR) / "supervisor.md"
    if prompt_path.exists():
        system_prompt = prompt_path.read_text(encoding="utf-8")
    else:
        system_prompt = _get_fallback_supervisor_prompt()

    # 构建决策上下文
    context = f"""当前任务类型: {state.get('task_type', 'inspection')}
当前状态: {state.get('status', 'pending')}
是否有图像: {state.get('image_b64') is not None}
是否有检测结果: {state.get('detections') is not None}
检测汇总: {state.get('detection_summary', {})}
是否有分析结果: {state.get('analysis_results') is not None}
是否有报告: {state.get('report_markdown') is not None}
是否已告警: {state.get('alert_triggered', False)}
告警级别: {state.get('alert_level', '无')}
最近错误: {state.get('error', '无')}
重试次数: {state.get('retry_count', 0)}
用户消息: {state.get('user_message', '无')}
"""

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        # 无 API Key → 使用简单规则路由（fallback）
        return _rule_based_routing(state)

    try:
        llm = ChatAnthropic(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            api_key=api_key,
        )

        response = llm.invoke([
            ("system", system_prompt),
            ("human", f"根据以下状态信息，决定下一步调用哪个 Agent：\n\n{context}\n\n请输出一行决策。"),
        ])

        next_agent = _parse_next_agent(response.content)
        print(f"[Supervisor] → {next_agent}")

        update: dict = {
            "next_agent": next_agent,
            "status": "completed" if next_agent == "END" else "running",
        }

        if next_agent == "END":
            update["status"] = "completed"

        return update

    except Exception as e:
        print(f"[Supervisor] LLM call failed, using rule-based fallback: {e}")
        return _rule_based_routing(state)


def inspection_node(state: SmartEyeState) -> dict:
    """
    InspectionAgent: 调用 CV 三引擎执行视觉检测。

    直接操作 fusion_inspect，不通过 LLM——因为视觉检测是确定性的，
    不需要 LLM 来做决策，只需要把结果写入 state。
    """
    import base64
    import numpy as np
    import cv2

    image_b64 = state.get("image_b64")
    if not image_b64:
        return {"error": "No image provided for inspection", "retry_count": state.get("retry_count", 0) + 1}

    try:
        # base64 → numpy
        img_bytes = base64.b64decode(image_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return {"error": "Failed to decode image", "retry_count": state.get("retry_count", 0) + 1}

        # 执行三引擎检测
        from backend.cv.fusion import fusion_inspect

        sam_point = state.get("sam_point")
        result = fusion_inspect(
            image,
            sam_interactive=sam_point is not None,
            sam_point=(sam_point["x"], sam_point["y"]) if sam_point else None,
            enable_sam=True,
        )

        # 转换 Detection 对象为 dict（确保所有数值为原生 Python 类型）
        def to_native(val):
            """递归转换 numpy 类型为原生 Python 类型"""
            import numpy as np
            if isinstance(val, (np.integer,)):
                return int(val)
            if isinstance(val, (np.floating,)):
                return float(val)
            if isinstance(val, np.ndarray):
                return val.tolist()
            if isinstance(val, dict):
                return {k: to_native(v) for k, v in val.items()}
            if isinstance(val, (list, tuple)):
                return [to_native(v) for v in val]
            return val

        detections_list = []
        for det in result.defects:
            det_dict = {
                "bbox": [float(v) for v in det.bbox],
                "class_name": str(det.class_name),
                "confidence": float(det.confidence),
                "verdict": str(det.verdict),
                "severity": str(det.severity),
            }
            measurements_serializable = {}
            for k, v in det.measurements.items():
                if hasattr(v, '__dataclass_fields__'):
                    measurements_serializable[k] = {
                        "value": float(v.value),
                        "unit": str(v.unit),
                        "threshold": float(v.threshold),
                        "passed": bool(v.passed),
                        "detail": str(v.detail),
                    }
                else:
                    measurements_serializable[k] = to_native(v)
            det_dict["measurements"] = measurements_serializable
            det_dict["has_mask"] = det.mask is not None
            detections_list.append(det_dict)

        return {
            "detections": detections_list,
            "detection_summary": to_native(result.summary),
            "annotated_image_b64": result.annotated_image_b64,
            "processing_time_ms": float(result.processing_time_ms),
            "retry_count": state.get("retry_count", 0) + 1,
            "error": None,
        }

    except Exception as e:
        print(f"[InspectionAgent] Error: {e}")
        return {
            "error": f"Inspection failed: {str(e)}",
            "retry_count": state.get("retry_count", 0) + 1,
        }


def analysis_node(state: SmartEyeState) -> dict:
    """
    AnalysisAgent: 对检测结果做统计分析。

    使用 LLM 分析检测数据，判断是否存在系统性异常。
    """
    import os
    from langchain_anthropic import ChatAnthropic

    detections = state.get("detections")
    if not detections:
        return {"analysis_results": {"conclusion": "无检测数据可分析", "is_systemic": False}}

    # 加载 prompt
    prompt_path = Path(PROMPTS_DIR) / "analysis.md"
    system_prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else "你是一个SPC质量分析师。"

    # 构建分析数据
    detection_text = _format_detections_for_analysis(detections)
    summary = state.get("detection_summary", {})

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return {"analysis_results": _basic_analysis(detections, summary)}

    try:
        llm = ChatAnthropic(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            max_tokens=2048,
            api_key=api_key,
        )

        response = llm.invoke([
            ("system", system_prompt),
            ("human", f"分析以下检测数据：\n\n汇总: {summary}\n\n明细: {detection_text}"),
        ])

        return {
            "analysis_results": {
                "raw_analysis": response.content,
                "detections_count": len(detections),
            }
        }
    except Exception as e:
        print(f"[AnalysisAgent] LLM failed, using basic analysis: {e}")
        return {"analysis_results": _basic_analysis(detections, summary)}


def report_node(state: SmartEyeState) -> dict:
    """
    ReportAgent: 生成质检报告 / 回答用户问题。

    如果是 chat 任务：搜索 RAG 知识库，生成对话式回复。
    如果是 inspection 任务：生成质检报告。
    """
    import os
    from langchain_anthropic import ChatAnthropic

    task_type = state.get("task_type", "inspection")
    detections = state.get("detections", [])
    summary = state.get("detection_summary", {})
    analysis = state.get("analysis_results", {})
    user_message = state.get("user_message", "")

    # ── Chat 模式：知识库问答 ──
    if task_type == "chat" and user_message:
        # 安全获取 RAG 上下文（绝不崩溃）
        rag_context = ""
        try:
            from backend.rag.vector_store import get_collection
            collection = get_collection()
            chunk_count = collection.count()
            print(f"[ReportAgent] Chat mode: KB has {chunk_count} chunks")
            if chunk_count > 0:
                results = collection.query(query_texts=[user_message], n_results=3)
                docs = results.get("documents", [[]])[0]
                metas = results.get("metadatas", [[]])[0]
                if docs:
                    rag_context = "\n\n".join([
                        f"[来源: {m.get('source', '?') if m else '?'}]\n{d}"
                        for d, m in zip(docs, metas)
                    ])
                    print(f"[ReportAgent] RAG found {len(docs)} results")
                else:
                    print("[ReportAgent] RAG query returned empty docs")
        except Exception as e:
            print(f"[ReportAgent] RAG search error (non-fatal): {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

        # 尝试用 LLM 生成回复
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if api_key and rag_context:
            try:
                llm = ChatAnthropic(model=LLM_MODEL, temperature=LLM_TEMPERATURE, max_tokens=1024, api_key=api_key)
                response = llm.invoke([
                    ("system", "你是工厂质检助手。根据知识库内容回答用户问题。如果知识库没有相关信息，诚实告知。用中文回答。"),
                    ("human", f"知识库参考:\n{rag_context}\n\n用户问题: {user_message}"),
                ])
                print(f"[ReportAgent] Chat reply: {response.content[:100]}...")
                return {"report_markdown": response.content, "report_id": f"chat_{int(time.time())}", "error": None}
            except Exception as e:
                print(f"[ReportAgent] LLM failed: {e}")

        # Fallback: 用知识库原文回复
        if rag_context:
            reply = f"**根据知识库检索结果：**\n\n{rag_context}"
        else:
            reply = f"关于「{user_message}」，知识库中暂未找到相关信息。请尝试其他关键词，或上传 PCB 图片进行视觉检测。"
        return {"report_markdown": reply, "report_id": f"chat_{int(time.time())}", "error": None}

    # ── Inspection 模式：生成质检报告 ──

    # 构建报告上下文
    context = f"""## 检测汇总
{summary}

## 缺陷明细
{_format_detections_for_analysis(detections) if detections else '无缺陷'}

## 分析结论
{analysis.get('raw_analysis', analysis.get('conclusion', '无')) if analysis else '未执行分析'}

请据此生成完整的质检报告（Markdown 格式）。"""

    report_md = f"""# 质检报告

**检测时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**检测数量**: {summary.get('total', 0)} 个缺陷候选
**判定结果**: {"🔴 FAIL" if summary.get('critical', 0) > 0 else "⚠️ WARN" if summary.get('confirmed', 0) > 0 else "✅ PASS"}

## 缺陷汇总
- 确认缺陷: {summary.get('confirmed', 0)}
- 疑似缺陷: {summary.get('suspicious', 0)}
- 可能误报: {summary.get('likely_fp', 0)}

## 处置建议
"""

    if summary.get('critical', 0) > 0:
        report_md += "- ⚠️ 检测到严重缺陷，建议立即复查相关工位\n"
    if summary.get('confirmed', 0) > 0:
        report_md += "- 确认缺陷已记录，请质量工程师审核\n"
    if summary.get('suspicious', 0) > 0:
        report_md += "- 疑似缺陷建议人工复检确认\n"

    if not detections:
        report_md += "- ✅ 未检测到缺陷，批次放行\n"

    report_id = f"R{int(time.time()) % 100000:05d}"

    print(f"[ReportAgent] Report {report_id} generated")

    return {
        "report_markdown": report_md,
        "report_id": report_id,
        "error": None,
    }


def alert_node(state: SmartEyeState) -> dict:
    """
    AlertAgent: 评估是否需要告警，生成告警消息。
    """
    detections = state.get("detections", [])
    summary = state.get("detection_summary", {})

    critical_count = summary.get("critical", 0)
    overall = summary.get("overall_severity", "INFO")

    alert_triggered = critical_count > 0 or overall in ("CRITICAL", "WARN")
    alert_level = overall if alert_triggered else "INFO"

    alert_message = ""
    if alert_triggered:
        alert_message = f"检测到 {critical_count} 个严重缺陷，整体严重度: {overall}。建议立即处理。"

    print(f"[AlertAgent] Triggered={alert_triggered}, Level={alert_level}")

    return {
        "alert_triggered": alert_triggered,
        "alert_level": alert_level,
        "alert_message": alert_message,
        "error": None,
    }


# ═══════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════

def _parse_next_agent(response: str) -> str:
    """从 LLM 响应中解析 next_agent"""
    text = response.strip()
    for line in text.split("\n"):
        line_upper = line.upper()
        if line_upper.startswith("NEXT:"):
            agent = line.split(":", 1)[1].strip().lower()
            if agent in ("inspection", "analysis", "report", "alert", "end"):
                return "END" if agent == "end" else agent
    # Fallback: 扫描整个文本
    for agent in ["inspection", "analysis", "report", "alert", "END"]:
        if agent.lower() in text.lower():
            return agent
    return "END"


def _rule_based_routing(state: SmartEyeState) -> dict:
    """无 API Key 时的规则路由（fallback）"""
    task_type = state.get("task_type", "inspection")
    has_image = state.get("image_b64") is not None
    has_message = bool(state.get("user_message"))
    detections = state.get("detections")
    has_detections = detections is not None and len(detections) > 0
    has_report = state.get("report_markdown") is not None
    alerted = state.get("alert_triggered", False)
    retry = state.get("retry_count", 0)

    # 同一 agent 重试超过 3 次 → 强制结束
    if retry >= 3:
        if not has_report:
            return {"next_agent": "report", "status": "running"}
        return {"next_agent": "END", "status": "completed"}

    # ── Chat 模式：纯文字问答 → report agent (RAG 检索 + 回复) ──
    if task_type == "chat" and has_message and not has_report:
        return {"next_agent": "report", "status": "running"}
    if task_type == "chat" and has_report:
        return {"next_agent": "END", "status": "completed"}

    # ── Inspection 模式 ──
    # 有图像且还没检测过 → inspection
    if has_image and detections is None:
        return {"next_agent": "inspection", "status": "running"}

    # 已检测完，有严重缺陷且未告警 → 先告警
    if detections is not None and not alerted:
        summary = state.get("detection_summary", {})
        if summary.get("critical", 0) > 0:
            return {"next_agent": "alert", "status": "running"}

    # 已检测完（无论有没有缺陷）且没报告 → report
    if detections is not None and not has_report:
        return {"next_agent": "report", "status": "running"}

    # 有报告未告警 → alert (最终检查)
    if has_report and not alerted:
        summary = state.get("detection_summary", {})
        if summary.get("critical", 0) > 0:
            return {"next_agent": "alert", "status": "running"}

    # 全部完成
    return {"next_agent": "END", "status": "completed"}


def _format_detections_for_analysis(detections: list) -> str:
    """将检测结果格式化为分析用的文本"""
    lines = []
    for i, det in enumerate(detections, 1):
        lines.append(
            f"{i}. {det.get('class_name', 'unknown')} — "
            f"置信度: {det.get('confidence', 0):.2f}, "
            f"判定: {det.get('verdict', '?')}, "
            f"严重度: {det.get('severity', '?')}"
        )
    return "\n".join(lines) if lines else "无检测结果"


def _basic_analysis(detections: list, summary: dict) -> dict:
    """基本统计分析（不需要 LLM）"""
    total = summary.get("total", len(detections))
    confirmed = summary.get("confirmed", 0)
    critical = summary.get("critical", 0)

    is_systemic = critical > 0 and confirmed > 3

    return {
        "defect_rate": round(confirmed / max(total, 1), 3),
        "total": total,
        "confirmed": confirmed,
        "critical": critical,
        "is_systemic": is_systemic,
        "conclusion": (
            f"检测到 {confirmed} 个确认缺陷，其中 {critical} 个为严重级别。"
            f"{'疑似系统性异常，建议调查。' if is_systemic else '暂无明显系统性异常。'}"
        ),
    }


def _get_fallback_supervisor_prompt() -> str:
    """Supervisor 的 fallback prompt（当 MD 文件不可用时）"""
    return """你是 AI 质检总调度。根据状态决定下一步:

可用 Agent: inspection, analysis, report, alert

规则:
- 有图无结果 → inspection
- 有结果无报告 → report
- 有严重缺陷未告警 → alert
- 需要分析 → analysis
- 完成 → END

只输出: NEXT: <agent>"""
