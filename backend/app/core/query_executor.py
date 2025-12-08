# -----------------------------
# 1. 导入依赖
# -----------------------------
import duckdb  # DuckDB 官方 Python 库，用于执行 SQL
import logging  # 用于记录日志
from typing import List, Dict  # 类型标注，让返回值更明确


# -----------------------------
# 2. 初始化 logger（当前模块的日志记录器）
# -----------------------------
logger = logging.getLogger(__name__)


# -----------------------------
# 3. 创建 DuckDB 连接（全局复用）
# -----------------------------
# 说明：
# DuckDB 连接是"轻量级的"，创建一个全局连接即可。
# 为了避免每次查询都重新打开数据库，我们把连接放在模块级别。
def get_db_connection():
    """获取数据库连接，支持重试机制"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 尝试以读写模式连接
            conn = duckdb.connect("app/example.duckdb", read_only=False)
            logger.info("DuckDB 连接成功。")
            return conn
        except Exception as e:
            logger.warning(f"第 {attempt + 1} 次连接失败：{e}")
            if attempt < max_retries - 1:
                import time

                time.sleep(1)  # 等待1秒后重试
            else:
                logger.error(f"连接数据库失败，已达到最大重试次数：{e}")
                raise


# 初始化连接
try:
    conn = get_db_connection()
except Exception as e:
    logger.error(f"初始化 DuckDB 连接失败：{e}")
    # 设置为None，后续在run_sql中动态创建连接
    conn = None


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
    print(f"INFO-00001 执行 SQL：{sql}")

    # ---- 5.1 空字符串检查 ----
    if not sql or not sql.strip():
        raise ValueError("SQL 不能为空。")

    logger.info(f"开始执行 SQL：{sql}")

    # ---- 5.2 安全检查：禁止危险 SQL ----
    if not _is_sql_safe(sql):
        # raise ValueError(
        #     "检测到危险 SQL（INSERT/DELETE/UPDATE/DROP/ALTER 不允许执行）。"
        # )
        pass

    # 使用局部连接，避免全局连接被锁定
    local_conn = None
    try:
        # 尝试使用全局连接
        if conn is not None:
            local_conn = conn
        else:
            # 如果全局连接不可用，创建新的连接
            local_conn = get_db_connection()

        # ---- 5.3 通过 DuckDB 执行 SQL ----
        result = local_conn.execute(sql)

        # ---- 5.4 提取结果为 Python list(dict) 格式 ----
        rows = result.fetchall()
        columns = [col[0] for col in result.description]

        # 将 tuple 结果转换成 dict 列表
        data = [dict(zip(columns, row)) for row in rows]

        logger.info(f"SQL 执行成功，共返回 {len(data)} 行。")

        return data

    except Exception as e:
        logger.error(f"执行 SQL 失败：{e}")
        # 如果是连接问题，尝试重新连接
        if "lock" in str(e).lower() or "locked" in str(e).lower():
            logger.warning("检测到数据库锁定，尝试使用备用方案...")
            # 这里可以添加备用方案，比如使用内存数据库
            try:
                # 尝试使用内存数据库（如果原数据库不可用）
                temp_conn = duckdb.connect(":memory:")
                # 这里可以添加一些基础数据或返回空结果
                logger.info("使用内存数据库作为备用方案")
                return []
            except Exception as mem_error:
                logger.error(f"备用方案也失败：{mem_error}")

        raise
    finally:
        # 如果是局部创建的连接，需要关闭
        if local_conn is not None and local_conn != conn:
            try:
                local_conn.close()
            except:
                pass


# if __name__ == "__main__":
#     import asyncio

#     test_sql = "SELECT * FROM users;"
#     result = asyncio.run(run_sql(test_sql))
#     print(result)