
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
> **Primary Directive**: If it's not tested, it doesn't exist. If it breaks coverage, it's rejected.

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

### Agent Best Practices & Boundaries
- **⛔ DO NOT** run release commands (`nox -s publish-release`) interactively.
- **⛔ DO NOT** modify `.github/workflows` without explicit user approval.
- **⛔ DO NOT** simplify `{{cookiecutter.*}}` expressions—they are template variables!
- **✅ DO** run partial test suites (`nox -s tests`) frequently.
- **✅ DO** use "Chain of Thought": Plan → Implement → Verify.
- **✅ DO** consult `nox -l` to see all available sessions.

### Thinking Process
1. **Understand**: Read `AGENTS.md` and related file context.
2. **Plan**: Draft a change in your scratchpad or `<thinking>` block.
3. **Test**: Verify your change locally using `nox`.
4. **Refine**: If tests fail, fix *before* presenting to the user.

## Testing & Verification
We use `nox` to manage all testing and linting sessions.

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
1. **Tests**: Must pass all `nox` sessions.
2. **Coverage**: Ensure unit tests cover 100% of new code.
3. **Documentation**: Update docs if functionality is modified or added.
4. **Labels**: Use descriptive labels (e.g., `enhancement`, `bug`, `documentation`).

### Commit Messages
- Use descriptive, imperative titles (e.g., "Add feature X", "Fix bug Y").
- Squash and merge is the preferred strategy.

## Workflows
For complex multi-step tasks, refer to the workflows defined in `.agent/workflows`:
- **/docs**: Build project documentation
- **/lint**: Lint the codebase using pre-commit
- **/tests**: Test the cookiecutter template

---
*Generated based on [agents.md](https://agents.md) philosophy.*
