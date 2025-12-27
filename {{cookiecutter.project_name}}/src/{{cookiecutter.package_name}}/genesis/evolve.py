{%- if cookiecutter.use_google_adk == 'y' and cookiecutter.use_google_cloud == 'y' %}
"""Modulo de Evolucion - Auto-mejora del sistema.

Este modulo implementa la fase EVOLVE del ciclo GENESIS.
Analiza el rendimiento del sistema y genera mejoras automaticas.
"""
import ast
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class Improvement:
    """Mejora propuesta para el sistema.
    
    Attributes:
        file: Archivo a modificar
        description: Descripcion de la mejora
        code: Codigo nuevo/modificado
        confidence: Confianza en la mejora (0-1)
        impact: Impacto estimado (low/medium/high)
    """
    file: str
    description: str
    code: str
    confidence: float = 0.5
    impact: str = "medium"
    
    def to_dict(self) -> dict:
        """Convierte a diccionario."""
        return {
            "file": self.file,
            "description": self.description,
            "code_preview": self.code[:200] + "..." if len(self.code) > 200 else self.code,
            "confidence": self.confidence,
            "impact": self.impact,
        }


@dataclass
class EvolutionResult:
    """Resultado de un ciclo de evolucion.
    
    Attributes:
        improvements_proposed: Mejoras propuestas
        improvements_applied: Mejoras aplicadas
        success: Si la evolucion fue exitosa
        timestamp: Momento de la evolucion
    """
    improvements_proposed: List[Improvement] = field(default_factory=list)
    improvements_applied: List[Improvement] = field(default_factory=list)
    success: bool = True
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convierte a diccionario."""
        return {
            "improvements_proposed": len(self.improvements_proposed),
            "improvements_applied": len(self.improvements_applied),
            "success": self.success,
            "timestamp": self.timestamp.isoformat(),
            "applied": [i.to_dict() for i in self.improvements_applied],
        }


class EvolveModule:
    """Modulo de auto-mejora del sistema.
    
    Analiza metricas y errores para proponer y aplicar
    mejoras automaticas al codigo del sistema.
    
    Example:
        >>> evolve = EvolveModule()
        >>> evolve.think = think_module
        >>> evolve.memory = memory_module
        >>> result = await evolve.improve()
        >>> print(f"Applied {len(result.improvements_applied)} improvements")
    """
    
    # Prompt para analisis de evolucion
    EVOLUTION_PROMPT = '''Eres GENESIS en modo EVOLUCION.

Analiza las metricas y errores del sistema para proponer mejoras.

## Metricas Actuales
{metrics}

## Errores Recientes
{errors}

## Codigo Actual (fragmento relevante)
{code_context}

REGLAS:
1. Solo proponer mejoras que mejoren metricas concretas
2. Las mejoras deben ser pequeñas e incrementales
3. Priorizar correccion de errores recurrentes
4. No modificar logica core sin razon clara
5. Mantener compatibilidad hacia atras

Responde en JSON:
{
    "analysis": "Analisis de la situacion actual",
    "improvements": [
        {
            "file": "ruta/al/archivo.py",
            "description": "Que mejora y por que",
            "code": "codigo python completo del archivo mejorado",
            "confidence": 0.0-1.0,
            "impact": "low|medium|high"
        }
    ]
    }
    
    Si no hay mejoras necesarias, retorna improvements como lista vacia.
'''

    # Umbral de confianza para aplicar mejoras automaticamente
    AUTO_APPLY_CONFIDENCE = 0.8
    
    # Maximo de mejoras a aplicar por ciclo
    MAX_IMPROVEMENTS_PER_CYCLE = 3
    
    def __init__(self):
        """Inicializa el modulo de evolucion."""
        self.think = None  # Inyectado por GenesisCore
        self.act = None    # Inyectado por GenesisCore
        self.memory = None # Inyectado por GenesisCore
        self._evolution_count = 0
        logger.info("EvolveModule initialized")
    
    async def improve(self) -> EvolutionResult:
        """Ejecuta ciclo de auto-mejora.
        
        Analiza el estado del sistema y aplica mejoras
        automaticas cuando la confianza es alta.
        
        Returns:
            EvolutionResult con mejoras aplicadas
        """
        logger.info("[EVOLVE] Starting evolution cycle...")
        self._evolution_count += 1
        
        try:
            # Obtener metricas y errores
            metrics = await self._get_metrics()
            errors = await self._get_recent_errors()
            
            # Obtener contexto de codigo relevante
            code_context = await self._get_code_context(errors)
            
            # Proponer mejoras
            improvements = await self._propose_improvements(
                metrics, errors, code_context
            )
            
            logger.info(f"[EVOLVE] Proposed {len(improvements)} improvements")
            
            # Filtrar y aplicar mejoras con alta confianza
            applied = []
            for imp in improvements[:self.MAX_IMPROVEMENTS_PER_CYCLE]:
                if imp.confidence >= self.AUTO_APPLY_CONFIDENCE:
                    if await self._validate_improvement(imp):
                        if await self._apply_improvement(imp):
                            applied.append(imp)
                            logger.info(
                                f"[EVOLVE] Applied: {imp.description[:50]}..."
                            )
            
            logger.info(f"[EVOLVE] Applied {len(applied)} improvements")
            
            return EvolutionResult(
                improvements_proposed=improvements,
                improvements_applied=applied,
                success=True,
            )
            
        except Exception as e:
            logger.error(f"[EVOLVE] Evolution failed: {e}")
            return EvolutionResult(
                success=False,
            )
    
    async def _get_metrics(self) -> Dict[str, Any]:
        """Obtiene metricas del sistema.
        
        Returns:
            Diccionario con metricas
        """
        if self.memory is None:
            return {"status": "memory_unavailable"}
        
        try:
            return await self.memory.get_metrics()
        except Exception as e:
            logger.warning(f"Could not get metrics: {e}")
            return {"error": str(e)}
    
    async def _get_recent_errors(self) -> List[str]:
        """Obtiene errores recientes.
        
        Returns:
            Lista de errores
        """
        if self.memory is None:
            return []
        
        try:
            state = await self.memory.get_state()
            return state.errors_recent
        except Exception as e:
            logger.warning(f"Could not get errors: {e}")
            return []
    
    async def _get_code_context(self, errors: List[str]) -> str:
        """Obtiene contexto de codigo relevante.
        
        Analiza errores para identificar archivos relevantes
        y extrae fragmentos de codigo.
        
        Args:
            errors: Lista de errores recientes
            
        Returns:
            Fragmentos de codigo como string
        """
        # Identificar archivos mencionados en errores
        import re
        
        files_mentioned = set()
        for error in errors:
            # Buscar patrones de archivos Python
            matches = re.findall(r'[\w/]+\.py', error)
            files_mentioned.update(matches)
        
        if not files_mentioned:
            return "No specific files identified from errors."
        
        # Por seguridad, solo incluir archivos del sistema GENESIS
        context_parts = []
        for file in list(files_mentioned)[:3]:  # Max 3 archivos
            if "genesis" in file.lower():
                context_parts.append(f"# File: {file}")
                context_parts.append("# [Code content would be here]")
        
        return "\n\n".join(context_parts) if context_parts else "No GENESIS files in errors."
    
    async def _propose_improvements(
        self,
        metrics: Dict[str, Any],
        errors: List[str],
        code_context: str,
    ) -> List[Improvement]:
        """Propone mejoras basadas en analisis.
        
        Args:
            metrics: Metricas del sistema
            errors: Errores recientes
            code_context: Contexto de codigo
            
        Returns:
            Lista de mejoras propuestas
        """
        if self.think is None:
            logger.warning("[EVOLVE] ThinkModule not available")
            return []
        
        import json
        
        prompt = self.EVOLUTION_PROMPT.format(
            metrics=json.dumps(metrics, indent=2),
            errors=json.dumps(errors[:10], indent=2),  # Limitar errores
            code_context=code_context[:2000],  # Limitar contexto
        )
        
        try:
            response = await self.think.agent.run(prompt)
            
            # Parsear respuesta
            data = self._parse_response(response)
            
            improvements = []
            for imp_data in data.get("improvements", []):
                improvements.append(Improvement(
                    file=imp_data.get("file", ""),
                    description=imp_data.get("description", ""),
                    code=imp_data.get("code", ""),
                    confidence=imp_data.get("confidence", 0.5),
                    impact=imp_data.get("impact", "medium"),
                ))
            
            return improvements
            
        except Exception as e:
            logger.error(f"[EVOLVE] Failed to propose improvements: {e}")
            return []
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parsea respuesta JSON de Gemini.
        
        Args:
            response: Respuesta raw
            
        Returns:
            Diccionario parseado
        """
        import json
        import re
        
        # Intentar parsear directamente
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Buscar bloque JSON
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        return {"improvements": []}
    
    async def _validate_improvement(self, improvement: Improvement) -> bool:
        """Valida que una mejora es segura de aplicar.
        
        Args:
            improvement: Mejora a validar
            
        Returns:
            True si es segura
        """
        # Verificar que el codigo es valido
        try:
            ast.parse(improvement.code)
        except SyntaxError as e:
            logger.warning(f"[EVOLVE] Invalid syntax in improvement: {e}")
            return False
        
        # Verificar que el archivo objetivo es del sistema GENESIS
        if not any(
            pattern in improvement.file.lower()
            for pattern in ["genesis", "agents", "core", "cloud"]
        ):
            logger.warning(f"[EVOLVE] Target file not in allowed paths: {improvement.file}")
            return False
        
        # Verificar que no es un archivo critico
        critical_files = ["__init__.py", "core.py", "config.py"]
        if any(cf in improvement.file for cf in critical_files):
            # Solo permitir con alta confianza
            if improvement.confidence < 0.9:
                logger.warning(f"[EVOLVE] Critical file requires higher confidence")
                return False
        
        return True
    
    async def _apply_improvement(self, improvement: Improvement) -> bool:
        """Aplica una mejora al sistema.
        
        Args:
            improvement: Mejora a aplicar
            
        Returns:
            True si se aplico exitosamente
        """
        import os
        
        try:
            # Crear backup
            if os.path.exists(improvement.file):
                backup_path = f"{improvement.file}.backup.{self._evolution_count}"
                with open(improvement.file, "r") as f:
                    original = f.read()
                with open(backup_path, "w") as f:
                    f.write(original)
                logger.debug(f"[EVOLVE] Created backup: {backup_path}")
            
            # Escribir nuevo codigo
            os.makedirs(os.path.dirname(improvement.file), exist_ok=True)
            with open(improvement.file, "w") as f:
                f.write(improvement.code)
            
            logger.info(f"[EVOLVE] Applied improvement to: {improvement.file}")
            
            # Registrar en memoria
            if self.memory:
                await self.memory.store_agent(
                    f"evolution_{self._evolution_count}",
                    {
                        "type": "evolution",
                        "file": improvement.file,
                        "description": improvement.description,
                        "confidence": improvement.confidence,
                    },
                )
            
            return True
            
        except Exception as e:
            logger.error(f"[EVOLVE] Failed to apply improvement: {e}")
            return False
    
    def get_evolution_count(self) -> int:
        """Retorna numero de evoluciones ejecutadas.
        
        Returns:
            Contador de evoluciones
        """
        return self._evolution_count
{%- endif %}
