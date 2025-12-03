from fastapi import FastAPI
import duckdb
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# ---------------------------
# FastAPI 初始化
# ---------------------------
app = FastAPI()

# 允许跨域（前端开发常用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# 连接 DuckDB（文件模式）
# 如果文件不存在，会自动创建
# ---------------------------
conn = duckdb.connect("example.duckdb")

# 初始化数据库（只执行一次）
conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER,
    name VARCHAR,
    age INTEGER
);
""")

# 插入测试数据（如果为空）
row_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
if row_count == 0:
    conn.execute("""
    INSERT INTO users VALUES
    (1, 'Alice', 22),
    (2, 'Bob', 25),
    (3, 'Charlie', 30);
    """)

# ---------------------------
# 请求体模型
# ---------------------------
class SQLQuery(BaseModel):
    query: str

# ---------------------------
# SQL 查询接口
# ---------------------------
@app.post("/query")
def run_query(payload: SQLQuery):
    try:
        result = conn.execute(payload.query).fetchdf()   # 返回 DataFrame
        return {
            "success": True,
            "data": result.to_dict(orient="records")
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ---------------------------
# 健康检查
# ---------------------------
@app.get("/")
def root():
    return {"message": "FastAPI + DuckDB is running!"}
