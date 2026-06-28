from langgraph.checkpoint.memory import MemorySaver

def get_checkpointer():
    """
    Returns an in-memory checkpointer for the LangGraph state.
    In a production app, this would use Redis or PostgreSQL.
    """
    return MemorySaver()
