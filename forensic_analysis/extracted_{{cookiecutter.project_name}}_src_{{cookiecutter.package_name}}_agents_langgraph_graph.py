{%- if cookiecutter.use_langgraph == 'y' %}
"""LangGraph agent graph definitions.

This module provides pre-built LangGraph graphs for common patterns:
- Simple processing graph
- Supervisor pattern for multi-agent orchestration
- Map-reduce pattern for parallel execution

All graphs use REAL Gemini calls via the ADK integration.
"""
import logging
from typing import Any, Dict, List, Optional

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from .state import AgentState, SupervisorState, create_initial_state, create_supervisor_state
from .nodes import (
    process_node,
    router_node,
    analyzer_node,
    aggregator_node,
    create_worker_node,
    should_continue,
)

logger = logging.getLogger(__name__)


def create_simple_graph() -> StateGraph:
    """Create a simple processing graph.
    
    Graph structure:
        START -> process -> router -> (process | END)
    
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
        {"process": "process", "end": END, "retry": "process"}
    )
    
    return builder.compile()


def create_supervisor_graph(
    workers: Optional[List[str]] = None
) -> StateGraph:
    """Create a supervisor graph for multi-agent orchestration.
    
    The supervisor analyzes tasks, delegates to workers, and aggregates results.
    Workers execute in PARALLEL via LangGraph's Send mechanism.
    
    Graph structure:
        START -> analyze -> route_to_workers -> [worker nodes] -> aggregate -> END
    
    Args:
        workers: List of worker types to include. Default: all types.
    
    Returns:
        Compiled LangGraph StateGraph
    
    Example:
        >>> graph = create_supervisor_graph(["research", "writer"])
        >>> result = await graph.ainvoke(create_supervisor_state("Write about AI"))
    """
    if workers is None:
        workers = ["research", "analysis", "writer", "code", "planner", "critic"]
    
    builder = StateGraph(SupervisorState)
    
    # Add analyzer node
    builder.add_node("analyze", analyzer_node)
    
    # Add worker nodes
    for worker in workers:
        builder.add_node(worker, create_worker_node(worker))
    
    # Add aggregator node
    builder.add_node("aggregate", aggregator_node)
    
    # Edges: START -> analyze
    builder.add_edge(START, "analyze")
    
    # Conditional edges from analyze to workers (parallel)
    def route_to_workers(state: SupervisorState) -> List[Send]:
        """Route to workers in parallel using Send."""
        needed = state.get("workers_needed", [])
        return [Send(w, state) for w in needed if w in workers]
    
    builder.add_conditional_edges(
        "analyze",
        route_to_workers,
        # Empty dict means use Send routing
    )
    
    # All workers lead to aggregate
    for worker in workers:
        builder.add_edge(worker, "aggregate")
    
    # Aggregate to END
    builder.add_edge("aggregate", END)
    
    return builder.compile()


def create_sequential_graph(steps: List[str]) -> StateGraph:
    """Create a sequential processing graph.
    
    Each step processes the output of the previous step.
    
    Args:
        steps: List of step names (each will be a process node)
    
    Returns:
        Compiled LangGraph StateGraph
    
    Example:
        >>> graph = create_sequential_graph(["research", "analyze", "write"])
    """
    builder = StateGraph(AgentState)
    
    # Add nodes for each step
    for step in steps:
        builder.add_node(step, process_node)
    
    # Chain edges
    builder.add_edge(START, steps[0])
    for i in range(len(steps) - 1):
        builder.add_edge(steps[i], steps[i + 1])
    builder.add_edge(steps[-1], END)
    
    return builder.compile()


async def run_simple(task: str) -> Dict[str, Any]:
    """Run a task through the simple graph.
    
    Convenience function for quick execution.
    
    Args:
        task: Task to process
    
    Returns:
        Final state dict
    """
    graph = create_simple_graph()
    initial_state = create_initial_state(task)
    return await graph.ainvoke(initial_state)


async def run_supervisor(
    task: str,
    workers: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Run a task through the supervisor graph.
    
    This executes multiple workers in PARALLEL and aggregates results.
    
    Args:
        task: Task to process
        workers: Optional list of workers to use
    
    Returns:
        Final state dict with results and final_output
    
    Example:
        >>> result = await run_supervisor("Research AI and write a summary")
        >>> print(result["final_output"])
    """
    graph = create_supervisor_graph(workers)
    initial_state = create_supervisor_state(task, workers)
    return await graph.ainvoke(initial_state)


# Default compiled graphs (lazy initialization)
_simple_graph = None
_supervisor_graph = None


def get_simple_graph() -> StateGraph:
    """Get the default simple graph (singleton)."""
    global _simple_graph
    if _simple_graph is None:
        _simple_graph = create_simple_graph()
    return _simple_graph


def get_supervisor_graph() -> StateGraph:
    """Get the default supervisor graph (singleton)."""
    global _supervisor_graph
    if _supervisor_graph is None:
        _supervisor_graph = create_supervisor_graph()
    return _supervisor_graph


# Legacy alias for backward compatibility
agent_graph = None


def _init_default_graph():
    """Initialize the default agent graph."""
    global agent_graph
    if agent_graph is None:
        agent_graph = get_simple_graph()


# Call initialization at module load
_init_default_graph()
{%- endif %}
