{%- if cookiecutter.use_google_adk == 'y' and cookiecutter.use_google_cloud == 'y' %}
"""Tests for GENESIS Think module."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import json


class TestAction:
    """Tests for Action dataclass."""
    
    def test_action_to_dict(self):
        """Test Action serialization."""
        from {{cookiecutter.package_name}}.genesis.think import Action
        
        action = Action(
            type="generate_agent",
            target="bigquery",
            spec={"description": "BQ agent"},
            priority=5,
            reasoning="Need BQ support",
        )
        
        data = action.to_dict()
        
        assert data["type"] == "generate_agent"
        assert data["target"] == "bigquery"
        assert data["priority"] == 5
    
    def test_action_from_dict(self):
        """Test Action deserialization."""
        from {{cookiecutter.package_name}}.genesis.think import Action
        
        data = {
            "type": "query",
            "target": "storage",
            "spec": {"query_type": "list"},
            "priority": 3,
            "reasoning": "List buckets",
        }
        
        action = Action.from_dict(data)
        
        assert action.type == "query"
        assert action.target == "storage"
        assert action.priority == 3


class TestActionPlan:
    """Tests for ActionPlan dataclass."""
    
    def test_action_plan_from_json(self):
        """Test ActionPlan creation from JSON."""
        from {{cookiecutter.package_name}}.genesis.think import ActionPlan
        
        data = {
            "reasoning": "Test reasoning",
            "confidence": 0.8,
            "actions": [
                {"type": "query", "target": "test", "priority": 1},
                {"type": "deploy", "target": "app", "priority": 5},
            ],
        }
        
        plan = ActionPlan.from_json(data)
        
        assert plan.reasoning == "Test reasoning"
        assert plan.confidence == 0.8
        assert len(plan.actions) == 2
    
    def test_action_plan_get_actions_by_priority(self):
        """Test actions are sorted by priority."""
        from {{cookiecutter.package_name}}.genesis.think import ActionPlan, Action
        
        plan = ActionPlan(
            reasoning="Test",
            actions=[
                Action(type="a", target="1", priority=1),
                Action(type="b", target="2", priority=10),
                Action(type="c", target="3", priority=5),
            ],
        )
        
        sorted_actions = plan.get_actions_by_priority()
        
        assert sorted_actions[0].priority == 10
        assert sorted_actions[1].priority == 5
        assert sorted_actions[2].priority == 1
    
    def test_action_plan_empty(self):
        """Test empty plan creation."""
        from {{cookiecutter.package_name}}.genesis.think import ActionPlan
        
        plan = ActionPlan.empty()
        
        assert len(plan.actions) == 0
        assert plan.confidence == 0.0


class TestThinkModule:
    """Tests for ThinkModule."""
    
    def test_extract_json_from_raw(self):
        """Test JSON extraction from raw response."""
        from {{cookiecutter.package_name}}.genesis.think import ThinkModule
        
        module = ThinkModule()
        
        raw_json = '{"reasoning": "test", "actions": []}'
        result = module._extract_json(raw_json)
        
        assert result is not None
        data = json.loads(result)
        assert data["reasoning"] == "test"
    
    def test_extract_json_from_markdown(self):
        """Test JSON extraction from markdown code block."""
        from {{cookiecutter.package_name}}.genesis.think import ThinkModule
        
        module = ThinkModule()
        
        markdown_json = '''Here is the plan:
```json
{"reasoning": "test", "actions": []}
```
'''
        result = module._extract_json(markdown_json)
        
        assert result is not None
        data = json.loads(result)
        assert data["reasoning"] == "test"
    
    def test_clean_code_removes_markdown(self):
        """Test code cleaning removes markdown."""
        from {{cookiecutter.package_name}}.genesis.think import ThinkModule
        
        module = ThinkModule()
        
        code_with_markdown = '''```python
def hello():
    print("Hello")
```'''
        
        clean = module._clean_code(code_with_markdown)
        
        assert "```" not in clean
        assert "def hello():" in clean
    
    def test_validate_syntax_accepts_valid_code(self):
        """Test syntax validation accepts valid Python."""
        from {{cookiecutter.package_name}}.genesis.think import ThinkModule
        
        module = ThinkModule()
        
        valid_code = '''
def hello(name: str) -> str:
    """Say hello."""
    return f"Hello, {name}"
'''
        # Should not raise
        module._validate_syntax(valid_code)
    
    def test_validate_syntax_rejects_invalid_code(self):
        """Test syntax validation rejects invalid Python."""
        from {{cookiecutter.package_name}}.genesis.think import ThinkModule
        
        module = ThinkModule()
        
        invalid_code = '''
def broken(
    print("missing closing paren"
'''
        
        with pytest.raises(SyntaxError):
            module._validate_syntax(invalid_code)
{%- endif %}
