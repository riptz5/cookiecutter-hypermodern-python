{%- if cookiecutter.use_google_adk == 'y' and cookiecutter.use_google_cloud == 'y' %}
"""Modulo de Accion - Ejecuta planes y genera codigo.

Este modulo implementa la fase ACT del ciclo GENESIS.
Ejecuta las acciones planificadas por el modulo Think,
incluyendo generacion de codigo, deployment y queries.
"""
import ast
import logging
import os
from dataclasses import dataclass, field
from typing import List, Any, Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ActionResult:
    """Resultado de ejecutar acciones.
    
    Attributes:
        actions: Lista de acciones ejecutadas (tipo:target)
        success: Si todas las acciones fueron exitosas
        outputs: Outputs de cada accion
        errors: Errores encontrados
        timestamp: Momento de ejecucion
    """
    actions: List[str] = field(default_factory=list)
    success: bool = True
    outputs: List[Any] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convierte a diccionario."""
        return {
            "actions": self.actions,
            "success": self.success,
            "outputs": [str(o)[:200] for o in self.outputs],  # Truncar outputs largos
            "errors": self.errors,
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def empty(cls) -> "ActionResult":
        """Crea resultado vacio para casos de error."""
        return cls(
            actions=[],
            success=False,
            errors=["No actions executed due to error"],
        )


class ActModule:
    """Modulo de ejecucion de acciones.
    
    Ejecuta las acciones del plan generado por ThinkModule.
    Soporta generacion de agentes, plugins, deployment y queries.
    
    Example:
        >>> act = ActModule()
        >>> act.think = think_module  # Inyectar dependencia
        >>> result = await act.execute(plan)
        >>> print(f"Success: {result.success}")
    """
    
    # Directorio base para codigo generado
    GENERATED_CODE_DIR = "generated"
    
    def __init__(self):
        """Inicializa el modulo de accion."""
        self.think = None  # Inyectado por GenesisCore
        self._generated_files: List[str] = []
        logger.info("ActModule initialized")
    
    async def execute(self, plan) -> ActionResult:
        """Ejecuta todas las acciones del plan.
        
        Args:
            plan: ActionPlan con acciones a ejecutar
            
        Returns:
            ActionResult con resultados
        """
        logger.info(f"[ACT] Executing plan with {len(plan.actions)} actions...")
        
        outputs: List[Any] = []
        errors: List[str] = []
        actions_done: List[str] = []
        
        # Ordenar por prioridad (mayor primero)
        sorted_actions = plan.get_actions_by_priority()
        
        for action in sorted_actions:
            action_id = f"{action.type}:{action.target}"
            logger.info(f"[ACT] Executing: {action_id}")
            
            try:
                result = await self._execute_action(action)
                outputs.append(result)
                actions_done.append(action_id)
                logger.info(f"[ACT] Success: {action_id}")
                
            except Exception as e:
                error_msg = f"{action_id} - {str(e)}"
                errors.append(error_msg)
                logger.error(f"[ACT] Failed: {error_msg}")
        
        success = len(errors) == 0 and len(actions_done) > 0
        
        logger.info(
            f"[ACT] Execution complete: "
            f"{len(actions_done)} succeeded, "
            f"{len(errors)} failed"
        )
        
        return ActionResult(
            actions=actions_done,
            success=success,
            outputs=outputs,
            errors=errors,
        )
    
    async def _execute_action(self, action) -> Any:
        """Ejecuta una accion individual.
        
        Args:
            action: Action a ejecutar
            
        Returns:
            Resultado de la accion
            
        Raises:
            ValueError: Si el tipo de accion es desconocido
        """
        handlers = {
            "generate_agent": self._generate_agent,
            "generate_plugin": self._generate_plugin,
            "deploy": self._deploy,
            "query": self._query,
            "modify_code": self._modify_code,
        }
        
        handler = handlers.get(action.type)
        if not handler:
            raise ValueError(f"Unknown action type: {action.type}")
        
        return await handler(action)
    
    async def _generate_agent(self, action) -> Dict[str, Any]:
        """Genera un nuevo agente para un servicio GCP.
        
        Args:
            action: Action con spec del agente
            
        Returns:
            Info sobre el agente generado
        """
        if self.think is None:
            raise RuntimeError("ThinkModule not injected")
        
        target = action.target
        spec = action.spec
        
        # Construir especificacion completa
        agent_spec = f'''Agente especializado para el servicio GCP: {target}

Descripcion: {spec.get("description", f"Agente para interactuar con {target}")}

Requerimientos:
{chr(10).join(f"- {r}" for r in spec.get("requirements", []))}

El agente debe:
1. Heredar de GoogleADKAgent
2. Tener system prompt especializado para {target}
3. Implementar metodos para las operaciones principales de {target}
4. Manejar errores de API de Google Cloud
5. Incluir logging apropiado
6. Ser compatible con async/await

Nombre de la clase: {self._to_class_name(target)}Agent
'''
        
        # Generar codigo
        code = await self.think.generate_code(agent_spec)
        
        # Validar sintaxis
        ast.parse(code)
        
        # Guardar archivo
        filename = f"{target.lower().replace('.', '_')}_agent.py"
        filepath = await self._save_generated_code(
            f"agents/{filename}",
            code,
            f"Generated agent for {target}"
        )
        
        return {
            "type": "agent",
            "target": target,
            "class_name": f"{self._to_class_name(target)}Agent",
            "filepath": filepath,
            "code_length": len(code),
        }
    
    async def _generate_plugin(self, action) -> Dict[str, Any]:
        """Genera un nuevo plugin de discovery.
        
        Args:
            action: Action con spec del plugin
            
        Returns:
            Info sobre el plugin generado
        """
        if self.think is None:
            raise RuntimeError("ThinkModule not injected")
        
        target = action.target
        spec = action.spec
        
        # Construir especificacion
        plugin_spec = f'''Plugin de discovery para el servicio GCP: {target}

Descripcion: {spec.get("description", f"Plugin para descubrir recursos de {target}")}

El plugin debe:
1. Heredar de BaseGCPPlugin
2. Implementar service_patterns con patrones para identificar {target}
3. Implementar required_packages con los paquetes necesarios
4. Implementar discover_resources() que:
   - Conecta al servicio usando google-cloud-{target.lower()}
   - Lista los recursos disponibles
   - Retorna dict con type, count y resources

Nombre de la clase: {self._to_class_name(target)}Plugin
'''
        
        # Generar codigo
        code = await self.think.generate_code(plugin_spec)
        
        # Validar sintaxis
        ast.parse(code)
        
        # Guardar archivo
        filename = f"{target.lower().replace('.', '_')}_plugin.py"
        filepath = await self._save_generated_code(
            f"plugins/{filename}",
            code,
            f"Generated plugin for {target}"
        )
        
        return {
            "type": "plugin",
            "target": target,
            "class_name": f"{self._to_class_name(target)}Plugin",
            "filepath": filepath,
            "code_length": len(code),
        }
    
    async def _deploy(self, action) -> Dict[str, Any]:
        """Despliega cambios a Cloud Run.
        
        Args:
            action: Action con spec del deployment
            
        Returns:
            Info sobre el deployment
        """
        logger.info(f"[ACT] Deploying: {action.target}")
        
        try:
            from ..cloud.run import CloudRunDeployer
            deployer = CloudRunDeployer()
            url = await deployer.deploy()
            
            return {
                "type": "deploy",
                "target": action.target,
                "url": url,
                "status": "deployed",
            }
        except ImportError:
            logger.warning("[ACT] CloudRunDeployer not available")
            return {
                "type": "deploy",
                "target": action.target,
                "status": "skipped",
                "reason": "CloudRunDeployer not installed",
            }
        except Exception as e:
            return {
                "type": "deploy",
                "target": action.target,
                "status": "failed",
                "error": str(e),
            }
    
    async def _query(self, action) -> Dict[str, Any]:
        """Ejecuta una consulta.
        
        Args:
            action: Action con spec de la query
            
        Returns:
            Resultados de la query
        """
        target = action.target
        spec = action.spec
        
        # Por ahora, queries se delegan a los agentes especializados
        # o se implementan segun el tipo de query
        
        query_type = spec.get("query_type", "info")
        
        if query_type == "info":
            return {
                "type": "query",
                "target": target,
                "query_type": query_type,
                "result": f"Query info for {target} - pending implementation",
            }
        
        return {
            "type": "query",
            "target": target,
            "query_type": query_type,
            "status": "not_implemented",
        }
    
    async def _modify_code(self, action) -> Dict[str, Any]:
        """Modifica codigo existente.
        
        Args:
            action: Action con spec de la modificacion
            
        Returns:
            Info sobre la modificacion
        """
        if self.think is None:
            raise RuntimeError("ThinkModule not injected")
        
        target = action.target
        spec = action.spec
        
        filepath = spec.get("filepath", "")
        modification = spec.get("modification", "")
        
        if not filepath or not modification:
            return {
                "type": "modify_code",
                "target": target,
                "status": "skipped",
                "reason": "Missing filepath or modification spec",
            }
        
        # Leer codigo actual
        try:
            with open(filepath, "r") as f:
                current_code = f.read()
        except FileNotFoundError:
            return {
                "type": "modify_code",
                "target": target,
                "status": "failed",
                "error": f"File not found: {filepath}",
            }
        
        # Generar modificacion
        mod_spec = f'''Modifica el siguiente codigo Python:

```python
{current_code}
```

Modificacion requerida: {modification}

Retorna el codigo completo modificado.
'''
        
        new_code = await self.think.generate_code(mod_spec)
        
        # Validar sintaxis
        ast.parse(new_code)
        
        # Guardar backup y nuevo codigo
        backup_path = f"{filepath}.backup"
        with open(backup_path, "w") as f:
            f.write(current_code)
        
        with open(filepath, "w") as f:
            f.write(new_code)
        
        return {
            "type": "modify_code",
            "target": target,
            "filepath": filepath,
            "backup": backup_path,
            "status": "modified",
        }
    
    async def _save_generated_code(
        self,
        relative_path: str,
        code: str,
        description: str,
    ) -> str:
        """Guarda codigo generado.
        
        Args:
            relative_path: Ruta relativa dentro de generated/
            code: Codigo a guardar
            description: Descripcion para el header
            
        Returns:
            Ruta completa del archivo guardado
        """
        # Header con metadata
        header = f'''"""Auto-generated by GENESIS.

