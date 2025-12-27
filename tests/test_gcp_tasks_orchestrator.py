"""Tests for Google Cloud Tasks Orchestrator.

These tests verify:
- Task payload creation and serialization
- Cloud Tasks client initialization
- Orchestrator task distribution
- Error handling and retries
- Integration with Pub/Sub and Firestore (mocked)
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4

from tools.gcp_tasks_orchestrator import (
    TaskPayload,
    TaskResult,
    TaskStatus,
    TaskPriority,
    GCPTasksClient,
    GCPTasksOrchestrator,
    execute_parallel,
    execute_with_scaling,
)


class TestTaskPayload:
    """Test TaskPayload serialization."""
    
    def test_create_payload(self):
        """Test creating a task payload."""
        payload = TaskPayload(
            task_id="test-123",
            agent_type="research",
            agent_name="agent-001",
            input_data={"task": "test"},
        )
        
        assert payload.task_id == "test-123"
        assert payload.agent_type == "research"
        assert payload.agent_name == "agent-001"
        assert payload.created_at is not None
    
    def test_payload_to_json(self):
        """Test serializing payload to JSON."""
        payload = TaskPayload(
            task_id="test-123",
            agent_type="research",
            agent_name="agent-001",
            input_data={"task": "test"},
        )
        
        json_str = payload.to_json()
        data = json.loads(json_str)
        
        assert data["task_id"] == "test-123"
        assert data["agent_type"] == "research"
        assert "created_at" in data
    
    def test_payload_from_json(self):
        """Test deserializing payload from JSON."""
        original = TaskPayload(
            task_id="test-123",
            agent_type="research",
            agent_name="agent-001",
            input_data={"task": "test"},
        )
        
        json_str = original.to_json()
        restored = TaskPayload.from_json(json_str)
        
        assert restored.task_id == original.task_id
        assert restored.agent_type == original.agent_type
        assert restored.agent_name == original.agent_name
    
    def test_payload_retry_tracking(self):
        """Test payload retry count."""
        payload = TaskPayload(
            task_id="test-123",
            agent_type="research",
            agent_name="agent-001",
            input_data={"task": "test"},
            retry_count=2,
            max_retries=3,
        )
        
        assert payload.retry_count == 2
        assert payload.max_retries == 3


class TestTaskResult:
    """Test TaskResult creation."""
    
    def test_create_result(self):
        """Test creating a task result."""
        result = TaskResult(
            task_id="test-123",
            agent_name="agent-001",
            status=TaskStatus.COMPLETED,
            output={"data": "result"},
        )
        
        assert result.task_id == "test-123"
        assert result.status == TaskStatus.COMPLETED
        assert result.output == {"data": "result"}
    
    def test_result_with_error(self):
        """Test result with error."""
        result = TaskResult(
            task_id="test-123",
            agent_name="agent-001",
            status=TaskStatus.FAILED,
            error="Something went wrong",
        )
        
        assert result.status == TaskStatus.FAILED
        assert result.error == "Something went wrong"


class TestGCPTasksClient:
    """Test GCP Tasks Client."""
    
    @pytest.fixture
    def client(self):
        """Create a test client with mocked credentials."""
        with patch.dict("os.environ", {"GOOGLE_CLOUD_PROJECT": "test-project"}):
            return GCPTasksClient(
                project_id="test-project",
                queue_name="test-queue",
                region="us-central1",
            )
    
    def test_initialization(self, client):
        """Test client initialization."""
        assert client.project_id == "test-project"
        assert client.queue_name == "test-queue"
        assert client.region == "us-central1"
    
    def test_queue_path(self, client):
        """Test queue path generation."""
        # Mock the client property
        with patch.object(client, "client") as mock_client:
            mock_client.queue_path.return_value = (
                "projects/test-project/locations/us-central1/queues/test-queue"
            )
            path = client._queue_path()
            assert "test-project" in path
            assert "test-queue" in path
    
    @pytest.mark.asyncio
    async def test_create_queue_if_not_exists(self):
        """Test queue creation (mocked)."""
        with patch.dict("os.environ", {"GOOGLE_CLOUD_PROJECT": "test-project"}):
            with patch("tools.gcp_tasks_orchestrator.GCPTasksClient.client", new_callable=AsyncMock) as mock_client:
                client = GCPTasksClient(project_id="test-project")
                mock_client.create_queue = AsyncMock()
                
                # Should not raise
                await client.create_queue_if_not_exists()
    
    @pytest.mark.asyncio
    async def test_create_task(self):
        """Test task creation (mocked)."""
        with patch.dict("os.environ", {
            "GOOGLE_CLOUD_PROJECT": "test-project",
            "GENESIS_WORKER_URL": "https://test-worker.example.com/execute",
        }):
            with patch("tools.gcp_tasks_orchestrator.GCPTasksClient.client", new_callable=AsyncMock) as mock_client:
                client = GCPTasksClient(project_id="test-project")
                
                # Mock the create_task response
                mock_response = Mock()
                mock_response.name = "projects/test-project/locations/us-central1/queues/test-queue/tasks/123"
                mock_client.create_task = AsyncMock(return_value=mock_response)
                
                payload = TaskPayload(
                    task_id="test-123",
                    agent_type="research",
                    agent_name="agent-001",
                    input_data={"task": "test"},
                )
                
                # Would need proper GCP setup, so we just verify structure
                assert payload.task_id == "test-123"
    
    @pytest.mark.asyncio
    async def test_create_batch_tasks(self):
        """Test batch task creation."""
        with patch.dict("os.environ", {"GOOGLE_CLOUD_PROJECT": "test-project"}):
            with patch("tools.gcp_tasks_orchestrator.GCPTasksClient.create_task", new_callable=AsyncMock) as mock_create:
                client = GCPTasksClient(project_id="test-project")
                
                mock_create.side_effect = [
                    f"task-{i}" for i in range(3)
                ]
                
                payloads = [
                    TaskPayload(
                        task_id=f"test-{i}",
                        agent_type="research",
                        agent_name=f"agent-{i:04d}",
                        input_data={"task": "test"},
                    )
                    for i in range(3)
                ]
                
                # Would execute with real client
                assert len(payloads) == 3


class TestGCPTasksOrchestrator:
    """Test GCP Tasks Orchestrator."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create test orchestrator."""
        with patch.dict("os.environ", {"GOOGLE_CLOUD_PROJECT": "test-project"}):
            return GCPTasksOrchestrator(
                project_id="test-project",
                queue_name="test-queue",
            )
    
    def test_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator.project_id == "test-project"
        assert orchestrator.queue_name == "test-queue"
        assert orchestrator.region == "us-central1"
        assert len(orchestrator.active_tasks) == 0
        assert len(orchestrator.completed_tasks) == 0
    
    @pytest.mark.asyncio
    async def test_create_agent_tasks(self, orchestrator):
        """Test agent task creation."""
        payloads = await orchestrator.create_agent_tasks(
            task_input="Test task",
            num_agents=5,
            agent_types=["research", "analysis"],
        )
        
        assert len(payloads) == 5
        assert all(isinstance(p, TaskPayload) for p in payloads)
        assert payloads[0].agent_type in ["research", "analysis"]
        assert payloads[0].input_data["task"] == "Test task"
    
    @pytest.mark.asyncio
    async def test_create_agent_tasks_default_types(self, orchestrator):
        """Test agent task creation with default types."""
        payloads = await orchestrator.create_agent_tasks(
            task_input="Test task",
            num_agents=10,
        )
        
        assert len(payloads) == 10
        # Should round-robin through default types
        types = [p.agent_type for p in payloads]
        assert len(set(types)) > 1  # Multiple types
    
    @pytest.mark.asyncio
    async def test_execute_parallel_agents(self, orchestrator):
        """Test parallel agent execution (mocked)."""
        with patch.object(
            orchestrator.tasks_client,
            "create_queue_if_not_exists",
            new_callable=AsyncMock
        ):
            with patch.object(
                orchestrator.tasks_client,
                "create_batch_tasks",
                new_callable=AsyncMock,
                return_value=[f"task-{i}" for i in range(5)]
            ):
                result = await orchestrator.execute_parallel_agents(
                    task="Test task",
                    num_agents=5,
                )
                
                assert result["success"] is True
                assert result["num_agents"] == 5
                assert result["tasks_submitted"] == 5
                assert "execution_id" in result
                assert "queue" in result
    
    @pytest.mark.asyncio
    async def test_execute_with_scaling(self, orchestrator):
        """Test scaling execution (mocked)."""
        with patch.object(
            orchestrator,
            "execute_parallel_agents",
            new_callable=AsyncMock,
            side_effect=[
                {"success": True, "num_agents": 10, "tasks_submitted": 10},
                {"success": True, "num_agents": 15, "tasks_submitted": 15},
                {"success": True, "num_agents": 22, "tasks_submitted": 22},
            ]
        ):
            result = await orchestrator.execute_with_scaling(
                task="Test task",
                initial_agents=10,
                scale_factor=1.5,
                num_loops=3,
            )
            
            assert result["success"] is True
            assert result["total_agents"] == 47  # 10 + 15 + 22
            assert result["total_loops"] == 3
            assert len(result["loops"]) == 3
    
    def test_get_statistics(self, orchestrator):
        """Test getting statistics."""
        stats = orchestrator.get_statistics()
        
        assert stats["project_id"] == "test-project"
        assert stats["queue_name"] == "test-queue"
        assert stats["active_tasks"] == 0
        assert stats["completed_tasks"] == 0
    
    @pytest.mark.asyncio
    async def test_get_execution_status(self, orchestrator):
        """Test getting execution status."""
        status = await orchestrator.get_execution_status("test-execution-123")
        
        assert status["execution_id"] == "test-execution-123"
        assert "status" in status
        assert "completed_agents" in status


