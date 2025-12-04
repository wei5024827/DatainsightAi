# -----------------------------
# 导入依赖
# -----------------------------
import re  # Python 内置正则库，用于从 LLM 输出中提取 SQL
import logging  # 用于记录日志，便于调试

# 创建 logger（当前模块的 logger）
logger = logging.getLogger(__name__)


# -----------------------------
# 核心函数：从 LLM 输出中提取 SQL
# -----------------------------
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

    # ---- 1. 基础参数检查 ----
    if not llm_output or not llm_output.strip():
        # LLM 返回了空字符串 → 无法提取 SQL
        logger.warning("LLM 输出为空，无法提取 SQL。")
        return ""

    # ---- 2. 优先匹配 Markdown 格式的 ```sql ... ``` 代码块 ----
    # 解释：
    # 很多模型会输出：
    #   ```sql
    #   SELECT * FROM table;
    #   ```
    # 用正则匹配其中内容
    markdown_pattern = r"```sql(.*?)```"  # 非贪婪匹配中间的内容 (.*?)，括号用于捕获内容

    match = re.search(markdown_pattern, llm_output, re.DOTALL | re.IGNORECASE)
    # re.DOTALL → 让 . 可以匹配换行
    # re.IGNORECASE → 忽略大小写，例如 ```SQL 也能识别

    if match:
        # 捕获到 SQL 代码块
        sql = match.group(1).strip()  # group(1) 是正则中第一个括号的内容
        logger.info(f"从 Markdown 代码块提取 SQL 成功：{sql[:80]!r}")
        return sql

    # ---- 3. 如果没有 ```sql```，尝试匹配普通的 SQL 开头，例如 SELECT / WITH / INSERT ----
    # LLM 可能返回：
    # "你可以使用如下 SQL：SELECT * FROM users ..."
    # 我们用正则寻找以 SELECT / WITH / INSERT / UPDATE / DELETE 开头的内容。
    sql_pattern = r"(SELECT|WITH|INSERT|UPDATE|DELETE)[\s\S]*"  # 从关键字开始提取后续所有内容
    match = re.search(sql_pattern, llm_output, re.IGNORECASE)

    if match:
        sql = match.group(0).strip()  # group(0) 是整个匹配到的内容
        logger.info(f"从普通文本中提取 SQL 成功：{sql[:80]!r}")
        return sql

    # ---- 4. 如果仍然没有匹配到 SQL，则打印警告并返回空字符串 ----
    logger.warning("未能从 LLM 输出中提取任何 SQL。")
    return ""

# if __name__ == "__main__":
#     print(extract_sql("""```sql
# SELECT * FROM users;
# ```

# 如果需要指定列名而不是使用通配符 `*`，可以这样写：
# ```sql
# SELECT id, username, email, created_at FROM users;
# ```

# 如果需要按特定条件筛选或排序，可以添加相应的子句：
# ```sql
# SELECT * FROM users WHERE is_active = 1 ORDER BY created_at DESC;
# ```"""))
