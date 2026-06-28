from langchain_core.messages import AIMessage

def personalization_node(state: dict) -> dict:
    return {"messages": [AIMessage(content="Personalization Agent: I can load your usual commute and set up your preferred routes.")]}
