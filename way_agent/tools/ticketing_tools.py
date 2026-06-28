from langchain_core.tools import tool

@tool
def calculate_fare(origin: str, destination: str) -> str:
    """Calculates the fare between two stations."""
    return f"The standard fare from {origin} to {destination} is $2.50."

@tool
def buy_pass(pass_type: str, user_id: str) -> str:
    """Mock purchasing a pass."""
    return f"Successfully purchased {pass_type} pass for user {user_id}. Mock payment processed."
