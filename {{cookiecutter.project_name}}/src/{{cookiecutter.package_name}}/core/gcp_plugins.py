{%- if cookiecutter.use_google_cloud == 'y' %}
"""Dynamic plugin system for GCP service discovery.

This module implements a plugin architecture that:
1. Discovers GCP services dynamically
2. Loads appropriate clients automatically
3. Adapts to new services without code changes
4. ZERO HARDCODING

Philosophy:
- Services register themselves
- Plugins are discovered at runtime
- New services = new plugins, no core code changes
"""
import importlib
import logging
from typing import Dict, List, Optional, Any, Callable, Protocol
from dataclasses import dataclass
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class GCPServicePlugin(Protocol):
    """Protocol for GCP service plugins.
    
    Any class implementing this protocol can be a plugin.
    """
    
    @property
    def service_patterns(self) -> List[str]:
        """Service name patterns this plugin handles.
        
        Returns:
            List of patterns (e.g., ['secretmanager', 'secret'])
        """
        ...
    
    @property
    def required_packages(self) -> List[str]:
        """Python packages required for this plugin.
        
        Returns:
            List of package names (e.g., ['google-cloud-secret-manager'])
        """
        ...
    
    def can_handle(self, service_name: str) -> bool:
        """Check if this plugin can handle a service.
        
        Args:
            service_name: Service name to check
            
        Returns:
            True if plugin can handle this service
        """
        ...
    
    def discover_resources(
        self,
        project_id: str,
        credentials: Any,
        region: str
    ) -> Dict[str, Any]:
        """Discover resources for this service.
        
        Args:
            project_id: GCP project ID
            credentials: GCP credentials
            region: GCP region
            
        Returns:
            Dict with discovered resources
        """
        ...


@dataclass
class PluginRegistry:
    """Registry of discovered plugins."""
    plugins: List[GCPServicePlugin]
    
    def find_plugin(self, service_name: str) -> Optional[GCPServicePlugin]:
        """Find plugin that can handle a service.
        
        Args:
            service_name: Service name
            
        Returns:
            Plugin if found, None otherwise
        """
        for plugin in self.plugins:
            if plugin.can_handle(service_name):
                return plugin
        return None
    
    def list_supported_services(self) -> List[str]:
        """List all supported service patterns.
        
        Returns:
            List of service patterns
        """
        patterns = []
        for plugin in self.plugins:
            patterns.extend(plugin.service_patterns)
        return patterns


class BaseGCPPlugin(ABC):
    """Base class for GCP service plugins."""
    
    @property
    @abstractmethod
    def service_patterns(self) -> List[str]:
        """Service patterns this plugin handles."""
        pass
    
    @property
    @abstractmethod
    def required_packages(self) -> List[str]:
        """Required Python packages."""
        pass
    
    def can_handle(self, service_name: str) -> bool:
        """Check if plugin can handle service."""
        service_lower = service_name.lower()
        return any(pattern in service_lower for pattern in self.service_patterns)
    
    @abstractmethod
    def discover_resources(
        self,
        project_id: str,
        credentials: Any,
        region: str
    ) -> Dict[str, Any]:
        """Discover resources for service."""
        pass
    
    def _try_import(self, module_name: str) -> Optional[Any]:
        """Try to import a module dynamically.
        
        Args:
            module_name: Module to import
            
        Returns:
            Imported module or None
        """
        try:
            return importlib.import_module(module_name)
        except ImportError:
            logger.debug(f"Could not import {module_name}")
            return None


class SecretManagerPlugin(BaseGCPPlugin):
    """Plugin for Secret Manager."""
    
    @property
    def service_patterns(self) -> List[str]:
        return ['secretmanager', 'secret']
    
    @property
    def required_packages(self) -> List[str]:
        return ['google-cloud-secret-manager']
    
    def discover_resources(
        self,
        project_id: str,
        credentials: Any,
        region: str
    ) -> Dict[str, Any]:
        """Discover secrets."""
        module = self._try_import('google.cloud.secretmanager')
        if not module:
            return {"error": "Package not installed"}
        
        try:
            client = module.SecretManagerServiceClient(credentials=credentials)
            parent = f"projects/{project_id}"
            
            secrets = [
                secret.name.split("/")[-1]
                for secret in client.list_secrets(request={"parent": parent})
            ]
            
            return {
                "type": "secrets",
                "count": len(secrets),
                "resources": secrets
            }
        except Exception as e:
            return {"error": str(e)}


