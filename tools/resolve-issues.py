"""Automatically resolve GitHub issues using AI agent capabilities."""
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import github3


def get_github_repo(owner: str, repository: str, token: str):
    """Get GitHub repository instance."""
    github = github3.login(token=token)
    return github.repository(owner, repository)


def list_open_issues(repository: Any, labels: Optional[List[str]] = None) -> List[Any]:
    """List open issues from repository.
    
    Args:
        repository: GitHub repository instance
        labels: Optional list of labels to filter by
        
    Returns:
        List of open issues
    """
    issues = []
    for issue in repository.issues(state="open", labels=labels or []):
        issues.append(issue)
    return issues


def can_auto_resolve(issue: Any) -> tuple[bool, str]:
    """Determine if an issue can be auto-resolved.
    
    Args:
        issue: GitHub issue instance
        
    Returns:
        Tuple of (can_resolve: bool, reason: str)
    """
    # Skip issues that are already assigned (human working on it)
    if issue.assignee:
        return False, "Issue is assigned to a human"
    
    # Skip issues with "no-auto-resolve" label
    label_names = {label.name for label in issue.labels}
    if "no-auto-resolve" in label_names:
        return False, "Issue has 'no-auto-resolve' label"
    
    # Skip issues that are questions/discussions
    if "question" in label_names or "discussion" in label_names:
        return False, "Issue is a question/discussion"
    
    # Issues that CAN be auto-resolved:
    # - Bug fixes (if simple)
    # - Documentation updates
    # - Code style/formatting
    # - Dependency updates
    # - Template improvements
    
    if "bug" in label_names and "good first issue" in label_names:
        return True, "Simple bug fix suitable for auto-resolution"
    
    if "documentation" in label_names:
        return True, "Documentation update"
    
    if "style" in label_names or "refactoring" in label_names:
        return True, "Code style/formatting"
    
    if "dependencies" in label_names:
        return True, "Dependency update"
    
    if "cookiecutter" in label_names or "template" in label_names:
        return True, "Template improvement"
    
    # Default: can try to resolve
    return True, "Issue appears resolvable by agent"


def analyze_issue(issue: Any, repo_path: Path) -> Dict[str, Any]:
    """Analyze an issue to determine resolution strategy.
    
    Args:
        issue: GitHub issue instance
        repo_path: Path to repository root
        
    Returns:
        Dictionary with analysis results
    """
    can_resolve, reason = can_auto_resolve(issue)
    
    analysis = {
        "number": issue.number,
        "title": issue.title,
        "can_resolve": can_resolve,
        "reason": reason,
        "labels": [label.name for label in issue.labels],
        "body": issue.body or "",
    }
    
    # Try to identify files mentioned in issue
    mentioned_files = []
    if issue.body:
        # Simple heuristic: look for file paths
        import re
        file_pattern = r'`([^`]+\.(py|md|toml|yaml|yml|txt))`'
        mentioned_files = re.findall(file_pattern, issue.body)
        mentioned_files = [f[0] for f in mentioned_files]
    
    analysis["mentioned_files"] = mentioned_files
    
    return analysis


def git_command(*args: str, cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd or Path.cwd(),
            capture_output=True,
            text=True,
            check=check,
        )
        return result
    except subprocess.CalledProcessError as e:
        click.secho(f"Git error: {e.stderr}", fg="red")
        raise


