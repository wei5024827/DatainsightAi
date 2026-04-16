from typing import Any, Dict, List


def build_sql_generation_prompt(
    user_question: str,
    parsed_intent: Dict[str, Any],
    schema_text: str,
    metric_rules: List[Dict[str, Any]],
    business_term_rules: List[Dict[str, Any]],
    join_rules: List[Dict[str, Any]],
    time_rules: List[Dict[str, Any]],
    missing_tables: List[str],
) -> str:
    metric_sections = "\n\n".join(rule.get("context_text", "") for rule in metric_rules) or "（未检索到指标规则）"
    term_sections = "\n\n".join(rule.get("context_text", "") for rule in business_term_rules) or "（未检索到业务术语规则）"
    join_sections = "\n\n".join(rule.get("context_text", "") for rule in join_rules) or "（未检索到 Join 规则）"
    time_sections = "\n\n".join(rule.get("context_text", "") for rule in time_rules) or "（未检索到时间规则）"
    missing_table_text = ", ".join(missing_tables) if missing_tables else "无"

    return f"""
你是证券公司收入分析 SQL 助手。请根据给定的 schema、指标规则、业务术语规则、时间规则和关联规则生成 SQL。

请严格遵守以下要求：
1. 只允许输出一条 SELECT / WITH SQL，不要输出解释或 Markdown。
2. 只能使用给定 schema 中存在的表和字段，不要臆造。
3. 优先遵循业务规则中的指标编码、时间映射和术语口径。
4. 如果某条业务规则依赖的表不在 schema 中，不要编造该表；尽量使用已知表生成最接近的 SQL。
5. 如果无法完整满足规则，请保持 SQL 保守，不要伪造条件。

[用户问题]
{user_question}

[查询解析结果]
{parsed_intent}

[指标规则]
{metric_sections}

[业务术语规则]
{term_sections}

[Join 规则]
{join_sections}

[时间规则]
{time_sections}

[Schema]
{schema_text}

[规则依赖但 schema 中缺失的表]
{missing_table_text}
""".strip()
