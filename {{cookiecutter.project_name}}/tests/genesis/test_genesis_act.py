{%- if cookiecutter.use_google_adk == 'y' and cookiecutter.use_google_cloud == 'y' %}
"""Tests for GENESIS Act module."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestActionResult:
    """Tests for ActionResult dataclass."""
    
    def test_action_result_to_dict(self):
        """Test ActionResult serialization."""
        from {{cookiecutter.package_name}}.genesis.act import ActionResult
        
        result = ActionResult(
            actions=["action1:target1", "action2:target2"],
            success=True,
            outputs=["output1", "output2"],
            errors=[],
        )
        
        data = result.to_dict()
        
        assert len(data["actions"]) == 2
        assert data["success"] is True
        assert "timestamp" in data
    
    def test_action_result_empty(self):
        """Test empty result creation."""
        from {{cookiecutter.package_name}}.genesis.act import ActionResult
        
        result = ActionResult.empty()
        
        assert result.success is False
        assert len(result.errors) > 0


class TestActModule:
    """Tests for ActModule."""
    
    def test_to_class_name_simple(self):
        """Test class name conversion - simple."""
        from {{cookiecutter.package_name}}.genesis.act import ActModule
        
        module = ActModule()
        
        assert module._to_class_name("bigquery") == "Bigquery"
        assert module._to_class_name("cloud-run") == "CloudRun"
    
    def test_to_class_name_with_prefix(self):
        """Test class name conversion with GCP prefixes."""
        from {{cookiecutter.package_name}}.genesis.act import ActModule
        
        module = ActModule()
        
        assert module._to_class_name("google-cloud-storage") == "Storage"
        assert module._to_class_name("gcp-compute") == "Compute"
    
    def test_to_class_name_with_dots(self):
        """Test class name conversion with dots."""
        from {{cookiecutter.package_name}}.genesis.act import ActModule
        
        module = ActModule()
        
        assert module._to_class_name("vertex.ai") == "VertexAi"
    
    @pytest.mark.asyncio
    async def test_execute_unknown_action_type(self):
        """Test executing unknown action type fails gracefully."""
        from {{cookiecutter.package_name}}.genesis.act import ActModule
        from {{cookiecutter.package_name}}.genesis.think import Action, ActionPlan
        
        module = ActModule()
        
        plan = ActionPlan(
            reasoning="Test",
            actions=[
                Action(type="unknown_type", target="test", priority=1),
            ],
        )
        
        result = await module.execute(plan)
        
        assert not result.success
        assert len(result.errors) > 0
        assert "unknown" in result.errors[0].lower()
    
    @pytest.mark.asyncio
    async def test_execute_empty_plan(self):
        """Test executing empty plan."""
        from {{cookiecutter.package_name}}.genesis.act import ActModule
        from {{cookiecutter.package_name}}.genesis.think import ActionPlan
        
        module = ActModule()
        plan = ActionPlan.empty()
        
        result = await module.execute(plan)
        
        # Empty plan succeeds but with no actions
        assert len(result.actions) == 0
    
    def test_get_generated_files_initially_empty(self):
        """Test generated files list is initially empty."""
        from {{cookiecutter.package_name}}.genesis.act import ActModule
        
        module = ActModule()
        
        assert module.get_generated_files() == []
{%- endif %}
