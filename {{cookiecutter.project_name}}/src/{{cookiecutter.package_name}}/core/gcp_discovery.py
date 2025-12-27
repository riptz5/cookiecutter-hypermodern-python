{%- if cookiecutter.use_google_adk == 'y' or cookiecutter.use_google_cloud == 'y' %}
"""Google Cloud Platform automatic discovery and configuration.

This module discovers:
- Project ID and metadata
- Enabled services/APIs
- Available credentials (ADC)
- Active resources (databases, storage, etc.)

ZERO HARDCODING - Uses plugin architecture:
- Services are discovered dynamically
- Plugins handle resource discovery
- New services = new plugins (no core code changes)
- Adapts automatically to GCP changes
"""
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import logging

try:
    import google.auth
    from google.auth.credentials import Credentials
    from google.cloud import service_usage_v1
    HAS_GCP = True
except ImportError:
    HAS_GCP = False

try:
    from .gcp_plugins import (
        create_plugin_registry,
        discover_custom_plugins,
        PluginRegistry,
    )
    HAS_PLUGINS = True
except ImportError:
    HAS_PLUGINS = False

logger = logging.getLogger(__name__)


@dataclass
class GCPProject:
    """Discovered GCP project information."""
    project_id: str
    project_number: Optional[str] = None
    credentials: Optional[Any] = None
    region: str = "us-central1"
    
    def __repr__(self) -> str:
        return f"GCPProject(id={self.project_id}, region={self.region})"


@dataclass
class GCPService:
    """Information about an enabled GCP service."""
    name: str
    display_name: str
    state: str
    enabled: bool = False
    
    def __repr__(self) -> str:
        status = "✓" if self.enabled else "✗"
        return f"{status} {self.display_name} ({self.name})"


@dataclass
class GCPResources:
    """Discovered GCP resources.
    
    Uses dynamic plugin system - NO hardcoded resource types.
    """
    project: GCPProject
    services: List[GCPService] = field(default_factory=list)
    service_resources: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "project_id": self.project.project_id,
            "region": self.project.region,
            "enabled_services": len([s for s in self.services if s.enabled]),
            "services": [s.name for s in self.services if s.enabled],
        }
        
        # Add resource counts dynamically
        for service_name, resources in self.service_resources.items():
            if "count" in resources:
                service_key = service_name.split('.')[0]
                result[f"{service_key}_count"] = resources["count"]
        
        return result


