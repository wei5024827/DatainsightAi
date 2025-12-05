# -----------------------------
# 1. 导入依赖
# -----------------------------
import duckdb                      # DuckDB 官方 Python 库，用于执行 SQL
import logging                     # 用于记录日志
from typing import List, Dict      # 类型标注，让返回值更明确


# -----------------------------
# 2. 初始化 logger（当前模块的日志记录器）
# -----------------------------
logger = logging.getLogger(__name__)


# -----------------------------
# 3. 创建 DuckDB 连接（全局复用）
# -----------------------------
# 说明：
# DuckDB 连接是“轻量级的”，创建一个全局连接即可。
# 为了避免每次查询都重新打开数据库，我们把连接放在模块级别。
try:
    # 连接一个持久化数据库文件（可换成你项目里的 example.duckdb）
    conn = duckdb.connect("app/example.duckdb")

    # 也可以使用内存数据库：
    # conn = duckdb.connect(":memory:")

    logger.info("DuckDB 连接成功。")

except Exception as e:
    logger.error(f"初始化 DuckDB 连接失败：{e}")
    raise


# -----------------------------
# 4. 检查并禁止危险 SQL（强烈建议）
# -----------------------------
def _is_sql_safe(sql: str) -> bool:
    """
    检查 SQL 是否包含危险操作。
    我们不允许 DELETE、DROP、UPDATE、ALTER 这种写操作。
    """
    sql_upper = sql.upper()

    forbidden = ["DELETE", "DROP", "UPDATE", "ALTER", "INSERT"]
    # INSERT 通常也禁止，因为自然语言接口不应该往 DB 写数据。

    # 只要 SQL 中出现任何危险关键字，我们就禁止执行
    return not any(keyword in sql_upper for keyword in forbidden)


# -----------------------------
# 5. 核心函数：执行 SQL
# -----------------------------
async def run_sql(sql: str) -> List[Dict]:
    """
    执行 SQL 并返回查询结果（list[dict] 格式，前端最容易解析）。
    """

    # ---- 5.1 空字符串检查 ----
    if not sql or not sql.strip():
        raise ValueError("SQL 不能为空。")

    logger.info(f"开始执行 SQL：{sql}")

    # ---- 5.2 安全检查：禁止危险 SQL ----
    if not _is_sql_safe(sql):
        raise ValueError("检测到危险 SQL（INSERT/DELETE/UPDATE/DROP/ALTER 不允许执行）。")

    try:
        # ---- 5.3 通过 DuckDB 执行 SQL ----
        result = conn.execute(sql)
        # conn.execute() 会返回一个 DuckDB Cursor，里面包含查询结果

        # ---- 5.4 提取结果为 Python list(dict) 格式 ----
        # fetchall() 返回 list[tuple]
        # description 获取字段名
        rows = result.fetchall()
        columns = [col[0] for col in result.description]

        # 将 tuple 结果转换成 dict 列表
        data = [dict(zip(columns, row)) for row in rows]

        logger.info(f"SQL 执行成功，共返回 {len(data)} 行。")

        return data

    except Exception as e:
        logger.error(f"执行 SQL 失败：{e}")
        raise

# if __name__ == "__main__":
#     import asyncio

#     test_sql = "SELECT * FROM users;"
#     result = asyncio.run(run_sql(test_sql))
#     print(result)
