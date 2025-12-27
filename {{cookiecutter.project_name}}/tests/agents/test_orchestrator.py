"""Tests for agent orchestrator."""
import asyncio
import pytest

from {{cookiecutter.package_name}}.agents.orchestrator import (
    AgentOrchestrator,
    Task,
    TaskResult,
    ExecutionMode,
    run_parallel,
    run_pipeline,
)


# Test agent functions
async def async_agent(data: str) -> str:
    """Async test agent."""
    await asyncio.sleep(0.01)
    return f"processed: {data}"


def sync_agent(data: str) -> str:
    """Sync test agent."""
    return f"processed: {data}"


async def failing_agent(data: str) -> str:
    """Agent that always fails."""
    raise ValueError("Test error")


async def slow_agent(data: str) -> str:
    """Slow agent for timeout tests."""
    await asyncio.sleep(10)
    return "done"


class TestAgentOrchestrator:
    """Tests for AgentOrchestrator class."""
    
    def test_init(self):
        """Test orchestrator initialization."""
        orchestrator = AgentOrchestrator(max_concurrent=5)
        assert orchestrator.max_concurrent == 5
        assert orchestrator._results == {}
    
    @pytest.mark.asyncio
    async def test_execute_parallel_async(self):
        """Test parallel execution with async agents."""
        orchestrator = AgentOrchestrator()
        
        tasks = [
            Task("task1", "data1", async_agent),
            Task("task2", "data2", async_agent),
            Task("task3", "data3", async_agent),
        ]
        
        results = await orchestrator.execute_parallel(tasks)
        
        assert len(results) == 3
        assert all(r.success for r in results)
        assert results[0].output == "processed: data1"
        assert results[1].output == "processed: data2"
        assert results[2].output == "processed: data3"
    
    @pytest.mark.asyncio
    async def test_execute_parallel_sync(self):
        """Test parallel execution with sync agents."""
        orchestrator = AgentOrchestrator()
        
        tasks = [
            Task("task1", "data1", sync_agent),
            Task("task2", "data2", sync_agent),
        ]
        
        results = await orchestrator.execute_parallel(tasks)
        
        assert len(results) == 2
        assert all(r.success for r in results)
        assert results[0].output == "processed: data1"
    
    @pytest.mark.asyncio
    async def test_execute_parallel_with_failure(self):
        """Test parallel execution handles failures gracefully."""
        orchestrator = AgentOrchestrator()
        
        tasks = [
            Task("task1", "data1", async_agent),
            Task("task2", "data2", failing_agent),
            Task("task3", "data3", async_agent),
        ]
        
        results = await orchestrator.execute_parallel(tasks)
        
        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False
        assert "Test error" in results[1].error
        assert results[2].success is True
    
    @pytest.mark.asyncio
    async def test_execute_parallel_timeout(self):
        """Test parallel execution with timeout."""
        orchestrator = AgentOrchestrator()
        
        tasks = [
            Task("slow", "data", slow_agent),
        ]
        
        results = await orchestrator.execute_parallel(tasks, timeout=0.1)
        
        assert len(results) == 1
        assert results[0].success is False
        assert "Timeout" in results[0].error
    
    @pytest.mark.asyncio
    async def test_execute_pipeline(self):
        """Test sequential pipeline execution."""
        orchestrator = AgentOrchestrator()
        
        async def step1(data: str) -> str:
            return f"step1({data})"
        
        async def step2(data: str) -> str:
            return f"step2({data})"
        
        async def step3(data: str) -> str:
            return f"step3({data})"
        
        tasks = [
            Task("step1", None, step1),
            Task("step2", None, step2),
            Task("step3", None, step3),
        ]
        
        result = await orchestrator.execute_pipeline(tasks, initial_input="start")
        
        assert result.success is True
        assert result.output == "step3(step2(step1(start)))"
        assert result.metadata["steps"] == ["step1", "step2", "step3"]
    
    @pytest.mark.asyncio
    async def test_execute_pipeline_with_failure(self):
        """Test pipeline stops on failure."""
        orchestrator = AgentOrchestrator()
        
        tasks = [
            Task("step1", None, async_agent),
            Task("step2", None, failing_agent),
            Task("step3", None, async_agent),  # Should not execute
        ]
        
        result = await orchestrator.execute_pipeline(tasks, initial_input="start")
        
        assert result.success is False
        assert "Test error" in result.error
        assert result.task_name == "step2"
    
    @pytest.mark.asyncio
    async def test_execute_map_reduce(self):
        """Test map-reduce pattern."""
        orchestrator = AgentOrchestrator()
        
        async def map_fn(item: int) -> int:
            return item * 2
        
        def reduce_fn(results: list) -> int:
            return sum(results)
        
        result = await orchestrator.execute_map_reduce(
            data_items=[1, 2, 3, 4, 5],
            map_fn=map_fn,
            reduce_fn=reduce_fn,
        )
        
        assert result.success is True
        assert result.output == 30  # (1+2+3+4+5)*2 = 30
    
    @pytest.mark.asyncio
    async def test_execute_map_reduce_with_map_failure(self):
        """Test map-reduce handles map phase failures."""
        orchestrator = AgentOrchestrator()
        
        async def map_fn(item: int) -> int:
            if item == 3:
                raise ValueError("Map failed")
            return item * 2
        
        def reduce_fn(results: list) -> int:
            return sum(results)
        
        result = await orchestrator.execute_map_reduce(
            data_items=[1, 2, 3, 4, 5],
            map_fn=map_fn,
            reduce_fn=reduce_fn,
        )
        
        assert result.success is False
        assert "Map phase failed" in result.error
    
    @pytest.mark.asyncio
    async def test_get_result(self):
        """Test retrieving stored results."""
        orchestrator = AgentOrchestrator()
        
        tasks = [Task("task1", "data1", async_agent)]
        await orchestrator.execute_parallel(tasks)
        
        result = orchestrator.get_result("task1")
        assert result is not None
        assert result.task_name == "task1"
        assert result.output == "processed: data1"
    
    def test_clear_results(self):
        """Test clearing stored results."""
        orchestrator = AgentOrchestrator()
        orchestrator._results["test"] = TaskResult("test", "output", True)
        
        orchestrator.clear_results()
        
        assert len(orchestrator._results) == 0


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    @pytest.mark.asyncio
    async def test_run_parallel(self):
        """Test run_parallel convenience function."""
        results = await run_parallel(
            async_agent,
            async_agent,
            async_agent,
            inputs=["a", "b", "c"]
        )
        
        assert len(results) == 3
        assert all(r.success for r in results)
        assert results[0].output == "processed: a"
        assert results[1].output == "processed: b"
        assert results[2].output == "processed: c"
    
    @pytest.mark.asyncio
    async def test_run_parallel_no_inputs(self):
        """Test run_parallel with no inputs."""
        async def no_input_agent(data):
            return "done"
        
        results = await run_parallel(
            no_input_agent,
            no_input_agent,
        )
        
        assert len(results) == 2
        assert all(r.success for r in results)
    
    @pytest.mark.asyncio
    async def test_run_pipeline(self):
        """Test run_pipeline convenience function."""
        async def step1(data: str) -> str:
            return f"1({data})"
        
        async def step2(data: str) -> str:
            return f"2({data})"
        
        result = await run_pipeline(
            step1,
            step2,
            initial_input="start"
        )
        
        assert result.success is True
        assert result.output == "2(1(start))"


class TestTaskResult:
    """Tests for TaskResult dataclass."""
    
    def test_task_result_success(self):
        """Test successful task result."""
        result = TaskResult(
            task_name="test",
            output="result",
            success=True,
        )
        
        assert result.task_name == "test"
        assert result.output == "result"
        assert result.success is True
        assert result.error is None
    
    def test_task_result_failure(self):
        """Test failed task result."""
        result = TaskResult(
            task_name="test",
            output=None,
            success=False,
            error="Something went wrong",
        )
        
        assert result.task_name == "test"
        assert result.output is None
        assert result.success is False
        assert result.error == "Something went wrong"


class TestTask:
    """Tests for Task dataclass."""
    
    def test_task_creation(self):
        """Test task creation."""
        task = Task(
            name="test_task",
            input_data={"key": "value"},
            agent_fn=async_agent,
            metadata={"priority": "high"}
        )
        
        assert task.name == "test_task"
        assert task.input_data == {"key": "value"}
        assert task.agent_fn == async_agent
        assert task.metadata == {"priority": "high"}
    
    def test_task_default_metadata(self):
        """Test task with default metadata."""
        task = Task(
            name="test",
            input_data="data",
            agent_fn=async_agent,
        )
        
        assert task.metadata == {}
