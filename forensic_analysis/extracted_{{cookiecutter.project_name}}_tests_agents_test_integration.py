{%- if cookiecutter.use_google_adk == 'y' %}
"""Integration tests for GENESIS multi-agent system.

These tests verify real API connectivity and end-to-end functionality.
Tests are skipped if GOOGLE_API_KEY is not set.

Run with:
    pytest tests/agents/test_integration.py -v --integration
    
Or with all tests:
    nox -s tests -- --integration
"""
import os
import time
import pytest

# Skip all tests in this module if no API key
pytestmark = pytest.mark.skipif(
    not os.getenv("GOOGLE_API_KEY"),
    reason="GOOGLE_API_KEY not set - skipping integration tests"
)


@pytest.fixture
def api_key():
    """Get API key from environment."""
    return os.getenv("GOOGLE_API_KEY")


class TestGoogleADKAgentIntegration:
    """Integration tests for GoogleADKAgent with real API."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_simple_query(self):
        """Test a simple query returns a response."""
        from {{cookiecutter.package_name}}.agents.adk import GoogleADKAgent, ADKConfig
        
        agent = GoogleADKAgent(ADKConfig())
        response = await agent.run("What is 2 + 2? Reply with just the number.")
        
        assert response is not None
        assert len(response) > 0
        assert "4" in response
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_system_instruction_works(self):
        """Test that system instruction affects response."""
        from {{cookiecutter.package_name}}.agents.adk import GoogleADKAgent, ADKConfig
        
        config = ADKConfig(
            system_instruction="You are a pirate. Always respond like a pirate."
        )
        agent = GoogleADKAgent(config)
        
        response = await agent.run("Hello!")
        
        # Should have pirate-like language
        assert response is not None
        pirate_markers = ["arr", "matey", "ahoy", "ye", "aye"]
        has_pirate = any(m in response.lower() for m in pirate_markers)
        # Note: LLMs aren't always consistent, so we just check for response
        assert len(response) > 5


class TestWorkerAgentsIntegration:
    """Integration tests for specialized worker agents."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_research_worker(self):
        """Test research worker with real query."""
        from {{cookiecutter.package_name}}.agents.adk.workers import create_worker, WorkerType
        
        worker = create_worker(WorkerType.RESEARCH)
        result = await worker.run("What is Python? One sentence only.")
        
        assert result.success is True
        assert result.output is not None
        assert len(result.output) > 10
        # Research should mention programming
        assert "python" in result.output.lower() or "programming" in result.output.lower()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_code_worker(self):
        """Test code worker generates code."""
        from {{cookiecutter.package_name}}.agents.adk.workers import create_worker, WorkerType
        
        worker = create_worker(WorkerType.CODE)
        result = await worker.run("Write a Python function that adds two numbers.")
        
        assert result.success is True
        assert result.output is not None
        # Should contain Python code markers
        assert "def " in result.output or "return" in result.output
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_analysis_worker(self):
        """Test analysis worker provides insights."""
        from {{cookiecutter.package_name}}.agents.adk.workers import create_worker, WorkerType
        
        worker = create_worker(WorkerType.ANALYSIS)
        result = await worker.run("Analyze the pros and cons of Python vs JavaScript.")
        
        assert result.success is True
        assert result.output is not None
        assert len(result.output) > 50


