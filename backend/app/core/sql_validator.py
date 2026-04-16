import re
from typing import Any, Dict, List


def validate_generated_sql(
    sql: str,
    parsed_intent: Dict[str, Any],
    metric_rules: List[Dict[str, Any]],
    available_table_names: List[str],
) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []

    normalized_sql = (sql or "").strip()
    upper_sql = normalized_sql.upper()

    if not normalized_sql:
        errors.append("SQL 为空。")
    if normalized_sql and not (upper_sql.startswith("SELECT") or upper_sql.startswith("WITH")):
        errors.append("仅允许 SELECT/WITH 查询。")

    for metric_rule in metric_rules:
        code_field = metric_rule.get("code_field")
        code_value = metric_rule.get("code_value")
        source_table = metric_rule.get("source_table")
        if code_field and code_value and code_value not in normalized_sql:
            warnings.append(f"SQL 中未显式包含指标编码 {code_field} = '{code_value}'。")
        if source_table and source_table not in available_table_names:
            warnings.append(f"指标规则依赖表 {source_table}，但 schema 未提供该表。")

    time_range = parsed_intent.get("time_range") or {}
    if time_range.get("grain") == "month":
        expected_value = str(time_range.get("normalized_value", ""))
        if expected_value and expected_value not in normalized_sql:
            warnings.append(f"SQL 中未显式使用标准化月份值 {expected_value}。")
        if re.search(r"\d{4}-\d{2}-\d{2}", normalized_sql):
            warnings.append("检测到日期格式字面量，月份字段应优先使用 YYYYMM。")

    for entity in parsed_intent.get("entities", []):
        value = str(entity.get("value", "")).strip()
        if value and value not in normalized_sql:
            warnings.append(f"SQL 中未显式包含实体过滤值 {value}。")

    return {
        "is_valid": not errors,
        "errors": errors,
        "warnings": warnings,
    }
