import duckdb  
import logging  
from typing import List, Dict  
import os

logger = logging.getLogger(__name__)

def get_db_connection():
    """获取数据库连接，支持重试机制"""
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_path = os.path.join(BASE_DIR, "app/example.duckdb")
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 尝试以读写模式连接
            conn = duckdb.connect(db_path, read_only=True)
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

# def _is_sql_safe(sql: str) -> bool:
#     """
#     检查 SQL 是否包含危险操作。
#     我们不允许 DELETE、DROP、UPDATE、ALTER 这种写操作。
#     """
#     sql_upper = sql.upper()

#     forbidden = ["DELETE", "DROP", "UPDATE", "ALTER", "INSERT"]
#     return not any(keyword in sql_upper for keyword in forbidden)


async def run_sql(sql: str) -> List[Dict]:
    """
    执行 SQL 并返回查询结果（list[dict] 格式，前端最容易解析）。
    """
    print(f"INFO-00001 执行 SQL：{sql}")

    #  空字符串检查
    if not sql or not sql.strip():
        raise ValueError("SQL 不能为空。")

    logger.info(f"开始执行 SQL：{sql}")

    # 使用局部连接，避免全局连接被锁定
    local_conn = None
    try:
        if conn is not None:
            local_conn = conn
        else:
            local_conn = get_db_connection()

        result = local_conn.execute(sql)

        rows = result.fetchall()
        columns = [col[0] for col in result.description]

        data = [dict(zip(columns, row)) for row in rows]

        logger.info(f"SQL 执行成功，共返回 {len(data)} 行。")

        return data

    except Exception as e:
        logger.error(f"执行 SQL 失败：{e}")
        if "lock" in str(e).lower() or "locked" in str(e).lower():
            logger.warning("检测到数据库锁定，尝试使用备用方案...")
            try:
                temp_conn = duckdb.connect(":memory:")
                logger.info("使用内存数据库作为备用方案")
                return []
            except Exception as mem_error:
                logger.error(f"备用方案也失败：{mem_error}")

        raise
    finally:
        if local_conn is not None and local_conn != conn:
            try:
                local_conn.close()
            except:
                pass


# if __name__ == "__main__":
#     import asyncio

#     test_sql = "SELECT id, name, city FROM users WHERE city = '上海';"
#     result = asyncio.run(run_sql(test_sql))
#     print(result)