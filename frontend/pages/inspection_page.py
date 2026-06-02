"""质量检测页 — Hero Page"""
import base64
import io
import time
import streamlit as st
import requests
from PIL import Image


def render(api_url: str):
    st.title("📸 质量检测")
    st.caption("上传 PCB 图像 → AI Agent 三引擎检测 → 查看缺陷结果")

    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.subheader("📁 输入")

        uploaded_file = st.file_uploader(
            "上传 PCB 图像",
            type=["jpg", "jpeg", "png"],
            help="支持 JPG/PNG 格式",
            label_visibility="collapsed",
        )

        # 或选择示例
        st.divider()
        st.caption("— 或选择示例图片 —")

        sample_dir = "data/sample_images"
        import os
        samples = []
        if os.path.isdir(sample_dir):
            for f in sorted(os.listdir(sample_dir)):
                if f.endswith(('.jpg', '.png', '.jpeg')):
                    samples.append(f)

        if samples:
            sample_cols = st.columns(min(len(samples), 3))
            selected_sample = None
            for i, name in enumerate(samples):
                label = name.replace("pcb_", "").replace("defect_", "").replace("golden", "✅金板").replace(".jpg", "").replace(".png", "")
                if sample_cols[i % 3].button(label, key=f"sample_{i}"):
                    selected_sample = name
        else:
            st.info("示例图片目录为空。请将 PCB 图片放入 `data/sample_images/`")
            selected_sample = None

        st.divider()

        # 检测参数
        with st.expander("⚙️ 检测参数", expanded=False):
            conf_threshold = st.slider("置信度阈值", 0.0, 1.0, 0.25, 0.05)
            enable_sam = st.checkbox("启用 SAM 精细分割", value=True)

        # 检测按钮
        st.divider()
        detect_btn = st.button("🔍 开始检测", type="primary", use_container_width=True)

    with col_right:
        if detect_btn and (uploaded_file or selected_sample):
            # 读取图像
            if uploaded_file:
                image_bytes = uploaded_file.read()
            elif selected_sample:
                img_path = f"{sample_dir}/{selected_sample}"
                with open(img_path, "rb") as f:
                    image_bytes = f.read()

            image_b64 = base64.b64encode(image_bytes).decode()

            with st.spinner("AI Agent 正在检测中..."):
                t0 = time.time()
                try:
                    resp = requests.post(
                        f"{api_url}/api/inspect",
                        json={
                            "image": image_b64,
                            "conf_threshold": conf_threshold,
                            "enable_sam": enable_sam,
                        },
                        timeout=120,
                    )
                    elapsed = time.time() - t0

                    if resp.status_code == 200:
                        result = resp.json()
                        st.session_state.last_inspection_result = result

                        # 显示标注图
                        st.subheader(f"📷 检测结果 `{elapsed:.1f}s`")
                        if result.get("annotated_image_b64"):
                            anno_bytes = base64.b64decode(result["annotated_image_b64"])
                            st.image(anno_bytes, use_container_width=True)

                        # 判定横幅
                        overall = result.get("summary", {}).get("overall_severity", "INFO")
                        banner_colors = {
                            "INFO": ("✅ PASS — 未检测到严重缺陷", "green"),
                            "WARN": ("⚠️ WARN — 检测到疑似缺陷，建议人工复核", "orange"),
                            "CRITICAL": ("🔴 FAIL — 检测到严重缺陷，需立即处理", "red"),
                        }
                        banner_text, banner_color = banner_colors.get(overall, banner_colors["INFO"])
                        st.markdown(f":{banner_color}[{banner_text}]")

                        # 汇总统计
                        summary = result.get("summary", {})
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("缺陷候选", summary.get("total", 0))
                        m2.metric("已确认", summary.get("confirmed", 0))
                        m3.metric("疑似", summary.get("suspicious", 0))
                        m4.metric("严重", summary.get("critical", 0))

                        # 缺陷明细表
                        defects = result.get("defects", [])
                        if defects:
                            st.subheader("📋 缺陷明细")
                            import pandas as pd
                            df = pd.DataFrame([{
                                "类型": d.get("class_name", "?"),
                                "置信度": f"{d.get('confidence', 0):.2f}",
                                "严重度": d.get("severity", "INFO"),
                                "判定": d.get("verdict", "?"),
                                "SAM": "✅" if d.get("has_mask") else "❌",
                            } for d in defects])
                            st.dataframe(df, use_container_width=True, hide_index=True)

                    else:
                        st.error(f"检测失败 ({resp.status_code}): {resp.text[:200]}")

                except requests.exceptions.ConnectionError:
                    st.error(f"无法连接后端 API ({api_url})。请先启动 FastAPI: `python -m backend.main`")
                except Exception as e:
                    st.error(f"检测出错: {e}")

        elif not detect_btn:
            # 初始状态 — 显示提示
            st.info("👈 上传 PCB 图片或选择示例，然后点击 **开始检测**")
