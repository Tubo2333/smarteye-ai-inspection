#!/bin/bash
# SmartEye 一键启动脚本
# 启动 FastAPI 后端 + Streamlit 前端

set -e
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "=========================================="
echo "  SmartEye — AI 质检多 Agent 系统"
echo "  汽车电子 AI 质检"
echo "=========================================="
echo ""

# 激活虚拟环境
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
    echo "[OK] Virtual environment activated"
else
    echo "[ERROR] venv not found. Please run: python -m venv venv"
    exit 1
fi

# 构建 RAG 知识库（如果还没构建）
echo ""
echo "[INFO] Checking RAG knowledge base..."
python -c "
from backend.rag.vector_store import get_collection
try:
    c = get_collection()
    if c.count() == 0:
        print('[INFO] Knowledge base empty, building...')
        from backend.rag.vector_store import build_knowledge_base
        build_knowledge_base()
    else:
        print(f'[OK] Knowledge base ready: {c.count()} chunks')
except Exception as e:
    print(f'[WARN] Knowledge base check failed: {e}')
"

# 启动 FastAPI
echo ""
echo "[INFO] Starting FastAPI backend on port 8000..."
python -m backend.main &
BACKEND_PID=$!
echo "[OK] Backend PID: $BACKEND_PID"

# 等待后端就绪
sleep 2

# 启动 Streamlit
echo ""
echo "[INFO] Starting Streamlit frontend on port 8501..."
streamlit run frontend/app.py --server.port 8501 &
FRONTEND_PID=$!
echo "[OK] Frontend PID: $FRONTEND_PID"

echo ""
echo "=========================================="
echo "  SmartEye is running!"
echo ""
echo "  Backend:  http://localhost:8000"
echo "  Swagger:  http://localhost:8000/docs"
echo "  Frontend: http://localhost:8501"
echo ""
echo "  Press Ctrl+C to stop"
echo "=========================================="

# 捕获退出信号
cleanup() {
    echo ""
    echo "[INFO] Shutting down..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "[OK] Done"
}
trap cleanup EXIT INT TERM

wait
