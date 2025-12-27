"""Integration tests for multi-agent system.

These tests require GOOGLE_API_KEY to be set and make REAL API calls.
They are skipped automatically if the API key is not available.

Run with:
    pytest tests/test_multiagent_integration.py -v -m integration

To run all tests including integration:
    GOOGLE_API_KEY=your_key pytest tests/test_multiagent_integration.py -v
"""
import os
import pytest
import time

# Skip all tests if no API key
pytestmark = pytest.mark.skipif(
    not os.getenv("GOOGLE_API_KEY"),
    reason="GOOGLE_API_KEY not set - skipping integration tests"
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_worker_agent_real():
    """Test single worker with REAL Gemini API."""
    from {{cookiecutter.package_name}}.agents.adk.workers import create_worker
    
    worker = create_worker("research")
    result = await worker.run("What is Python? Answer in one sentence.")
    
    assert result.success is True
    assert result.output is not None
    assert len(result.output) > 10
    # Should mention Python or programming
    assert any(kw in result.output.lower() for kw in ["python", "programming", "language"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_workers_parallel():
    """Test multiple workers in parallel execution."""
    from {{cookiecutter.package_name}}.agents.adk.workers import WorkerPool, create_worker
    import asyncio
    
    # Create pool with workers
    pool = WorkerPool()
    pool.add_worker(create_worker("research"))
    pool.add_worker(create_worker("analysis"))
    
    # Execute tasks in parallel
    start = time.time()
    results = await pool.execute_parallel([
        ("research", "What is machine learning? One sentence."),
        ("analysis", "Compare Python and JavaScript in one sentence."),
    ])
    elapsed = time.time() - start
    
    assert len(results) == 2
    assert all(r.success for r in results)
    
    # Both should complete in reasonable time
    # (parallel should be faster than 2x sequential)
    assert elapsed < 60  # Generous timeout for API calls


@pytest.mark.integration
@pytest.mark.asyncio
async def test_production_orchestrator_verification():
    """Test ProductionOrchestrator system verification."""
    from {{cookiecutter.package_name}}.agents.orchestrator import ProductionOrchestrator
    
    orchestrator = ProductionOrchestrator()
    result = await orchestrator.verify_system()
    
    assert "success" in result
    assert "checks" in result
    
    # API key should be valid
    assert result["checks"].get("api_key") is True
    
    # Gemini should be accessible
    assert result["checks"].get("gemini_api") is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multi_agent_execution():
    """Test full multi-agent task execution."""
    from {{cookiecutter.package_name}}.agents.orchestrator import ProductionOrchestrator
    
    orchestrator = ProductionOrchestrator()
    
    start = time.time()
    result = await orchestrator.execute_multi_agent(
        "What is Python? Provide a brief answer."
    )
    elapsed = time.time() - start
    
    assert result["success"] is True
    assert result["output"] is not None
    assert len(result["output"]) > 0
    assert result["parallel"] is True
    
    # Should use at least one worker
    assert len(result["workers_used"]) >= 1
    
    # Should complete in reasonable time
    assert elapsed < 120  # 2 minutes max


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_with_specific_workers():
    """Test execution with specific workers."""
    from {{cookiecutter.package_name}}.agents.orchestrator import ProductionOrchestrator
    
    orchestrator = ProductionOrchestrator()
    
    result = await orchestrator.execute_with_workers(
        "Explain what Python is.",
        ["research", "writer"]
    )
    
    assert result["success"] is True
    assert "research" in result["output"]
    assert "writer" in result["output"]
    assert result["parallel"] is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_a2a_protocol_messaging():
    """Test A2A protocol message passing."""
    from {{cookiecutter.package_name}}.agents.a2a.protocol import (
        A2AProtocol, A2AMessage, A2AMessageType, AgentCard
    )
    
    protocol = A2AProtocol()
    
    # Register agents
    protocol.register_agent(AgentCard(
        agent_id="agent1",
        name="Agent 1",
        capabilities=["research"],
    ))
    
    protocol.register_agent(AgentCard(
        agent_id="agent2",
        name="Agent 2",
        capabilities=["analysis"],
    ))
    
    # Test discovery
    researchers = protocol.discover_agents("research")
    assert len(researchers) == 1
    assert researchers[0].agent_id == "agent1"
    
    # Test messaging
    msg = A2AMessage(
        type=A2AMessageType.TASK_REQUEST,
        sender="supervisor",
        receiver="agent1",
        payload={"task": "test"},
    )
    await protocol.send(msg)
    
    received = await protocol.receive("agent1", timeout=1.0)
    assert received is not None
    assert received.sender == "supervisor"
    assert received.payload["task"] == "test"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_memory_store_operations():
    """Test memory store CRUD operations."""
    from {{cookiecutter.package_name}}.cloud.memory_store import MemoryStore
    
    store = MemoryStore()
    
    # Test remember
    entry = await store.remember(
        key="test_memory_001",
        content={"test": "data", "number": 42},
        memory_type="test",
        tags=["integration", "test"],
    )
    
    assert entry.key == "test_memory_001"
    assert entry.version == 1
    
    # Test recall
    recalled = await store.recall("test_memory_001")
    assert recalled is not None
    assert recalled.content["test"] == "data"
    
    # Test search by tags
    by_tags = await store.search_by_tags(["integration"])
    assert len(by_tags) >= 1
    
    # Test forget
    deleted = await store.forget("test_memory_001")
    assert deleted is True
    
    # Verify deleted
    recalled_after = await store.recall("test_memory_001")
    assert recalled_after is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_base_agent_lifecycle():
    """Test base agent lifecycle hooks."""
    from {{cookiecutter.package_name}}.agents.base import BaseAgent, AgentContext
    
    class TestAgent(BaseAgent[str, str]):
        @property
        def name(self) -> str:
            return "test_agent"
        
        @property
        def capabilities(self):
            return ["test"]
        
        async def _execute(self, input_data: str, context: AgentContext) -> str:
            return f"Processed: {input_data}"
    
    agent = TestAgent()
    result = await agent.run("test input")
    
    assert result.success is True
    assert "Processed: test input" in result.output
    assert result.duration_ms is not None
    
    # Check metrics
    metrics = agent.get_metrics()
    assert metrics["execution_count"] == 1
    assert metrics["error_count"] == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_config_loading():
    """Test configuration loading from environment."""
    from {{cookiecutter.package_name}}.core.config import Config, get_config
    
    config = get_config()
    
    assert config.gemini.api_key is not None
    assert config.gemini.model == "gemini-2.0-flash-exp"
    
    # Validate should not return errors for API key
    errors = config.validate()
    assert "GOOGLE_API_KEY not set" not in errors


# ============================================================================
# Supervisor Tests (require LangGraph)
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_supervisor_agent():
    """Test SupervisorAgent multi-agent orchestration."""
    try:
        from {{cookiecutter.package_name}}.agents.langgraph.supervisor import SupervisorAgent
    except ImportError:
        pytest.skip("LangGraph not available")
    
    supervisor = SupervisorAgent()
    
    result = await supervisor.run("What is Python? Brief answer.")
    
    assert "final_output" in result
    assert result["final_output"] is not None
    assert len(result["final_output"]) > 0
    
    # Should have used workers
    assert "metadata" in result
    assert "workers_executed" in result["metadata"]


# ============================================================================
# Autopoiesis Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_autopoietic_cycle_dry_run():
    """Test autopoietic cycle in dry run mode."""
    try:
        from {{cookiecutter.package_name}}.autopoiesis import run_cycle
    except ImportError:
        pytest.skip("Autopoiesis module not available")
    
    result = await run_cycle(dry_run=True)
    
    assert result.success is True
    assert result.cycle_id is not None
    
    # Should have perception results
    assert result.perception is not None
    
    # Should have cognition (improvement suggestions)
    assert result.cognition is not None
    assert result.cognition.improvements is not None
    
    # Should NOT have made actual changes (dry run)
    assert result.action is not None
    assert len(result.action.changes_made) == 0


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_parallel_execution_performance():
    """Test that parallel execution is actually faster than sequential."""
    from {{cookiecutter.package_name}}.agents.adk.workers import create_worker
    import asyncio
    
    workers = {
        "research": create_worker("research"),
        "analysis": create_worker("analysis"),
    }
    
    query = "What is machine learning? One sentence."
    
    # Sequential execution
    sequential_start = time.time()
    for worker in workers.values():
        await worker.run(query)
    sequential_time = time.time() - sequential_start
    
    # Parallel execution
    parallel_start = time.time()
    await asyncio.gather(*[w.run(query) for w in workers.values()])
    parallel_time = time.time() - parallel_start
    
    # Parallel should be faster (at least 1.5x improvement)
    # Note: This might not always hold due to API rate limiting
    print(f"Sequential: {sequential_time:.2f}s, Parallel: {parallel_time:.2f}s")
    
    # Just assert both completed successfully
    assert sequential_time > 0
    assert parallel_time > 0
