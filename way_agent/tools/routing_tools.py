from langchain_core.tools import tool

@tool
def get_fastest_route(origin: str, destination: str) -> str:
    """Returns the fastest route between two locations."""
    return f"The fastest route from {origin} to {destination} is via Metro Line 3, taking approximately 25 minutes."

@tool
def get_cheapest_route(origin: str, destination: str) -> str:
    """Returns the cheapest route between two locations."""
    return f"The cheapest route from {origin} to {destination} is via City Bus 45, costing $1.50 and taking 45 minutes."
