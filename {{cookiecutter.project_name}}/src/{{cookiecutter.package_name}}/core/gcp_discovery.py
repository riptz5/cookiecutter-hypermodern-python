{%- if cookiecutter.use_google_adk == 'y' or cookiecutter.use_google_cloud == 'y' %}
"""Google Cloud Platform automatic discovery and configuration.

This module discovers:
- Project ID and metadata
- Enabled services/APIs
- Available credentials (ADC)
- Active resources (databases, storage, etc.)
- Secret Manager secrets
- Vertex AI models

NO hardcoding - everything is discovered automatically from GCP.
"""
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import logging

try:
    import google.auth
    from google.auth.credentials import Credentials
    from google.cloud import service_usage_v1
    from google.cloud import secretmanager
    from google.cloud import storage
    from google.cloud import firestore
    from google.cloud import bigquery
    from google.cloud import aiplatform
    HAS_GCP = True
except ImportError:
    HAS_GCP = False

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
    """Discovered GCP resources."""
    project: GCPProject
    services: List[GCPService] = field(default_factory=list)
    secrets: List[str] = field(default_factory=list)
    storage_buckets: List[str] = field(default_factory=list)
    firestore_collections: List[str] = field(default_factory=list)
    bigquery_datasets: List[str] = field(default_factory=list)
    vertex_models: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "project_id": self.project.project_id,
            "region": self.project.region,
            "services": [s.name for s in self.services if s.enabled],
            "secrets_count": len(self.secrets),
            "storage_buckets_count": len(self.storage_buckets),
            "firestore_collections_count": len(self.firestore_collections),
            "bigquery_datasets_count": len(self.bigquery_datasets),
            "vertex_models_count": len(self.vertex_models),
        }


class GCPDiscovery:
    """Automatic discovery of Google Cloud Platform resources.
    
    Uses Application Default Credentials (ADC) for authentication.
    Discovers project, services, and resources automatically.
    """
    
    def __init__(self, project_id: Optional[str] = None):
        """Initialize GCP discovery.
        
        Args:
            project_id: Optional project ID. If None, auto-discovers from ADC.
        """
        if not HAS_GCP:
            raise ImportError(
                "Google Cloud libraries not installed. "
                "Install with: pip install google-cloud-service-usage "
                "google-cloud-secret-manager google-cloud-storage "
                "google-cloud-firestore google-cloud-bigquery "
                "google-cloud-aiplatform"
            )
        
        self.project_id = project_id
        self.credentials: Optional[Credentials] = None
        self._project: Optional[GCPProject] = None
        self._resources: Optional[GCPResources] = None
    
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
    
    def discover_secrets(self) -> List[str]:
        """Discover secrets in Secret Manager.
        
        Returns:
            List of secret names
        """
        project = self.discover_project()
        
        try:
            client = secretmanager.SecretManagerServiceClient(credentials=self.credentials)
            parent = f"projects/{project.project_id}"
            
            secrets = []
            for secret in client.list_secrets(request={"parent": parent}):
                secret_name = secret.name.split("/")[-1]
                secrets.append(secret_name)
            
            logger.info(f"✓ Discovered {len(secrets)} secrets")
            return secrets
        
        except Exception as e:
            logger.warning(f"Could not discover secrets: {e}")
            return []
    
    def discover_storage_buckets(self) -> List[str]:
        """Discover Cloud Storage buckets.
        
        Returns:
            List of bucket names
        """
        project = self.discover_project()
        
        try:
            client = storage.Client(
                project=project.project_id,
                credentials=self.credentials
            )
            
            buckets = [bucket.name for bucket in client.list_buckets()]
            logger.info(f"✓ Discovered {len(buckets)} storage buckets")
            return buckets
        
        except Exception as e:
            logger.warning(f"Could not discover storage buckets: {e}")
            return []
    
    def discover_firestore_collections(self) -> List[str]:
        """Discover Firestore collections.
        
        Returns:
            List of collection names
        """
        project = self.discover_project()
        
        try:
            db = firestore.Client(
                project=project.project_id,
                credentials=self.credentials
            )
            
            collections = [col.id for col in db.collections()]
            logger.info(f"✓ Discovered {len(collections)} Firestore collections")
            return collections
        
        except Exception as e:
            logger.warning(f"Could not discover Firestore collections: {e}")
            return []
    
    def discover_bigquery_datasets(self) -> List[str]:
        """Discover BigQuery datasets.
        
        Returns:
            List of dataset IDs
        """
        project = self.discover_project()
        
        try:
            client = bigquery.Client(
                project=project.project_id,
                credentials=self.credentials
            )
            
            datasets = [dataset.dataset_id for dataset in client.list_datasets()]
            logger.info(f"✓ Discovered {len(datasets)} BigQuery datasets")
            return datasets
        
        except Exception as e:
            logger.warning(f"Could not discover BigQuery datasets: {e}")
            return []
    
    def discover_vertex_models(self) -> List[str]:
        """Discover Vertex AI models.
        
        Returns:
            List of model resource names
        """
        project = self.discover_project()
        
        try:
            aiplatform.init(
                project=project.project_id,
                location=project.region,
                credentials=self.credentials
            )
            
            models = [model.resource_name for model in aiplatform.Model.list()]
            logger.info(f"✓ Discovered {len(models)} Vertex AI models")
            return models
        
        except Exception as e:
            logger.warning(f"Could not discover Vertex AI models: {e}")
            return []
    
    def discover_all(self) -> GCPResources:
        """Discover all GCP resources.
        
        Returns:
            Complete resource inventory
        """
        if self._resources is not None:
            return self._resources
        
        logger.info("=" * 80)
        logger.info("DISCOVERING GOOGLE CLOUD RESOURCES")
        logger.info("=" * 80)
        
        project = self.discover_project()
        
        resources = GCPResources(
            project=project,
            services=self.discover_enabled_services(),
            secrets=self.discover_secrets(),
            storage_buckets=self.discover_storage_buckets(),
            firestore_collections=self.discover_firestore_collections(),
            bigquery_datasets=self.discover_bigquery_datasets(),
            vertex_models=self.discover_vertex_models(),
        )
        
        self._resources = resources
        
        logger.info("=" * 80)
        logger.info("DISCOVERY COMPLETE")
        logger.info(f"Project: {resources.project.project_id}")
        logger.info(f"Services: {len([s for s in resources.services if s.enabled])}")
        logger.info(f"Secrets: {len(resources.secrets)}")
        logger.info(f"Storage Buckets: {len(resources.storage_buckets)}")
        logger.info(f"Firestore Collections: {len(resources.firestore_collections)}")
        logger.info(f"BigQuery Datasets: {len(resources.bigquery_datasets)}")
        logger.info(f"Vertex AI Models: {len(resources.vertex_models)}")
        logger.info("=" * 80)
        
        return resources
    
    def get_secret(self, secret_id: str, version: str = "latest") -> Optional[str]:
        """Get secret value from Secret Manager.
        
        Args:
            secret_id: Secret ID
            version: Secret version (default: "latest")
            
        Returns:
            Secret value or None if not found
        """
        project = self.discover_project()
        
        try:
            client = secretmanager.SecretManagerServiceClient(credentials=self.credentials)
            name = f"projects/{project.project_id}/secrets/{secret_id}/versions/{version}"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        
        except Exception as e:
            logger.error(f"Could not access secret {secret_id}: {e}")
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
