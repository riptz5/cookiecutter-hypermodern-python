"""Example: Agent orchestration in action.

This example demonstrates:
1. Parallel execution of multiple agents
2. Sequential pipeline execution
3. Map-reduce pattern

Run with: python -m examples.orchestration_example
"""
import asyncio
from {{cookiecutter.package_name}}.agents.orchestrator import (
    AgentOrchestrator,
    Task,
    run_parallel,
    run_pipeline,
)


# ============================================================================
# Example Agents (Simple functions that simulate agent work)
# ============================================================================

async def research_agent(topic: str) -> dict:
    """Simulates a research agent."""
    print(f"🔍 Research agent working on: {topic}")
    await asyncio.sleep(1)  # Simulate work
    return {
        "topic": topic,
        "findings": f"Research results for {topic}",
        "sources": 5
    }


async def analyze_agent(data: dict) -> dict:
    """Simulates an analysis agent."""
    print(f"📊 Analysis agent processing: {data.get('topic', 'data')}")
    await asyncio.sleep(1)  # Simulate work
    return {
        "analysis": f"Analysis of {data}",
        "insights": ["insight 1", "insight 2"],
        "confidence": 0.85
    }


async def writer_agent(content: dict) -> str:
    """Simulates a writing agent."""
    print(f"✍️  Writer agent creating content...")
    await asyncio.sleep(1)  # Simulate work
    return f"Article based on: {content}"


async def reviewer_agent(article: str) -> dict:
    """Simulates a review agent."""
    print(f"👀 Reviewer agent checking article...")
    await asyncio.sleep(1)  # Simulate work
    return {
        "article": article,
        "approved": True,
        "suggestions": ["Good work!"]
    }


def summarize_agent(results: list) -> str:
    """Simulates a summarization agent (sync function)."""
    print(f"📝 Summarizer aggregating {len(results)} results...")
    return f"Summary of {len(results)} items: " + ", ".join(str(r) for r in results)


# ============================================================================
# Example 1: Parallel Execution
# ============================================================================

async def example_parallel():
    """Execute multiple agents in parallel."""
    print("\n" + "="*70)
    print("EXAMPLE 1: PARALLEL EXECUTION")
    print("="*70)
    print("Running 3 research agents simultaneously...\n")
    
    orchestrator = AgentOrchestrator()
    
    tasks = [
        Task("research_ai", "Artificial Intelligence", research_agent),
        Task("research_ml", "Machine Learning", research_agent),
        Task("research_nlp", "Natural Language Processing", research_agent),
    ]
    
    import time
    start = time.time()
    results = await orchestrator.execute_parallel(tasks)
    elapsed = time.time() - start
    
    print(f"\n✅ Completed {len(results)} tasks in {elapsed:.2f}s (parallel)")
    print(f"   (Sequential would take ~{len(tasks)}s)\n")
    
    for result in results:
        if result.success:
            print(f"   ✓ {result.task_name}: {result.output}")
        else:
            print(f"   ✗ {result.task_name}: {result.error}")


# ============================================================================
# Example 2: Pipeline Execution
# ============================================================================

async def example_pipeline():
    """Execute agents in a sequential pipeline."""
    print("\n" + "="*70)
    print("EXAMPLE 2: PIPELINE EXECUTION")
    print("="*70)
    print("Running research → analyze → write → review pipeline...\n")
    
    orchestrator = AgentOrchestrator()
    
    tasks = [
        Task("research", None, research_agent),
        Task("analyze", None, analyze_agent),
        Task("write", None, writer_agent),
        Task("review", None, reviewer_agent),
    ]
    
    result = await orchestrator.execute_pipeline(
        tasks,
        initial_input="AI Ethics"
    )
    
    if result.success:
        print(f"\n✅ Pipeline completed successfully!")
        print(f"   Steps: {result.metadata.get('steps')}")
        print(f"   Final output: {result.output}\n")
    else:
        print(f"\n✗ Pipeline failed: {result.error}\n")


# ============================================================================
# Example 3: Map-Reduce Pattern
# ============================================================================

