# FASE 3: ESPECIFICACIONES TÉCNICAS - TOP 3 IDEAS

## ISSUE #1: Self-Correcting Test Suite (SCTS)

**Assigned to:** Agent_Coder_01  
**Priority:** P0 | **Effort:** 5 days  
**Labels:** `enhancement`, `testing`, `automation`, `genesis`

### Descripción
Sistema que detecta fallos de tests causados por cambios de API y auto-genera fixtures actualizadas sin intervención humana.

### Aceptación
- [ ] Detecta cambios de firma de función automáticamente
- [ ] Genera fixtures actualizadas vía introspección
- [ ] 100% test coverage
- [ ] Integra con nox session `test-autocorrect`

### Código Propuesto

```python
# src/{{cookiecutter.package_name}}/testing/autocorrect.py
import inspect
from typing import Callable, Any
from dataclasses import dataclass

@dataclass
class FixtureMutation:
    test_name: str
    function_name: str
    old_signature: inspect.Signature
    new_signature: inspect.Signature
    auto_generated_fixture: str

class TestAutoCorrector:
    """Detecta y repara tests rotos automáticamente."""
    
    def __init__(self, test_module_path: str):
        self.test_module_path = test_module_path
        self.mutations: list[FixtureMutation] = []
    
    def detect_signature_changes(self, old_code: str, new_code: str) -> list[str]:
        """Detecta funciones con firma cambiada."""
        # Implementación: parse AST de ambos, compara signatures
        pass
    
    def auto_generate_fixture(self, func: Callable) -> str:
        """Genera fixture basado en tipo hints."""
        sig = inspect.signature(func)
        params = {}
        for name, param in sig.parameters.items():
            if param.annotation != inspect.Parameter.empty:
                params[name] = self._generate_value(param.annotation)
        return f"@pytest.fixture\ndef {func.__name__}_fixture():\n    return {params}"
    
    def _generate_value(self, type_hint: Any) -> Any:
        """Genera valor de prueba basado en type hint."""
        mapping = {
            int: 42,
            str: "test_value",
            bool: True,
            list: [],
            dict: {},
        }
        return mapping.get(type_hint, None)
    
    def apply_corrections(self) -> int:
        """Aplica todas las correcciones. Retorna número de tests reparados."""
        # Implementación: reescribe archivos de test
        return len(self.mutations)
```

### Tests Propuestos

```python
# tests/testing/test_autocorrect.py
import pytest
from {{cookiecutter.package_name}}.testing.autocorrect import TestAutoCorrector

def test_detect_signature_changes():
    old_code = "def foo(x: int) -> int: pass"
    new_code = "def foo(x: int, y: str) -> int: pass"
    corrector = TestAutoCorrector(".")
    changes = corrector.detect_signature_changes(old_code, new_code)
    assert "foo" in changes

def test_auto_generate_fixture_from_type_hints():
    def example_func(name: str, age: int) -> None:
        pass
    corrector = TestAutoCorrector(".")
    fixture = corrector.auto_generate_fixture(example_func)
    assert "@pytest.fixture" in fixture
    assert "name" in fixture
```

---

## ISSUE #2: Multi-Agent Review Code Integration (MARCI)

**Assigned to:** Agent_Coder_02  
**Priority:** P0 | **Effort:** 7 days  
**Labels:** `enhancement`, `code-review`, `ai`, `genesis`

### Descripción
Sistema que asigna PRs a múltiples "agentes especializados" (linting, security, performance) y consolida feedback en un reporte unificado.

### Aceptación
- [ ] Integra con GitHub Actions
- [ ] Crea 3 agentes especializados (lint, security, perf)
- [ ] Consolida resultados en single GitHub comment
- [ ] 100% test coverage

### Código Propuesto

