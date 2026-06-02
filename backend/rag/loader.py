"""
RAG 知识库文档加载器

支持 Markdown 和 JSON 格式的文档加载，
返回统一格式的文档字典列表。
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
from backend.config import DATA_DIR, CHUNK_SIZE, CHUNK_OVERLAP


def load_all_documents(knowledge_dir: Optional[str] = None) -> List[Dict]:
    """
    加载知识库目录下所有文档。

    Returns:
        [{source, section, defect_type, content, metadata}, ...]
    """
    if knowledge_dir is None:
        knowledge_dir = str(DATA_DIR / "knowledge")

    docs = []
    kd = Path(knowledge_dir)

    if not kd.exists():
        print(f"[RAG] Knowledge directory not found: {knowledge_dir}")
        return docs

    for file_path in kd.glob("*.md"):
        docs.extend(_load_markdown(file_path))

    for file_path in kd.glob("*.json"):
        docs.extend(_load_json_cases(file_path))

    print(f"[RAG] Loaded {len(docs)} documents from {knowledge_dir}")
    return docs


def _load_markdown(file_path: Path) -> List[Dict]:
    """加载 Markdown 文档，按 ## 标题分段"""
    source = file_path.stem
    content = file_path.read_text(encoding="utf-8")

    docs = []
    # 按二级标题分段
    sections = content.split("\n## ")
    for section in sections:
        if not section.strip():
            continue
        # 提取 section 标题
        lines = section.split("\n", 1)
        title = lines[0].strip().lstrip("#").strip()
        body = lines[1] if len(lines) > 1 else ""

        docs.append({
            "source": source,
            "section": title,
            "defect_type": _extract_defect_type(title, body),
            "content": section.strip(),
            "metadata": {
                "file": file_path.name,
                "section": title,
            }
        })
    return docs


def _load_json_cases(file_path: Path) -> List[Dict]:
    """加载 JSON 格式的缺陷案例库"""
    source = file_path.stem
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"[RAG] Failed to parse {file_path}: {e}")
        return []

    if not isinstance(data, list):
        return []

    docs = []
    for case in data:
        case_id = case.get("case_id", "unknown")
        defect_type = case.get("defect_type", "")
        content_parts = [
            f"案例编号: {case_id}",
            f"缺陷类型: {defect_type}",
            f"严重度: {case.get('severity', '')}",
            f"根因: {case.get('root_cause', '')}",
            f"处置措施: {case.get('corrective_action', '')}",
            f"图像特征: {', '.join(case.get('image_features', []))}",
            f"影响批次: {case.get('affected_batch', '')}",
            f"预防措施: {case.get('preventive_measure', '')}",
        ]

        docs.append({
            "source": source,
            "section": case_id,
            "defect_type": defect_type,
            "content": "\n".join(content_parts),
            "metadata": {
                "file": file_path.name,
                "case_id": case_id,
                "defect_type": defect_type,
                "severity": case.get("severity", ""),
            }
        })
    return docs


def _extract_defect_type(title: str, body: str) -> str:
    """尝试从标题和正文中提取缺陷类型关键词"""
    keywords = [
        "bridge", "桥接", "open", "开路", "offset", "偏移",
        "solder", "焊点", "锡膏", "scratch", "划伤", "划痕",
        "missing", "缺件", "wrong", "错件", "BGA", "void", "空洞",
    ]
    text = (title + " " + body[:200]).lower()
    for kw in keywords:
        if kw.lower() in text:
            return kw
    return ""


def chunk_documents(
    docs: List[Dict],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> List[Dict]:
    """
    使用 langchain 的 RecursiveCharacterTextSplitter 进行文档分块。

    Args:
        docs: load_all_documents 的输出
        chunk_size: 每块最大字符数
        chunk_overlap: 块间重叠字符数

    Returns:
        分块后的文档列表，每个元素包含 content, metadata
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n## ", "\n### ", "\n", "。", ".", " "],
    )

    chunks = []
    for doc in docs:
        doc_chunks = splitter.split_text(doc["content"])
        for i, chunk_text in enumerate(doc_chunks):
            chunks.append({
                "content": chunk_text,
                "metadata": {
                    **doc["metadata"],
                    "source": doc["source"],
                    "section": doc.get("section", ""),
                    "defect_type": doc.get("defect_type", ""),
                    "chunk_index": i,
                }
            })

    print(f"[RAG] Chunked {len(docs)} docs into {len(chunks)} chunks")
    return chunks
