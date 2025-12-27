"""Tests for base agent classes."""
import pytest
from typing import Any, Dict

from {{cookiecutter.package_name}}.agents.base import (
    AgentCapability,
    AgentSpec,
    AgentResult,
    BaseAgent,
    AgentRegistry,
    get_registry,
    register_agent,
)


class TestAgentSpec:
    """Tests for AgentSpec dataclass."""
    
    def test_create_valid_spec(self):
        """Test creating a valid AgentSpec."""
        spec = AgentSpec(
            name="test_agent",
            role="Test role",
            system_prompt="You are a test agent.",
            capabilities=(AgentCapability.RESEARCH,),
        )
        
        assert spec.name == "test_agent"
        assert spec.role == "Test role"
        assert spec.system_prompt == "You are a test agent."
        assert AgentCapability.RESEARCH in spec.capabilities
        assert spec.model == "gemini-2.0-flash-exp"  # Default
    
    def test_spec_validation_empty_name(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            AgentSpec(
                name="",
                role="Test",
                system_prompt="Test",
            )
    
    def test_spec_validation_empty_prompt(self):
        """Test that empty system_prompt raises ValueError."""
        with pytest.raises(ValueError, match="System prompt cannot be empty"):
            AgentSpec(
                name="test",
                role="Test",
                system_prompt="",
            )
    
    def test_spec_to_dict(self):
        """Test serialization to dictionary."""
        spec = AgentSpec(
            name="test",
            role="Role",
            system_prompt="Prompt",
            capabilities=(AgentCapability.RESEARCH, AgentCapability.ANALYSIS),
        )
        
        d = spec.to_dict()
        
        assert d["name"] == "test"
        assert "RESEARCH" in d["capabilities"]
        assert "ANALYSIS" in d["capabilities"]
    
    def test_spec_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "name": "restored",
            "role": "Restored role",
            "system_prompt": "Restored prompt",
            "capabilities": ["WRITING", "CODING"],
            "model": "gemini-2.0-flash-exp",
            "temperature": 0.5,
            "max_tokens": 4096,
            "tools": [],
            "metadata": {},
        }
        
        spec = AgentSpec.from_dict(data)
        
        assert spec.name == "restored"
        assert AgentCapability.WRITING in spec.capabilities
        assert AgentCapability.CODING in spec.capabilities
        assert spec.temperature == 0.5
    
    def test_spec_json_roundtrip(self):
        """Test JSON serialization roundtrip."""
        original = AgentSpec(
            name="json_test",
            role="JSON Test",
            system_prompt="Test prompt",
            capabilities=(AgentCapability.META,),
            temperature=0.9,
        )
        
        json_str = original.to_json()
        restored = AgentSpec.from_json(json_str)
        
        assert restored.name == original.name
        assert restored.temperature == original.temperature
        assert restored.capabilities == original.capabilities
    
    def test_spec_is_hashable(self):
        """Test that frozen spec is hashable (can be dict key)."""
        spec = AgentSpec(
            name="hashable",
            role="Test",
            system_prompt="Test",
        )
        
        # Should not raise
        d = {spec: "value"}
        assert d[spec] == "value"


class TestAgentResult:
    """Tests for AgentResult dataclass."""
    
    def test_create_success_result(self):
        """Test creating a successful result."""
        result = AgentResult(
            output="Test output",
            success=True,
            agent_name="test_agent",
            execution_time=1.5,
        )
        
        assert result.output == "Test output"
        assert result.success is True
        assert result.error is None
        assert result.execution_time == 1.5
    
    def test_create_failure_result(self):
        """Test creating a failure result."""
        result = AgentResult(
            output=None,
            success=False,
            error="Test error",
            agent_name="test_agent",
        )
        
        assert result.output is None
        assert result.success is False
        assert result.error == "Test error"
    
    def test_result_to_dict(self):
        """Test result serialization."""
        result = AgentResult(
            output="output",
            success=True,
            agent_name="agent",
            token_usage={"input": 100, "output": 50},
        )
        
        d = result.to_dict()
        
        assert d["output"] == "output"
        assert d["success"] is True
        assert d["token_usage"]["input"] == 100


