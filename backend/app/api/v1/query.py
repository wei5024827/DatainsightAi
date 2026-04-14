import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.query_executor import run_sql


class QueryRequest(BaseModel):
    sql: str


router = APIRouter(prefix="/query", tags=["Query"])
logger = logging.getLogger(__name__)


@router.post("/")
async def run_query(req: QueryRequest):
    """接收 SQL，执行并返回结果。"""
    sql = req.sql.strip() if req.sql else ""
    if not sql:
        raise HTTPException(status_code=400, detail="SQL 不能为空")

    logger.info("收到 Query SQL：%s", sql)
    try:
        return await run_sql(sql)
    except Exception as exc:
        logger.error("SQL 执行失败：%s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
