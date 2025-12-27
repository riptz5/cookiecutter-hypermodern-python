{%- if cookiecutter.use_langgraph == 'y' %}
"""LangGraph agent graph definition."""
from langgraph.graph import StateGraph, START, END

from .state import AgentState
from .nodes import process_node, router_node


def create_agent_graph() -> StateGraph:
    """Create and compile the agent graph.
    
    Returns:
        Compiled LangGraph StateGraph
    """
    builder = StateGraph(AgentState)
    
    # Add nodes
    builder.add_node("process", process_node)
    
    # Add edges
    builder.add_edge(START, "process")
    builder.add_conditional_edges(
        "process",
        router_node,
        {"process": "process", "end": END}
    )
    
    return builder.compile()


# Default compiled graph
agent_graph = create_agent_graph()
{%- endif %}