async def example_map_reduce():
    """Execute map-reduce pattern."""
    print("\n" + "="*70)
    print("EXAMPLE 3: MAP-REDUCE PATTERN")
    print("="*70)
    print("Processing 5 topics in parallel, then summarizing...\n")
    
    orchestrator = AgentOrchestrator()
    
    topics = ["AI", "ML", "NLP", "Computer Vision", "Robotics"]
    
    result = await orchestrator.execute_map_reduce(
        data_items=topics,
        map_fn=research_agent,  # Process each topic in parallel
        reduce_fn=summarize_agent,  # Aggregate all results
    )
    
    if result.success:
        print(f"\n✅ Map-Reduce completed!")
        print(f"   Final summary: {result.output}\n")
    else:
        print(f"\n✗ Map-Reduce failed: {result.error}\n")


# ============================================================================
# Example 4: Quick Helpers
# ============================================================================

async def example_quick_helpers():
    """Use convenience functions for quick orchestration."""
    print("\n" + "="*70)
    print("EXAMPLE 4: QUICK HELPER FUNCTIONS")
    print("="*70)
    
    # Quick parallel execution
    print("\n1. Quick parallel execution:")
    results = await run_parallel(
        research_agent,
        research_agent,
        research_agent,
        inputs=["Topic A", "Topic B", "Topic C"]
    )
    print(f"   ✓ Executed {len(results)} agents in parallel\n")
    
    # Quick pipeline execution
    print("2. Quick pipeline execution:")
    result = await run_pipeline(
        research_agent,
        analyze_agent,
        writer_agent,
        initial_input="Quick Test"
    )
    print(f"   ✓ Pipeline result: {result.success}\n")


# ============================================================================
# Example 5: Real-World Scenario
# ============================================================================

async def example_real_world():
    """Realistic multi-agent scenario."""
    print("\n" + "="*70)
    print("EXAMPLE 5: REAL-WORLD SCENARIO")
    print("="*70)
    print("Creating a research report with multiple specialized agents...\n")
    
    orchestrator = AgentOrchestrator()
    
    # Step 1: Research multiple aspects in parallel
    print("Step 1: Parallel research on different aspects...")
    research_tasks = [
        Task("research_history", "History of AI", research_agent),
        Task("research_current", "Current AI State", research_agent),
        Task("research_future", "Future of AI", research_agent),
    ]
    research_results = await orchestrator.execute_parallel(research_tasks)
    
    # Step 2: Analyze each research result in parallel
    print("\nStep 2: Parallel analysis of research results...")
    analysis_tasks = [
        Task(f"analyze_{r.task_name}", r.output, analyze_agent)
        for r in research_results if r.success
    ]
    analysis_results = await orchestrator.execute_parallel(analysis_tasks)
    
    # Step 3: Aggregate and write
    print("\nStep 3: Writing comprehensive report...")
    all_analyses = [r.output for r in analysis_results if r.success]
    write_result = await writer_agent({"analyses": all_analyses})
    
    # Step 4: Review
    print("\nStep 4: Final review...")
    final_result = await reviewer_agent(write_result)
    
    print(f"\n✅ Complete workflow finished!")
    print(f"   Research tasks: {len(research_results)}")
    print(f"   Analysis tasks: {len(analysis_results)}")
    print(f"   Final approval: {final_result.get('approved')}\n")


# ============================================================================
# Main
# ============================================================================

async def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("AGENT ORCHESTRATION EXAMPLES")
    print("="*70)
    
    await example_parallel()
    await example_pipeline()
    await example_map_reduce()
    await example_quick_helpers()
    await example_real_world()
    
    print("\n" + "="*70)
    print("ALL EXAMPLES COMPLETED! 🎉")
    print("="*70)
    print("\nKey Takeaways:")
    print("  • Parallel execution: Run multiple agents simultaneously")
    print("  • Pipeline execution: Chain agents sequentially")
    print("  • Map-Reduce: Process data in parallel, aggregate results")
    print("  • Mix and match: Combine patterns for complex workflows")
    print()


if __name__ == "__main__":
    asyncio.run(main())
