from __future__ import annotations

import os

from dotenv import load_dotenv


dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path)


def get_llm(model_name: str = "llama-3.1-8b-instant"):
    try:
        from langchain_groq import ChatGroq
    except ImportError as exc:
        raise RuntimeError("Install langchain-groq to enable LLM responses.") from exc

    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("Set GROQ_API_KEY to enable LLM responses.")

    return ChatGroq(model=model_name, temperature=0)
