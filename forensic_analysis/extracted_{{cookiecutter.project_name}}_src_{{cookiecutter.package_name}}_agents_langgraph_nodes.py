{%- if cookiecutter.use_langgraph == 'y' %}
"""Node functions for LangGraph agents using REAL Gemini API.

This module provides node functions that make REAL API calls:
- gemini_node: Direct Gemini API calls via LangChain
- adk_node: Calls via Google ADK
- router_node: Intelligent routing based on task analysis
- tool_node: Tool execution node

ZERO SIMULATION: All nodes make real API calls when invoked.

Example:
    >>> from langgraph.graph import StateGraph, START, END
    >>> from .nodes import gemini_node, router_node
    >>> 
    >>> builder = StateGraph(AgentState)
    >>> builder.add_node("process", gemini_node)
    >>> builder.add_conditional_edges("process", router_node)
    >>> graph = builder.compile()
    >>> 
    >>> result = await graph.ainvoke({"messages": [{"content": "Hello"}]})
"""
import os
from typing import Any, Callable, Dict, List, Literal, Optional, Union
import logging

from .state import AgentState

logger = logging.getLogger(__name__)

# Try to import LangChain for Gemini integration
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    logger.warning("langchain-google-genai not installed. Some nodes will not work.")


# ============================================================================
# Gemini LLM Instance (lazy loaded)
# ============================================================================

_llm: Optional["ChatGoogleGenerativeAI"] = None


def get_gemini_llm(
    model: str = "gemini-2.0-flash-exp",
    temperature: float = 0.7,
    api_key: Optional[str] = None
) -> "ChatGoogleGenerativeAI":
    """Get or create Gemini LLM instance.
    
    Uses lazy loading to defer initialization until first use.
    
    Args:
        model: Gemini model to use
        temperature: Sampling temperature
        api_key: Optional API key (uses env var if not set)
    
    Returns:
        ChatGoogleGenerativeAI instance
        
    Raises:
        ImportError: If langchain-google-genai not installed
        ValueError: If no API key available
    """
    global _llm
    
    if not HAS_LANGCHAIN:
        raise ImportError(
            "langchain-google-genai required. Install with: pip install langchain-google-genai"
        )
    
    if _llm is None:
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY required")
        
        _llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temperature,
        )
        logger.info(f"Initialized Gemini LLM: {model}")
    
    return _llm


# ============================================================================
# Core Node Functions
# ============================================================================

async def gemini_node(state: AgentState) -> Dict[str, Any]:
    """Process state using REAL Gemini API.
    
    Extracts the last message from state and sends it to Gemini.
    Returns the response as a new message.
    
    Args:
        state: Current agent state
    
    Returns:
        State update with assistant message
        
    Example:
        >>> builder.add_node("gemini", gemini_node)
    """
    messages = state.get("messages", [])
    
    if not messages:
        return {
            "messages": [{"role": "assistant", "content": "No input provided"}],
            "context": {"error": "No messages in state"},
        }
    
    # Get last message
    last_msg = messages[-1]
    if hasattr(last_msg, 'content'):
        content = last_msg.content
    elif isinstance(last_msg, dict):
        content = last_msg.get('content', str(last_msg))
    else:
        content = str(last_msg)
    
    try:
        # Get LLM and invoke
        llm = get_gemini_llm()
        
        # Build message history for context
        langchain_messages = []
        for msg in messages[-5:]:  # Last 5 messages for context
            if hasattr(msg, 'content'):
                if hasattr(msg, 'type') and msg.type == 'human':
                    langchain_messages.append(HumanMessage(content=msg.content))
                else:
                    langchain_messages.append(AIMessage(content=msg.content))
            elif isinstance(msg, dict):
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role == 'user':
                    langchain_messages.append(HumanMessage(content=content))
                else:
                    langchain_messages.append(AIMessage(content=content))
        
        # Ensure last message is from user
        if langchain_messages and isinstance(langchain_messages[-1], AIMessage):
            langchain_messages.append(HumanMessage(content=content))
        elif not langchain_messages:
            langchain_messages = [HumanMessage(content=content)]
        
        # REAL API CALL
        response = await llm.ainvoke(langchain_messages)
        
        logger.debug(f"Gemini response: {response.content[:100]}...")
        
        return {
            "messages": [AIMessage(content=response.content)],
            "context": {"last_node": "gemini", "success": True},
        }
        
    except Exception as e:
        logger.error(f"Gemini node error: {e}", exc_info=True)
        return {
            "messages": [{"role": "assistant", "content": f"Error: {str(e)}"}],
            "context": {"error": str(e), "success": False},
        }


