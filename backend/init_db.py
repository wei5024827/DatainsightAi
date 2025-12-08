# ---------------------------------------
# 初始化 DuckDB 示例数据库
# ---------------------------------------

import duckdb
import logging
from datetime import date, timedelta
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------
# 1. 数据库文件路径
# ---------------------------------------
DB_PATH = "app/example.duckdb"

# 如果文件已存在，删除重新生成（确保数据干净）
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    logger.info("旧的 example.duckdb 已删除，准备重新创建。")


# ---------------------------------------
# 2. 建立 DuckDB 数据库连接
# ---------------------------------------
conn = duckdb.connect(DB_PATH)
logger.info("成功连接到 DuckDB。")


# ---------------------------------------
# 3. 创建表结构
# ---------------------------------------

logger.info("开始创建表结构...")

conn.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name VARCHAR,
    city VARCHAR
);
""")

conn.execute("""
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    amount DOUBLE,
    date DATE
);
""")

conn.execute("""
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name VARCHAR,
    price DOUBLE
);
""")

logger.info("表结构创建完成！")


# ---------------------------------------
# 4. 插入 users 示例数据
# ---------------------------------------

logger.info("插入 users 示例数据...")

users_data = [
    (1, "Alice", "Beijing"),
    (2, "Bob", "Shanghai"),
    (3, "Charlie", "Guangzhou"),
    (4, "David", "Shenzhen"),
    (5, "Eva", "Beijing")
]

conn.executemany("INSERT INTO users VALUES (?, ?, ?);", users_data)


# ---------------------------------------
# 5. 插入 products 示例数据
# ---------------------------------------

logger.info("插入 products 示例数据...")

products_data = [
    (1, "iPhone", 6999),
    (2, "Laptop", 8999),
    (3, "Tablet", 3999),
    (4, "Headset", 799),
    (5, "Smartwatch", 1999)
]

conn.executemany("INSERT INTO products VALUES (?, ?, ?);", products_data)


# ---------------------------------------
# 6. 插入 orders 示例数据（自动生成 90 天数据）
# ---------------------------------------

logger.info("开始生成 90 天订单数据...")

today = date.today()
order_id = 1
orders_data = []

# 生成过去 90 天的随机订单数据
import random

for i in range(90):
    day = today - timedelta(days=i)

    # 每天随机 5–15 个订单
    count = random.randint(5, 15)

    for _ in range(count):
        user_id = random.randint(1, 5)      # 用户 1-5
        amount = round(random.uniform(20, 800), 2)  # 金额 20~800
        orders_data.append((order_id, user_id, amount, day))
        order_id += 1

conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?);", orders_data)

logger.info(f"成功生成 {len(orders_data)} 条订单。")


# ---------------------------------------
# 7. 关闭连接
# ---------------------------------------
conn.close()
logger.info("数据库初始化完成！🎉 已生成 example.duckdb。")
