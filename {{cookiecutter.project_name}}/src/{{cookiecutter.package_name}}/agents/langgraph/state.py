{%- if cookiecutter.use_langgraph == 'y' %}
"""State schemas for LangGraph agents."""
from typing import Annotated, TypedDict
import operator


class AgentState(TypedDict):
    """Base state for LangGraph agents.
    
    Attributes:
        messages: List of conversation messages, appended via operator.add
        context: Optional context data for the agent
    """
    messages: Annotated[list, operator.add]
    context: dict
{%- endif %}
