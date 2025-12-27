{%- if cookiecutter.use_langgraph == 'y' %}
"""LangGraph agents for {{cookiecutter.friendly_name}}."""
from .graph import agent_graph, create_agent_graph
from .state import AgentState
from .nodes import process_node, router_node

__all__ = [
    "agent_graph",
    "create_agent_graph", 
    "AgentState",
    "process_node",
    "router_node",
]
{%- else %}
"""LangGraph agents placeholder.

Enable with: use_langgraph = 'y' in cookiecutter options.
"""
{%- endif %}
