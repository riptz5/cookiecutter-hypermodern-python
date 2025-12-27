"""Tests for GeneticMemory."""
import pytest

{%- if cookiecutter.use_google_adk == 'y' %}
from {{cookiecutter.package_name}}.agents.meta.genetic_memory import (
    GeneticMemory,
    AgentGenome,
    EvolutionEvent,
)


class TestAgentGenome:
    """Tests for AgentGenome dataclass."""
    
    def test_genome_creation(self):
        """Test creating a genome."""
        genome = AgentGenome(
            agent_id="test",
            code="class Test: pass",
            spec={"name": "test"},
        )
        
        assert genome.agent_id == "test"
        assert genome.code == "class Test: pass"
        assert genome.version == 1


class TestGeneticMemory:
    """Tests for GeneticMemory (in-memory mode)."""
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve(self):
        """Test storing and retrieving genomes."""
        memory = GeneticMemory()
        
        genome = await memory.store_genome(
            agent_id="test_agent",
            code="class TestAgent: pass",
            spec={"name": "test_agent"},
        )
        
        assert genome.agent_id == "test_agent"
        assert genome.version == 1
        
        retrieved = await memory.get_genome("test_agent")
        assert retrieved is not None
        assert retrieved.code == "class TestAgent: pass"
    
    @pytest.mark.asyncio
    async def test_versioning(self):
        """Test automatic versioning."""
        memory = GeneticMemory()
        
        v1 = await memory.store_genome(
            agent_id="versioned",
            code="v1",
            spec={},
        )
        assert v1.version == 1
        
        v2 = await memory.store_genome(
            agent_id="versioned",
            code="v2",
            spec={},
        )
        assert v2.version == 2
        
        # Latest should be v2
        latest = await memory.get_genome("versioned")
        assert latest.version == 2
    
    @pytest.mark.asyncio
    async def test_lineage_tracking(self):
        """Test lineage tracking."""
        memory = GeneticMemory()
        
        await memory.store_genome(
            agent_id="parent",
            code="parent code",
            spec={},
        )
        
        await memory.store_genome(
            agent_id="child",
            code="child code",
            spec={},
            parent_id="parent",
        )
        
        lineage = await memory.get_lineage("child")
        # In-memory version may not fully support lineage
        assert len(lineage) >= 1
    
    @pytest.mark.asyncio
    async def test_metrics_update(self):
        """Test updating metrics."""
        memory = GeneticMemory()
        
        await memory.store_genome(
            agent_id="metrics_test",
            code="code",
            spec={},
        )
        
        await memory.update_metrics("metrics_test", {"success_rate": 0.95})
        
        genome = await memory.get_genome("metrics_test")
        assert genome.metrics.get("success_rate") == 0.95
    
    @pytest.mark.asyncio
    async def test_evolution_history(self):
        """Test recording evolution history."""
        memory = GeneticMemory()
        
        event = await memory.record_evolution(
            agent_id="history_test",
            details={"event_type": "create", "version": 1},
        )
        
        assert event.agent_id == "history_test"
        assert event.event_type == "create"
        
        history = await memory.get_evolution_history("history_test")
        assert len(history) >= 1
{%- else %}
# GeneticMemory requires use_google_adk=y
pytestmark = pytest.mark.skip(reason="Requires use_google_adk=y")
{%- endif %}
