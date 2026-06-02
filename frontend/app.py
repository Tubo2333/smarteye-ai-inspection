"""
SmartEye Streamlit 前端入口
"""
import streamlit as st
from frontend.config import init_page_config, get_api_url
from frontend.session import init_session

init_page_config()
init_session()

# ═══════════════════════════════════════════════════════════════
# 侧边栏
# ═══════════════════════════════════════════════════════════════

st.sidebar.title("🏭 SmartEye")
st.sidebar.caption("博世苏州 · AI 质检多 Agent 系统")

st.sidebar.divider()

# 导航
page = st.sidebar.radio(
    "导航",
    ["📸 质量检测", "💬 Agent 对话", "📊 分析仪表盘", "📋 质检报告"],
    label_visibility="visible",
)

st.sidebar.divider()

# 设置
st.sidebar.subheader("⚙️ 设置")
api_url = st.sidebar.text_input(
    "API 地址",
    value=st.session_state.get("api_url", "http://127.0.0.1:8000"),
    key="api_url_input",
)
if api_url != st.session_state.get("api_url"):
    st.session_state.api_url = api_url

# 技术栈信息
st.sidebar.divider()
st.sidebar.caption("Powered by")
st.sidebar.caption("🧠 Claude + LangGraph")
st.sidebar.caption("👁️ YOLOv8 + SAM 2.1")
st.sidebar.caption("📚 ChromaDB RAG")
st.sidebar.caption("🌐 FastAPI + Streamlit")

# ═══════════════════════════════════════════════════════════════
# 页面路由
# ═══════════════════════════════════════════════════════════════

api = get_api_url()

if page == "📸 质量检测":
    from frontend.pages import inspection_page
    inspection_page.render(api)

elif page == "💬 Agent 对话":
    from frontend.pages import chat_page
    chat_page.render(api)

elif page == "📊 分析仪表盘":
    from frontend.pages import dashboard_page
    dashboard_page.render(api)

elif page == "📋 质检报告":
    from frontend.pages import report_page
    report_page.render(api)
