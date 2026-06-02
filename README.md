# SmartEye — 汽车电子产线 AI 质检多 Agent 系统

🏭 **对标博世苏州汽车电子工厂 AI Agent 质检平台**

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
│   ├── orchestrator/ # LangGraph StateGraph
│   ├── agents/       # 5 个 Agent 实现
│   ├── tools/        # 16 个 Tool (@tool 装饰器)
│   ├── cv/           # YOLO + OpenCV + SAM + Fusion
│   ├── rag/          # ChromaDB 检索 pipeline
│   ├── models/       # 训练好的模型权重
│   └── prompts/      # Agent System Prompts (Markdown)
├── frontend/
│   ├── pages/        # 4 个 Streamlit 页面
│   └── components/   # 可复用 UI 组件
├── data/
│   ├── knowledge/    # RAG 知识库文档
│   ├── sample_images/# Demo 用 PCB 图片
│   └── pcb_dataset/  # PCB 缺陷训练数据
├── tests/            # Pytest 测试
├── notebooks/        # Jupyter 开发笔记
├── scripts/          # 辅助脚本
└── docs/             # 文档
```

## 五个 Agent

| Agent | 职责 | 核心 Tool |
|-------|------|-----------|
| 🎯 SupervisorAgent | 总调度，动态路由 | — |
| 🔍 InspectionAgent | 视觉缺陷检测 | detect_defects, measure_component, segment_region, ocr |
| 📊 AnalysisAgent | 统计分析 | defect_rate, trend, pareto, severity |
| 📝 ReportAgent | 报告生成 | generate_report_md, render_chart, format_table, export |
| 🚨 AlertAgent | 异常告警 | check_threshold, format_alert, suggest_action, escalate |

## 面试相关

- **设计文档**: [docs/superpowers/specs/2026-06-02-smarteye-design.md](../docs/superpowers/specs/2026-06-02-smarteye-design.md)
- **白话说明文档**: [docs/SmartEye-白话说明文档.docx](docs/SmartEye-白话说明文档.docx)
- **目标岗位**: 博世中国 AI Agent 应用实习生

## License

MIT — 本项目的 IPC 标准和 SOP 文档为基于公开材料的模拟内容，不包含任何真实工厂的机密信息。
