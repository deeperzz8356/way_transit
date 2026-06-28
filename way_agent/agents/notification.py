from langchain_core.messages import AIMessage

def notification_node(state: dict) -> dict:
    return {"messages": [AIMessage(content="Notification Agent: I handle proactive alerts like delays and missed connections.")]}
