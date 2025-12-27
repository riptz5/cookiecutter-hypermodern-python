{%- if cookiecutter.use_google_cloud == 'y' %}
"""Tests for Cloud Run deployer."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestDeploymentConfig:
    """Tests for DeploymentConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        from {{cookiecutter.package_name}}.cloud.run import DeploymentConfig
        
        config = DeploymentConfig()
        
        assert config.service_name == "genesis"
        assert config.region == "us-central1"
        assert config.memory == "256Mi"
        assert config.min_instances == 0
        assert config.max_instances == 1
        assert config.allow_unauthenticated is False
    
    def test_custom_config(self):
        """Test custom configuration."""
        from {{cookiecutter.package_name}}.cloud.run import DeploymentConfig
        
        config = DeploymentConfig(
            service_name="custom-service",
            region="europe-west1",
            memory="512Mi",
            max_instances=10,
            env_vars={"KEY": "value"},
        )
        
        assert config.service_name == "custom-service"
        assert config.region == "europe-west1"
        assert config.max_instances == 10
        assert config.env_vars["KEY"] == "value"
    
    def test_env_vars_default_to_dict(self):
        """Test env_vars defaults to empty dict."""
        from {{cookiecutter.package_name}}.cloud.run import DeploymentConfig
        
        config = DeploymentConfig()
        
        assert config.env_vars == {}


class TestCloudRunDeployer:
    """Tests for CloudRunDeployer."""
    
    def test_initialization(self):
        """Test deployer initialization."""
        with patch.dict("os.environ", {"GOOGLE_CLOUD_PROJECT": "test-project"}):
            from {{cookiecutter.package_name}}.cloud.run import CloudRunDeployer
            
            deployer = CloudRunDeployer()
            
            assert deployer._project_id == "test-project"
            assert deployer.config is not None
    
    def test_initialization_with_config(self):
        """Test deployer with custom config."""
        from {{cookiecutter.package_name}}.cloud.run import (
            CloudRunDeployer,
            DeploymentConfig,
        )
        
        config = DeploymentConfig(service_name="custom")
        deployer = CloudRunDeployer(config=config)
        
        assert deployer.config.service_name == "custom"
    
    @pytest.mark.asyncio
    async def test_deploy_requires_image(self):
        """Test deploy fails without image."""
        from {{cookiecutter.package_name}}.cloud.run import CloudRunDeployer
        
        deployer = CloudRunDeployer(project_id="test")
        
        with pytest.raises(ValueError, match="No image"):
            await deployer.deploy()
{%- endif %}
