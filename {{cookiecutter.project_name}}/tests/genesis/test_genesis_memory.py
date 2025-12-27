{%- if cookiecutter.use_google_adk == 'y' and cookiecutter.use_google_cloud == 'y' %}
"""Tests for GENESIS Memory module."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestMemoryState:
    """Tests for MemoryState dataclass."""
    
    def test_memory_state_to_dict(self):
        """Test MemoryState serialization."""
        from {{cookiecutter.package_name}}.genesis.memory import MemoryState
        
        state = MemoryState(
            total_cycles=100,
            success_rate=0.95,
            agents_generated=5,
            plugins_generated=3,
        )
        
        data = state.to_dict()
        
        assert data["total_cycles"] == 100
        assert data["success_rate"] == 0.95
        assert data["agents_generated"] == 5


class TestMemoryModule:
    """Tests for MemoryModule."""
    
    @pytest.mark.asyncio
    async def test_local_cache_fallback(self):
        """Test local cache is used when Firestore unavailable."""
        from {{cookiecutter.package_name}}.genesis.memory import MemoryModule
        
        module = MemoryModule()
        module._use_local = True
        
        # Should use local cache
        state = await module.get_state()
        
        assert state is not None
        assert state.total_cycles == 0
    
    @pytest.mark.asyncio
    async def test_store_cycle_locally(self):
        """Test storing cycle in local cache."""
        from {{cookiecutter.package_name}}.genesis.memory import MemoryModule
        
        module = MemoryModule()
        module._use_local = True
        
        # Create mock objects
        context = MagicMock()
        context.hash.return_value = "test_hash"
        context.project_id = "test"
        context.services = []
        context.resources = {}
        context.changes = []
        context.user_task = None
        
        plan = MagicMock()
        plan.reasoning = "Test"
        plan.actions = []
        plan.confidence = 0.5
        
        result = MagicMock()
        result.to_dict.return_value = {"success": True, "actions": []}
        
        # Store cycle
        await module.store_cycle(
            cycle_id="test_123",
            context=context,
            plan=plan,
            result=result,
        )
        
        # Verify stored
        assert "cycles" in module._local_cache
        assert "test_123" in module._local_cache["cycles"]
    
    @pytest.mark.asyncio
    async def test_store_agent_locally(self):
        """Test storing agent info in local cache."""
        from {{cookiecutter.package_name}}.genesis.memory import MemoryModule
        
        module = MemoryModule()
        module._use_local = True
        
        await module.store_agent(
            "test_agent",
            {"type": "research", "target": "bigquery"},
        )
        
        assert "agents" in module._local_cache
        assert "test_agent" in module._local_cache["agents"]
    
    @pytest.mark.asyncio
    async def test_get_cycles_empty(self):
        """Test getting cycles when none exist."""
        from {{cookiecutter.package_name}}.genesis.memory import MemoryModule
        
        module = MemoryModule()
        module._use_local = True
        
        cycles = await module.get_cycles()
        
        assert cycles == []
    
    @pytest.mark.asyncio
    async def test_get_metrics(self):
        """Test getting metrics."""
        from {{cookiecutter.package_name}}.genesis.memory import MemoryModule
        
        module = MemoryModule()
        module._use_local = True
        
        metrics = await module.get_metrics()
        
        assert "total_cycles" in metrics
        assert "success_rate" in metrics
        assert "avg_cycle_duration_ms" in metrics
{%- endif %}
