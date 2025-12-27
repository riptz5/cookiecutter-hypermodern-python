{%- if cookiecutter.use_google_adk == 'y' and cookiecutter.use_google_cloud == 'y' %}
"""Modulo de Memoria - Persistencia en Firestore.

Este modulo implementa la persistencia del estado de GENESIS
usando Google Cloud Firestore como backend.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MemoryState:
    """Estado de memoria del sistema.
    
    Attributes:
        total_cycles: Total de ciclos ejecutados
        success_rate: Tasa de exito (0-1)
        agents_generated: Numero de agentes generados
        plugins_generated: Numero de plugins generados
        last_cycle: Info del ultimo ciclo
        last_evolution: Info de la ultima evolucion
        errors_recent: Errores recientes
    """
    total_cycles: int = 0
    success_rate: float = 0.0
    agents_generated: int = 0
    plugins_generated: int = 0
    last_cycle: Optional[Dict[str, Any]] = None
    last_evolution: Optional[Dict[str, Any]] = None
    errors_recent: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convierte a diccionario."""
        return {
            "total_cycles": self.total_cycles,
            "success_rate": self.success_rate,
            "agents_generated": self.agents_generated,
            "plugins_generated": self.plugins_generated,
            "last_cycle": self.last_cycle,
            "last_evolution": self.last_evolution,
            "errors_recent": self.errors_recent,
        }


