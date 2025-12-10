# app/api/v1/rag.py
## DEBUG RAG 检索相关接口
from fastapi import APIRouter, Query
from typing import List, Dict, Any

from app.core.schema_index import (
    init_schema_index,
    get_relevant_tables,
    format_tables_for_prompt,
    get_full_schema,
   # _load_schema_from_duckdb,   # 直接复用 schema 读取函数
)

router = APIRouter(
    prefix="/rag",
    tags=["RAG Schema Debug"]
)


@router.get("/tables")
def get_all_tables():
    """
    返回数据库所有表结构。
    用来确认 DuckDB schema 是否正确加载。
    """
    tables = get_full_schema()
    return {
        "tables": tables,
        "total": len(tables),
    }


@router.get("/search")
def rag_search(query: str = Query(..., description="自然语言查询，例如：'查询用户订单金额'"),
               top_k: int = 5):
    """
    基于自然语言做 RAG 检索，返回最相关的表结构与格式化文本。
    """
    # 初始化 RAG（如果未初始化）
    init_schema_index()

    tables = get_relevant_tables(query, top_k=top_k)
    formatted = format_tables_for_prompt(tables)

    return {
        "query": query,
        "matched_tables": [
            {
                "table_name": t["table_name"],
                "score": t["score"],
                "columns": t["columns"],
            }
            for t in tables
        ],
        "formatted_schema": formatted
    }
