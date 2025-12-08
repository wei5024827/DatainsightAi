import re  
import logging  

logger = logging.getLogger(__name__)


def extract_sql(llm_output: str) -> str:
    """
    从 LLM（如 gpt-4o）生成的文本中提取 SQL 语句。

    LLM 可能返回：
        - 纯 SQL
        - 带 Markdown 代码块 ```sql ... ```
        - 前后带解释性文字
        - 多条 SQL，但我们只取第一条有效 SQL

    本函数的目标：
        只提取最核心的 SQL，并返回干净的 SQL 字符串。
    """

  
    if not llm_output or not llm_output.strip():
        # LLM 返回了空字符串 → 无法提取 SQL
        logger.warning("LLM 输出为空，无法提取 SQL。")
        return ""


    markdown_pattern = r"```sql(.*?)```"  # 非贪婪匹配中间的内容 (.*?)，括号用于捕获内容

    match = re.search(markdown_pattern, llm_output, re.DOTALL | re.IGNORECASE)


    if match:
        # 捕获到 SQL 代码块
        sql = match.group(1).strip()  # group(1) 是正则中第一个括号的内容
        logger.info(f"从 Markdown 代码块提取 SQL 成功：{sql[:80]!r}")
        return sql

    sql_pattern = r"(SELECT|WITH|INSERT|UPDATE|DELETE)[\s\S]*"  # 从关键字开始提取后续所有内容
    match = re.search(sql_pattern, llm_output, re.IGNORECASE)

    if match:
        sql = match.group(0).strip()  # group(0) 是整个匹配到的内容
        logger.info(f"从普通文本中提取 SQL 成功：{sql[:80]!r}")
        return sql

    logger.warning("未能从 LLM 输出中提取任何 SQL。")
    return ""

# if __name__ == "__main__":
#     print(extract_sql("""```sql
# SELECT * FROM users;
