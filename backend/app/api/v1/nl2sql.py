import logging

from fastapi import APIRouter, HTTPException

from app.core.nl2sql_workflow import run_nl2sql_workflow
from app.core.schema_index import init_schema_index
from app.models.nl_request import NLRequest

router = APIRouter(prefix="/nl2sql", tags=["LLM"])
logger = logging.getLogger(__name__)


try:
    init_schema_index()
except Exception as exc:
    logger.warning("初始化 schema 索引失败（后续按需初始化）：%s", exc)


@router.post("/")
async def nl2sql_handler(req: NLRequest):
    """自然语言 → RAG 检索 schema → LLM 生成 SQL。"""
    user_question = req.text.strip() if req.text else ""
    if not user_question:
        raise HTTPException(status_code=400, detail="text 字段不能为空")

    logger.info("收到 NL2SQL 请求：%s", user_question)

    try:
        result = run_nl2sql_workflow(user_question)
    except Exception as exc:
        logger.error("NL2SQL 工作流失败：%s", exc)
        raise HTTPException(status_code=502, detail="NL2SQL 工作流执行失败")

    if not result.get("sql"):
        raise HTTPException(status_code=500, detail="未能从模型输出中解析出 SQL")

    return result
