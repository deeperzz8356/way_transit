from langchain_core.messages import AIMessage

def safety_node(state: dict) -> dict:
    return {"messages": [AIMessage(content="Safety Agent: I monitor crowd density and provide safe, accessible routes.")]}
