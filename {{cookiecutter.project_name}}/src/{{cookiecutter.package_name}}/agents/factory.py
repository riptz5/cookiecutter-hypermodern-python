{%- if cookiecutter.use_google_adk == 'y' %}
"""Agent Factory - Auto-genera agentes para servicios GCP.

Este modulo proporciona una fabrica para crear agentes
especializados automaticamente basandose en el servicio
GCP objetivo.
"""
import logging
from typing import Dict, Any, Optional, Type, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Tipos de agentes disponibles."""
    RESEARCH = "research"
    ANALYSIS = "analysis"
    WRITER = "writer"
    CODE = "code"
    DATA = "data"
    INFRASTRUCTURE = "infrastructure"
    MONITORING = "monitoring"


@dataclass
class AgentSpec:
    """Especificacion de un agente.
    
    Attributes:
        name: Nombre unico del agente
        agent_type: Tipo de agente
        target_service: Servicio GCP objetivo
        capabilities: Lista de capacidades
        system_prompt: Prompt de sistema personalizado
        model: Modelo a usar
        temperature: Temperatura del modelo
    """
    name: str
    agent_type: AgentType
    target_service: str = ""
    capabilities: List[str] = field(default_factory=list)
    system_prompt: Optional[str] = None
    model: str = "gemini-2.0-flash-exp"
    temperature: float = 0.7


# Templates de system prompts por tipo
AGENT_PROMPTS = {
    AgentType.RESEARCH: """Eres un agente de investigacion especializado.
Tu objetivo es buscar, analizar y sintetizar informacion sobre {target_service}.
Proporciona respuestas bien estructuradas y citando fuentes cuando sea posible.
Enfocate en hechos verificables y datos actuales.""",

    AgentType.ANALYSIS: """Eres un agente de analisis especializado.
Tu objetivo es analizar datos y patrones relacionados con {target_service}.
Proporciona analisis profundos con conclusiones accionables.
Usa metricas cuantitativas cuando sea posible.""",

    AgentType.WRITER: """Eres un agente escritor especializado.
Tu objetivo es generar contenido de alta calidad sobre {target_service}.
Escribe de forma clara, concisa y profesional.
Adapta el tono al contexto solicitado.""",

    AgentType.CODE: """Eres un agente de desarrollo de codigo especializado.
Tu objetivo es generar, revisar y mejorar codigo para {target_service}.
Sigue las mejores practicas de Python y PEP8.
Incluye type hints, docstrings y manejo de errores robusto.""",

    AgentType.DATA: """Eres un agente de datos especializado.
Tu objetivo es manejar operaciones de datos en {target_service}.
Optimiza consultas, transforma datos y asegura calidad.
Prioriza eficiencia y escalabilidad.""",

    AgentType.INFRASTRUCTURE: """Eres un agente de infraestructura especializado.
Tu objetivo es gestionar recursos de {target_service}.
Aplica IaC best practices y optimiza costos.
Prioriza seguridad y disponibilidad.""",

    AgentType.MONITORING: """Eres un agente de monitoreo especializado.
