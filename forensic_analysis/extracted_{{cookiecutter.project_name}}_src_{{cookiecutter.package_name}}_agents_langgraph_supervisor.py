{%- if cookiecutter.use_langgraph == 'y' and cookiecutter.use_google_adk == 'y' %}
"""Supervisor agent for multi-agent orchestration.

This module implements the SupervisorAgent pattern:
- Coordinates multiple worker agents
- Routes tasks to appropriate workers
- Executes workers in parallel when possible
- Aggregates results

Architecture:
    User Request
         │
         ▼
    ┌─────────────┐
    │ Supervisor  │ ◄── Decides which workers to use
    └─────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│Research│ │Analysis│  ◄── Workers execute in PARALLEL
└────────┘ └────────┘
    │         │
    └────┬────┘
         ▼
    ┌─────────────┐
    │ Aggregator  │ ◄── Combines results
    └─────────────┘
         │
         ▼
    Final Response

Uses LangGraph's Send() for true parallel execution.
"""
import asyncio
import os
from typing import Any, Callable, Dict, List, Literal, Optional, TypedDict, Annotated
from dataclasses import dataclass
import operator
import logging

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

try:
    from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False

from ..adk.workers import WorkerAgent, create_worker, WorkerPool
from ..base import AgentContext, AgentResult

logger = logging.getLogger(__name__)


# ============================================================================
# State Definitions
# ============================================================================

class SupervisorState(TypedDict):
    """State for supervisor workflow.
    
    Attributes:
        task: Original task from user
        messages: Conversation messages (append-only)
        workers_to_use: List of worker types to execute
        worker_results: Results from each worker
        final_output: Aggregated final output
        metadata: Additional metadata
    """
    task: str
    messages: Annotated[List[Any], operator.add]  # Append-only
    workers_to_use: List[str]
    worker_results: Dict[str, str]
    final_output: str
    metadata: Dict[str, Any]


class WorkerState(TypedDict):
    """State for individual worker execution."""
    task: str
    worker_type: str


# ============================================================================
# Supervisor Agent
# ============================================================================

class SupervisorAgent:
    """Supervisor that orchestrates multiple worker agents.
    
    Implements the supervisor pattern where:
    1. Supervisor analyzes the task
    2. Decides which workers to invoke
    3. Workers execute in PARALLEL
    4. Results are aggregated
    
    Example:
        >>> supervisor = SupervisorAgent()
        >>> result = await supervisor.run("Research AI trends and write a summary")
        >>> print(result["final_output"])
    
    Parallel Execution:
        Uses LangGraph's Send() to fan out to multiple workers.
        This is REAL parallel execution, not simulated.
    """
    
    # Available worker types
    WORKER_TYPES = ["research", "analysis", "writer", "code"]
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        enable_all_workers: bool = True,
        custom_workers: Optional[Dict[str, WorkerAgent]] = None
    ):
        """Initialize supervisor.
        
        Args:
            api_key: Optional API key for workers
            enable_all_workers: Whether to create all default workers
            custom_workers: Custom workers to use instead of defaults
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY required for supervisor")
        
        # Initialize workers
        if custom_workers:
            self.workers = custom_workers
        elif enable_all_workers:
            self.workers = self._create_default_workers()
        else:
            self.workers = {}
        
        # Build the supervisor graph
        self.graph = self._build_graph()
        
        logger.info(f"Supervisor initialized with {len(self.workers)} workers")
    
    def _create_default_workers(self) -> Dict[str, WorkerAgent]:
        """Create default worker agents.
        
        Returns:
            Dictionary of worker type -> WorkerAgent
        """
        workers = {}
        for worker_type in self.WORKER_TYPES:
            try:
                workers[worker_type] = create_worker(
                    worker_type,
                    api_key=self.api_key
                )
                logger.debug(f"Created {worker_type} worker")
            except Exception as e:
                logger.warning(f"Could not create {worker_type} worker: {e}")
        
        return workers
    
    def _build_graph(self) -> StateGraph:
        """Build the supervisor LangGraph.
        
        Graph structure:
            START -> analyze_task -> [route_to_workers] -> worker_nodes -> aggregate -> END
            
        The route_to_workers node uses Send() to fan out to multiple workers
        for true parallel execution.
        
        Returns:
            Compiled StateGraph
        """
        builder = StateGraph(SupervisorState)
        
        # Add nodes
        builder.add_node("analyze_task", self._analyze_task_node)
        builder.add_node("aggregate", self._aggregate_node)
        
        # Add worker nodes dynamically
        for worker_type in self.workers:
            builder.add_node(
                f"worker_{worker_type}",
                self._create_worker_node(worker_type)
            )
        
        # Add edges
        builder.add_edge(START, "analyze_task")
        
        # Conditional routing to workers (parallel via Send)
        builder.add_conditional_edges(
            "analyze_task",
            self._route_to_workers,
            # Dynamic mapping based on available workers
            {f"worker_{wt}": f"worker_{wt}" for wt in self.workers}
        )
        
        # All workers lead to aggregate
        for worker_type in self.workers:
            builder.add_edge(f"worker_{worker_type}", "aggregate")
        
        # Aggregate leads to end
        builder.add_edge("aggregate", END)
        
        return builder.compile()
    
    async def _analyze_task_node(self, state: SupervisorState) -> Dict[str, Any]:
        """Analyze task and decide which workers to use.
        
        Uses a worker (analysis) to understand the task and
        determine which specialized workers should handle it.
        
        Args:
            state: Current supervisor state
            
        Returns:
            State update with workers_to_use
        """
        task = state["task"]
        
        logger.info(f"Analyzing task: {task[:100]}...")
        
        # Use analysis worker to determine which workers to use
        analysis_prompt = f"""Analyze this task and determine which specialized workers should handle it.

