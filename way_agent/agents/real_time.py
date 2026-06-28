from langchain_core.messages import AIMessage

def real_time_node(state: dict) -> dict:
    return {"messages": [AIMessage(content="Real-Time Agent: I track live trains, buses, delays, and platform changes. What do you need to check?")]}
