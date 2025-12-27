#!/bin/bash
set -e

echo "🚀 Creating GitHub issues for Hypermodern Python Cookiecutter development plan..."
echo ""

# Check if gh is authenticated
if ! gh auth status > /dev/null 2>&1; then
    echo "❌ GitHub CLI is not authenticated. Please run: gh auth login"
    exit 1
fi

# Milestone 1: Google ADK Integration
echo "📦 Creating Milestone 1 (M1) issues..."

gh issue create \
    --title "Add Google ADK cookiecutter option" \
    --label "enhancement,milestone:m1" \
    --body "## Goal
Enable Google Agent Development Kit (ADK) as an agent framework option in generated projects.

## Tasks
- [ ] Add \`use_google_adk\` boolean variable to \`cookiecutter.json\`
- [ ] Add conditional logic in template for ADK dependencies
- [ ] Update template validation workflow to test ADK combinations
- [ ] Document ADK option in template README

## Acceptance Criteria
- Users can choose \`use_google_adk=y\` during project generation
- ADK dependencies are only included when option is enabled
- All validation tests pass with ADK enabled/disabled

## Milestone
M1: Google ADK Integration"

gh issue create \
    --title "Implement Google ADK agent scaffolding" \
    --label "enhancement,milestone:m1" \
    --body "## Goal
Create the base scaffolding for Google ADK agents in generated projects.

## Tasks
- [ ] Create \`agents/adk/agent.py\` with base ADK agent class
- [ ] Create \`agents/adk/tools.py\` for ADK tool definitions
- [ ] Create \`agents/adk/config.py\` for ADK configuration
- [ ] Add conditional rendering in templates based on \`use_google_adk\`
- [ ] Add example ADK agent implementation

## Acceptance Criteria
- Generated projects with ADK have working agent scaffolding
- ADK agents can be instantiated and run
- Code follows Hypermodern Python standards (typing, docstrings, tests)

## Milestone
M1: Google ADK Integration"

gh issue create \
    --title "Add tests for Google ADK integration" \
    --label "testing,milestone:m1" \
    --body "## Goal
Ensure 100% test coverage for Google ADK integration code.

## Tasks
- [ ] Create \`tests/agents/adk/test_agent.py\`
- [ ] Create \`tests/agents/adk/test_tools.py\`
- [ ] Create \`tests/agents/adk/test_config.py\`
- [ ] Ensure 100% test coverage for ADK code
- [ ] Add integration tests for ADK agent execution

## Acceptance Criteria
- All ADK code has 100% test coverage
- Tests pass in CI/CD pipeline
- Tests are only included when \`use_google_adk=y\`

## Milestone
M1: Google ADK Integration"

gh issue create \
    --title "Document Google ADK usage" \
    --label "documentation,milestone:m1" \
    --body "## Goal
Provide comprehensive documentation for using Google ADK in generated projects.

## Tasks
- [ ] Add ADK section to generated project's \`AGENTS.md\`
- [ ] Create ADK quickstart guide in generated project
- [ ] Add ADK examples to documentation
- [ ] Update template documentation to mention ADK option

## Acceptance Criteria
- Clear documentation for using ADK in generated projects
- Examples demonstrate common ADK patterns
- Documentation is conditionally rendered based on option

## Milestone
M1: Google ADK Integration"

# Milestone 2: MCP Integration
echo "📦 Creating Milestone 2 (M2) issues..."

gh issue create \
    --title "Add MCP cookiecutter option" \
    --label "enhancement,milestone:m2" \
    --body "## Goal
Add Model Context Protocol (MCP) server/client capabilities to generated projects.

## Tasks
- [ ] Add \`use_mcp\` boolean variable to \`cookiecutter.json\`
- [ ] Add conditional logic for MCP dependencies
- [ ] Update validation workflow for MCP combinations
- [ ] Document MCP option in template README

## Acceptance Criteria
- Users can choose \`use_mcp=y\` during project generation
- MCP dependencies are only included when option is enabled
- Validation tests cover MCP scenarios

## Milestone
M2: MCP Integration"

gh issue create \
    --title "Implement MCP server scaffolding" \
    --label "enhancement,milestone:m2" \
    --body "## Goal
Create MCP server infrastructure for exposing tools to AI agents.

## Tasks
- [ ] Create \`mcp/server.py\` with base MCP server
- [ ] Create \`mcp/tools.py\` for MCP tool definitions
- [ ] Create \`mcp/config.py\` for MCP server configuration
- [ ] Add example MCP server implementation
- [ ] Add MCP server startup script

## Acceptance Criteria
- Generated projects can run an MCP server
- MCP server can register and expose tools
- Server follows MCP specification

## Milestone
M2: MCP Integration"

gh issue create \
    --title "Implement MCP client scaffolding" \
    --label "enhancement,milestone:m2" \
    --body "## Goal
Create MCP client infrastructure for connecting to MCP servers.

## Tasks
- [ ] Create \`mcp/client.py\` with base MCP client
- [ ] Add methods for connecting to MCP servers
- [ ] Add methods for calling MCP tools
- [ ] Add example MCP client usage

## Acceptance Criteria
- Generated projects can connect to MCP servers
- Clients can discover and call MCP tools
- Error handling for connection failures

## Milestone
M2: MCP Integration"

gh issue create \
    --title "Add tests for MCP integration" \
    --label "testing,milestone:m2" \
    --body "## Goal
Ensure 100% test coverage for MCP server and client code.

## Tasks
- [ ] Create \`tests/mcp/test_server.py\`
- [ ] Create \`tests/mcp/test_client.py\`
- [ ] Create \`tests/mcp/test_tools.py\`
- [ ] Ensure 100% test coverage for MCP code
- [ ] Add integration tests for server-client communication

## Acceptance Criteria
- All MCP code has 100% test coverage
- Tests pass in CI/CD pipeline
- Tests include server-client integration scenarios

## Milestone
M2: MCP Integration"

gh issue create \
    --title "Document MCP usage" \
    --label "documentation,milestone:m2" \
    --body "## Goal
Provide comprehensive documentation for MCP server and client usage.

## Tasks
- [ ] Add MCP section to generated project's \`AGENTS.md\`
- [ ] Create MCP server/client quickstart guides
- [ ] Add MCP examples to documentation
- [ ] Document common MCP patterns and best practices

## Acceptance Criteria
- Clear documentation for MCP server and client usage
- Examples demonstrate MCP tool creation and usage
- Documentation explains MCP architecture

## Milestone
M2: MCP Integration"

# Milestone 3: Agent Bridge & Adapters
echo "📦 Creating Milestone 3 (M3) issues..."

gh issue create \
    --title "Implement agent bridge pattern" \
    --label "enhancement,milestone:m3" \
    --body "## Goal
Create a unified interface for working with multiple agent frameworks.

## Tasks
- [ ] Design unified agent interface in \`agents/base.py\`
- [ ] Implement bridge in \`agents/bridge.py\` for framework abstraction
- [ ] Add factory pattern for creating agents
- [ ] Support switching between LangGraph, ADK, and custom agents
- [ ] Add configuration-based agent selection

## Acceptance Criteria
- Single interface works with all agent frameworks
- Agents can be swapped without changing client code
- Bridge pattern is well-documented with examples

## Milestone
M3: Agent Bridge & Adapters"

gh issue create \
    --title "Create adapter infrastructure" \
    --label "enhancement,milestone:m3" \
    --body "## Goal
Build extensible adapter system for external service integrations.

## Tasks
- [ ] Design adapter base class in \`adapters/__init__.py\`
- [ ] Create example adapters (e.g., database, API, file system)
- [ ] Add adapter registry and discovery
- [ ] Implement adapter lifecycle management
- [ ] Add adapter configuration system

## Acceptance Criteria
- Adapters follow consistent interface
- Easy to add new adapters
- Adapters are testable and mockable

## Milestone
M3: Agent Bridge & Adapters"

gh issue create \
    --title "Add tests for bridge and adapters" \
    --label "testing,milestone:m3" \
    --body "## Goal
Ensure 100% test coverage for bridge and adapter code.

## Tasks
- [ ] Create \`tests/agents/test_base.py\`
- [ ] Create \`tests/agents/test_bridge.py\`
- [ ] Create \`tests/adapters/test_adapters.py\`
- [ ] Ensure 100% test coverage
- [ ] Add integration tests for adapter usage

## Acceptance Criteria
- All bridge and adapter code has 100% coverage
- Tests demonstrate proper usage patterns
- Tests include error scenarios

## Milestone
M3: Agent Bridge & Adapters"

gh issue create \
    --title "Document bridge and adapter patterns" \
    --label "documentation,milestone:m3" \
    --body "## Goal
Document architecture and usage of bridge and adapter patterns.

## Tasks
- [ ] Add architecture documentation to \`AGENTS.md\`
- [ ] Create adapter development guide
- [ ] Add examples for common adapter patterns
- [ ] Document bridge pattern benefits and usage

## Acceptance Criteria
- Clear explanation of architecture
- Examples show how to create custom adapters
- Documentation explains when to use each pattern

## Milestone
M3: Agent Bridge & Adapters"

# Milestone 4: Advanced Features & Polish
echo "📦 Creating Milestone 4 (M4) issues..."

gh issue create \
    --title "Add agent observability" \
    --label "enhancement,milestone:m4" \
    --body "## Goal
Add logging, metrics, and tracing for agent operations.

## Tasks
- [ ] Integrate logging for agent operations
- [ ] Add metrics collection (execution time, success rate)
- [ ] Create dashboard/visualization for agent metrics
- [ ] Add tracing for agent execution flow
- [ ] Implement error tracking and reporting

## Acceptance Criteria
- All agent operations are logged
- Metrics are collected and accessible
- Tracing helps debug agent behavior

## Milestone
M4: Advanced Features & Polish"

gh issue create \
    --title "Add agent testing utilities" \
    --label "testing,milestone:m4" \
    --body "## Goal
Create utilities to simplify testing of agent code.

## Tasks
- [ ] Create test fixtures for agents
- [ ] Add mocking utilities for agent dependencies
- [ ] Create assertion helpers for agent behavior
- [ ] Add test data generators
- [ ] Create integration test helpers

## Acceptance Criteria
- Testing agents is straightforward
- Utilities reduce boilerplate in tests
- Examples demonstrate testing best practices

## Milestone
M4: Advanced Features & Polish"

gh issue create \
    --title "Improve agent configuration" \
    --label "enhancement,milestone:m4" \
    --body "## Goal
Enhance agent configuration system with validation and flexibility.

## Tasks
- [ ] Add environment-based configuration
- [ ] Support configuration validation
- [ ] Add configuration schema documentation
- [ ] Create configuration examples for common scenarios
- [ ] Add configuration hot-reloading

## Acceptance Criteria
- Configuration is flexible and type-safe
- Invalid configurations are caught early
- Configuration changes don't require restarts (where applicable)

## Milestone
M4: Advanced Features & Polish"

gh issue create \
    --title "Add agent CLI commands" \
    --label "enhancement,milestone:m4" \
    --body "## Goal
Create CLI commands for convenient agent operations.

## Tasks
- [ ] Create \`agent run\` command for executing agents
- [ ] Create \`agent test\` command for testing agents
- [ ] Create \`agent list\` command for listing available agents
- [ ] Create \`agent info\` command for agent details
- [ ] Add CLI documentation and help text

## Acceptance Criteria
- CLI provides convenient agent operations
- Commands have good UX and error messages
- CLI is documented in generated project

## Milestone
M4: Advanced Features & Polish"

gh issue create \
    --title "Create comprehensive examples" \
    --label "documentation,milestone:m4" \
    --body "## Goal
Provide comprehensive examples for all agent features.

## Tasks
- [ ] Add simple agent example (Hello World)
- [ ] Add LangGraph agent example
- [ ] Add Google ADK agent example
- [ ] Add MCP server/client example
- [ ] Add multi-agent collaboration example
- [ ] Add adapter usage examples

## Acceptance Criteria
- Examples cover common use cases
- Examples are well-documented
- Examples follow best practices

## Milestone
M4: Advanced Features & Polish"

gh issue create \
    --title "Performance optimization" \
    --label "enhancement,milestone:m4" \
    --body "## Goal
Optimize agent performance and document characteristics.

## Tasks
- [ ] Profile agent execution
- [ ] Optimize hot paths
- [ ] Add caching where appropriate
- [ ] Reduce dependency loading time
- [ ] Benchmark and document performance

## Acceptance Criteria
- Agent operations are performant
- No obvious performance bottlenecks
- Performance characteristics are documented

## Milestone
M4: Advanced Features & Polish"

gh issue create \
    --title "Security hardening" \
    --label "security,milestone:m4" \
    --body "## Goal
Ensure agent code follows security best practices.

## Tasks
- [ ] Add input validation for agent inputs
- [ ] Implement rate limiting for agent operations
- [ ] Add authentication/authorization for MCP servers
- [ ] Audit dependencies for security issues
- [ ] Add security best practices documentation

## Acceptance Criteria
- Common security issues are prevented
- Security guidance is provided
- Dependencies are kept up to date

## Milestone
M4: Advanced Features & Polish"

gh issue create \
    --title "Final documentation pass" \
    --label "documentation,milestone:m4" \
    --body "## Goal
Complete and polish all project documentation.

## Tasks
- [ ] Review and update all AGENTS.md files
- [ ] Create video tutorials (optional)
- [ ] Add troubleshooting guide
- [ ] Create migration guide from vanilla template
- [ ] Add FAQ section
- [ ] Ensure all code has docstrings

## Acceptance Criteria
- Documentation is comprehensive and accurate
- New users can get started quickly
- Common issues have documented solutions

## Milestone
M4: Advanced Features & Polish"

echo ""
echo "✅ All issues created successfully!"
echo ""
echo "📊 Summary:"
echo "  - M1 (Google ADK Integration): 4 issues"
echo "  - M2 (MCP Integration): 5 issues"
echo "  - M3 (Agent Bridge & Adapters): 4 issues"
echo "  - M4 (Advanced Features & Polish): 8 issues"
echo "  - Total: 21 issues"
echo ""
echo "🔗 View issues at: https://github.com/riptz5/cookiecutter-hypermodern-python/issues"
