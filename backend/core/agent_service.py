from store import agents, agent_logs


def get_all_agents():
    """Return all known agents."""
    return list(agents.values())


def get_agent(agent_id: str):
    """Return one agent by ID, or None if it does not exist."""
    return agents.get(agent_id)


def get_logs(agent_id: str):
    """Return all logs for one agent."""
    return agent_logs.get(agent_id, [])