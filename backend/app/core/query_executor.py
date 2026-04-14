import logging
import os
import time
from typing import Dict, List

import duckdb

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "app/example.duckdb")


def get_db_connection(max_retries: int = 3, retry_delay: int = 1) -> duckdb.DuckDBPyConnection:
    """获取 DuckDB 连接，失败时进行有限重试。"""
    last_error = None
    for attempt in range(max_retries):
        try:
            return duckdb.connect(DB_PATH, read_only=True)
        except Exception as exc:
            last_error = exc
            logger.warning("第 %d 次连接失败：%s", attempt + 1, exc)
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    logger.error("连接数据库失败，已达到最大重试次数：%s", last_error)
    raise last_error


async def run_sql(sql: str) -> List[Dict]:
    """
    执行 SQL 并返回查询结果（list[dict] 格式，前端最容易解析）。
    """
    normalized_sql = sql.strip() if sql else ""
    if not normalized_sql:
        raise ValueError("SQL 不能为空。")

    logger.info("开始执行 SQL：%s", normalized_sql)
    try:
        with get_db_connection() as conn:
            result = conn.execute(normalized_sql)
            rows = result.fetchall()
            columns = [col[0] for col in result.description]
        data = [dict(zip(columns, row)) for row in rows]
        logger.info("SQL 执行成功，共返回 %d 行。", len(data))
        return data
    except Exception as exc:
        logger.error("执行 SQL 失败：%s", exc)
        raise
