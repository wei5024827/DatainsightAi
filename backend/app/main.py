# -----------------------------------------
# main.py — FastAPI 应用入口
# -----------------------------------------

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# 导入你已经实现的 API 路由
from app.api.v1.nl2sql import router as nl2sql_router
from app.api.v1.query import router as query_router
from app.api.v1.schema import router as schema_router


# -----------------------------------------
# 1. 初始化 FastAPI 应用
# -----------------------------------------
app = FastAPI(
    title="DataInsight AI API",
    description="自然语言转 SQL + SQL 执行 + Schema 返回",
    version="1.0.0"
)


# -----------------------------------------
# 2. 配置 CORS（解决前端跨域问题）
# -----------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # 允许任何前端访问（开发环境特别好用）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------
# 3. 配置全局日志
# -----------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.info("🚀 FastAPI 启动中...")


# -----------------------------------------
# 4. 注册所有路由（非常关键）
# -----------------------------------------
app.include_router(nl2sql_router)   # 自然语言 → SQL
app.include_router(query_router)    # 执行 SQL
app.include_router(schema_router)   # 返回数据库结构


# -----------------------------------------
# 5. 健康检查接口（可选）
# -----------------------------------------
@app.get("/")
async def root():
    return {"message": "DataInsight AI backend is running!"}
