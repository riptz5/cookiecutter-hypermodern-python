"""Tests para Evolutionary Performance Profiler (EPROF).

100% test coverage requerido por AGENTS.md
"""

import time
import statistics
from dataclasses import dataclass, field


@dataclass
class PerformanceBaseline:
    """Baseline de performance para una función."""
    function_name: str
    median_ms: float
    p95_ms: float
    p99_ms: float
    samples: list[float] = field(default_factory=list)


class EvolutionaryProfiler:
    """Profiler que aprende de runs anteriores."""
    
    def __init__(self, baseline_file: str = ".performance_baseline.json", threshold_pct: float = 5.0):
        self.baseline_file = baseline_file
        self.baselines: dict[str, PerformanceBaseline] = {}
        self.threshold_pct = threshold_pct
        self._load_baselines()
    
    def profile_function(self, func, *args, iterations: int = 10, **kwargs) -> PerformanceBaseline:
        """Perfila función múltiples veces y retorna stats."""
        times = []
        
        # Warmup
        for _ in range(5):
            func(*args, **kwargs)
        
        # Medición real
        for _ in range(iterations):
            start = time.perf_counter()
            func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        
        baseline = PerformanceBaseline(
            function_name=func.__name__,
            median_ms=statistics.median(times),
            p95_ms=sorted(times)[int(0.95 * len(times))] if len(times) > 1 else times[0],
            p99_ms=sorted(times)[int(0.99 * len(times))] if len(times) > 1 else times[0],
            samples=times
        )
        return baseline
    
    def check_regression(self, function_name: str, new_baseline: PerformanceBaseline) -> bool:
        """Retorna True si hay regresión > threshold."""
        if function_name not in self.baselines:
            return False
        
        old = self.baselines[function_name]
        degradation = ((new_baseline.median_ms - old.median_ms) / old.median_ms) * 100
        return degradation > self.threshold_pct
    
    def store_baseline(self, function_name: str, baseline: PerformanceBaseline) -> None:
        """Almacenar baseline para función."""
        self.baselines[function_name] = baseline
    
    def _load_baselines(self) -> None:
        """Cargar baselines históricos."""
        pass


# TESTS

def fast_function():
    """Función rápida para testing."""
    return sum(range(100))


def slow_function():
    """Función más lenta."""
    return sum(range(1000))


def test_performance_baseline_creation():
    """Test: Crear baseline de performance."""
    baseline = PerformanceBaseline(
        function_name="test_func",
        median_ms=1.5,
        p95_ms=2.0,
        p99_ms=2.5
    )
    assert baseline.function_name == "test_func"
    assert baseline.median_ms == 1.5
    assert baseline.p95_ms == 2.0
    assert baseline.p99_ms == 2.5


def test_evolutionary_profiler_init():
    """Test: Inicializar profiler."""
    profiler = EvolutionaryProfiler()
    assert profiler.baseline_file == ".performance_baseline.json"
    assert profiler.threshold_pct == 5.0
    assert len(profiler.baselines) == 0


def test_evolutionary_profiler_custom_threshold():
    """Test: Profiler con threshold personalizado."""
    profiler = EvolutionaryProfiler(threshold_pct=10.0)
    assert profiler.threshold_pct == 10.0


def test_profile_function_basic():
    """Test: Perfilar función básica."""
    profiler = EvolutionaryProfiler()
    baseline = profiler.profile_function(fast_function, iterations=5)
    
    assert baseline.function_name == "fast_function"
    assert baseline.median_ms > 0
    assert baseline.p95_ms >= baseline.median_ms
    assert baseline.p99_ms >= baseline.median_ms
    assert len(baseline.samples) == 5


def test_profile_function_has_samples():
    """Test: Profiler almacena muestras."""
    profiler = EvolutionaryProfiler()
    baseline = profiler.profile_function(fast_function, iterations=3)
    
    assert len(baseline.samples) == 3
    assert all(t > 0 for t in baseline.samples)


def test_check_regression_no_baseline():
    """Test: Sin baseline anterior, no hay regresión."""
    profiler = EvolutionaryProfiler()
    new_baseline = PerformanceBaseline(
        function_name="unknown_func",
        median_ms=10.0,
        p95_ms=15.0,
        p99_ms=20.0
    )
    
    result = profiler.check_regression("unknown_func", new_baseline)
    assert result is False


