"""分析仪表盘 — 检测会话历史 + 后端API + 演示数据"""
import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
from frontend.session import get_inspect_sessions, delete_inspect_session, MAX_SESSIONS


def _demo_data():
    np.random.seed(42)
    dates = pd.date_range("2026-05-01", periods=30)
    n = 90
    return pd.DataFrame({
        "日期": np.repeat(dates, 3),
        "缺陷类型": np.random.choice(["桥接","偏移","少锡","多锡","划伤","错件"], n, p=[0.3,0.25,0.2,0.1,0.1,0.05]),
        "工位": np.random.choice(["S1","S2","S3","S4"], n),
        "数量": np.random.poisson(2, n),
    })


def _session_data():
    """从检测会话历史构建统计数据"""
    sessions = get_inspect_sessions()
    if not sessions:
        return None
    type_counter = Counter()
    items = []
    for s in sessions:
        for d in s.get("defects", []):
            type_counter[d.get("class_name", "?")] += 1
        items.append({
            "timestamp": s["timestamp"],
            "image_name": s["image_name"],
            "defect_count": s["summary"].get("total", 0),
            "confirmed": s["summary"].get("confirmed", 0),
            "critical": s["summary"].get("critical", 0),
            "severity": s["severity"],
            "session_id": s["id"],
        })
    total = len(sessions)
    critical = sum(1 for i in items if i["critical"] > 0)
    return {
        "total": total, "critical": critical,
        "type_counter": dict(type_counter), "items": items,
    }


def _real_data(api_url: str):
    try:
        r = requests.get(f"{api_url}/api/inspect/history?limit=50", timeout=5)
        if r.status_code != 200: return None
        items = r.json().get("items", [])
        if not items: return None
        tc = Counter()
        for i in items:
            for t, c in i.get("defect_types", {}).items(): tc[t] += c
        return {"total": len(items), "type_counter": dict(tc), "items": items}
    except: return None


def render(api_url: str):
    st.title("📊 分析仪表盘")

    mode = st.radio("数据来源", ["📋 检测会话", "📡 后端实时", "📊 演示数据"],
                    horizontal=True, label_visibility="collapsed")
    is_session = "会话" in mode
    is_real = "后端" in mode

    # 准备数据
    if is_session:
        data = _session_data()
        if not data:
            st.warning("暂无检测记录。请先在「质量检测」页面执行检测。")
            return
        # 显示会话列表
        with st.expander(f"📋 检测会话 ({data['total']}/{MAX_SESSIONS})", expanded=False):
            for item in data["items"]:
                c1, c2 = st.columns([5, 1])
                sev = {"INFO":"🟢","WARN":"🟡","CRITICAL":"🔴"}.get(item["severity"],"⚪")
                c1.caption(f"{sev} {item['timestamp']} | {item['image_name']} | {item['defect_count']}缺陷")
                if c2.button("🗑", key=f"dd_{item['session_id']}"):
                    delete_inspect_session(item["session_id"])
                    st.rerun()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("检测次数", data["total"])
        c2.metric("含严重缺陷", data["critical"])
        c3.metric("合格率", f"{(data['total'] - data['critical']) / max(data['total'], 1) * 100:.0f}%")
        c4.metric("会话上限", f"{data['total']}/{MAX_SESSIONS}")
        type_counter = data["type_counter"]
        items = data["items"]
    elif is_real:
        real = _real_data(api_url)
        if real is None:
            st.warning("暂无后端检测记录。")
            return
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("总检测", real["total"])
        c2.metric("待定", "-")
        c3.metric("待定", "-")
        c4.metric("来源", "API")
        type_counter = real["type_counter"]
        items = real["items"]
    else:
        data = _demo_data()
        type_counter = dict(data.groupby("缺陷类型")["数量"].sum())
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("总批次", "152", "+12")
        c2.metric("合格率", "93.4%", "-1.2%")
        c3.metric("检测时间", "1.0s", "-0.2s")
        c4.metric("告警", "3", "+2")
        items = None

    st.divider()

    r1l, r1r = st.columns(2)
    with r1l:
        st.subheader("📊 帕累托分析")
        if type_counter:
            pareto = pd.DataFrame({"类型": list(type_counter.keys()), "数量": list(type_counter.values())}).sort_values("数量", ascending=False)
            pareto["累计%"] = (pareto["数量"].cumsum() / pareto["数量"].sum() * 100)
            fig = go.Figure()
            fig.add_trace(go.Bar(x=pareto["类型"], y=pareto["数量"], name="数量", marker_color="#3498DB"))
            fig.add_trace(go.Scatter(x=pareto["类型"], y=pareto["累计%"], name="累计%", yaxis="y2", mode="lines+markers", marker_color="#E74C3C"))
            fig.add_hline(y=80, line_dash="dash", line_color="gray", annotation_text="80%", yref="y2")
            fig.update_layout(yaxis2=dict(overlaying="y", side="right", range=[0, 100]), height=350, margin=dict(t=30))
            st.plotly_chart(fig, use_container_width=True)
    with r1r:
        st.subheader("📈 趋势")
        if is_session and items:
            # 会话数据趋势
            rows = [{"t": pd.Timestamp(i["timestamp"]), "n": i["defect_count"]} for i in items]
            trend = pd.DataFrame(rows).sort_values("t")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=trend["t"], y=trend["n"], mode="lines+markers", marker_color="#2E86C1"))
            fig.update_layout(height=350, margin=dict(t=30), yaxis_title="缺陷数")
            st.plotly_chart(fig, use_container_width=True)
        elif is_real and items:
            # 后端API数据趋势
            if isinstance(items[0], dict) and "timestamp" in items[0]:
                rows = [{"t": pd.Timestamp(i["timestamp"]), "n": i.get("defect_count", 0)} for i in items]
                trend = pd.DataFrame(rows).sort_values("t")
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=trend["t"], y=trend["n"], mode="lines+markers", marker_color="#2E86C1"))
                fig.update_layout(height=350, margin=dict(t=30), yaxis_title="缺陷数")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("暂无时间序列数据")
        elif not is_session and not is_real:
            # 演示数据趋势
            demo = _demo_data()
            trend = demo.groupby("日期")["数量"].sum().reset_index()
            m = trend["数量"].mean()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=trend["日期"], y=trend["数量"], mode="lines+markers", marker_color="#2E86C1"))
            fig.add_hline(y=m+3*trend["数量"].std(), line_dash="dash", line_color="red", annotation_text="UCL")
            fig.update_layout(height=350, margin=dict(t=30), yaxis_title="缺陷数量")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无足够数据绘制趋势")

    r2l, r2r = st.columns(2)
    with r2l:
        st.subheader("📋 会话列表")
        if items:
            df = pd.DataFrame([{"时间": i["timestamp"], "图片": i.get("image_name",""), "缺陷": i.get("defect_count",0), "严重度": i.get("severity","")} for i in items[:10]])
            st.dataframe(df, use_container_width=True, hide_index=True, height=300)
    with r2r:
        st.subheader("🔴 严重缺陷会话")
        if items:
            crit = [i for i in items if i.get("severity") == "CRITICAL"]
            if crit:
                for c in crit:
                    st.caption(f"🔴 {c['timestamp']} | {c.get('image_name','')} | {c.get('defect_count',0)}缺陷")
            else:
                st.caption("无严重缺陷记录 ✅")
