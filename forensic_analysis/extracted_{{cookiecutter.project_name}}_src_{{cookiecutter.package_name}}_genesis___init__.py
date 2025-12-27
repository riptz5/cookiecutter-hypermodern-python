{%- if cookiecutter.use_google_adk == 'y' and cookiecutter.use_google_cloud == 'y' %}
"""GENESIS - Sistema Autopoietico en Google Cloud.

GENESIS es un sistema de IA auto-programable que:
- PERCIBE su entorno GCP automaticamente
- PIENSA usando Gemini para razonar
- ACTUA generando y ejecutando codigo
- EVOLUCIONA mejorando su propio codigo
- PERSISTE su estado en Firestore
- VIVE en Cloud Run

Arquitectura:
    ┌─────────────────────────────────────────┐
    │  PERCEIVE → THINK → ACT → REMEMBER      │
    │       ↑                      │          │
    │       └──────── EVOLVE ──────┘          │
    └─────────────────────────────────────────┘

Uso:
    >>> from {{cookiecutter.package_name}}.genesis import GenesisCore
    >>> genesis = GenesisCore()
    >>> result = await genesis.run_cycle()
    >>> print(result.success)
"""
from .core import GenesisCore, CycleResult
from .perceive import PerceiveModule, EnvironmentContext
from .think import ThinkModule, ActionPlan, Action
from .act import ActModule, ActionResult
from .memory import MemoryModule
from .evolve import EvolveModule

__all__ = [
    "GenesisCore",
    "CycleResult",
    "PerceiveModule",
    "EnvironmentContext",
    "ThinkModule",
    "ActionPlan",
    "Action",
    "ActModule",
    "ActionResult",
    "MemoryModule",
    "EvolveModule",
]
{%- endif %}
