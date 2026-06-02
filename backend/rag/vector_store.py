"""
ChromaDB 向量存储 — 索引构建与查询

使用 sentence-transformers 作为 embedding 函数（替代 ChromaDB 默认的 ONNX 下载，
后者在 GFW 环境下经常超时）。
"""
import os
from typing import List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.api.types import EmbeddingFunction
from backend.config import CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME
from backend.rag.loader import load_all_documents, chunk_documents


class STEmbeddingFunction(EmbeddingFunction):
    """
    使用 sentence-transformers 的 embedding 函数。
    支持 HF_ENDPOINT 环境变量设置镜像。
    全局单例，避免 ChromaDB 因不同实例而拒绝读取已有 collection。
    """
    _instance = None

    def __new__(cls, model_name: str = "all-MiniLM-L6-v2"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if self._initialized:
            return
        self._initialized = True
        self.model_name = model_name
        self._model = None

    def name(self) -> str:
        return f"st-{self.model_name}"

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def __call__(self, input: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(input, show_progress_bar=False)
        return embeddings.tolist()


def get_chroma_client() -> chromadb.PersistentClient:
    """获取 ChromaDB 客户端"""
    return chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def get_collection() -> chromadb.Collection:
    """获取或创建 knowledge collection"""
    client = get_chroma_client()
    # 先尝试直接获取已有的 collection（不指定 embedding function）
    try:
        collection = client.get_collection(
            name=CHROMA_COLLECTION_NAME,
            embedding_function=STEmbeddingFunction(),
        )
        return collection
    except Exception:
        pass

    # 不存在则创建
    try:
        collection = client.create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"description": "SmartEye 工厂知识库 — IPC/SOP/缺陷案例/设备参数"},
            embedding_function=STEmbeddingFunction(),
        )
    except Exception:
        # 可能已被其他进程创建，再试获取
        collection = client.get_collection(
            name=CHROMA_COLLECTION_NAME,
            embedding_function=STEmbeddingFunction(),
        )
    return collection


def build_knowledge_base(knowledge_dir: Optional[str] = None) -> int:
    """
    首次运行或重建时调用：加载文档 → 分块 → 构建 ChromaDB 索引。

    Returns:
        索引的文档块数量
    """
    print("[RAG] Building knowledge base...")
    docs = load_all_documents(knowledge_dir)
    if not docs:
        print("[RAG] No documents found, skipping index build.")
        return 0

    chunks = chunk_documents(docs)

    # 删除旧 collection 并重建
    client = get_chroma_client()
    try:
        client.delete_collection(CHROMA_COLLECTION_NAME)
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={"description": "SmartEye 工厂知识库"},
        embedding_function=STEmbeddingFunction(),
    )

    # 批量添加
    batch_size = 50
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        collection.add(
            documents=[c["content"] for c in batch],
            metadatas=[c["metadata"] for c in batch],
            ids=[f"{c['metadata']['source']}_{c['metadata'].get('section', '')}_{c['metadata']['chunk_index']}"
                 for c in batch],
        )

    count = collection.count()
    print(f"[RAG] Knowledge base built: {count} chunks indexed.")
    return count


def get_knowledge_stats() -> dict:
    """返回知识库统计信息"""
    try:
        collection = get_collection()
        count = collection.count()
        return {
            "total_chunks": count,
            "collection_name": CHROMA_COLLECTION_NAME,
            "persist_dir": CHROMA_PERSIST_DIR,
        }
    except Exception as e:
        return {"error": str(e)}
