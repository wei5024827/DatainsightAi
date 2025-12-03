# -----------------------------
# 导入依赖
# -----------------------------
import os
# 用来读取环境变量（比如 OPENAI_API_KEY）

from openai import AsyncOpenAI
# OpenAI 官方异步客户端，用于调用模型

import logging
# 用来记录日志，方便调试


# -----------------------------
# 初始化 OpenAI 客户端
# -----------------------------
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)
# 创建一个异步 LLM 客户端实例
# api_key：从系统环境变量读取（你需要在 .env 或系统中提前设置）
# AsyncOpenAI：让 LLM 调用支持异步 await，更适合 FastAPI


# -----------------------------
# 核心函数：发送 prompt 并获取 SQL 文本
# -----------------------------
async def generate_sql_from_llm(prompt: str) -> str:
    """
    调用大模型（LLM），根据 prompt 返回生成的文本。
    返回内容可能包含 Markdown，需要后续解析。
    """

    logging.info("开始调用 LLM 生成 SQL...")
    # 打印提示，便于调试流程

    try:
        # -----------------------------------------
        # 调用模型
        # -----------------------------------------
        response = await client.chat.completions.create(
            model="gpt-4o-mini",       # 可根据你项目自由选择（轻量小型号）
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0,             # 设置为 0，确保输出更稳定，不乱跑
            max_tokens=256             # 控制最大生成长度，防止模型写太多废话
        )
        # response 是模型完整输出对象，包含 choices、usage 等字段
        # messages：传给模型的对话内容（只有一个用户 prompt）
        # temperature = 0：尽量减少随机性（SQL 生成更可靠）
        # max_tokens：避免生成过长内容浪费 tokens

    except Exception as e:
        # 捕获网络错误、API key 错误、超时等
        logging.error(f"LLM API 调用失败：{e}")
        raise e
        # 将错误继续抛出，由上层（nl2sql.py）决定返回 HTTP 错误码

    # -----------------------------------------
    # 提取模型生成的文本内容
    # -----------------------------------------
    llm_output = response.choices[0].message.content
    # LLM 输出文本位于 response.choices[0].message.content
    # OpenAI 的返回格式固定是 choices 列表形式

    logging.info(f"LLM 输出：{llm_output[:80]}...")
    # 只打印前 80 个字符，避免日志太长

    return llm_output
    # 将原始 LLM 输出交给上层 /nl2sql.py 去进一步解析 SQL
