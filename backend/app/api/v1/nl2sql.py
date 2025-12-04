# -----------------------------
# 导入依赖
# -----------------------------
from fastapi import APIRouter, HTTPException
from app.models.nl_request import NLRequest
from app.core.llm_client import generate_sql_from_llm
from app.utils.sql_parser import extract_sql
import logging
import json

# ⭐ 新增：导入 Schema 读取函数
from app.api.v1.schema import get_schema


# -----------------------------
# 创建路由对象
# -----------------------------
router = APIRouter(
    prefix="/nl2sql",
    tags=["LLM"]
)


@router.post("/")
async def nl2sql_handler(req: NLRequest):
    logging.info(f"收到 NL2SQL 请求：{req.text}")

    if not req.text or req.text.strip() == "":
        raise HTTPException(status_code=400, detail="text 字段不能为空")

    # ⭐ 第一步：获取数据库结构
    schema_data = await get_schema()   # 返回 {"schema": {...}}
    schema_json = json.dumps(schema_data["schema"], ensure_ascii=False, indent=2)

    # ⭐ 第二步：构造 Prompt（注入 Schema）
    prompt = f"""
你是一个 SQL 生成专家。

下面是数据库的结构，请务必严格按照这些表和字段生成 SQL：

数据库结构如下（JSON 格式）：
{schema_json}

要求：
- 只生成 SQL，不要解释
- 不允许 DELETE、DROP、UPDATE、ALTER
- SQL 必须合法可执行
- 表名和字段名必须来自 schema

用户问题：{req.text}
"""

    # 调用 LLM
    try:
        llm_output = await generate_sql_from_llm(prompt)
    except Exception as e:
        logging.error(f"LLM 调用失败: {e}")
        raise HTTPException(status_code=502, detail="LLM 服务调用失败")

    # 提取 SQL
    sql = extract_sql(llm_output)

    if not sql:
        raise HTTPException(status_code=500, detail="未能从模型输出中解析 SQL")

    return {
        "sql": sql,
        "raw_output": llm_output,
        "schema_used": schema_json  # 可选返回，方便调试
    }
