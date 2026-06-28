import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path)

def get_llm(model_name: str = "llama-3.1-8b-instant"):
    """
    Get the Groq LLM instance.
    Uses GROQ_API_KEY from environment variables.
    """
    return ChatGroq(model=model_name, temperature=0)
