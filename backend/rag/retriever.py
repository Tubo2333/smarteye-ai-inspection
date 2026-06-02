"""
RAG 检索 Pipeline — 检索 → 去重 → Rerank → Top K
"""
from typing import List, Dict, Optional
from backend.rag.vector_store import get_collection
from backend.config import RAG_TOP_K_RETRIEVAL, RAG_TOP_K_FINAL


async def search_knowledge_base(
    query: str,
    defect_type: Optional[str] = None,
    doc_source: Optional[str] = None,
    top_k: int = RAG_TOP_K_FINAL,
) -> List[Dict]:
    """
    检索知识库。

    Args:
        query: 自然语言查询
        defect_type: 按缺陷类型过滤（可选）
        doc_source: 按文档来源过滤（可选）
        top_k: 最终返回数量

    Returns:
        [{content, metadata, relevance_score}, ...]
    """
    collection = get_collection()

    if collection.count() == 0:
        print("[RAG] Knowledge base is empty. Run build_knowledge_base() first.")
        return []

    # 构建过滤条件
    where_filter = {}
    if doc_source:
        where_filter["source"] = doc_source
    if defect_type:
        where_filter["defect_type"] = defect_type

    # 初检: 取 top_k * 2 用于 rerank
    try:
        results = collection.query(
            query_texts=[query],
            n_results=RAG_TOP_K_RETRIEVAL,
            where=where_filter if where_filter else None,
        )
    except Exception as e:
        print(f"[RAG] Query failed: {e}")
        return []

    if not results["documents"] or not results["documents"][0]:
        return []

    # 按 source 去重（同一文档最多保留 2 个 chunk，防止一篇文档霸占结果）
    seen_sources: Dict[str, int] = {}
    deduped = []

    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        src = meta.get("source", "unknown") if meta else "unknown"
        if seen_sources.get(src, 0) < 2:
            deduped.append({
                "content": doc,
                "metadata": meta or {},
                "distance": dist,
            })
            seen_sources[src] = seen_sources.get(src, 0) + 1

    # 按原始距离排序
    deduped.sort(key=lambda x: x["distance"])

    # 构建最终结果
    final = []
    for item in deduped[:top_k]:
        final.append({
            "content": item["content"],
            "metadata": item["metadata"],
            "relevance_score": round(1.0 / (1.0 + item["distance"]), 4),  # 转为相关性分数
        })

    return final
