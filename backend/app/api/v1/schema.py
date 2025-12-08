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


conn = duckdb.connect("app/example.duckdb", read_only=False)


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
    使用 PRAGMA table_info 读取表结构
    """
    sql = f"PRAGMA table_info('{table_name}');"
    result = conn.execute(sql)

    rows = result.fetchall()
    columns = [col[0] for col in result.description]

    # 将每一行信息转成 dict
    return [dict(zip(columns, row)) for row in rows]


@router.get("/")
async def get_schema():
    """
    返回数据库的完整 Schema，用于帮助 LLM 生成 SQL。
    """

    schema = {}
    tables = get_tables()
    for table in tables:
        schema[table] = get_table_schema(table)
    return {"schema": schema}

if __name__ == "__main__":
    import asyncio

    schema = asyncio.run(get_schema())

    for table, cols in schema["schema"].items():
        print(f"=== 表：{table} ===")
        for col in cols:
            print(col)
        print()
