import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.core.knowledge_base import list_knowledge_names, retrieve_knowledge
from app.core.llm_client import call_llm

logger = logging.getLogger(__name__)


def _extract_json_block(content: str) -> Optional[Dict[str, Any]]:
    if not content:
        return None

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", content)
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _extract_month(query: str) -> Optional[Dict[str, Any]]:
    match = re.search(r"(\d{4})年\s*(\d{1,2})月", query)
    if not match:
        return None

    year = int(match.group(1))
    month = int(match.group(2))
    if month < 1 or month > 12:
        return None

    normalized = f"{year}{month:02d}"
    return {
        "raw_text": match.group(0),
        "grain": "month",
        "normalized_value": normalized,
        "storage_format": "YYYYMM",
    }


def _extract_year(query: str) -> Optional[Dict[str, Any]]:
    match = re.search(r"(\d{4})年(?!\s*\d{1,2}月)", query)
    if not match:
        return None

    year = match.group(1)
    return {
        "raw_text": match.group(0),
        "grain": "year",
        "normalized_value": year,
        "storage_format": "YYYY",
    }


def _extract_employee_id(query: str) -> List[Dict[str, Any]]:
    patterns = [
        r"员工(?:号)?\s*([A-Za-z0-9_]+)",
        r"工号\s*([A-Za-z0-9_]+)",
        r"员工([A-Za-z0-9_]+)",
    ]
    matches = []
    seen = set()
    for pattern in patterns:
        for value in re.findall(pattern, query):
            if value and value not in seen:
                matches.append({"type": "employee_id", "value": value, "field_hint": "emp_num"})
                seen.add(value)
    return matches


def _detect_query_type(query: str) -> str:
    if any(keyword in query for keyword in ["排名", "前10", "前5", "top"]):
        return "ranking"
    if any(keyword in query for keyword in ["趋势", "每月", "按月", "走势"]):
        return "trend"
    if any(keyword in query for keyword in ["对比", "比较", "同比", "环比"]):
        return "compare"
    if any(keyword in query for keyword in ["明细", "列表", "逐笔"]):
        return "detail"
    return "aggregate"


def _detect_dimensions(query: str) -> List[str]:
    dimension_map = {
        "员工": ["员工", "人员", "姓名"],
        "营业部": ["营业部", "部门", "机构"],
        "月份": ["月", "月份"],
        "客户": ["按客户", "客户维度", "客户号"],
    }
    dimensions = []
    for name, keywords in dimension_map.items():
        if any(keyword in query for keyword in keywords):
            dimensions.append(name)
    return dimensions


def _detect_aggregation(query: str) -> str:
    if any(keyword in query for keyword in ["平均", "人均"]):
        return "avg"
    if any(keyword in query for keyword in ["数量", "多少个", "人数", "户数"]):
        return "count"
    return "sum"


def _match_terms(query: str, category: str) -> List[str]:
    matched = []
    for name in sorted(list_knowledge_names(category), key=len, reverse=True):
        if name and name in query:
            if any(name in existing for existing in matched):
                continue
            matched.append(name)
    return matched


def _heuristic_parse(query: str) -> Dict[str, Any]:
    time_range = _extract_month(query) or _extract_year(query)
    return {
        "query_type": _detect_query_type(query),
        "metrics": _match_terms(query, "metrics"),
        "business_terms": _match_terms(query, "business_terms"),
        "entities": _extract_employee_id(query),
        "time_range": time_range,
        "dimensions": _detect_dimensions(query),
        "aggregation": _detect_aggregation(query),
        "needs_clarification": False,
        "clarification_questions": [],
    }


def _llm_parse(query: str, heuristic_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    metric_candidates = [item.get("name") for item in retrieve_knowledge("metrics", query, top_k=8)]
    term_candidates = [item.get("name") for item in retrieve_knowledge("business_terms", query, top_k=8)]

    prompt = f"""
你是证券业务查询解析器。你的任务是把用户问题解析成结构化查询意图，不要生成 SQL。

用户问题：
{query}

规则预解析结果：
{json.dumps(heuristic_result, ensure_ascii=False)}

指标候选：
{json.dumps(metric_candidates, ensure_ascii=False)}

业务术语候选：
{json.dumps(term_candidates, ensure_ascii=False)}

请输出一个 JSON 对象，包含以下字段：
- query_type
- metrics
- business_terms
- entities
- time_range
- dimensions
- aggregation
- needs_clarification
- clarification_questions

要求：
1. 只输出 JSON，不要输出解释。
2. metrics 和 business_terms 使用最接近候选名称；如果没有把握，可以留空。
3. entities 中每个元素形如 {{"type":"employee_id","value":"E001","field_hint":"emp_num"}}。
4. time_range 中如果识别到月份，请输出 raw_text/grain/normalized_value/storage_format。
5. 不要编造数据库字段名，不要生成 SQL。
""".strip()

    try:
        llm_output = call_llm(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0,
        )
    except Exception as exc:
        logger.warning("LLM 解析查询意图失败，回退到规则解析：%s", exc)
        return None

    return _extract_json_block(llm_output)


def _merge_results(base: Dict[str, Any], refined: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not refined:
        return base

    merged = dict(base)
    for key in ["query_type", "aggregation", "needs_clarification"]:
        if refined.get(key) not in [None, ""]:
            merged[key] = refined[key]

    for key in ["metrics", "business_terms", "entities", "dimensions", "clarification_questions"]:
        if isinstance(refined.get(key), list) and refined[key]:
            merged[key] = refined[key]

    if isinstance(refined.get("time_range"), dict) and refined["time_range"]:
        merged["time_range"] = refined["time_range"]

    return merged


def parse_user_query(query: str) -> Dict[str, Any]:
    heuristic_result = _heuristic_parse(query)
    refined_result = _llm_parse(query, heuristic_result)
    parsed = _merge_results(heuristic_result, refined_result)

    if not parsed.get("metrics"):
        parsed["metrics"] = [item.get("name") for item in retrieve_knowledge("metrics", query, top_k=3)]
    if not parsed.get("business_terms"):
        parsed["business_terms"] = [item.get("name") for item in retrieve_knowledge("business_terms", query, top_k=3)]

    return parsed
