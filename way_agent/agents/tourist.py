from agent_utils import run_enriched_agent


def tourist_node(state: dict) -> dict:
    return run_enriched_agent("Tourist Agent", state)
