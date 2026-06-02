"""
SmartEye Streamlit 前端入口
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from frontend.config import init_page_config, get_api_url, inject_global_css
from frontend.session import init_session

init_page_config()
init_session()
inject_global_css()

# ═══════════════════════════════════════════════════════════════
# 侧边栏
# ═══════════════════════════════════════════════════════════════

st.sidebar.markdown("### 🏭 SmartEye")
st.sidebar.caption("AI 视觉质检多 Agent 系统")
st.sidebar.divider()

# 导航
page = st.sidebar.radio(
    "导航",
    ["📸 质量检测", "💬 Agent 对话", "📊 分析仪表盘", "📋 质检报告"],
    label_visibility="collapsed",
)
st.sidebar.divider()

# 设置
with st.sidebar.expander("⚙️ 设置", expanded=False):
    api_url = st.text_input(
        "API 地址",
        value=st.session_state.get("api_url", "http://127.0.0.1:8000"),
        key="api_url_input", label_visibility="collapsed",
    )
    if api_url != st.session_state.get("api_url"):
        st.session_state.api_url = api_url

# 技术栈（折叠到底部关于）
with st.sidebar.expander("ℹ️ 关于", expanded=False):
    st.caption("Powered by")
    st.caption("🧠 Claude + LangGraph")
    st.caption("👁️ YOLOv8 + SAM 2.1")
    st.caption("📚 ChromaDB RAG")
    st.caption("🌐 FastAPI + Streamlit")

# ═══════════════════════════════════════════════════════════════
# 页面路由
# ═══════════════════════════════════════════════════════════════

api = get_api_url()

if page == "📸 质量检测":
    from frontend.views import inspection_page
    inspection_page.render(api)

elif page == "💬 Agent 对话":
    from frontend.views import chat_page
    chat_page.render(api)

elif page == "📊 分析仪表盘":
    from frontend.views import dashboard_page
    dashboard_page.render(api)

elif page == "📋 质检报告":
    from frontend.views import report_page
    report_page.render(api)
