from agent_utils import run_enriched_agent


def journey_planner_node(state: dict) -> dict:
    return run_enriched_agent("Journey Planner Agent", state)
