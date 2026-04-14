from fastapi import APIRouter
import logging
import os

import duckdb

logger = logging.getLogger(__name__)


# 功能：返回数据库的完整 Schem
router = APIRouter(
    prefix="/schema", tags=["Schema"]
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DB_PATH = os.path.join(BASE_DIR, "app", "example.duckdb")


def _connect_db() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(DB_PATH, read_only=True)


def get_tables() -> list:
    """
    读取数据库中的所有表名
    """
    with _connect_db() as conn:
        result = conn.execute("SHOW TABLES;")
        tables = [row[0] for row in result.fetchall()]
    logger.info(f"检测到数据表：{tables}")
    return tables


def get_table_schema(table_name: str) -> list[dict]:
    """
    读取表结构信息包括comment
    """
    sql = """
        SELECT column_name AS name, data_type AS type, comment AS comment, column_index AS cid
        FROM duckdb_columns
        WHERE table_name = ?;
    """
    with _connect_db() as conn:
        result = conn.execute(sql, [table_name])
        rows = result.fetchall()
        columns = [col[0] for col in result.description]

    # 将每一行信息转成 dict
    return [dict(zip(columns, row)) for row in rows]


def get_table_comment(table_name: str) -> str:  # 读取表的注释
    sql = "SELECT comment FROM duckdb_tables WHERE table_name = ?;"
    with _connect_db() as conn:
        result = conn.execute(sql, [table_name]).fetchone()
    return result[0] if result else ""


@router.get("/")
def get_full_schema() -> dict:
    """
    返回完整数据库 schema，供 schema_index 调用。
    格式：
    {
        "users": [...],
        "orders": [...],
        ...
    }
    """
    tables = get_tables()
    schema = {
        f"table_name:{table};comment:{get_table_comment(table)}": get_table_schema(table)
        for table in tables
    }

    return schema
