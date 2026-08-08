from agent_utils import run_enriched_agent


def qa_node(state: dict) -> dict:
    return run_enriched_agent("General Q&A Agent", state)
