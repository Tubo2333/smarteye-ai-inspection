"""
SmartEye FastAPI 应用入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import CORS_ORIGINS, API_HOST, API_PORT
from backend.api.deps import get_registry, get_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期: 启动时预热模型，关闭时清理 GPU"""
    print("[SmartEye] Starting up...")

    # 预热 LangGraph
    get_graph()
    print("[SmartEye] LangGraph initialized")

    # 预热 YOLO (可选，False 则首次请求时加载)
    # registry = get_registry()
    # registry.get_yolo()
    print("[SmartEye] Ready")

    yield

    # 清理
    print("[SmartEye] Shutting down...")
    registry = get_registry()
    registry.clear()
    print("[SmartEye] Cleanup complete")


app = FastAPI(
    title="SmartEye API",
    description="汽车电子产线 AI 质检多 Agent 系统 — 博世苏州 Style",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — 允许 Streamlit 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS + ["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
from backend.api.routes import inspection, agent_chat, report, knowledge

app.include_router(inspection.router, prefix="/api", tags=["检测 Inspection"])
app.include_router(agent_chat.router, prefix="/api", tags=["对话 Agent Chat"])
app.include_router(report.router, prefix="/api", tags=["报告 Report"])
app.include_router(knowledge.router, prefix="/api", tags=["知识库 Knowledge"])


@app.get("/")
async def root():
    return {
        "service": "SmartEye API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# ═══════════════════════════════════════════════════════════════
# 启动入口
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
    )
