{%- if cookiecutter.use_google_cloud == 'y' %}
"""Tests for GCP discovery system."""
import pytest
from unittest.mock import Mock, MagicMock, patch
import os

from {{cookiecutter.package_name}}.core.gcp_discovery import (
    GCPProject,
    GCPService,
    GCPResources,
    GCPDiscovery,
    get_gcp_discovery,
    discover_gcp_resources,
)


class TestGCPProject:
    """Tests for GCPProject."""
    
    def test_initialization(self):
        """Test project initialization."""
        project = GCPProject(
            project_id="test-project",
            project_number="123456",
            region="us-west1"
        )
        assert project.project_id == "test-project"
        assert project.project_number == "123456"
        assert project.region == "us-west1"
    
    def test_repr(self):
        """Test project repr."""
        project = GCPProject(project_id="test", region="us-central1")
        assert "test" in repr(project)
        assert "us-central1" in repr(project)


class TestGCPService:
    """Tests for GCPService."""
    
    def test_initialization(self):
        """Test service initialization."""
        service = GCPService(
            name="storage.googleapis.com",
            display_name="Cloud Storage",
            state="ENABLED",
            enabled=True
        )
        assert service.name == "storage.googleapis.com"
        assert service.enabled is True
    
    def test_repr(self):
        """Test service repr."""
        service = GCPService(
            name="storage",
            display_name="Storage",
            state="ENABLED",
            enabled=True
        )
        assert "✓" in repr(service)
        assert "Storage" in repr(service)


class TestGCPResources:
    """Tests for GCPResources."""
    
    def test_to_dict(self):
        """Test converting resources to dict."""
        project = GCPProject(project_id="test", region="us-central1")
        service = GCPService(
            name="storage.googleapis.com",
            display_name="Storage",
            state="ENABLED",
            enabled=True
        )
        
        resources = GCPResources(
            project=project,
            services=[service],
            service_resources={
                "storage.googleapis.com": {
                    "type": "buckets",
                    "count": 5,
                    "resources": ["bucket1", "bucket2"]
                }
            }
        )
        
        result = resources.to_dict()
        assert result["project_id"] == "test"
        assert result["region"] == "us-central1"
        assert result["enabled_services"] == 1
        assert "storage_count" in result
        assert result["storage_count"] == 5


