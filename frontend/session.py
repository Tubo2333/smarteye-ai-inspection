"""Streamlit Session State 管理 — 含检测会话历史系统"""
import uuid
import time
import streamlit as st

MAX_SESSIONS = 10


def init_session():
    """初始化所有 session state 默认值"""
    defaults = {
        "session_id": str(uuid.uuid4()),
        "chat_histories": {},      # {session_id: [{role, content}, ...]}  按会话隔离
        "last_trace": [],
        "api_url": "http://127.0.0.1:8000",
        "inspect_sessions": [],
        "active_session_id": None,
        "chat_session_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_session_id() -> str:
    return st.session_state.session_id


def clear_chat(session_id: str = None):
    """清除对话历史。指定 session_id 则只清除该会话的。"""
    if session_id:
        st.session_state.chat_histories.pop(session_id, None)
    else:
        st.session_state.chat_histories = {}
    st.session_state.last_trace = []


def add_chat_message(role: str, content: str, session_id: str = None, artifacts: list = None):
    """添加消息到指定会话的对话历史"""
    sid = session_id or st.session_state.get("chat_session_id") or "default"
    if sid not in st.session_state.chat_histories:
        st.session_state.chat_histories[sid] = []
    msg = {"role": role, "content": content}
    if artifacts:
        msg["artifacts"] = artifacts
    st.session_state.chat_histories[sid].append(msg)


def get_chat_history(session_id: str = None):
    """获取指定会话的对话历史"""
    sid = session_id or st.session_state.get("chat_session_id") or "default"
    return st.session_state.chat_histories.get(sid, [])


# ═══════════════════════════════════════════════════════════════
# 检测会话历史管理
# ═══════════════════════════════════════════════════════════════

def add_inspect_session(image_name: str, summary: dict, defects: list,
                        severity: str, elapsed: float,
                        image_b64: str = "", annotated_b64: str = ""):
    """添加一次检测记录到历史（最多 MAX_SESSIONS 条）"""
    session = {
        "id": f"sess_{int(time.time() * 1000)}",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "image_name": image_name,
        "summary": summary,
        "defects": defects,
        "severity": severity,
        "elapsed": elapsed,
        "image_b64": image_b64,
        "annotated_image_b64": annotated_b64,
    }
    sessions = st.session_state.inspect_sessions
    sessions.insert(0, session)

    # 超过上限则截断
    if len(sessions) > MAX_SESSIONS:
        sessions = sessions[:MAX_SESSIONS]

    st.session_state.inspect_sessions = sessions
    st.session_state.active_session_id = session["id"]
    return session["id"]


def get_inspect_sessions():
    """获取所有检测历史"""
    return st.session_state.inspect_sessions


def get_active_session():
    """获取当前选中的检测会话"""
    sid = st.session_state.get("active_session_id")
    for s in st.session_state.inspect_sessions:
        if s["id"] == sid:
            return s
    # 默认返回最新
    sessions = st.session_state.inspect_sessions
    return sessions[0] if sessions else None


def get_chat_session():
    """获取 Agent 对话页当前选中的会话"""
    sid = st.session_state.get("chat_session_id")
    for s in st.session_state.inspect_sessions:
        if s["id"] == sid:
            return s
    sessions = st.session_state.inspect_sessions
    return sessions[0] if sessions else None


def set_chat_session(session_id: str):
    st.session_state.chat_session_id = session_id


def delete_inspect_session(session_id: str):
    """删除指定检测会话"""
    st.session_state.inspect_sessions = [
        s for s in st.session_state.inspect_sessions if s["id"] != session_id
    ]
    if st.session_state.get("active_session_id") == session_id:
        st.session_state.active_session_id = None
    if st.session_state.get("chat_session_id") == session_id:
        st.session_state.chat_session_id = None


def is_history_full():
    return len(st.session_state.inspect_sessions) >= MAX_SESSIONS
