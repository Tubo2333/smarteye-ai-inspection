"""Streamlit Session State 管理"""
import uuid
import streamlit as st


def init_session():
    """初始化 Streamlit session state 默认值"""
    defaults = {
        "session_id": str(uuid.uuid4()),
        "chat_history": [],
        "last_task_id": None,
        "last_inspection_result": None,
        "last_trace": [],
        "api_url": "http://127.0.0.1:8000",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_session_id() -> str:
    """获取当前会话 ID"""
    return st.session_state.session_id


def clear_chat():
    """清除对话历史"""
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.chat_history = []
    st.session_state.last_trace = []


def add_chat_message(role: str, content: str, artifacts: list = None):
    """添加一条对话消息"""
    msg = {"role": role, "content": content}
    if artifacts:
        msg["artifacts"] = artifacts
    st.session_state.chat_history.append(msg)
