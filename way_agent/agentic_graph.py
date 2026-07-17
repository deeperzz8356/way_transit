from __future__ import annotations

import operator
from typing import Annotated, Literal, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from agent_runner import run_agent
from llm_client import get_llm
from prompts import build_supervisor_prompt, latest_user_text


MEMBERS = [
    "Journey Planner Agent",
    "Real-Time Transit Agent",
    "Ticketing Agent",
    "Tourist Agent",
    "Safety Agent",
    "Personalization Agent",
    "General Q&A Agent",
]


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str


class RouteResponse(BaseModel):
    next: Literal[
        "FINISH",
        "Journey Planner Agent",
        "Real-Time Transit Agent",
        "Ticketing Agent",
        "Tourist Agent",
        "Safety Agent",
        "Personalization Agent",
        "General Q&A Agent",
    ] = Field(description="The specialist agent that should answer the user's latest request.")


KEYWORD_ROUTES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Safety Agent", ("emergency", "unsafe", "danger", "harassment", "crowd", "crowded", "medical", "lost", "help me", "night")),
    ("Ticketing Agent", ("ticket", "fare", "pass", "refund", "cancel", "booking", "book", "recharge", "payment", "upi", "price")),
    ("Real-Time Transit Agent", ("delay", "late", "platform", "live", "status", "cancelled", "disruption", "running", "arrival")),
    ("Tourist Agent", ("tour", "tourist", "hotel", "attraction", "visit", "food", "itinerary", "places", "sightseeing")),
    ("Personalization Agent", ("remember", "preference", "usual", "commute", "favorite", "alert", "notify", "profile")),
    ("Journey Planner Agent", ("route", "from", "to", "travel", "go", "reach", "fastest", "cheapest", "accessible", "station")),
)


def fallback_route(state: AgentState) -> str:
    text = latest_user_text(state.get("messages", [])).lower()
    for agent_name, keywords in KEYWORD_ROUTES:
        if any(keyword in text for keyword in keywords):
            return agent_name
    return "General Q&A Agent"


def supervisor_node(state: AgentState) -> dict:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", build_supervisor_prompt(MEMBERS)),
            ("placeholder", "{messages}"),
            ("system", "Select exactly one of these options: {options}"),
        ]
    ).partial(options=str(["FINISH"] + MEMBERS))

    try:
        chain = prompt | get_llm("llama-3.3-70b-versatile").with_structured_output(RouteResponse)
        result = chain.invoke({"messages": state.get("messages", [])})
        return {"next": result.next}
    except Exception:
        return {"next": fallback_route(state)}


def journey_planner_node(state: AgentState) -> dict:
    return run_agent("Journey Planner Agent", state)


def real_time_node(state: AgentState) -> dict:
    return run_agent("Real-Time Transit Agent", state)


def ticketing_node(state: AgentState) -> dict:
    return run_agent("Ticketing Agent", state)


def tourist_node(state: AgentState) -> dict:
    return run_agent("Tourist Agent", state)


def safety_node(state: AgentState) -> dict:
    return run_agent("Safety Agent", state)


def personalization_node(state: AgentState) -> dict:
    return run_agent("Personalization Agent", state)


def qa_node(state: AgentState) -> dict:
    return run_agent("General Q&A Agent", state)


workflow = StateGraph(AgentState)

workflow.add_node("Supervisor", supervisor_node)
workflow.add_node("Journey Planner Agent", journey_planner_node)
workflow.add_node("Real-Time Transit Agent", real_time_node)
workflow.add_node("Ticketing Agent", ticketing_node)
workflow.add_node("Tourist Agent", tourist_node)
workflow.add_node("Safety Agent", safety_node)
workflow.add_node("Personalization Agent", personalization_node)
workflow.add_node("General Q&A Agent", qa_node)

for member in MEMBERS:
    workflow.add_edge(member, END)

workflow.add_conditional_edges(
    "Supervisor",
    lambda state: state["next"],
    {
        "Journey Planner Agent": "Journey Planner Agent",
        "Real-Time Transit Agent": "Real-Time Transit Agent",
        "Ticketing Agent": "Ticketing Agent",
        "Tourist Agent": "Tourist Agent",
        "Safety Agent": "Safety Agent",
        "Personalization Agent": "Personalization Agent",
        "General Q&A Agent": "General Q&A Agent",
        "FINISH": END,
    },
)

workflow.set_entry_point("Supervisor")

app = workflow.compile()
