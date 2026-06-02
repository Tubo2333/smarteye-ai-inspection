#!/bin/bash
set -e

echo "╔══════════════════════════════════════════════════╗"
echo "║          SmartEye — AI 视觉质检系统               ║"
echo "║          Docker 容器已启动                        ║"
echo "╚══════════════════════════════════════════════════╝"

# 确保知识库已构建
echo "[INFO] 检查知识库..."
python -c "
from backend.rag.vector_store import get_knowledge_stats, build_knowledge_base
stats = get_knowledge_stats()
if stats.get('total_chunks', 0) == 0:
    print('[INFO] 构建知识库...')
    build_knowledge_base()
else:
    print(f'[OK] 知识库就绪: {stats[\"total_chunks\"]} 条索引')
" || echo "[WARN] 知识库跳过"

# 启动后端
echo "[INFO] 启动后端 (FastAPI) ..."
python -c "import uvicorn; uvicorn.run('backend.main:app', host='0.0.0.0', port=8000)" &
BACKEND_PID=$!

# 等待后端就绪
echo "[INFO] 等待后端就绪..."
for i in $(seq 1 30); do
    sleep 1
    curl -s http://localhost:8000/health > /dev/null 2>&1 && break
done
echo "[OK] 后端就绪"

# 启动前端
echo "[INFO] 启动前端 (Streamlit) ..."
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0 \
    --server.headless true --browser.gatherUsageStats false &
FRONTEND_PID=$!

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  前端界面:  http://localhost:8501                 ║"
echo "║  API 文档:  http://localhost:8000/docs            ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# 等待任意进程退出
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGTERM SIGINT
wait