class GCPDiscovery:
    """Automatic discovery of Google Cloud Platform resources.
    
    Uses Application Default Credentials (ADC) for authentication.
    Discovers project, services, and resources automatically.
    """
    
    def __init__(self, project_id: Optional[str] = None, custom_plugins: Optional[List[Any]] = None):
        """Initialize GCP discovery.
        
        Args:
            project_id: Optional project ID. If None, auto-discovers from ADC.
            custom_plugins: Optional list of custom plugins to register
        """
        if not HAS_GCP:
            raise ImportError(
                "Google Cloud libraries not installed. "
                "Install with: pip install google-cloud-service-usage google-auth"
            )
        
        self.project_id = project_id
        self.credentials: Optional[Credentials] = None
        self._project: Optional[GCPProject] = None
        self._resources: Optional[GCPResources] = None
        
        # Initialize plugin registry
        if HAS_PLUGINS:
            # Discover custom plugins automatically
            discovered_plugins = discover_custom_plugins()
            all_custom = (custom_plugins or []) + discovered_plugins
            self.plugin_registry = create_plugin_registry(additional_plugins=all_custom if all_custom else None)
            logger.info(f"Plugin system initialized with {len(self.plugin_registry.plugins)} plugins")
        else:
            self.plugin_registry = None
            logger.warning("Plugin system not available - limited discovery")
    
    def discover_project(self) -> GCPProject:
        """Discover GCP project using Application Default Credentials.
        
        Returns:
            Discovered project information
            
        Raises:
            google.auth.exceptions.DefaultCredentialsError: If no credentials found
        """
        if self._project is not None:
            return self._project
        
        logger.info("Discovering GCP project using ADC...")
        
        # Use Application Default Credentials
        credentials, project_id = google.auth.default()
        
        # Override with explicit project_id if provided
        if self.project_id:
            project_id = self.project_id
        
        if not project_id:
            # Try environment variables
            project_id = (
                os.getenv("GOOGLE_CLOUD_PROJECT") or
                os.getenv("GCP_PROJECT") or
                os.getenv("GCLOUD_PROJECT")
            )
        
        if not project_id:
            raise ValueError(
                "Could not discover project ID. Set GOOGLE_CLOUD_PROJECT "
                "environment variable or run: gcloud config set project PROJECT_ID"
            )
        
        self.credentials = credentials
        self._project = GCPProject(
            project_id=project_id,
            credentials=credentials,
            region=os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
        )
        
        logger.info(f"✓ Discovered project: {self._project}")
        return self._project
    
    def discover_enabled_services(self) -> List[GCPService]:
        """Discover enabled GCP services/APIs.
        
        Returns:
            List of enabled services
        """
        project = self.discover_project()
        
        logger.info("Discovering enabled services...")
        
        try:
            client = service_usage_v1.ServiceUsageClient(credentials=self.credentials)
            parent = f"projects/{project.project_id}"
            
            services = []
            request = service_usage_v1.ListServicesRequest(
                parent=parent,
                filter="state:ENABLED"
            )
            
            for service in client.list_services(request=request):
                services.append(GCPService(
                    name=service.name.split("/")[-1],
                    display_name=service.config.title if service.config else service.name,
                    state=str(service.state),
                    enabled=service.state == service_usage_v1.State.ENABLED
                ))
            
            logger.info(f"✓ Discovered {len(services)} enabled services")
            return services
        
        except Exception as e:
            logger.warning(f"Could not discover services: {e}")
            return []
    
    def add_custom_plugin(self, plugin: Any):
        """Add a custom plugin at runtime.
        
        Args:
            plugin: Plugin implementing GCPServicePlugin protocol
            
        Example:
            >>> class MyServicePlugin(BaseGCPPlugin):
            ...     @property
            ...     def service_patterns(self):
            ...         return ['myservice']
            ...     
            ...     def discover_resources(self, project_id, credentials, region):
            ...         # Custom discovery logic
            ...         return {"type": "items", "count": 0, "resources": []}
            >>> 
            >>> discovery = GCPDiscovery()
            >>> discovery.add_custom_plugin(MyServicePlugin())
        """
        if self.plugin_registry:
            self.plugin_registry.plugins.append(plugin)
            logger.info(f"Added custom plugin: {plugin.__class__.__name__}")
    
    def discover_all_service_resources(self) -> Dict[str, Dict[str, Any]]:
        """Discover resources for ALL enabled services using plugins.
        
        This method:
        1. Gets list of enabled services from GCP
        2. For each service, finds matching plugin
        3. Plugin discovers resources dynamically
        4. ZERO HARDCODING - adapts to any service
        
        New service? Just add a plugin. No core code changes.
        
        Returns:
            Dict mapping service names to their resources
        """
        if not self.plugin_registry:
            logger.warning("Plugin system not available")
            return {}
        
        project = self.discover_project()
        services = self.discover_enabled_services()
        all_resources = {}
        
        logger.info(f"Discovering resources for {len(services)} enabled services using plugins...")
        
        for service in services:
            if not service.enabled:
                continue
            
            # Find plugin that can handle this service
            plugin = self.plugin_registry.find_plugin(service.name)
            
            if plugin:
                logger.debug(f"Found plugin for {service.display_name}")
                try:
                    resources = plugin.discover_resources(
                        project_id=project.project_id,
                        credentials=self.credentials,
                        region=project.region
                    )
                    
                    if "error" not in resources and resources.get("count", 0) > 0:
                        all_resources[service.name] = resources
                        logger.info(
                            f"✓ {service.display_name}: {resources['count']} "
                            f"{resources.get('type', 'resources')}"
                        )
                except Exception as e:
                    logger.debug(f"Could not discover {service.display_name}: {e}")
            else:
                logger.debug(f"No plugin for {service.display_name} - skipping")
        
        logger.info(f"Discovered resources for {len(all_resources)} services")
        return all_resources
    
    def discover_all(self) -> GCPResources:
        """Discover all GCP resources using plugin system.
        
        Returns:
            Complete resource inventory
        """
        if self._resources is not None:
            return self._resources
        
        logger.info("=" * 80)
        logger.info("DISCOVERING GOOGLE CLOUD RESOURCES (PLUGIN-BASED)")
        logger.info("=" * 80)
        
        project = self.discover_project()
        services = self.discover_enabled_services()
        service_resources = self.discover_all_service_resources()
        
        resources = GCPResources(
            project=project,
            services=services,
            service_resources=service_resources
        )
        
        self._resources = resources
        
        logger.info("=" * 80)
        logger.info("DISCOVERY COMPLETE")
        logger.info(f"Project: {resources.project.project_id}")
        logger.info(f"Enabled Services: {len([s for s in resources.services if s.enabled])}")
        logger.info(f"Services with Resources: {len(resources.service_resources)}")
        
        # Log resource counts dynamically
        for service_name, service_data in resources.service_resources.items():
            service_key = service_name.split('.')[0]
            logger.info(
                f"  {service_key}: {service_data.get('count', 0)} "
                f"{service_data.get('type', 'resources')}"
            )
        
        logger.info("=" * 80)
        
        return resources
    
    def get_service_resources(self, service_pattern: str) -> Optional[Dict[str, Any]]:
        """Get discovered resources for a service.
        
        Args:
            service_pattern: Service pattern to search for (e.g., 'secretmanager', 'storage')
            
        Returns:
            Service resources if found
        """
        if not self._resources:
            self.discover_all()
        
        for service_name, resources in self._resources.service_resources.items():
            if service_pattern.lower() in service_name.lower():
                return resources
        
        return None


# Global discovery instance
_discovery: Optional[GCPDiscovery] = None


def get_gcp_discovery(project_id: Optional[str] = None) -> GCPDiscovery:
    """Get global GCP discovery instance.
    
    Args:
        project_id: Optional project ID
        
    Returns:
        Singleton GCPDiscovery instance
    """
    global _discovery
    if _discovery is None:
        _discovery = GCPDiscovery(project_id=project_id)
    return _discovery


def discover_gcp_resources(project_id: Optional[str] = None) -> GCPResources:
    """Discover all GCP resources.
    
    Args:
        project_id: Optional project ID
        
    Returns:
        Complete resource inventory
    """
    discovery = get_gcp_discovery(project_id=project_id)
    return discovery.discover_all()
{%- endif %}
