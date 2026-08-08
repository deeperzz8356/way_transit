from langchain_core.messages import AIMessage

from prompts import build_agent_prompt, latest_user_text
from llm_client import get_llm
from tools.ticketing_tools import (
    list_wallet_tickets,
    get_ticket,
    start_journey,
    wallet_context_for_user,
)


def _intent_wallet_action(text: str) -> str | None:
    t = text.lower()
    if any(k in t for k in ("start journey", "begin journey", "start trip")):
        return "start"
    if any(k in t for k in ("wallet", "my ticket", "my tickets", "show ticket", "metro ticket", "rail ticket", "bus ticket")):
        return "list"
    return None


def _extract_mode(text: str) -> str | None:
    t = text.lower()
    for mode in ("metro", "rail", "bus", "cab"):
        if mode in t:
            return mode
    return None


def _extract_ticket_id(text: str) -> int | None:
    import re

    m = re.search(r"(?:ticket\s*#?\s*|id\s*=?\s*)(\d+)", text, flags=re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"\b(\d{1,6})\b", text)
    return int(m.group(1)) if m else None


def ticketing_node(state: dict) -> dict:
    user_text = latest_user_text(state.get("messages", []))
    user_id = state.get("user_id")
    wallet_ctx = ""
    tool_note = ""

    if user_id:
        try:
            wallet_ctx = wallet_context_for_user(int(user_id))
        except Exception as exc:
            wallet_ctx = f"USER WALLET: unavailable ({exc})"

        intent = _intent_wallet_action(user_text)
        try:
            if intent == "list":
                mode = _extract_mode(user_text)
                tool_note = list_wallet_tickets.invoke(
                    {"user_id": int(user_id), "mode": mode}
                )
            elif intent == "start":
                tid = _extract_ticket_id(user_text)
                if tid:
                    tool_note = start_journey.invoke(
                        {"user_id": int(user_id), "ticket_id": tid}
                    )
                else:
                    # start latest active ticket
                    listing = list_wallet_tickets.invoke(
                        {"user_id": int(user_id), "mode": _extract_mode(user_text)}
                    )
                    tool_note = (
                        "Ask which ticket id to start, or say e.g. 'start journey ticket 12'.\n"
                        + listing
                    )
            elif "ticket" in user_text.lower() and _extract_ticket_id(user_text):
                tool_note = get_ticket.invoke(
                    {
                        "user_id": int(user_id),
                        "ticket_id": _extract_ticket_id(user_text),
                    }
                )
        except Exception as exc:
            tool_note = f"Wallet tool error: {exc}"

    enriched = dict(state)
    db_context = (state.get("db_context") or "") + "\n" + wallet_ctx
    if tool_note:
        db_context += f"\n\nWALLET TOOL RESULT:\n{tool_note}\n"
    enriched["db_context"] = db_context

    try:
        prompt = build_agent_prompt("Ticketing Agent")
        llm = get_llm()
        chain = prompt | llm
        response = chain.invoke(
            {"messages": state.get("messages", []), "db_context": db_context}
        )
        content = getattr(response, "content", str(response))
    except Exception:
        content = tool_note or (
            "Ticketing Agent: I can list your wallet tickets by platform, show a ticket, "
            "or start a journey. Ask e.g. 'show my metro tickets' or 'start journey on latest rail ticket'."
        )
        if wallet_ctx:
            content += "\n\n" + wallet_ctx

    # Prefer concrete tool output when available
    if tool_note and "Wallet tool error" not in tool_note:
        content = f"{content}\n\n{tool_note}"

    return {"messages": [AIMessage(content=content)]}
