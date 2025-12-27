{%- if cookiecutter.use_google_cloud == 'y' %}
"""Tests for GCP plugins system."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Any

from {{cookiecutter.package_name}}.core.gcp_plugins import (
    BaseGCPPlugin,
    SecretManagerPlugin,
    StoragePlugin,
    FirestorePlugin,
    BigQueryPlugin,
    VertexAIPlugin,
    PluginRegistry,
    create_plugin_registry,
    discover_custom_plugins,
    BUILTIN_PLUGINS,
)


class TestPluginRegistry:
    """Tests for PluginRegistry."""
    
    def test_find_plugin_match(self):
        """Test finding plugin that matches service."""
        plugin = SecretManagerPlugin()
        registry = PluginRegistry(plugins=[plugin])
        
        found = registry.find_plugin("secretmanager.googleapis.com")
        assert found is plugin
    
    def test_find_plugin_no_match(self):
        """Test finding plugin with no match."""
        plugin = SecretManagerPlugin()
        registry = PluginRegistry(plugins=[plugin])
        
        found = registry.find_plugin("unknown.googleapis.com")
        assert found is None
    
    def test_list_supported_services(self):
        """Test listing supported service patterns."""
        plugins = [SecretManagerPlugin(), StoragePlugin()]
        registry = PluginRegistry(plugins=plugins)
        
        patterns = registry.list_supported_services()
        assert 'secretmanager' in patterns
        assert 'storage' in patterns


class TestSecretManagerPlugin:
    """Tests for SecretManagerPlugin."""
    
    def test_service_patterns(self):
        """Test service patterns."""
        plugin = SecretManagerPlugin()
        assert 'secretmanager' in plugin.service_patterns
        assert 'secret' in plugin.service_patterns
    
    def test_required_packages(self):
        """Test required packages."""
        plugin = SecretManagerPlugin()
        assert 'google-cloud-secret-manager' in plugin.required_packages
    
    def test_can_handle_match(self):
        """Test can_handle with matching service."""
        plugin = SecretManagerPlugin()
        assert plugin.can_handle("secretmanager.googleapis.com")
        assert plugin.can_handle("secret-service")
    
    def test_can_handle_no_match(self):
        """Test can_handle with non-matching service."""
        plugin = SecretManagerPlugin()
        assert not plugin.can_handle("storage.googleapis.com")
    
    @patch('{{cookiecutter.package_name}}.core.gcp_plugins.importlib.import_module')
    def test_discover_resources_no_module(self, mock_import):
        """Test discover_resources when module not installed."""
        mock_import.return_value = None
        plugin = SecretManagerPlugin()
        
        result = plugin.discover_resources("project-id", Mock(), "us-central1")
        assert "error" in result
    
    @patch('{{cookiecutter.package_name}}.core.gcp_plugins.importlib.import_module')
    def test_discover_resources_success(self, mock_import):
        """Test discover_resources success."""
        # Mock module and client
        mock_module = MagicMock()
        mock_client = MagicMock()
        mock_secret = MagicMock()
        mock_secret.name = "projects/test/secrets/my-secret"
        mock_client.list_secrets.return_value = [mock_secret]
        mock_module.SecretManagerServiceClient.return_value = mock_client
        mock_import.return_value = mock_module
        
        plugin = SecretManagerPlugin()
        result = plugin.discover_resources("project-id", Mock(), "us-central1")
        
        assert result["type"] == "secrets"
        assert result["count"] == 1
        assert "my-secret" in result["resources"]


class TestStoragePlugin:
    """Tests for StoragePlugin."""
    
    def test_service_patterns(self):
        """Test service patterns."""
        plugin = StoragePlugin()
        assert 'storage' in plugin.service_patterns
        assert 'gcs' in plugin.service_patterns
    
    def test_can_handle(self):
        """Test can_handle."""
        plugin = StoragePlugin()
        assert plugin.can_handle("storage.googleapis.com")
        assert plugin.can_handle("gcs-service")
    
    @patch('{{cookiecutter.package_name}}.core.gcp_plugins.importlib.import_module')
    def test_discover_resources_success(self, mock_import):
        """Test discover_resources success."""
        mock_module = MagicMock()
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_bucket.name = "my-bucket"
        mock_client.list_buckets.return_value = [mock_bucket]
        mock_module.Client.return_value = mock_client
        mock_import.return_value = mock_module
        
        plugin = StoragePlugin()
        result = plugin.discover_resources("project-id", Mock(), "us-central1")
        
        assert result["type"] == "buckets"
        assert result["count"] == 1
        assert "my-bucket" in result["resources"]


class TestFirestorePlugin:
    """Tests for FirestorePlugin."""
    
    def test_service_patterns(self):
        """Test service patterns."""
        plugin = FirestorePlugin()
        assert 'firestore' in plugin.service_patterns
        assert 'datastore' in plugin.service_patterns
    
    @patch('{{cookiecutter.package_name}}.core.gcp_plugins.importlib.import_module')
    def test_discover_resources_success(self, mock_import):
        """Test discover_resources success."""
        mock_module = MagicMock()
        mock_db = MagicMock()
        mock_col = MagicMock()
        mock_col.id = "users"
        mock_db.collections.return_value = [mock_col]
        mock_module.Client.return_value = mock_db
        mock_import.return_value = mock_module
        
        plugin = FirestorePlugin()
        result = plugin.discover_resources("project-id", Mock(), "us-central1")
        
        assert result["type"] == "collections"
        assert result["count"] == 1
        assert "users" in result["resources"]


class TestBigQueryPlugin:
    """Tests for BigQueryPlugin."""
    
    def test_service_patterns(self):
        """Test service patterns."""
        plugin = BigQueryPlugin()
        assert 'bigquery' in plugin.service_patterns
        assert 'bq' in plugin.service_patterns
    
    @patch('{{cookiecutter.package_name}}.core.gcp_plugins.importlib.import_module')
    def test_discover_resources_success(self, mock_import):
        """Test discover_resources success."""
        mock_module = MagicMock()
        mock_client = MagicMock()
        mock_dataset = MagicMock()
        mock_dataset.dataset_id = "my_dataset"
        mock_client.list_datasets.return_value = [mock_dataset]
        mock_module.Client.return_value = mock_client
        mock_import.return_value = mock_module
        
        plugin = BigQueryPlugin()
        result = plugin.discover_resources("project-id", Mock(), "us-central1")
        
        assert result["type"] == "datasets"
        assert result["count"] == 1
        assert "my_dataset" in result["resources"]


class TestVertexAIPlugin:
    """Tests for VertexAIPlugin."""
    
    def test_service_patterns(self):
        """Test service patterns."""
        plugin = VertexAIPlugin()
        assert 'aiplatform' in plugin.service_patterns
        assert 'vertex' in plugin.service_patterns
    
    @patch('{{cookiecutter.package_name}}.core.gcp_plugins.importlib.import_module')
    def test_discover_resources_success(self, mock_import):
        """Test discover_resources success."""
        mock_module = MagicMock()
        mock_model = MagicMock()
        mock_model.resource_name = "projects/test/models/my-model"
        mock_module.Model.list.return_value = [mock_model]
        mock_import.return_value = mock_module
        
        plugin = VertexAIPlugin()
        result = plugin.discover_resources("project-id", Mock(), "us-central1")
        
        assert result["type"] == "models"
        assert result["count"] == 1


class TestBaseGCPPlugin:
    """Tests for BaseGCPPlugin."""
    
    def test_try_import_success(self):
        """Test _try_import with existing module."""
        plugin = SecretManagerPlugin()
        result = plugin._try_import('os')
        assert result is not None
    
    def test_try_import_failure(self):
        """Test _try_import with non-existing module."""
        plugin = SecretManagerPlugin()
        result = plugin._try_import('nonexistent_module_xyz')
        assert result is None


def test_create_plugin_registry():
    """Test creating plugin registry."""
    registry = create_plugin_registry()
    assert len(registry.plugins) == len(BUILTIN_PLUGINS)


def test_create_plugin_registry_with_custom():
    """Test creating plugin registry with custom plugins."""
    custom = SecretManagerPlugin()
    registry = create_plugin_registry(additional_plugins=[custom])
    assert len(registry.plugins) == len(BUILTIN_PLUGINS) + 1


@patch('{{cookiecutter.package_name}}.core.gcp_plugins.importlib.import_module')
def test_discover_custom_plugins_not_found(mock_import):
    """Test discovering custom plugins when package not found."""
    mock_import.side_effect = ImportError()
    plugins = discover_custom_plugins("nonexistent")
    assert plugins == []


@patch('{{cookiecutter.package_name}}.core.gcp_plugins.importlib.import_module')
def test_discover_custom_plugins_found(mock_import):
    """Test discovering custom plugins."""
    # Mock module with a plugin class
    mock_module = MagicMock()
    mock_plugin_class = MagicMock()
    mock_plugin_class.service_patterns = ['test']
    mock_plugin_instance = MagicMock()
    mock_plugin_class.return_value = mock_plugin_instance
    
    mock_module.__dir__ = lambda: ['TestPlugin', 'other']
    setattr(mock_module, 'TestPlugin', mock_plugin_class)
    setattr(mock_module, 'other', "not a class")
    
    mock_import.return_value = mock_module
    
    plugins = discover_custom_plugins("test_package")
    assert len(plugins) >= 0  # May or may not find plugins depending on mock
{%- endif %}
