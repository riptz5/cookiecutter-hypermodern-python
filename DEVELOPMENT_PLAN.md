# Development Plan - Hypermodern Python Cookiecutter with AI Agent Support

This document outlines the complete development roadmap for adding AI agent infrastructure to the Cookiecutter Hypermodern Python template.

## 🎯 Vision

Transform the Hypermodern Python Cookiecutter into an **agent-first template** that enables AI agents to work seamlessly with generated projects while maintaining all existing best practices.

---

## ✅ Milestone 0 (M0): Foundation - COMPLETED

**Status**: ✅ Completed (commit: 9753c64)

### Completed Tasks

- [x] **#1**: Unificar AGENTS.md
  - Separate template vs generated project documentation
  - Add 'Two Levels' architecture section
  - Add 'Where Things Live' structure
  - Add 'Recommended Workflow for AI Agents'

- [x] **#2**: Directory structure for agents
  - Create `core/`, `adapters/`, `agents/`, `mcp/` directories
  - Create `agents/langgraph/`, `agents/adk/` subdirectories
  - Create `agents/base.py` and `agents/bridge.py` placeholders
  - Create mirrored test directories

- [x] **#3**: Machine-readable config
  - Create `.agent/config.yaml` for template
  - Create `{{cookiecutter.project_name}}/.agent/config.yaml` for generated projects

- [x] **#4**: Update Python to 3.10+
  - Update `pyproject.toml`: python ^3.10
  - Update test matrix: 3.10, 3.11, 3.12, 3.13
  - Update release workflow to Python 3.13

- [x] **#13**: Add LangGraph integration option
  - Add `use_langgraph` variable to `cookiecutter.json`
  - Conditional LangGraph dependencies in template
  - LangGraph agent scaffolding (state, nodes, graph)

- [x] **#15**: Add template validation workflow
  - Validate TOML syntax
  - Validate Python syntax
  - Check for unrendered Jinja artifacts
  - Test all license and langgraph combinations

- [x] **Fix**: Remove undefined `cookiecutter.documentation` variable
  - Fixed template generation error
  - All template combinations now generate successfully

---

## 🚧 Milestone 1 (M1): Google ADK Integration

**Status**: 🔨 In Progress (branch: feature/m2-google-adk exists)

### Goals
Enable Google Agent Development Kit (ADK) as an agent framework option in generated projects.

### Tasks

#### Issue #16: Add Google ADK cookiecutter option
- [ ] Add `use_google_adk` boolean variable to `cookiecutter.json`
- [ ] Add conditional logic in template for ADK dependencies
- [ ] Update template validation workflow to test ADK combinations
- [ ] Document ADK option in template README

**Acceptance Criteria**:
- Users can choose `use_google_adk=y` during project generation
- ADK dependencies are only included when option is enabled
- All validation tests pass with ADK enabled/disabled

---

#### Issue #17: Implement Google ADK agent scaffolding
- [ ] Create `agents/adk/agent.py` with base ADK agent class
- [ ] Create `agents/adk/tools.py` for ADK tool definitions
- [ ] Create `agents/adk/config.py` for ADK configuration
- [ ] Add conditional rendering in templates based on `use_google_adk`
- [ ] Add example ADK agent implementation

**Acceptance Criteria**:
- Generated projects with ADK have working agent scaffolding
- ADK agents can be instantiated and run
- Code follows Hypermodern Python standards (typing, docstrings, tests)

---

#### Issue #18: Add tests for Google ADK integration
- [ ] Create `tests/agents/adk/test_agent.py`
- [ ] Create `tests/agents/adk/test_tools.py`
- [ ] Create `tests/agents/adk/test_config.py`
- [ ] Ensure 100% test coverage for ADK code
- [ ] Add integration tests for ADK agent execution

**Acceptance Criteria**:
- All ADK code has 100% test coverage
- Tests pass in CI/CD pipeline
- Tests are only included when `use_google_adk=y`

---

#### Issue #19: Document Google ADK usage
- [ ] Add ADK section to generated project's `AGENTS.md`
- [ ] Create ADK quickstart guide in generated project
- [ ] Add ADK examples to documentation
- [ ] Update template documentation to mention ADK option

**Acceptance Criteria**:
- Clear documentation for using ADK in generated projects
- Examples demonstrate common ADK patterns
- Documentation is conditionally rendered based on option

---

## 🔮 Milestone 2 (M2): MCP (Model Context Protocol) Integration

**Status**: 📋 Planned

### Goals
Add MCP server/client capabilities to enable AI agents to interact with external tools and services.

### Tasks

