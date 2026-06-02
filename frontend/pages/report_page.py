"""质检报告页"""
import streamlit as st
import requests


def render(api_url: str):
    st.title("📋 质检报告")
    st.caption("查看和导出 AI 自动生成的质检报告")

    # 报告列表
    st.subheader("报告列表")

    reports = [
        {"id": "R00047", "batch": "B2406-033", "verdict": "⚠️WARN", "date": "2026-06-02 14:32"},
        {"id": "R00046", "batch": "B2406-032", "verdict": "✅PASS", "date": "2026-06-01 09:15"},
        {"id": "R00045", "batch": "B2406-031", "verdict": "✅PASS", "date": "2026-05-31 16:45"},
        {"id": "R00044", "batch": "B2406-030", "verdict": "🔴FAIL", "date": "2026-05-30 11:00"},
    ]

    selected_idx = st.selectbox(
        "选择报告",
        options=range(len(reports)),
        format_func=lambda i: f"{reports[i]['id']} | {reports[i]['batch']} | {reports[i]['verdict']} | {reports[i]['date']}",
    )

    selected = reports[selected_idx]

    st.divider()
    st.subheader(f"📄 报告 {selected['id']} — 批次 {selected['batch']}")

    # 报告内容（Markdown 渲染）
    verdict_emoji = {"✅PASS": "合格", "⚠️WARN": "警告放行", "🔴FAIL": "不合格"}

    report_content = f"""---

## 基本信息

| 项目 | 内容 |
|------|------|
| **报告ID** | {selected['id']} |
| **批次号** | {selected['batch']} |
| **检测时间** | {selected['date']} |
| **检测数量** | 50 pcs |
| **判定结果** | **{selected['verdict']}** ({verdict_emoji.get(selected['verdict'], '')}) |

## 缺陷汇总

| 缺陷类型 | 数量 | 占比 | 严重度 | 主要工位 |
|----------|------|------|--------|----------|
| 桥接 | 3 | 35% | 🔴CRITICAL | S2 |
| 偏移 | 2 | 25% | 🟡WARN | S3 |
| 少锡 | 1 | 12% | 🟡WARN | S2 |

## 处置建议

1. **桥接缺陷集中于 S2 工位** (3/3 桥接发生在 S2)，建议立即检查 S2 印刷机钢网张力
2. 本批次按 **AQL=0.65** 标准实施加严抽检
3. 检查回流焊 **Zone2-Zone3** 温度曲线是否偏离标准 (±5°C)
4. 历史案例参考: C2024-0152 — 类似桥接问题，根因为钢网清洗周期不足

## 技术参数

| 参数 | 值 |
|------|-----|
| 检测引擎 | YOLOv8n + SAM 2.1 |
| 置信度阈值 | 0.25 |
| 处理耗时 | 1.2s |
| 报告生成 | 自动 (Agent) |

---

*本报告由 SmartEye AI Agent 自动生成，未经人工审核。*
"""

    st.markdown(report_content)

    # 导出按钮
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📥 下载 Markdown",
            data=report_content,
            file_name=f"{selected['id']}_质检报告.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col2:
        st.button("📥 导出 DOCX (需 python-docx)", use_container_width=True, disabled=True,
                  help="完整 DOCX 导出功能开发中")
