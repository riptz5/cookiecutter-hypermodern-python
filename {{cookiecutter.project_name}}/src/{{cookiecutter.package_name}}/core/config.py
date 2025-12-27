{%- if cookiecutter.use_google_adk == 'y' or cookiecutter.use_google_cloud == 'y' %}
"""Centralized configuration for {{cookiecutter.friendly_name}}.

This module provides:
- Environment-based configuration
- Google Cloud credentials management
- Runtime configuration validation
- Zero-hardcoding principle enforcement

Configuration Sources (priority order):
1. Environment variables
2. Secret Manager (if available)
3. Default values

ZERO HARDCODING: All values are parameterized.
"""
import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GeminiConfig:
    """Configuration for Gemini API.
    
    Attributes:
        model: Model identifier (e.g., 'gemini-2.0-flash-exp')
        api_key: API key (from env or Secret Manager)
        temperature: Sampling temperature (0.0-2.0)
        max_tokens: Maximum output tokens
        timeout: Request timeout in seconds
    """
    model: str = "gemini-2.0-flash-exp"
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 8192
    timeout: float = 30.0
    
    def __post_init__(self):
        """Validate configuration."""
        if not self.api_key:
            # Try environment variable
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            if api_key:
                object.__setattr__(self, 'api_key', api_key)


@dataclass(frozen=True)
class GCPConfig:
    """Configuration for Google Cloud Platform.
    
    Attributes:
        project_id: GCP project ID (auto-discovered if not set)
        region: Default region for resources
        credentials_path: Path to service account JSON (optional)
    """
    project_id: Optional[str] = None
    region: str = "us-central1"
    credentials_path: Optional[str] = None
    
    def __post_init__(self):
        """Auto-discover project ID if not set."""
        if not self.project_id:
            project_id = (
                os.getenv("GOOGLE_CLOUD_PROJECT") or
                os.getenv("GCP_PROJECT") or
                os.getenv("GCLOUD_PROJECT")
            )
            if project_id:
                object.__setattr__(self, 'project_id', project_id)


@dataclass(frozen=True)
class AgentConfig:
    """Configuration for AI agents.
    
    Attributes:
        max_concurrent: Maximum concurrent agent executions
        default_timeout: Default timeout for agent operations
        retry_attempts: Number of retry attempts on failure
        enable_memory: Whether to use persistent memory (Firestore)
        enable_parallel: Whether to enable parallel execution
    """
    max_concurrent: int = 10
    default_timeout: float = 60.0
    retry_attempts: int = 3
    enable_memory: bool = True
    enable_parallel: bool = True


@dataclass(frozen=True)
class AutopoiesisConfig:
    """Configuration for autopoietic system.
    
    Attributes:
        cycle_interval: Interval between autopoietic cycles (seconds)
        enable_self_improve: Whether to allow self-improvement
        enable_self_deploy: Whether to allow self-deployment
        memory_collection: Firestore collection for autopoietic memory
        max_changes_per_cycle: Maximum code changes per cycle
    """
    cycle_interval: int = 3600  # 1 hour
    enable_self_improve: bool = False  # Disabled by default for safety
    enable_self_deploy: bool = False   # Disabled by default for safety
    memory_collection: str = "autopoiesis_memory"
    max_changes_per_cycle: int = 5


