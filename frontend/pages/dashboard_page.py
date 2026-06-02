"""分析仪表盘页"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


def render(api_url: str):
    st.title("📊 分析仪表盘")
    st.caption("缺陷统计 · 趋势分析 · 质量热力图   (演示数据)")

    # 生成演示数据
    np.random.seed(42)
    dates = pd.date_range("2026-05-01", periods=30)
    n = 90  # 30 days × 3 entries
    demo_data = pd.DataFrame({
        "日期": np.repeat(dates, 3),
        "缺陷类型": np.random.choice(
            ["桥接", "偏移", "少锡", "多锡", "划伤", "错件"],
            n, p=[0.3, 0.25, 0.2, 0.1, 0.1, 0.05]
        ),
        "工位": np.random.choice(["S1", "S2", "S3", "S4"], n),
        "数量": np.random.poisson(2, n),
    })

    # 卡片区
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("总检测批次数", "152", "+12")
    c2.metric("平均合格率", "93.4%", "-1.2%")
    c3.metric("平均检测时间", "1.2s", "-0.3s")
    c4.metric("本周告警", "3", "+2")

    st.divider()

    # 2×2 图表布局
    row1_l, row1_r = st.columns(2)
    row2_l, row2_r = st.columns(2)

    with row1_l:
        st.subheader("📊 帕累托分析")
        pareto = demo_data.groupby("缺陷类型")["数量"].sum().sort_values(ascending=False).reset_index()
        pareto["累计占比"] = pareto["数量"].cumsum() / pareto["数量"].sum()

        fig = go.Figure()
        fig.add_trace(go.Bar(x=pareto["缺陷类型"], y=pareto["数量"], name="数量",
                             marker_color="#3498DB"))
        fig.add_trace(go.Scatter(x=pareto["缺陷类型"], y=pareto["累计占比"]*100,
                                 name="累计占比%", yaxis="y2", mode="lines+markers",
                                 marker_color="#E74C3C"))
        fig.add_hline(y=80, line_dash="dash", line_color="gray",
                      annotation_text="80% 线", yref="y2")
        fig.update_layout(
            yaxis=dict(title="缺陷数量"),
            yaxis2=dict(title="累计占比 (%)", overlaying="y", side="right", range=[0, 100]),
            height=350,
            margin=dict(t=30),
        )
        st.plotly_chart(fig, use_container_width=True)

    with row1_r:
        st.subheader("📈 缺陷率趋势 (P-Chart)")
        trend = demo_data.groupby("日期")["数量"].sum().reset_index()
        mean_val = trend["数量"].mean()
        std_val = trend["数量"].std()
        ucl = mean_val + 3 * std_val

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=trend["日期"], y=trend["数量"], mode="lines+markers",
                                 name="缺陷数", marker_color="#2E86C1"))
        fig.add_hline(y=mean_val, line_dash="dash", line_color="green",
                      annotation_text=f"均值 {mean_val:.0f}")
        fig.add_hline(y=ucl, line_dash="dash", line_color="red",
                      annotation_text=f"UCL {ucl:.0f}")
        fig.update_layout(height=350, margin=dict(t=30),
                          yaxis_title="缺陷数量")
        st.plotly_chart(fig, use_container_width=True)

    with row2_l:
        st.subheader("🔥 工位 × 缺陷热力图")
        heatmap = demo_data.pivot_table(
            values="数量", index="缺陷类型", columns="工位", aggfunc="sum", fill_value=0
        )
        fig = px.imshow(heatmap, text_auto=True, aspect="auto",
                        color_continuous_scale="YlOrRd")
        fig.update_layout(height=350, margin=dict(t=30), xaxis_title="工位", yaxis_title="缺陷类型")
        st.plotly_chart(fig, use_container_width=True)

    with row2_r:
        st.subheader("📋 最近检测记录")
        recent = demo_data.tail(10).groupby("日期")["数量"].sum().reset_index()
        recent["判定"] = np.where(recent["数量"] > mean_val + 2*std_val,
                                 "⚠️", "✅")
        st.dataframe(
            recent.sort_values("日期", ascending=False),
            column_config={
                "日期": st.column_config.DateColumn("日期"),
                "数量": st.column_config.NumberColumn("缺陷数"),
                "判定": "判定",
            },
            use_container_width=True,
            hide_index=True,
        )
