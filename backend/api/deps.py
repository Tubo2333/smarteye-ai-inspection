"""
FastAPI 依赖注入 — 全局共享的资源（Graph、Registry、Collection）
"""
from typing import Optional
from backend.cv.registry import ModelRegistry
from backend.orchestrator.graph import build_graph

# 全局实例（应用启动时初始化）
_graph = None
_registry = None


def get_graph():
    """获取全局 LangGraph 实例"""
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def get_registry() -> ModelRegistry:
    """获取全局 ModelRegistry"""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry
