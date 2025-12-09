from fastapi import APIRouter
import duckdb  
import logging  

logger = logging.getLogger(__name__)


# -----------------------------
# 3. 创建路由对象
# 数据库 Schema 返回接口 (GET /schema)
# 功能：返回数据库的完整 Schema，用于帮助 LLM 生成 SQL。
# -----------------------------
router = APIRouter(
    prefix="/schema", tags=["Schema"] 
)


conn = duckdb.connect("app/example.duckdb", read_only=True)


def get_tables() -> list:
    """
    读取数据库中的所有表名
    """
    result = conn.execute("SHOW TABLES;")
    # SHOW TABLES 返回 list[tuple]

    tables = [row[0] for row in result.fetchall()]
    logger.info(f"检测到数据表：{tables}")
    return tables

def get_table_schema(table_name: str) -> list[dict]:
    """
    读取表结构信息包括comment
    """
    sql = f"""
        SELECT column_name AS name, data_type AS type,comment AS comment,column_index AS cid   FROM duckdb_columns WHERE table_name = '{table_name}';
    """
    result = conn.execute(sql)

    rows = result.fetchall()
    columns = [col[0] for col in result.description]

    # 将每一行信息转成 dict
    return [dict(zip(columns, row)) for row in rows]

def get_table_comment(table_name: str) -> str: # 读取表的注释
    sql = f"""
        SELECT comment FROM duckdb_tables  WHERE table_name = '{table_name}';
    """
    result = conn.execute(sql).fetchone()
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
    schema = {}

    for table in tables:
        schema[f"table_name:{table};comment:{get_table_comment(table)}"] = get_table_schema(table)

    return schema


# if __name__ == "__main__":
#     import asyncio

#     schema = asyncio.run(get_schema())

#     for table, cols in schema["schema"].items():
#         print(f"=== 表：{table} ===")
#         for col in cols:
#             print(col)
#         print()