Task: {task}

Available workers:
- research: For gathering information, fact-finding, searching
- analysis: For analyzing data, comparing options, evaluating
- writer: For creating documentation, summaries, reports
- code: For writing code, debugging, refactoring

Respond with ONLY a comma-separated list of worker names (e.g., "research,writer").
Choose workers that would be most helpful for this specific task."""
        
        # Get recommendation from analysis worker
        if "analysis" in self.workers:
            result = await self.workers["analysis"].run(analysis_prompt)
            response = result.output if result.success else "research"
        else:
            # Default to research if no analysis worker
            response = "research"
        
        # Parse response to get worker list
        workers_to_use = self._parse_worker_selection(response)
        
        # Ensure at least one worker
        if not workers_to_use:
            workers_to_use = ["research"]
        
        logger.info(f"Selected workers: {workers_to_use}")
        
        return {
            "workers_to_use": workers_to_use,
            "metadata": {"analysis": response},
        }
    
    def _parse_worker_selection(self, response: str) -> List[str]:
        """Parse worker selection from analysis response.
        
        Args:
            response: Analysis response string
            
        Returns:
            List of valid worker types
        """
        # Extract worker names from response
        response_lower = response.lower()
        selected = []
        
        for worker_type in self.WORKER_TYPES:
            if worker_type in response_lower and worker_type in self.workers:
                selected.append(worker_type)
        
        return selected
    
    def _route_to_workers(self, state: SupervisorState) -> List[Send]:
        """Route task to selected workers using Send() for parallel execution.
        
        This is the key to true parallel execution. Each Send() creates
        a new execution branch that runs concurrently.
        
        Args:
            state: Current supervisor state
            
        Returns:
            List of Send objects for parallel execution
        """
        workers_to_use = state.get("workers_to_use", ["research"])
        task = state["task"]
        
        sends = []
        for worker_type in workers_to_use:
            if worker_type in self.workers:
                sends.append(Send(
                    f"worker_{worker_type}",
                    {"task": task, "worker_type": worker_type}
                ))
        
        logger.info(f"Routing to {len(sends)} workers in PARALLEL")
        return sends
    
    def _create_worker_node(self, worker_type: str) -> Callable:
        """Create a node function for a specific worker.
        
        Args:
            worker_type: Type of worker
            
        Returns:
            Async node function
        """
        async def worker_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """Execute worker and return results."""
            task = state.get("task", "")
            
            logger.debug(f"Executing {worker_type} worker...")
            
            worker = self.workers.get(worker_type)
            if not worker:
                return {
                    "worker_results": {worker_type: f"Worker {worker_type} not available"},
                }
            
            # Execute worker (REAL API call)
            result = await worker.run(task)
            
            output = result.output if result.success else f"Error: {result.error}"
            
            logger.debug(f"{worker_type} completed: {output[:100]}...")
            
            return {
                "worker_results": {worker_type: output},
            }
        
        return worker_node
    
    async def _aggregate_node(self, state: SupervisorState) -> Dict[str, Any]:
        """Aggregate results from all workers.
        
        Uses writer worker to synthesize results into coherent output.
        
        Args:
            state: Current supervisor state with worker_results
            
        Returns:
            State update with final_output
        """
        worker_results = state.get("worker_results", {})
        task = state.get("task", "")
        
        logger.info(f"Aggregating results from {len(worker_results)} workers")
        
        if not worker_results:
            return {"final_output": "No results from workers"}
        
        # Build aggregation prompt
        results_text = "\n\n".join([
            f"=== {worker_type.upper()} RESULTS ===\n{result}"
            for worker_type, result in worker_results.items()
        ])
        
        aggregation_prompt = f"""Synthesize the following results from multiple specialized agents into a coherent, well-structured response.

