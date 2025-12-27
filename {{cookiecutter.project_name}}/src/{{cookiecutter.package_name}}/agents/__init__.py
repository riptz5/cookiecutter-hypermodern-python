"""AI agent orchestration module.

This module provides a complete multi-agent system with:
- Google ADK integration for Gemini LLM
- LangGraph for workflow orchestration
- A2A protocol for inter-agent communication
- Production-ready orchestration

Quick Start:
    >>> from {{cookiecutter.package_name}}.agents import ProductionOrchestrator
    >>> 
    >>> orchestrator = ProductionOrchestrator()
    >>> result = await orchestrator.execute_multi_agent("Research AI trends")
    >>> print(result["output"])

Components:
- orchestrator: Task orchestration and parallel execution
- adk: Google ADK agent wrappers
- langgraph: LangGraph workflow integration
- a2a: Agent2Agent protocol
- bridge: ADK-LangGraph bridge
- base: Base agent interfaces
"""
from .orchestrator import (
    AgentOrchestrator,
    ProductionOrchestrator,
    Task,
    TaskResult,
    ExecutionMode,
    run_parallel,
    run_pipeline,
    quick_multi_agent,
    verify_production,
)

from .base import (
    BaseAgent,
    AgentResult,
    AgentContext,
    AgentStatus,
    AgentProtocol,
)

{%- if cookiecutter.use_google_adk == 'y' %}
from .adk import (
    GoogleADKAgent,
    ADKConfig,
)
{%- endif %}

__all__ = [
    # Orchestration
    "AgentOrchestrator",
    "ProductionOrchestrator",
    "Task",
    "TaskResult",
    "ExecutionMode",
    "run_parallel",
    "run_pipeline",
    "quick_multi_agent",
    "verify_production",
    # Base
    "BaseAgent",
    "AgentResult",
    "AgentContext",
    "AgentStatus",
    "AgentProtocol",
{%- if cookiecutter.use_google_adk == 'y' %}
    # ADK
    "GoogleADKAgent",
    "ADKConfig",
{%- endif %}
]
