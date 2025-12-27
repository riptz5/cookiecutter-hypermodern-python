{%- if cookiecutter.use_google_adk == 'y' and cookiecutter.use_langgraph == 'y' %}
"""ADK-LangGraph Bridge - Conecta agentes ADK con LangGraph.

Este modulo proporciona utilidades para integrar agentes
GoogleADK como nodos en grafos de LangGraph, permitiendo
orquestacion sofisticada de multi-agentes.
"""
import asyncio
import logging
import os
from typing import Callable, Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class BridgeConfig:
    """Configuracion del bridge.
    
    Attributes:
        api_key: API key de Google
        default_model: Modelo por defecto
        max_parallel: Max agentes en paralelo
        timeout_seconds: Timeout por agente
    """
    api_key: Optional[str] = None
    default_model: str = "gemini-2.0-flash-exp"
    max_parallel: int = 5
    timeout_seconds: float = 120.0
    
    def __post_init__(self):
        if self.api_key is None:
            self.api_key = os.getenv("GOOGLE_API_KEY")


class ADKLangGraphBridge:
    """Bridge entre Google ADK y LangGraph.
    
    Permite usar agentes ADK como nodos en grafos LangGraph,
    facilitando la construccion de sistemas multi-agente
    con orquestacion sofisticada.
    
    Example:
        >>> bridge = ADKLangGraphBridge()
        >>> 
        >>> # Crear nodo desde agente ADK
        >>> agent = GoogleADKAgent(config)
        >>> node_fn = bridge.wrap_adk_agent(agent)
        >>> 
        >>> # Usar en grafo LangGraph
        >>> graph = StateGraph(AgentState)
        >>> graph.add_node("researcher", node_fn)
    """
    
    def __init__(self, config: Optional[BridgeConfig] = None):
        """Inicializa el bridge.
        
        Args:
            config: Configuracion del bridge
        """
        self.config = config or BridgeConfig()
        self._wrapped_agents: Dict[str, Callable] = {}
        logger.info("ADKLangGraphBridge initialized")
    
    def wrap_adk_agent(
        self,
        agent,
        state_key: str = "messages",
        output_key: str = "agent_response",
    ) -> Callable:
        """Envuelve un agente ADK como nodo LangGraph.
        
        Args:
            agent: Instancia de GoogleADKAgent
            state_key: Key en el state para obtener el prompt
            output_key: Key donde guardar la respuesta
            
        Returns:
            Funcion async compatible con LangGraph
        """
        async def node_fn(state: Dict[str, Any]) -> Dict[str, Any]:
            """Nodo LangGraph que ejecuta el agente ADK."""
            # Extraer prompt del state
            prompt = self._extract_prompt(state, state_key)
            
            if not prompt:
                logger.warning("No prompt found in state")
                return {output_key: "No prompt provided", "error": True}
            
            try:
                # Ejecutar agente con timeout
                response = await asyncio.wait_for(
                    agent.run(prompt),
                    timeout=self.config.timeout_seconds,
                )
                
                return {
                    output_key: response,
                    "agent_name": getattr(agent, "name", "unknown"),
                    "error": False,
                }
                
            except asyncio.TimeoutError:
                logger.error(f"Agent timeout after {self.config.timeout_seconds}s")
                return {output_key: "Agent timeout", "error": True}
            except Exception as e:
                logger.error(f"Agent error: {e}")
                return {output_key: str(e), "error": True}
        
        return node_fn
    
    def wrap_multiple(
        self,
        agents: Dict[str, Any],
        state_key: str = "task",
    ) -> Dict[str, Callable]:
        """Envuelve multiples agentes como nodos.
        
        Args:
            agents: Dict de nombre -> agente
            state_key: Key del state para el prompt
            
        Returns:
            Dict de nombre -> node function
        """
        nodes = {}
        for name, agent in agents.items():
            nodes[name] = self.wrap_adk_agent(
                agent,
                state_key=state_key,
                output_key=f"{name}_response",
            )
            self._wrapped_agents[name] = nodes[name]
        
        logger.info(f"Wrapped {len(nodes)} agents as LangGraph nodes")
        return nodes
    
    def create_parallel_node(
        self,
        agents: Dict[str, Any],
        state_key: str = "task",
    ) -> Callable:
        """Crea un nodo que ejecuta multiples agentes en paralelo.
        
        Args:
            agents: Dict de nombre -> agente
            state_key: Key del state para el prompt
            
        Returns:
            Funcion async que ejecuta todos en paralelo
        """
        async def parallel_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """Ejecuta todos los agentes en paralelo."""
            prompt = self._extract_prompt(state, state_key)
            
            if not prompt:
                return {"results": {}, "error": True}
            
            # Crear tareas para todos los agentes
            tasks = {}
            for name, agent in agents.items():
                tasks[name] = asyncio.create_task(
                    self._run_with_timeout(agent, prompt)
                )
            
            # Esperar todos
            results = {}
            for name, task in tasks.items():
                try:
                    results[name] = await task
                except Exception as e:
                    results[name] = f"Error: {e}"
            
            return {
                "results": results,
                "agents_run": list(results.keys()),
                "error": False,
            }
        
        return parallel_node
    
    def create_sequential_node(
        self,
        agents: List[Any],
        state_key: str = "task",
    ) -> Callable:
        """Crea un nodo que ejecuta agentes secuencialmente.
        
        Cada agente recibe el output del anterior.
        
        Args:
            agents: Lista ordenada de agentes
            state_key: Key del state para el prompt inicial
            
        Returns:
            Funcion async que ejecuta en secuencia
        """
        async def sequential_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """Ejecuta agentes en secuencia."""
            current_input = self._extract_prompt(state, state_key)
            results = []
            
            for i, agent in enumerate(agents):
                try:
                    response = await self._run_with_timeout(agent, current_input)
                    results.append(response)
                    # El output se convierte en input del siguiente
                    current_input = response
                except Exception as e:
                    results.append(f"Error at step {i}: {e}")
                    break
            
            return {
                "final_output": results[-1] if results else "",
                "intermediate_results": results,
                "steps_completed": len(results),
            }
        
        return sequential_node
    
    def create_router_node(
        self,
        agents: Dict[str, Any],
        router_agent: Any,
    ) -> Callable:
        """Crea un nodo que routea tareas a agentes especificos.
        
        Args:
            agents: Dict de nombre -> agente
            router_agent: Agente que decide a quien routear
            
        Returns:
            Funcion async que routea y ejecuta
        """
        async def router_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """Routea tarea al agente apropiado."""
            task = self._extract_prompt(state, "task")
            
            # Pedir al router que decida
            routing_prompt = f"""Analiza la siguiente tarea y decide que agente debe manejarla.

Agentes disponibles: {list(agents.keys())}

Tarea: {task}

Responde SOLO con el nombre del agente (una palabra).
"""
            
            try:
                router_response = await self._run_with_timeout(router_agent, routing_prompt)
                selected_agent = router_response.strip().lower()
                
                # Buscar agente
                agent = None
                for name, a in agents.items():
                    if name.lower() in selected_agent or selected_agent in name.lower():
                        agent = a
                        selected_agent = name
                        break
                
                if agent is None:
                    # Default al primero
                    selected_agent = list(agents.keys())[0]
                    agent = agents[selected_agent]
                
                # Ejecutar agente seleccionado
                result = await self._run_with_timeout(agent, task)
                
                return {
                    "routed_to": selected_agent,
                    "agent_response": result,
                    "routing_decision": router_response,
                }
                
            except Exception as e:
                return {
                    "error": True,
                    "message": str(e),
                }
        
        return router_node
    
    async def _run_with_timeout(self, agent, prompt: str) -> str:
        """Ejecuta agente con timeout.
        
        Args:
            agent: Agente a ejecutar
            prompt: Prompt para el agente
            
        Returns:
            Respuesta del agente
        """
        return await asyncio.wait_for(
            agent.run(prompt),
            timeout=self.config.timeout_seconds,
        )
    
    def _extract_prompt(self, state: Dict[str, Any], key: str) -> str:
        """Extrae prompt del state.
        
        Args:
            state: State de LangGraph
            key: Key a buscar
            
        Returns:
            Prompt como string
        """
        value = state.get(key)
        
        if isinstance(value, str):
            return value
        
        if isinstance(value, list):
            # Asumir lista de mensajes, tomar el ultimo
            if value:
                last = value[-1]
                if isinstance(last, dict):
                    return last.get("content", str(last))
                return str(last)
            return ""
        
        if isinstance(value, dict):
            return value.get("content", str(value))
        
        return str(value) if value else ""


def create_bridge(api_key: Optional[str] = None) -> ADKLangGraphBridge:
    """Crea un bridge con configuracion por defecto.
    
    Args:
        api_key: API key de Google (opcional)
        
    Returns:
        ADKLangGraphBridge configurado
    """
    config = BridgeConfig(api_key=api_key)
    return ADKLangGraphBridge(config)
{%- else %}
"""A2A/MCP bridge for agent communication.

Este modulo requiere use_google_adk='y' y use_langgraph='y'
para funcionalidad completa.
"""
{%- endif %}
