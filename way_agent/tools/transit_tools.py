from langchain_core.tools import tool

@tool
def check_train_delay(train_id: str) -> str:
    """Checks if a specific train is delayed."""
    return f"Train {train_id} is currently running on time."

@tool
def check_platform(train_id: str, station: str) -> str:
    """Checks the platform for a given train at a station."""
    return f"Train {train_id} will arrive at platform 4 at {station}."
