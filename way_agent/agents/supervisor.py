from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from llm import get_llm

members = [
    "Journey Planner Agent",
    "Real-Time Transit Agent",
    "Ticketing Agent",
    "Tourist Agent",
    "Safety Agent",
    "Personalization Agent",
    "General Q&A Agent"
]

system_prompt = (
    "You are a supervisor tasked with managing a conversation between the"
    " following workers: {members}. Given the following user request,"
    " respond with the worker to act next. Each worker will perform a"
    " task and respond with their results and status. When finished,"
    " respond with FINISH."
)

options = ["FINISH"] + members

class RouteResponse(BaseModel):
    next: Literal[
        "FINISH", 
        "Journey Planner Agent", 
        "Real-Time Transit Agent", 
        "Ticketing Agent", 
        "Tourist Agent", 
        "Safety Agent", 
        "Personalization Agent", 
        "General Q&A Agent"
    ] = Field(
        description="The next agent to route to, or FINISH if the user intent has been handled or no agent applies."
    )

def create_supervisor():
    llm = get_llm("llama-3.3-70b-versatile")
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("placeholder", "{messages}"),
        (
            "system",
            "Given the conversation above, who should act next?"
            " Or should we FINISH? Select one of: {options}",
        ),
    ]).partial(options=str(options), members=", ".join(members))
    
    # We use function calling/structured output to guarantee routing
    supervisor_chain = prompt | llm.with_structured_output(RouteResponse)
    
    return supervisor_chain

def supervisor_node(state: dict) -> dict:
    supervisor_chain = create_supervisor()
    result = supervisor_chain.invoke(state)
    return {"next": result.next}
