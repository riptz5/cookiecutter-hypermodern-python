{%- if cookiecutter.use_google_adk == 'y' %}
"""Google ADK agents for {{cookiecutter.friendly_name}}.

<<<<<<< Current (Your changes)
This package provides:
- GoogleADKAgent: Core agent using Gemini API
- ADKConfig: Configuration for agents
- WorkerAgent: Specialized workers (research, analysis, writer, code, etc.)
- create_worker: Factory for creating workers
"""
from .agent import GoogleADKAgent, ADKConfig, create_adk_agent
from .workers import WorkerAgent, WorkerType, create_worker, create_worker_team

__all__ = [
    "GoogleADKAgent",
    "ADKConfig",
    "create_adk_agent",
    "WorkerAgent",
    "WorkerType",
    "create_worker",
    "create_worker_team",
=======
This module provides Google ADK integration:
- GoogleADKAgent: Base agent wrapper for Gemini
- Specialized workers: research, analysis, writer, code
- Worker pool for parallel execution

Quick Start:
    >>> from {{cookiecutter.package_name}}.agents.adk import GoogleADKAgent, ADKConfig
    >>> 
    >>> agent = GoogleADKAgent(ADKConfig())
    >>> response = await agent.run("What is Python?")
    >>> print(response)

Workers:
    >>> from {{cookiecutter.package_name}}.agents.adk import create_worker
    >>> 
    >>> research = create_worker("research")
    >>> result = await research.run("AI trends 2024")
    >>> print(result.output)
"""
from .agent import GoogleADKAgent, ADKConfig, create_adk_agent
from .workers import (
    WorkerAgent,
    WorkerConfig,
    WorkerPool,
    create_worker,
    create_research_agent,
    create_analysis_agent,
    create_writer_agent,
    create_code_agent,
)

__all__ = [
    # Core
    "GoogleADKAgent",
    "ADKConfig",
    "create_adk_agent",
    # Workers
    "WorkerAgent",
    "WorkerConfig",
    "WorkerPool",
    "create_worker",
    "create_research_agent",
    "create_analysis_agent",
    "create_writer_agent",
    "create_code_agent",
>>>>>>> Incoming (Background Agent changes)
]
{%- endif %}
