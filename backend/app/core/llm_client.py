import logging
import os

from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)

load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("KIMI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.moonshot.cn/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "kimi2.5")

if not LLM_API_KEY:
    logger.error("未检测到 LLM API Key，请在 .env 中配置 LLM_API_KEY。")
    raise ValueError("LLM_API_KEY is not set in environment variables.")

client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)


def generate_sql_from_llm(prompt: str) -> str:
    normalized_prompt = prompt.strip() if prompt else ""
    if not normalized_prompt:
        raise ValueError("Prompt must not be empty.")

    logger.info("调用 LLM 生成 SQL，model=%s, prompt 前 50 字符：%r", LLM_MODEL, normalized_prompt[:50])

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": normalized_prompt}],
            temperature=0,
            max_tokens=256,
        )
    except Exception as exc:
        logger.error("调用 LLM 失败（model=%s, base_url=%s）：%s", LLM_MODEL, LLM_BASE_URL, exc)
        raise

    llm_output = response.choices[0].message.content or ""
    if not llm_output:
        logger.warning("LLM 返回内容为空。")
        return ""

    logger.info("LLM 输出前 80 字符：%r", llm_output[:80])
    return llm_output
