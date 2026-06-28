from langchain_core.messages import AIMessage

def journey_planner_node(state: dict) -> dict:
    return {"messages": [AIMessage(content="Journey Planner Agent: I can help you find the fastest, cheapest, or most accessible route. What is your destination?")]}
