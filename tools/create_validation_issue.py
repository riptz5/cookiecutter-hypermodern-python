#!/usr/bin/env python
"""Create GitHub issue for template validation tasks."""
import os
import sys
from pathlib import Path

import click
import github3


def get_github_repo(owner: str, repository: str, token: str):
    """Get GitHub repository instance."""
    github = github3.login(token=token)
    return github.repository(owner, repository)


def create_validation_issue(repository, title: str, body: str, labels: list[str]) -> bool:
    """Create a GitHub issue for validation tasks."""
    try:
        issue = repository.create_issue(
            title=title,
            body=body,
            labels=labels
        )
        if issue:
            click.secho(f"✓ Created issue #{issue.number}: {title}", fg="green")
            click.echo(f"  URL: {issue.html_url}")
            return True
        return False
    except Exception as e:
        click.secho(f"✗ Error creating issue: {e}", fg="red")
        return False


@click.command()
@click.option(
    "--owner",
    metavar="USER",
    required=True,
    envvar="GITHUB_USER",
    default="riptz5",
    help="GitHub username",
)
@click.option(
    "--repository",
    metavar="REPO",
    required=True,
    envvar="GITHUB_REPOSITORY",
    default="cookiecutter-hypermodern-python",
    help="GitHub repository",
)
@click.option(
    "--token",
    metavar="TOKEN",
    required=True,
    envvar="GITHUB_TOKEN",
    help="GitHub API token",
)
@click.option(
    "--dry-run/--no-dry-run",
    default=False,
    help="Dry run mode (don't actually create issue)",
)
def main(owner: str, repository: str, token: str, dry_run: bool) -> None:
    """Create GitHub issue for template validation enforcement tasks."""
    
    repo = get_github_repo(owner, repository, token)
    
    title = "Implement enforcement gates for AGENTS.md workflow compliance"
    
    body = """## Problem Statement

Currently, AGENTS.md defines a workflow (Plan → Implement → Verify → Refine) but there is **no technical enforcement**. Agents can skip steps without consequences.

### Current State
- ❌ Pre-commit hooks can be bypassed with `--no-verify`
- ❌ GitHub Actions run POST-COMMIT (too late)
- ❌ Validation steps are "advisory" only
- ❌ No gates that block progression without completing previous steps

### Required Solution

Implement a **gate system** that:
1. **Blocks commits** without validation (pre-commit hook that CANNOT be bypassed)
2. **Verifies workflow compliance** before allowing push
3. **Uses orchestrator** to enforce sequential step completion
4. **Integrates with A2A protocol** for multi-agent coordination

## Technical Requirements

### 1. Pre-Commit Gate (Mandatory)
- Hook that validates template generation
- Checks for Jinja artifacts
- Verifies TOML syntax
- **Cannot be bypassed** (fail hard on violation)

### 2. Pre-Push Gate
- Verifies all validation steps completed
- Checks test coverage (100% requirement)
- Validates workflow compliance
- Blocks push if any check fails

### 3. Orchestrator Integration
- Use existing `ProductionOrchestrator` to enforce sequential steps
- Each step must complete before next can start
- Use A2A protocol for agent coordination

### 4. GitHub Integration
- Create issues automatically for validation failures
- Use `tools/resolve-issues.py` for auto-resolution
- Track validation state in GitHub

## Implementation Plan

1. **Phase 1**: Create mandatory pre-commit hook
   - File: `.git/hooks/pre-commit` (not `.pre-commit-config.yaml`)
   - Validates template generation
   - Exits with error code on failure

2. **Phase 2**: Create pre-push hook
   - File: `.git/hooks/pre-push`
   - Verifies validation checklist completed
   - Blocks push if incomplete

3. **Phase 3**: Orchestrator integration
   - Extend `ProductionOrchestrator` with validation gates
   - Use A2A protocol for step coordination
   - Implement sequential enforcement

4. **Phase 4**: GitHub automation
   - Auto-create issues for validation failures
   - Use existing `tools/resolve-issues.py` infrastructure
   - Track compliance metrics

## Acceptance Criteria

- [ ] Pre-commit hook blocks commits without validation
- [ ] Pre-push hook blocks push without workflow compliance
- [ ] Orchestrator enforces sequential step completion
- [ ] A2A protocol used for agent coordination
- [ ] GitHub issues auto-created for failures
- [ ] 100% test coverage maintained
- [ ] Documentation updated

## Related Files

- `AGENTS.md` - Workflow definition
- `.agent/procedures/TESTING_PROCEDURE.md` - Validation checklist
- `hooks/post_gen_project.py` - Post-generation validation
- `{{cookiecutter.project_name}}/src/{{cookiecutter.package_name}}/agents/orchestrator.py` - Orchestrator
- `{{cookiecutter.project_name}}/src/{{cookiecutter.package_name}}/agents/a2a/protocol.py` - A2A protocol
- `tools/resolve-issues.py` - Issue resolution automation

## Labels

- `enhancement`
- `genesis`
- `validation`
- `automation`
- `multi-agent`
"""

    labels = ["enhancement", "genesis", "validation", "automation", "multi-agent"]
    
    if dry_run:
        click.echo("[DRY RUN] Would create issue:")
        click.echo(f"  Title: {title}")
        click.echo(f"  Labels: {', '.join(labels)}")
        click.echo(f"  Body length: {len(body)} characters")
    else:
        success = create_validation_issue(repo, title, body, labels)
        if success:
            click.echo("\n✓ Issue created successfully!")
            click.echo("  Other agents can now pick this up via orchestrator.")
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