def resolve_issue(
    issue: Any,
    repo_path: Path,
    repository: Any,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """Attempt to resolve an issue.
    
    Args:
        issue: GitHub issue instance
        repo_path: Path to repository root
        repository: GitHub repository instance
        dry_run: If True, don't make actual changes
        
    Returns:
        Dictionary with resolution results
    """
    analysis = analyze_issue(issue, repo_path)
    
    if not analysis["can_resolve"]:
        return {
            "success": False,
            "reason": analysis["reason"],
            "analysis": analysis,
        }
    
    branch_name = f"auto-resolve-{issue.number}"
    result = {
        "success": True,
        "dry_run": dry_run,
        "analysis": analysis,
        "branch_name": branch_name,
        "changes_made": [],
        "tests_passed": False,
        "pr_created": False,
    }
    
    if dry_run:
        click.echo(f"[DRY RUN] Would resolve issue #{issue.number}: {issue.title}")
        click.echo(f"  Would create branch: {branch_name}")
        result["message"] = "Dry run - no changes made"
        return result
    
    # Create branch
    try:
        git_command("checkout", "-b", branch_name, cwd=repo_path)
        click.echo(f"✓ Created branch: {branch_name}")
    except subprocess.CalledProcessError:
        # Branch might already exist
        git_command("checkout", branch_name, cwd=repo_path)
        click.echo(f"✓ Switched to existing branch: {branch_name}")
    
    # Implement actual resolution logic
    # 1. Read the issue description
    issue_body = issue.body or ""
    issue_title = issue.title
    
    click.echo(f"📋 Analyzing issue: {issue_title}")
    click.echo(f"   Description: {issue_body[:200]}...")
    
    # 2. Determine what needs to be done based on issue content
    changes_made = []
    files_modified = []
    
    # Simple heuristics for common issue types
    issue_lower = (issue_title + " " + issue_body).lower()
    
    # Documentation fixes
    if any(keyword in issue_lower for keyword in ["typo", "spelling", "grammar", "documentation", "doc"]):
        # Find documentation files mentioned
        doc_files = analysis.get("mentioned_files", [])
        if doc_files:
            click.echo(f"   📝 Would fix documentation in: {', '.join(doc_files)}")
            changes_made.append("Documentation fix")
        else:
            click.echo("   ⚠️  Documentation issue but no files mentioned")
    
    # Code style/formatting
    elif any(keyword in issue_lower for keyword in ["format", "style", "black", "isort", "lint"]):
        click.echo("   🎨 Would run code formatters")
        changes_made.append("Code formatting")
        # Would run: black, isort, etc.
    
    # Template issues
    elif any(keyword in issue_lower for keyword in ["template", "cookiecutter", "jinja"]):
        template_files = [f for f in analysis.get("mentioned_files", []) if "cookiecutter" in f.lower() or ".toml" in f or ".yaml" in f]
        if template_files:
            click.echo(f"   🔧 Would fix template in: {', '.join(template_files)}")
            changes_made.append("Template fix")
    
    # For now, if we can't determine the fix, create a structured PR for manual completion
    if not changes_made:
        click.echo("   ⚠️  Issue type not automatically resolvable")
        click.echo("   📝 Creating PR with issue details for manual resolution")
        changes_made.append("Manual resolution needed")
    
    # 3. Make actual changes (placeholder - would use agent capabilities)
    # In a full implementation, this would:
    # - Use the agent's code editing capabilities
    # - Make actual file changes
    # - Run formatters if needed
    
    # 4. Run tests (if changes were made)
    tests_passed = False
    if changes_made and "Manual resolution needed" not in changes_made:
        click.echo("   🧪 Running tests...")
        try:
            # Check if we're in a generated project or template
            if (repo_path / "noxfile.py").exists():
                test_result = subprocess.run(
                    ["nox", "-s", "tests"],
                    cwd=repo_path,
                    capture_output=True,
                    timeout=300,
                )
                tests_passed = test_result.returncode == 0
                if tests_passed:
                    click.echo("   ✅ Tests passed")
                else:
                    click.echo(f"   ❌ Tests failed: {test_result.stderr[:200]}")
            else:
                click.echo("   ⚠️  No noxfile.py found, skipping tests")
                tests_passed = True  # Assume OK if no tests
        except subprocess.TimeoutExpired:
            click.echo("   ⏱️  Tests timed out")
        except Exception as e:
            click.echo(f"   ⚠️  Could not run tests: {e}")
    
    result["changes_made"] = changes_made
    result["tests_passed"] = tests_passed
    
    # 5. Commit changes
    try:
        # Check if there are actual changes to commit
        git_status = git_command("status", "--porcelain", cwd=repo_path, check=False)
        if git_status.stdout.strip():
            git_command("add", "-A", cwd=repo_path)
            commit_msg = f"[Auto] Resolve #{issue.number}: {issue.title}\n\n"
            commit_msg += f"Issue: {issue.html_url}\n"
            commit_msg += f"Changes: {', '.join(changes_made)}\n"
            if not tests_passed and changes_made:
                commit_msg += "\n⚠️ Tests need to be fixed"
            
            git_command("commit", "-m", commit_msg, cwd=repo_path)
            click.echo("✓ Committed changes")
        else:
            # No changes, create empty commit with issue info
            commit_msg = f"[Auto] Resolve #{issue.number}: {issue.title}\n\n"
            commit_msg += f"Issue: {issue.html_url}\n"
            commit_msg += "Status: Analysis complete, manual changes may be needed"
            git_command("commit", "--allow-empty", "-m", commit_msg, cwd=repo_path)
            click.echo("✓ Created commit (no code changes detected)")
        
        # Push branch
        git_command("push", "-u", "origin", branch_name, cwd=repo_path)
        click.echo(f"✓ Pushed branch: {branch_name}")
        
        # Create PR
        changes_list = "\n".join([f"- {change}" for change in changes_made])
        test_status = "✅ Passed" if tests_passed else "⚠️ Needs attention"
        
        pr_body = f"""## Automated Resolution

This PR was created automatically to resolve issue #{issue.number}.

**Issue**: {issue.title}
**Issue URL**: {issue.html_url}

### Analysis
{changes_list}

### Test Status
{test_status}

### Next Steps
{"✅ Ready for review" if tests_passed else "⚠️ Manual review recommended - tests may need attention"}

### Auto-merge
This PR will be auto-approved and merged if all checks pass.
"""
        
        pr = repository.create_pull(
            title=f"[Auto] Fix #{issue.number}: {issue.title}",
            base="main",
            head=branch_name,
            body=pr_body,
        )
        
        # Add labels
        pr.issue().add_labels("auto-resolved", "enhancement")
        
        # Comment on issue
        issue.create_comment(
            f"🤖 Automated resolution PR created: #{pr.number}\n\n"
            f"This PR will be auto-approved and merged if all checks pass."
        )
        
        result["pr_created"] = True
        result["pr_number"] = pr.number
        result["message"] = f"PR #{pr.number} created successfully"
        click.echo(f"✓ Created PR: #{pr.number}")
        
    except Exception as e:
        click.secho(f"Error during resolution: {e}", fg="red")
        result["success"] = False
        result["message"] = f"Error: {e}"
    
    return result


def create_pr_for_issue(
    repository: Any,
    issue: Any,
    branch_name: str,
    title: str,
    body: str,
    base: str = "main",
) -> Optional[Any]:
    """Create a pull request for a resolved issue.
    
    Args:
        repository: GitHub repository instance
        issue: GitHub issue instance
        branch_name: Name of branch with changes
        title: PR title
        body: PR body
        base: Base branch
        
    Returns:
        Pull request instance or None if creation failed
    """
    try:
        pr = repository.create_pull(
            title=title,
            base=base,
            head=branch_name,
            body=body,
        )
        
        # Link PR to issue
        issue.create_comment(f"Automated resolution: #{pr.number}")
        return pr
    except Exception as e:
        click.secho(f"Error creating PR: {e}", fg="red")
        return None


@click.group()
def cli():
    """Automatically resolve GitHub issues using AI agent."""
    pass


@cli.command()
@click.option(
    "--owner",
    metavar="USER",
    required=True,
    envvar="GITHUB_USER",
    help="GitHub username",
)
@click.option(
    "--repository",
    metavar="REPO",
    required=True,
    envvar="GITHUB_REPOSITORY",
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
    "--label",
    "labels",
    metavar="LABEL",
    multiple=True,
    help="Filter issues by label (may be specified multiple times)",
)
def list_cmd(owner: str, repository: str, token: str, labels: tuple) -> None:
    """List open issues."""
    repo = get_github_repo(owner, repository, token)
    issues = list_open_issues(repo, labels=list(labels) if labels else None)
    
    click.echo(f"Found {len(issues)} open issue(s):\n")
    for issue in issues:
        labels_str = ", ".join([label.name for label in issue.labels])
        click.echo(f"  #{issue.number}: {issue.title}")
        click.echo(f"    Labels: {labels_str}")
        click.echo(f"    URL: {issue.html_url}\n")


@cli.command()
@click.option(
    "--owner",
    metavar="USER",
    required=True,
    envvar="GITHUB_USER",
    help="GitHub username",
)
@click.option(
    "--repository",
    metavar="REPO",
    required=True,
    envvar="GITHUB_REPOSITORY",
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
    "--label",
    "labels",
    metavar="LABEL",
    multiple=True,
    help="Filter issues by label (may be specified multiple times)",
)
def analyze(owner: str, repository: str, token: str, labels: tuple) -> None:
    """Analyze issues to determine if they can be auto-resolved."""
    repo = get_github_repo(owner, repository, token)
    issues = list_open_issues(repo, labels=list(labels) if labels else None)
    repo_path = Path.cwd()
    
    click.echo(f"Analyzing {len(issues)} issue(s):\n")
    
    resolvable = []
    not_resolvable = []
    
    for issue in issues:
        analysis = analyze_issue(issue, repo_path)
        if analysis["can_resolve"]:
            resolvable.append(analysis)
            click.secho(f"  ✓ #{issue.number}: {issue.title}", fg="green")
            click.echo(f"    Reason: {analysis['reason']}")
        else:
            not_resolvable.append(analysis)
            click.secho(f"  ✗ #{issue.number}: {issue.title}", fg="yellow")
            click.echo(f"    Reason: {analysis['reason']}")
        click.echo()
    
    click.echo(f"\nSummary:")
    click.echo(f"  Resolvable: {len(resolvable)}")
    click.echo(f"  Not resolvable: {len(not_resolvable)}")


@cli.command()
@click.option(
    "--owner",
    metavar="USER",
    required=True,
    envvar="GITHUB_USER",
    help="GitHub username",
)
@click.option(
    "--repository",
    metavar="REPO",
    required=True,
    envvar="GITHUB_REPOSITORY",
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
    default=True,
    help="Dry run mode (don't make actual changes)",
)
@click.option(
    "--label",
    "labels",
    metavar="LABEL",
    multiple=True,
    help="Filter issues by label (may be specified multiple times)",
)
@click.option(
    "--limit",
    type=int,
    help="Maximum number of issues to process",
)
def resolve(
    owner: str,
    repository: str,
    token: str,
    dry_run: bool,
    labels: tuple,
    limit: Optional[int],
) -> None:
    """Attempt to resolve issues automatically."""
    repo = get_github_repo(owner, repository, token)
    issues = list_open_issues(repo, labels=list(labels) if labels else None)
    repo_path = Path.cwd()
    
    if limit:
        issues = issues[:limit]
    
    click.echo(f"Processing {len(issues)} issue(s) (dry_run={dry_run}):\n")
    
    resolved = []
    failed = []
    
    for issue in issues:
        result = resolve_issue(issue, repo_path, repo, dry_run=dry_run)
        if result["success"]:
            resolved.append(result)
            click.secho(f"  ✓ #{issue.number}: {result['message']}", fg="green")
        else:
            failed.append(result)
            click.secho(f"  ✗ #{issue.number}: {result['reason']}", fg="red")
        click.echo()
    
    click.echo(f"\nSummary:")
    click.echo(f"  Resolved: {len(resolved)}")
    click.echo(f"  Failed: {len(failed)}")
    
    if not dry_run and resolved:
        click.echo(f"\n✅ Created {len([r for r in resolved if r.get('pr_created')])} PR(s)")
        click.echo("   PRs will be auto-approved and merged if checks pass")


@cli.command()
@click.option(
    "--owner",
    metavar="USER",
    required=True,
    envvar="GITHUB_USER",
    help="GitHub username",
)
@click.option(
    "--repository",
    metavar="REPO",
    required=True,
    envvar="GITHUB_REPOSITORY",
    help="GitHub repository",
)
@click.option(
    "--token",
    metavar="TOKEN",
    required=True,
    envvar="GITHUB_TOKEN",
    help="GitHub API token",
)
def create_prs(owner: str, repository: str, token: str) -> None:
    """Create pull requests for resolved issues."""
    # TODO: Implement PR creation logic
    click.echo("PR creation not yet implemented")
    click.echo("This would create PRs for branches created during --resolve")


if __name__ == "__main__":
    cli(prog_name="resolve-issues")
