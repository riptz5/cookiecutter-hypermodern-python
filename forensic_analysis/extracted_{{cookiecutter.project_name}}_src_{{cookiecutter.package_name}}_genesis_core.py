{%- if cookiecutter.use_google_adk == 'y' and cookiecutter.use_google_cloud == 'y' %}
"""GENESIS Core - Sistema Autopoietico Central.

Este modulo implementa el nucleo de GENESIS, un sistema que:
1. Se auto-descubre en su entorno GCP
2. Razona sobre que acciones tomar
3. Genera y ejecuta codigo automaticamente
4. Persiste su estado para continuidad
5. Mejora su propio codigo periodicamente

El ciclo de vida sigue el patron OODA (Observe, Orient, Decide, Act)
adaptado para sistemas autopoieticos.
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional, List, Any
from datetime import datetime
import hashlib

from .perceive import PerceiveModule, EnvironmentContext
from .think import ThinkModule, ActionPlan
from .act import ActModule, ActionResult
from .memory import MemoryModule
from .evolve import EvolveModule

logger = logging.getLogger(__name__)


@dataclass
class CycleResult:
    """Resultado de un ciclo GENESIS.
    
    Attributes:
        cycle_id: Identificador unico del ciclo
        timestamp: Momento de ejecucion
        context_hash: Hash del contexto para detectar cambios
        plan_summary: Resumen del plan ejecutado
        actions_taken: Lista de acciones ejecutadas
        success: Si el ciclo fue exitoso
        duration_ms: Duracion en milisegundos
        evolved: Si se ejecuto evolucion
        errors: Lista de errores encontrados
    """
    cycle_id: str
    timestamp: datetime
    context_hash: str
    plan_summary: str
    actions_taken: List[str]
    success: bool
    duration_ms: float
    evolved: bool = False
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convierte a diccionario para persistencia."""
        return {
            "cycle_id": self.cycle_id,
            "timestamp": self.timestamp.isoformat(),
            "context_hash": self.context_hash,
            "plan_summary": self.plan_summary,
            "actions_taken": self.actions_taken,
            "success": self.success,
            "duration_ms": self.duration_ms,
            "evolved": self.evolved,
            "errors": self.errors,
        }


