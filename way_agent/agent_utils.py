"""Shared helpers for running specialist agents with enriched context."""

from __future__ import annotations

from langchain_core.messages import AIMessage

from agent_runner import _fallback_response
from context_enricher import maybe_enrich_context
from llm_client import get_llm
from prompts import build_agent_prompt, latest_user_text


def run_enriched_agent(
    agent_name: str,
    state: dict,
    *,
    enable_web_search: bool = True,
) -> dict:
    db_context = state.get("db_context") or ""
    messages = state.get("messages", [])

    if enable_web_search:
        user_text = latest_user_text(messages)
        db_context = maybe_enrich_context(
            user_text, db_context, agent_name=agent_name
        )

    try:
        chain = build_agent_prompt(agent_name) | get_llm()
        response = chain.invoke({"messages": messages, "db_context": db_context})
        content = getattr(response, "content", str(response))
        return {"messages": [AIMessage(content=content)]}
    except Exception:
        return {"messages": [AIMessage(content=_fallback_response(agent_name, state))]}
