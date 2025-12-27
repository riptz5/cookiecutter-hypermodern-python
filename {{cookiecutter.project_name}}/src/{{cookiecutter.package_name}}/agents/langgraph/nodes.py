{%- if cookiecutter.use_langgraph == 'y' %}
"""Node functions for LangGraph agents."""
from .state import AgentState


def process_node(state: AgentState) -> dict:
    """Example processing node.
    
    Args:
        state: Current agent state
        
    Returns:
        State update dictionary
    """
    return {"messages": [{"role": "assistant", "content": "Processed"}]}


def router_node(state: AgentState) -> str:
    """Example router node for conditional edges.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node name
    """
    if state.get("context", {}).get("done"):
        return "end"
    return "process"
{%- endif %}
