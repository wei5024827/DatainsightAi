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



def generate_sql_from_llm(prompt: str) -> str:

    if not prompt or not prompt.strip():
        raise ValueError("Prompt must not be empty.")
    logger.info(f"调用 LLM 生成 SQL，prompt 前 50 字符：{prompt[:50]!r}")

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",  
            messages=[
                {
                    "role": "user",      
                    "content": prompt    # prompt 作为内容传给模型
                }
            ],
            temperature=0,              # 温度设为 0，尽量让输出稳定、确定，避免 SQL 随机变化
            max_tokens=256              # 限制最大输出长度，防止生成太长的无关内容
        )


    except Exception as e:
        logger.error(f"调用 OpenAI LLM 失败：{e}")
        raise

    llm_output = response.choices[0].message.content

    if not llm_output:
        logger.warning("LLM 返回内容为空。")
        return ""

    logger.info(f"LLM 输出前 80 字符：{llm_output[:80]!r}")

    return llm_output

    
# if __name__ == "__main__":
#      print(api_key)
#      llm_output = generate_sql_from_llm("生成一个查询所有用户的 SQL 语句,用户表为users")
#      print(llm_output)
