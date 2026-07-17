from langchain_core.messages import AIMessage
from prompts import build_agent_prompt
from llm_client import get_llm

def qa_node(state: dict) -> dict:
    prompt = build_agent_prompt("General Q&A Agent")
    llm = get_llm()
    chain = prompt | llm
    
    # We pass the state to the chain. The state contains 'messages' and 'db_context'.
    response = chain.invoke(state)
    
    return {"messages": [response]}
