from fastapi import APIRouter, HTTPException
from app.models.nl_request import NLRequest
from app.core.llm_client import generate_sql_from_llm
from app.utils.sql_parser import extract_sql
import logging

from app.core.schema_index import (
    get_relevant_tables,
    format_tables_for_prompt,
    init_schema_index,
)

# -----------------------------
# 创建路由对象
# -----------------------------
router = APIRouter(
    prefix="/nl2sql",   # 访问前缀，例如 POST /nl2sql
    tags=["LLM"]        # Swagger 文档标签分类
)

# 模块导入时，尝试预初始化一次索引（避免首个请求时的延迟）
try:
    init_schema_index()
except Exception as e:
    logging.warning(f"初始化 schema 索引时发生错误（可以忽略，后续按需再初始化）：{e}")


# -----------------------------
# 定义 POST 接口
# -----------------------------
@router.post("/")
async def nl2sql_handler(req: NLRequest):
    """
    接收自然语言 → 通过 RAG 检索相关 schema → 调用 LLM → 返回 SQL
    """

    logging.info(f"收到 NL2SQL 请求：{req.text}")

    # -----------------------------
    # 1. 输入校验
    # -----------------------------
    if not req.text or req.text.strip() == "":
        raise HTTPException(status_code=400, detail="text 字段不能为空")

    user_question = req.text.strip()

    # -----------------------------
    # 2. 使用 RAG 检索相关表结构
    # -----------------------------
    try:
        # 根据用户问题，检索出 Top-K 个最相关的表（可根据实际情况调整 top_k）
        relevant_tables = get_relevant_tables(user_question, top_k=10)
        schema_text = format_tables_for_prompt(relevant_tables)
    except Exception as e:
        logging.error(f"RAG schema 检索失败：{e}")
        # 即使 RAG 出问题，也不要让整个接口挂掉，可以退化为“无 schema 提示”的模式
        schema_text = "（RAG schema 检索失败，本次未提供表结构，请尽量按照常见 SQL 规范生成查询。）"

    # -----------------------------
    # 3. 构造 Prompt（非常关键）
    # -----------------------------
    # 和之前相比，现在我们会把“相关 schema 文本”塞进 prompt 里
    prompt = f"""
你是一个专业的 SQL 生成器，擅长根据用户的自然语言问题生成 SQL 查询。
请严格遵守以下要求：
1. 你只能使用下面给出的数据库表结构（Schema）中的表和字段，不要臆造不存在的表或字段。
2. 只生成 SQL 语句本身，不要返回多余的解释、说明或 Markdown 标记。
3. 禁止生成任何 DDL 或 DML（如 CREATE/UPDATE/DELETE/INSERT/DROP/ALTER 等），只允许 SELECT / WITH 查询。
4. 如果根据提供的表结构无法满足用户需求，你可以尽量给出最接近的查询，但不要捏造字段。

注意只能使用下面给出的数据库表结构：
{schema_text}

用户问题：{user_question}

请根据上述表结构和用户问题，生成一条合法、可执行的 SQL 查询语句：
"""

    # -----------------------------
    # 4. 调用 LLM 获取原始输出
    # -----------------------------
    try:
        # 这里仍然使用你现有的 llm_client.generate_sql_from_llm（不要改）
        llm_output = generate_sql_from_llm(prompt)
        # 如果你用的是异步版本的 llm_client，这里应该是：
        # llm_output = await generate_sql_from_llm(prompt)

    except Exception as e:
        logging.error(f"LLM 调用失败: {e}")
        raise HTTPException(status_code=502, detail="LLM 服务调用失败")

    # -----------------------------
    # 5. 解析 SQL（从 LLM 返回内容中提取 SQL）
    # -----------------------------
    sql = extract_sql(llm_output)

    if not sql:
        raise HTTPException(status_code=500, detail="未能从模型输出中解析出 SQL")

    # -----------------------------
    # 6. 返回结果
    # -----------------------------
    return {
        "sql": sql,               # 生成的 SQL（纯 SQL 字符串）
        "raw_output": llm_output, # 模型原始输出（调试用，可视情况删掉）
        "used_schema": schema_text  # 本次 RAG 使用的 schema 片段（方便前端展示/调试）
    }
# if __name__ == "__main__":
#     generate_sql_from_llm

   
