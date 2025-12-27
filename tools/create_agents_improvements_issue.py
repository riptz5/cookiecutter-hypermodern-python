#!/usr/bin/env python
"""Create GitHub issue for AGENTS.md improvements based on prompt engineering best practices."""
import os
import sys
from pathlib import Path

import click
import github3


def get_github_repo(owner: str, repository: str, token: str):
    """Get GitHub repository instance."""
    github = github3.login(token=token)
    return github.repository(owner, repository)


def create_issue(repository, title: str, body: str, labels: list[str]) -> bool:
    """Create a GitHub issue."""
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
    """Create GitHub issue for AGENTS.md improvements."""
    
    repo = get_github_repo(owner, repository, token)
    
    title = "Improve AGENTS.md with honest language and latest prompt engineering best practices"
    
    body = """## Problem Statement

The current `AGENTS.md` presents aspirational features as if they're technically enforced, which confuses agents about what's mandatory vs optional. This violates core prompt engineering principles of clarity and honesty.

### Current Issues

1. **False Claims**: Document claims "TECHNICALLY ENFORCED" and "BLOCKS" when these features don't exist
2. **Missing Features**: References to `--save-checklist` flag that doesn't exist in `tools/validate_template.py`
3. **Unclear Status**: No clear separation between what works vs what's planned
4. **Ambiguous Language**: Uses absolute terms ("NO EXCEPTIONS", "CANNOT be bypassed") for features that aren't implemented

### Verification Results

**What Actually Works:**
- ✅ `tools/validate_template.py` exists and works
- ✅ Code location rules (RULE 1-3) are documented
- ✅ Manual validation process works
- ✅ Template generation validation works

**What Doesn't Work (but is claimed to):**
- ❌ Pre-commit hook: MISSING (not installed)
- ❌ Pre-push hook: MISSING (not installed)
- ❌ `--save-checklist` flag: DOESN'T EXIST in validate_template.py
- ❌ "TECHNICALLY ENFORCED": False - these are manual processes
- ❌ "BLOCKS": False - nothing blocks automatically

## Proposed Improvements

Based on latest prompt engineering best practices (2024-2025):

### 1. Separate Reality from Aspirations

**Current**: Mixed claims about what works vs what's planned

**Proposed**: Clear sections:
- "What Actually Works (Currently Implemented)"
- "What We Want But Don't Have Yet (Planned/Desired)"
- "Until Those Exist (Manual Process Required)"

### 2. Use Honest Language

**Replace:**
- ❌ "BLOCKS" → ✅ "SHOULD validate" or "Expected to validate"
- ❌ "TECHNICALLY ENFORCED" → ✅ "Manual verification required" or "Process expectation"
- ❌ "NO EXCEPTIONS" → ✅ "Expected unless justified"
- ❌ "MANDATORY" → ✅ "Required" (for implemented) or "Expected" (for aspirational)
- ❌ "CANNOT be bypassed" → ✅ "Should not be bypassed" (until actually implemented)

### 3. Define Key Terms Explicitly

**Add definitions:**
- **Session**: A single conversation thread with an agent (one user query → agent response cycle, or a complete task from start to finish)
- **Validation**: The process of verifying template generation works correctly
- **Workflow Compliance**: Following the defined process steps

### 4. Fix Tool References

**Remove or mark as TODO:**
- `python3 tools/validate_template.py --save-checklist` → Remove or mark as "TODO: Not yet implemented"
- Pre-commit hook installation → Mark as "Planned feature"
- Pre-push hook installation → Mark as "Planned feature"

**Keep only working commands:**
- `python3 tools/validate_template.py` (works)
- `python3 -m pytest tests/` (works)
- `cookiecutter . --no-input --overwrite-if-exists` (works)

### 5. Make Checklists Verifiable

**Ensure all checklist items:**
- Can be verified manually without CI
- Use commands that actually exist
- Don't depend on non-existent tools
- Have clear success/failure criteria

### 6. Incorporate Latest Prompt Engineering Best Practices

**Based on 2024-2025 trends:**
- **Clarity**: Use simple, direct language
- **Honesty**: Never claim something works if it doesn't
- **Specificity**: Provide exact commands, not vague instructions
- **Structure**: Clear hierarchy with visual indicators (✅/❌/⚠️)
- **Context**: Explain WHY rules exist, not just WHAT they are
- **Boundaries**: Clearly state what agents should NOT do

## Implementation Plan

1. **Phase 1**: Restructure document with clear sections
   - Add "What Actually Works" section
   - Add "What We Want But Don't Have Yet" section
   - Add "Until Those Exist" section

2. **Phase 2**: Replace all false claims with honest language
   - Replace "BLOCKS" with "SHOULD validate"
   - Replace "TECHNICALLY ENFORCED" with "Manual verification required"
   - Replace "NO EXCEPTIONS" with "Expected unless justified"

3. **Phase 3**: Add explicit definitions
   - Define "Session"
   - Define "Validation"
   - Define "Workflow Compliance"

4. **Phase 4**: Fix tool references
   - Remove non-existent `--save-checklist` flag
   - Mark pre-commit/pre-push hooks as "PLANNED - NOT IMPLEMENTED"
   - Verify all commands actually work

5. **Phase 5**: Make checklists verifiable
   - Ensure all items can be checked manually
   - Use exact commands that work
   - Remove dependencies on non-existent tools

## Acceptance Criteria

- [ ] Document clearly separates "Currently Implemented" from "Planned/Desired"
- [ ] All false claims replaced with honest language
- [ ] Key terms explicitly defined
- [ ] All referenced tools/commands actually exist and work
- [ ] All checklists are manually verifiable
- [ ] Language follows latest prompt engineering best practices
- [ ] No references to non-existent features (or clearly marked as TODO)
- [ ] Document is honest about current state vs future plans

## Verification Commands

```bash
# Verify tools exist
test -f tools/validate_template.py && echo "EXISTS" || echo "MISSING"
test -f .git/hooks/pre-commit && echo "EXISTS" || echo "MISSING"
test -f .git/hooks/pre-push && echo "EXISTS" || echo "MISSING"

# Verify commands work
python3 tools/validate_template.py  # Should work
python3 -m pytest tests/  # Should work
cookiecutter . --no-input --overwrite-if-exists  # Should work (if template structure is correct)

# Verify no false claims
grep -i "technically enforced" AGENTS.md  # Should only appear in "Planned" sections
grep -i "blocks" AGENTS.md  # Should only appear in "Planned" sections or as "SHOULD validate"
```

## Related Files

- `AGENTS.md` - Main document to improve
- `tools/validate_template.py` - Validation tool (works, but missing `--save-checklist` flag)
- `tools/implement_validation_gates.py` - Gate implementation tool (simulation only)

## Labels

- `enhancement`
- `documentation`
- `prompt-engineering`
- `agent-guidelines`
"""
    
    labels = ["enhancement", "documentation", "prompt-engineering", "agent-guidelines"]
    
    if dry_run:
        click.echo("[DRY RUN] Would create issue:")
        click.echo(f"  Title: {title}")
        click.echo(f"  Labels: {', '.join(labels)}")
        click.echo(f"  Body length: {len(body)} characters")
    else:
        success = create_issue(repo, title, body, labels)
        if success:
            click.echo("\n✓ Issue created successfully!")
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