#### Issue #20: Add MCP cookiecutter option
- [ ] Add `use_mcp` boolean variable to `cookiecutter.json`
- [ ] Add conditional logic for MCP dependencies
- [ ] Update validation workflow for MCP combinations
- [ ] Document MCP option in template README

**Acceptance Criteria**:
- Users can choose `use_mcp=y` during project generation
- MCP dependencies are only included when option is enabled
- Validation tests cover MCP scenarios

---

#### Issue #21: Implement MCP server scaffolding
- [ ] Create `mcp/server.py` with base MCP server
- [ ] Create `mcp/tools.py` for MCP tool definitions
- [ ] Create `mcp/config.py` for MCP server configuration
- [ ] Add example MCP server implementation
- [ ] Add MCP server startup script

**Acceptance Criteria**:
- Generated projects can run an MCP server
- MCP server can register and expose tools
- Server follows MCP specification

---

#### Issue #22: Implement MCP client scaffolding
- [ ] Create `mcp/client.py` with base MCP client
- [ ] Add methods for connecting to MCP servers
- [ ] Add methods for calling MCP tools
- [ ] Add example MCP client usage

**Acceptance Criteria**:
- Generated projects can connect to MCP servers
- Clients can discover and call MCP tools
- Error handling for connection failures

---

#### Issue #23: Add tests for MCP integration
- [ ] Create `tests/mcp/test_server.py`
- [ ] Create `tests/mcp/test_client.py`
- [ ] Create `tests/mcp/test_tools.py`
- [ ] Ensure 100% test coverage for MCP code
- [ ] Add integration tests for server-client communication

**Acceptance Criteria**:
- All MCP code has 100% test coverage
- Tests pass in CI/CD pipeline
- Tests include server-client integration scenarios

---

#### Issue #24: Document MCP usage
- [ ] Add MCP section to generated project's `AGENTS.md`
- [ ] Create MCP server/client quickstart guides
- [ ] Add MCP examples to documentation
- [ ] Document common MCP patterns and best practices

**Acceptance Criteria**:
- Clear documentation for MCP server and client usage
- Examples demonstrate MCP tool creation and usage
- Documentation explains MCP architecture

---

## 🎨 Milestone 3 (M3): Agent Bridge & Adapters

**Status**: 📋 Planned

### Goals
Create a unified interface for working with multiple agent frameworks and external service adapters.

### Tasks

#### Issue #25: Implement agent bridge pattern
- [ ] Design unified agent interface in `agents/base.py`
- [ ] Implement bridge in `agents/bridge.py` for framework abstraction
- [ ] Add factory pattern for creating agents
- [ ] Support switching between LangGraph, ADK, and custom agents
- [ ] Add configuration-based agent selection

**Acceptance Criteria**:
- Single interface works with all agent frameworks
- Agents can be swapped without changing client code
- Bridge pattern is well-documented with examples

---

#### Issue #26: Create adapter infrastructure
- [ ] Design adapter base class in `adapters/__init__.py`
- [ ] Create example adapters (e.g., database, API, file system)
- [ ] Add adapter registry and discovery
- [ ] Implement adapter lifecycle management
- [ ] Add adapter configuration system

**Acceptance Criteria**:
- Adapters follow consistent interface
- Easy to add new adapters
- Adapters are testable and mockable

---

#### Issue #27: Add tests for bridge and adapters
- [ ] Create `tests/agents/test_base.py`
- [ ] Create `tests/agents/test_bridge.py`
- [ ] Create `tests/adapters/test_adapters.py`
- [ ] Ensure 100% test coverage
- [ ] Add integration tests for adapter usage

**Acceptance Criteria**:
- All bridge and adapter code has 100% coverage
- Tests demonstrate proper usage patterns
- Tests include error scenarios

---

#### Issue #28: Document bridge and adapter patterns
- [ ] Add architecture documentation to `AGENTS.md`
- [ ] Create adapter development guide
- [ ] Add examples for common adapter patterns
- [ ] Document bridge pattern benefits and usage

**Acceptance Criteria**:
- Clear explanation of architecture
- Examples show how to create custom adapters
- Documentation explains when to use each pattern

---

## 🚀 Milestone 4 (M4): Advanced Features & Polish

**Status**: 📋 Planned

### Goals
Add advanced features, improve developer experience, and ensure production readiness.

### Tasks

#### Issue #29: Add agent observability
- [ ] Integrate logging for agent operations
- [ ] Add metrics collection (execution time, success rate)
- [ ] Create dashboard/visualization for agent metrics
- [ ] Add tracing for agent execution flow
- [ ] Implement error tracking and reporting

**Acceptance Criteria**:
- All agent operations are logged
- Metrics are collected and accessible
- Tracing helps debug agent behavior

