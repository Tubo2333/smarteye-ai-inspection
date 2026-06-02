# SmartEye — 汽车电子产线 AI 质检多 Agent 系统

🏭 **AI 驱动的 PCB 视觉质检多 Agent 系统**

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-green.svg)](https://langchain.com)
[![Claude](https://img.shields.io/badge/LLM-Claude%20Sonnet-orange.svg)](https://anthropic.com)
[![YOLOv8](https://img.shields.io/badge/CV-YOLOv8-red.svg)](https://ultralytics.com)

## 项目简介

SmartEye 是一个面向汽车电子制造场景的 AI 质检多 Agent 系统。它模拟了一条 SMT 产线末端的 AOI 工序：
- 上传 PCB 图片 → AI Agent 自动检测缺陷
- YOLOv8 + OpenCV + SAM 2.1 三引擎视觉检测
- LangGraph Supervisor 模式多 Agent 协作
- ChromaDB RAG 知识库（IPC 标准 + SOP + 历史案例）
- 自动生成中文质检报告 + 异常告警
- Streamlit + FastAPI 前后端分离架构

## 系统架构

```
Streamlit (前端) → FastAPI (API) → LangGraph (编排)
                                     ├── InspectionAgent → YOLO + OpenCV + SAM
                                     ├── AnalysisAgent  → Pandas + Stats
                                     ├── ReportAgent    → RAG + Jinja2
                                     └── AlertAgent     → Rule Engine
```

## 快速启动

### 1. 环境准备

```bash
cd smarteye
python -m venv venv
source venv/Scripts/activate  # Windows
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入 ANTHROPIC_API_KEY
```

### 3. 构建 RAG 知识库

```bash
python -c "from backend.rag.vector_store import build_knowledge_base; build_knowledge_base()"
```

### 4. 一键启动

```bash
bash scripts/run_demo.sh
```

或者分别启动：

```bash
# 终端 1: 后端
python -m backend.main

# 终端 2: 前端
streamlit run frontend/app.py
```

- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **前端 UI**: http://localhost:8501

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| LLM | Claude API (Sonnet) | Agent 决策 + 报告生成 |
| Agent 框架 | LangGraph | Supervisor 模式多 Agent 编排 |
| 后端 | FastAPI | REST API + OpenAPI 文档 |
| 前端 | Streamlit | 纯 Python Web UI |
| 目标检测 | YOLOv8n | 3.2M 参数，RTX 4060 30分钟训练 |
| 图像分割 | SAM 2.1 → SAM 1 → MobileSAM | 三级 fallback |
| 传统视觉 | OpenCV | 5 个规则器：焊点/偏移/划痕/颜色/OCR |
| 向量数据库 | ChromaDB | 本地持久化，零部署 |
| 文档导出 | python-docx + Playwright | DOCX + PDF |
| 测试 | Pytest | 三层金字塔 |

## 项目结构

```
smarteye/
├── backend/
│   ├── api/          # FastAPI 路由 + Schemas
│   ├── orchestrator/ # LangGraph StateGraph + Agent 节点
│   ├── cv/           # YOLO + OpenCV + SAM + Fusion
│   ├── rag/          # ChromaDB 检索 pipeline
│   ├── models/       # 训练好的模型权重
│   └── prompts/      # Agent System Prompts (Markdown)
├── frontend/
│   └── views/        # 4 个 Streamlit 页面
├── data/
│   ├── knowledge/    # RAG 知识库文档
│   ├── sample_images/# Demo 用 PCB 图片
│   └── pcb_dataset/  # PCB 缺陷训练数据
├── tests/            # Pytest 测试
├── scripts/          # 辅助脚本
└── docs/             # 文档
```

## 五个 Agent

所有 Agent 逻辑实现在 `backend/orchestrator/graph.py` 中，通过 LangGraph StateGraph 编排。

| Agent 节点 | 职责 |
|-----------|------|
| 🎯 supervisor_node | 总调度，基于当前状态动态路由到合适的 Worker |
| 🔍 inspection_node | 视觉缺陷检测：调用 YOLO + OpenCV + SAM 三引擎 |
| 📊 analysis_node | 统计分析：缺陷率计算、趋势判断、系统性异常识别 |
| 📝 report_node | 报告生成 + 知识库问答：Markdown 报告 / RAG 对话回复 |
| 🚨 alert_node | 异常告警：三级严重度评定 + 处置建议 |

## 最近更新

- **桌面版**：基于 pywebview + Edge WebView2 的独立窗口启动，无需浏览器
- **会话历史系统**：检测记录最多保存 10 条，跨质量检测/Agent对话/仪表盘/报告四页面联动
- **Agent 对话增强**：按检测会话隔离对话历史、快捷提问按钮、RAG 知识库同步检索
- **仪表盘三数据源**：检测会话 / 后端 API 实时数据 / 演示数据，一键切换
- **全局 UI 优化**：统一字号梯度、8px 间距系统、深色模式适配、侧边栏精简
- **后端修复**：API 参数传递修正、bbox 不可变绘制、ChromaDB embedding 单例、端口自动清理
- **便携打包**：`python scripts/build_portable.py` 生成免安装独立文件夹

## License

MIT — 本项目的 IPC 标准和 SOP 文档为基于公开材料的模拟内容，不包含任何真实工厂的机密信息。
