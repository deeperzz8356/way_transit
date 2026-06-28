from langchain_core.messages import AIMessage

def qa_node(state: dict) -> dict:
    return {"messages": [AIMessage(content="General Q&A Agent: I can answer questions about transit rules, policies, and FAQs.")]}
