{%- if cookiecutter.use_google_adk == 'y' and cookiecutter.use_google_cloud == 'y' %}
"""Tests for GENESIS Perceive module."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestEnvironmentContext:
    """Tests for EnvironmentContext dataclass."""
    
    def test_context_hash_is_consistent(self):
        """Test that hash is consistent for same data."""
        from {{cookiecutter.package_name}}.genesis.perceive import EnvironmentContext
        
        ctx1 = EnvironmentContext(
            project_id="test-project",
            region="us-central1",
            services=["service1", "service2"],
        )
        
        ctx2 = EnvironmentContext(
            project_id="test-project",
            region="us-central1",
            services=["service1", "service2"],
        )
        
        assert ctx1.hash() == ctx2.hash()
    
    def test_context_hash_differs_for_different_data(self):
        """Test that hash differs for different data."""
        from {{cookiecutter.package_name}}.genesis.perceive import EnvironmentContext
        
        ctx1 = EnvironmentContext(project_id="project1")
        ctx2 = EnvironmentContext(project_id="project2")
        
        assert ctx1.hash() != ctx2.hash()
    
    def test_context_to_prompt(self):
        """Test converting context to prompt."""
        from {{cookiecutter.package_name}}.genesis.perceive import EnvironmentContext
        
        ctx = EnvironmentContext(
            project_id="test-project",
            region="us-central1",
            services=["storage.googleapis.com", "bigquery.googleapis.com"],
            user_task="Test task",
        )
        
        prompt = ctx.to_prompt()
        
        assert "test-project" in prompt
        assert "us-central1" in prompt
        assert "Test task" in prompt
    
    def test_context_empty_factory(self):
        """Test empty context creation."""
        from {{cookiecutter.package_name}}.genesis.perceive import EnvironmentContext
        
        ctx = EnvironmentContext.empty()
        
        assert ctx.project_id == "unknown"
        assert len(ctx.changes) > 0
    
    def test_context_to_dict(self):
        """Test context serialization."""
        from {{cookiecutter.package_name}}.genesis.perceive import EnvironmentContext
        
        ctx = EnvironmentContext(
            project_id="test-project",
            services=["svc1"],
        )
        
        data = ctx.to_dict()
        
        assert data["project_id"] == "test-project"
        assert "hash" in data
        assert "timestamp" in data


class TestPerceiveModule:
    """Tests for PerceiveModule."""
    
    @pytest.fixture
    def mock_discovery(self):
        """Mock GCPDiscovery."""
        with patch(
            "{{cookiecutter.package_name}}.genesis.perceive.PerceiveModule.discovery",
            new_callable=lambda: property(lambda self: self._mock_discovery),
        ):
            yield
    
    @pytest.mark.asyncio
    async def test_scan_without_discovery(self):
        """Test scan works even without GCP discovery."""
        from {{cookiecutter.package_name}}.genesis.perceive import PerceiveModule
        
        # Create module without mocking - will use None discovery
        module = PerceiveModule()
        module._discovery = None  # Force no discovery
        
        context = await module.scan()
        
        assert context is not None
        assert context.project_id == "unknown"
    
    @pytest.mark.asyncio
    async def test_scan_detects_changes(self):
        """Test that changes are detected between scans."""
        from {{cookiecutter.package_name}}.genesis.perceive import PerceiveModule
        
        module = PerceiveModule()
        module._discovery = None
        
        # First scan
        ctx1 = await module.scan()
        assert any(c.get("type") == "initial_scan" for c in ctx1.changes)
        
        # Second scan (would detect changes if any)
        ctx2 = await module.scan()
        assert ctx2.changes is not None
    
    def test_get_last_context(self):
        """Test retrieving last scanned context."""
        from {{cookiecutter.package_name}}.genesis.perceive import PerceiveModule
        
        module = PerceiveModule()
        
        # Initially None
        assert module.get_last_context() is None
{%- endif %}