class TestGCPDiscovery:
    """Tests for GCPDiscovery."""
    
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.HAS_GCP', True)
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.HAS_PLUGINS', True)
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.create_plugin_registry')
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.discover_custom_plugins')
    def test_initialization(self, mock_discover, mock_create_registry):
        """Test discovery initialization."""
        mock_discover.return_value = []
        mock_registry = Mock()
        mock_registry.plugins = []
        mock_create_registry.return_value = mock_registry
        
        discovery = GCPDiscovery(project_id="test-project")
        assert discovery.project_id == "test-project"
        assert discovery.plugin_registry is not None
    
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.HAS_GCP', False)
    def test_initialization_no_gcp(self):
        """Test initialization without GCP libraries."""
        with pytest.raises(ImportError, match="Google Cloud libraries"):
            GCPDiscovery()
    
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.HAS_GCP', True)
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.HAS_PLUGINS', True)
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.google.auth.default')
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.create_plugin_registry')
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.discover_custom_plugins')
    def test_discover_project(self, mock_discover, mock_registry, mock_auth):
        """Test project discovery."""
        mock_discover.return_value = []
        mock_registry.return_value = Mock(plugins=[])
        mock_credentials = Mock()
        mock_auth.return_value = (mock_credentials, "discovered-project")
        
        discovery = GCPDiscovery()
        project = discovery.discover_project()
        
        assert project.project_id == "discovered-project"
        assert project.credentials == mock_credentials
    
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.HAS_GCP', True)
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.HAS_PLUGINS', True)
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.google.auth.default')
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.create_plugin_registry')
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.discover_custom_plugins')
    def test_discover_project_explicit(self, mock_discover, mock_registry, mock_auth):
        """Test project discovery with explicit project ID."""
        mock_discover.return_value = []
        mock_registry.return_value = Mock(plugins=[])
        mock_credentials = Mock()
        mock_auth.return_value = (mock_credentials, None)
        
        discovery = GCPDiscovery(project_id="explicit-project")
        project = discovery.discover_project()
        
        assert project.project_id == "explicit-project"
    
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.HAS_GCP', True)
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.HAS_PLUGINS', True)
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.google.auth.default')
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.create_plugin_registry')
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.discover_custom_plugins')
    def test_discover_project_no_id(self, mock_discover, mock_registry, mock_auth, monkeypatch):
        """Test project discovery without project ID."""
        mock_discover.return_value = []
        mock_registry.return_value = Mock(plugins=[])
        mock_credentials = Mock()
        mock_auth.return_value = (mock_credentials, None)
        monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
        monkeypatch.delenv("GCP_PROJECT", raising=False)
        monkeypatch.delenv("GCLOUD_PROJECT", raising=False)
        
        discovery = GCPDiscovery()
        with pytest.raises(ValueError, match="Could not discover project ID"):
            discovery.discover_project()
    
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.HAS_GCP', True)
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.HAS_PLUGINS', True)
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.google.auth.default')
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.service_usage_v1.ServiceUsageClient')
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.create_plugin_registry')
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.discover_custom_plugins')
    def test_discover_enabled_services(self, mock_discover, mock_registry, mock_client, mock_auth):
        """Test discovering enabled services."""
        mock_discover.return_value = []
        mock_registry.return_value = Mock(plugins=[])
        mock_auth.return_value = (Mock(), "test-project")
        
        # Mock service
        mock_service = Mock()
        mock_service.name = "projects/test/services/storage.googleapis.com"
        mock_service.config.title = "Cloud Storage"
        mock_service.state = 1  # ENABLED
        
        mock_client_instance = Mock()
        mock_client_instance.list_services.return_value = [mock_service]
        mock_client.return_value = mock_client_instance
        
        discovery = GCPDiscovery()
        services = discovery.discover_enabled_services()
        
        assert len(services) == 1
        assert services[0].name == "storage.googleapis.com"
    
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.HAS_GCP', True)
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.HAS_PLUGINS', True)
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.google.auth.default')
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.create_plugin_registry')
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.discover_custom_plugins')
    def test_add_custom_plugin(self, mock_discover, mock_registry, mock_auth):
        """Test adding custom plugin."""
        mock_discover.return_value = []
        mock_registry_instance = Mock()
        mock_registry_instance.plugins = []
        mock_registry.return_value = mock_registry_instance
        mock_auth.return_value = (Mock(), "test-project")
        
        discovery = GCPDiscovery()
        custom_plugin = Mock()
        discovery.add_custom_plugin(custom_plugin)
        
        assert custom_plugin in discovery.plugin_registry.plugins
    
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.HAS_GCP', True)
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.HAS_PLUGINS', True)
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.google.auth.default')
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.create_plugin_registry')
    @patch('{{cookiecutter.package_name}}.core.gcp_discovery.discover_custom_plugins')
    def test_get_service_resources(self, mock_discover, mock_registry, mock_auth):
        """Test getting service resources."""
        mock_discover.return_value = []
        mock_registry.return_value = Mock(plugins=[])
        mock_auth.return_value = (Mock(), "test-project")
        
        discovery = GCPDiscovery()
        discovery._resources = GCPResources(
            project=GCPProject(project_id="test", region="us-central1"),
            services=[],
            service_resources={
                "storage.googleapis.com": {
                    "type": "buckets",
                    "count": 5
                }
            }
        )
        
        resources = discovery.get_service_resources("storage")
        assert resources is not None
        assert resources["type"] == "buckets"


@patch('{{cookiecutter.package_name}}.core.gcp_discovery.HAS_GCP', True)
@patch('{{cookiecutter.package_name}}.core.gcp_discovery.HAS_PLUGINS', True)
@patch('{{cookiecutter.package_name}}.core.gcp_discovery.google.auth.default')
@patch('{{cookiecutter.package_name}}.core.gcp_discovery.create_plugin_registry')
@patch('{{cookiecutter.package_name}}.core.gcp_discovery.discover_custom_plugins')
def test_get_gcp_discovery(mock_discover, mock_registry, mock_auth):
    """Test getting global discovery instance."""
    mock_discover.return_value = []
    mock_registry.return_value = Mock(plugins=[])
    mock_auth.return_value = (Mock(), "test-project")
    
    discovery1 = get_gcp_discovery()
    discovery2 = get_gcp_discovery()
    
    assert discovery1 is discovery2  # Singleton


@patch('{{cookiecutter.package_name}}.core.gcp_discovery.HAS_GCP', True)
@patch('{{cookiecutter.package_name}}.core.gcp_discovery.HAS_PLUGINS', True)
@patch('{{cookiecutter.package_name}}.core.gcp_discovery.google.auth.default')
@patch('{{cookiecutter.package_name}}.core.gcp_discovery.create_plugin_registry')
@patch('{{cookiecutter.package_name}}.core.gcp_discovery.discover_custom_plugins')
def test_discover_gcp_resources(mock_discover, mock_registry, mock_auth):
    """Test convenience function for discovering resources."""
    mock_discover.return_value = []
    mock_registry_instance = Mock()
    mock_registry_instance.plugins = []
    mock_registry.return_value = mock_registry_instance
    mock_auth.return_value = (Mock(), "test-project")
    
    # Mock discover_all to avoid actual API calls
    with patch.object(GCPDiscovery, 'discover_all') as mock_discover_all:
        mock_resources = GCPResources(
            project=GCPProject(project_id="test", region="us-central1"),
            services=[],
            service_resources={}
        )
        mock_discover_all.return_value = mock_resources
        
        resources = discover_gcp_resources()
        assert resources.project.project_id == "test"
{%- endif %}
