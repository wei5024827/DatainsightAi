from fastapi import APIRouter, HTTPException
from app.models.nl_request import NLRequest
from app.core.llm_client import generate_sql_from_llm
from app.utils.sql_parser import extract_sql
import logging
import json
from app.api.v1.schema import get_schema


# -----------------------------
# 创建路由对象
# 自然语言转SQL接口 (POST /nl2sql)
# 功能：将自然语言问题转换为SQL查询
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


    schema_data = await get_schema()  
    schema_json = json.dumps(schema_data["schema"], ensure_ascii=False, indent=2)


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
        llm_output =  generate_sql_from_llm(prompt)
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
        "schema_used": schema_json  
    }

if __name__ == "__main__":
   # import asyncio
   # from app.api.v1.nl2sql import nl2sql_handler


    llm_output = generate_sql_from_llm("帮我查一下Alice在25年9月6号消费了多少钱")
    print(llm_output)