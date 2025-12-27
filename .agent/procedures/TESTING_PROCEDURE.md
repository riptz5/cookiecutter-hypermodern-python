# Testing Procedure - Standard Operating Procedure

> **Purpose**: Establish a consistent, fast, and reliable testing workflow for all code changes.
> **Audience**: AI agents and developers working on this cookiecutter template.

## 🎯 Core Principle

**Primary Directive**: If it's not tested, you should test it through the proposed procedure or create one by using best practices. If it breaks coverage, it needs to be fixed until it works and the code runs smoothly.

## 📋 Standard Testing Workflow

### 1. Before Writing Code

```bash
# Understand what you're building
- Read AGENTS.md
- Identify the module/feature
- Check if similar tests exist
```

### 2. Write Code + Tests Together

**NEVER write code without tests. ALWAYS write them together.**

```python
# Example structure:
{{cookiecutter.project_name}}/
├── src/{{cookiecutter.package_name}}/
│   └── agents/
│       └── new_feature.py          # ← Implementation
└── tests/
    └── agents/
        └── test_new_feature.py     # ← Tests (SAME TIME)
```

### 3. Test Structure Template

Use this template for ALL new test files:

```python
"""{%- if cookiecutter.use_feature == 'y' %}
Tests for [Feature Name].
{%- endif %}"""
import pytest
from unittest.mock import Mock, patch, AsyncMock

from {{cookiecutter.package_name}}.module import (
    ClassToTest,
    function_to_test,
)


class TestClassName:
    """Tests for ClassName."""
    
    @pytest.fixture
    def mock_dependency(self):
        """Mock external dependencies."""
        with patch('module.Dependency') as mock:
            yield mock
    
    @pytest.fixture
    def instance(self, mock_dependency):
        """Create instance for testing."""
        return ClassToTest(config)
    
    def test_initialization(self, instance):
        """Test object initializes correctly."""
        assert instance.property == expected_value
    
    def test_basic_functionality(self, instance):
        """Test core functionality."""
        result = instance.method()
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_async_method(self, instance):
        """Test async methods."""
        result = await instance.async_method()
        assert result == expected
    
    def test_error_handling(self, instance):
        """Test error cases."""
        with pytest.raises(ExpectedError):
            instance.method_that_fails()


def test_standalone_function():
    """Test module-level functions."""
    result = function_to_test(input)
    assert result == expected
```

### 4. Validation Checklist

Run these commands IN ORDER after writing code:

```bash
# Step 1: Generate test project
cookiecutter . --no-input use_feature=y license=MIT

# Step 2: Verify TOML is valid
python3 -c "import tomllib; tomllib.load(open('hypermodern-python/pyproject.toml', 'rb'))"

# Step 3: Verify Python syntax
find hypermodern-python/src -name "*.py" -exec python3 -m py_compile {} \;

# Step 4: Check for unrendered Jinja
grep -r "{{cookiecutter" hypermodern-python/ && echo "ERROR" || echo "OK"

# Step 5: Clean up
rm -rf hypermodern-python
```

### 5. Coverage Requirements

**100% coverage is MANDATORY.**

Test coverage must include:
- ✅ All public methods
- ✅ All private methods (if complex)
- ✅ Error handling paths
- ✅ Edge cases
- ✅ Async/sync variants
- ✅ Configuration options

### 6. Mock External Dependencies

**ALWAYS mock external APIs/services:**

```python
# ✅ GOOD: Mock external calls
@patch('module.external_api_call')
def test_with_mock(mock_api):
    mock_api.return_value = "mocked"
    result = function_that_calls_api()
    assert result == expected

# ❌ BAD: Real API calls
def test_without_mock():
    result = function_that_calls_api()  # ← Will fail without API key
    assert result == expected
```

### 7. Commit Only When Tests Pass

```bash
# ✅ CORRECT workflow:
1. Write code + tests
2. Validate template (steps 1-4 above)
3. git add -A
4. git commit -m "feat: Add feature with tests"
5. git push origin main

# ❌ WRONG workflow:
1. Write code
2. git commit (no tests)
3. "I'll add tests later"  ← NEVER DO THIS
```

## 🚀 Quick Reference

### For New Features

```bash
# 1. Create implementation
touch {{cookiecutter.project_name}}/src/.../feature.py

# 2. Create tests (IMMEDIATELY)
touch {{cookiecutter.project_name}}/tests/.../test_feature.py

# 3. Write both together

# 4. Validate
cookiecutter . --no-input && \
python3 -c "import tomllib; tomllib.load(open('hypermodern-python/pyproject.toml', 'rb'))" && \
find hypermodern-python/src -name "*.py" -exec python3 -m py_compile {} \; && \
! grep -r "{{cookiecutter" hypermodern-python/ && \
rm -rf hypermodern-python && \
echo "✅ ALL CHECKS PASSED"

# 5. Commit
git add -A && git commit -m "feat: Add feature with 100% test coverage" && git push
```

### For Bug Fixes

```bash
# 1. Write failing test first
# 2. Fix the bug
# 3. Verify test passes
# 4. Validate template
# 5. Commit
```

## ⚠️ Common Mistakes to Avoid

| Mistake | Why It's Bad | Solution |
|---------|-------------|----------|
| Writing code without tests | Breaks coverage, wastes time | Write tests FIRST or TOGETHER |
| Skipping validation | Broken templates in production | ALWAYS run validation checklist |
| Committing without validation | CI fails, wastes time | Validate BEFORE commit |
| Using real API calls in tests | Tests fail without credentials | ALWAYS mock external calls |
| "I'll add tests later" | Tests never get added | Tests are NOT optional |

## 🎯 Success Criteria

Before ANY commit, verify:

- ✅ Code implemented
- ✅ Tests written (100% coverage)
- ✅ Template generates successfully
- ✅ TOML is valid
- ✅ Python syntax is valid
- ✅ No Jinja artifacts
- ✅ All checks pass

**If ANY check fails, FIX IT before committing.**

## 📚 Examples

### Example 1: New Agent Class

```python
# File: src/agents/new_agent.py
class NewAgent:
    def __init__(self, config):
        self.config = config
    
    async def run(self, prompt):
        return await self._process(prompt)

# File: tests/agents/test_new_agent.py
class TestNewAgent:
    @pytest.fixture
    def agent(self):
        return NewAgent(config={"key": "value"})
    
    @pytest.mark.asyncio
    async def test_run(self, agent):
        result = await agent.run("test")
        assert result is not None
```

### Example 2: Utility Function

```python
# File: src/utils/helpers.py
def format_response(data):
    if not data:
        raise ValueError("Data required")
    return {"formatted": data}

# File: tests/utils/test_helpers.py
def test_format_response_success():
    result = format_response("test")
    assert result == {"formatted": "test"}

def test_format_response_error():
    with pytest.raises(ValueError, match="Data required"):
        format_response(None)
```

## 🔄 Continuous Improvement

This procedure should be updated when:
- New testing patterns emerge
- Common issues are identified
- Better practices are discovered

**Location**: `.agent/procedures/TESTING_PROCEDURE.md`
**Owner**: All agents and developers
**Review**: After every major feature

---

**Remember**: Tests are not optional. They are part of the implementation.
