from langchain_core.messages import AIMessage
from prompts import build_agent_prompt
from llm_client import get_llm

def real_time_node(state: dict) -> dict:
    prompt = build_agent_prompt("Real-Time Transit Agent")
    llm = get_llm()
    chain = prompt | llm
    response = chain.invoke(state)
    return {"messages": [response]}
