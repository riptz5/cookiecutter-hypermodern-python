{%- if cookiecutter.use_langgraph == 'y' %}
"""LangGraph agent workflow integration.

This module provides LangGraph-based workflow orchestration:
- SupervisorAgent for multi-agent coordination
- Pre-built nodes for common operations
- State management
- Conditional routing

Quick Start:
    >>> from {{cookiecutter.package_name}}.agents.langgraph import SupervisorAgent
    >>> 
    >>> supervisor = SupervisorAgent()
    >>> result = await supervisor.run("Research and summarize AI trends")
    >>> print(result["final_output"])

Components:
- supervisor: Multi-agent supervisor with parallel execution
- nodes: Pre-built node functions (Gemini, ADK, etc.)
- state: State schemas for workflows
- graph: Graph building utilities
"""
from .state import AgentState
from .nodes import (
    gemini_node,
    process_node,
    router_node,
    adk_node,
    task_analyzer_router,
    create_gemini_node,
    create_worker_node,
)
from .graph import create_agent_graph

# Import supervisor only if both ADK and LangGraph are available
{%- if cookiecutter.use_google_adk == 'y' %}
from .supervisor import (
    SupervisorAgent,
    SupervisorState,
    run_supervised,
    create_supervisor,
)

__all__ = [
    # State
    "AgentState",
    # Nodes
    "gemini_node",
    "process_node",
    "router_node",
    "adk_node",
    "task_analyzer_router",
    "create_gemini_node",
    "create_worker_node",
    # Graph
    "create_agent_graph",
    # Supervisor
    "SupervisorAgent",
    "SupervisorState",
    "run_supervised",
    "create_supervisor",
]
{%- else %}
__all__ = [
    "AgentState",
    "gemini_node",
    "process_node",
    "router_node",
    "create_agent_graph",
]
{%- endif %}
{%- else %}
"""LangGraph placeholder - enable with use_langgraph=y."""
{%- endif %}
