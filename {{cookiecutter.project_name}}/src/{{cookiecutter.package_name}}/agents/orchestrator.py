"""Agent orchestrator for parallel and sequential execution."""
import asyncio
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


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
