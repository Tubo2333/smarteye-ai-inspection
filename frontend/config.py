"""Streamlit 前端配置 — 全局样式 & 主题"""
import streamlit as st

DEFAULT_API_URL = "http://127.0.0.1:8000"


def get_api_url() -> str:
    return st.session_state.get("api_url", DEFAULT_API_URL)


def init_page_config():
    st.set_page_config(
        page_title="SmartEye — AI 质检系统",
        page_icon="🏭",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_global_css():
    """注入全局 CSS — 统一字号梯度、间距、深色适配"""
    st.markdown("""
<style>
/* ═══════════ 全局字号梯度 ═══════════ */
/* H1 主标题 */
h1 { font-size: 22px !important; font-weight: 700 !important; letter-spacing: -0.3px; }
/* H2 二级标题 */
h2 { font-size: 18px !important; font-weight: 600 !important; }
/* H3 三级标题 */
h3 { font-size: 15px !important; font-weight: 600 !important; }
/* 正文 */
p, li, label, .stCaption, .stMarkdown { font-size: 14px !important; }
/* 小字辅助信息 */
small, .st-emotion-cache-1aehpvj, .stDeckGlJsonChart { font-size: 12px !important; }
/* 代码块 */
code, pre { font-size: 13px !important; }

/* ─ 侧边栏 ─ */
[data-testid="stSidebar"] .stRadio label { font-size: 14px !important; padding: 8px 0 !important; }
[data-testid="stSidebar"] .stRadio [role="radiogroup"] { gap: 4px !important; }
[data-testid="stSidebar"] .stTextInput input { font-size: 13px !important; padding: 4px 8px !important; height: 32px !important; }
[data-testid="stSidebar"] hr { margin: 12px 0 !important; }

/* ─ 按钮 ─ */
.stButton > button { font-size: 13px !important; padding: 6px 14px !important; border-radius: 6px !important; }
.stButton > button[kind="primary"] { font-weight: 600 !important; }

/* ─ 对话气泡 ─ */
[data-testid="stChatMessage"] { padding: 10px 16px !important; margin-bottom: 8px !important; }

/* ─ 指标卡片 ─ */
[data-testid="stMetric"] { padding: 8px 12px !important; }
[data-testid="stMetric"] label { font-size: 12px !important; }
[data-testid="stMetric"] [data-testid="stMetricValue"] { font-size: 22px !important; font-weight: 700 !important; }

/* ─ 表格 ─ */
.stDataFrame { font-size: 13px !important; }
.stDataFrame th { font-size: 12px !important; font-weight: 600 !important; }

/* ─ 展开器 ─ */
.stExpander { border-radius: 8px !important; margin-bottom: 12px !important; }
.stExpander summary { font-size: 13px !important; font-weight: 500 !important; }

/* ─ 全局间距统一（8px 倍数） ─ */
[data-testid="stAppViewContainer"] .block-container { padding-top: 24px !important; }
div[data-testid="stVerticalBlock"] > div { gap: 12px !important; }
.stDivider { margin: 16px 0 !important; }

/* ─ 深色模式适配 ─ */
@media (prefers-color-scheme: dark) {
    .stCaption, small { color: #999 !important; }
    .stWarning, .stError, .stSuccess { opacity: 0.9; }
}
</style>
""", unsafe_allow_html=True)