class StoragePlugin(BaseGCPPlugin):
    """Plugin for Cloud Storage."""
    
    @property
    def service_patterns(self) -> List[str]:
        return ['storage', 'gcs', 'bucket']
    
    @property
    def required_packages(self) -> List[str]:
        return ['google-cloud-storage']
    
    def discover_resources(
        self,
        project_id: str,
        credentials: Any,
        region: str
    ) -> Dict[str, Any]:
        """Discover storage buckets."""
        module = self._try_import('google.cloud.storage')
        if not module:
            return {"error": "Package not installed"}
        
        try:
            client = module.Client(project=project_id, credentials=credentials)
            buckets = [bucket.name for bucket in client.list_buckets()]
            
            return {
                "type": "buckets",
                "count": len(buckets),
                "resources": buckets
            }
        except Exception as e:
            return {"error": str(e)}


class FirestorePlugin(BaseGCPPlugin):
    """Plugin for Firestore."""
    
    @property
    def service_patterns(self) -> List[str]:
        return ['firestore', 'datastore']
    
    @property
    def required_packages(self) -> List[str]:
        return ['google-cloud-firestore']
    
    def discover_resources(
        self,
        project_id: str,
        credentials: Any,
        region: str
    ) -> Dict[str, Any]:
        """Discover Firestore collections."""
        module = self._try_import('google.cloud.firestore')
        if not module:
            return {"error": "Package not installed"}
        
        try:
            db = module.Client(project=project_id, credentials=credentials)
            collections = [col.id for col in db.collections()]
            
            return {
                "type": "collections",
                "count": len(collections),
                "resources": collections
            }
        except Exception as e:
            return {"error": str(e)}


class BigQueryPlugin(BaseGCPPlugin):
    """Plugin for BigQuery."""
    
    @property
    def service_patterns(self) -> List[str]:
        return ['bigquery', 'bq']
    
    @property
    def required_packages(self) -> List[str]:
        return ['google-cloud-bigquery']
    
    def discover_resources(
        self,
        project_id: str,
        credentials: Any,
        region: str
    ) -> Dict[str, Any]:
        """Discover BigQuery datasets."""
        module = self._try_import('google.cloud.bigquery')
        if not module:
            return {"error": "Package not installed"}
        
        try:
            client = module.Client(project=project_id, credentials=credentials)
            datasets = [dataset.dataset_id for dataset in client.list_datasets()]
            
            return {
                "type": "datasets",
                "count": len(datasets),
                "resources": datasets
            }
        except Exception as e:
            return {"error": str(e)}


class VertexAIPlugin(BaseGCPPlugin):
    """Plugin for Vertex AI."""
    
    @property
    def service_patterns(self) -> List[str]:
        return ['aiplatform', 'vertex', 'vertexai']
    
    @property
    def required_packages(self) -> List[str]:
        return ['google-cloud-aiplatform']
    
    def discover_resources(
        self,
        project_id: str,
        credentials: Any,
        region: str
    ) -> Dict[str, Any]:
        """Discover Vertex AI models."""
        module = self._try_import('google.cloud.aiplatform')
        if not module:
            return {"error": "Package not installed"}
        
        try:
            module.init(project=project_id, location=region, credentials=credentials)
            models = [model.resource_name for model in module.Model.list()]
            
            return {
                "type": "models",
                "count": len(models),
                "resources": models
            }
        except Exception as e:
            return {"error": str(e)}


# Built-in plugins
BUILTIN_PLUGINS = [
    SecretManagerPlugin(),
    StoragePlugin(),
    FirestorePlugin(),
    BigQueryPlugin(),
    VertexAIPlugin(),
]


def create_plugin_registry(additional_plugins: Optional[List[GCPServicePlugin]] = None) -> PluginRegistry:
    """Create plugin registry with built-in and additional plugins.
    
    Args:
        additional_plugins: Additional plugins to register
        
    Returns:
        Plugin registry
    """
    plugins = BUILTIN_PLUGINS.copy()
    if additional_plugins:
        plugins.extend(additional_plugins)
    
    logger.info(f"Registered {len(plugins)} plugins")
    return PluginRegistry(plugins=plugins)


def discover_custom_plugins(package_name: str = "gcp_plugins") -> List[GCPServicePlugin]:
    """Discover custom plugins from a package.
    
    Looks for classes implementing GCPServicePlugin protocol.
    
    Args:
        package_name: Package to search for plugins
        
    Returns:
        List of discovered plugins
    """
    plugins = []
    
    try:
        module = importlib.import_module(package_name)
        
        # Find all classes implementing the protocol
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and hasattr(attr, 'service_patterns'):
                try:
                    plugin = attr()
                    plugins.append(plugin)
                    logger.info(f"Discovered custom plugin: {attr_name}")
                except Exception as e:
                    logger.debug(f"Could not instantiate {attr_name}: {e}")
    
    except ImportError:
        logger.debug(f"No custom plugins found in {package_name}")
    
    return plugins
{%- endif %}