class ConcreteAgent(BaseAgent):
    """Concrete implementation for testing."""
    
    def __init__(self, name: str = "concrete"):
        self._name = name
    
    @property
    def spec(self) -> AgentSpec:
        return AgentSpec(
            name=self._name,
            role="Test agent",
            system_prompt="Test prompt",
            capabilities=(AgentCapability.REASONING,),
        )
    
    async def run(self, input_data: Any) -> AgentResult:
        return AgentResult(
            output=f"Processed: {input_data}",
            success=True,
            agent_name=self._name,
        )
    
    async def introspect(self) -> Dict[str, Any]:
        return {
            "type": "concrete",
            "status": "ready",
            "spec": self.spec.to_dict(),
        }


class TestBaseAgent:
    """Tests for BaseAgent abstract class."""
    
    def test_concrete_agent_spec(self):
        """Test that concrete agent has valid spec."""
        agent = ConcreteAgent()
        
        assert agent.spec.name == "concrete"
        assert agent.spec.role == "Test agent"
    
    @pytest.mark.asyncio
    async def test_concrete_agent_run(self):
        """Test that concrete agent runs correctly."""
        agent = ConcreteAgent()
        result = await agent.run("test input")
        
        assert result.success is True
        assert "Processed: test input" in result.output
    
    @pytest.mark.asyncio
    async def test_concrete_agent_introspect(self):
        """Test agent introspection."""
        agent = ConcreteAgent()
        info = await agent.introspect()
        
        assert info["type"] == "concrete"
        assert info["status"] == "ready"
        assert "spec" in info
    
    def test_agent_to_genome(self):
        """Test genome extraction (source code)."""
        agent = ConcreteAgent()
        genome = agent.to_genome()
        
        assert "class ConcreteAgent" in genome
        assert "BaseAgent" in genome
    
    def test_agent_capabilities(self):
        """Test capability methods."""
        agent = ConcreteAgent()
        
        assert AgentCapability.REASONING in agent.get_capabilities()
        assert agent.has_capability(AgentCapability.REASONING)
        assert not agent.has_capability(AgentCapability.META)
    
    def test_agent_repr(self):
        """Test string representation."""
        agent = ConcreteAgent()
        repr_str = repr(agent)
        
        assert "ConcreteAgent" in repr_str
        assert "concrete" in repr_str
        assert "REASONING" in repr_str


class TestAgentRegistry:
    """Tests for AgentRegistry."""
    
    def test_register_and_get(self):
        """Test registering and retrieving agents."""
        registry = AgentRegistry()
        agent = ConcreteAgent("registry_test")
        
        registry.register(agent)
        retrieved = registry.get("registry_test")
        
        assert retrieved is agent
    
    def test_register_duplicate_raises(self):
        """Test that registering duplicate name raises."""
        registry = AgentRegistry()
        agent1 = ConcreteAgent("duplicate")
        agent2 = ConcreteAgent("duplicate")
        
        registry.register(agent1)
        
        with pytest.raises(ValueError, match="already registered"):
            registry.register(agent2)
    
    def test_unregister(self):
        """Test unregistering agents."""
        registry = AgentRegistry()
        agent = ConcreteAgent("unregister_test")
        
        registry.register(agent)
        removed = registry.unregister("unregister_test")
        
        assert removed is agent
        assert registry.get("unregister_test") is None
    
    def test_find_by_capability(self):
        """Test finding agents by capability."""
        registry = AgentRegistry()
        agent = ConcreteAgent("capability_test")
        registry.register(agent)
        
        found = registry.find_by_capability(AgentCapability.REASONING)
        
        assert len(found) == 1
        assert found[0] is agent
        
        not_found = registry.find_by_capability(AgentCapability.META)
        assert len(not_found) == 0
    
    def test_list_all(self):
        """Test listing all agents."""
        registry = AgentRegistry()
        agent1 = ConcreteAgent("list_test_1")
        agent2 = ConcreteAgent("list_test_2")
        
        registry.register(agent1)
        registry.register(agent2)
        
        all_agents = registry.list_all()
        
        assert len(all_agents) == 2
    
    def test_len_and_contains(self):
        """Test len() and 'in' operators."""
        registry = AgentRegistry()
        agent = ConcreteAgent("contains_test")
        
        assert len(registry) == 0
        assert "contains_test" not in registry
        
        registry.register(agent)
        
        assert len(registry) == 1
        assert "contains_test" in registry


class TestGlobalRegistry:
    """Tests for global registry functions."""
    
    def test_get_registry_singleton(self):
        """Test that get_registry returns singleton."""
        reg1 = get_registry()
        reg2 = get_registry()
        
        assert reg1 is reg2
