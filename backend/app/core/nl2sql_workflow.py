import logging
from typing import Any, Dict, List, Set

from app.core.context_builder import build_sql_generation_prompt
from app.core.knowledge_base import find_exact_matches, get_time_rules, retrieve_knowledge
from app.core.llm_client import generate_sql_from_llm
from app.core.query_parser import parse_user_query
from app.core.schema_index import format_tables_for_prompt, get_relevant_tables
from app.core.schema_service import get_full_schema
from app.core.sql_validator import validate_generated_sql
from app.utils.sql_parser import extract_sql

logger = logging.getLogger(__name__)


def _normalize_schema(full_schema: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    normalized = {}
    for raw_name, columns in full_schema.items():
        table_name = raw_name
        comment = ""
        if raw_name.startswith("table_name:") and ";comment:" in raw_name:
            table_name, comment = raw_name.split(";comment:", 1)
            table_name = table_name.replace("table_name:", "", 1)

        normalized[table_name] = {
            "table_name": table_name,
            "comment": comment,
            "columns": columns if isinstance(columns, list) else columns.get("columns", []),
        }
    return normalized


def _collect_table_hints(metric_rules: List[Dict[str, Any]], business_term_rules: List[Dict[str, Any]], join_rules: List[Dict[str, Any]]) -> Set[str]:
    hinted_tables: Set[str] = set()
    for rule in metric_rules:
        if rule.get("source_table"):
            hinted_tables.add(rule["source_table"])
    for rule in business_term_rules:
        hinted_tables.update(rule.get("required_tables", []))
    for rule in join_rules:
        hinted_tables.update(rule.get("tables", []))
    return hinted_tables


def _fetch_schema_context(user_question: str, hinted_tables: Set[str]) -> Dict[str, Any]:
    relevant_tables = get_relevant_tables(user_question, top_k=10)
    full_schema = _normalize_schema(get_full_schema())

    combined = {table["table_name"]: table for table in relevant_tables}
    missing_tables = []
    for table_name in hinted_tables:
        if table_name in full_schema:
            combined[table_name] = full_schema[table_name]
        else:
            missing_tables.append(table_name)

    schema_tables = list(combined.values())
    schema_text = format_tables_for_prompt(schema_tables)
    return {
        "schema_text": schema_text,
        "schema_tables": schema_tables,
        "available_table_names": list(full_schema.keys()),
        "missing_tables": missing_tables,
    }


def _retrieve_rules(user_question: str, parsed_intent: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    metric_terms = parsed_intent.get("metrics", [])
    business_terms = parsed_intent.get("business_terms", [])

    metric_rules = find_exact_matches("metrics", metric_terms) if metric_terms else retrieve_knowledge("metrics", user_question, top_k=3)
    business_term_rules = (
        find_exact_matches("business_terms", business_terms) if business_terms else retrieve_knowledge("business_terms", user_question, top_k=3)
    )
    join_rules = retrieve_knowledge("join_rules", user_question, top_k=3)
    time_rules = get_time_rules()

    return {
        "metric_rules": metric_rules,
        "business_term_rules": business_term_rules,
        "join_rules": join_rules,
        "time_rules": time_rules,
    }


def run_nl2sql_workflow(user_question: str) -> Dict[str, Any]:
    parsed_intent = parse_user_query(user_question)
    rules = _retrieve_rules(user_question, parsed_intent)

    hinted_tables = _collect_table_hints(
        rules["metric_rules"],
        rules["business_term_rules"],
        rules["join_rules"],
    )
    schema_context = _fetch_schema_context(user_question, hinted_tables)

    prompt = build_sql_generation_prompt(
        user_question=user_question,
        parsed_intent=parsed_intent,
        schema_text=schema_context["schema_text"],
        metric_rules=rules["metric_rules"],
        business_term_rules=rules["business_term_rules"],
        join_rules=rules["join_rules"],
        time_rules=rules["time_rules"],
        missing_tables=schema_context["missing_tables"],
    )

    llm_output = generate_sql_from_llm(prompt)
    sql = extract_sql(llm_output)
    validation = validate_generated_sql(
        sql=sql,
        parsed_intent=parsed_intent,
        metric_rules=rules["metric_rules"],
        available_table_names=schema_context["available_table_names"],
    )

    logger.info(
        "NL2SQL 工作流完成，metrics=%s, business_terms=%s, warnings=%s",
        parsed_intent.get("metrics"),
        parsed_intent.get("business_terms"),
        validation.get("warnings"),
    )

    return {
        "sql": sql,
        "raw_output": llm_output,
        "used_schema": schema_context["schema_text"],
        "parsed_intent": parsed_intent,
        "retrieved_knowledge": {
            "metrics": rules["metric_rules"],
            "business_terms": rules["business_term_rules"],
            "join_rules": rules["join_rules"],
            "time_rules": rules["time_rules"],
            "missing_tables": schema_context["missing_tables"],
        },
        "validation": validation,
        "generation_prompt": prompt,
    }
