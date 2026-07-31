from __future__ import annotations

from fastapi import FastAPI
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from agentic_graph import app as graph_app


api = FastAPI(title="WAY Transit Agentic AI API", version="2.0")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    user_id: str | None = None
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    agent: str


@api.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "way-agentic-ai"}


@api.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    state = {
        "messages": [HumanMessage(content=request.message)],
        "next": "Supervisor",
    }
    thread_id = request.session_id or f"user_{request.user_id or 'default'}"
    config = {"configurable": {"thread_id": thread_id}}
    result = graph_app.invoke(state, config=config)
    messages = result.get("messages", [])
    response = messages[-1].content if messages else "No response generated."

    return ChatResponse(
        response=response,
        agent=result.get("next", "Unknown"),
    )


app = api


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(api, host="0.0.0.0", port=8001)