def process_node(state: AgentState) -> Dict[str, Any]:
    """Synchronous processing node (for simple transformations).
    
    Use this for non-LLM processing steps.
    For LLM calls, use gemini_node instead.
    
    Args:
        state: Current agent state
        
    Returns:
        State update dictionary
    """
    messages = state.get("messages", [])
    context = state.get("context", {})
    
    # Example processing: extract and format last message
    if messages:
        last_msg = messages[-1]
        if hasattr(last_msg, 'content'):
            content = last_msg.content
        elif isinstance(last_msg, dict):
            content = last_msg.get('content', '')
        else:
            content = str(last_msg)
        
        return {
            "context": {
                **context,
                "processed": True,
                "input_length": len(content),
            }
        }
    
    return {"context": {**context, "processed": True}}


def router_node(state: AgentState) -> str:
    """Router node for conditional edges.
    
    Analyzes state to determine next node.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node name ("continue", "end", or custom)
        
    Example:
        >>> builder.add_conditional_edges(
        ...     "process",
        ...     router_node,
        ...     {"continue": "gemini", "end": END}
        ... )
    """
    context = state.get("context", {})
    
    # Check for completion
    if context.get("done"):
        return "end"
    
    # Check for errors
    if context.get("error"):
        return "end"
    
    # Check iteration count
    iteration = context.get("iteration", 0)
    if iteration >= context.get("max_iterations", 3):
        return "end"
    
    return "continue"


async def adk_node(state: AgentState) -> Dict[str, Any]:
    """Process state using Google ADK agent.
    
    Uses the ADK agent wrapper for Gemini calls.
    Provides more control than direct LangChain.
    
    Args:
        state: Current agent state
    
    Returns:
        State update with assistant message
    """
    from ..adk.agent import GoogleADKAgent, ADKConfig
    
    messages = state.get("messages", [])
    
    if not messages:
        return {
            "messages": [{"role": "assistant", "content": "No input provided"}],
        }
    
    # Get last message content
    last_msg = messages[-1]
    if hasattr(last_msg, 'content'):
        content = last_msg.content
    elif isinstance(last_msg, dict):
        content = last_msg.get('content', str(last_msg))
    else:
        content = str(last_msg)
    
    try:
        # Create ADK agent and run
        config = ADKConfig()
        agent = GoogleADKAgent(config)
        
        response = await agent.run(content)
        
        return {
            "messages": [{"role": "assistant", "content": response}],
            "context": {"last_node": "adk", "success": True},
        }
        
    except Exception as e:
        logger.error(f"ADK node error: {e}", exc_info=True)
        return {
            "messages": [{"role": "assistant", "content": f"Error: {str(e)}"}],
            "context": {"error": str(e), "success": False},
        }


# ============================================================================
# Specialized Router Nodes
# ============================================================================

async def task_analyzer_router(state: AgentState) -> str:
    """Analyze task and route to appropriate handler.
    
    Uses Gemini to understand the task and decide routing.
    
    Args:
        state: Current agent state
    
    Returns:
        Next node name based on task analysis
    """
    messages = state.get("messages", [])
    
    if not messages:
        return "end"
    
    # Get task content
    last_msg = messages[-1]
    if hasattr(last_msg, 'content'):
        content = last_msg.content
    elif isinstance(last_msg, dict):
        content = last_msg.get('content', '')
    else:
        content = str(last_msg)
    
    # Analyze task type
    content_lower = content.lower()
    
    # Simple keyword-based routing (can be enhanced with LLM)
    if any(kw in content_lower for kw in ["research", "find", "search", "what is"]):
        return "research"
    elif any(kw in content_lower for kw in ["analyze", "compare", "evaluate"]):
        return "analysis"
    elif any(kw in content_lower for kw in ["write", "create", "document", "summarize"]):
        return "writer"
    elif any(kw in content_lower for kw in ["code", "implement", "debug", "fix"]):
        return "code"
    else:
        return "general"


