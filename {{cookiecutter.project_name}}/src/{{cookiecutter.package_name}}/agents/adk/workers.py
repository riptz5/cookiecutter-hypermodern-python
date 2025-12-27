{%- if cookiecutter.use_google_adk == 'y' %}
"""Specialized worker agents using Google ADK.

This module provides specialized agents for different tasks:
- ResearchAgent: Information gathering and research
- AnalysisAgent: Data analysis and insight extraction
- WriterAgent: Content generation and documentation
- CodeAgent: Code generation and refactoring

Each agent:
- Uses REAL Gemini API (no simulation)
- Has specialized system prompts
- Can be orchestrated by SupervisorAgent
- Supports A2A protocol communication

ZERO SIMULATION: All agents make real API calls.
"""
import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging

from .agent import GoogleADKAgent, ADKConfig
from ..base import BaseAgent, AgentContext, AgentResult

logger = logging.getLogger(__name__)


# ============================================================================
# System Prompts for Specialized Agents
# ============================================================================

SYSTEM_PROMPTS = {
    "research": """You are an expert researcher with the following capabilities:
- Gather and synthesize information on any topic
- Identify key facts, trends, and patterns
- Evaluate source credibility and relevance
- Present findings in a clear, structured format

Guidelines:
- Be thorough but concise
- Cite sources when available
- Distinguish between facts and inferences
- Acknowledge uncertainty when appropriate""",

    "analysis": """You are an expert data analyst with the following capabilities:
- Analyze complex data and extract insights
- Identify patterns, correlations, and anomalies
- Evaluate strengths and weaknesses
- Provide actionable recommendations

Guidelines:
- Use systematic analysis methods
- Support conclusions with evidence
- Consider multiple perspectives
- Quantify findings when possible""",

    "writer": """You are a professional technical writer with the following capabilities:
- Create clear, well-structured documentation
- Adapt tone and style to audience
- Explain complex concepts simply
- Produce various formats (docs, reports, summaries)

Guidelines:
- Prioritize clarity over cleverness
- Use active voice and concrete examples
- Structure content logically
- Ensure consistency in terminology""",

    "code": """You are an expert software engineer with the following capabilities:
- Write clean, efficient, production-ready code
- Follow best practices and design patterns
- Debug and refactor existing code
- Document code clearly

Guidelines:
- Prioritize readability and maintainability
- Handle errors explicitly
- Write defensive code
- Include type hints and docstrings
- Follow the project's coding standards""",
}


# ============================================================================
# Worker Agent Factory
# ============================================================================

@dataclass
class WorkerConfig:
    """Configuration for a worker agent.
    
    Attributes:
        agent_type: Type of agent (research, analysis, writer, code)
        api_key: Optional API key (uses env var if not set)
        model: Gemini model to use
        temperature: Sampling temperature
        max_tokens: Maximum output tokens
        custom_prompt: Optional custom system prompt
    """
    agent_type: str
    api_key: Optional[str] = None
    model: str = "gemini-2.0-flash-exp"
    temperature: float = 0.7
    max_tokens: int = 8192
    custom_prompt: Optional[str] = None
    
    @property
    def system_prompt(self) -> str:
        """Get system prompt for this agent type."""
        if self.custom_prompt:
            return self.custom_prompt
        return SYSTEM_PROMPTS.get(self.agent_type, SYSTEM_PROMPTS["research"])


