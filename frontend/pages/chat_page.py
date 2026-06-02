"""Agent 对话页 — Chat + Agent Trace"""
import base64
import json
import streamlit as st
import requests
from frontend.session import get_session_id, add_chat_message, clear_chat


def render(api_url: str):
    st.title("💬 Agent 对话")
    st.caption("与 AI 质检 Agent 对话，查询标准、分析缺陷、获取建议")

    col_main, col_trace = st.columns([2, 1])

    with col_main:
        # 对话历史
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.get("chat_history", []):
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    for art in msg.get("artifacts", []):
                        if art.get("type") == "image":
                            st.image(base64.b64decode(art["data"]))

        # 输入区
        col_input, col_upload = st.columns([5, 1])
        with col_input:
            user_msg = st.chat_input("输入消息，例如：BGA焊点void率标准是多少？")
        with col_upload:
            uploaded_img = st.file_uploader(
                "📎", type=["jpg", "png"],
                label_visibility="collapsed",
                key="chat_upload",
            )

        if user_msg or (uploaded_img and uploaded_img is not None):
            image_b64 = None
            if uploaded_img:
                image_b64 = base64.b64encode(uploaded_img.read()).decode()

            add_chat_message("user", user_msg or "(已上传图片)")

            with st.spinner("Agent 思考中..."):
                try:
                    resp = requests.post(
                        f"{api_url}/api/agent/chat",
                        json={
                            "message": user_msg or "请分析这张图片",
                            "image_b64": image_b64,
                            "session_id": get_session_id(),
                            "task_type": "inspection" if image_b64 else "chat",
                        },
                        timeout=120,
                    )

                    if resp.status_code == 200:
                        result = resp.json()
                        add_chat_message("assistant", result.get("reply", ""),
                                         result.get("artifacts"))
                        st.session_state.last_trace = result.get("agent_trace", [])
                        st.rerun()
                    else:
                        st.error(f"请求失败: {resp.text[:200]}")
                except requests.exceptions.ConnectionError:
                    st.error(f"无法连接后端 API ({api_url})")
                except Exception as e:
                    st.error(f"出错: {e}")

    with col_trace:
        st.subheader("📡 Agent Trace")

        if st.button("🗑️ 清除对话", use_container_width=True):
            clear_chat()
            st.rerun()

        st.divider()

        traces = st.session_state.get("last_trace", [])
        if traces:
            for i, entry in enumerate(traces):
                with st.expander(f"{entry.get('agent', '?')} — {entry.get('action', '')}", expanded=(i == 0)):
                    st.caption(f"🕐 {entry.get('timestamp', '')}")
                    for tc in entry.get("tool_calls", []):
                        st.code(tc, language="json")
        else:
            st.caption("发送消息后，这里会显示 Agent 调用链路")

        st.divider()
        st.caption("💡 试试这些问题:")
        st.caption("- BGA焊点void率不能超过多少？")
        st.caption("- 虚焊率高该怎么处理？")
        st.caption("- 帮我看看这张PCB照片")
