{%- if cookiecutter.use_google_adk == 'y' %}
"""Google ADK agents for {{cookiecutter.friendly_name}}."""
from .agent import GoogleADKAgent, ADKConfig, create_adk_agent

__all__ = ["GoogleADKAgent", "ADKConfig", "create_adk_agent"]
{%- endif %}
