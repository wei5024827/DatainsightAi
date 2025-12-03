# -----------------------------
# 导入依赖
# -----------------------------
from fastapi import APIRouter, HTTPException
# 导入 FastAPI 的路由、异常类

from app.models.nl_request import NLRequest
# 导入你定义的请求模型（Pydantic），包含 text 字段

from app.core.llm_client import generate_sql_from_llm
# 这是你自己在 llm_client.py 文件中定义的函数，用来调用 LLM

from app.utils.sql_parser import extract_sql
# 工具函数：从 LLM 返回的文本中提取纯 SQL

import logging
# 用于记录日志（方便调试）


# -----------------------------
# 创建路由对象
# -----------------------------
router = APIRouter(
    prefix="/nl2sql",   # 访问前缀，例如 POST /nl2sql
    tags=["LLM"]        # Swagger 文档标签分类
)


# -----------------------------
# 定义 POST 接口
# -----------------------------
@router.post("/")
async def nl2sql_handler(req: NLRequest):
    """
    接收自然语言 → 调用 LLM → 返回 SQL
    """

    logging.info(f"收到 NL2SQL 请求：{req.text}")
    # 记录日志（便于调试）

    # -----------------------------
    # 1. 输入校验
    # -----------------------------
    if not req.text or req.text.strip() == "":
        raise HTTPException(status_code=400, detail="text 字段不能为空")
    # 检查 text 是否为空，如果为空返回 HTTP 400

    # -----------------------------
    # 2. 构造 Prompt（非常关键）
    # -----------------------------
    prompt = f"""
你是一个专业 SQL 生成器。
请根据用户的问题生成 SQL 查询语句。
注意：
- 只返回 SQL，不要返回解释
- SQL 必须合法可执行
- 不允许 DELETE、DROP、UPDATE 等危险语句

用户问题：{req.text}
"""
    # prompt 通过字符串拼接，把用户的问题放进去

    # -----------------------------
    # 3. 调用 LLM 获取原始输出
    # -----------------------------
    try:
        llm_output = await generate_sql_from_llm(prompt)
        # 调用你封装的模型调用函数
        # 这里 llm_output 是模型返回的完整文本

    except Exception as e:
        logging.error(f"LLM 调用失败: {e}")
        raise HTTPException(status_code=502, detail="LLM 服务调用失败")
    # 捕捉网络、超时、API错误，返回 502 Bad Gateway

    # -----------------------------
    # 4. 解析 SQL（从 LLM 返回内容中提取 SQL）
    # -----------------------------
    sql = extract_sql(llm_output)
    # extract_sql 工具会自动去掉 markdown 符号、解释性文字，只保留 SQL

    if not sql:
        raise HTTPException(status_code=500, detail="未能从模型输出中解析出 SQL")
    # 如果 SQL 为空，说明模型输出不符合要求

    # -----------------------------
    # 5. 返回结果
    # -----------------------------
    return {
        "sql": sql,              # 生成的 SQL
        "raw_output": llm_output # 模型原始输出（调试用，可删）
    }