class MemoryModule:
    """Modulo de memoria persistente.
    
    Utiliza Firestore para persistir:
    - Historial de ciclos
    - Agentes generados
    - Plugins generados
    - Metricas del sistema
    
    Example:
        >>> memory = MemoryModule()
        >>> await memory.store_cycle(cycle_id, context, plan, result)
        >>> state = await memory.get_state()
        >>> print(f"Total cycles: {state.total_cycles}")
    """
    
    # Colecciones de Firestore
    COLLECTION_CYCLES = "genesis_cycles"
    COLLECTION_AGENTS = "genesis_agents"
    COLLECTION_PLUGINS = "genesis_plugins"
    COLLECTION_STATE = "genesis_state"
    
    # Limite de ciclos a mantener en memoria
    MAX_CYCLES_HISTORY = 1000
    MAX_RECENT_ERRORS = 50
    
    def __init__(self):
        """Inicializa el modulo de memoria."""
        self._client = None
        self._local_cache: Dict[str, Any] = {}
        self._use_local = False
        logger.info("MemoryModule initialized")
    
    @property
    def client(self):
        """Lazy initialization del cliente Firestore."""
        if self._client is None:
            try:
                from ..cloud.firestore import FirestoreClient
                self._client = FirestoreClient()
                logger.info("Firestore client initialized")
            except ImportError:
                logger.warning("Firestore not available, using local cache")
                self._use_local = True
            except Exception as e:
                logger.warning(f"Firestore init failed: {e}, using local cache")
                self._use_local = True
        return self._client
    
    async def store_cycle(
        self,
        cycle_id: str,
        context,
        plan,
        result,
    ) -> None:
        """Almacena resultado de un ciclo.
        
        Args:
            cycle_id: ID del ciclo
            context: EnvironmentContext del ciclo
            plan: ActionPlan ejecutado
            result: ActionResult del ciclo
        """
        doc = {
            "cycle_id": cycle_id,
            "timestamp": datetime.utcnow().isoformat(),
            "context_hash": context.hash(),
            "context_summary": {
                "project_id": context.project_id,
                "services_count": len(context.services),
                "resources_count": len(context.resources),
                "changes_count": len(context.changes),
                "user_task": context.user_task,
            },
            "plan_summary": {
                "reasoning": plan.reasoning[:500] if plan.reasoning else "",
                "actions_count": len(plan.actions),
                "confidence": plan.confidence,
            },
            "result": result.to_dict(),
        }
        
        if self._use_local:
            self._store_local("cycles", cycle_id, doc)
        else:
            try:
                await self.client.add(self.COLLECTION_CYCLES, doc)
            except Exception as e:
                logger.error(f"Failed to store cycle: {e}")
                self._store_local("cycles", cycle_id, doc)
        
        logger.debug(f"Stored cycle: {cycle_id}")
    
    async def store_agent(
        self,
        agent_name: str,
        agent_info: Dict[str, Any],
    ) -> None:
        """Almacena informacion de un agente generado.
        
        Args:
            agent_name: Nombre del agente
            agent_info: Informacion del agente
        """
        doc = {
            "name": agent_name,
            "created_at": datetime.utcnow().isoformat(),
            **agent_info,
        }
        
        if self._use_local:
            self._store_local("agents", agent_name, doc)
        else:
            try:
                await self.client.set(
                    f"{self.COLLECTION_AGENTS}/{agent_name}",
                    doc,
                )
            except Exception as e:
                logger.error(f"Failed to store agent: {e}")
                self._store_local("agents", agent_name, doc)
    
    async def store_plugin(
        self,
        plugin_name: str,
        plugin_info: Dict[str, Any],
    ) -> None:
        """Almacena informacion de un plugin generado.
        
        Args:
            plugin_name: Nombre del plugin
            plugin_info: Informacion del plugin
        """
        doc = {
            "name": plugin_name,
            "created_at": datetime.utcnow().isoformat(),
            **plugin_info,
        }
        
        if self._use_local:
            self._store_local("plugins", plugin_name, doc)
        else:
            try:
                await self.client.set(
                    f"{self.COLLECTION_PLUGINS}/{plugin_name}",
                    doc,
                )
            except Exception as e:
                logger.error(f"Failed to store plugin: {e}")
                self._store_local("plugins", plugin_name, doc)
    
    async def get_state(self) -> MemoryState:
        """Obtiene estado actual del sistema.
        
        Returns:
            MemoryState con metricas del sistema
        """
        if self._use_local:
            return self._get_local_state()
        
        try:
            # Obtener ciclos recientes
            cycles = await self.client.query(
                self.COLLECTION_CYCLES,
                order_by="timestamp",
                order_direction="desc",
                limit=self.MAX_CYCLES_HISTORY,
            )
            
            # Obtener agentes
            agents = await self.client.list(self.COLLECTION_AGENTS)
            
            # Obtener plugins
            plugins = await self.client.list(self.COLLECTION_PLUGINS)
            
            # Calcular metricas
            total_cycles = len(cycles)
            successes = sum(
                1 for c in cycles
                if c.get("result", {}).get("success", False)
            )
            success_rate = successes / total_cycles if total_cycles > 0 else 0.0
            
            # Obtener errores recientes
            errors = []
            for c in cycles[:20]:  # Ultimos 20 ciclos
                cycle_errors = c.get("result", {}).get("errors", [])
                errors.extend(cycle_errors[:5])  # Max 5 errores por ciclo
            
            return MemoryState(
                total_cycles=total_cycles,
                success_rate=success_rate,
                agents_generated=len(agents),
                plugins_generated=len(plugins),
                last_cycle=cycles[0] if cycles else None,
                errors_recent=errors[:self.MAX_RECENT_ERRORS],
            )
            
        except Exception as e:
            logger.error(f"Failed to get state: {e}")
            return self._get_local_state()
    
    async def get_cycles(
        self,
        limit: int = 100,
        only_successful: bool = False,
    ) -> List[Dict[str, Any]]:
        """Obtiene historial de ciclos.
        
        Args:
            limit: Numero maximo de ciclos
            only_successful: Si solo retornar ciclos exitosos
            
        Returns:
            Lista de ciclos
        """
        if self._use_local:
            cycles = list(self._local_cache.get("cycles", {}).values())
            if only_successful:
                cycles = [
                    c for c in cycles
                    if c.get("result", {}).get("success", False)
                ]
            return sorted(
                cycles,
                key=lambda x: x.get("timestamp", ""),
                reverse=True,
            )[:limit]
        
        try:
            cycles = await self.client.query(
                self.COLLECTION_CYCLES,
                order_by="timestamp",
                order_direction="desc",
                limit=limit,
            )
            
            if only_successful:
                cycles = [
                    c for c in cycles
                    if c.get("result", {}).get("success", False)
                ]
            
            return cycles
            
        except Exception as e:
            logger.error(f"Failed to get cycles: {e}")
            return []
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Obtiene metricas detalladas del sistema.
        
        Returns:
            Diccionario con metricas
        """
        state = await self.get_state()
        cycles = await self.get_cycles(limit=100)
        
        # Calcular metricas adicionales
        if cycles:
            durations = [
                c.get("result", {}).get("duration_ms", 0)
                for c in cycles
            ]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            actions_counts = [
                len(c.get("result", {}).get("actions", []))
                for c in cycles
            ]
            avg_actions = sum(actions_counts) / len(actions_counts) if actions_counts else 0
        else:
            avg_duration = 0
            avg_actions = 0
        
        return {
            "total_cycles": state.total_cycles,
            "success_rate": state.success_rate,
            "agents_generated": state.agents_generated,
            "plugins_generated": state.plugins_generated,
            "avg_cycle_duration_ms": avg_duration,
            "avg_actions_per_cycle": avg_actions,
            "recent_errors_count": len(state.errors_recent),
        }
    
    def _store_local(self, collection: str, doc_id: str, doc: dict) -> None:
        """Almacena documento en cache local.
        
        Args:
            collection: Nombre de la coleccion
            doc_id: ID del documento
            doc: Documento a almacenar
        """
        if collection not in self._local_cache:
            self._local_cache[collection] = {}
        
        self._local_cache[collection][doc_id] = doc
        
        # Limpiar cache si es muy grande
        if len(self._local_cache[collection]) > self.MAX_CYCLES_HISTORY:
            # Mantener solo los mas recientes
            items = sorted(
                self._local_cache[collection].items(),
                key=lambda x: x[1].get("timestamp", ""),
                reverse=True,
            )
            self._local_cache[collection] = dict(items[:self.MAX_CYCLES_HISTORY])
    
    def _get_local_state(self) -> MemoryState:
        """Obtiene estado desde cache local.
        
        Returns:
            MemoryState desde cache local
        """
        cycles = list(self._local_cache.get("cycles", {}).values())
        agents = list(self._local_cache.get("agents", {}).values())
        plugins = list(self._local_cache.get("plugins", {}).values())
        
        total = len(cycles)
        successes = sum(
            1 for c in cycles
            if c.get("result", {}).get("success", False)
        )
        
        errors = []
        for c in sorted(
            cycles,
            key=lambda x: x.get("timestamp", ""),
            reverse=True,
        )[:20]:
            cycle_errors = c.get("result", {}).get("errors", [])
            errors.extend(cycle_errors[:5])
        
        return MemoryState(
            total_cycles=total,
            success_rate=successes / total if total > 0 else 0.0,
            agents_generated=len(agents),
            plugins_generated=len(plugins),
            last_cycle=cycles[-1] if cycles else None,
            errors_recent=errors[:self.MAX_RECENT_ERRORS],
        )
{%- endif %}
