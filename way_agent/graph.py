from typing import Annotated, Sequence, TypedDict
import operator
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END

from agents.supervisor import supervisor_node
from agents.journey_planner import journey_planner_node
from agents.real_time import real_time_node
from agents.ticketing import ticketing_node
from agents.tourist import tourist_node
from agents.safety import safety_node
from agents.personalization import personalization_node
from agents.qa_agent import qa_node

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# Build the Graph
workflow = StateGraph(AgentState)

workflow.add_node("Supervisor", supervisor_node)
workflow.add_node("Journey Planner Agent", journey_planner_node)
workflow.add_node("Real-Time Transit Agent", real_time_node)
workflow.add_node("Ticketing Agent", ticketing_node)
workflow.add_node("Tourist Agent", tourist_node)
workflow.add_node("Safety Agent", safety_node)
workflow.add_node("Personalization Agent", personalization_node)
workflow.add_node("General Q&A Agent", qa_node)

# Add edges
for agent in [
    "Journey Planner Agent",
    "Real-Time Transit Agent",
    "Ticketing Agent",
    "Tourist Agent",
    "Safety Agent",
    "Personalization Agent",
    "General Q&A Agent"
]:
    workflow.add_edge(agent, END)

workflow.add_conditional_edges(
    "Supervisor",
    lambda x: x["next"],
    {
        "Journey Planner Agent": "Journey Planner Agent",
        "Real-Time Transit Agent": "Real-Time Transit Agent",
        "Ticketing Agent": "Ticketing Agent",
        "Tourist Agent": "Tourist Agent",
        "Safety Agent": "Safety Agent",
        "Personalization Agent": "Personalization Agent",
        "General Q&A Agent": "General Q&A Agent",
        "FINISH": END
    }
)
workflow.set_entry_point("Supervisor")

app = workflow.compile()
