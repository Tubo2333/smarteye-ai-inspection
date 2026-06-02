"""质量检测页 — 检测 → 联动 Agent对话 / 仪表盘 / 报告"""
import base64
import os
import time
import io
import streamlit as st
import requests
from PIL import Image
from pathlib import Path
from frontend.session import add_inspect_session, get_inspect_sessions, delete_inspect_session, is_history_full, MAX_SESSIONS


LABEL_MAP = {
    "pcb_golden.jpg": "✅ 正常板",
    "pcb_defect_bridge.jpg": "桥接缺陷",
    "pcb_defect_missing_component.jpg": "缺件缺陷",
    "pcb_defect_offset.jpg": "元件偏移",
    "pcb_defect_insufficient_solder.jpg": "少锡缺陷",
    "pcb_defect_scratch.jpg": "划伤缺陷",
    "pcb_defect_mixed.jpg": "混合缺陷",
    "pcb_defect_mixed_1.jpg": "混合缺陷 1",
    "pcb_defect_mixed_2.jpg": "混合缺陷 2",
    "pcb_defect_mixed_3.jpg": "混合缺陷 3",
}

MAX_IMG_HEIGHT = 380


def resize_for_display(image_bytes: bytes, max_height: int = MAX_IMG_HEIGHT) -> bytes:
    img = Image.open(io.BytesIO(image_bytes))
    w, h = img.size
    if h > max_height:
        ratio = max_height / h
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def render(api_url: str):
    st.markdown("### 📸 质量检测")

    # session state 初始化
    for key, default in [
        ("selected_sample_name", None),
        ("uploaded_image_bytes", None),
        ("last_inspect_task_id", None),
        ("last_inspect_summary", None),
        ("last_inspect_defects", None),
        ("last_inspect_severity", None),
        ("last_inspect_image_b64", None),
        ("last_inspect_elapsed", None),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    sample_dir = str(Path(__file__).parent.parent.parent / "data" / "sample_images")
    samples = []
    if os.path.isdir(sample_dir):
        for f in sorted(os.listdir(sample_dir)):
            if f.endswith(('.jpg', '.png', '.jpeg')):
                samples.append(f)

    col_left, col_right = st.columns([0.9, 1.6])

    with col_left:
        st.caption("📁 示例图片")
        labels = [LABEL_MAP.get(n, n) for n in samples]
        current_idx = 0
        if st.session_state.selected_sample_name in samples:
            current_idx = samples.index(st.session_state.selected_sample_name)

        selected_label = st.selectbox(
            "选示例", options=labels, index=current_idx,
            label_visibility="collapsed", key="sample_select",
        )
        selected_name = samples[labels.index(selected_label)]
        if selected_name != st.session_state.selected_sample_name:
            st.session_state.selected_sample_name = selected_name
            st.session_state.uploaded_image_bytes = None
            st.rerun()

        with st.expander("📤 或上传图片", expanded=False):
            uf = st.file_uploader("file", type=["jpg","jpeg","png"], label_visibility="collapsed")
            if uf is not None:
                st.session_state.uploaded_image_bytes = uf.read()
                st.session_state.selected_sample_name = None
                st.rerun()

        with st.expander("⚙️ 参数", expanded=False):
            conf_threshold = st.slider("阈值", 0.0, 1.0, 0.25, 0.05)
            enable_sam = st.checkbox("SAM 分割", value=True)

        detect_btn = st.button("🔍 开始检测", type="primary", use_container_width=True)

        # ── 历史记录列表 ──
        sessions = get_inspect_sessions()
        if sessions:
            st.divider()
            st.caption(f"📋 检测记录 ({len(sessions)}/{MAX_SESSIONS})")
            if is_history_full():
                st.warning("⚠️ 已达 10 条上限，新记录将覆盖最旧的")
            for s in sessions[:5]:
                sev_icon = {"INFO": "🟢", "WARN": "🟡", "CRITICAL": "🔴"}.get(s["severity"], "⚪")
                c1, c2 = st.columns([4, 1])
                c1.caption(f"{sev_icon} {s['timestamp'][11:]} | {s['image_name']} | {s['summary'].get('total',0)}缺陷")
                if c2.button("🗑", key=f"del_{s['id']}", help="删除此记录"):
                    delete_inspect_session(s["id"])
                    st.rerun()

    with col_right:
        has_image = st.session_state.uploaded_image_bytes is not None or st.session_state.selected_sample_name is not None

        if detect_btn and has_image:
            if st.session_state.uploaded_image_bytes is not None:
                raw_bytes = st.session_state.uploaded_image_bytes
            else:
                with open(f"{sample_dir}/{st.session_state.selected_sample_name}", "rb") as f:
                    raw_bytes = f.read()

            image_b64 = base64.b64encode(raw_bytes).decode()

            with st.spinner("AI 检测中..."):
                t0 = time.time()
                try:
                    resp = requests.post(f"{api_url}/api/inspect", json={
                        "image": image_b64, "conf_threshold": conf_threshold,
                        "enable_sam": enable_sam,
                    }, timeout=120)
                    elapsed = time.time() - t0

                    if resp.status_code == 200:
                        result = resp.json()

                        # ── 存入历史会话系统 ──
                        img_label = LABEL_MAP.get(st.session_state.selected_sample_name, "上传图片") if st.session_state.selected_sample_name else "上传图片"
                        add_inspect_session(
                            image_name=img_label,
                            summary=result.get("summary", {}),
                            defects=result.get("defects", []),
                            severity=result.get("summary", {}).get("overall_severity", "INFO"),
                            elapsed=elapsed,
                            image_b64=image_b64,
                            annotated_b64=result.get("annotated_image_b64", ""),
                        )

                        # 原图 + 标注图
                        pic1, pic2 = st.columns(2)
                        with pic1:
                            st.caption("📷 原图")
                            st.image(resize_for_display(raw_bytes), use_container_width=True)
                        with pic2:
                            st.caption(f"🔍 检测结果 ({elapsed:.1f}s)")
                            if result.get("annotated_image_b64"):
                                st.image(resize_for_display(base64.b64decode(result["annotated_image_b64"])), use_container_width=True)

                        # 判定
                        overall = result.get("summary", {}).get("overall_severity", "INFO")
                        if overall == "CRITICAL":
                            st.error("🔴 FAIL — 检测到严重缺陷")
                        elif overall == "WARN":
                            st.warning("⚠️ WARN — 疑似缺陷，建议复核")
                        else:
                            st.success("✅ PASS — 未检测到严重缺陷")

                        # 统计
                        s = result.get("summary", {})
                        m1, m2, m3, m4, m5 = st.columns(5)
                        m1.metric("候选", s.get("total", 0))
                        m2.metric("确认", s.get("confirmed", 0))
                        m3.metric("疑似", s.get("suspicious", 0))
                        m4.metric("严重", s.get("critical", 0))
                        m5.metric("耗时", f"{elapsed:.1f}s")

                        # 缺陷表
                        defects = result.get("defects", [])
                        if defects:
                            import pandas as pd
                            df = pd.DataFrame([{
                                "类型": d.get("class_name","?"),
                                "置信度": f"{d.get('confidence',0):.2f}",
                                "严重度": d.get("severity",""),
                                "判定": d.get("verdict",""),
                            } for d in defects])
                            st.dataframe(df, use_container_width=True, hide_index=True,
                                         height=min(35*len(defects)+38, 150))

                        # ── 联动按钮：引导用户去其他页面看结果 ──
                        st.divider()
                        st.caption("🔗 基于本次检测结果，你可以：")
                        btn_col1, btn_col2, btn_col3 = st.columns(3)
                        with btn_col1:
                            st.info("💬 **Agent 对话**\n\n让 AI 分析检测结果、查标准、给建议")
                        with btn_col2:
                            st.info("📊 **分析仪表盘**\n\n切到「实时数据」看累积统计和趋势")
                        with btn_col3:
                            st.info("📋 **质检报告**\n\n切到「真实历史」看本次检测报告")

                    else:
                        st.error(f"检测失败 ({resp.status_code})")
                except requests.exceptions.ConnectionError:
                    st.error("无法连接后端 API，请先启动 FastAPI")
                except Exception as e:
                    st.error(f"出错: {e}")

        elif has_image and not detect_btn:
            if st.session_state.uploaded_image_bytes is not None:
                preview = resize_for_display(st.session_state.uploaded_image_bytes)
            else:
                with open(f"{sample_dir}/{st.session_state.selected_sample_name}", "rb") as f:
                    preview = resize_for_display(f.read())
            st.caption(f"📷 预览 — {LABEL_MAP.get(st.session_state.selected_sample_name, '')}")
            st.image(preview, use_container_width=True)
            st.info("👈 点击 **开始检测**")

        else:
            sessions = get_inspect_sessions()
            if sessions:
                latest = sessions[0]
                st.success(
                    f"📌 最近检测 ({len(sessions)}条记录)：{latest['image_name']}，"
                    f"{latest['summary'].get('total', 0)} 缺陷，{latest['severity']}，"
                    f"{latest['elapsed']:.1f}s"
                )
                st.caption("👈 选择新图片继续检测，或去其他页面查看分析结果")
            else:
                st.info("👈 选择示例图片或上传，点击开始检测")
