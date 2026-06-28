from langchain_core.messages import AIMessage

def ticketing_node(state: dict) -> dict:
    return {"messages": [AIMessage(content="Ticketing Agent: I can help you buy tickets, recharge cards, or get pass recommendations.")]}