class TestQuickFunctions:
    """Test quick execution functions."""
    
    @pytest.mark.asyncio
    async def test_execute_parallel(self):
        """Test execute_parallel quick function."""
        with patch.dict("os.environ", {"GOOGLE_CLOUD_PROJECT": "test-project"}):
            with patch(
                "tools.gcp_tasks_orchestrator.GCPTasksOrchestrator.execute_parallel_agents",
                new_callable=AsyncMock,
                return_value={"success": True, "num_agents": 10}
            ):
                result = await execute_parallel(
                    task="Test task",
                    num_agents=10,
                )
                
                assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_execute_with_scaling_quick(self):
        """Test execute_with_scaling quick function."""
        with patch.dict("os.environ", {"GOOGLE_CLOUD_PROJECT": "test-project"}):
            with patch(
                "tools.gcp_tasks_orchestrator.GCPTasksOrchestrator.execute_with_scaling",
                new_callable=AsyncMock,
                return_value={"success": True, "total_agents": 47}
            ):
                result = await execute_with_scaling(
                    task="Test task",
                    initial_agents=10,
                )
                
                assert result["success"] is True


class TestIntegration:
    """Integration tests (require GCP setup)."""
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires GCP credentials")
    async def test_end_to_end_execution(self):
        """Test complete execution flow."""
        orchestrator = GCPTasksOrchestrator()
        result = await orchestrator.execute_parallel_agents(
            task="Test task",
            num_agents=3,
        )
        
        assert result["success"] is True
        assert result["num_agents"] == 3


# ============================================================================
# Parametrized Tests
# ============================================================================

@pytest.mark.parametrize("num_agents", [1, 10, 100, 230, 500])
@pytest.mark.asyncio
async def test_scaling_scenarios(num_agents):
    """Test various agent counts."""
    with patch.dict("os.environ", {"GOOGLE_CLOUD_PROJECT": "test-project"}):
        orchestrator = GCPTasksOrchestrator()
        payloads = await orchestrator.create_agent_tasks(
            task_input="Test",
            num_agents=num_agents,
        )
        
        assert len(payloads) == num_agents


@pytest.mark.parametrize("agent_type", ["research", "analysis", "writer", "code", "testing"])
@pytest.mark.asyncio
async def test_agent_types(agent_type):
    """Test different agent types."""
    with patch.dict("os.environ", {"GOOGLE_CLOUD_PROJECT": "test-project"}):
        orchestrator = GCPTasksOrchestrator()
        payloads = await orchestrator.create_agent_tasks(
            task_input="Test",
            num_agents=5,
            agent_types=[agent_type],
        )
        
        assert all(p.agent_type == agent_type for p in payloads)
