"""Command-line interface for {{cookiecutter.friendly_name}}.

Provides commands for:
- Multi-agent task execution
- System verification
- Autopoietic cycle management
- Individual agent invocation

Examples:
    # Run multi-agent task
    $ {{cookiecutter.project_name}} --multi-agent "Research AI trends"
    
    # Verify system setup
    $ {{cookiecutter.project_name}} --verify
    
    # Run autopoietic cycle
    $ {{cookiecutter.project_name}} --autopoiesis
    
    # Single agent query
    $ {{cookiecutter.project_name}} --agent research "What is Python?"
"""
import asyncio
import os
import sys
from typing import Optional

import click

{%- if cookiecutter.use_google_adk == 'y' %}


def _run_async(coro):
    """Run async coroutine in sync context."""
    try:
        return asyncio.run(coro)
    except RuntimeError:
        # Already in async context
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)


async def _verify_system():
    """Verify all production systems."""
    click.echo("=" * 60)
    click.echo("SYSTEM VERIFICATION")
    click.echo("=" * 60)
    
    checks = []
    
    # Check 1: API Key
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        checks.append(("API Key", True, f"{api_key[:10]}..."))
    else:
        checks.append(("API Key", False, "GOOGLE_API_KEY not set"))
    
    # Check 2: Gemini Connection
    try:
        from .agents.adk import GoogleADKAgent, ADKConfig
        agent = GoogleADKAgent(ADKConfig())
        response = await agent.run("Say 'OK' if you can hear me")
        if response:
            checks.append(("Gemini API", True, f"Response: {response[:30]}..."))
        else:
            checks.append(("Gemini API", False, "Empty response"))
    except ImportError as e:
        checks.append(("Gemini API", False, f"Import error: {e}"))
    except Exception as e:
        checks.append(("Gemini API", False, f"Error: {e}"))
    
    # Check 3: Multi-agent System
    try:
        from .agents.orchestrator import ProductionOrchestrator
        orchestrator = ProductionOrchestrator()
        result = await orchestrator.verify_system()
        if result["success"]:
            checks.append(("Multi-Agent", True, "All checks passed"))
        else:
            failed = [k for k, v in result["checks"].items() if not v]
            checks.append(("Multi-Agent", False, f"Failed: {failed}"))
    except Exception as e:
        checks.append(("Multi-Agent", False, f"Error: {e}"))
    
    # Check 4: Memory Store
    try:
        from .cloud.memory_store import get_memory_store
        store = get_memory_store()
        stats = store.get_stats()
        if stats["using_firestore"]:
            checks.append(("Memory (Firestore)", True, f"Project: {stats['project_id']}"))
        else:
            checks.append(("Memory (In-Memory)", True, "Firestore not configured"))
    except Exception as e:
        checks.append(("Memory", False, f"Error: {e}"))
    
    # Print results
    click.echo("")
    all_passed = True
    for name, passed, detail in checks:
        status = click.style("[PASS]", fg="green") if passed else click.style("[FAIL]", fg="red")
        click.echo(f"{status} {name}: {detail}")
        if not passed:
            all_passed = False
    
    click.echo("")
    if all_passed:
        click.echo(click.style("All systems operational!", fg="green", bold=True))
    else:
        click.echo(click.style("Some checks failed. See above for details.", fg="yellow"))
    
    return all_passed


async def _run_multi_agent(task: str):
    """Run multi-agent task."""
    from .agents.orchestrator import ProductionOrchestrator
    
    click.echo(click.style(f"\nExecuting multi-agent task...", fg="cyan"))
    click.echo(f"Task: {task}\n")
    
    orchestrator = ProductionOrchestrator()
    result = await orchestrator.execute_multi_agent(task)
    
    if result["success"]:
        click.echo(click.style("SUCCESS", fg="green", bold=True))
        click.echo(f"\nWorkers used: {', '.join(result['workers_used'])}")
        click.echo(f"Execution time: {result['execution_time']:.2f}s")
        click.echo(f"\n{'='*60}")
        click.echo("OUTPUT:")
        click.echo("="*60)
        click.echo(result["output"])
    else:
        click.echo(click.style("FAILED", fg="red", bold=True))
        click.echo(f"Error: {result.get('error', 'Unknown error')}")
    
    return result


async def _run_single_agent(agent_type: str, query: str):
    """Run a single agent."""
    from .agents.adk.workers import create_worker
    
    click.echo(click.style(f"\nRunning {agent_type} agent...", fg="cyan"))
    click.echo(f"Query: {query}\n")
    
    worker = create_worker(agent_type)
    result = await worker.run(query)
    
    if result.success:
        click.echo(click.style("SUCCESS", fg="green", bold=True))
        click.echo(f"Duration: {result.duration_ms:.0f}ms\n")
        click.echo("="*60)
        click.echo("OUTPUT:")
        click.echo("="*60)
        click.echo(result.output)
    else:
        click.echo(click.style("FAILED", fg="red", bold=True))
        click.echo(f"Error: {result.error}")
    
    return result


