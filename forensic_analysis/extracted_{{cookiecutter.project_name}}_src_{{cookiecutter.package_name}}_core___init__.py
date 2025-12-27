"""Core utilities and configuration.

This module provides:
- Centralized configuration management
- GCP resource discovery
- Common utilities

Components:
- config: Environment-based configuration
- gcp_discovery: Automatic GCP resource discovery
- gcp_plugins: Plugin system for GCP services
"""
{%- if cookiecutter.use_google_adk == 'y' or cookiecutter.use_google_cloud == 'y' %}
from .config import (
    Config,
    GeminiConfig,
    GCPConfig,
    AgentConfig,
    AutopoiesisConfig,
    get_config,
    set_config,
)

__all__ = [
    "Config",
    "GeminiConfig",
    "GCPConfig",
    "AgentConfig",
    "AutopoiesisConfig",
    "get_config",
    "set_config",
]
{%- else %}
__all__ = []
{%- endif %}