class GenesisCore:
    """Sistema autopoietico central que vive en Google Cloud.
    
    GenesisCore es el cerebro del sistema GENESIS. Coordina todos los
    modulos (Perceive, Think, Act, Memory, Evolve) en un ciclo continuo
    de auto-mejora y adaptacion.
    
    Ciclo de vida:
        ┌─────────────────────────────────────────┐
        │  PERCEIVE → THINK → ACT → REMEMBER      │
        │       ↑                      │          │
        │       └──────── EVOLVE ──────┘          │
        └─────────────────────────────────────────┘
    
    El sistema:
    - Auto-descubre su entorno GCP usando el plugin system
    - Razona sobre que hacer usando Gemini
    - Genera y ejecuta codigo para nuevos agentes/plugins
    - Persiste estado en Firestore para continuidad
    - Mejora su propio codigo periodicamente
    
    Example:
        >>> genesis = GenesisCore()
        >>> 
        >>> # Ejecutar un ciclo
        >>> result = await genesis.run_cycle()
        >>> print(f"Success: {result.success}")
        >>> 
        >>> # Ejecutar con tarea especifica
        >>> result = await genesis.run_cycle(task="Crear agente para BigQuery")
        >>> 
        >>> # Ejecutar continuamente
        >>> await genesis.run_continuous(interval_seconds=60)
    
    Attributes:
        perceive: Modulo de percepcion del entorno
        think: Modulo de razonamiento con Gemini
        act: Modulo de ejecucion de acciones
        memory: Modulo de persistencia
        evolve: Modulo de auto-mejora
    """
    
    # Configuracion por defecto
    DEFAULT_EVOLUTION_THRESHOLD = 10  # Evolucionar cada N ciclos
    DEFAULT_CYCLE_INTERVAL = 60  # Segundos entre ciclos continuos
    
    def __init__(
        self,
        evolution_threshold: int = DEFAULT_EVOLUTION_THRESHOLD,
        auto_evolve: bool = True,
    ):
        """Inicializa GenesisCore.
        
        Args:
            evolution_threshold: Numero de ciclos entre evoluciones
            auto_evolve: Si debe evolucionar automaticamente
        """
        logger.info("Initializing GENESIS Core...")
        
        # Inicializar modulos
        self.perceive = PerceiveModule()
        self.think = ThinkModule()
        self.act = ActModule()
        self.memory = MemoryModule()
        self.evolve = EvolveModule()
        
        # Inyectar dependencias entre modulos
        self.act.think = self.think
        self.evolve.think = self.think
        self.evolve.act = self.act
        self.evolve.memory = self.memory
        
        # Configuracion
        self._evolution_threshold = evolution_threshold
        self._auto_evolve = auto_evolve
        self._cycle_count = 0
        self._start_time = datetime.utcnow()
        
        logger.info("GENESIS Core initialized successfully")
    
    async def run_cycle(self, task: Optional[str] = None) -> CycleResult:
        """Ejecuta un ciclo completo GENESIS.
        
        Un ciclo consiste en:
        1. PERCEIVE - Escanear y entender el entorno GCP
        2. THINK - Razonar sobre que acciones tomar
        3. ACT - Ejecutar las acciones planificadas
        4. REMEMBER - Persistir el resultado
        5. EVOLVE - Mejorar el sistema (periodicamente)
        
        Args:
            task: Tarea opcional especifica. Si es None, el sistema
                  auto-determina que hacer basado en el contexto.
        
        Returns:
            CycleResult con el resultado del ciclo
            
        Example:
            >>> result = await genesis.run_cycle()
            >>> if result.success:
            ...     print(f"Ejecutadas {len(result.actions_taken)} acciones")
            >>> else:
            ...     print(f"Errores: {result.errors}")
        """
        cycle_id = self._generate_cycle_id()
        start_time = time.time()
        errors: List[str] = []
        
        logger.info(f"[GENESIS] Starting cycle {cycle_id}")
        
        try:
            # ═══════════════════════════════════════════════════════════
            # FASE 1: PERCEIVE - Escanear entorno
            # ═══════════════════════════════════════════════════════════
            logger.info("[GENESIS] Phase 1: PERCEIVE")
            try:
                context = await self.perceive.scan()
                if task:
                    context.user_task = task
                logger.info(f"[GENESIS] Context hash: {context.hash()}")
            except Exception as e:
                logger.error(f"[GENESIS] Perceive failed: {e}")
                errors.append(f"perceive: {str(e)}")
                # Crear contexto minimo para continuar
                context = EnvironmentContext.empty()
                context.user_task = task
            
            # ═══════════════════════════════════════════════════════════
            # FASE 2: THINK - Razonar sobre que hacer
            # ═══════════════════════════════════════════════════════════
            logger.info("[GENESIS] Phase 2: THINK")
            try:
                plan = await self.think.reason(context)
                logger.info(f"[GENESIS] Plan: {len(plan.actions)} actions")
            except Exception as e:
                logger.error(f"[GENESIS] Think failed: {e}")
                errors.append(f"think: {str(e)}")
                plan = ActionPlan.empty()
            
            # ═══════════════════════════════════════════════════════════
            # FASE 3: ACT - Ejecutar acciones
            # ═══════════════════════════════════════════════════════════
            logger.info("[GENESIS] Phase 3: ACT")
            try:
                result = await self.act.execute(plan)
                logger.info(f"[GENESIS] Actions executed: {result.success}")
                if result.errors:
                    errors.extend(result.errors)
            except Exception as e:
                logger.error(f"[GENESIS] Act failed: {e}")
                errors.append(f"act: {str(e)}")
                result = ActionResult.empty()
            
            # ═══════════════════════════════════════════════════════════
            # FASE 4: REMEMBER - Persistir estado
            # ═══════════════════════════════════════════════════════════
            logger.info("[GENESIS] Phase 4: REMEMBER")
            try:
                await self.memory.store_cycle(
                    cycle_id=cycle_id,
                    context=context,
                    plan=plan,
                    result=result,
                )
            except Exception as e:
                logger.warning(f"[GENESIS] Memory store failed: {e}")
                errors.append(f"memory: {str(e)}")
            
            # ═══════════════════════════════════════════════════════════
            # FASE 5: EVOLVE - Auto-mejora (periodica)
            # ═══════════════════════════════════════════════════════════
            self._cycle_count += 1
            evolved = False
            
            if self._auto_evolve and self._should_evolve():
                logger.info("[GENESIS] Phase 5: EVOLVE")
                try:
                    await self.evolve.improve()
                    evolved = True
                except Exception as e:
                    logger.warning(f"[GENESIS] Evolve failed: {e}")
                    errors.append(f"evolve: {str(e)}")
            
            # ═══════════════════════════════════════════════════════════
            # Construir resultado
            # ═══════════════════════════════════════════════════════════
            duration_ms = (time.time() - start_time) * 1000
            
            cycle_result = CycleResult(
                cycle_id=cycle_id,
                timestamp=datetime.utcnow(),
                context_hash=context.hash(),
                plan_summary=plan.reasoning[:200] if plan.reasoning else "",
                actions_taken=result.actions,
                success=len(errors) == 0 and result.success,
                duration_ms=duration_ms,
                evolved=evolved,
                errors=errors,
            )
            
            logger.info(
                f"[GENESIS] Cycle {cycle_id} completed: "
                f"success={cycle_result.success}, "
                f"actions={len(result.actions)}, "
                f"duration={duration_ms:.2f}ms"
            )
            
            return cycle_result
            
        except Exception as e:
            # Error catastrofico - registrar y crear resultado de error
            logger.critical(f"[GENESIS] Critical error in cycle: {e}")
            duration_ms = (time.time() - start_time) * 1000
            
            return CycleResult(
                cycle_id=cycle_id,
                timestamp=datetime.utcnow(),
                context_hash="error",
                plan_summary="",
                actions_taken=[],
                success=False,
                duration_ms=duration_ms,
                evolved=False,
                errors=[f"critical: {str(e)}"],
            )
    
    async def run_continuous(
        self,
        interval_seconds: float = DEFAULT_CYCLE_INTERVAL,
        max_cycles: Optional[int] = None,
    ) -> None:
        """Ejecuta ciclos GENESIS continuamente.
        
        El sistema ejecutara ciclos indefinidamente (o hasta max_cycles)
        con el intervalo especificado entre ciclos.
        
        Args:
            interval_seconds: Segundos entre ciclos
            max_cycles: Numero maximo de ciclos (None = infinito)
            
        Example:
            >>> # Ejecutar indefinidamente
            >>> await genesis.run_continuous()
            >>> 
            >>> # Ejecutar 100 ciclos
            >>> await genesis.run_continuous(max_cycles=100)
        """
        logger.info(
            f"[GENESIS] Starting continuous mode: "
            f"interval={interval_seconds}s, max_cycles={max_cycles}"
        )
        
        cycles_run = 0
        
        while max_cycles is None or cycles_run < max_cycles:
            try:
                result = await self.run_cycle()
                cycles_run += 1
                
                status = "✓" if result.success else "✗"
                logger.info(
                    f"[GENESIS] Continuous cycle {cycles_run}: "
                    f"{status} ({result.duration_ms:.0f}ms)"
                )
                
            except Exception as e:
                logger.error(f"[GENESIS] Continuous cycle error: {e}")
            
            # Esperar antes del siguiente ciclo
            await asyncio.sleep(interval_seconds)
        
        logger.info(f"[GENESIS] Continuous mode ended after {cycles_run} cycles")
    
    async def force_evolve(self) -> bool:
        """Fuerza un ciclo de evolucion inmediato.
        
        Returns:
            True si la evolucion fue exitosa
        """
        logger.info("[GENESIS] Forcing evolution cycle")
        try:
            await self.evolve.improve()
            return True
        except Exception as e:
            logger.error(f"[GENESIS] Forced evolution failed: {e}")
            return False
    
    def _should_evolve(self) -> bool:
        """Determina si debe ejecutarse evolucion."""
        return self._cycle_count % self._evolution_threshold == 0
    
    def _generate_cycle_id(self) -> str:
        """Genera ID unico para el ciclo."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique = hashlib.sha256(
            f"{timestamp}_{self._cycle_count}".encode()
        ).hexdigest()[:8]
        return f"cycle_{timestamp}_{unique}"
    
    def get_status(self) -> dict:
        """Obtiene estado actual del sistema.
        
        Returns:
            Diccionario con metricas del sistema
        """
        uptime = (datetime.utcnow() - self._start_time).total_seconds()
        
        return {
            "status": "running",
            "uptime_seconds": uptime,
            "cycles_completed": self._cycle_count,
            "next_evolution_in": self._evolution_threshold - (
                self._cycle_count % self._evolution_threshold
            ),
            "auto_evolve": self._auto_evolve,
        }
{%- endif %}
