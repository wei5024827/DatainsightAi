import logging

from fastapi import APIRouter, HTTPException

from app.core.llm_client import generate_sql_from_llm
from app.core.schema_index import (
    format_tables_for_prompt,
    get_relevant_tables,
    init_schema_index,
)
from app.models.nl_request import NLRequest
from app.utils.sql_parser import extract_sql

router = APIRouter(prefix="/nl2sql", tags=["LLM"])
logger = logging.getLogger(__name__)


try:
    init_schema_index()
except Exception as exc:
    logger.warning("初始化 schema 索引失败（后续按需初始化）：%s", exc)


def _build_prompt(schema_text: str, user_question: str) -> str:
    return f"""
请根据用户的自然语言问题生成 SQL 查询。
请严格遵守以下要求：
1. 你只能使用下面给出的数据库表结构（Schema）中的表和字段，不要臆造不存在的表或字段。
2. 只生成 SQL 语句本身，不要返回多余的解释、说明或 Markdown 标记。
3. 只允许 SELECT / WITH 查询。
4. 如果根据提供的表结构无法满足用户需求，你可以尽量给出最接近的查询，但不要捏造字段。

注意只能使用下面给出的数据库表结构：
{schema_text}

用户问题：{user_question}

请根据上述表结构和用户问题，生成一条合法、可执行的 SQL 查询语句：
"""


@router.post("/")
async def nl2sql_handler(req: NLRequest):
    """自然语言 → RAG 检索 schema → LLM 生成 SQL。"""
    user_question = req.text.strip() if req.text else ""
    if not user_question:
        raise HTTPException(status_code=400, detail="text 字段不能为空")

    logger.info("收到 NL2SQL 请求：%s", user_question)

    try:
        relevant_tables = get_relevant_tables(user_question, top_k=10)
        schema_text = format_tables_for_prompt(relevant_tables)
    except Exception as exc:
        logger.error("RAG schema 检索失败：%s", exc)
        schema_text = "（RAG schema 检索失败，本次未提供表结构，请尽量按照常见 SQL 规范生成查询。）"

    try:
        llm_output = generate_sql_from_llm(_build_prompt(schema_text, user_question))
    except Exception as exc:
        logger.error("LLM 调用失败: %s", exc)
        raise HTTPException(status_code=502, detail="LLM 服务调用失败")

    sql = extract_sql(llm_output)
    if not sql:
        raise HTTPException(status_code=500, detail="未能从模型输出中解析出 SQL")

    return {
        "sql": sql,
        "raw_output": llm_output,
        "used_schema": schema_text,
    }
