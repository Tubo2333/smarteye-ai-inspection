"""
GET /api/knowledge/search — 知识库检索
GET /api/knowledge/stats — 知识库统计
"""
import time
from fastapi import APIRouter, Query
from backend.api.schemas import KnowledgeSearchResult, KnowledgeSearchResponse, KnowledgeStatsResponse
from backend.rag.retriever import search_knowledge_base
from backend.rag.vector_store import get_knowledge_stats

router = APIRouter()


@router.get("/knowledge/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    q: str = Query(..., description="查询文本"),
    defect_type: str = Query(default=None, description="缺陷类型筛选"),
    source: str = Query(default=None, description="文档来源筛选"),
    limit: int = Query(default=4, ge=1, le=10, description="返回数量"),
):
    """
    搜索工厂知识库。
    支持 IPC 质量标准、SOP、历史缺陷案例、设备参数四类文档。
    """
    t_start = time.time()

    results = await search_knowledge_base(
        query=q,
        defect_type=defect_type,
        doc_source=source,
        top_k=limit,
    )

    search_time_ms = (time.time() - t_start) * 1000

    return KnowledgeSearchResponse(
        results=[KnowledgeSearchResult(**r) for r in results],
        search_time_ms=search_time_ms,
        total_chunks=len(results),
    )


@router.get("/knowledge/stats", response_model=KnowledgeStatsResponse)
async def knowledge_stats():
    """返回知识库统计信息"""
    stats = get_knowledge_stats()
    return KnowledgeStatsResponse(
        total_chunks=stats.get("total_chunks", 0),
        collection_name=stats.get("collection_name", "smarteye_knowledge"),
    )