---

#### Issue #30: Add agent testing utilities
- [ ] Create test fixtures for agents
- [ ] Add mocking utilities for agent dependencies
- [ ] Create assertion helpers for agent behavior
- [ ] Add test data generators
- [ ] Create integration test helpers

**Acceptance Criteria**:
- Testing agents is straightforward
- Utilities reduce boilerplate in tests
- Examples demonstrate testing best practices

---

#### Issue #31: Improve agent configuration
- [ ] Add environment-based configuration
- [ ] Support configuration validation
- [ ] Add configuration schema documentation
- [ ] Create configuration examples for common scenarios
- [ ] Add configuration hot-reloading

**Acceptance Criteria**:
- Configuration is flexible and type-safe
- Invalid configurations are caught early
- Configuration changes don't require restarts (where applicable)

---

#### Issue #32: Add agent CLI commands
- [ ] Create `agent run` command for executing agents
- [ ] Create `agent test` command for testing agents
- [ ] Create `agent list` command for listing available agents
- [ ] Create `agent info` command for agent details
- [ ] Add CLI documentation and help text

**Acceptance Criteria**:
- CLI provides convenient agent operations
- Commands have good UX and error messages
- CLI is documented in generated project

---

#### Issue #33: Create comprehensive examples
- [ ] Add simple agent example (Hello World)
- [ ] Add LangGraph agent example
- [ ] Add Google ADK agent example
- [ ] Add MCP server/client example
- [ ] Add multi-agent collaboration example
- [ ] Add adapter usage examples

**Acceptance Criteria**:
- Examples cover common use cases
- Examples are well-documented
- Examples follow best practices

---

#### Issue #34: Performance optimization
- [ ] Profile agent execution
- [ ] Optimize hot paths
- [ ] Add caching where appropriate
- [ ] Reduce dependency loading time
- [ ] Benchmark and document performance

**Acceptance Criteria**:
- Agent operations are performant
- No obvious performance bottlenecks
- Performance characteristics are documented

---

#### Issue #35: Security hardening
- [ ] Add input validation for agent inputs
- [ ] Implement rate limiting for agent operations
- [ ] Add authentication/authorization for MCP servers
- [ ] Audit dependencies for security issues
- [ ] Add security best practices documentation

**Acceptance Criteria**:
- Common security issues are prevented
- Security guidance is provided
- Dependencies are kept up to date

---

#### Issue #36: Final documentation pass
- [ ] Review and update all AGENTS.md files
- [ ] Create video tutorials (optional)
- [ ] Add troubleshooting guide
- [ ] Create migration guide from vanilla template
- [ ] Add FAQ section
- [ ] Ensure all code has docstrings

**Acceptance Criteria**:
- Documentation is comprehensive and accurate
- New users can get started quickly
- Common issues have documented solutions

---

## 📊 Success Metrics

### Template Quality
- ✅ 100% test coverage maintained
- ✅ All CI/CD checks pass
- ✅ No linter errors or warnings
- ✅ Documentation is complete and accurate

### User Experience
- 🎯 Users can generate agent-enabled projects in < 2 minutes
- 🎯 Generated projects have working agent examples
- 🎯 Clear documentation for all agent features
- 🎯 Easy to extend with custom agents/adapters

### Agent Capabilities
- 🎯 Support for 3+ agent frameworks (LangGraph, ADK, custom)
- 🎯 MCP server/client implementation
- 🎯 Unified agent interface via bridge pattern
- 🎯 Extensible adapter system

---

## 🔄 Development Workflow

### For Each Issue:
1. **Create branch**: `git checkout -b feature/issue-XX-description`
2. **Implement**: Follow TDD approach (test first)
3. **Test**: Ensure 100% coverage, all tests pass
4. **Validate**: Run template generation and validation
5. **Document**: Update relevant documentation
6. **PR**: Create pull request with clear description
7. **Review**: Address feedback, merge when approved

### Testing Checklist:
- [ ] Unit tests pass (`nox -s tests`)
- [ ] Template generates successfully
- [ ] No Jinja artifacts in generated project
- [ ] All cookiecutter option combinations work
- [ ] Documentation is updated
- [ ] CHANGELOG is updated (if applicable)

---

## 📝 Notes

- All changes must maintain backward compatibility with existing template users
- Agent features are opt-in via cookiecutter variables
- Generated projects without agent features should be identical to vanilla template
- Follow Hypermodern Python principles: simplicity, automation, reliability

---

**Last Updated**: December 26, 2025
**Current Milestone**: M1 (Google ADK Integration)
**Next Milestone**: M2 (MCP Integration)
