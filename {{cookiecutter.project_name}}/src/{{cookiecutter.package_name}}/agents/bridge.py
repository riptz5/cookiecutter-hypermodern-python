{%- if cookiecutter.use_google_adk == 'y' and cookiecutter.use_langgraph == 'y' %}
"""Bridge between Google ADK and LangGraph.

This module provides seamless integration between:
- Google ADK agents (adk/)
- LangGraph workflows (langgraph/)
- A2A protocol for communication

Purpose:
- Wrap ADK agents as LangGraph nodes
- Wrap LangGraph graphs as ADK-compatible agents
- Unify interfaces for orchestration

Design Principle: ZERO COUPLING
- Each framework can operate independently
- Bridge provides optional integration layer
"""
import asyncio
import os
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass
import logging

# ADK imports
from .adk.agent import GoogleADKAgent, ADKConfig
from .adk.workers import WorkerAgent, create_worker

# LangGraph imports
from .langgraph.state import AgentState

# A2A imports
from .a2a.protocol import A2AProtocol, A2AMessage, A2AMessageType, AgentCard, create_protocol

# Base imports
from .base import BaseAgent, AgentContext, AgentResult

# LangChain imports (for LLM compatibility)
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False

logger = logging.getLogger(__name__)


@dataclass
class BridgeConfig:
    """Configuration for the ADK-LangGraph bridge.
    
    Attributes:
        model: Gemini model to use
        api_key: API key (uses env var if not set)
        temperature: Sampling temperature
        enable_a2a: Whether to enable A2A protocol
    """
    model: str = "gemini-2.0-flash-exp"
    api_key: Optional[str] = None
    temperature: float = 0.7
    enable_a2a: bool = True
    
    def __post_init__(self):
        """Set API key from environment if not provided."""
        if not self.api_key:
            self.api_key = os.getenv("GOOGLE_API_KEY")


