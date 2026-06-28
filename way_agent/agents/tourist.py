from langchain_core.messages import AIMessage

def tourist_node(state: dict) -> dict:
    return {"messages": [AIMessage(content="Tourist Agent: I can help you find attractions, hotels, and plan your day. Where are we exploring?")]}
