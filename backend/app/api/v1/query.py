# -----------------------------
# 导入依赖
# -----------------------------
from fastapi import APIRouter, HTTPException
# APIRouter：创建路由
# HTTPException：返回标准化 API 错误

import logging
# 打日志用

from app.core.query_executor import run_sql
# ⭐ 这是关键：所有 SQL 执行逻辑在 query_executor.py 中
# query.py 只负责调用这个函数

# -----------------------------
# 创建 /query 路由
# SQL执行接口 (POST /query)
# 功能：执行SQL查询并返回结果
# 请求方式：POST
# 请求体：{"sql": "SELECT * FROM users"}
# -----------------------------
router = APIRouter(
    prefix="/query",
    tags=["Query"]
)

# -----------------------------
# 接口：执行 SQL 查询
# -----------------------------
@router.post("/")
async def run_query(sql: str):
    """
    接收 SQL → 调用 query_executor 执行 → 返回结果
    """

    logging.info(f"收到 Query SQL：{sql}")

    # -----------------------------
    # 1. 输入校验
    # -----------------------------
    if not sql or sql.strip() == "":
        raise HTTPException(status_code=400, detail="SQL 不能为空")

    # -----------------------------
    # 2. 调用 query_executor 执行 SQL
    # -----------------------------
    try:
        result = await run_sql(sql)
        # ⭐ 这里 result 是 query_executor 返回的 dict，例如：
        # {
        #   "columns": [...],
        #   "rows": [...]
        # }

    except Exception as e:
        logging.error(f"SQL 执行失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))

    # -----------------------------
    # 3. 返回标准响应
    # -----------------------------
    return result
