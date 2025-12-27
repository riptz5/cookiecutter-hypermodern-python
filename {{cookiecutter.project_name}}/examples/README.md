# Examples

This directory contains examples demonstrating the capabilities of {{cookiecutter.friendly_name}}.

## Agent Orchestration

### orchestration_example.py

Comprehensive examples of agent orchestration patterns:

1. **Parallel Execution**: Run multiple agents simultaneously
2. **Pipeline Execution**: Chain agents sequentially
3. **Map-Reduce Pattern**: Process data in parallel, aggregate results
4. **Quick Helpers**: Convenience functions for common patterns
5. **Real-World Scenario**: Complex multi-agent workflow

**Run it:**
```bash
cd {{cookiecutter.project_name}}
python -m examples.orchestration_example
```

**Expected output:**
- Demonstrates all orchestration patterns
- Shows timing comparisons (parallel vs sequential)
- Displays success/failure handling
- ~10 seconds total runtime

## Quick Start

```python
import asyncio
from {{cookiecutter.package_name}}.agents.orchestrator import run_parallel, run_pipeline

# Define your agents
async def agent1(data):
    return f"Agent 1 processed: {data}"

async def agent2(data):
    return f"Agent 2 processed: {data}"

# Run in parallel
results = await run_parallel(agent1, agent2, inputs=["task A", "task B"])

# Run in pipeline
result = await run_pipeline(agent1, agent2, initial_input="start")
```

## More Examples

More examples coming soon:
- LangGraph integration
- MCP server/client
- Custom agent implementations
