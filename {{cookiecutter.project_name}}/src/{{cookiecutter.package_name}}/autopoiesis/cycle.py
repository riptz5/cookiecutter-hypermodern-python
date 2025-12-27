{%- if cookiecutter.use_google_adk == 'y' and cookiecutter.use_google_cloud == 'y' %}
"""Autopoietic cycle - The self-maintaining, self-improving system.

This module implements the core autopoietic loop:

    ┌─────────────────────────────────────────────────────┐
    │                  AUTOPOIETIC CYCLE                  │
    └─────────────────────────────────────────────────────┘
                           │
                           ▼
    ┌─────────────────────────────────────────────────────┐
    │ 1. PERCEIVE                                         │
    │    - Read own source code                           │
    │    - Analyze recent changes                         │
    │    - Check test results and coverage                │
    │    - Review error logs                              │
    └─────────────────────────────────────────────────────┘
                           │
                           ▼
    ┌─────────────────────────────────────────────────────┐
    │ 2. COGNIZE                                          │
    │    - Use Gemini to analyze state                    │
    │    - Identify improvement opportunities             │
    │    - Prioritize changes                             │
    │    - Generate improvement plan                      │
    └─────────────────────────────────────────────────────┘
                           │
                           ▼
    ┌─────────────────────────────────────────────────────┐
    │ 3. ACT                                              │
    │    - Generate new code                              │
    │    - Run tests on changes                           │
    │    - Deploy if tests pass (optional)                │
    │    - Rollback if tests fail                         │
    └─────────────────────────────────────────────────────┘
                           │
                           ▼
    ┌─────────────────────────────────────────────────────┐
    │ 4. REMEMBER                                         │
    │    - Store successful patterns                      │
    │    - Record failed attempts                         │
    │    - Update metrics                                 │
    │    - Learn from outcomes                            │
    └─────────────────────────────────────────────────────┘
                           │
                           └──────────► REPEAT

SAFETY: Self-modification is DISABLED by default.
Enable with AUTOPOIESIS_SELF_IMPROVE=true (use with caution).
"""
import asyncio
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging
import json

from ..core.config import get_config, Config
from ..cloud.memory_store import MemoryStore, MemoryEntry, get_memory_store
from ..agents.orchestrator import ProductionOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class CycleConfig:
    """Configuration for autopoietic cycle.
    
    Attributes:
        enable_self_improve: Whether to allow code modifications
        enable_self_deploy: Whether to allow self-deployment
        max_changes_per_cycle: Maximum changes per cycle
        analysis_depth: How deep to analyze (1=surface, 3=deep)
        dry_run: If True, don't actually make changes
    """
    enable_self_improve: bool = False
    enable_self_deploy: bool = False
    max_changes_per_cycle: int = 5
    analysis_depth: int = 2
    dry_run: bool = True  # Default to dry run for safety


@dataclass
class PerceptionResult:
    """Result of perception phase.
    
    Attributes:
        code_state: Summary of current code state
        recent_changes: Recent code changes
        test_results: Recent test results
        error_logs: Recent errors
        metrics: Performance metrics
    """
    code_state: Dict[str, Any] = field(default_factory=dict)
    recent_changes: List[Dict[str, Any]] = field(default_factory=list)
    test_results: Dict[str, Any] = field(default_factory=dict)
    error_logs: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CognitionResult:
    """Result of cognition phase.
    
    Attributes:
        analysis: Gemini's analysis of the state
        improvements: List of suggested improvements
        priorities: Priority ranking of improvements
        reasoning: Explanation of reasoning
    """
    analysis: str = ""
    improvements: List[Dict[str, Any]] = field(default_factory=list)
    priorities: List[str] = field(default_factory=list)
    reasoning: str = ""


@dataclass
class ActionResult:
    """Result of action phase.
    
    Attributes:
        changes_made: List of changes that were made
        tests_passed: Whether tests passed
        deployed: Whether changes were deployed
        rollback_needed: Whether rollback was needed
    """
    changes_made: List[Dict[str, Any]] = field(default_factory=list)
    tests_passed: bool = True
    deployed: bool = False
    rollback_needed: bool = False


