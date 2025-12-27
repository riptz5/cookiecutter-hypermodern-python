{%- if cookiecutter.use_google_adk == 'y' and cookiecutter.use_google_cloud == 'y' %}
"""Example: Run GENESIS autopoietic system.

This script demonstrates the GENESIS autopoietic system that:
1. PERCEIVES its GCP environment automatically
2. THINKS about what actions to take using Gemini
3. ACTS by generating code and executing actions
4. REMEMBERS its state in Firestore
5. EVOLVES by improving its own code

Setup:
1. Set GOOGLE_API_KEY environment variable
2. Optionally set GOOGLE_CLOUD_PROJECT
3. Authenticate: gcloud auth application-default login
4. Run this script

GENESIS will autonomously discover your GCP resources and
propose actions to improve itself.
"""
import asyncio
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger("genesis_example")


async def run_single_cycle():
    """Run a single GENESIS cycle."""
    from {{cookiecutter.package_name}}.genesis import GenesisCore
    
    print("\n" + "=" * 80)
    print("GENESIS - SINGLE CYCLE EXECUTION")
    print("=" * 80)
    
    # Initialize GENESIS
    logger.info("Initializing GENESIS Core...")
    genesis = GenesisCore(
        evolution_threshold=10,  # Evolve every 10 cycles
        auto_evolve=True,
    )
    
    # Run a cycle
    logger.info("Running cycle...")
    result = await genesis.run_cycle()
    
    # Display results
    print("\n" + "-" * 40)
    print("CYCLE RESULT")
    print("-" * 40)
    print(f"  Cycle ID: {result.cycle_id}")
    print(f"  Success: {result.success}")
    print(f"  Duration: {result.duration_ms:.2f}ms")
    print(f"  Context Hash: {result.context_hash}")
    print(f"  Actions: {len(result.actions_taken)}")
    print(f"  Evolved: {result.evolved}")
    
    if result.actions_taken:
        print("\n  Actions taken:")
        for action in result.actions_taken:
            print(f"    - {action}")
    
    if result.errors:
        print(f"\n  Errors ({len(result.errors)}):")
        for error in result.errors[:5]:
            print(f"    - {error}")
    
    if result.plan_summary:
        print(f"\n  Plan summary: {result.plan_summary[:200]}...")
    
    # Show system status
    status = genesis.get_status()
    print("\n" + "-" * 40)
    print("SYSTEM STATUS")
    print("-" * 40)
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    return result


async def run_with_task(task: str):
    """Run GENESIS with a specific task."""
    from {{cookiecutter.package_name}}.genesis import GenesisCore
    
    print("\n" + "=" * 80)
    print(f"GENESIS - TASK: {task[:50]}...")
    print("=" * 80)
    
    genesis = GenesisCore()
    result = await genesis.run_cycle(task=task)
    
    print(f"\nResult: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Actions: {result.actions_taken}")
    
    return result


async def run_continuous(cycles: int = 3, interval: int = 30):
    """Run GENESIS continuously for N cycles."""
    from {{cookiecutter.package_name}}.genesis import GenesisCore
    
    print("\n" + "=" * 80)
    print(f"GENESIS - CONTINUOUS MODE ({cycles} cycles)")
    print("=" * 80)
    
    genesis = GenesisCore(evolution_threshold=2)  # Lower for demo
    
    try:
        await genesis.run_continuous(
            interval_seconds=interval,
            max_cycles=cycles,
        )
    except KeyboardInterrupt:
        print("\nStopped by user.")
    
    status = genesis.get_status()
    print(f"\nCompleted {status['cycles_completed']} cycles")
    
    return status


async def demo_modules():
    """Demonstrate individual GENESIS modules."""
    print("\n" + "=" * 80)
    print("GENESIS MODULE DEMO")
    print("=" * 80)
    
    # 1. Perceive Module
    print("\n1. PERCEIVE MODULE")
    print("-" * 40)
    
    from {{cookiecutter.package_name}}.genesis.perceive import PerceiveModule
    
    perceive = PerceiveModule()
    context = await perceive.scan()
    
    print(f"  Project: {context.project_id}")
    print(f"  Region: {context.region}")
    print(f"  Services: {len(context.services)}")
    print(f"  Resources: {len(context.resources)}")
    print(f"  Changes: {len(context.changes)}")
    
    # 2. Think Module (requires GOOGLE_API_KEY)
    print("\n2. THINK MODULE")
    print("-" * 40)
    
    if os.getenv("GOOGLE_API_KEY"):
        from {{cookiecutter.package_name}}.genesis.think import ThinkModule
        
        think = ThinkModule()
        
        # Test JSON extraction
        test_json = '{"reasoning": "test", "actions": []}'
        extracted = think._extract_json(test_json)
        print(f"  JSON extraction: {'OK' if extracted else 'FAILED'}")
        
        # Test syntax validation
        try:
            think._validate_syntax("def test(): pass")
            print("  Syntax validation: OK")
        except SyntaxError:
            print("  Syntax validation: FAILED")
    else:
        print("  Skipped (GOOGLE_API_KEY not set)")
    
    # 3. Memory Module
    print("\n3. MEMORY MODULE")
    print("-" * 40)
    
    from {{cookiecutter.package_name}}.genesis.memory import MemoryModule
    
    memory = MemoryModule()
    memory._use_local = True  # Force local for demo
    
    state = await memory.get_state()
    print(f"  Total cycles: {state.total_cycles}")
    print(f"  Success rate: {state.success_rate:.1%}")
    print(f"  Using local cache: {memory._use_local}")
    
    print("\nAll modules functional!")


async def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("GENESIS AUTOPOIETIC SYSTEM - EXAMPLE")
    print("=" * 80)
    
    # Check prerequisites
    api_key = os.getenv("GOOGLE_API_KEY")
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    
    print("\nPrerequisites:")
    print(f"  GOOGLE_API_KEY: {'SET' if api_key else 'NOT SET'}")
    print(f"  GOOGLE_CLOUD_PROJECT: {project or 'NOT SET'}")
    
    if not api_key:
        print("\n⚠️  GOOGLE_API_KEY not set!")
        print("Set it with: export GOOGLE_API_KEY=your_key")
        print("\nRunning in demo mode (modules only)...\n")
        await demo_modules()
        return
    
    # Menu
    print("\nOptions:")
    print("  1. Run single cycle")
    print("  2. Run with specific task")
    print("  3. Run continuous (3 cycles)")
    print("  4. Demo individual modules")
    print("  5. Exit")
    
    choice = input("\nSelect option (1-5): ").strip()
    
    if choice == "1":
        await run_single_cycle()
    elif choice == "2":
        task = input("Enter task: ").strip()
        if task:
            await run_with_task(task)
    elif choice == "3":
        await run_continuous(cycles=3, interval=10)
    elif choice == "4":
        await demo_modules()
    elif choice == "5":
        print("Goodbye!")
        return
    else:
        print("Invalid option. Running single cycle...")
        await run_single_cycle()
    
    print("\n✅ Example complete!")


if __name__ == "__main__":
    asyncio.run(main())
{%- endif %}