{description}
Generated at: {datetime.utcnow().isoformat()}

DO NOT EDIT MANUALLY - This file is managed by GENESIS.
"""
'''
        
        full_code = header + "\n" + code
        
        # Crear directorio si no existe
        base_dir = os.path.join(os.path.dirname(__file__), "..", self.GENERATED_CODE_DIR)
        full_path = os.path.join(base_dir, relative_path)
        
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Guardar archivo
        with open(full_path, "w") as f:
            f.write(full_code)
        
        self._generated_files.append(full_path)
        logger.info(f"[ACT] Saved generated code: {full_path}")
        
        return full_path
    
    def _to_class_name(self, target: str) -> str:
        """Convierte target a nombre de clase.
        
        Args:
            target: Nombre del target (ej: "bigquery", "cloud-run")
            
        Returns:
            Nombre de clase (ej: "BigQuery", "CloudRun")
        """
        # Remover prefijos comunes
        name = target.lower()
        for prefix in ["google-cloud-", "google-", "cloud-", "gcp-"]:
            if name.startswith(prefix):
                name = name[len(prefix):]
        
        # Convertir a CamelCase
        parts = name.replace("-", "_").replace(".", "_").split("_")
        return "".join(part.capitalize() for part in parts)
    
    def get_generated_files(self) -> List[str]:
        """Retorna lista de archivos generados.
        
        Returns:
            Lista de rutas de archivos generados
        """
        return self._generated_files.copy()
{%- endif %}
