import json
import logging
import os
from functools import lru_cache
from typing import Any, Dict, Iterable, List

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_DIR = os.path.join(BASE_DIR, "knowledge")

CATEGORY_FILES = {
    "metrics": "metrics.json",
    "business_terms": "business_terms.json",
    "time_rules": "time_rules.json",
    "join_rules": "join_rules.json",
}


def _normalize_text(text: str) -> str:
    return (text or "").strip().lower()


def _iter_terms(entry: Dict[str, Any]) -> Iterable[str]:
    yield entry.get("name", "")
    for alias in entry.get("aliases", []):
        yield alias
    for keyword in entry.get("keywords", []):
        yield keyword


def _score_entry(query: str, entry: Dict[str, Any]) -> int:
    normalized_query = _normalize_text(query)
    if not normalized_query:
        return 0

    score = 0
    for term in _iter_terms(entry):
        normalized_term = _normalize_text(term)
        if not normalized_term:
            continue
        if normalized_term == normalized_query:
            score += 120
        elif normalized_term in normalized_query:
            score += 70
        elif normalized_query in normalized_term:
            score += 50

    corpus = " ".join(
        [
            entry.get("name", ""),
            " ".join(entry.get("aliases", [])),
            " ".join(entry.get("keywords", [])),
            entry.get("description", ""),
            entry.get("sql_hint", ""),
        ]
    ).lower()
    for char in set(normalized_query):
        if char.strip() and char in corpus:
            score += 1
    return score


def _entry_to_context(entry: Dict[str, Any]) -> str:
    lines = [f"名称: {entry.get('name', '')}"]
    if entry.get("aliases"):
        lines.append(f"别名: {', '.join(entry['aliases'])}")
    if entry.get("description"):
        lines.append(f"说明: {entry['description']}")
    if entry.get("source_table"):
        lines.append(f"来源表: {entry['source_table']}")
    if entry.get("code_field") and entry.get("code_value"):
        lines.append(f"编码规则: {entry['code_field']} = '{entry['code_value']}'")
    if entry.get("value_field"):
        lines.append(f"数值字段: {entry['value_field']}")
    if entry.get("default_aggregation"):
        lines.append(f"默认聚合: {entry['default_aggregation']}")
    if entry.get("required_tables"):
        lines.append(f"涉及表: {', '.join(entry['required_tables'])}")
    if entry.get("join_keys"):
        lines.append(f"关联键: {', '.join(entry['join_keys'])}")
    if entry.get("logic_steps"):
        lines.append(f"逻辑步骤: {'; '.join(entry['logic_steps'])}")
    if entry.get("sql_hint"):
        lines.append(f"SQL提示: {entry['sql_hint']}")
    if entry.get("examples"):
        lines.append(f"示例: {'; '.join(entry['examples'])}")
    return "\n".join(lines)


def _load_category(category: str) -> List[Dict[str, Any]]:
    filename = CATEGORY_FILES.get(category)
    if not filename:
        return []

    path = os.path.join(KNOWLEDGE_DIR, filename)
    if not os.path.exists(path):
        logger.warning("知识库文件不存在：%s", path)
        return []

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    entries = []
    for entry in data:
        normalized = dict(entry)
        normalized["category"] = category
        normalized["context_text"] = _entry_to_context(normalized)
        entries.append(normalized)
    return entries


@lru_cache(maxsize=1)
def load_knowledge_base() -> Dict[str, List[Dict[str, Any]]]:
    kb = {category: _load_category(category) for category in CATEGORY_FILES}
    logger.info("知识库加载完成：%s", {key: len(value) for key, value in kb.items()})
    return kb


def list_knowledge_names(category: str) -> List[str]:
    kb = load_knowledge_base()
    return [entry.get("name", "") for entry in kb.get(category, []) if entry.get("name")]


def find_exact_matches(category: str, terms: List[str]) -> List[Dict[str, Any]]:
    kb = load_knowledge_base()
    matched: List[Dict[str, Any]] = []
    seen_ids = set()
    normalized_terms = [_normalize_text(term) for term in terms if term]

    for entry in kb.get(category, []):
        entry_terms = {_normalize_text(term) for term in _iter_terms(entry) if term}
        if entry_terms.intersection(normalized_terms):
            entry_id = entry.get("id")
            if entry_id not in seen_ids:
                matched.append(entry)
                seen_ids.add(entry_id)

    return matched


def retrieve_knowledge(category: str, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    kb = load_knowledge_base()
    scored = []
    for entry in kb.get(category, []):
        score = _score_entry(query, entry)
        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda item: item[0], reverse=True)
    results = []
    for score, entry in scored[:top_k]:
        enriched = dict(entry)
        enriched["score"] = score
        results.append(enriched)
    return results


def get_time_rules() -> List[Dict[str, Any]]:
    return load_knowledge_base().get("time_rules", [])
