# AGENTS.md

![AGENTS.md logo](https://agents.md/og.png)

This file acts as the **single source of truth** for AI agents working on **this cookiecutter template repository**.

## Reality Check - Read This First

**CRITICAL FOR AI AGENTS**: This document separates what is **CURRENTLY IMPLEMENTED** from what is **FUTURE GOALS**.

**CURRENTLY IMPLEMENTED (Works Now)**:
- ✅ Code location rules (RULE 1-3) - **MANDATORY**
- ✅ Manual testing requirement - **MANDATORY**
- ✅ Template validation script (`tools/validate_template.py`) - **WORKS**
- ✅ Validation checklist commands - **ALL WORK**

**NOT YET IMPLEMENTED (Future Goals)**:
- ❌ Pre-commit hooks - **DO NOT EXIST** (`.git/hooks/pre-commit` missing)
- ❌ Pre-push hooks - **DO NOT EXIST** (`.git/hooks/pre-push` missing)
- ❌ Automated enforcement gates - **SIMULATION ONLY** (`tools/implement_validation_gates.py` is dry-run by default)
- ❌ `--save-checklist` flag - **DOES NOT EXIST** in `validate_template.py`

**ENFORCEMENT STATUS**:
- Rules marked **MANDATORY** = You MUST follow these. They are manually verified.
- Rules marked **EXPECTED** = You SHOULD follow these. They will be enforced when automation exists.
- If you see "BLOCKS" or "TECHNICALLY ENFORCED" = This is aspirational. Currently manual verification required.

## Two Levels: Template vs Generated Project

> [!CAUTION]
> This repository has **two separate contexts** for AI agents:
>
> | Context | AGENTS.md Location | Purpose |
> |---------|-------------------|---------|
> | **Template** (this repo) | `/AGENTS.md` (this file) | Developing the cookiecutter template itself |
> | **Generated Project** | `{{cookiecutter.project_name}}/AGENTS.md` | End-user projects created from this template |

### Working with Jinja Templates

Files inside `{{cookiecutter.project_name}}/` are **Jinja2 templates**, not regular Python files.

> [!WARNING]
> **⛔ NEVER simplify or "fix" `{{cookiecutter.*}}` expressions!**
> These are intentional template variables that get replaced during project generation.

**Examples of expressions you must preserve:**
- `{{cookiecutter.project_name}}` → becomes the project name
- `{{cookiecutter.friendly_name}}` → becomes human-readable name
- `{{cookiecutter.author}}` → becomes the author name
- `{%- if cookiecutter.license == 'MIT' -%}` → conditional blocks

## Identity & Goals

You are an expert **Hypermodern Python Developer** working on a **Cookiecutter template**.
Your goal is to improve the template while maintaining compatibility with generated projects.

> [!TIP]
> **Primary Directive**: If it's not tested, you should test it through the proposed procedure or create one by using best practices. If it breaks coverage, it needs to be fixed until it works and the code runs smoothly.

## Project Overview

This is a **Cookiecutter template** for Hypermodern Python projects using `poetry` and `nox`.
The goal is to provide a robust, modern Python project template with best practices baked in.

## Development Environment Configuration

### Top-Level Tools
- **Python**: 3.7+
- **Dependency Management**: [Poetry](https://python-poetry.org/)
- **Task Runner**: [Nox](https://nox.thea.codes/)
- **Project Structure**: [Cookiecutter](https://cookiecutter.readthedocs.io/)

### Quick Start
```bash
pip install nox poetry
```

## Code Location Rules (MANDATORY - CURRENTLY ENFORCED)

**RULE 1**: Code in `tools/` (root level) → Tests in `tests/` (root level)
- `tools/resolve-issues.py` → `tests/test_resolve_issues.py`
- `tools/prepare-github-release.py` → `tests/test_prepare_github_release.py`
- Pattern: `tools/{name}.py` → `tests/test_{name}.py`

**RULE 2**: Code in `{{cookiecutter.project_name}}/src/` → Tests in `{{cookiecutter.project_name}}/tests/`
- Template code tests go in template directory

**RULE 3**: Tests MUST be written in the SAME session as code. NO exceptions.

**Definition of "Session"**: A **session** is a single conversation thread with an AI agent from initial request through final presentation. Code and tests written in the same session means written in the same conversation thread.

**ENFORCEMENT**: These rules are manually verified. Violations will be caught during code review.

## Testing Requirements (MANDATORY - CURRENTLY ENFORCED)

**REQUIREMENT 1**: All external dependencies MUST be mocked.
- GitHub API calls → Mock `github3` or `requests`
- Git commands → Mock `subprocess.run`
- File system → Mock `Path` operations if needed
- Environment variables → Mock `os.getenv`

**REQUIREMENT 2**: Tests MUST pass before code is considered complete.
- Run: `python3 -m pytest tests/` (or equivalent)
- ALL tests must pass
- NO test failures allowed

**REQUIREMENT 3**: Test coverage MUST be 100% for new code.
- Use coverage tools to verify
- NO uncovered lines allowed

**ENFORCEMENT**: Tests are manually verified. Code without tests will be rejected.

## Thinking Process (MANDATORY - MANUALLY ENFORCED)

**CRITICAL**: This process MUST be followed in EXACT order. Skipping ANY step is a violation.

**CURRENT ENFORCEMENT**: Manual verification. Pre-commit/pre-push hooks are planned but not yet implemented.

1. **Understand**: Read `AGENTS.md` COMPLETELY. Read related file context. Understand the FULL scope.
2. **Plan**: Draft change in scratchpad or `<thinking>` block. Document ALL steps you will take.
3. **Implement + Test**: Write code AND tests TOGETHER in the SAME session. NO code without tests. NO tests after code.
4. **Verify**: Execute tests. Verify code works. Fix ALL failures BEFORE proceeding.
5. **Validate**: Run validation checklist (see below). ALL checks MUST pass.
6. **Refine**: If ANY check fails, fix it. Repeat validation. DO NOT proceed until ALL pass.
7. **Present**: Only present to user AFTER all steps complete and ALL checks pass.

**VIOLATION DETECTION**: 
- Currently: Manual review catches violations
- Planned: Pre-commit hook will REJECT commits without validation (not yet implemented)
- Planned: Pre-push hook will REJECT pushes without workflow compliance (not yet implemented)
- If you present code without completing steps 1-6, you have violated this process

## Agent Best Practices & Boundaries

**PROHIBITED ACTIONS** (MANDATORY - NO EXCEPTIONS):
- **⛔ DO NOT** run release commands (`nox -s publish-release`) interactively.
- **⛔ DO NOT** modify `.github/workflows` without explicit user approval.
- **⛔ DO NOT** simplify `{{cookiecutter.*}}` expressions—they are template variables!
- **⛔ DO NOT** present code without completing pre-presentation checklist.
- **⛔ DO NOT** skip validation steps. (Manual verification required - automation planned)
- **⛔ DO NOT** write code without tests. (Manual verification required - automation planned)
- **⛔ DO NOT** create unnecessary documents or files.
- **⛔ DO NOT** bypass git hooks with `--no-verify`. (Violates process - will be caught by CI)

**REQUIRED ACTIONS** (MANDATORY):
- **✅ DO** run partial test suites (`nox -s tests`) frequently.
- **✅ DO** use "Chain of Thought": Plan → Implement → Verify → Validate → Refine → Present.
- **✅ DO** consult `nox -l` to see all available sessions.
- **✅ DO** write tests in the SAME session as code. (Manually enforced - automation planned)
- **✅ DO** complete validation checklist before presenting. (Manually enforced - automation planned)
- **✅ DO** verify code works before presenting. (Manually enforced - automation planned)
- **✅ DO** mock all external dependencies in tests. (Manually enforced)

## Template Nox Sessions

| Command | Purpose |
|---------|---------|
| `nox` | Run default sessions (linkcheck) |
| `nox -s docs` | Build template documentation |
| `nox -s linkcheck` | Check documentation links |
| `nox -s dependencies-table` | Update dependencies table |
| `nox -s prepare-release` | Prepare a GitHub release |
| `nox -s publish-release` | Publish a GitHub release (⛔ interactive) |

### Coverage Rule
> [!IMPORTANT]
> **100% Code Coverage** is strictly enforced. Any changes that drop coverage below 100% will fail the build.

## Validating Templates (MANDATORY CHECKLIST)

**CRITICAL**: This checklist MUST be executed BEFORE any commit. NO exceptions.

**CURRENT ENFORCEMENT**: Manual execution required. Pre-commit hook is planned but not yet implemented.

### Validation Checklist (Execute in Order)

**All commands below are verified to work:**

```bash
# Step 1: Generate test project (overwrite if exists)
cookiecutter . --no-input --overwrite-if-exists

# Step 2: Verify TOML is valid
# Python 3.11+: use tomllib
python3 -c "import tomllib; f = open('hypermodern-python/pyproject.toml', 'rb'); tomllib.load(f); print('TOML OK')"
# Python <3.11: use tomli (install: pip install tomli)
python3 -c "import tomli; f = open('hypermodern-python/pyproject.toml', 'rb'); tomli.load(f); print('TOML OK')"

# Step 3: Verify Python syntax
find hypermodern-python/src -name "*.py" -exec python3 -m py_compile {} \;
# OR on Windows/PowerShell:
Get-ChildItem -Path hypermodern-python/src -Recurse -Filter "*.py" | ForEach-Object { python3 -m py_compile $_.FullName }

# Step 4: Check for unrendered Jinja artifacts
grep -r "{{cookiecutter" hypermodern-python/ && echo "ERROR: Jinja artifacts found" || echo "OK: No Jinja artifacts"
# OR on Windows/PowerShell:
Select-String -Path "hypermodern-python\**\*" -Pattern "{{cookiecutter" && echo "ERROR" || echo "OK"

# Step 5: Verify tests pass (if applicable)
cd hypermodern-python && nox -s tests && cd ..
```

**ALTERNATIVE**: Use validation script (this works):
```bash
python3 tools/validate_template.py
```

**VALIDATION RULE**: If ANY step fails, STOP. Fix the issue. Re-run validation from Step 1. DO NOT proceed until ALL steps pass.

**OUTPUT REQUIREMENT**: Validation MUST produce explicit "OK" or "ERROR" messages. Ambiguous output is a failure.

## Pre-Presentation Checklist (MANDATORY)

**CRITICAL**: This checklist MUST be completed BEFORE presenting work to user. NO exceptions.

- [ ] Code implemented
- [ ] Tests written (100% coverage for new code)
- [ ] Tests pass (`python3 -m pytest tests/` or equivalent)
- [ ] Template generates successfully (`cookiecutter . --no-input --overwrite-if-exists`)
- [ ] TOML is valid (no parse errors)
- [ ] Python syntax is valid (no compilation errors)
- [ ] No Jinja artifacts in generated project
- [ ] Code actually works (manual test if applicable)
- [ ] All linter checks pass
- [ ] Documentation updated if needed
- [ ] Validation checklist (above) completed and ALL steps passed

**PRESENTATION RULE**: If ANY checkbox is unchecked, DO NOT present. Fix issues. Re-validate. Present only when ALL checked.

**CURRENT ENFORCEMENT**: Manual verification required. Automated enforcement is planned but not yet implemented.

## Cookiecutter Variables

Variables defined in `cookiecutter.json`:
- `project_name` - Project slug (e.g., `hypermodern-python`)
- `package_name` - Python package name (derived)
- `friendly_name` - Human-readable name (derived)
- `author` - Author name
- `email` - Author email
- `github_user` - GitHub username
- `version` - Initial version
- `copyright_year` - Copyright year
- `license` - License type (MIT, Apache-2.0, GPL-3.0)
- `development_status` - PyPI development status

> [!NOTE]
> Variables `project_short_description` and `documentation` are used in templates but not defined in `cookiecutter.json`. This may need to be fixed.

## Contribution Guidelines

### Pull Requests
1. **Tests**: Must pass all `nox` sessions. NO test failures allowed.
2. **Coverage**: Ensure unit tests cover 100% of new code. NO uncovered lines.
3. **Documentation**: Update docs if functionality is modified or added.
4. **Labels**: Use descriptive labels (e.g., `enhancement`, `bug`, `documentation`).
5. **Validation**: Pre-presentation checklist MUST be completed.

### Commit Messages
- Use descriptive, imperative titles (e.g., "Add feature X", "Fix bug Y").
- Squash and merge is the preferred strategy.
- Include validation status in commit message if applicable.

## Workflows & Procedures

### Workflows
For complex multi-step tasks, refer to the workflows defined in `.agent/workflows`:
- **/docs**: Build project documentation
- **/lint**: Lint the codebase using pre-commit
- **/tests**: Test the cookiecutter template

### Standard Procedures
For consistent execution of common tasks:
- **Testing**: `.agent/procedures/TESTING_PROCEDURE.md` - How to write and validate tests (READ THIS FIRST)

## Future Automation (PLANNED - NOT YET IMPLEMENTED)

The following features are **planned but not yet implemented**. They are documented here so agents understand what automation is coming.

### Planned: Pre-Commit Hook

**Status**: NOT IMPLEMENTED. Hook does not exist at `.git/hooks/pre-commit`.

**Planned Behavior**:
- Would run automatically on `git commit`
- Would validate: template generation, TOML syntax, Jinja artifacts, Python syntax
- Would exit with code 1 to REJECT commits that fail

**Installation** (when implemented):
```bash
python3 tools/implement_validation_gates.py --no-dry-run
```

**Current Workaround**: Manually run validation checklist before committing.

### Planned: Pre-Push Hook

**Status**: NOT IMPLEMENTED. Hook does not exist at `.git/hooks/pre-push`.

**Planned Behavior**:
- Would run automatically on `git push`
- Would validate: validation checklist completion, 100% test coverage, workflow compliance
- Would exit with code 1 to REJECT pushes that fail

**Installation** (when implemented):
```bash
python3 tools/implement_validation_gates.py --no-dry-run
```

**Current Workaround**: Manually verify all checklist items before pushing.

### Planned: Orchestrator Validation Gates

**Status**: NOT IMPLEMENTED. `ProductionOrchestrator` does not have validation gates.

**Planned Behavior**:
- Would enforce sequential step completion (step N must complete before step N+1)
- Would use A2A protocol for multi-agent coordination
- Would block task execution if validation gates fail

**Current Workaround**: Manually follow the thinking process steps in order.

### Planned: Validation State Tracking

**Status**: NOT IMPLEMENTED. `--save-checklist` flag does not exist in `tools/validate_template.py`.

**Planned Behavior**:
- Would save validation state to `.validation_checklist.json`
- Would include: validation steps status, test coverage percentage, timestamp, git commit hash
- Would be required by pre-push hook

**Current Workaround**: `.validation_checklist.json` can be manually created if needed, but it's not required.

## Verification Commands (All Verified to Work)

These commands are verified to exist and work:

```bash
# Validate template
python3 tools/validate_template.py

# Run tests
python3 -m pytest tests/

# Generate template
cookiecutter . --no-input --overwrite-if-exists

# Check for hooks (will show missing until implemented)
test -f .git/hooks/pre-commit && echo "✅ Pre-commit hook exists" || echo "❌ Pre-commit hook missing"
test -f .git/hooks/pre-push && echo "✅ Pre-push hook exists" || echo "❌ Pre-push hook missing"
```

---
*Generated based on [agents.md](https://agents.md) philosophy.*
