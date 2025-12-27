{%- if cookiecutter.use_google_adk == 'y' %}
"""Tests for Agent Factory."""
import pytest
from unittest.mock import MagicMock, patch


class TestAgentSpec:
    """Tests for AgentSpec dataclass."""
    
    def test_agent_spec_defaults(self):
        """Test AgentSpec default values."""
        from {{cookiecutter.package_name}}.agents.factory import AgentSpec, AgentType
        
        spec = AgentSpec(
            name="test-agent",
            agent_type=AgentType.RESEARCH,
        )
        
        assert spec.name == "test-agent"
        assert spec.model == "gemini-2.0-flash-exp"
        assert spec.temperature == 0.7
        assert spec.capabilities == []


class TestAgentType:
    """Tests for AgentType enum."""
    
    def test_agent_types_exist(self):
        """Test all expected agent types exist."""
        from {{cookiecutter.package_name}}.agents.factory import AgentType
        
        assert AgentType.RESEARCH.value == "research"
        assert AgentType.ANALYSIS.value == "analysis"
        assert AgentType.WRITER.value == "writer"
        assert AgentType.CODE.value == "code"
        assert AgentType.DATA.value == "data"


class TestAgentPrompts:
    """Tests for agent system prompts."""
    
    def test_prompts_contain_placeholder(self):
        """Test prompts have service placeholder."""
        from {{cookiecutter.package_name}}.agents.factory import AGENT_PROMPTS, AgentType
        
        for agent_type, prompt in AGENT_PROMPTS.items():
            assert "{target_service}" in prompt, f"{agent_type} missing placeholder"


class TestServiceAgentMapping:
    """Tests for service to agent mapping."""
    
    def test_bigquery_mapping(self):
        """Test BigQuery service mapping."""
        from {{cookiecutter.package_name}}.agents.factory import (
            SERVICE_AGENT_MAPPING,
            AgentType,
        )
        
        mapping = SERVICE_AGENT_MAPPING.get("bigquery", [])
        
        assert AgentType.DATA in mapping
        assert AgentType.ANALYSIS in mapping


class TestAgentFactory:
    """Tests for AgentFactory."""
    
    @pytest.fixture
    def mock_adk_agent(self):
        """Mock GoogleADKAgent."""
        with patch("{{cookiecutter.package_name}}.agents.factory.GoogleADKAgent") as mock:
            mock.return_value = MagicMock()
            yield mock
    
    @pytest.fixture
    def mock_adk_config(self):
        """Mock ADKConfig."""
        with patch("{{cookiecutter.package_name}}.agents.factory.ADKConfig") as mock:
            yield mock
    
    def test_factory_initialization(self):
        """Test factory initializes correctly."""
        from {{cookiecutter.package_name}}.agents.factory import AgentFactory
        
        factory = AgentFactory(api_key="test-key")
        
        assert factory._api_key == "test-key"
        assert factory._agents == {}
    
    def test_factory_create_agent(self, mock_adk_agent, mock_adk_config):
        """Test creating an agent."""
        from {{cookiecutter.package_name}}.agents.factory import (
            AgentFactory,
            AgentType,
        )
        
        factory = AgentFactory(api_key="test-key")
        agent = factory.create("test-agent", AgentType.RESEARCH)
        
        assert agent is not None
        assert "test-agent" in factory._agents
    
    def test_factory_caches_agents(self, mock_adk_agent, mock_adk_config):
        """Test factory caches created agents."""
        from {{cookiecutter.package_name}}.agents.factory import (
            AgentFactory,
            AgentType,
        )
        
        factory = AgentFactory(api_key="test-key")
        
        agent1 = factory.create("cached-agent", AgentType.RESEARCH)
        agent2 = factory.create("cached-agent", AgentType.RESEARCH)
        
        assert agent1 is agent2
    
    def test_factory_list_agents(self, mock_adk_agent, mock_adk_config):
        """Test listing created agents."""
        from {{cookiecutter.package_name}}.agents.factory import (
            AgentFactory,
            AgentType,
        )
        
        factory = AgentFactory(api_key="test-key")
        factory.create("agent1", AgentType.RESEARCH)
        factory.create("agent2", AgentType.ANALYSIS)
        
        agents = factory.list_agents()
        
        assert len(agents) == 2
        assert "agent1" in agents
        assert "agent2" in agents
    
    def test_factory_clear(self, mock_adk_agent, mock_adk_config):
        """Test clearing factory cache."""
        from {{cookiecutter.package_name}}.agents.factory import (
            AgentFactory,
            AgentType,
        )
        
        factory = AgentFactory(api_key="test-key")
        factory.create("agent", AgentType.RESEARCH)
        
        factory.clear()
        
        assert factory.list_agents() == []
    
    def test_factory_create_workers(self, mock_adk_agent, mock_adk_config):
        """Test creating worker agents."""
        from {{cookiecutter.package_name}}.agents.factory import (
            AgentFactory,
            AgentType,
        )
        
        factory = AgentFactory(api_key="test-key")
        workers = factory.create_workers()
        
        assert "research" in workers
        assert "analysis" in workers
        assert "writer" in workers
        assert "code" in workers
{%- endif %}