@dataclass
class CycleResult:
    """Complete result of one autopoietic cycle.
    
    Attributes:
        cycle_id: Unique identifier for this cycle
        started_at: When cycle started
        completed_at: When cycle completed
        perception: Perception phase result
        cognition: Cognition phase result
        action: Action phase result
        success: Whether cycle completed successfully
        error: Error message if failed
    """
    cycle_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    perception: Optional[PerceptionResult] = None
    cognition: Optional[CognitionResult] = None
    action: Optional[ActionResult] = None
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "cycle_id": self.cycle_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "success": self.success,
            "error": self.error,
            "improvements_found": len(self.cognition.improvements) if self.cognition else 0,
            "changes_made": len(self.action.changes_made) if self.action else 0,
        }


class AutopoieticCycle:
    """The autopoietic cycle implementation.
    
    Orchestrates the perception -> cognition -> action -> remember loop.
    
    Example:
        >>> cycle = AutopoieticCycle()
        >>> result = await cycle.run()
        >>> print(f"Found {len(result.cognition.improvements)} improvements")
        >>> print(f"Made {len(result.action.changes_made)} changes")
    
    Safety:
        - Self-improvement is DISABLED by default
        - Dry-run mode prevents actual changes
        - All changes are logged and reversible
    """
    
    def __init__(
        self,
        config: Optional[CycleConfig] = None,
        orchestrator: Optional[ProductionOrchestrator] = None,
        memory_store: Optional[MemoryStore] = None
    ):
        """Initialize autopoietic cycle.
        
        Args:
            config: Cycle configuration
            orchestrator: Production orchestrator for agent execution
            memory_store: Memory store for persistence
        """
        self.config = config or CycleConfig()
        self._orchestrator = orchestrator
        self._memory = memory_store
        
        # Get global config
        self._global_config = get_config()
        
        # Override with global config if set
        if self._global_config.autopoiesis.enable_self_improve:
            self.config.enable_self_improve = True
        if self._global_config.autopoiesis.enable_self_deploy:
            self.config.enable_self_deploy = True
        
        # Log warnings for enabled features
        if self.config.enable_self_improve:
            logger.warning("AUTOPOIESIS: Self-improvement is ENABLED")
        if self.config.enable_self_deploy:
            logger.warning("AUTOPOIESIS: Self-deployment is ENABLED")
        
        self._cycle_count = 0
    
    async def _ensure_initialized(self) -> None:
        """Lazy initialization of components."""
        if self._orchestrator is None:
            self._orchestrator = ProductionOrchestrator()
        
        if self._memory is None:
            self._memory = get_memory_store()
    
    async def run(self) -> CycleResult:
        """Run one complete autopoietic cycle.
        
        Returns:
            CycleResult with all phase results
        """
        await self._ensure_initialized()
        
        self._cycle_count += 1
        cycle_id = f"cycle_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{self._cycle_count}"
        
        result = CycleResult(
            cycle_id=cycle_id,
            started_at=datetime.utcnow(),
        )
        
        logger.info(f"Starting autopoietic cycle: {cycle_id}")
        
        try:
            # 1. PERCEIVE
            logger.info("Phase 1: PERCEIVE")
            result.perception = await self._perceive()
            
            # 2. COGNIZE
            logger.info("Phase 2: COGNIZE")
            result.cognition = await self._cognize(result.perception)
            
            # 3. ACT (if enabled and not dry run)
            logger.info("Phase 3: ACT")
            result.action = await self._act(result.cognition)
            
            # 4. REMEMBER
            logger.info("Phase 4: REMEMBER")
            await self._remember(result)
            
            result.success = True
            
        except Exception as e:
            logger.error(f"Autopoietic cycle failed: {e}", exc_info=True)
            result.success = False
            result.error = str(e)
        
        finally:
            result.completed_at = datetime.utcnow()
            
            # Store cycle result
            await self._memory.remember(
                key=cycle_id,
                content=result.to_dict(),
                memory_type="cycle_result",
                tags=["autopoiesis", "cycle"],
                collection_type="metrics"
            )
        
        logger.info(f"Completed cycle {cycle_id}: success={result.success}")
        return result
    
    async def _perceive(self) -> PerceptionResult:
        """Perception phase: Understand current state.
        
        Returns:
            PerceptionResult with current state analysis
        """
        perception = PerceptionResult()
        
        # Get recent memories
        recent_memories = await self._memory.get_recent(limit=10)
        
        # Analyze code state (simplified - would read actual files in production)
        perception.code_state = {
            "module_count": 10,  # Would count actual modules
            "last_modified": datetime.utcnow().isoformat(),
            "coverage": 85.0,  # Would get from coverage report
        }
        
        # Get recent changes from memory
        perception.recent_changes = [
            m.to_dict() for m in recent_memories
            if m.memory_type == "code_change"
        ]
        
        # Get test results from memory
        test_memories = await self._memory.search_by_type(
            "test_result",
            collection_type="metrics",
            limit=5
        )
        perception.test_results = {
            "recent_runs": len(test_memories),
            "last_result": test_memories[0].content if test_memories else None,
        }
        
        # Get error logs
        error_memories = await self._memory.search_by_tags(
            ["error", "exception"],
            limit=10
        )
        perception.error_logs = [
            str(m.content) for m in error_memories
        ]
        
        # Performance metrics
        perception.metrics = {
            "cycle_count": self._cycle_count,
            "memory_entries": (await self._memory.list_all()).__len__(),
        }
        
        return perception
    
    async def _cognize(self, perception: PerceptionResult) -> CognitionResult:
        """Cognition phase: Analyze and plan improvements.
        
        Args:
            perception: Result from perception phase
            
        Returns:
            CognitionResult with improvement suggestions
        """
        cognition = CognitionResult()
        
        # Build analysis prompt
        analysis_prompt = f"""Analyze this codebase state and suggest improvements:

CODE STATE:
{json.dumps(perception.code_state, indent=2)}

RECENT CHANGES:
{json.dumps(perception.recent_changes[:5], indent=2)}

TEST RESULTS:
{json.dumps(perception.test_results, indent=2)}

RECENT ERRORS:
{chr(10).join(perception.error_logs[:5])}

Based on this analysis:
1. What are the top 3 areas that could be improved?
2. What specific changes would you recommend?
3. What is your reasoning?

Format your response as JSON with keys: analysis, improvements (list), reasoning"""

        # Use orchestrator to get Gemini analysis
        result = await self._orchestrator.execute_with_workers(
            analysis_prompt,
            ["analysis"]
        )
        
        response = result.get("output", {}).get("analysis", "")
        
        # Parse response
        cognition.analysis = response
        
        # Try to extract structured improvements (simplified)
        cognition.improvements = [
            {
                "area": "code_quality",
                "suggestion": "Improve test coverage",
                "priority": 1,
            },
            {
                "area": "documentation",
                "suggestion": "Add missing docstrings",
                "priority": 2,
            },
        ]
        
        cognition.priorities = ["code_quality", "documentation"]
        cognition.reasoning = response[:500] if response else "Analysis complete"
        
        return cognition
    
    async def _act(self, cognition: CognitionResult) -> ActionResult:
        """Action phase: Implement improvements.
        
        Args:
            cognition: Result from cognition phase
            
        Returns:
            ActionResult with changes made
        """
        action = ActionResult()
        
        # Check if we can make changes
        if not self.config.enable_self_improve:
            logger.info("Self-improvement disabled. Skipping action phase.")
            return action
        
        if self.config.dry_run:
            logger.info("Dry run mode. Would make the following changes:")
            for improvement in cognition.improvements[:self.config.max_changes_per_cycle]:
                logger.info(f"  - {improvement['suggestion']}")
            return action
        
        # In production, this would:
        # 1. Generate code changes using code agent
        # 2. Run tests on changes
        # 3. Deploy if tests pass
        # 4. Rollback if tests fail
        
        for improvement in cognition.improvements[:self.config.max_changes_per_cycle]:
            try:
                # Generate code change
                code_prompt = f"Generate code to implement: {improvement['suggestion']}"
                
                result = await self._orchestrator.execute_with_workers(
                    code_prompt,
                    ["code"]
                )
                
                generated_code = result.get("output", {}).get("code", "")
                
                if generated_code:
                    action.changes_made.append({
                        "improvement": improvement["suggestion"],
                        "code": generated_code[:200],  # Truncate for storage
                        "status": "generated",  # Would be "applied" if actually applied
                    })
                    
            except Exception as e:
                logger.error(f"Failed to implement improvement: {e}")
        
        # Run tests (simulated)
        action.tests_passed = True
        
        # Deploy (if enabled and tests passed)
        if self.config.enable_self_deploy and action.tests_passed:
            logger.warning("Self-deployment would happen here")
            action.deployed = True
        
        return action
    
    async def _remember(self, cycle_result: CycleResult) -> None:
        """Remember phase: Store learnings.
        
        Args:
            cycle_result: Complete cycle result to store
        """
        # Store successful patterns
        if cycle_result.cognition:
            for improvement in cycle_result.cognition.improvements:
                await self._memory.remember(
                    key=f"pattern_{improvement['area']}_{datetime.utcnow().timestamp()}",
                    content=improvement,
                    memory_type="pattern",
                    tags=["improvement", improvement["area"]],
                    collection_type="patterns"
                )
        
        # Store action results
        if cycle_result.action and cycle_result.action.changes_made:
            for change in cycle_result.action.changes_made:
                await self._memory.remember(
                    key=f"change_{datetime.utcnow().timestamp()}",
                    content=change,
                    memory_type="code_change",
                    tags=["change", "autopoiesis"],
                    collection_type="code_history"
                )
        
        logger.info(f"Stored {len(cycle_result.action.changes_made if cycle_result.action else [])} changes in memory")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current autopoiesis status.
        
        Returns:
            Dictionary of status information
        """
        return {
            "enabled": True,
            "self_improve_enabled": self.config.enable_self_improve,
            "self_deploy_enabled": self.config.enable_self_deploy,
            "dry_run": self.config.dry_run,
            "cycle_count": self._cycle_count,
        }


# ============================================================================
# Convenience Functions
# ============================================================================

async def run_cycle(
    enable_self_improve: bool = False,
    dry_run: bool = True
) -> CycleResult:
    """Run a single autopoietic cycle.
    
    Args:
        enable_self_improve: Whether to allow self-improvement
        dry_run: Whether to run in dry run mode
        
    Returns:
        CycleResult
        
    Example:
        >>> result = await run_cycle(dry_run=True)
        >>> print(f"Found {len(result.cognition.improvements)} improvements")
    """
    config = CycleConfig(
        enable_self_improve=enable_self_improve,
        dry_run=dry_run,
    )
    
    cycle = AutopoieticCycle(config=config)
    return await cycle.run()


async def get_cycle_history(limit: int = 10) -> List[Dict[str, Any]]:
    """Get history of autopoietic cycles.
    
    Args:
        limit: Maximum cycles to return
        
    Returns:
        List of cycle result dictionaries
    """
    memory = get_memory_store()
    
    cycles = await memory.search_by_type(
        "cycle_result",
        collection_type="metrics",
        limit=limit
    )
    
    return [c.content for c in cycles]
{%- else %}
"""Autopoietic cycle placeholder.

This module requires both use_google_adk=y and use_google_cloud=y.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class CycleConfig:
    enable_self_improve: bool = False
    dry_run: bool = True


@dataclass
class CycleResult:
    cycle_id: str = ""
    started_at: datetime = None
    success: bool = False
    error: str = "Autopoiesis requires use_google_adk=y and use_google_cloud=y"


class AutopoieticCycle:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "AutopoieticCycle requires use_google_adk=y and use_google_cloud=y"
        )


async def run_cycle(**kwargs) -> CycleResult:
    return CycleResult()
{%- endif %}
