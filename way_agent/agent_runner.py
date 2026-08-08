from __future__ import annotations

from prompts import AGENT_SPECS, latest_user_text


def _fallback_response(agent_name: str, state: dict) -> str:
    user_text = latest_user_text(state.get("messages", []))
    spec = AGENT_SPECS[agent_name]

    if not user_text:
        return f"{agent_name}: Tell me what you need help with and I will route the next step."

    if agent_name == "Journey Planner Agent":
        return (
            "Journey Planner Agent: I can plan that trip. Please share your origin, destination, "
            "travel time, and whether you prefer fastest, cheapest, or most accessible."
        )
    if agent_name == "Real-Time Transit Agent":
        return (
            "Real-Time Transit Agent: I can check service status when you provide the route, train, "
            "bus, station, or stop. I will label live data clearly when connected."
        )
    if agent_name == "Ticketing Agent":
        return (
            "Ticketing Agent: I can list your unified wallet by platform (rail/metro/bus/cab), "
            "show ticket numbers, or start a journey from a saved ticket. "
            "I will never ask for OTP, UPI PIN, CVV, or card details."
        )
    if agent_name == "Tourist Agent":
        return (
            "Tourist Agent: I can build a transit-friendly plan. Share the city, starting point, "
            "time available, interests, and budget."
        )
    if agent_name == "Safety Agent":
        return (
            "Safety Agent: If there is immediate danger, contact local emergency services or station staff now. "
            "Tell me your station, situation, and whether you need a safer route or accessibility support."
        )
    if agent_name == "Personalization Agent":
        return (
            "Personalization Agent: I can tailor WAY around your commute and preferences. "
            "Share what you want remembered, and I will ask before storing anything sensitive."
        )

    return (
        f"{agent_name}: {spec.mission} Ask me a specific WAY Transit question, "
        "or share trip details if you want a specialist answer."
    )


def run_agent(agent_name: str, state: dict) -> dict:
    from agent_utils import run_enriched_agent

    enable_web = agent_name != "Ticketing Agent"
    return run_enriched_agent(agent_name, state, enable_web_search=enable_web)