class WorkerAgent(BaseAgent[str, str]):
    """Specialized worker agent using Google ADK.
    
    Wraps GoogleADKAgent with:
    - Specialized system prompts
    - BaseAgent lifecycle management
    - Metrics and observability
    - A2A protocol compatibility
    
    Example:
        >>> worker = WorkerAgent(WorkerConfig(agent_type="research"))
        >>> result = await worker.run("What are the latest trends in AI?")
        >>> print(result.output)
    """
    
    # Capability mappings for A2A protocol
    CAPABILITY_MAP = {
        "research": ["research", "search", "gather_info", "fact_check"],
        "analysis": ["analyze", "evaluate", "compare", "assess"],
        "writer": ["write", "document", "summarize", "explain"],
        "code": ["code", "debug", "refactor", "review"],
    }
    
    def __init__(self, config: WorkerConfig):
        """Initialize worker agent.
        
        Args:
            config: Worker configuration
        """
        super().__init__()
        self.config = config
        
        # Create underlying ADK agent
        adk_config = ADKConfig(
            model=config.model,
            api_key=config.api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            system_instruction=config.system_prompt,
        )
        self._adk_agent = GoogleADKAgent(adk_config)
        
        logger.info(f"Initialized {self.name} with model {config.model}")
    
    @property
    def name(self) -> str:
        """Unique identifier for this agent."""
        return f"{self.config.agent_type}_agent"
    
    @property
    def capabilities(self) -> List[str]:
        """List of capabilities this agent provides."""
        return self.CAPABILITY_MAP.get(
            self.config.agent_type, 
            ["general"]
        )
    
    async def _execute(self, input_data: str, context: AgentContext) -> str:
        """Execute the agent using real Gemini API.
        
        Args:
            input_data: Query/task to process
            context: Execution context
            
        Returns:
            Agent response from Gemini
        """
        # Build prompt with context
        prompt = self._build_prompt(input_data, context)
        
        # Call REAL Gemini API
        logger.debug(f"Calling Gemini API: {prompt[:100]}...")
        response = await self._adk_agent.run(prompt)
        
        logger.debug(f"Received response: {response[:100]}...")
        return response
    
    def _build_prompt(self, input_data: str, context: AgentContext) -> str:
        """Build prompt with context.
        
        Args:
            input_data: Main query
            context: Execution context
            
        Returns:
            Complete prompt
        """
        parts = []
        
        # Add parent agent context if available
        if context.parent_agent:
            parts.append(f"[Delegated from: {context.parent_agent}]")
        
        # Add history summary if available
        if context.history:
            history_summary = "\n".join([
                f"- {h.get('role', 'user')}: {str(h.get('content', ''))[:100]}..."
                for h in context.history[-3:]  # Last 3 messages
            ])
            parts.append(f"Recent context:\n{history_summary}")
        
        # Add main query
        parts.append(input_data)
        
        return "\n\n".join(parts)
    
    def clear_history(self) -> None:
        """Clear agent conversation history."""
        self._adk_agent.clear_history()
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get agent conversation history."""
        return self._adk_agent.get_history()


# ============================================================================
# Convenience Factory Functions
# ============================================================================

def create_research_agent(
    api_key: Optional[str] = None,
    **kwargs
) -> WorkerAgent:
    """Create a research agent.
    
    Args:
        api_key: Optional API key
        **kwargs: Additional WorkerConfig options
        
    Returns:
        Configured research agent
    """
    config = WorkerConfig(agent_type="research", api_key=api_key, **kwargs)
    return WorkerAgent(config)


def create_analysis_agent(
    api_key: Optional[str] = None,
    **kwargs
) -> WorkerAgent:
    """Create an analysis agent.
    
    Args:
        api_key: Optional API key
        **kwargs: Additional WorkerConfig options
        
    Returns:
        Configured analysis agent
    """
    config = WorkerConfig(agent_type="analysis", api_key=api_key, **kwargs)
    return WorkerAgent(config)


def create_writer_agent(
    api_key: Optional[str] = None,
    **kwargs
) -> WorkerAgent:
    """Create a writer agent.
    
    Args:
        api_key: Optional API key
        **kwargs: Additional WorkerConfig options
        
    Returns:
        Configured writer agent
    """
    config = WorkerConfig(agent_type="writer", api_key=api_key, **kwargs)
    return WorkerAgent(config)


def create_code_agent(
    api_key: Optional[str] = None,
    **kwargs
) -> WorkerAgent:
    """Create a code agent.
    
    Args:
        api_key: Optional API key
        **kwargs: Additional WorkerConfig options
        
    Returns:
        Configured code agent
    """
    config = WorkerConfig(agent_type="code", api_key=api_key, **kwargs)
    return WorkerAgent(config)


def create_worker(
    agent_type: str,
    api_key: Optional[str] = None,
    **kwargs
) -> WorkerAgent:
    """Factory function to create any worker agent.
    
    Args:
        agent_type: Type of agent (research, analysis, writer, code)
        api_key: Optional API key
        **kwargs: Additional WorkerConfig options
        
    Returns:
        Configured worker agent
        
    Example:
        >>> agent = create_worker("research")
        >>> result = await agent.run("Latest AI trends")
    """
    factories = {
        "research": create_research_agent,
        "analysis": create_analysis_agent,
        "writer": create_writer_agent,
        "code": create_code_agent,
    }
    
    factory = factories.get(agent_type)
    if not factory:
        raise ValueError(f"Unknown agent type: {agent_type}. Valid: {list(factories.keys())}")
    
    return factory(api_key=api_key, **kwargs)


# ============================================================================
# Worker Pool for Parallel Execution
# ============================================================================

class WorkerPool:
    """Pool of worker agents for parallel execution.
    
    Manages multiple workers and provides:
    - Parallel task execution
    - Load balancing
    - Worker lifecycle management
    
    Example:
        >>> pool = WorkerPool()
        >>> pool.add_worker(create_research_agent())
        >>> pool.add_worker(create_analysis_agent())
        >>> results = await pool.execute_parallel([
        ...     ("research", "AI trends"),
        ...     ("analysis", "Compare GPT vs Gemini"),
        ... ])
    """
    
    def __init__(self):
        """Initialize empty worker pool."""
        self._workers: Dict[str, WorkerAgent] = {}
    
    def add_worker(self, worker: WorkerAgent) -> "WorkerPool":
        """Add a worker to the pool.
        
        Args:
            worker: Worker agent to add
            
        Returns:
            Self for chaining
        """
        self._workers[worker.config.agent_type] = worker
        logger.info(f"Added {worker.name} to pool")
        return self
    
    def get_worker(self, agent_type: str) -> Optional[WorkerAgent]:
        """Get a worker by type.
        
        Args:
            agent_type: Type of worker
            
        Returns:
            Worker if found
        """
        return self._workers.get(agent_type)
    
    async def execute_parallel(
        self,
        tasks: List[tuple],
        context: Optional[AgentContext] = None
    ) -> List[AgentResult]:
        """Execute tasks in parallel across workers.
        
        Args:
            tasks: List of (agent_type, input) tuples
            context: Optional shared context
            
        Returns:
            List of results in same order as tasks
        """
        context = context or AgentContext(task="parallel_execution")
        
        async def execute_task(agent_type: str, input_data: str) -> AgentResult:
            worker = self._workers.get(agent_type)
            if not worker:
                return AgentResult(
                    output=None,
                    success=False,
                    error=f"No worker for type: {agent_type}"
                )
            return await worker.run(input_data, context.with_task(input_data))
        
        # Execute all tasks in parallel
        coroutines = [execute_task(t, i) for t, i in tasks]
        results = await asyncio.gather(*coroutines)
        
        logger.info(f"Executed {len(results)} tasks in parallel")
        return list(results)
    
    def create_default_pool(self) -> "WorkerPool":
        """Create pool with all default workers.
        
        Returns:
            Self with all workers added
        """
        self.add_worker(create_research_agent())
        self.add_worker(create_analysis_agent())
        self.add_worker(create_writer_agent())
        self.add_worker(create_code_agent())
        return self
    
    def get_all_capabilities(self) -> List[str]:
        """Get combined capabilities from all workers.
        
        Returns:
            List of all capabilities
        """
        capabilities = []
        for worker in self._workers.values():
            capabilities.extend(worker.capabilities)
        return list(set(capabilities))
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics from all workers.
        
        Returns:
            Dictionary of worker metrics
        """
        return {
            name: worker.get_metrics()
            for name, worker in self._workers.items()
        }
{%- endif %}
