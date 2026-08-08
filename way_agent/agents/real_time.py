from agent_utils import run_enriched_agent


def real_time_node(state: dict) -> dict:
    return run_enriched_agent("Real-Time Transit Agent", state)