@dataclass
class Config:
    """Main configuration container.
    
    Aggregates all sub-configurations into a single immutable object.
    Uses factory pattern to allow runtime customization.
    
    Example:
        >>> config = Config.from_env()
        >>> print(config.gemini.model)
        'gemini-2.0-flash-exp'
        
        >>> # Custom configuration
        >>> config = Config(
        ...     gemini=GeminiConfig(model="gemini-pro"),
        ...     agent=AgentConfig(max_concurrent=5)
        ... )
    """
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    gcp: GCPConfig = field(default_factory=GCPConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    autopoiesis: AutopoiesisConfig = field(default_factory=AutopoiesisConfig)
    
    # Runtime flags
    debug: bool = False
    dry_run: bool = False  # If True, don't execute real API calls
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables.
        
        Environment Variables:
            GOOGLE_API_KEY: Gemini API key
            GOOGLE_CLOUD_PROJECT: GCP project ID
            GOOGLE_CLOUD_REGION: GCP region
            DEBUG: Enable debug mode
            DRY_RUN: Enable dry run mode
            
        Returns:
            Config instance populated from environment
        """
        return cls(
            gemini=GeminiConfig(
                model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp"),
                api_key=os.getenv("GOOGLE_API_KEY"),
                temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.7")),
                max_tokens=int(os.getenv("GEMINI_MAX_TOKENS", "8192")),
            ),
            gcp=GCPConfig(
                project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
                region=os.getenv("GOOGLE_CLOUD_REGION", "us-central1"),
                credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
            ),
            agent=AgentConfig(
                max_concurrent=int(os.getenv("AGENT_MAX_CONCURRENT", "10")),
                default_timeout=float(os.getenv("AGENT_TIMEOUT", "60.0")),
                enable_memory=os.getenv("AGENT_ENABLE_MEMORY", "true").lower() == "true",
                enable_parallel=os.getenv("AGENT_ENABLE_PARALLEL", "true").lower() == "true",
            ),
            autopoiesis=AutopoiesisConfig(
                enable_self_improve=os.getenv("AUTOPOIESIS_SELF_IMPROVE", "false").lower() == "true",
                enable_self_deploy=os.getenv("AUTOPOIESIS_SELF_DEPLOY", "false").lower() == "true",
            ),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            dry_run=os.getenv("DRY_RUN", "false").lower() == "true",
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check Gemini API key
        if not self.gemini.api_key:
            errors.append("GOOGLE_API_KEY not set")
        
        # Check GCP project for cloud features
        if not self.gcp.project_id and self.agent.enable_memory:
            errors.append("GOOGLE_CLOUD_PROJECT required when memory is enabled")
        
        # Warn about autopoiesis settings
        if self.autopoiesis.enable_self_improve:
            logger.warning("Self-improvement is ENABLED - system can modify its own code")
        
        if self.autopoiesis.enable_self_deploy:
            logger.warning("Self-deployment is ENABLED - system can deploy itself")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (safe for logging - no secrets)."""
        return {
            "gemini": {
                "model": self.gemini.model,
                "api_key": "***" if self.gemini.api_key else None,
                "temperature": self.gemini.temperature,
                "max_tokens": self.gemini.max_tokens,
            },
            "gcp": {
                "project_id": self.gcp.project_id,
                "region": self.gcp.region,
            },
            "agent": {
                "max_concurrent": self.agent.max_concurrent,
                "enable_memory": self.agent.enable_memory,
                "enable_parallel": self.agent.enable_parallel,
            },
            "autopoiesis": {
                "enable_self_improve": self.autopoiesis.enable_self_improve,
                "enable_self_deploy": self.autopoiesis.enable_self_deploy,
            },
            "debug": self.debug,
            "dry_run": self.dry_run,
        }


# Global configuration instance (singleton pattern)
_config: Optional[Config] = None


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Get global configuration instance.
    
    Uses singleton pattern with lazy initialization.
    Configuration is loaded from environment on first access.
    
    Returns:
        Global Config instance
        
    Example:
        >>> config = get_config()
        >>> print(config.gemini.model)
    """
    global _config
    if _config is None:
        _config = Config.from_env()
        
        # Log configuration (without secrets)
        logger.info(f"Configuration loaded: {_config.to_dict()}")
        
        # Validate
        errors = _config.validate()
        for error in errors:
            logger.warning(f"Configuration warning: {error}")
    
    return _config


def set_config(config: Config) -> None:
    """Set global configuration instance.
    
    Useful for testing or runtime reconfiguration.
    
    Args:
        config: Configuration to set as global
    """
    global _config
    _config = config
    get_config.cache_clear()  # Clear the lru_cache
    logger.info("Configuration updated")
{%- endif %}