```python
# src/{{cookiecutter.package_name}}/agents/review/orchestrator.py
from dataclasses import dataclass
from enum import Enum

class ReviewCategory(Enum):
    LINTING = "linting"
    SECURITY = "security"
    PERFORMANCE = "performance"

@dataclass
class ReviewComment:
    category: ReviewCategory
    severity: str  # "info", "warning", "error"
    message: str
    line_number: int

class CodeReviewOrchestrator:
    """Orquesta múltiples agentes de revisión."""
    
    def __init__(self, pr_number: int, repo_owner: str, repo_name: str):
        self.pr_number = pr_number
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.reviews: dict[ReviewCategory, list[ReviewComment]] = {
            cat: [] for cat in ReviewCategory
        }
    
    def run_all_reviews(self, diff: str) -> None:
        """Ejecuta todos los agentes de revisión en paralelo."""
        # Pseudocódigo: ejecutar en ThreadPoolExecutor
        self._run_lint_agent(diff)
        self._run_security_agent(diff)
        self._run_performance_agent(diff)
    
    def _run_lint_agent(self, diff: str) -> None:
        """Agente de linting via ruff/flake8."""
        pass
    
    def _run_security_agent(self, diff: str) -> None:
        """Agente de seguridad via bandit."""
        pass
    
    def _run_performance_agent(self, diff: str) -> None:
        """Agente de performance via profiling."""
        pass
    
    def consolidate_report(self) -> str:
        """Genera reporte consolidado en Markdown."""
        report = "# Code Review Report\n\n"
        for category, comments in self.reviews.items():
            report += f"## {category.value.title()}\n"
            for comment in comments:
                report += f"- [{comment.severity.upper()}] L{comment.line_number}: {comment.message}\n"
        return report
    
    def post_to_github(self) -> None:
        """Publica el reporte en GitHub como comment."""
        pass
```

---

## ISSUE #3: Evolutionary Performance Profiler (EPROF)

**Assigned to:** Agent_Coder_03  
**Priority:** P1 | **Effort:** 6 days  
**Labels:** `enhancement`, `performance`, `optimization`, `genesis`

### Descripción
Profiler que aprende patrones históricos de performance y predice bottlenecks antes de que el código sea mergeado.

### Aceptación
- [ ] Genera baseline de performance (con estadísticas)
- [ ] Detecta degradaciones > 5% automáticamente
- [ ] Bloquea merges si hay degradación significativa
- [ ] 100% test coverage

### Código Propuesto

```python
# src/{{cookiecutter.package_name}}/profiling/evolutionary.py
import time
import statistics
from dataclasses import dataclass, field

@dataclass
class PerformanceBaseline:
    function_name: str
    median_ms: float
    p95_ms: float
    p99_ms: float
    samples: list[float] = field(default_factory=list)

class EvolutionaryProfiler:
    """Profiler que aprende de runs anteriores."""
    
    def __init__(self, baseline_file: str = ".performance_baseline.json"):
        self.baseline_file = baseline_file
        self.baselines: dict[str, PerformanceBaseline] = {}
        self._load_baselines()
    
    def profile_function(self, func, *args, iterations: int = 100, **kwargs) -> PerformanceBaseline:
        """Perfila función múltiples veces y retorna stats."""
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        
        baseline = PerformanceBaseline(
            function_name=func.__name__,
            median_ms=statistics.median(times),
            p95_ms=sorted(times)[int(0.95 * len(times))],
            p99_ms=sorted(times)[int(0.99 * len(times))],
            samples=times
        )
        return baseline
    
    def check_regression(self, function_name: str, new_baseline: PerformanceBaseline) -> bool:
        """Retorna True si hay regresión > 5%."""
        if function_name not in self.baselines:
            return False  # Sin baseline anterior
        
        old = self.baselines[function_name]
        degradation = ((new_baseline.median_ms - old.median_ms) / old.median_ms) * 100
        return degradation > 5.0  # Umbral de 5%
    
    def _load_baselines(self) -> None:
        """Carga baselines históricos de archivo."""
        pass
```

---

## VALIDACIÓN CRUZADA

Todas 3 ideas:
- [x] Implementables en Python puro
- [x] Integrables con nox/poetry
- [x] Con 100% test coverage posible
- [x] Documentables vía docstrings