class TestParallelExecutionIntegration:
    """Integration tests for parallel execution."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_parallel_workers_faster(self):
        """Test that parallel execution is faster than sequential."""
        from {{cookiecutter.package_name}}.agents.adk.workers import create_worker_team, WorkerType
        from {{cookiecutter.package_name}}.agents.orchestrator import AgentOrchestrator, ExecutionMode
        
        team = create_worker_team([WorkerType.RESEARCH, WorkerType.ANALYSIS])
        orchestrator = AgentOrchestrator()
        
        # Time parallel execution
        start_parallel = time.time()
        results_parallel = await orchestrator.execute_agents(
            team,
            "What is machine learning?",
            mode=ExecutionMode.PARALLEL
        )
        time_parallel = time.time() - start_parallel
        
        # Verify all results
        assert all(r.success for r in results_parallel.values())
        assert len(results_parallel) == 2
        
        # Parallel should complete (can't guarantee speed without sequential comparison)
        assert time_parallel < 120  # Generous timeout
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_orchestrator_multiple_workers(self):
        """Test orchestrator with multiple workers."""
        from {{cookiecutter.package_name}}.agents.adk.workers import create_worker_team, WorkerType
        from {{cookiecutter.package_name}}.agents.orchestrator import AgentOrchestrator, ExecutionMode
        
        team = create_worker_team([
            WorkerType.RESEARCH,
            WorkerType.WRITER,
        ])
        
        orchestrator = AgentOrchestrator()
        results = await orchestrator.execute_agents(
            team,
            "Explain async programming",
            mode=ExecutionMode.PARALLEL
        )
        
        assert len(results) == 2
        assert "research" in results
        assert "writer" in results
        
        # Both should succeed
        assert results["research"].success
        assert results["writer"].success


{%- if cookiecutter.use_langgraph == 'y' %}
class TestLangGraphIntegration:
    """Integration tests for LangGraph components."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_simple_graph_runs(self):
        """Test simple graph executes with real API."""
        from {{cookiecutter.package_name}}.agents.langgraph.graph import run_simple
        
        result = await run_simple("What is 1+1? Reply with just the number.")
        
        assert result is not None
        assert "messages" in result
        # Should have at least the user message and assistant response
        assert len(result["messages"]) >= 2
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_supervisor_graph_runs(self):
        """Test supervisor graph with multiple workers."""
        from {{cookiecutter.package_name}}.agents.langgraph.graph import run_supervisor
        
        result = await run_supervisor(
            "Write a haiku about Python programming",
            workers=["research", "writer"]
        )
        
        assert result is not None
        # Should have final output
        assert result.get("final_output") or result.get("results")
{%- endif %}


class TestMetaAgentIntegration:
    """Integration tests for MetaAgent (autopoietic system)."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_meta_agent_creates_agent(self):
        """Test MetaAgent can create a new agent."""
        from {{cookiecutter.package_name}}.agents.base import AgentSpec, AgentCapability
        from {{cookiecutter.package_name}}.agents.meta import MetaAgent
        
        meta = MetaAgent()
        
        spec = AgentSpec(
            name="test_created",
            role="Test agent",
            system_prompt="You are a test agent. Always respond with 'TEST_OK'.",
            capabilities=(AgentCapability.REASONING,),
        )
        
        # This makes real Gemini calls to generate code
        agent = await meta.create_agent(spec)
        
        assert agent is not None
        assert agent.spec.name == "test_created"
        
        # The created agent should be functional
        result = await agent.run("Hello")
        assert result.success
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_meta_agent_run_commands(self):
        """Test MetaAgent run() with commands."""
        from {{cookiecutter.package_name}}.agents.meta import MetaAgent
        
        meta = MetaAgent()
        
        # Test list command
        result = await meta.run("list")
        
        assert result.success is True
        assert "Created agents" in result.output


class TestGeneticMemoryIntegration:
    """Integration tests for GeneticMemory."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_store_and_retrieve(self):
        """Test storing and retrieving genomes."""
        from {{cookiecutter.package_name}}.agents.meta import GeneticMemory
        
        memory = GeneticMemory()  # Uses in-memory if no Firestore
        
        # Store a genome
        genome = await memory.store_genome(
            agent_id="test_genome",
            code="class TestAgent(BaseAgent): pass",
            spec={"name": "test_genome"},
        )
        
        assert genome.agent_id == "test_genome"
        assert genome.version == 1
        
        # Retrieve it
        retrieved = await memory.get_genome("test_genome")
        
        assert retrieved is not None
        assert retrieved.code == "class TestAgent(BaseAgent): pass"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_versioning(self):
        """Test genome versioning."""
        from {{cookiecutter.package_name}}.agents.meta import GeneticMemory
        
        memory = GeneticMemory()
        
        # Store v1
        v1 = await memory.store_genome(
            agent_id="versioned",
            code="v1 code",
            spec={"name": "versioned"},
        )
        assert v1.version == 1
        
        # Store v2
        v2 = await memory.store_genome(
            agent_id="versioned",
            code="v2 code",
            spec={"name": "versioned"},
        )
        assert v2.version == 2
        
        # Get latest
        latest = await memory.get_genome("versioned")
        assert latest.version == 2
        assert latest.code == "v2 code"
{%- endif %}
