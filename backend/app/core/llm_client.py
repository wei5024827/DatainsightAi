import logging
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)

load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("KIMI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.moonshot.cn/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "kimi2.5")

_client = None


def _get_client() -> OpenAI:
    global _client
    if not LLM_API_KEY:
        logger.error("未检测到 LLM API Key，请在 .env 中配置 LLM_API_KEY。")
        raise ValueError("LLM_API_KEY is not set in environment variables.")

    if _client is None:
        _client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    return _client


def call_llm(messages: List[Dict[str, Any]], max_tokens: int = 256, temperature: float = 0) -> str:
    if not messages:
        raise ValueError("Messages must not be empty.")

    first_message = messages[0].get("content", "") if messages else ""
    logger.info("调用 LLM，model=%s, 首条消息前 50 字符：%r", LLM_MODEL, str(first_message)[:50])

    try:
        response = _get_client().chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
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


def generate_sql_from_llm(prompt: str) -> str:
    normalized_prompt = prompt.strip() if prompt else ""
    if not normalized_prompt:
        raise ValueError("Prompt must not be empty.")

    return call_llm(
        messages=[{"role": "user", "content": normalized_prompt}],
        max_tokens=512,
        temperature=0,
    )
