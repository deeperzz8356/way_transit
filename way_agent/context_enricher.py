"""Augment agent context with web search when RAG/DB alone are insufficient."""

from __future__ import annotations

import re

from tools.web_search_tools import search_web, web_search_available

# Agents that benefit from external / current information
WEB_SEARCH_AGENTS = frozenset(
    {
        "Journey Planner Agent",
        "Real-Time Transit Agent",
        "Tourist Agent",
        "Safety Agent",
        "General Q&A Agent",
    }
)

# Wallet / payment queries should stay on DB + tools only
_WALLET_ONLY = re.compile(
    r"\b(wallet|my ticket|my tickets|start journey|qr|refund|pass\b|recharge|booking)\b",
    re.I,
)

# Signals that fresh or external info would help
_CURRENT_INFO = re.compile(
    r"\b(today|tonight|now|current|latest|update|news|delay|delayed|cancel|"
    r"disruption|status|schedule|timetable|fare|price|cost|open|hours|"
    r"attraction|museum|restaurant|hotel|visit|tourist|things to do|"
    r"policy|rules|allowed|permit|construction|diversion|strike|holiday)\b",
    re.I,
)


def should_web_search(query: str, *, agent_name: str | None = None) -> bool:
    if not query or not web_search_available():
        return False
    if agent_name and agent_name not in WEB_SEARCH_AGENTS:
        return False
    if _WALLET_ONLY.search(query):
        return False
    if _CURRENT_INFO.search(query):
        return True
    # Short or open-ended questions often need more than stale RAG chunks
    if len(query.split()) >= 4 and "?" in query:
        return True
    return False


def _build_search_query(user_query: str, agent_name: str | None) -> str:
    base = user_query.strip()
    if agent_name == "Tourist Agent":
        return f"{base} transit friendly attractions India"
    if agent_name == "Real-Time Transit Agent":
        return f"{base} transit delay status India today"
    if agent_name == "Journey Planner Agent":
        return f"{base} public transport route India"
    if agent_name == "Safety Agent":
        return f"{base} public transport safety advisory India"
    return f"{base} India public transport"


def maybe_enrich_context(
    user_query: str,
    db_context: str,
    *,
    agent_name: str | None = None,
    force: bool = False,
) -> str:
    """Append web search results to db_context when appropriate."""
    if "WEB SEARCH RESULTS" in (db_context or ""):
        return db_context
    if not force and not should_web_search(user_query, agent_name=agent_name):
        return db_context

    search_query = _build_search_query(user_query, agent_name)
    try:
        results = search_web.invoke(search_query)
    except Exception as exc:
        results = f"Search failed: {exc}"

    if not results or results.startswith("Web search unavailable"):
        return db_context

    block = f"""
WEB SEARCH RESULTS (verify against official sources when critical):
Query: {search_query}
{results}
"""
    return (db_context or "") + "\n" + block
