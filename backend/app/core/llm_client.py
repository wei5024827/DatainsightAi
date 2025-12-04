# app/core/llm_client.py

# -----------------------------
# 1. 导入标准库
# -----------------------------
import os  # 用于读取环境变量，比如 OPENAI_API_KEY
import logging  # 用于记录日志，方便排查问题

# -----------------------------
# 2. 导入第三方库
# -----------------------------
from dotenv import load_dotenv  # 加载 .env 文件中的环境变量
from openai import OpenAI




# -----------------------------
# 3. 初始化日志记录器
# -----------------------------
logger = logging.getLogger(__name__)  # 获取当前模块的 logger（建议在主程序配置 logging.basicConfig）


# -----------------------------
# 4. 加载 .env 文件
# -----------------------------
# 说明：
# - 这一步会从项目根目录的 .env 文件中加载环境变量
# - 如果 main.py 里已经调用过 load_dotenv()，再调用一次也没问题（幂等）
load_dotenv()


# -----------------------------
# 5. 读取 OpenAI API Key
# -----------------------------
# 从环境变量中读取 OPENAI_API_KEY
# 你在 .env 中写的是：OPENAI_API_KEY=sk-xxxxxxx
api_key = os.getenv("DEEPSEEK_API_KEY")

# 做一个健壮性检查：如果没有读到 key，则打错误日志并抛出异常
if not api_key:
    # 这里不会直接退出程序，而是抛出异常，让上层（比如启动阶段）能感知问题
    logger.error("环境变量 OPENAI_API_KEY 未设置，请检查 .env 或系统环境变量配置。")
    # 抛出 ValueError，让开发阶段尽早发现问题
    raise ValueError("OPENAI_API_KEY is not set in environment variables.")


# -----------------------------
# 6. 创建 OpenAI 异步客户端
# -----------------------------
# 使用 AsyncOpenAI 创建一个客户端实例
# 说明：
# - 这个 client 会在整个进程中复用，避免每次调用都重新创建连接
client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com")

# -----------------------------
# 7. 核心函数：调用 LLM 生成 SQL 文本
# -----------------------------
def generate_sql_from_llm(prompt: str) -> str:
    """
    根据传入的 prompt 调用大模型，返回模型生成的原始文本（字符串）。

    在你的项目中：
    - /nl2sql 接口会调用这个函数
    - 返回的文本再交给 sql_parser 去从中提取 SQL
    """

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
        # 调用成功后，response 是一个包含多个字段的对象：
        # - response.choices 是一个列表，每个元素是一种候选答案
        # - 我们通常只取第一个，即 choices[0]

    except Exception as e:
        # ---- 7.3 异常捕获 ----
        # 任何网络错误、认证错误、超时、服务端错误都会进入这里
        logger.error(f"调用 OpenAI LLM 失败：{e}")
        # 继续把异常向上抛，让上层（如 /nl2sql 接口）决定如何返回 HTTP 错误
        raise

    # ---- 7.4 从返回对象中提取文本内容 ----
    # OpenAI ChatCompletion 的标准结构：
    # response.choices 是一个列表
    # 我们取第一个回答：choices[0]
    # 它里面有一个 message 对象，其中 content 字段就是模型输出的文本
    llm_output = response.choices[0].message.content

    # 为了安全起见，做一个空值检查
    if not llm_output:
        logger.warning("LLM 返回内容为空。")
        # 返回空字符串，让上层去判断如何处理
        return ""

    # 记录一条日志，展示部分模型输出内容（只截取前 80 个字符）
    logger.info(f"LLM 输出前 80 字符：{llm_output[:80]!r}")

    # ---- 7.5 返回模型原始输出 ----
    # 注意：这里返回的是“原始文本”，里面可能还带有解释、Markdown 等格式
    # 你会在 sql_parser.extract_sql() 中进一步从中提取真正的 SQL 语句
    return llm_output

    
# if __name__ == "__main__":
#      print(api_key)
#      llm_output = generate_sql_from_llm("生成一个查询所有用户的 SQL 语句,用户表为users")
#      print(llm_output)