class ADKLangGraphBridge:
    """Bridge between Google ADK and LangGraph frameworks.
    
    Provides:
    - ADK agents as LangGraph nodes
    - LangChain-compatible LLM from ADK config
    - Unified interface for both frameworks
    - A2A protocol integration
    
    Example:
        >>> bridge = ADKLangGraphBridge()
        >>> 
        >>> # Use as LangChain LLM
        >>> llm = bridge.get_langchain_llm()
        >>> response = await llm.ainvoke([HumanMessage(content="Hello")])
        >>> 
        >>> # Wrap ADK agent as LangGraph node
        >>> research_agent = create_worker("research")
        >>> node_fn = bridge.wrap_adk_agent(research_agent)
        >>> 
        >>> # Use in LangGraph
        >>> builder.add_node("research", node_fn)
    """
    
    def __init__(self, config: Optional[BridgeConfig] = None):
        """Initialize bridge.
        
        Args:
            config: Bridge configuration
        """
        self.config = config or BridgeConfig()
        self._llm: Optional[ChatGoogleGenerativeAI] = None
        self._protocol: Optional[A2AProtocol] = None
        
        if not self.config.api_key:
            raise ValueError(
                "GOOGLE_API_KEY required. Set environment variable or pass api_key."
            )
        
        # Initialize A2A if enabled
        if self.config.enable_a2a:
            self._protocol = create_protocol()
        
        logger.info(f"Bridge initialized with model {self.config.model}")
    
    def get_langchain_llm(self) -> "ChatGoogleGenerativeAI":
        """Get LangChain-compatible LLM.
        
        Creates a ChatGoogleGenerativeAI instance configured with
        the same settings as the ADK agents.
        
        Returns:
            LangChain LLM instance
            
        Raises:
            ImportError: If langchain-google-genai not installed
        """
        if not HAS_LANGCHAIN:
            raise ImportError(
                "langchain-google-genai not installed. "
                "Install with: pip install langchain-google-genai"
            )
        
        if self._llm is None:
            self._llm = ChatGoogleGenerativeAI(
                model=self.config.model,
                google_api_key=self.config.api_key,
                temperature=self.config.temperature,
            )
        
        return self._llm
    
    def wrap_adk_agent(self, agent: Union[GoogleADKAgent, WorkerAgent]) -> Callable:
        """Wrap ADK agent as LangGraph node function.
        
        Creates an async function compatible with LangGraph's
        add_node() method.
        
        Args:
            agent: ADK agent to wrap
            
        Returns:
            Async function for LangGraph node
            
        Example:
            >>> agent = create_worker("research")
            >>> node_fn = bridge.wrap_adk_agent(agent)
            >>> builder.add_node("research", node_fn)
        """
        async def node_fn(state: AgentState) -> Dict[str, Any]:
            """LangGraph node function wrapping ADK agent."""
            # Extract prompt from state
            messages = state.get("messages", [])
            
            if messages:
                # Get last message content
                last_msg = messages[-1]
                if hasattr(last_msg, 'content'):
                    prompt = last_msg.content
                elif isinstance(last_msg, dict):
                    prompt = last_msg.get('content', str(last_msg))
                else:
                    prompt = str(last_msg)
            else:
                # Fall back to task from context
                prompt = state.get("context", {}).get("task", "")
            
            if not prompt:
                return {"messages": [], "context": {"error": "No prompt provided"}}
            
            # Execute ADK agent (REAL API call)
            logger.debug(f"Executing ADK agent: {prompt[:50]}...")
            
            if isinstance(agent, WorkerAgent):
                result = await agent.run(prompt)
                response = result.output if result.success else f"Error: {result.error}"
            else:
                response = await agent.run(prompt)
            
            # Return state update
            return {
                "messages": [AIMessage(content=response)] if HAS_LANGCHAIN else [{"role": "assistant", "content": response}],
                "context": {
                    "last_agent": getattr(agent, 'name', agent.__class__.__name__),
                    "success": True,
                },
            }
        
        return node_fn
    
    def wrap_adk_agent_with_a2a(
        self,
        agent: Union[GoogleADKAgent, WorkerAgent],
        agent_id: str
    ) -> Callable:
        """Wrap ADK agent with A2A protocol support.
        
        Creates a node function that:
        - Registers agent with A2A protocol
        - Handles A2A messages
        - Can be discovered by other agents
        
        Args:
            agent: ADK agent to wrap
            agent_id: Unique agent identifier
            
        Returns:
            Async function for LangGraph node with A2A
        """
        if not self._protocol:
            raise ValueError("A2A not enabled. Set enable_a2a=True in config.")
        
        # Register agent card
        capabilities = getattr(agent, 'capabilities', ['general'])
        card = AgentCard(
            agent_id=agent_id,
            name=getattr(agent, 'name', agent.__class__.__name__),
            capabilities=capabilities,
        )
        self._protocol.register_agent(card)
        
        # Create wrapped node function
        base_fn = self.wrap_adk_agent(agent)
        
        async def a2a_node_fn(state: AgentState) -> Dict[str, Any]:
            """Node function with A2A support."""
            # Check for incoming A2A message
            message = await self._protocol.receive(agent_id, timeout=0.1)
            
            if message and message.type == A2AMessageType.TASK_REQUEST:
                # Process A2A request
                task = message.payload.get("task", "")
                state = {**state, "messages": [{"content": task}]}
                
                # Execute
                result = await base_fn(state)
                
                # Send response via A2A
                response_msg = message.create_response({
                    "result": result.get("messages", [{}])[-1].get("content", "") if result.get("messages") else "",
                    "success": result.get("context", {}).get("success", True),
                })
                await self._protocol.send(response_msg)
                
                return result
            
            # Normal execution without A2A
            return await base_fn(state)
        
        return a2a_node_fn
    
    def create_parallel_node(
        self,
        agents: Dict[str, Union[GoogleADKAgent, WorkerAgent]]
    ) -> Callable:
        """Create a node that executes multiple agents in parallel.
        
        Args:
            agents: Dictionary of agent_name -> agent
            
        Returns:
            Async function that executes all agents in parallel
            
        Example:
            >>> agents = {
            ...     "research": create_worker("research"),
            ...     "analysis": create_worker("analysis"),
            ... }
            >>> parallel_node = bridge.create_parallel_node(agents)
            >>> builder.add_node("parallel_work", parallel_node)
        """
        async def parallel_node_fn(state: AgentState) -> Dict[str, Any]:
            """Execute multiple agents in parallel."""
            # Extract prompt from state
            messages = state.get("messages", [])
            prompt = ""
            if messages:
                last_msg = messages[-1]
                prompt = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)
            
            # Execute all agents in parallel
            tasks = {}
            for name, agent in agents.items():
                if isinstance(agent, WorkerAgent):
                    tasks[name] = agent.run(prompt)
                else:
                    tasks[name] = agent.run(prompt)
            
            # Gather results
            results_list = await asyncio.gather(*tasks.values(), return_exceptions=True)
            results = dict(zip(tasks.keys(), results_list))
            
            # Process results
            outputs = {}
            for name, result in results.items():
                if isinstance(result, Exception):
                    outputs[name] = f"Error: {str(result)}"
                elif isinstance(result, AgentResult):
                    outputs[name] = result.output if result.success else f"Error: {result.error}"
                else:
                    outputs[name] = result
            
            return {
                "messages": [{"role": "assistant", "content": str(outputs)}],
                "context": {
                    "parallel_results": outputs,
                    "agents_executed": list(agents.keys()),
                },
            }
        
        return parallel_node_fn
    
    async def invoke_langchain(
        self,
        prompt: str,
        **kwargs
    ) -> str:
        """Invoke LangChain LLM directly.
        
        Args:
            prompt: Prompt text
            **kwargs: Additional arguments for LLM
            
        Returns:
            LLM response text
        """
        llm = self.get_langchain_llm()
        messages = [HumanMessage(content=prompt)]
        response = await llm.ainvoke(messages, **kwargs)
        return response.content
    
    def get_protocol(self) -> Optional[A2AProtocol]:
        """Get A2A protocol instance.
        
        Returns:
            A2A protocol if enabled
        """
        return self._protocol


# Convenience functions

def create_bridge(
    api_key: Optional[str] = None,
    model: str = "gemini-2.0-flash-exp",
    enable_a2a: bool = True
) -> ADKLangGraphBridge:
    """Create a configured bridge instance.
    
    Args:
        api_key: Optional API key
        model: Gemini model to use
        enable_a2a: Whether to enable A2A protocol
        
    Returns:
        Configured bridge instance
    """
    config = BridgeConfig(
        api_key=api_key,
        model=model,
        enable_a2a=enable_a2a,
    )
    return ADKLangGraphBridge(config)


async def quick_invoke(
    prompt: str,
    agent_type: str = "research",
    api_key: Optional[str] = None
) -> str:
    """Quick invocation using bridge.
    
    Args:
        prompt: Prompt text
        agent_type: Type of worker agent
        api_key: Optional API key
        
    Returns:
        Agent response
        
    Example:
        >>> response = await quick_invoke("What are AI trends?", "research")
    """
    worker = create_worker(agent_type, api_key=api_key)
    result = await worker.run(prompt)
    return result.output if result.success else f"Error: {result.error}"
{%- else %}
"""Bridge module placeholder.

This module requires both use_google_adk and use_langgraph to be enabled.
"""

def create_bridge(*args, **kwargs):
    raise NotImplementedError(
        "Bridge requires both use_google_adk=y and use_langgraph=y"
    )
{%- endif %}
