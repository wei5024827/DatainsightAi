# -----------------------------
# 1. 导入依赖
# -----------------------------
from fastapi import APIRouter
import duckdb                    # 用于查询数据库元数据
import logging                  # 日志模块


# -----------------------------
# 2. 初始化 logger
# -----------------------------
logger = logging.getLogger(__name__)


# -----------------------------
# 3. 创建路由对象
# 数据库 Schema 返回接口 (GET /schema)
# 功能：返回数据库的完整 Schema，用于帮助 LLM 生成 SQL。
# 请求方式：GET
# 示例：GET /schema
# -----------------------------
router = APIRouter(
    prefix="/schema",   # 访问路径: GET /schema
    
    tags=["Schema"]     # Swagger 文档中分类标签
)


# -----------------------------
# 4. 创建数据库连接（可复用）
# -----------------------------
# 与 query_executor.py 一样的连接方式
conn = duckdb.connect("app/example.duckdb")


# -----------------------------
# 5. 工具函数：读取所有表名
# -----------------------------
def get_tables() -> list:
    """
    读取数据库中的所有表名
    """
    result = conn.execute("SHOW TABLES;")
    # SHOW TABLES 返回 list[tuple]

    tables = [row[0] for row in result.fetchall()]
    logger.info(f"检测到数据表：{tables}")
    return tables


# -----------------------------
# 6. 工具函数：读取某个表的字段结构
# -----------------------------
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


# -----------------------------
# 7. API：返回数据库所有表结构
# -----------------------------
@router.get("/")
async def get_schema():
    """
    返回数据库的完整 Schema，用于帮助 LLM 生成 SQL。
    """

    schema = {}

    # 1）获取所有表名
    tables = get_tables()

    # 2）对每个表获取字段结构
    for table in tables:
        schema[table] = get_table_schema(table)

    # 3）返回 JSON
    return {"schema": schema}

#test code

if __name__ == "__main__":
    import asyncio 

    schema = asyncio.run(get_schema())

    for table, cols in schema["schema"].items():
        print(f"=== 表：{table} ===")
        for col in cols:
            print(col)
        print()