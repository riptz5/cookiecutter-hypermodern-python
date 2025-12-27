"""Command-line interface for {{cookiecutter.friendly_name}}.

Provides commands for:
- Multi-agent task execution
- System verification
- GENESIS autopoietic cycles
- GCP resource discovery

Examples:
    # Run multi-agent task
    $ {{cookiecutter.project_name}} multi "Research AI trends"
    
    # Verify system setup
    $ {{cookiecutter.project_name}} verify
    
    # Run GENESIS cycle
    $ {{cookiecutter.project_name}} genesis cycle
    
    # Single agent query
    $ {{cookiecutter.project_name}} ask "What is Python?"
"""
import asyncio
import logging
import os
import sys

import click


def setup_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@click.group()
@click.version_option()
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    """{{cookiecutter.friendly_name}} - AI-powered multi-agent system."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    setup_logging(verbose)


@main.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    """Show system information."""
    click.echo("{{cookiecutter.friendly_name}} v{{cookiecutter.version}}")
    click.echo("=" * 40)
    
    # Check available features
    features = []
    {%- if cookiecutter.use_google_adk == 'y' %}
    features.append("Google ADK")
    {%- endif %}
    {%- if cookiecutter.use_langgraph == 'y' %}
    features.append("LangGraph")
    {%- endif %}
    {%- if cookiecutter.use_google_cloud == 'y' %}
    features.append("Google Cloud")
    {%- endif %}
    
    if features:
        click.echo(f"Features: {', '.join(features)}")
    else:
        click.echo("Features: Base configuration")


{%- if cookiecutter.use_google_adk == 'y' %}


@main.command()
@click.argument("prompt")
@click.option("--model", default="gemini-2.0-flash-exp", help="Model to use")
@click.pass_context
def ask(ctx: click.Context, prompt: str, model: str) -> None:
    """Ask a question using the ADK agent."""
    async def _ask():
        from .agents.adk import GoogleADKAgent, ADKConfig
        
        config = ADKConfig(model=model)
        agent = GoogleADKAgent(config)
        
        click.echo(f"Asking: {prompt[:50]}...")
        response = await agent.run(prompt)
        click.echo("\nResponse:")
        click.echo("-" * 40)
        click.echo(response)
    
    asyncio.run(_ask())


@main.command()
@click.argument("task")
@click.option("--workers", "-w", multiple=True, help="Worker types to use")
@click.pass_context
def multi(ctx: click.Context, task: str, workers: tuple) -> None:
    """Run a task using multiple agents in parallel."""
    async def _multi():
        from .agents.factory import AgentFactory, AgentType
        
        factory = AgentFactory()
        
        # Default workers if none specified
        if not workers:
            worker_types = [AgentType.RESEARCH, AgentType.ANALYSIS]
        else:
            worker_types = [AgentType(w) for w in workers]
        
        click.echo(f"Running task with {len(worker_types)} workers...")
        
        # Create workers
        agents = {}
        for wt in worker_types:
            agents[wt.value] = factory.create(f"worker-{wt.value}", wt)
        
        # Run in parallel
        tasks = {
            name: asyncio.create_task(agent.run(task))
            for name, agent in agents.items()
        }
        
        results = {}
        for name, t in tasks.items():
            try:
                results[name] = await t
                click.echo(f"\n[{name.upper()}]")
                click.echo("-" * 40)
                click.echo(results[name][:500] + "..." if len(results[name]) > 500 else results[name])
            except Exception as e:
                click.echo(f"\n[{name.upper()}] Error: {e}")
        
        click.echo(f"\nCompleted {len(results)} worker responses.")
    
    asyncio.run(_multi())
{%- endif %}


{%- if cookiecutter.use_google_adk == 'y' and cookiecutter.use_google_cloud == 'y' %}


@main.group()
@click.pass_context
def genesis(ctx: click.Context) -> None:
    """GENESIS autopoietic system commands."""
    pass


@genesis.command()
@click.option("--task", "-t", default=None, help="Specific task to execute")
@click.pass_context
def cycle(ctx: click.Context, task: str) -> None:
    """Run a single GENESIS cycle."""
    async def _cycle():
        from .genesis import GenesisCore
        
        click.echo("Initializing GENESIS Core...")
        core = GenesisCore()
        
        click.echo("Running cycle...")
        result = await core.run_cycle(task=task)
        
        click.echo("\nCycle Result:")
        click.echo("-" * 40)
        click.echo(f"Cycle ID: {result.cycle_id}")
        click.echo(f"Success: {result.success}")
        click.echo(f"Actions: {len(result.actions_taken)}")
        click.echo(f"Duration: {result.duration_ms:.2f}ms")
        click.echo(f"Evolved: {result.evolved}")
        
        if result.errors:
            click.echo(f"\nErrors ({len(result.errors)}):")
            for err in result.errors[:5]:
                click.echo(f"  - {err}")
        
        if result.actions_taken:
            click.echo(f"\nActions taken:")
            for action in result.actions_taken[:10]:
                click.echo(f"  - {action}")
    
    asyncio.run(_cycle())


@genesis.command()
@click.option("--interval", "-i", default=60, help="Seconds between cycles")
@click.option("--max-cycles", "-m", default=None, type=int, help="Max cycles to run")
@click.pass_context
def run(ctx: click.Context, interval: int, max_cycles: int) -> None:
    """Run GENESIS continuously."""
    async def _run():
        from .genesis import GenesisCore
        
        click.echo("Starting GENESIS in continuous mode...")
        click.echo(f"Interval: {interval}s, Max cycles: {max_cycles or 'unlimited'}")
        click.echo("Press Ctrl+C to stop.\n")
        
        core = GenesisCore()
        
        try:
            await core.run_continuous(
                interval_seconds=interval,
                max_cycles=max_cycles,
            )
        except KeyboardInterrupt:
            click.echo("\nStopping GENESIS...")
        
        status = core.get_status()
        click.echo(f"\nFinal status:")
        click.echo(f"  Cycles completed: {status['cycles_completed']}")
        click.echo(f"  Uptime: {status['uptime_seconds']:.0f}s")
    
    asyncio.run(_run())


@genesis.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show GENESIS system status."""
    async def _status():
        from .genesis import GenesisCore, MemoryModule
        
        click.echo("GENESIS System Status")
        click.echo("=" * 40)
        
        # Try to get memory state
        memory = MemoryModule()
        try:
            state = await memory.get_state()
            click.echo(f"Total cycles: {state.total_cycles}")
            click.echo(f"Success rate: {state.success_rate:.1%}")
            click.echo(f"Agents generated: {state.agents_generated}")
            click.echo(f"Plugins generated: {state.plugins_generated}")
            
            if state.errors_recent:
                click.echo(f"\nRecent errors ({len(state.errors_recent)}):")
                for err in state.errors_recent[:3]:
                    click.echo(f"  - {err[:60]}...")
        except Exception as e:
            click.echo(f"Could not retrieve memory state: {e}")
            click.echo("(Memory may not be initialized yet)")
    
    asyncio.run(_status())


