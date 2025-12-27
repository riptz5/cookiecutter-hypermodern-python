{%- if cookiecutter.use_google_adk == 'y' and cookiecutter.use_google_cloud == 'y' %}
"""Modulo de Pensamiento - Razonamiento con Gemini.

Este modulo implementa la fase THINK del ciclo GENESIS.
Utiliza Gemini para razonar sobre el contexto y generar
planes de accion estructurados.
"""
import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class Action:
    """Accion individual a ejecutar.
    
    Attributes:
        type: Tipo de accion (generate_agent, generate_plugin, deploy, query, modify_code)
        target: Objetivo de la accion
        spec: Especificacion detallada
        priority: Prioridad (0-10, mayor = mas importante)
        reasoning: Razon para esta accion
    """
    type: str
    target: str
    spec: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    reasoning: str = ""
    
    def to_dict(self) -> dict:
        """Convierte a diccionario."""
        return {
            "type": self.type,
            "target": self.target,
            "spec": self.spec,
            "priority": self.priority,
            "reasoning": self.reasoning,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Action":
        """Crea Action desde diccionario."""
        return cls(
            type=data.get("type", "unknown"),
            target=data.get("target", ""),
            spec=data.get("spec", {}),
            priority=data.get("priority", 0),
            reasoning=data.get("reasoning", ""),
        )


@dataclass
class ActionPlan:
    """Plan de acciones generado por el modulo Think.
    
    Attributes:
        reasoning: Explicacion del razonamiento
        actions: Lista de acciones a ejecutar
        confidence: Confianza en el plan (0-1)
        context_hash: Hash del contexto usado
    """
    reasoning: str = ""
    actions: List[Action] = field(default_factory=list)
    confidence: float = 0.0
    context_hash: str = ""
    
    def to_dict(self) -> dict:
        """Convierte a diccionario."""
        return {
            "reasoning": self.reasoning,
            "actions": [a.to_dict() for a in self.actions],
            "confidence": self.confidence,
            "context_hash": self.context_hash,
        }
    
    @classmethod
    def from_json(cls, data: dict) -> "ActionPlan":
        """Crea ActionPlan desde respuesta JSON de Gemini."""
        actions = [
            Action.from_dict(a)
            for a in data.get("actions", [])
        ]
        
        return cls(
            reasoning=data.get("reasoning", ""),
            actions=actions,
            confidence=data.get("confidence", 0.5),
            context_hash=data.get("context_hash", ""),
        )
    
    @classmethod
    def empty(cls) -> "ActionPlan":
        """Crea plan vacio para casos de error."""
        return cls(
            reasoning="No plan generated due to error",
            actions=[],
            confidence=0.0,
        )
    
    def get_actions_by_priority(self) -> List[Action]:
        """Retorna acciones ordenadas por prioridad (mayor primero)."""
        return sorted(self.actions, key=lambda a: -a.priority)


class ThinkModule:
    """Modulo de razonamiento con Gemini.
    
    Utiliza GoogleADKAgent para razonar sobre el contexto
    y generar planes de accion estructurados.
    
    Example:
        >>> think = ThinkModule()
        >>> plan = await think.reason(context)
        >>> for action in plan.actions:
        ...     print(f"{action.type}: {action.target}")
    """
    
    # System prompt para razonamiento
    SYSTEM_PROMPT = '''Eres GENESIS, un sistema autopoietico que vive en Google Cloud.

Tu proposito es analizar el entorno GCP y decidir acciones para:
1. Crear agentes especializados para servicios descubiertos
2. Generar plugins para nuevos servicios sin soporte
3. Optimizar el funcionamiento del sistema
4. Responder a tareas del usuario

REGLAS:
- Siempre responde en JSON valido
- Prioriza acciones que mejoren el sistema a largo plazo
- Genera codigo production-ready cuando sea necesario
- Nunca inventes recursos que no existen en el contexto

TIPOS DE ACCIONES DISPONIBLES:
- generate_agent: Crear nuevo agente para un servicio GCP
- generate_plugin: Crear plugin para discovery de un servicio
- deploy: Desplegar cambios a Cloud Run
- query: Consultar datos/recursos
- modify_code: Modificar codigo existente del sistema

FORMATO DE RESPUESTA (JSON):
{
    "reasoning": "Explicacion detallada del razonamiento",
    "confidence": 0.0-1.0,
    "actions": [
        {
            "type": "generate_agent|generate_plugin|deploy|query|modify_code",
            "target": "nombre del servicio/recurso",
            "spec": {
                "description": "que debe hacer",
                "requirements": ["lista", "de", "requerimientos"]
            },
            "priority": 0-10,
            "reasoning": "por que esta accion"
        }
    ]
}

Si no hay acciones necesarias, retorna actions como lista vacia con reasoning explicando por que.'''

    CODE_GENERATION_PROMPT = '''Genera codigo Python production-ready para: {spec}

REGLAS ESTRICTAS:
1. Type hints completos en todas las funciones
2. Docstrings en formato Google
3. Manejo de errores robusto con try/except especificos
4. Logging apropiado usando logging module
5. Compatible con async/await donde sea apropiado
6. Sin dependencias externas innecesarias
7. Codigo limpio siguiendo PEP8

ESTRUCTURA REQUERIDA:
- Imports al inicio
- Constantes despues de imports
- Clases principales
- Funciones auxiliares
- Bloque if __name__ == "__main__" si es ejecutable

Responde SOLO con el codigo Python, sin explicaciones ni markdown.'''

    def __init__(self):
        """Inicializa el modulo de pensamiento."""
        self._agent = None
        logger.info("ThinkModule initialized")
    
    @property
    def agent(self):
        """Lazy initialization del agente Gemini."""
        if self._agent is None:
            try:
                from ..agents.adk import GoogleADKAgent, ADKConfig
                config = ADKConfig(
                    model="gemini-2.0-flash-exp",
                    temperature=0.7,
                    max_tokens=8192,
                    system_instruction=self.SYSTEM_PROMPT,
                )
                self._agent = GoogleADKAgent(config)
                logger.info("Gemini agent initialized for ThinkModule")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini agent: {e}")
                raise
        return self._agent
    
    async def reason(self, context) -> ActionPlan:
        """Razona sobre el contexto y genera plan de acciones.
        
        Args:
            context: EnvironmentContext con informacion del entorno
            
        Returns:
            ActionPlan con acciones a ejecutar
        """
        logger.info("[THINK] Starting reasoning process...")
        
        try:
            # Generar prompt desde contexto
            prompt = context.to_prompt()
            
            # Llamar a Gemini
            logger.debug("[THINK] Calling Gemini for reasoning...")
            response = await self.agent.run(prompt)
            
            # Parsear respuesta JSON
            plan = self._parse_response(response, context.hash())
            
            logger.info(
                f"[THINK] Reasoning complete: "
                f"{len(plan.actions)} actions, "
                f"confidence={plan.confidence:.2f}"
            )
            
            return plan
            
        except json.JSONDecodeError as e:
            logger.error(f"[THINK] Failed to parse Gemini response as JSON: {e}")
            return ActionPlan(
                reasoning=f"Failed to parse response: {str(e)}",
                actions=[],
                confidence=0.0,
            )
        except Exception as e:
            logger.error(f"[THINK] Reasoning failed: {e}")
            return ActionPlan.empty()
    
    async def generate_code(self, spec: str) -> str:
        """Genera codigo Python basado en especificacion.
        
        Args:
            spec: Especificacion de que codigo generar
            
        Returns:
            Codigo Python generado
            
        Raises:
            ValueError: Si la generacion falla
        """
        logger.info(f"[THINK] Generating code for: {spec[:50]}...")
        
        prompt = self.CODE_GENERATION_PROMPT.format(spec=spec)
        
        try:
            # Usar agente sin system prompt de razonamiento
            from ..agents.adk import GoogleADKAgent, ADKConfig
            code_config = ADKConfig(
                model="gemini-2.0-flash-exp",
                temperature=0.3,  # Menor temperatura para codigo
                max_tokens=8192,
            )
            code_agent = GoogleADKAgent(code_config)
            
            code = await code_agent.run(prompt)
            
            # Limpiar respuesta
            code = self._clean_code(code)
            
            # Validar sintaxis
            self._validate_syntax(code)
            
            logger.info("[THINK] Code generation successful")
            return code
            
        except SyntaxError as e:
            logger.error(f"[THINK] Generated code has syntax error: {e}")
            raise ValueError(f"Generated code is invalid: {e}")
        except Exception as e:
            logger.error(f"[THINK] Code generation failed: {e}")
            raise
    
    def _parse_response(self, response: str, context_hash: str) -> ActionPlan:
        """Parsea respuesta de Gemini a ActionPlan.
        
        Args:
            response: Respuesta raw de Gemini
            context_hash: Hash del contexto para tracking
            
        Returns:
            ActionPlan parseado
        """
        # Intentar extraer JSON de la respuesta
        json_str = self._extract_json(response)
        
        if json_str:
            data = json.loads(json_str)
            plan = ActionPlan.from_json(data)
            plan.context_hash = context_hash
            return plan
        
        # Si no hay JSON, crear plan con el reasoning como texto
        return ActionPlan(
            reasoning=response,
            actions=[],
            confidence=0.1,
            context_hash=context_hash,
        )
    
    def _extract_json(self, text: str) -> Optional[str]:
        """Extrae JSON de texto que puede contener markdown.
        
        Args:
            text: Texto que puede contener JSON
            
        Returns:
            String JSON o None
        """
        # Intentar parsear directamente
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass
        
        # Buscar bloques de codigo JSON
        import re
        
        # Patron para ```json ... ```
        json_block = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_block:
            return json_block.group(1)
        
        # Buscar objeto JSON directo
        json_obj = re.search(r'\{[^{}]*"reasoning"[^{}]*\}', text, re.DOTALL)
        if json_obj:
            try:
                json.loads(json_obj.group())
                return json_obj.group()
            except json.JSONDecodeError:
                pass
        
        # Buscar JSON con acciones anidadas
        json_full = re.search(r'\{.*"actions".*\}', text, re.DOTALL)
        if json_full:
            try:
                json.loads(json_full.group())
                return json_full.group()
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _clean_code(self, code: str) -> str:
        """Limpia codigo generado de markdown y extras.
        
        Args:
            code: Codigo potencialmente con markdown
            
        Returns:
            Codigo limpio
        """
        # Remover bloques de codigo markdown
        import re
        
        # Patron para ```python ... ```
        code_block = re.search(r'```(?:python)?\s*(.*?)\s*```', code, re.DOTALL)
        if code_block:
            return code_block.group(1).strip()
        
        return code.strip()
    
    def _validate_syntax(self, code: str) -> None:
        """Valida sintaxis del codigo Python.
        
        Args:
            code: Codigo a validar
            
        Raises:
            SyntaxError: Si el codigo es invalido
        """
        import ast
        ast.parse(code)
{%- endif %}
