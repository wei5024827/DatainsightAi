# app/core/schema_index.py

"""
基于 DuckDB schema 的 RAG 检索模块（使用 text2vec + FAISS）

功能：
- 启动时从 DuckDB 读取所有表结构
- 使用 text2vec 的 SentenceModel 将每张表的 schema 向量化
- 使用 FAISS 建立向量索引
- 对于用户的自然语言问题，检索出 Top-K 相关表
- 格式化输出 schema 供 NL2SQL prompt 使用
"""

import logging
from typing import List, Dict, Any
import faiss
from text2vec import SentenceModel
from app.api.v1.schema import get_full_schema

logger = logging.getLogger(__name__)

# -----------------------------
# 1. 全局对象
# -----------------------------
_faiss_index = None
_id_to_table_meta: List[Dict[str, Any]] = []
_embedding_model: SentenceModel = None



# -----------------------------
# 2. 加载 text2vec 模型
# -----------------------------
def _get_embedding_model() -> SentenceModel:
    global _embedding_model
    if _embedding_model is None:
        logger.info("正在加载 text2vec 本地 Embedding 模型 ...")
        _embedding_model = SentenceModel("BAAI/bge-large-zh")

       # _embedding_model = SentenceModel("shibing624/text2vec-base-chinese")

       # _embedding_model = SentenceModel("sentence-transformers/paraphrase-MiniLM-L6-v2")
        logger.info("Embedding 模型加载完成。")
    return _embedding_model




# -----------------------------
# 4. schema → 文本
# -----------------------------
def _table_meta_to_text(table_meta: Dict[str, Any]) -> str:
    table = table_meta["table_name"]
    table_comment = table_meta.get("comment", "")

    cols = table_meta["columns"]

    parts = []
    for col in cols:
        name = col.get("name")
        t = col.get("type")
        comment = col.get("comment", "")
        if comment:
            parts.append(f"{name} {t} ({comment})")
        else:
            parts.append(f"{name} {t}")

    columns_text = ", ".join(parts)

    return f"表 {table} ({table_comment}): {columns_text}"


# -----------------------------
# 5. 初始化 FAISS 索引
# -----------------------------
def init_schema_index() -> None:
    global _faiss_index, _id_to_table_meta

    if _faiss_index is not None:
        return

    logger.info("[RAG] 开始初始化 schema 索引 ...")
    full_schema = get_full_schema()

    tables =  [
    {
        "table_name": table,
        "columns": full_schema[table]
    }
    for table in full_schema
]
    if not tables:
        logger.warning("[RAG] 没有数据表。")
        return

    texts = [_table_meta_to_text(t) for t in tables]

    model = _get_embedding_model()
    embeddings = model.encode(texts)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # 内积 = cosine 相似度（text2vec 已归一化）

    index.add(embeddings)

    _faiss_index = index
    _id_to_table_meta = tables

    logger.info(f"[RAG] schema 索引初始化完成，共 {len(_id_to_table_meta)} 张表。")


# -----------------------------
# 6. 基于用户问题做 RAG 检索
# -----------------------------
def get_relevant_tables(query: str, top_k: int = 5):
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

        results.append({
            **table_meta,
            "score": float(score)
        })

    logger.info(f"[RAG] query='{query}' → 表: {[r['table_name'] for r in results]}")
    return results


# -----------------------------
# 7. 格式化 schema，用于 prompt
# -----------------------------
def format_tables_for_prompt(tables: List[Dict[str, Any]]) -> str:
    if not tables:
        return "（未检索到相关表结构，请尽量根据常规 SQL 规范生成查询。）"

    lines = []

    for table in tables:
        lines.append(f"表 {table['table_name']}:")
        for col in table["columns"]:
            name = col.get("name")
            t = col.get("type")
            pk = col.get("pk")
            text = f"  - {name} {t}"
            if pk:
                text += " (PRIMARY KEY)"
            lines.append(text)
        lines.append("")

    return "\n".join(lines)