@genesis.command()
@click.pass_context
def evolve(ctx: click.Context) -> None:
    """Force an evolution cycle."""
    async def _evolve():
        from .genesis import GenesisCore
        
        click.echo("Forcing GENESIS evolution...")
        core = GenesisCore()
        
        success = await core.force_evolve()
        
        if success:
            click.echo("Evolution completed successfully!")
        else:
            click.echo("Evolution failed. Check logs for details.")
    
    asyncio.run(_evolve())
{%- endif %}


{%- if cookiecutter.use_google_cloud == 'y' %}


@main.command()
@click.pass_context
def discover(ctx: click.Context) -> None:
    """Discover GCP resources in the project."""
    from .core.gcp_discovery import GCPDiscovery
    
    click.echo("Discovering GCP resources...")
    discovery = GCPDiscovery()
    
    # Discover project
    project = discovery.discover_project()
    click.echo(f"\nProject: {project.project_id}")
    click.echo(f"Region: {project.region}")
    
    # Discover services
    services = discovery.discover_enabled_services()
    enabled = [s for s in services if s.enabled]
    click.echo(f"\nEnabled services: {len(enabled)}")
    for svc in enabled[:10]:
        click.echo(f"  - {svc.name}")
    if len(enabled) > 10:
        click.echo(f"  ... and {len(enabled) - 10} more")
    
    # Discover resources
    resources = discovery.discover_all_service_resources()
    click.echo(f"\nResources by service:")
    for service, data in resources.items():
        count = data.get("count", 0)
        if count > 0:
            click.echo(f"  - {service}: {count}")


@main.command()
@click.pass_context
def verify(ctx: click.Context) -> None:
    """Verify the production setup."""
    click.echo("Verifying production setup...")
    click.echo("=" * 40)
    
    checks = []
    
    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY")
    checks.append(("GOOGLE_API_KEY", "set" if api_key else "missing"))
    
    # Check project
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    checks.append(("GOOGLE_CLOUD_PROJECT", project or "not set"))
    
    # Check imports
    try:
        from google import genai
        checks.append(("google-genai", "installed"))
    except ImportError:
        checks.append(("google-genai", "not installed"))
    
    try:
        from google.cloud import firestore
        checks.append(("google-cloud-firestore", "installed"))
    except ImportError:
        checks.append(("google-cloud-firestore", "not installed"))
    
    try:
        from langgraph.graph import StateGraph
        checks.append(("langgraph", "installed"))
    except ImportError:
        checks.append(("langgraph", "not installed"))
    
    # Print results
    all_ok = True
    for name, status in checks:
        icon = "✓" if status not in ["missing", "not installed", "not set"] else "✗"
        if icon == "✗":
            all_ok = False
        click.echo(f"  {icon} {name}: {status}")
    
    click.echo()
    if all_ok:
        click.echo("All checks passed! System ready for production.")
    else:
        click.echo("Some checks failed. Review configuration.")
        sys.exit(1)
{%- endif %}


if __name__ == "__main__":
    main(prog_name="{{cookiecutter.project_name}}")  # pragma: no cover