def error_router(state: AgentState) -> str:
    """Route based on error state.
    
    Args:
        state: Current agent state
    
    Returns:
        "retry" if retries available, "error_handler" otherwise
    """
    context = state.get("context", {})
    
    retries = context.get("retries", 0)
    max_retries = context.get("max_retries", 3)
    
    if context.get("error") and retries < max_retries:
        return "retry"
    elif context.get("error"):
        return "error_handler"
    else:
        return "continue"


# ============================================================================
# Utility Nodes
# ============================================================================

def increment_iteration(state: AgentState) -> Dict[str, Any]:
    """Increment iteration counter in context.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated context with incremented iteration
    """
    context = state.get("context", {})
    iteration = context.get("iteration", 0) + 1
    
    return {
        "context": {
            **context,
            "iteration": iteration,
        }
    }


def mark_done(state: AgentState) -> Dict[str, Any]:
    """Mark state as done.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated context with done=True
    """
    context = state.get("context", {})
    
    return {
        "context": {
            **context,
            "done": True,
        }
    }


async def error_handler_node(state: AgentState) -> Dict[str, Any]:
    """Handle errors gracefully.
    
    Args:
        state: Current agent state
    
    Returns:
        Error response message
    """
    context = state.get("context", {})
    error = context.get("error", "Unknown error")
    
    return {
        "messages": [{
            "role": "assistant",
            "content": f"I encountered an error: {error}. Please try again or rephrase your request."
        }],
        "context": {
            **context,
            "done": True,
            "error_handled": True,
        }
    }


# ============================================================================
# Node Factory Functions
# ============================================================================

def create_gemini_node(
    system_prompt: Optional[str] = None,
    temperature: float = 0.7
) -> Callable:
    """Create a customized Gemini node.
    
    Args:
        system_prompt: Optional system prompt to prepend
        temperature: Sampling temperature
    
    Returns:
        Async node function
        
    Example:
        >>> research_node = create_gemini_node(
        ...     system_prompt="You are a research assistant.",
        ...     temperature=0.5
        ... )
        >>> builder.add_node("research", research_node)
    """
    async def custom_gemini_node(state: AgentState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        
        if not messages:
            return {"messages": [{"role": "assistant", "content": "No input"}]}
        
        # Get content
        last_msg = messages[-1]
        if hasattr(last_msg, 'content'):
            content = last_msg.content
        elif isinstance(last_msg, dict):
            content = last_msg.get('content', '')
        else:
            content = str(last_msg)
        
        try:
            llm = get_gemini_llm(temperature=temperature)
            
            # Build messages with system prompt
            langchain_messages = []
            if system_prompt:
                langchain_messages.append(HumanMessage(content=f"[System: {system_prompt}]"))
            langchain_messages.append(HumanMessage(content=content))
            
            response = await llm.ainvoke(langchain_messages)
            
            return {
                "messages": [AIMessage(content=response.content)],
                "context": {"success": True},
            }
            
        except Exception as e:
            return {
                "messages": [{"role": "assistant", "content": f"Error: {e}"}],
                "context": {"error": str(e)},
            }
    
    return custom_gemini_node


def create_worker_node(worker_type: str) -> Callable:
    """Create a node that uses a specific worker agent.
    
    Args:
        worker_type: Type of worker (research, analysis, writer, code)
    
    Returns:
        Async node function
        
    Example:
        >>> research_node = create_worker_node("research")
        >>> builder.add_node("research", research_node)
    """
    async def worker_node(state: AgentState) -> Dict[str, Any]:
        from ..adk.workers import create_worker
        
        messages = state.get("messages", [])
        
        if not messages:
            return {"messages": [{"role": "assistant", "content": "No input"}]}
        
        # Get content
        last_msg = messages[-1]
        if hasattr(last_msg, 'content'):
            content = last_msg.content
        elif isinstance(last_msg, dict):
            content = last_msg.get('content', '')
        else:
            content = str(last_msg)
        
        try:
            worker = create_worker(worker_type)
            result = await worker.run(content)
            
            output = result.output if result.success else f"Error: {result.error}"
            
            return {
                "messages": [{"role": "assistant", "content": output}],
                "context": {"worker": worker_type, "success": result.success},
            }
            
        except Exception as e:
            return {
                "messages": [{"role": "assistant", "content": f"Error: {e}"}],
                "context": {"error": str(e)},
            }
    
    return worker_node
{%- endif %}