Tu objetivo es observar y reportar sobre {target_service}.
Detecta anomalias, genera alertas y propone remediaciones.
Mantien dashboards y metricas actualizados.""",
}


# Mapeo de servicios GCP a tipos de agentes recomendados
SERVICE_AGENT_MAPPING = {
    "bigquery": [AgentType.DATA, AgentType.ANALYSIS],
    "storage": [AgentType.DATA, AgentType.INFRASTRUCTURE],
    "compute": [AgentType.INFRASTRUCTURE, AgentType.MONITORING],
    "run": [AgentType.INFRASTRUCTURE, AgentType.CODE],
    "functions": [AgentType.CODE, AgentType.INFRASTRUCTURE],
    "pubsub": [AgentType.DATA, AgentType.INFRASTRUCTURE],
    "firestore": [AgentType.DATA, AgentType.CODE],
    "spanner": [AgentType.DATA, AgentType.ANALYSIS],
    "vertexai": [AgentType.RESEARCH, AgentType.ANALYSIS],
    "monitoring": [AgentType.MONITORING, AgentType.ANALYSIS],
    "logging": [AgentType.MONITORING, AgentType.ANALYSIS],
}


class AgentFactory:
    """Fabrica de agentes especializados.
    
    Crea agentes automaticamente basandose en el servicio
    objetivo y el tipo de tarea requerida.
    
    Example:
        >>> factory = AgentFactory()
        >>> agent = factory.create("bigquery-analyst", AgentType.DATA, "bigquery")
        >>> result = await agent.run("Analiza las tablas disponibles")
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Inicializa la fabrica.
        
        Args:
            api_key: API key de Google (usa GOOGLE_API_KEY si es None)
        """
        import os
        self._api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self._agents: Dict[str, Any] = {}
        self._specs: Dict[str, AgentSpec] = {}
        logger.info("AgentFactory initialized")
    
    def create(
        self,
        name: str,
        agent_type: AgentType,
        target_service: str = "",
        capabilities: Optional[List[str]] = None,
        custom_prompt: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """Crea un nuevo agente.
        
        Args:
            name: Nombre unico del agente
            agent_type: Tipo de agente
            target_service: Servicio GCP objetivo
            capabilities: Lista de capacidades
            custom_prompt: Prompt personalizado (override default)
            **kwargs: Args adicionales para el agente
            
        Returns:
            Instancia del agente creado
        """
        if name in self._agents:
            logger.debug(f"Returning cached agent: {name}")
            return self._agents[name]
        
        # Construir system prompt
        if custom_prompt:
            system_prompt = custom_prompt
        else:
            template = AGENT_PROMPTS.get(agent_type, AGENT_PROMPTS[AgentType.RESEARCH])
            system_prompt = template.format(target_service=target_service or "GCP")
        
        # Crear spec
        spec = AgentSpec(
            name=name,
            agent_type=agent_type,
            target_service=target_service,
            capabilities=capabilities or [],
            system_prompt=system_prompt,
            model=kwargs.get("model", "gemini-2.0-flash-exp"),
            temperature=kwargs.get("temperature", 0.7),
        )
        
        # Crear agente
        try:
            from .adk import GoogleADKAgent, ADKConfig
            
            config = ADKConfig(
                model=spec.model,
                temperature=spec.temperature,
                system_instruction=spec.system_prompt,
                api_key=self._api_key,
            )
            
            agent = GoogleADKAgent(config)
            agent.name = name
            agent.spec = spec
            
            # Cachear
            self._agents[name] = agent
            self._specs[name] = spec
            
            logger.info(f"Created agent: {name} ({agent_type.value})")
            return agent
            
        except ImportError as e:
            logger.error(f"Failed to create agent: {e}")
            raise
    
    def create_for_service(
        self,
        service: str,
        agent_type: Optional[AgentType] = None,
    ) -> Any:
        """Crea un agente optimizado para un servicio GCP.
        
        Args:
            service: Nombre del servicio GCP (ej: "bigquery", "storage")
            agent_type: Tipo de agente (auto-selecciona si es None)
            
        Returns:
            Agente especializado
        """
        # Auto-seleccionar tipo si no se especifica
        if agent_type is None:
            recommended = SERVICE_AGENT_MAPPING.get(
                service.lower(),
                [AgentType.RESEARCH],
            )
            agent_type = recommended[0]
        
        name = f"{service.lower()}-{agent_type.value}"
        return self.create(name, agent_type, service)
    
    def create_workers(
        self,
        types: Optional[List[AgentType]] = None,
    ) -> Dict[str, Any]:
        """Crea conjunto de workers especializados.
        
        Args:
            types: Lista de tipos a crear (default: todos basicos)
            
        Returns:
            Diccionario de agentes por tipo
        """
        if types is None:
            types = [
                AgentType.RESEARCH,
                AgentType.ANALYSIS,
                AgentType.WRITER,
                AgentType.CODE,
            ]
        
        workers = {}
        for agent_type in types:
            name = f"worker-{agent_type.value}"
            workers[agent_type.value] = self.create(name, agent_type)
        
        logger.info(f"Created {len(workers)} workers")
        return workers
    
    def get(self, name: str) -> Optional[Any]:
        """Obtiene un agente existente.
        
        Args:
            name: Nombre del agente
            
        Returns:
            Agente o None si no existe
        """
        return self._agents.get(name)
    
    def get_spec(self, name: str) -> Optional[AgentSpec]:
        """Obtiene spec de un agente.
        
        Args:
            name: Nombre del agente
            
        Returns:
            AgentSpec o None
        """
        return self._specs.get(name)
    
    def list_agents(self) -> List[str]:
        """Lista todos los agentes creados.
        
        Returns:
            Lista de nombres de agentes
        """
        return list(self._agents.keys())
    
    def clear(self) -> None:
        """Limpia todos los agentes cacheados."""
        self._agents.clear()
        self._specs.clear()
        logger.info("Cleared all cached agents")


# Instancia global para acceso facil
_default_factory: Optional[AgentFactory] = None


def get_factory() -> AgentFactory:
    """Obtiene la fabrica global.
    
    Returns:
        AgentFactory global
    """
    global _default_factory
    if _default_factory is None:
        _default_factory = AgentFactory()
    return _default_factory


def create_agent(
    name: str,
    agent_type: AgentType,
    target_service: str = "",
    **kwargs,
) -> Any:
    """Atajo para crear agentes usando la fabrica global.
    
    Args:
        name: Nombre del agente
        agent_type: Tipo de agente
        target_service: Servicio objetivo
        **kwargs: Args adicionales
        
        
    Returns:
        Agente creado
    """
    return get_factory().create(name, agent_type, target_service, **kwargs)


def create_worker(agent_type: AgentType) -> Any:
    """Atajo para crear un worker de tipo especifico.
    
    Args:
        agent_type: Tipo de worker
        
    Returns:
        Worker creado
    """
    return get_factory().create(f"worker-{agent_type.value}", agent_type)
{%- endif %}
