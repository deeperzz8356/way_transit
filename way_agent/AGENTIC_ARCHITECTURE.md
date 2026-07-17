# WAY Transit Agentic AI Architecture

## Run

```bash
cd way_agent
uvicorn agentic_main:app --reload --port 8001
```

## Request Flow

1. `agentic_main.py` receives `/chat`.
2. `agentic_graph.py` sends the message to the Supervisor.
3. The Supervisor selects one specialist agent.
4. The selected worker uses the shared prompt contract in `prompts.py`.
5. `agent_runner.py` calls the LLM and falls back to deterministic guidance if local setup is missing.

## Prompt Structure

All agents share:

- WAY Agent identity
- Transit safety guardrails
- Response contract
- Specialist mission
- Responsibilities
- Handoff boundaries
- Tool policy

This keeps the system consistent while allowing each agent to focus on its own job.

## Agents

- `Journey Planner Agent`: routes, transfers, trip preferences, accessibility.
- `Real-Time Transit Agent`: delays, platforms, live status, disruptions.
- `Ticketing Agent`: fares, passes, booking, recharge, refunds.
- `Tourist Agent`: attractions, hotels, food, visitor itineraries.
- `Safety Agent`: emergencies, crowding, harassment, accessibility risk.
- `Personalization Agent`: commute preferences, alerts, saved travel habits.
- `General Q&A Agent`: policies, app help, broad transit questions.

## Extending

Add new agents by updating:

1. `AGENT_SPECS` in `prompts.py`.
2. `MEMBERS`, `RouteResponse`, and graph nodes in `agentic_graph.py`.
3. Optional tools in `tools/`.
