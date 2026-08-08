"""Web search tools for agents that need current or external information."""

from __future__ import annotations

import logging

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

_SEARCH_TOOL = None


def _get_search_tool():
    global _SEARCH_TOOL
    if _SEARCH_TOOL is None:
        from langchain_community.tools import DuckDuckGoSearchRun

        _SEARCH_TOOL = DuckDuckGoSearchRun(max_results=5)
    return _SEARCH_TOOL


@tool
def search_web(query: str) -> str:
    """Search the web for current transit news, operator updates, attractions, fares, or policies."""
    query = (query or "").strip()
    if not query:
        return "No search query provided."

    try:
        return _get_search_tool().invoke(query)
    except Exception as exc:
        logger.warning("Web search failed for %r: %s", query, exc)
        return f"Web search unavailable ({exc}). Use general knowledge and note that live details should be verified."


def web_search_available() -> bool:
    try:
        from ddgs import DDGS  # noqa: F401

        return True
    except ImportError:
        return False