async def _run_autopoiesis(dry_run: bool = True):
    """Run autopoietic cycle."""
    from .autopoiesis import run_cycle
    
    click.echo(click.style("\nStarting autopoietic cycle...", fg="cyan"))
    if dry_run:
        click.echo(click.style("(DRY RUN - no changes will be made)", fg="yellow"))
    click.echo("")
    
    result = await run_cycle(dry_run=dry_run)
    
    if result.success:
        click.echo(click.style("CYCLE COMPLETED", fg="green", bold=True))
        click.echo(f"\nCycle ID: {result.cycle_id}")
        
        if result.cognition:
            click.echo(f"Improvements found: {len(result.cognition.improvements)}")
            for i, imp in enumerate(result.cognition.improvements, 1):
                click.echo(f"  {i}. {imp.get('suggestion', 'N/A')}")
        
        if result.action:
            click.echo(f"\nChanges made: {len(result.action.changes_made)}")
            click.echo(f"Tests passed: {result.action.tests_passed}")
            click.echo(f"Deployed: {result.action.deployed}")
    else:
        click.echo(click.style("CYCLE FAILED", fg="red", bold=True))
        click.echo(f"Error: {result.error}")
    
    return result


async def _show_status():
    """Show system status."""
    from .core.config import get_config
    from .cloud.memory_store import get_memory_store
    
    config = get_config()
    memory = get_memory_store()
    
    click.echo("=" * 60)
    click.echo("SYSTEM STATUS")
    click.echo("=" * 60)
    
    # Configuration
    click.echo("\n[Configuration]")
    click.echo(f"  Gemini Model: {config.gemini.model}")
    click.echo(f"  API Key: {'Set' if config.gemini.api_key else 'NOT SET'}")
    click.echo(f"  GCP Project: {config.gcp.project_id or 'NOT SET'}")
    click.echo(f"  Debug Mode: {config.debug}")
    click.echo(f"  Dry Run: {config.dry_run}")
    
    # Agent settings
    click.echo("\n[Agent Settings]")
    click.echo(f"  Max Concurrent: {config.agent.max_concurrent}")
    click.echo(f"  Memory Enabled: {config.agent.enable_memory}")
    click.echo(f"  Parallel Enabled: {config.agent.enable_parallel}")
    
    # Autopoiesis settings
    click.echo("\n[Autopoiesis]")
    click.echo(f"  Self-Improve: {config.autopoiesis.enable_self_improve}")
    click.echo(f"  Self-Deploy: {config.autopoiesis.enable_self_deploy}")
    
    # Memory status
    stats = memory.get_stats()
    click.echo("\n[Memory Store]")
    click.echo(f"  Using Firestore: {stats['using_firestore']}")
    click.echo(f"  Cache Sizes: {stats['cache_sizes']}")
{%- endif %}


@click.command()
{%- if cookiecutter.use_google_adk == 'y' %}
@click.option(
    "--multi-agent", "-m",
    type=str,
    help="Execute task with multi-agent system"
)
@click.option(
    "--agent", "-a",
    type=(str, str),
    help="Run single agent: --agent TYPE QUERY (types: research, analysis, writer, code)"
)
@click.option(
    "--verify", "-v",
    is_flag=True,
    help="Verify production system setup"
)
@click.option(
    "--autopoiesis",
    is_flag=True,
    help="Run one autopoietic cycle"
)
@click.option(
    "--no-dry-run",
    is_flag=True,
    help="Execute autopoiesis changes (CAUTION: modifies code)"
)
@click.option(
    "--status", "-s",
    is_flag=True,
    help="Show system status"
)
{%- endif %}
@click.version_option()
{%- if cookiecutter.use_google_adk == 'y' %}
def main(
    multi_agent: Optional[str] = None,
    agent: Optional[tuple] = None,
    verify: bool = False,
    autopoiesis: bool = False,
    no_dry_run: bool = False,
    status: bool = False,
) -> None:
    """{{cookiecutter.friendly_name}} - Multi-Agent Orchestration System.
    
    A production-ready multi-agent system using Google ADK and LangGraph.
    
    \b
    Examples:
        # Verify system setup
        {{cookiecutter.project_name}} --verify
        
        # Run multi-agent task
        {{cookiecutter.project_name}} -m "Research and summarize AI trends"
        
        # Run single agent
        {{cookiecutter.project_name}} --agent research "What is quantum computing?"
        
        # Run autopoietic cycle (dry run)
        {{cookiecutter.project_name}} --autopoiesis
        
        # Show system status
        {{cookiecutter.project_name}} --status
    """
    try:
        if verify:
            _run_async(_verify_system())
        elif multi_agent:
            _run_async(_run_multi_agent(multi_agent))
        elif agent:
            agent_type, query = agent
            if agent_type not in ["research", "analysis", "writer", "code"]:
                click.echo(click.style(
                    f"Invalid agent type: {agent_type}. Valid: research, analysis, writer, code",
                    fg="red"
                ))
                sys.exit(1)
            _run_async(_run_single_agent(agent_type, query))
        elif autopoiesis:
            dry_run = not no_dry_run
            _run_async(_run_autopoiesis(dry_run=dry_run))
        elif status:
            _run_async(_show_status())
        else:
            # Default: show help
            ctx = click.get_current_context()
            click.echo(ctx.get_help())
            
    except KeyboardInterrupt:
        click.echo("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        click.echo(click.style(f"\nError: {e}", fg="red"))
        if os.getenv("DEBUG"):
            import traceback
            traceback.print_exc()
        sys.exit(1)
{%- else %}
def main() -> None:
    """{{cookiecutter.friendly_name}}."""
    click.echo("{{cookiecutter.friendly_name}}")
    click.echo("Enable use_google_adk for multi-agent features.")
{%- endif %}


if __name__ == "__main__":
    main(prog_name="{{cookiecutter.project_name}}")  # pragma: no cover
