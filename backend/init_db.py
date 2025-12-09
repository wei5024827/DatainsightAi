import duckdb
import os
import random
import datetime
from faker import Faker

fake = Faker("zh_CN")

db_path = os.path.join(os.path.dirname(__file__), "app", "example.duckdb")
conn = duckdb.connect(db_path,read_only=True)

# 生成随机日期
def date_offset(days_back=365):
    if days_back == 0:
        return datetime.date.today()

    days = random.randint(1, abs(days_back))
    delta = datetime.timedelta(days=days)
    return datetime.date.today() - delta if days_back > 0 else datetime.date.today() + delta



# =====================================
# 1. 生成 users
# =====================================
# users = []
# for i in range(1, 501):
#     users.append((
#         i,
#         fake.name(),
#         random.choice(["male", "female"]),
#         random.randint(18, 60),
#         fake.city_name(),
#         date_offset(500)
#     ))

# conn.execute("DELETE FROM users")
# conn.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", users)


# # =====================================
# # 2. user_address
# # =====================================
# addresses = []
# for i in range(1, 501):
#     addresses.append((
#         i,
#         i,
#         fake.address(),
#         True,
#         fake.phone_number()
#     ))

# conn.execute("DELETE FROM user_address")
# conn.executemany("INSERT INTO user_address VALUES (?, ?, ?, ?, ?)", addresses)


# # =====================================
# # 3. categories
# # =====================================
# category_list = [
#     "手机数码", "家用电器", "美妆护肤", "服饰鞋包", "母婴用品",
#     "宠物用品", "运动户外", "零食饮料", "生鲜食品", "电脑办公"
# ]
# categories = [(i + 1, name) for i, name in enumerate(category_list)]

# conn.execute("DELETE FROM categories")
# conn.executemany("INSERT INTO categories VALUES (?, ?)", categories)


# # =====================================
# # 4. products
# # =====================================
# products = []
# for pid in range(1, 201):
#     products.append((
#         pid,
#         fake.word(),
#         random.randint(1, 10),
#         round(random.uniform(20, 5000), 2),
#         random.choice(["active", "inactive"])
#     ))

# conn.execute("DELETE FROM products")
# conn.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?)", products)


# # =====================================
# # 5. inventory
# # =====================================
# inventory = []
# warehouses = ["上海仓", "北京仓", "广州仓"]

# for p in products:
#     for wh in warehouses:
#         inventory.append((p[0], wh, random.randint(0, 500)))

# conn.execute("DELETE FROM inventory")
# conn.executemany("INSERT INTO inventory VALUES (?, ?, ?)", inventory)


# # =====================================
# # 6. orders
# # =====================================
# orders = []
# for oid in range(1, 1001):
#     orders.append((
#         oid,
#         random.randint(1, 500),
#         date_offset(365),
#         random.choice(["paid", "shipped", "done", "cancelled"]),
#         0.0  # 稍后根据订单明细更新
#     ))

# conn.execute("DELETE FROM orders")
# conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", orders)


# # =====================================
# # 7. order_items
# # =====================================
# order_items = []
# item_id = 1
# order_amount_map = {}

# for oid in range(1, 1001):
#     item_count = random.randint(1, 3)
#     total = 0

#     for _ in range(item_count):
#         pid = random.randint(1, 200)
#         qty = random.randint(1, 5)
#         price = products[pid - 1][3]  # 从商品表读取价格
#         amount = round(price * qty, 2)

#         order_items.append((item_id, oid, pid, qty, amount))
#         item_id += 1

#         total += amount

#     order_amount_map[oid] = total

# # 写入明细表
# conn.execute("DELETE FROM order_items")
# conn.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?, ?)", order_items)

# # 回写订单金额
# for oid, amt in order_amount_map.items():
#     conn.execute("UPDATE orders SET total_amount = ? WHERE order_id = ?", (amt, oid))


# # =====================================
# # 8. payments
# # =====================================
# payments = []
# for oid in range(1, 1001):
#     payments.append((
#         oid,
#         oid,
#         random.choice(["alipay", "wechat", "bank"]),
#         order_amount_map[oid],
#         date_offset(365)
#     ))

# conn.execute("DELETE FROM payments")
# conn.executemany("INSERT INTO payments VALUES (?, ?, ?, ?, ?)", payments)


# # =====================================
# # 9. shipments
# # =====================================
# shipments = []
# companies = ["顺丰", "京东物流", "中通", "圆通"]

# for oid in range(1, 1001):
#     ship_time = date_offset(365)
#     shipments.append((
#         oid,
#         oid,
#         random.choice(companies),
#         ship_time,
#         ship_time + datetime.timedelta(days=random.randint(1, 5))
#     ))

# conn.execute("DELETE FROM shipments")
# conn.executemany("INSERT INTO shipments VALUES (?, ?, ?, ?, ?)", shipments)


# =====================================
# 10. coupons & 11. user_coupons
# =====================================
coupons = [(i, f"优惠券{i}", random.randint(5, 50), date_offset(-30)) for i in range(1, 21)]
conn.execute("DELETE FROM coupons")
conn.executemany("INSERT INTO coupons VALUES (?, ?, ?, ?)", coupons)

user_coupons = []
cid = 1
for uid in range(1, 201):
    user_coupons.append((
        cid,
        uid,
        random.randint(1, 20),
        random.choice(["used", "unused"]),
        date_offset(100)
    ))
    cid += 1

conn.execute("DELETE FROM user_coupons")
conn.executemany("INSERT INTO user_coupons VALUES (?, ?, ?, ?, ?)", user_coupons)

print("🎉 Mock 数据生成成功，已写入 example.duckdb！")
