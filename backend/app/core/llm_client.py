import os  
import logging 
from dotenv import load_dotenv 
from openai import OpenAI

logger = logging.getLogger(__name__) 

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")

if not api_key:
    logger.error("环境变量 OPENAI_API_KEY 未设置，请检查 .env 或系统环境变量配置。")
    raise ValueError("OPENAI_API_KEY is not set in environment variables.")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com")

# -----------------------------
# 7. 核心函数：调用 LLM 生成 SQL 文本
# -----------------------------
def generate_sql_from_llm(prompt: str) -> str:

    # ---- 7.1 基本参数检查 ----
    if not prompt or not prompt.strip():
        # 如果 prompt 是空的，直接抛异常，这是开发错误，不是 LLM 错误
        raise ValueError("Prompt must not be empty.")

    # 记录一条日志，说明即将调用 LLM
    # 仅打印 prompt 的长度或前几十个字符，避免日志太长泄露信息
    logger.info(f"调用 LLM 生成 SQL，prompt 前 50 字符：{prompt[:50]!r}")

    try:
        # ---- 7.2 调用 OpenAI Chat Completions 接口 ----
        # 使用异步客户端调用 chat.completions.create
        response = client.chat.completions.create(
            model="deepseek-chat",  # 指定模型名称，可按需替换为其它模型
            messages=[
                {
                    "role": "user",      # 角色是 user，表示这是用户的输入
                    "content": prompt    # 把我们构造好的 prompt 作为内容传给模型
                }
            ],
            temperature=0,              # 温度设为 0，尽量让输出稳定、确定，避免 SQL 随机变化
            max_tokens=256              # 限制最大输出长度，防止生成太长的无关内容
        )


    except Exception as e:
        # ---- 7.3 异常捕获 ----
        # 任何网络错误、认证错误、超时、服务端错误都会进入这里
        logger.error(f"调用 OpenAI LLM 失败：{e}")
        # 继续把异常向上抛，让上层（如 /nl2sql 接口）决定如何返回 HTTP 错误
        raise

    llm_output = response.choices[0].message.content

    # 为了安全起见，做一个空值检查
    if not llm_output:
        logger.warning("LLM 返回内容为空。")
        # 返回空字符串，让上层去判断如何处理
        return ""

    # 记录一条日志，展示部分模型输出内容（只截取前 80 个字符）
    logger.info(f"LLM 输出前 80 字符：{llm_output[:80]!r}")

    return llm_output

    
# if __name__ == "__main__":
#      print(api_key)
#      llm_output = generate_sql_from_llm("生成一个查询所有用户的 SQL 语句,用户表为users")
#      print(llm_output)
