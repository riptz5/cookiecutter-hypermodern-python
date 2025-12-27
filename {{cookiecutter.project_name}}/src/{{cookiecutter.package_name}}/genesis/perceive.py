{%- if cookiecutter.use_google_adk == 'y' and cookiecutter.use_google_cloud == 'y' %}
"""Modulo de Percepcion - Detecta y entiende el entorno GCP.

Este modulo implementa la fase PERCEIVE del ciclo GENESIS.
Se integra con el sistema de plugins de GCP Discovery para
detectar automaticamente todos los recursos disponibles.
"""
import hashlib
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class EnvironmentContext:
    """Contexto completo del entorno GCP.
    
    Contiene toda la informacion que GENESIS necesita para
    razonar sobre su entorno y decidir acciones.
    
    Attributes:
        project_id: ID del proyecto GCP
        region: Region activa
        services: Servicios habilitados
        resources: Recursos descubiertos por servicio
        changes: Cambios detectados desde ultimo scan
        memory_state: Estado de memoria del sistema
        user_task: Tarea especifica del usuario (opcional)
        timestamp: Momento del scan
    """
    project_id: str = ""
    region: str = "us-central1"
    services: List[str] = field(default_factory=list)
    resources: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    changes: List[Dict[str, Any]] = field(default_factory=list)
    memory_state: Dict[str, Any] = field(default_factory=dict)
    user_task: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def hash(self) -> str:
        """Genera hash unico del contexto.
        
        Util para detectar si el entorno ha cambiado.
        
        Returns:
            Hash SHA256 truncado a 16 caracteres
        """
        data = json.dumps({
            "project_id": self.project_id,
            "region": self.region,
            "services": sorted(self.services),
            "resources": self.resources,
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def to_prompt(self) -> str:
        """Convierte contexto a prompt para Gemini.
        
        Genera un prompt estructurado que permite a Gemini
        entender completamente el estado del sistema.
        
        Returns:
            Prompt formateado para razonamiento
        """
        services_str = "\n".join(f"  - {s}" for s in self.services[:20])
        if len(self.services) > 20:
            services_str += f"\n  ... y {len(self.services) - 20} mas"
        
        resources_str = json.dumps(self.resources, indent=2, default=str)
        changes_str = json.dumps(self.changes, indent=2, default=str)
        memory_str = json.dumps(self.memory_state, indent=2, default=str)
        
        return f'''## Contexto del Entorno GCP

### Proyecto
- ID: {self.project_id}
- Region: {self.region}
- Timestamp: {self.timestamp.isoformat()}

### Servicios Habilitados ({len(self.services)})
{services_str}

### Recursos Descubiertos
{resources_str}

### Cambios Detectados
{changes_str}

### Estado de Memoria
{memory_str}

### Tarea del Usuario
{self.user_task or "Auto-determinar siguiente accion optima"}

---
Analiza este contexto y decide que acciones tomar.
'''
    
    def to_dict(self) -> dict:
        """Convierte a diccionario para persistencia."""
        return {
            "project_id": self.project_id,
            "region": self.region,
            "services": self.services,
            "resources": self.resources,
            "changes": self.changes,
            "memory_state": self.memory_state,
            "user_task": self.user_task,
            "timestamp": self.timestamp.isoformat(),
            "hash": self.hash(),
        }
    
    @classmethod
    def empty(cls) -> "EnvironmentContext":
        """Crea contexto vacio para casos de error."""
        return cls(
            project_id="unknown",
            changes=[{"type": "error", "message": "Could not scan environment"}],
        )


class PerceiveModule:
    """Modulo de percepcion del entorno GCP.
    
    Se integra con GCPDiscovery para detectar automaticamente
    todos los recursos disponibles en el proyecto.
    
    Example:
        >>> perceive = PerceiveModule()
        >>> context = await perceive.scan()
        >>> print(f"Project: {context.project_id}")
        >>> print(f"Services: {len(context.services)}")
    """
    
    def __init__(self):
        """Inicializa el modulo de percepcion."""
        self._discovery = None
        self._last_context: Optional[EnvironmentContext] = None
        self._scan_count = 0
    
    @property
    def discovery(self):
        """Lazy initialization de GCPDiscovery."""
        if self._discovery is None:
            try:
                from ..core.gcp_discovery import GCPDiscovery
                self._discovery = GCPDiscovery()
                logger.info("GCP Discovery initialized")
            except ImportError as e:
                logger.warning(f"GCP Discovery not available: {e}")
                self._discovery = None
            except Exception as e:
                logger.error(f"Failed to initialize GCP Discovery: {e}")
                self._discovery = None
        return self._discovery
    
    async def scan(self) -> EnvironmentContext:
        """Escanea el entorno GCP completo.
        
        Ejecuta discovery de:
        - Proyecto y credenciales
        - Servicios habilitados
        - Recursos por servicio (via plugins)
        - Estado de memoria
        
        Tambien detecta cambios desde el ultimo scan.
        
        Returns:
            EnvironmentContext con toda la informacion
            
        Raises:
            No lanza excepciones - retorna contexto parcial en caso de error
        """
        logger.info("[PERCEIVE] Starting environment scan...")
        self._scan_count += 1
        
        # Valores por defecto
        project_id = "unknown"
        region = "us-central1"
        services: List[str] = []
        resources: Dict[str, Dict[str, Any]] = {}
        
        # Intentar discovery
        if self.discovery is not None:
            try:
                # Descubrir proyecto
                project = self.discovery.discover_project()
                project_id = project.project_id
                region = project.region
                logger.info(f"[PERCEIVE] Project: {project_id}")
                
                # Descubrir servicios
                enabled_services = self.discovery.discover_enabled_services()
                services = [s.name for s in enabled_services if s.enabled]
                logger.info(f"[PERCEIVE] Services: {len(services)} enabled")
                
                # Descubrir recursos via plugins
                resources = self.discovery.discover_all_service_resources()
                logger.info(f"[PERCEIVE] Resources: {len(resources)} services with resources")
                
            except Exception as e:
                logger.error(f"[PERCEIVE] Discovery error: {e}")
        else:
            logger.warning("[PERCEIVE] GCP Discovery not available")
        
        # Detectar cambios
        changes = self._detect_changes(project_id, services, resources)
        
        # Obtener estado de memoria
        memory_state = await self._get_memory_state()
        
        # Construir contexto
        context = EnvironmentContext(
            project_id=project_id,
            region=region,
            services=services,
            resources=resources,
            changes=changes,
            memory_state=memory_state,
            timestamp=datetime.utcnow(),
        )
        
        # Guardar para comparacion futura
        self._last_context = context
        
        logger.info(
            f"[PERCEIVE] Scan complete: "
            f"project={project_id}, "
            f"services={len(services)}, "
            f"resources={len(resources)}, "
            f"changes={len(changes)}"
        )
        
        return context
    
    def _detect_changes(
        self,
        project_id: str,
        services: List[str],
        resources: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Detecta cambios desde el ultimo scan.
        
        Args:
            project_id: ID del proyecto actual
            services: Servicios actuales
            resources: Recursos actuales
            
        Returns:
            Lista de cambios detectados
        """
        if self._last_context is None:
            return [{"type": "initial_scan", "scan_number": self._scan_count}]
        
        changes: List[Dict[str, Any]] = []
        
        # Comparar servicios
        old_services = set(self._last_context.services)
        new_services = set(services)
        
        added_services = new_services - old_services
        removed_services = old_services - new_services
        
        if added_services:
            changes.append({
                "type": "services_added",
                "services": list(added_services),
            })
        
        if removed_services:
            changes.append({
                "type": "services_removed",
                "services": list(removed_services),
            })
        
        # Comparar recursos
        for service, current_data in resources.items():
            old_data = self._last_context.resources.get(service, {})
            old_count = old_data.get("count", 0)
            new_count = current_data.get("count", 0)
            
            if new_count != old_count:
                change_type = "increased" if new_count > old_count else "decreased"
                changes.append({
                    "type": f"resource_count_{change_type}",
                    "service": service,
                    "old_count": old_count,
                    "new_count": new_count,
                    "delta": new_count - old_count,
                })
        
        # Detectar nuevos servicios con recursos
        old_resource_services = set(self._last_context.resources.keys())
        new_resource_services = set(resources.keys())
        
        new_with_resources = new_resource_services - old_resource_services
        if new_with_resources:
            changes.append({
                "type": "new_services_with_resources",
                "services": list(new_with_resources),
            })
        
        return changes
    
    async def _get_memory_state(self) -> Dict[str, Any]:
        """Obtiene estado de memoria desde Firestore.
        
        Returns:
            Estado de memoria o diccionario vacio si no disponible
        """
        try:
            from ..cloud.firestore import FirestoreClient
            client = FirestoreClient()
            state = await client.get_genesis_state()
            return state or {}
        except ImportError:
            logger.debug("Firestore client not available")
            return {"status": "memory_unavailable", "reason": "firestore_not_installed"}
        except Exception as e:
            logger.debug(f"Could not get memory state: {e}")
            return {"status": "memory_error", "error": str(e)}
    
    def get_last_context(self) -> Optional[EnvironmentContext]:
        """Obtiene el ultimo contexto escaneado.
        
        Returns:
            Ultimo contexto o None si no hay
        """
        return self._last_context
{%- endif %}
