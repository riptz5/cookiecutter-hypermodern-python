{%- if cookiecutter.use_langgraph == 'y' %}
"""State schemas for LangGraph agents.

This module defines TypedDict schemas for LangGraph state management.
States are used to pass data between nodes in the graph.

Key Schemas:
    - AgentState: Basic state with messages and context
    - SupervisorState: Extended state for multi-agent supervision
    - WorkflowState: State for complex multi-step workflows
"""
from typing import Annotated, Any, Dict, List, Optional, TypedDict
import operator


class AgentState(TypedDict, total=False):
    """Base state for LangGraph agents.
    
    Uses Annotated with operator.add to enable message accumulation
    across multiple node executions.
    
    Attributes:
        messages: List of conversation messages, appended via operator.add
        context: Optional context data for the agent
        task: The current task being processed
        agent_outputs: Results from executed agents
    """
    messages: Annotated[list, operator.add]
    context: dict
    task: str
    agent_outputs: Dict[str, Any]


class SupervisorState(TypedDict, total=False):
    """Extended state for supervisor agent orchestration.
    
    Used by the supervisor pattern where a central agent coordinates
    multiple worker agents.
    
    Attributes:
        messages: Conversation history
        task: The main task to be completed
        plan: List of steps to execute
        workers_needed: List of worker types required
        results: Results from each worker
        current_step: Current step index
        status: Overall workflow status
        final_output: Aggregated final result
    """
    messages: Annotated[list, operator.add]
    task: str
    plan: List[str]
    workers_needed: List[str]
    results: Annotated[Dict[str, Any], lambda a, b: {**a, **b}]
    current_step: int
    status: str  # pending, in_progress, completed, failed
    final_output: str


class WorkflowState(TypedDict, total=False):
    """State for complex multi-step workflows.
    
    Extends SupervisorState with additional tracking for
    branching workflows and error handling.
    
    Attributes:
        messages: Conversation history
        task: Main task
        workflow_id: Unique identifier for this workflow
        steps: List of workflow steps
        current_step: Current step being executed
        step_results: Results keyed by step name
        errors: Any errors encountered
        metadata: Additional workflow metadata
        should_retry: Flag for retry logic
        max_retries: Maximum retry attempts
        retry_count: Current retry count
    """
    messages: Annotated[list, operator.add]
    task: str
    workflow_id: str
    steps: List[str]
    current_step: str
    step_results: Dict[str, Any]
    errors: List[str]
    metadata: Dict[str, Any]
    should_retry: bool
    max_retries: int
    retry_count: int


def create_initial_state(task: str) -> AgentState:
    """Create initial AgentState with a task.
    
    Args:
        task: The task to process
    
    Returns:
        Initialized AgentState
    """
    return {
        "messages": [{"role": "user", "content": task}],
        "context": {},
        "task": task,
        "agent_outputs": {},
    }


def create_supervisor_state(task: str, workers: List[str] = None) -> SupervisorState:
    """Create initial SupervisorState.
    
    Args:
        task: The task to process
        workers: List of worker types needed (optional)
    
    Returns:
        Initialized SupervisorState
    """
    return {
        "messages": [{"role": "user", "content": task}],
        "task": task,
        "plan": [],
        "workers_needed": workers or [],
        "results": {},
        "current_step": 0,
        "status": "pending",
        "final_output": "",
    }
{%- endif %}
