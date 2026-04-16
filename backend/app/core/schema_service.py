import logging
import os
from typing import Any, Dict, List

try:
    import duckdb
except ImportError:  # pragma: no cover - 运行环境缺依赖时仅在调用时失败
    duckdb = None

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "app", "example.duckdb")


def _connect_db() -> Any:
    if duckdb is None:
        raise RuntimeError("duckdb is not installed")
    return duckdb.connect(DB_PATH, read_only=True)


def get_tables() -> List[str]:
    with _connect_db() as conn:
        result = conn.execute("SHOW TABLES;")
        tables = [row[0] for row in result.fetchall()]
    logger.info("检测到数据表：%s", tables)
    return tables


def get_table_schema(table_name: str) -> List[Dict]:
    sql = """
        SELECT column_name AS name, data_type AS type, comment AS comment, column_index AS cid
        FROM duckdb_columns
        WHERE table_name = ?;
    """
    with _connect_db() as conn:
        result = conn.execute(sql, [table_name])
        rows = result.fetchall()
        columns = [col[0] for col in result.description]
    return [dict(zip(columns, row)) for row in rows]


def get_table_comment(table_name: str) -> str:
    sql = "SELECT comment FROM duckdb_tables WHERE table_name = ?;"
    with _connect_db() as conn:
        result = conn.execute(sql, [table_name]).fetchone()
    return result[0] if result else ""


def get_full_schema() -> Dict:
    tables = get_tables()
    return {
        f"table_name:{table};comment:{get_table_comment(table)}": get_table_schema(table)
        for table in tables
    }
