"""Nox sessions."""
from pathlib import Path
import shutil

import nox
from nox.sessions import Session

nox.options.sessions = ["docs"]
owner, repository = "cjolowicz", "cookiecutter-hypermodern-python"
labels = "cookiecutter", "documentation"
bump_paths = "README.md", "docs/guide.rst", "docs/index.rst", "docs/quickstart.md"


@nox.session(name="prepare-release")
def prepare_release(session: Session) -> None:
    """Prepare a GitHub release."""
    args = [
        f"--owner={owner}",
        f"--repository={repository}",
        *[f"--bump={path}" for path in bump_paths],
        *[f"--label={label}" for label in labels],
        *session.posargs,
    ]
    session.install("click", "github3.py")
    session.run("python", "tools/prepare-github-release.py", *args, external=True)


@nox.session(name="publish-release")
def publish_release(session: Session) -> None:
    """Publish a GitHub release."""
    args = [f"--owner={owner}", f"--repository={repository}", *session.posargs]
    session.install("click", "github3.py")
    session.run("python", "tools/publish-github-release.py", *args, external=True)


nox.options.sessions = ["linkcheck"]


@nox.session
def docs(session: Session) -> None:
    """Build the documentation."""
    args = session.posargs or ["-W", "-n", "docs", "docs/_build"]

    if session.interactive and not session.posargs:
        args = ["-a", "--watch=docs/_static", "--open-browser", *args]

    builddir = Path("docs", "_build")
    if builddir.exists():
        shutil.rmtree(builddir)

    session.install("-r", "docs/requirements.txt")

    if session.interactive:
        session.run("sphinx-autobuild", *args)
    else:
        session.run("sphinx-build", *args)


@nox.session
def linkcheck(session: Session) -> None:
    """Build the documentation."""
    args = session.posargs or ["-b", "linkcheck", "-W", "--keep-going", "docs", "docs/_build"]

    builddir = Path("docs", "_build")
    if builddir.exists():
        shutil.rmtree(builddir)

    session.install("-r", "docs/requirements.txt")

    session.run("sphinx-build", *args)


@nox.session(name="dependencies-table")
def dependencies_table(session: Session) -> None:
    """Print the dependencies table."""
    session.install("tomli")
    session.run("python", "tools/dependencies-table.py", external=True)


@nox.session(name="resolve-issues")
def resolve_issues(session: Session) -> None:
    """Automatically resolve GitHub issues using AI agent."""
    args = [
        f"--owner={owner}",
        f"--repository={repository}",
        *session.posargs,
    ]
    session.install("click", "github3.py")
    session.run("python", "tools/resolve-issues.py", *args, external=True)


@nox.session(name="generate-innovation-issues")
def generate_innovation_issues(session: Session) -> None:
    """Generate 120 innovation issues for the repository."""
    args = ["create-issues", f"--owner={owner}", f"--repository={repository}", *session.posargs]
    session.install("click", "github3.py")
    session.run("python", "tools/generate_innovation_issues.py", *args, external=True)


@nox.session(name="list-innovation-ideas")
def list_innovation_ideas(session: Session) -> None:
    """List all 120 innovation ideas."""
    session.install("click")
    session.run("python", "tools/generate_innovation_issues.py", "list-ideas", external=True)


@nox.session(name="export-innovation-json")
def export_innovation_json(session: Session) -> None:
    """Export innovation ideas as JSON."""
    args = ["export-json", *session.posargs]
    session.install("click")
    session.run("python", "tools/generate_innovation_issues.py", *args, external=True)


@nox.session(name="orchestrate-agents")
def orchestrate_agents(session: Session) -> None:
    """Orchestrate sub-agents for parallel issue resolution."""
    args = ["orchestrate-loops", *session.posargs]
    session.install("click")
    session.run("python", "tools/agent_orchestrator.py", *args, external=True)
