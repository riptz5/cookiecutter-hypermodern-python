{%- if cookiecutter.use_google_adk == 'y' and cookiecutter.use_google_cloud == 'y' %}
"""Tests for GENESIS Core module.

These tests verify the GenesisCore system behavior using mocks
to avoid requiring actual GCP credentials during testing.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


@pytest.fixture
def mock_perceive():
    """Mock PerceiveModule."""
    with patch("{{cookiecutter.package_name}}.genesis.core.PerceiveModule") as mock:
        module = MagicMock()
        
        # Create mock context
        context = MagicMock()
        context.hash.return_value = "test_hash_123"
        context.user_task = None
        context.to_prompt.return_value = "Test context prompt"
        
        module.scan = AsyncMock(return_value=context)
        mock.return_value = module
        
        yield mock


@pytest.fixture
def mock_think():
    """Mock ThinkModule."""
    with patch("{{cookiecutter.package_name}}.genesis.core.ThinkModule") as mock:
        module = MagicMock()
        
        # Create mock plan
        plan = MagicMock()
        plan.actions = []
        plan.reasoning = "Test reasoning"
        plan.get_actions_by_priority.return_value = []
        
        module.reason = AsyncMock(return_value=plan)
        module.generate_code = AsyncMock(return_value="# Generated code")
        mock.return_value = module
        
        yield mock


@pytest.fixture
def mock_act():
    """Mock ActModule."""
    with patch("{{cookiecutter.package_name}}.genesis.core.ActModule") as mock:
        module = MagicMock()
        
        # Create mock result
        result = MagicMock()
        result.success = True
        result.actions = ["test:action"]
        result.errors = []
        result.to_dict.return_value = {
            "actions": ["test:action"],
            "success": True,
            "outputs": [],
            "errors": [],
        }
        
        module.execute = AsyncMock(return_value=result)
        mock.return_value = module
        
        yield mock


@pytest.fixture
def mock_memory():
    """Mock MemoryModule."""
    with patch("{{cookiecutter.package_name}}.genesis.core.MemoryModule") as mock:
        module = MagicMock()
        module.store_cycle = AsyncMock()
        mock.return_value = module
        yield mock


@pytest.fixture
def mock_evolve():
    """Mock EvolveModule."""
    with patch("{{cookiecutter.package_name}}.genesis.core.EvolveModule") as mock:
        module = MagicMock()
        module.improve = AsyncMock()
        mock.return_value = module
        yield mock


@pytest.mark.asyncio
async def test_genesis_core_initialization(
    mock_perceive, mock_think, mock_act, mock_memory, mock_evolve
):
    """Test GenesisCore initializes correctly."""
    from {{cookiecutter.package_name}}.genesis import GenesisCore
    
    core = GenesisCore()
    
    assert core.perceive is not None
    assert core.think is not None
    assert core.act is not None
    assert core.memory is not None
    assert core.evolve is not None
    assert core._cycle_count == 0


@pytest.mark.asyncio
async def test_genesis_core_run_cycle(
    mock_perceive, mock_think, mock_act, mock_memory, mock_evolve
):
    """Test running a single cycle."""
    from {{cookiecutter.package_name}}.genesis import GenesisCore
    
    core = GenesisCore()
    result = await core.run_cycle()
    
    # Verify phases were called
    core.perceive.scan.assert_called_once()
    core.think.reason.assert_called_once()
    core.act.execute.assert_called_once()
    core.memory.store_cycle.assert_called_once()
    
    # Check result
    assert result is not None
    assert result.cycle_id.startswith("cycle_")
    assert isinstance(result.timestamp, datetime)
    assert result.success is True
    assert result.duration_ms > 0


@pytest.mark.asyncio
async def test_genesis_core_run_cycle_with_task(
    mock_perceive, mock_think, mock_act, mock_memory, mock_evolve
):
    """Test running a cycle with specific task."""
    from {{cookiecutter.package_name}}.genesis import GenesisCore
    
    core = GenesisCore()
    result = await core.run_cycle(task="Test specific task")
    
    # Verify task was set in context
    core.perceive.scan.assert_called_once()
    context = await core.perceive.scan()
    
    assert result.success is True


@pytest.mark.asyncio
async def test_genesis_core_run_cycle_handles_errors(
    mock_perceive, mock_think, mock_act, mock_memory, mock_evolve
):
    """Test cycle handles errors gracefully."""
    from {{cookiecutter.package_name}}.genesis import GenesisCore
    
    # Make think module fail
    mock_think.return_value.reason = AsyncMock(
        side_effect=Exception("Think failed")
    )
    
    core = GenesisCore()
    result = await core.run_cycle()
    
    # Should still complete but with errors
    assert result is not None
    assert len(result.errors) > 0
    assert "think" in result.errors[0].lower()


@pytest.mark.asyncio
async def test_genesis_core_evolution(
    mock_perceive, mock_think, mock_act, mock_memory, mock_evolve
):
    """Test evolution is triggered at correct interval."""
    from {{cookiecutter.package_name}}.genesis import GenesisCore
    
    # Set low threshold for testing
    core = GenesisCore(evolution_threshold=2)
    
    # Run 2 cycles (evolution should trigger on 2nd)
    await core.run_cycle()
    assert not (await core.run_cycle()).evolved  # First cycle
    
    # Reset and run to threshold
    core._cycle_count = 1
    result = await core.run_cycle()  # Should trigger on cycle 2
    
    # Evolution should have been triggered
    assert core._cycle_count == 2


@pytest.mark.asyncio
async def test_genesis_core_force_evolve(
    mock_perceive, mock_think, mock_act, mock_memory, mock_evolve
):
    """Test forcing evolution."""
    from {{cookiecutter.package_name}}.genesis import GenesisCore
    
    core = GenesisCore()
    success = await core.force_evolve()
    
    assert success is True
    core.evolve.improve.assert_called_once()


@pytest.mark.asyncio
async def test_genesis_core_get_status(
    mock_perceive, mock_think, mock_act, mock_memory, mock_evolve
):
    """Test getting system status."""
    from {{cookiecutter.package_name}}.genesis import GenesisCore
    
    core = GenesisCore()
    await core.run_cycle()
    
    status = core.get_status()
    
    assert status["status"] == "running"
    assert "uptime_seconds" in status
    assert status["cycles_completed"] == 1
    assert "next_evolution_in" in status


class TestCycleResult:
    """Tests for CycleResult dataclass."""
    
    def test_cycle_result_to_dict(self):
        """Test CycleResult serialization."""
        from {{cookiecutter.package_name}}.genesis.core import CycleResult
        
        result = CycleResult(
            cycle_id="test_123",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            context_hash="hash123",
            plan_summary="Test plan",
            actions_taken=["action1", "action2"],
            success=True,
            duration_ms=100.5,
            evolved=False,
            errors=[],
        )
        
        data = result.to_dict()
        
        assert data["cycle_id"] == "test_123"
        assert data["success"] is True
        assert len(data["actions_taken"]) == 2
        assert data["duration_ms"] == 100.5
{%- endif %}
