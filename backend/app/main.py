from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.api.v1.nl2sql import router as nl2sql_router
from app.api.v1.query import router as query_router
from app.api.v1.schema import router as schema_router


app = FastAPI(
    title="DataInsight AI API",
    description="自然语言转 SQL + SQL 执行 + Schema 返回",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.info("🚀 FastAPI 启动中...")


app.include_router(nl2sql_router)   # 自然语言 → SQL
app.include_router(query_router)    # 执行 SQL
app.include_router(schema_router)   # 返回数据库结构


@app.get("/")
async def root():
    return {"message": "DataInsight AI backend is running!"}
