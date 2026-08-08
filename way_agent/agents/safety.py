from agent_utils import run_enriched_agent


def safety_node(state: dict) -> dict:
    return run_enriched_agent("Safety Agent", state)
