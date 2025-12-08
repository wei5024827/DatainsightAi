# -----------------------------
# 导入依赖
# -----------------------------
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# 添加BaseModel导入

import logging
from app.core.query_executor import run_sql


# -----------------------------
# 创建请求模型
# -----------------------------
class QueryRequest(BaseModel):
    sql: str


router = APIRouter(prefix="/query", tags=["Query"])


# -----------------------------
# 接口：执行 SQL 查询
# -----------------------------
@router.post("/")
async def run_query(req: QueryRequest):  # 修改参数类型
    """
    接收 SQL → 调用 query_executor 执行 → 返回结果
    """

    logging.info(f"收到 Query SQL：{req.sql}")  # 修改为req.sql

    # -----------------------------
    # 1. 输入校验
    # -----------------------------
    if not req.sql or req.sql.strip() == "":  # 修改为req.sql
        raise HTTPException(status_code=400, detail="SQL 不能为空")

    # -----------------------------
    # 2. 调用 query_executor 执行 SQL
    # -----------------------------
    try:
        # await 等待异步操作完成
        result = await run_sql(req.sql)  # 修改为req.sql

    except Exception as e:
        logging.error(f"SQL 执行失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))

    # -----------------------------
    # 3. 返回标准响应
    # -----------------------------
    return result
