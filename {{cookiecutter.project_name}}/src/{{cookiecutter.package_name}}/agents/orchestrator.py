"""Agent orchestrator for parallel and sequential execution.

<<<<<<< Current (Your changes)
This module provides the core execution engine for the GENESIS system:
- Parallel execution of multiple agents
- Sequential pipelines with data passing
- Map-reduce patterns for large workloads
- Integration with BaseAgent and ADKLangGraphBridge

The orchestrator does NOT simulate anything - all execution is real.
Agents are executed via their run() method, which makes actual LLM calls.
"""
import asyncio
import logging
=======
This module provides:
- AgentOrchestrator: Base orchestrator for task management
- ProductionOrchestrator: Full multi-agent system with REAL API calls

ProductionOrchestrator is the recommended entry point for production use.
"""
import asyncio
import os
>>>>>>> Incoming (Background Agent changes)
import time
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

from .base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Execution modes for agent orchestration."""
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    MAP_REDUCE = "map_reduce"


@dataclass
class Task:
    """Task to be executed by an agent.
    
    Attributes:
        name: Task identifier
        input_data: Input data for the task
        agent_fn: Function to execute (can be sync or async)
        metadata: Optional metadata
    """
    name: str
    input_data: Any
    agent_fn: Callable
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    """Result from task execution.
    
    Attributes:
        task_name: Name of the executed task
        output: Task output
        success: Whether task succeeded
        error: Error message if failed
        metadata: Result metadata
    """
    task_name: str
    output: Any
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentOrchestrator:
    """Orchestrates multiple agents for parallel and sequential execution.
    
    Example:
        >>> orchestrator = AgentOrchestrator()
        >>> 
        >>> # Parallel execution
        >>> results = await orchestrator.execute_parallel([
        ...     Task("research", "topic A", research_agent),
        ...     Task("analyze", "data B", analyze_agent),
        ... ])
        >>> 
        >>> # Sequential pipeline
        >>> result = await orchestrator.execute_pipeline([
        ...     Task("step1", input_data, agent1),
        ...     Task("step2", None, agent2),  # Uses output from step1
        ... ])
    """
    
    def __init__(self, max_concurrent: int = 10):
        """Initialize orchestrator.
        
        Args:
            max_concurrent: Maximum number of concurrent tasks
        """
        self.max_concurrent = max_concurrent
        self._results: Dict[str, TaskResult] = {}
    
    async def execute_parallel(
        self,
        tasks: List[Task],
        timeout: Optional[float] = None
    ) -> List[TaskResult]:
        """Execute tasks in parallel.
        
        Args:
            tasks: List of tasks to execute
            timeout: Optional timeout in seconds
            
        Returns:
            List of task results in order
            
        Example:
            >>> tasks = [
            ...     Task("task1", {"query": "X"}, agent1.run),
            ...     Task("task2", {"query": "Y"}, agent2.run),
            ...     Task("task3", {"query": "Z"}, agent3.run),
            ... ]
            >>> results = await orchestrator.execute_parallel(tasks)
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def _execute_with_semaphore(task: Task) -> TaskResult:
            async with semaphore:
                return await self._execute_task(task)
        
        try:
            results = await asyncio.wait_for(
                asyncio.gather(
                    *[_execute_with_semaphore(task) for task in tasks],
                    return_exceptions=True
                ),
                timeout=timeout
            )
            
            # Convert exceptions to TaskResult
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append(TaskResult(
                        task_name=tasks[i].name,
                        output=None,
                        success=False,
                        error=str(result)
                    ))
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except asyncio.TimeoutError:
            return [
                TaskResult(
                    task_name=task.name,
                    output=None,
                    success=False,
                    error="Timeout exceeded"
                )
                for task in tasks
            ]
    
    async def execute_pipeline(
        self,
        tasks: List[Task],
        initial_input: Any = None
    ) -> TaskResult:
        """Execute tasks sequentially, passing output to next task.
        
        Args:
            tasks: List of tasks to execute in order
            initial_input: Initial input for first task
            
        Returns:
            Final task result
            
        Example:
            >>> tasks = [
            ...     Task("research", None, research_agent.run),
            ...     Task("write", None, writer_agent.run),
            ...     Task("review", None, reviewer_agent.run),
            ... ]
            >>> result = await orchestrator.execute_pipeline(
            ...     tasks,
            ...     initial_input={"topic": "AI"}
            ... )
        """
        current_input = initial_input
        
        for task in tasks:
            # Use task's input_data if provided, otherwise use pipeline output
            task_input = task.input_data if task.input_data is not None else current_input
            
            # Create new task with current input
            current_task = Task(
                name=task.name,
                input_data=task_input,
                agent_fn=task.agent_fn,
                metadata=task.metadata
            )
            
            result = await self._execute_task(current_task)
            
            if not result.success:
                # Pipeline failed, return error
                return result
            
            # Pass output to next task
            current_input = result.output
        
        # Return final result
        return TaskResult(
            task_name="pipeline",
            output=current_input,
            success=True,
            metadata={"steps": [t.name for t in tasks]}
        )
    
    async def execute_map_reduce(
        self,
        data_items: List[Any],
        map_fn: Callable,
        reduce_fn: Callable,
        map_task_name: str = "map",
        reduce_task_name: str = "reduce"
    ) -> TaskResult:
        """Execute map-reduce pattern.
        
        Args:
            data_items: List of items to map over
            map_fn: Function to apply to each item (parallel)
            reduce_fn: Function to aggregate results
            map_task_name: Name prefix for map tasks
            reduce_task_name: Name for reduce task
            
        Returns:
            Reduced result
            
        Example:
            >>> # Process 100 documents in parallel, then summarize
            >>> result = await orchestrator.execute_map_reduce(
            ...     data_items=documents,
            ...     map_fn=lambda doc: analyze_document(doc),
            ...     reduce_fn=lambda results: summarize_all(results)
            ... )
        """
        # Map phase (parallel)
        map_tasks = [
            Task(
                name=f"{map_task_name}_{i}",
                input_data=item,
                agent_fn=map_fn
            )
            for i, item in enumerate(data_items)
        ]
        
        map_results = await self.execute_parallel(map_tasks)
        
        # Check for failures
        failed = [r for r in map_results if not r.success]
        if failed:
            return TaskResult(
                task_name=reduce_task_name,
                output=None,
                success=False,
                error=f"Map phase failed: {len(failed)} tasks failed"
            )
        
        # Reduce phase
        map_outputs = [r.output for r in map_results]
        reduce_task = Task(
            name=reduce_task_name,
            input_data=map_outputs,
            agent_fn=reduce_fn
        )
        
        return await self._execute_task(reduce_task)
    
    async def _execute_task(self, task: Task) -> TaskResult:
        """Execute a single task.
        
        Args:
            task: Task to execute
            
        Returns:
            Task result
        """
        try:
            # Check if function is async
            if asyncio.iscoroutinefunction(task.agent_fn):
                output = await task.agent_fn(task.input_data)
            else:
                # Run sync function in executor
                loop = asyncio.get_event_loop()
                output = await loop.run_in_executor(
                    None,
                    task.agent_fn,
                    task.input_data
                )
            
            result = TaskResult(
                task_name=task.name,
                output=output,
                success=True,
                metadata=task.metadata
            )
            
            self._results[task.name] = result
            return result
            
        except Exception as e:
            result = TaskResult(
                task_name=task.name,
                output=None,
                success=False,
                error=str(e),
                metadata=task.metadata
            )
            
            self._results[task.name] = result
            return result
    
    def get_result(self, task_name: str) -> Optional[TaskResult]:
        """Get result of a previously executed task.
        
        Args:
            task_name: Name of the task
            
        Returns:
            Task result if found
        """
        return self._results.get(task_name)
    
    def clear_results(self):
        """Clear all stored results."""
        self._results.clear()
    
    async def execute_agents(
        self,
        agents: Dict[str, BaseAgent],
        task: str,
        mode: ExecutionMode = ExecutionMode.PARALLEL,
        timeout: Optional[float] = None
    ) -> Dict[str, AgentResult]:
        """Execute multiple BaseAgent instances.
        
        Convenience method for executing agents directly without
        wrapping them in Task objects.
        
        Args:
            agents: Dict mapping names to BaseAgent instances
            task: The task/input to send to all agents
            mode: Execution mode (PARALLEL or SEQUENTIAL)
            timeout: Optional timeout in seconds
        
        Returns:
            Dict mapping agent names to their AgentResults
        
        Example:
            >>> from .adk.worker_agents import create_worker
            >>> agents = {
            ...     "research": create_worker("research"),
            ...     "analysis": create_worker("analysis"),
            ... }
            >>> results = await orchestrator.execute_agents(
            ...     agents,
            ...     task="Analyze Python trends",
            ...     mode=ExecutionMode.PARALLEL
            ... )
        """
        start_time = time.time()
        
        if mode == ExecutionMode.PARALLEL:
            # Create tasks for parallel execution
            tasks = [
                Task(
                    name=name,
                    input_data=task,
                    agent_fn=agent.run
                )
                for name, agent in agents.items()
            ]
            
            task_results = await self.execute_parallel(tasks, timeout=timeout)
            
            # Convert to dict format
            results = {}
            for task_result in task_results:
                output = task_result.output
                
                # Handle AgentResult returns
                if isinstance(output, AgentResult):
                    results[task_result.task_name] = output
                else:
                    results[task_result.task_name] = AgentResult(
                        output=output,
                        success=task_result.success,
                        error=task_result.error,
                        agent_name=task_result.task_name,
                    )
            
            return results
            
        else:  # SEQUENTIAL
            results = {}
            current_input = task
            
            for name, agent in agents.items():
                result = await agent.run(current_input)
                
                if isinstance(result, AgentResult):
                    results[name] = result
                    if result.success:
                        current_input = result.output
                    else:
                        break  # Stop pipeline on failure
                else:
                    results[name] = AgentResult(
                        output=result,
                        success=True,
                        agent_name=name,
                    )
                    current_input = result
            
            return results


# Convenience function for quick parallel execution
async def run_parallel(
    *agent_fns: Callable,
    inputs: Optional[List[Any]] = None,
    timeout: Optional[float] = None
) -> List[TaskResult]:
    """Quick parallel execution of multiple agents.
    
    Args:
        *agent_fns: Agent functions to execute
        inputs: Optional list of inputs (one per agent)
        timeout: Optional timeout in seconds
        
    Returns:
        List of results
        
    Example:
        >>> results = await run_parallel(
        ...     agent1.run,
        ...     agent2.run,
        ...     agent3.run,
        ...     inputs=["task A", "task B", "task C"]
        ... )
    """
    orchestrator = AgentOrchestrator()
    
    if inputs is None:
        inputs = [None] * len(agent_fns)
    
    tasks = [
        Task(name=f"task_{i}", input_data=inp, agent_fn=fn)
        for i, (fn, inp) in enumerate(zip(agent_fns, inputs))
    ]
    
    return await orchestrator.execute_parallel(tasks, timeout=timeout)


# Convenience function for quick pipeline execution
async def run_pipeline(
    *agent_fns: Callable,
    initial_input: Any = None
) -> TaskResult:
    """Quick pipeline execution of multiple agents.
    
    Args:
        *agent_fns: Agent functions to execute in order
        initial_input: Initial input for first agent
        
    Returns:
        Final result
        
    Example:
        >>> result = await run_pipeline(
        ...     research_agent.run,
        ...     writer_agent.run,
        ...     reviewer_agent.run,
        ...     initial_input={"topic": "AI"}
        ... )
    """
    orchestrator = AgentOrchestrator()
    
    tasks = [
        Task(name=f"step_{i}", input_data=None, agent_fn=fn)
        for i, fn in enumerate(agent_fns)
    ]
    
    return await orchestrator.execute_pipeline(tasks, initial_input=initial_input)


# ============================================================================
# PRODUCTION ORCHESTRATOR - Real Multi-Agent System
# ============================================================================

class ProductionOrchestrator(AgentOrchestrator):
    """Production orchestrator with REAL multi-agent capabilities.
    
    Extends AgentOrchestrator with:
    - SupervisorAgent integration for intelligent task routing
    - Real Gemini API calls (no simulation)
    - Parallel execution of specialized workers
    - A2A protocol support
    
    This is the PRIMARY entry point for production multi-agent systems.
    
    Example:
        >>> orchestrator = ProductionOrchestrator()
        >>> result = await orchestrator.execute_multi_agent(
        ...     "Research AI trends and write a summary"
        ... )
        >>> print(result["output"])
        >>> print(f"Workers used: {result['workers_used']}")
        >>> print(f"Time: {result['execution_time']:.2f}s")
    
    Environment:
        GOOGLE_API_KEY: Required for Gemini API access
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        max_concurrent: int = 10,
        enable_a2a: bool = True
    ):
        """Initialize production orchestrator.
        
        Args:
            api_key: Optional API key (uses GOOGLE_API_KEY env var if not set)
            max_concurrent: Maximum concurrent tasks
            enable_a2a: Whether to enable A2A protocol
        """
        super().__init__(max_concurrent=max_concurrent)
        
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY required. Set environment variable or pass api_key."
            )
        
        self.enable_a2a = enable_a2a
        
        # Lazy initialization
        self._supervisor = None
        self._a2a_protocol = None
        self._init_complete = False
        
        logger.info("ProductionOrchestrator initialized")
    
    async def _ensure_initialized(self) -> None:
        """Lazy initialization of supervisor and A2A.
        
        Defers expensive initialization until first use.
        """
        if self._init_complete:
            return
        
        # Import here to avoid circular dependencies
        from .langgraph.supervisor import SupervisorAgent
        
        self._supervisor = SupervisorAgent(api_key=self.api_key)
        
        if self.enable_a2a:
            from .a2a.protocol import create_protocol
            self._a2a_protocol = create_protocol()
        
        self._init_complete = True
        logger.debug("Supervisor and A2A initialized")
    
    async def execute_multi_agent(
        self,
        task: str,
        workers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Execute task with full multi-agent system.
        
        This is the REAL implementation that:
        1. Uses SupervisorAgent to analyze and route
        2. Executes workers in PARALLEL (via LangGraph Send)
        3. Makes REAL Gemini API calls
        4. Aggregates and returns results
        
        Args:
            task: Task to execute
            workers: Optional list of specific workers to use
                    (if not specified, supervisor decides)
        
        Returns:
            Dictionary with:
                - success: Whether execution succeeded
                - output: Final aggregated output
                - workers_used: List of workers that executed
                - execution_time: Time in seconds
                - parallel: True (always parallel)
                - metadata: Additional execution metadata
        
        Example:
            >>> result = await orchestrator.execute_multi_agent(
            ...     "What are the key trends in AI for 2024?"
            ... )
            >>> print(result["output"])
        """
        await self._ensure_initialized()
        
        start_time = time.time()
        
        logger.info(f"Executing multi-agent task: {task[:100]}...")
        
        try:
            # Execute via supervisor (handles routing and parallel execution)
            supervisor_result = await self._supervisor.run(task)
            
            elapsed = time.time() - start_time
            
            return {
                "success": True,
                "output": supervisor_result.get("final_output", ""),
                "workers_used": supervisor_result.get("metadata", {}).get("workers_executed", []),
                "execution_time": elapsed,
                "parallel": True,  # Always parallel via LangGraph Send
                "metadata": {
                    "supervisor_metadata": supervisor_result.get("metadata", {}),
                    "worker_results": supervisor_result.get("worker_results", {}),
                },
            }
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Multi-agent execution failed: {e}", exc_info=True)
            
            return {
                "success": False,
                "output": None,
                "workers_used": [],
                "execution_time": elapsed,
                "parallel": True,
                "error": str(e),
                "metadata": {},
            }
    
    async def execute_with_workers(
        self,
        task: str,
        worker_types: List[str]
    ) -> Dict[str, Any]:
        """Execute task with specific workers in parallel.
        
        Bypasses supervisor routing and directly executes specified workers.
        
        Args:
            task: Task to execute
            worker_types: List of worker types to use
        
        Returns:
            Dictionary with worker results
        
        Example:
            >>> result = await orchestrator.execute_with_workers(
            ...     "Analyze Python best practices",
            ...     ["research", "code"]
            ... )
        """
        await self._ensure_initialized()
        
        from .adk.workers import create_worker
        
        start_time = time.time()
        
        # Create workers and execute in parallel
        workers = {wt: create_worker(wt, api_key=self.api_key) for wt in worker_types}
        
        async def run_worker(worker_type: str):
            try:
                result = await workers[worker_type].run(task)
                return (worker_type, result.output if result.success else f"Error: {result.error}")
            except Exception as e:
                return (worker_type, f"Error: {str(e)}")
        
        # Execute all workers in parallel
        results = await asyncio.gather(*[run_worker(wt) for wt in worker_types])
        
        elapsed = time.time() - start_time
        
        worker_results = dict(results)
        
        return {
            "success": all("Error:" not in str(r) for _, r in results),
            "output": worker_results,
            "workers_used": worker_types,
            "execution_time": elapsed,
            "parallel": True,
        }
    
    async def verify_system(self) -> Dict[str, Any]:
        """Verify the production system is working.
        
        Checks:
        - API key is valid
        - Gemini API is accessible
        - Workers can execute
        - A2A protocol is working (if enabled)
        
        Returns:
            Dictionary with verification results
        
        Example:
            >>> result = await orchestrator.verify_system()
            >>> for check, status in result["checks"].items():
            ...     print(f"{check}: {'PASS' if status else 'FAIL'}")
        """
        checks = {}
        
        # Check 1: API Key
        checks["api_key"] = bool(self.api_key)
        
        # Check 2: Supervisor initialization
        try:
            await self._ensure_initialized()
            checks["supervisor_init"] = self._supervisor is not None
        except Exception as e:
            checks["supervisor_init"] = False
            checks["supervisor_error"] = str(e)
        
        # Check 3: Gemini API connection
        try:
            from .adk.workers import create_worker
            worker = create_worker("research", api_key=self.api_key)
            result = await worker.run("Say 'OK' if you can hear me")
            checks["gemini_api"] = result.success and len(result.output) > 0
        except Exception as e:
            checks["gemini_api"] = False
            checks["gemini_error"] = str(e)
        
        # Check 4: A2A Protocol
        if self.enable_a2a:
            try:
                checks["a2a_protocol"] = self._a2a_protocol is not None
            except Exception as e:
                checks["a2a_protocol"] = False
                checks["a2a_error"] = str(e)
        
        # Summary
        all_passed = all(
            v for k, v in checks.items() 
            if not k.endswith("_error") and isinstance(v, bool)
        )
        
        return {
            "success": all_passed,
            "checks": checks,
            "api_key_preview": f"{self.api_key[:10]}..." if self.api_key else None,
        }
    
    def get_available_workers(self) -> List[str]:
        """Get list of available worker types.
        
        Returns:
            List of worker type names
        """
        return ["research", "analysis", "writer", "code"]


# ============================================================================
# Quick Production Functions
# ============================================================================

async def quick_multi_agent(
    task: str,
    api_key: Optional[str] = None
) -> str:
    """Quick multi-agent execution.
    
    Convenience function for simple multi-agent tasks.
    
    Args:
        task: Task to execute
        api_key: Optional API key
    
    Returns:
        Output string
    
    Example:
        >>> result = await quick_multi_agent("What is quantum computing?")
        >>> print(result)
    """
    orchestrator = ProductionOrchestrator(api_key=api_key)
    result = await orchestrator.execute_multi_agent(task)
    return result["output"] if result["success"] else f"Error: {result.get('error', 'Unknown')}"


async def verify_production() -> bool:
    """Quick verification of production system.
    
    Returns:
        True if all checks pass
    """
    try:
        orchestrator = ProductionOrchestrator()
        result = await orchestrator.verify_system()
        return result["success"]
    except Exception:
        return False
