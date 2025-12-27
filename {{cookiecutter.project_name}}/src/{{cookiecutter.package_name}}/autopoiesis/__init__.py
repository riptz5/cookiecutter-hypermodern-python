"""Autopoietic system - Self-maintaining, self-improving code.

This module implements the autopoietic pattern where the system:
1. PERCEIVES its own state (code, logs, metrics)
2. COGNIZES improvements (analyzes what can be better)
3. ACTS on improvements (generates new code)
4. REMEMBERS learnings (stores in Firestore)
5. REPEATS the cycle (via Cloud Scheduler)

Components:
- AutopoieticCycle: Main cycle orchestration
- PerceptionModule: Code and metric analysis
- CognitionModule: Improvement reasoning (uses Gemini)
- ActionModule: Code generation and execution
- MemoryModule: Persistent learning storage

WARNING: Self-improvement and self-deployment are DISABLED by default.
Enable only in controlled environments.
"""
from .cycle import (
    AutopoieticCycle,
    CycleResult,
    CycleConfig,
    run_cycle,
)

__all__ = [
    "AutopoieticCycle",
    "CycleResult",
    "CycleConfig",
    "run_cycle",
]
