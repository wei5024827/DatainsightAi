import logging
import re

logger = logging.getLogger(__name__)


def extract_sql(llm_output: str) -> str:
    """从 LLM 生成文本中提取 SQL。"""
    content = llm_output.strip() if llm_output else ""
    if not content:
        logger.warning("LLM 输出为空，无法提取 SQL。")
        return ""

    markdown_match = re.search(r"```sql(.*?)```", content, re.DOTALL | re.IGNORECASE)
    if markdown_match:
        sql = markdown_match.group(1).strip()
        logger.info("从 Markdown 代码块提取 SQL 成功：%r", sql[:80])
        return sql

    plain_match = re.search(r"(SELECT|WITH)[\s\S]*", content, re.IGNORECASE)
    if plain_match:
        sql = plain_match.group(0).strip()
        logger.info("从普通文本提取 SQL 成功：%r", sql[:80])
        return sql

    logger.warning("未能从 LLM 输出中提取 SQL。")
    return ""
