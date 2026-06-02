"""质检报告页 — 检测会话历史 + 后端API + 演示"""
import streamlit as st
from frontend.session import get_inspect_sessions, delete_inspect_session, MAX_SESSIONS


def _demo_reports():
    return [
        {"id": "R00047", "batch": "B2406-033", "verdict": "WARN", "date": "2026-06-02 14:32", "defects": 5},
        {"id": "R00046", "batch": "B2406-032", "verdict": "PASS", "date": "2026-06-01 09:15", "defects": 0},
        {"id": "R00045", "batch": "B2406-031", "verdict": "PASS", "date": "2026-05-31 16:45", "defects": 0},
        {"id": "R00044", "batch": "B2406-030", "verdict": "FAIL", "date": "2026-05-30 11:00", "defects": 8},
    ]


def render(api_url: str):
    st.title("📋 质检报告")

    mode = st.radio("数据来源", ["📋 检测会话", "📊 演示报告"],
                    horizontal=True, label_visibility="collapsed")
    is_session = "会话" in mode

    if is_session:
        sessions = get_inspect_sessions()
        if not sessions:
            st.warning("暂无检测记录。请先在「质量检测」页面执行检测。")
            return
        st.caption(f"📋 检测会话 ({len(sessions)}/{MAX_SESSIONS}) — 每条检测 = 一份报告")

        # 会话列表
        with st.expander("会话列表 — 点击切换", expanded=True):
            for s in sessions:
                sev_icon = {"INFO": "🟢", "WARN": "🟡", "CRITICAL": "🔴"}.get(s["severity"], "⚪")
                c1, c2 = st.columns([5, 1])
                c1.caption(f"{sev_icon} {s['timestamp']} | {s['image_name']} | {s['summary'].get('total',0)}缺陷 | {s['severity']}")
                if c2.button("🗑", key=f"rd_{s['id']}"):
                    delete_inspect_session(s["id"])
                    st.rerun()

        # 展开查看详情
        options = [f"{s['timestamp']} | {s['image_name']} | {s['severity']} | {s['summary'].get('total',0)}缺陷" for s in sessions]
        sel_idx = st.selectbox("选择报告查看详情", range(len(sessions)),
                               format_func=lambda i: options[i])
        s = sessions[sel_idx]
        sev_icon = {"INFO": "✅ PASS", "WARN": "⚠️ WARN", "CRITICAL": "🔴 FAIL"}

        st.divider()
        st.subheader(f"📄 报告 — {s['image_name']}")

        defects = s.get("defects", [])
        defect_rows = ""
        for d in defects:
            defect_rows += f"| {d.get('class_name', '?')} | {d.get('confidence', 0):.2f} | {d.get('severity', '?')} | {d.get('verdict', '?')} |\n"

        st.markdown(f"""
| 项目 | 内容 |
|------|------|
| 会话ID | {s['id'][:12]} |
| 检测时间 | {s['timestamp']} |
| 检测图片 | {s['image_name']} |
| 耗时 | {s['elapsed']:.1f}s |
| 判定 | {sev_icon.get(s['severity'], s['severity'])} |
| 缺陷总数 | {s['summary'].get('total', 0)} |
| 确认缺陷 | {s['summary'].get('confirmed', 0)} |
| 严重缺陷 | {s['summary'].get('critical', 0)} |

### 缺陷明细
| 类型 | 置信度 | 严重度 | 判定 |
|------|--------|--------|------|
{defect_rows if defect_rows else '| 无 | - | - | - |'}

### 处置建议
- 基于检测结果的历史记录，可前往「Agent对话」页获取详细分析
- 建议核对 IPC 标准确认缺陷等级
- 如有严重缺陷，应隔离批次并通知质量工程师

---
*此报告来自本地检测会话记录*
""")
        st.caption("💡 这是你在「质量检测」页面实际检测后自动保存的数据，非模拟生成。")

    else:
        reports = _demo_reports()
        options = [f"{r['id']} | {r['batch']} | {r['verdict']} | {r['date']}" for r in reports]
        sel_idx = st.selectbox("选择报告", range(len(reports)),
                               format_func=lambda i: options[i])
        r = reports[sel_idx]
        verdict_zh = {"PASS": "合格", "WARN": "警告放行", "FAIL": "不合格"}
        icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "🔴"}
        st.markdown(f"""
| 项目 | 内容 |
|------|------|
| 报告ID | {r['id']} |
| 批次 | {r['batch']} |
| 时间 | {r['date']} |
| 检测数 | 50 pcs |
| 判定 | {icon[r['verdict']]} {r['verdict']} ({verdict_zh[r['verdict']]}) |
| 缺陷 | {r['defects']} |

### 处置建议
- 桥接集中于 S2 工位，检查钢网张力
- 按 AQL=0.65 加严抽检
- 检查回流焊 Zone2-3 温度曲线

---
*演示数据*
""")
