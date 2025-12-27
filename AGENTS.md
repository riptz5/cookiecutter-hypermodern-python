
# AGENTS.md

![AGENTS.md logo](https://agents.md/og.png)

This file acts as the **single source of truth** for AI agents working on **this cookiecutter template repository**.

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

### Agent Best Practices & Boundaries (STRICT RULES)

**PROHIBITED ACTIONS** (NO EXCEPTIONS):
- **⛔ DO NOT** run release commands (`nox -s publish-release`) interactively.
- **⛔ DO NOT** modify `.github/workflows` without explicit user approval.
- **⛔ DO NOT** simplify `{{cookiecutter.*}}` expressions—they are template variables!
- **⛔ DO NOT** present code without completing pre-presentation checklist.
- **⛔ DO NOT** skip validation steps.
- **⛔ DO NOT** write code without tests.
- **⛔ DO NOT** create unnecessary documents or files.

**REQUIRED ACTIONS** (MANDATORY):
- **✅ DO** run partial test suites (`nox -s tests`) frequently.
- **✅ DO** use "Chain of Thought": Plan → Implement → Verify → Validate → Refine → Present.
- **✅ DO** consult `nox -l` to see all available sessions.
- **✅ DO** write tests in the SAME session as code.
- **✅ DO** complete validation checklist before presenting.
- **✅ DO** verify code works before presenting.
- **✅ DO** mock all external dependencies in tests.

### Thinking Process (MANDATORY - NO EXCEPTIONS)

**CRITICAL**: This process MUST be followed in EXACT order. Skipping ANY step is a violation.

1. **Understand**: Read `AGENTS.md` COMPLETELY. Read related file context. Understand the FULL scope.
2. **Plan**: Draft change in scratchpad or `<thinking>` block. Document ALL steps you will take.
3. **Implement + Test**: Write code AND tests TOGETHER in the SAME session. NO code without tests. NO tests after code.
4. **Verify**: Execute tests. Verify code works. Fix ALL failures BEFORE proceeding.
5. **Validate**: Run validation checklist (see below). ALL checks MUST pass.
6. **Refine**: If ANY check fails, fix it. Repeat validation. DO NOT proceed until ALL pass.
7. **Present**: Only present to user AFTER all steps complete and ALL checks pass.

**VIOLATION DETECTION**: If you present code without completing steps 1-6, you have violated this process.

## Testing & Verification
We use `nox` to manage all testing and linting sessions.

### Code Location Rules (MANDATORY)

**RULE 1**: Code in `tools/` (root level) → Tests in `tests/` (root level)
- `tools/resolve-issues.py` → `tests/test_resolve_issues.py`
- `tools/prepare-github-release.py` → `tests/test_prepare_github_release.py`
- Pattern: `tools/{name}.py` → `tests/test_{name}.py`

**RULE 2**: Code in `{{cookiecutter.project_name}}/src/` → Tests in `{{cookiecutter.project_name}}/tests/`
- Template code tests go in template directory

**RULE 3**: Tests MUST be written in the SAME session as code. NO exceptions.

### Template Nox Sessions
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

### Testing Requirements (MANDATORY)

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

## Validating Templates (MANDATORY CHECKLIST)

**CRITICAL**: This checklist MUST be executed BEFORE any commit. NO exceptions.

### Validation Checklist (Execute in Order)

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

**VALIDATION RULE**: If ANY step fails, STOP. Fix the issue. Re-run validation from Step 1. DO NOT proceed until ALL steps pass.

**ALTERNATIVE**: Use validation script:
```bash
python3 tools/validate_template.py
```

**OUTPUT REQUIREMENT**: Validation MUST produce explicit "OK" or "ERROR" messages. Ambiguous output is a failure.

---
*Generated based on [agents.md](https://agents.md) philosophy.*