ORIGINAL TASK: {task}

WORKER RESULTS:
{results_text}

Create a unified response that:
1. Combines the insights from all workers
2. Removes any redundancy
3. Presents information in a logical order
4. Addresses the original task directly"""
        
        # Use writer worker for aggregation
        if "writer" in self.workers:
            result = await self.workers["writer"].run(aggregation_prompt)
            final_output = result.output if result.success else results_text
        else:
            # Fall back to concatenated results
            final_output = results_text
        
        return {
            "final_output": final_output,
            "messages": [{"role": "assistant", "content": final_output}],
        }
    
    async def run(self, task: str) -> Dict[str, Any]:
        """Execute the supervisor with a task.
        
        Args:
            task: Task to execute
            
        Returns:
            Dictionary with final_output and metadata
            
        Example:
            >>> supervisor = SupervisorAgent()
            >>> result = await supervisor.run("What are the latest AI trends?")
            >>> print(result["final_output"])
        """
        logger.info(f"Supervisor executing: {task[:100]}...")
        
        # Initialize state
        initial_state: SupervisorState = {
            "task": task,
            "messages": [{"role": "user", "content": task}],
            "workers_to_use": [],
            "worker_results": {},
            "final_output": "",
            "metadata": {},
        }
        
        # Execute graph
        import time
        start = time.time()
        
        result = await self.graph.ainvoke(initial_state)
        
        elapsed = time.time() - start
        
        logger.info(f"Supervisor completed in {elapsed:.2f}s")
        
        # Add timing to metadata
        result["metadata"]["execution_time_s"] = elapsed
        result["metadata"]["workers_executed"] = result.get("workers_to_use", [])
        
        return result
    
    def get_available_workers(self) -> List[str]:
        """Get list of available worker types.
        
        Returns:
            List of worker type names
        """
        return list(self.workers.keys())
    
    def add_worker(self, worker_type: str, worker: WorkerAgent) -> None:
        """Add or replace a worker.
        
        Args:
            worker_type: Worker type identifier
            worker: WorkerAgent instance
        """
        self.workers[worker_type] = worker
        # Rebuild graph to include new worker
        self.graph = self._build_graph()
        logger.info(f"Added worker: {worker_type}")


# ============================================================================
# Convenience Functions
# ============================================================================

async def run_supervised(
    task: str,
    api_key: Optional[str] = None
) -> str:
    """Quick supervised execution.
    
    Args:
        task: Task to execute
        api_key: Optional API key
        
    Returns:
        Final output string
        
    Example:
        >>> result = await run_supervised("Research Python async patterns")
        >>> print(result)
    """
    supervisor = SupervisorAgent(api_key=api_key)
    result = await supervisor.run(task)
    return result.get("final_output", "No output")


def create_supervisor(
    api_key: Optional[str] = None,
    workers: Optional[List[str]] = None
) -> SupervisorAgent:
    """Create a configured supervisor.
    
    Args:
        api_key: Optional API key
        workers: Optional list of worker types to enable
        
    Returns:
        Configured SupervisorAgent
    """
    if workers:
        # Create only specified workers
        custom_workers = {
            wt: create_worker(wt, api_key=api_key)
            for wt in workers
        }
        return SupervisorAgent(
            api_key=api_key,
            enable_all_workers=False,
            custom_workers=custom_workers
        )
    
    return SupervisorAgent(api_key=api_key)
{%- else %}
"""Supervisor module placeholder.

This module requires both use_langgraph=y and use_google_adk=y.
"""

class SupervisorAgent:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "SupervisorAgent requires both use_langgraph=y and use_google_adk=y"
        )
{%- endif %}