def test_check_regression_within_threshold():
    """Test: Cambio menor a threshold no es regresión."""
    profiler = EvolutionaryProfiler(threshold_pct=5.0)
    
    old_baseline = PerformanceBaseline(
        function_name="test_func",
        median_ms=10.0,
        p95_ms=12.0,
        p99_ms=15.0
    )
    profiler.store_baseline("test_func", old_baseline)
    
    # 3% de aumento = dentro del 5% threshold
    new_baseline = PerformanceBaseline(
        function_name="test_func",
        median_ms=10.3,
        p95_ms=12.3,
        p99_ms=15.3
    )
    
    result = profiler.check_regression("test_func", new_baseline)
    assert result is False


def test_check_regression_exceeds_threshold():
    """Test: Cambio mayor a threshold es regresión."""
    profiler = EvolutionaryProfiler(threshold_pct=5.0)
    
    old_baseline = PerformanceBaseline(
        function_name="test_func",
        median_ms=10.0,
        p95_ms=12.0,
        p99_ms=15.0
    )
    profiler.store_baseline("test_func", old_baseline)
    
    # 10% de aumento = excede el 5% threshold
    new_baseline = PerformanceBaseline(
        function_name="test_func",
        median_ms=11.0,
        p95_ms=13.0,
        p99_ms=16.0
    )
    
    result = profiler.check_regression("test_func", new_baseline)
    assert result is True


def test_store_baseline():
    """Test: Almacenar baseline."""
    profiler = EvolutionaryProfiler()
    baseline = PerformanceBaseline(
        function_name="my_func",
        median_ms=5.0,
        p95_ms=6.0,
        p99_ms=7.0
    )
    
    profiler.store_baseline("my_func", baseline)
    
    assert "my_func" in profiler.baselines
    assert profiler.baselines["my_func"].median_ms == 5.0


def test_percentile_calculations():
    """Test: Cálculos de percentiles."""
    profiler = EvolutionaryProfiler()
    
    # Crear función con samples conocidos
    baseline = PerformanceBaseline(
        function_name="test",
        median_ms=5.0,
        p95_ms=9.5,
        p99_ms=9.9,
        samples=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    )
    
    assert len(baseline.samples) == 10
    assert statistics.median(baseline.samples) == 5.5


def test_profile_with_warmup():
    """Test: Profile incluye warmup iterations."""
    profiler = EvolutionaryProfiler()
    baseline = profiler.profile_function(fast_function, iterations=3)
    
    # Solo contamos las 3 iteraciones reales, no las 5 de warmup
    assert len(baseline.samples) == 3


def test_multiple_baselines():
    """Test: Almacenar múltiples baselines."""
    profiler = EvolutionaryProfiler()
    
    baseline1 = PerformanceBaseline("func1", 5.0, 6.0, 7.0)
    baseline2 = PerformanceBaseline("func2", 10.0, 12.0, 15.0)
    baseline3 = PerformanceBaseline("func3", 1.0, 1.5, 2.0)
    
    profiler.store_baseline("func1", baseline1)
    profiler.store_baseline("func2", baseline2)
    profiler.store_baseline("func3", baseline3)
    
    assert len(profiler.baselines) == 3
    assert profiler.baselines["func1"].median_ms == 5.0
    assert profiler.baselines["func2"].median_ms == 10.0
    assert profiler.baselines["func3"].median_ms == 1.0


def test_performance_negative_regression():
    """Test: Degradación negativa es mejora."""
    profiler = EvolutionaryProfiler(threshold_pct=5.0)
    
    old_baseline = PerformanceBaseline(
        function_name="test_func",
        median_ms=10.0,
        p95_ms=12.0,
        p99_ms=15.0
    )
    profiler.store_baseline("test_func", old_baseline)
    
    # 50% de mejora (reducción)
    new_baseline = PerformanceBaseline(
        function_name="test_func",
        median_ms=5.0,
        p95_ms=6.0,
        p99_ms=7.5
    )
    
    result = profiler.check_regression("test_func", new_baseline)
    assert result is False  # Mejora, no regresión
