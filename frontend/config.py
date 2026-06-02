"""Streamlit 前端配置"""
import streamlit as st

# 默认 API 地址
DEFAULT_API_URL = "http://127.0.0.1:8000"


def get_api_url() -> str:
    """获取当前 API 地址（支持用户在侧边栏修改）"""
    return st.session_state.get("api_url", DEFAULT_API_URL)


def init_page_config():
    """初始化 Streamlit 页面全局配置"""
    st.set_page_config(
        page_title="SmartEye — AI 质检系统",
        page_icon="🏭",
        layout="wide",
        initial_sidebar_state="expanded",
    )
