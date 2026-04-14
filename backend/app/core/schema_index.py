# app/core/schema_index.py

"""
RAG 检索模块（使用 text2vec + FAISS）
"""

import logging
import re
from typing import Any, Dict, List

import faiss
from text2vec import SentenceModel

from app.api.v1.schema import get_full_schema

logger = logging.getLogger(__name__)

_faiss_index = None
_id_to_table_meta: List[Dict[str, Any]] = []
_embedding_model: SentenceModel = None


def _get_embedding_model() -> SentenceModel:
    global _embedding_model
    if _embedding_model is None:
        logger.info("正在加载 text2vec 本地 Embedding 模型 ...")
        _embedding_model = SentenceModel("BAAI/bge-large-zh")
        logger.info("Embedding 模型加载完成。")
    return _embedding_model


def _parse_table_key(raw_name: str) -> Dict[str, str]:
    """
    兼容 schema 接口中 `table_name:xxx;comment:yyy` 的历史格式。
    """
    match = re.match(r"table_name:(.*?);comment:(.*)", raw_name)
    if match:
        return {"table_name": match.group(1), "comment": match.group(2)}
    return {"table_name": raw_name, "comment": ""}


def _normalize_full_schema(full_schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    tables: List[Dict[str, Any]] = []
    for raw_name, value in full_schema.items():
        parsed = _parse_table_key(raw_name)
        if isinstance(value, dict):
            columns = value.get("columns", [])
            comment = value.get("comment") or parsed["comment"]
        else:
            columns = value
            comment = parsed["comment"]

        tables.append(
            {
                "table_name": parsed["table_name"],
                "comment": comment or "",
                "columns": columns or [],
            }
        )
    return tables


def _table_meta_to_text(table_meta: Dict[str, Any]) -> str:
    table = table_meta["table_name"]
    table_comment = table_meta.get("comment", "")

    parts = []
    for col in table_meta["columns"]:
        name = col.get("name")
        col_type = col.get("type")
        comment = col.get("comment", "")
        if comment:
            parts.append(f"{name} {col_type} ({comment})")
        else:
            parts.append(f"{name} {col_type}")

    columns_text = ", ".join(parts)
    return f"表 {table} ({table_comment}): {columns_text}"


def init_schema_index() -> None:
    global _faiss_index, _id_to_table_meta

    if _faiss_index is not None:
        return

    logger.info("[RAG] 开始初始化 schema 索引 ...")
    full_schema = get_full_schema()
    tables = _normalize_full_schema(full_schema)

    if not tables:
        logger.warning("[RAG] 没有数据表。")
        return

    texts = [_table_meta_to_text(t) for t in tables]
    model = _get_embedding_model()
    embeddings = model.encode(texts)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # 内积 = cosine 相似度（向量已归一化）
    index.add(embeddings)

    _faiss_index = index
    _id_to_table_meta = tables
    logger.info("[RAG] schema 索引初始化完成，共 %d 张表。", len(_id_to_table_meta))


def get_relevant_tables(query: str, top_k: int = 10):
    """基于用户问题做 RAG 检索。"""
    if not query.strip():
        return []

    if _faiss_index is None:
        init_schema_index()
    if _faiss_index is None:
        return []

    model = _get_embedding_model()
    q = model.encode([query])
    scores, indices = _faiss_index.search(q, top_k)

    results = []
    for idx, score in zip(indices[0], scores[0]):
        if idx == -1:
            continue
        table_meta = _id_to_table_meta[idx]
        results.append({**table_meta, "score": float(score)})

    logger.info("[RAG] query='%s' → 表: %s", query, [r["table_name"] for r in results])
    return results


def format_tables_for_prompt(tables: List[Dict[str, Any]]) -> str:
    """格式化 schema，用于 prompt。"""
    if not tables:
        return "（未检索到相关表结构，请尽量根据常规 SQL 规范生成查询。）"

    lines = []
    for table in tables:
        title = f"表 {table['table_name']}"
        if table.get("comment"):
            title += f"（{table['comment']}）"
        lines.append(f"{title}:")

        for col in table["columns"]:
            name = col.get("name")
            col_type = col.get("type")
            text = f"  - {name} {col_type}"
            if col.get("pk"):
                text += " (PRIMARY KEY)"
            lines.append(text)
        lines.append("")

    return "\n".join(lines)
