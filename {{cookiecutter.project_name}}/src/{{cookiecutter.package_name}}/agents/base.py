"""Abstract base interface for AI agents.

This module defines the contract that ALL agents must implement.
Enables polymorphism across different agent implementations:
- Google ADK agents
- LangGraph agents
- Custom agents

Design Principles:
- Protocol-based (structural typing) for flexibility
- Async-first for performance
- Observable (logging, metrics) for debugging
- Composable (agents can wrap other agents)
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Status of an agent execution."""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class AgentResult:
    """Result of an agent execution.
    
    Attributes:
        output: The agent's output (type depends on agent)
        success: Whether execution succeeded
        error: Error message if failed
        metadata: Additional metadata (timing, tokens, etc.)
        status: Execution status
        started_at: When execution started
        completed_at: When execution completed
    """
    output: Any
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: AgentStatus = AgentStatus.SUCCESS
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def duration_ms(self) -> Optional[float]:
        """Execution duration in milliseconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "output": str(self.output)[:500] if self.output else None,  # Truncate for safety
            "success": self.success,
            "error": self.error,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }


@dataclass
class AgentContext:
    """Context passed to agent during execution.
    
    Contains shared state, configuration, and dependencies.
    
    Attributes:
        task: The task/query to execute
        history: Previous conversation history
        tools: Available tools/functions
        config: Runtime configuration
        parent_agent: Parent agent if this is a sub-agent
        correlation_id: ID for tracing across agents
    """
    task: str
    history: List[Dict[str, Any]] = field(default_factory=list)
    tools: List[Any] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    parent_agent: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def with_task(self, task: str) -> "AgentContext":
        """Create new context with different task."""
        return AgentContext(
            task=task,
            history=self.history.copy(),
            tools=self.tools.copy(),
            config=self.config.copy(),
            parent_agent=self.parent_agent,
            correlation_id=self.correlation_id,
        )


class AgentProtocol(Protocol):
    """Protocol defining the agent interface.
    
    Any class implementing this protocol can be used as an agent.
    Uses structural typing (duck typing) for maximum flexibility.
    """
    
    @property
    def name(self) -> str:
        """Agent identifier."""
        ...
    
    @property
    def capabilities(self) -> List[str]:
        """List of capabilities this agent provides."""
        ...
    
    async def run(self, input_data: Any) -> Any:
        """Execute the agent with given input.
        
        Args:
            input_data: Input to process (type depends on agent)
            
        Returns:
            Agent output (type depends on agent)
        """
        ...


T = TypeVar('T')  # Input type
R = TypeVar('R')  # Result type


class BaseAgent(ABC, Generic[T, R]):
    """Abstract base class for all agents.
    
    Provides common functionality:
    - Logging and observability
    - Error handling
    - Lifecycle hooks
    - Metrics collection
    
    Subclasses must implement:
    - _execute: Core execution logic
    - name: Agent identifier
    - capabilities: What the agent can do
    
    Example:
        >>> class MyAgent(BaseAgent[str, str]):
        ...     @property
        ...     def name(self) -> str:
        ...         return "my_agent"
        ...     
        ...     @property
        ...     def capabilities(self) -> List[str]:
        ...         return ["process_text"]
        ...     
        ...     async def _execute(self, input_data: str, context: AgentContext) -> str:
        ...         return f"Processed: {input_data}"
    """
    
    def __init__(self):
        """Initialize base agent."""
        self._execution_count = 0
        self._total_duration_ms = 0.0
        self._error_count = 0
        self._logger = logging.getLogger(f"{__name__}.{self.name}")
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this agent."""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        """List of capabilities this agent provides.
        
        Used for:
        - Agent discovery and routing
        - A2A protocol agent cards
        - Documentation generation
        """
        pass
    
    @abstractmethod
    async def _execute(self, input_data: T, context: AgentContext) -> R:
        """Core execution logic. Implemented by subclasses.
        
        Args:
            input_data: Input to process
            context: Execution context
            
        Returns:
            Processed result
        """
        pass
    
    async def run(self, input_data: T, context: Optional[AgentContext] = None) -> AgentResult:
        """Execute the agent with full lifecycle management.
        
        Handles:
        - Logging (start, end, errors)
        - Timing and metrics
        - Error wrapping
        - Lifecycle hooks
        
        Args:
            input_data: Input to process
            context: Optional execution context
            
        Returns:
            AgentResult with output and metadata
        """
        # Create context if not provided
        if context is None:
            context = AgentContext(task=str(input_data))
        
        result = AgentResult(
            output=None,
            started_at=datetime.utcnow(),
            status=AgentStatus.RUNNING,
            metadata={"agent": self.name, "correlation_id": context.correlation_id},
        )
        
        self._logger.info(f"Starting execution: {str(input_data)[:100]}...")
        
        try:
            # Pre-execution hook
            await self._pre_execute(input_data, context)
            
            # Execute core logic
            output = await self._execute(input_data, context)
            
            # Post-execution hook
            output = await self._post_execute(output, context)
            
            result.output = output
            result.success = True
            result.status = AgentStatus.SUCCESS
            
            self._logger.info(f"Execution completed successfully")
            
        except TimeoutError as e:
            result.success = False
            result.error = f"Timeout: {str(e)}"
            result.status = AgentStatus.TIMEOUT
            self._error_count += 1
            self._logger.error(f"Execution timeout: {e}")
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            result.status = AgentStatus.FAILED
            self._error_count += 1
            self._logger.error(f"Execution failed: {e}", exc_info=True)
        
        finally:
            result.completed_at = datetime.utcnow()
            self._execution_count += 1
            if result.duration_ms:
                self._total_duration_ms += result.duration_ms
                result.metadata["duration_ms"] = result.duration_ms
        
        return result
    
    async def _pre_execute(self, input_data: T, context: AgentContext) -> None:
        """Hook called before execution. Override for custom logic."""
        pass
    
    async def _post_execute(self, output: R, context: AgentContext) -> R:
        """Hook called after execution. Override for custom logic."""
        return output
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics.
        
        Returns:
            Dictionary of metrics
        """
        avg_duration = (
            self._total_duration_ms / self._execution_count 
            if self._execution_count > 0 
            else 0
        )
        
        return {
            "agent": self.name,
            "execution_count": self._execution_count,
            "error_count": self._error_count,
            "total_duration_ms": self._total_duration_ms,
            "avg_duration_ms": avg_duration,
            "error_rate": self._error_count / max(self._execution_count, 1),
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, capabilities={self.capabilities})"


class ComposableAgent(BaseAgent[T, R]):
    """Agent that can be composed with other agents.
    
    Supports:
    - Chaining (sequential composition)
    - Parallel execution
    - Conditional routing
    """
    
    def __init__(self):
        super().__init__()
        self._sub_agents: List[BaseAgent] = []
    
    def add_sub_agent(self, agent: BaseAgent) -> "ComposableAgent":
        """Add a sub-agent for composition.
        
        Args:
            agent: Agent to add
            
        Returns:
            Self for chaining
        """
        self._sub_agents.append(agent)
        return self
    
    async def run_sub_agents_parallel(
        self, 
        inputs: List[Any],
        context: AgentContext
    ) -> List[AgentResult]:
        """Run sub-agents in parallel.
        
        Args:
            inputs: List of inputs (one per sub-agent)
            context: Shared context
            
        Returns:
            List of results from each sub-agent
        """
        import asyncio
        
        tasks = [
            agent.run(input_data, context.with_task(str(input_data)))
            for agent, input_data in zip(self._sub_agents, inputs)
        ]
        
        return await asyncio.gather(*tasks)
    
    async def run_sub_agents_sequential(
        self,
        initial_input: Any,
        context: AgentContext
    ) -> AgentResult:
        """Run sub-agents sequentially (pipeline).
        
        Output of each agent becomes input to the next.
        
        Args:
            initial_input: Input for first agent
            context: Shared context
            
        Returns:
            Result from final agent
        """
        current_input = initial_input
        result = None
        
        for agent in self._sub_agents:
            result = await agent.run(current_input, context)
            if not result.success:
                return result
            current_input = result.output
        
        return result or AgentResult(output=None, success=False, error="No sub-agents")
