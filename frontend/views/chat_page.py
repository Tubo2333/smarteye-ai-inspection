"""Agent 对话页 — 优化后的布局"""
import streamlit as st
import requests
from frontend.session import (
    get_session_id, add_chat_message, clear_chat, get_chat_history,
    get_inspect_sessions, get_chat_session, set_chat_session,
    delete_inspect_session, MAX_SESSIONS
)


def render(api_url: str):
    st.markdown("### 💬 Agent 对话")

    if "chat_pending_msg" not in st.session_state:
        st.session_state.chat_pending_msg = None

    sessions = get_inspect_sessions()

    # ═══════════ 会话选择（默认折叠，只显最近 3 条）═══════════
    if sessions:
        options = []
        option_to_id = {}
        for s in sessions:
            sev = {"INFO": "🟢", "WARN": "🟡", "CRITICAL": "🔴"}.get(s["severity"], "⚪")
            options.append(f"{sev} {s['timestamp']} | {s['image_name']} | {s['summary'].get('total',0)}缺陷")
            option_to_id[options[-1]] = s["id"]

        cur_id = st.session_state.get("chat_session_id")
        cur_idx = 0
        for i, s in enumerate(sessions):
            if s["id"] == cur_id:
                cur_idx = i
                break

        # 默认折叠，显示最近 3 条预览
        preview_lines = "<br>".join(options[:3])
        with st.expander(
            f"📋 检测会话 ({len(sessions)}/{MAX_SESSIONS}) — {sessions[0]['timestamp'] if sessions else ''}",
            expanded=(len(sessions) <= 3)
        ):
            selected_label = st.radio(
                "选择会话", options, index=cur_idx,
                label_visibility="collapsed", key="session_radio",
            )
            selected_id = option_to_id[selected_label]

            if selected_id != st.session_state.get("chat_session_id"):
                set_chat_session(selected_id)
                st.rerun()

            if len(sessions) >= MAX_SESSIONS:
                st.warning(f"⚠️ 已达 {MAX_SESSIONS} 条上限")

        # ── 操作按钮：主操作在前，危险操作在后 ──
        active = get_chat_session()
        if active:
            st.caption(f"📌 {active['image_name']} — {active['summary'].get('total',0)}缺陷, {active['severity']}")

            defect_names = [d.get("class_name", "?") for d in active.get("defects", [])]
            b1, b2, b3 = st.columns([2, 2, 1])
            with b1:
                if st.button("🔍 分析结果", use_container_width=True, key="btn_a",
                             help="分析此检测结果，判断是否存在系统性异常"):
                    st.session_state.chat_pending_msg = (
                        f"分析以下检测结果：{', '.join(defect_names) if defect_names else '无缺陷'}，严重度{active['severity']}"
                    )
                    st.rerun()
            with b2:
                if st.button("📖 查标准", use_container_width=True, key="btn_s",
                             help="查询此缺陷的IPC质量标准"):
                    st.session_state.chat_pending_msg = (
                        f"{defect_names[0] if defect_names else '缺陷'}的IPC质量标准是什么？"
                    )
                    st.rerun()
            with b3:
                if st.button("🗑", key="btn_d", help="删除此会话"):
                    delete_inspect_session(active["id"])
                    st.rerun()

            c1, _ = st.columns([1, 3])
            with c1:
                if st.button("清除对话", key="btn_cc", help="仅清除当前会话的聊天记录"):
                    clear_chat(selected_id)
                    st.rerun()
    else:
        st.info("暂无检测记录。请先在「质量检测」页面执行检测。")

    # ── 处理 pending ──
    pending = st.session_state.chat_pending_msg
    if pending:
        st.session_state.chat_pending_msg = None
        _do_send(api_url, pending)

    st.divider()

    # ═══════════ 对话区 ═══════════
    col_main, col_trace = st.columns([2.2, 1])

    with col_main:
        cur_sid = st.session_state.get("chat_session_id", "default")
        for msg in get_chat_history(cur_sid):
            with st.chat_message(msg["role"]):
                st.markdown(
                    f'<div style="font-size:13px;line-height:1.6;">{msg["content"]}</div>',
                    unsafe_allow_html=True,
                )

        user_msg = st.chat_input("输入问题（当前会话上下文自动附加）...")
        if user_msg:
            _do_send(api_url, user_msg)
            st.rerun()

    with col_trace:
        st.caption("📡 Agent Trace")
        traces = st.session_state.get("last_trace", [])
        for entry in traces:
            st.caption(
                f'<span style="font-size:11px;color:#888;">'
                f'{entry.get("timestamp","")} | {entry.get("agent","?")} | {entry.get("action","")}'
                f'</span>',
                unsafe_allow_html=True,
            )
        if not traces:
            st.caption('<span style="font-size:11px;color:#666;">发送后显示</span>', unsafe_allow_html=True)

        st.divider()

        # ── 快捷提问（紧凑版）──
        st.caption("💡 快捷提问")
        prompts = [
            ("📋 分析", "分析以上检测结果，判断是否存在系统性异常并给出处置优先级"),
            ("📖 标准", "以上检测到的缺陷对应的IPC-A-610质量标准是什么？"),
            ("🔧 处置", "针对以上缺陷给出具体可执行的处置措施，按紧急程度排序"),
            ("📊 趋势", "基于历史检测数据，分析缺陷率趋势并判断是否需要工艺调整"),
            ("⚠️ 风险", "评估当前缺陷的严重度和风险等级，给出升级建议"),
            ("✅ 放行", "基于检测结果和IPC标准，判断本批次是否可以放行"),
            ("🔍 根因", "根据缺陷特征推测可能的根因，建议排查方向"),
            ("📝 报告", "基于以上检测结果生成完整的质检报告（Markdown格式）"),
        ]
        for i, (label, text) in enumerate(prompts):
            if st.button(label, key=f"qp_{i}", use_container_width=True, help=text):
                st.session_state.chat_pending_msg = text
                st.rerun()


def _do_send(api_url: str, message: str):
    cur_sid = st.session_state.get("chat_session_id", "default")
    add_chat_message("user", message, session_id=cur_sid)
    active = get_chat_session()
    if active:
        d = active.get("defects", [])
        ds = ", ".join([f"{x.get('class_name','?')}({x.get('severity','')})" for x in d]) or "无"
        message = (
            f"[检测会话: {active['timestamp']}, 图片: {active['image_name']}, "
            f"缺陷: {ds}, 严重度: {active['severity']}, 总数: {active['summary'].get('total',0)}]"
            f"\n{message}"
        )
    try:
        resp = requests.post(f"{api_url}/api/agent/chat", json={
            "message": message, "session_id": get_session_id(), "task_type": "chat",
        }, timeout=120)
        if resp.status_code == 200:
            result = resp.json()
            add_chat_message("assistant", result.get("reply", ""), session_id=cur_sid)
            st.session_state.last_trace = result.get("agent_trace", [])
        else:
            add_chat_message("assistant", f"请求失败 ({resp.status_code})", session_id=cur_sid)
    except Exception as e:
        add_chat_message("assistant", f"出错: {e}", session_id=cur_sid)
