{%- if cookiecutter.use_google_adk == 'y' %}
"""Tests for Google ADK agent."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import os

from {{cookiecutter.package_name}}.agents.adk import (
    GoogleADKAgent,
    ADKConfig,
    create_adk_agent,
)


class TestADKConfig:
    """Tests for ADKConfig."""
    
    def test_config_with_api_key(self):
        """Test config with explicit API key."""
        config = ADKConfig(api_key="test-key")
        assert config.api_key == "test-key"
        assert config.model == "gemini-2.0-flash-exp"
        assert config.temperature == 0.7
    
    def test_config_from_env(self, monkeypatch):
        """Test config reads from environment."""
        monkeypatch.setenv("GOOGLE_API_KEY", "env-key")
        config = ADKConfig()
        assert config.api_key == "env-key"
    
    def test_config_missing_key(self, monkeypatch):
        """Test config fails without API key."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        with pytest.raises(ValueError, match="Google API key required"):
            ADKConfig()
    
    def test_config_custom_values(self):
        """Test config with custom values."""
        config = ADKConfig(
            model="gemini-pro",
            api_key="key",
            temperature=0.5,
            max_tokens=4096,
            system_instruction="Test instruction"
        )
        assert config.model == "gemini-pro"
        assert config.temperature == 0.5
        assert config.max_tokens == 4096
        assert config.system_instruction == "Test instruction"


class TestGoogleADKAgent:
    """Tests for GoogleADKAgent."""
    
    @pytest.fixture
    def mock_client(self):
        """Mock Google GenAI client."""
        with patch('{{cookiecutter.package_name}}.agents.adk.agent.genai.Client') as mock:
            yield mock
    
    @pytest.fixture
    def config(self):
        """Test configuration."""
        return ADKConfig(api_key="test-key")
    
    @pytest.fixture
    def agent(self, config, mock_client):
        """Test agent instance."""
        return GoogleADKAgent(config)
    
    def test_agent_initialization(self, agent, config):
        """Test agent initializes correctly."""
        assert agent.config == config
        assert agent.history == []
    
    @pytest.mark.asyncio
    async def test_run_basic(self, agent, mock_client):
        """Test basic run method."""
        # Mock response
        mock_response = Mock()
        mock_response.text = "Test response"
        mock_client.return_value.models.generate_content.return_value = mock_response
        
        result = await agent.run("Test prompt")
        
        assert result == "Test response"
        assert len(agent.history) == 2
        assert agent.history[0]["role"] == "user"
        assert agent.history[0]["content"] == "Test prompt"
        assert agent.history[1]["role"] == "assistant"
        assert agent.history[1]["content"] == "Test response"
    
    @pytest.mark.asyncio
    async def test_run_with_kwargs(self, agent, mock_client):
        """Test run with custom parameters."""
        mock_response = Mock()
        mock_response.text = "Response"
        mock_client.return_value.models.generate_content.return_value = mock_response
        
        result = await agent.run(
            "Prompt",
            temperature=0.9,
            max_tokens=1000
        )
        
        assert result == "Response"
    
    @pytest.mark.asyncio
    async def test_run_with_tools(self, agent, mock_client):
        """Test run with function calling tools."""
        mock_response = Mock()
        mock_response.text = "Tool response"
        mock_client.return_value.models.generate_content.return_value = mock_response
        
        mock_tool = Mock()
        result = await agent.run_with_tools(
            "Test prompt",
            tools=[mock_tool]
        )
        
        assert result == "Tool response"
    
    @pytest.mark.asyncio
    async def test_run_streaming(self, agent, mock_client):
        """Test streaming response."""
        # Mock streaming response
        mock_chunks = [
            Mock(text="chunk1"),
            Mock(text="chunk2"),
            Mock(text="chunk3"),
        ]
        mock_client.return_value.models.generate_content_stream.return_value = mock_chunks
        
        chunks = []
        async for chunk in agent.run_streaming("Test prompt"):
            chunks.append(chunk)
        
        assert chunks == ["chunk1", "chunk2", "chunk3"]
        assert len(agent.history) == 2
        assert agent.history[1]["content"] == "chunk1chunk2chunk3"
    
    def test_clear_history(self, agent):
        """Test clearing conversation history."""
        agent.history = [{"role": "user", "content": "test"}]
        agent.clear_history()
        assert agent.history == []
    
    def test_get_history(self, agent):
        """Test getting conversation history."""
        agent.history = [{"role": "user", "content": "test"}]
        history = agent.get_history()
        assert history == [{"role": "user", "content": "test"}]
        # Verify it's a copy
        history.append({"role": "assistant", "content": "test2"})
        assert len(agent.history) == 1


@pytest.mark.asyncio
async def test_create_adk_agent(mock_client):
    """Test convenience function for creating agent."""
    with patch('{{cookiecutter.package_name}}.agents.adk.agent.genai.Client'):
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
            agent = await create_adk_agent(
                model="gemini-pro",
                temperature=0.5,
                system_instruction="Test"
            )
            
            assert isinstance(agent, GoogleADKAgent)
            assert agent.config.model == "gemini-pro"
            assert agent.config.temperature == 0.5
            assert agent.config.system_instruction == "Test"
{%- endif %}
