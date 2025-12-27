{%- if cookiecutter.use_google_adk == 'y' %}
"""GENESIS Autopoietic System Components.

This package contains the self-programming core of the GENESIS system:

- MetaAgent: Agent that creates and evolves other agents
- GeneticMemory: Persistent storage for agent genomes (Firestore)
- AgentExecutor: Dynamic deployment to Cloud Run

Autopoiesis (from Greek: self-creation):
    The system can create, modify, and improve itself without external intervention.
    The MetaAgent uses Gemini to generate Python code for new agents, which are
    then stored in GeneticMemory and deployed via AgentExecutor.

Example:
    >>> from .meta import MetaAgent, GeneticMemory
    >>> 
    >>> memory = GeneticMemory()
    >>> meta = MetaAgent(memory=memory)
    >>> 
    >>> # Create a new agent dynamically
    >>> spec = AgentSpec(name="researcher", role="Research expert", ...)
    >>> new_agent = await meta.create_agent(spec)
    >>> 
    >>> # Evolve based on feedback
    >>> evolved = await meta.evolve_agent("researcher", "Needs better citations")
"""
from .meta_agent import MetaAgent, Mutation
from .genetic_memory import GeneticMemory, AgentGenome, EvolutionEvent

__all__ = [
    "MetaAgent",
    "Mutation",
    "GeneticMemory",
    "AgentGenome",
    "EvolutionEvent",
]
{%- else %}
"""Meta-agent components (requires use_google_adk=y)."""
{%- endif %}
