#!/usr/bin/env python
"""Agent Orchestrator for Parallel Issue Resolution.

Este script orquesta múltiples sub-agentes para resolver issues en paralelo,
con escalabilidad incremental a través de múltiples loops iterativos.
"""

import asyncio
import json
import os
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

import click


class AgentType(Enum):
    """Tipos de agentes especializados."""
    
    ARCHITECT = "architect"
    SECURITY = "security"
    TESTING = "testing"
    OPTIMIZATION = "optimization"
    DOCUMENTATION = "documentation"
    OPERATIONS = "operations"
    DX = "developer_experience"
    GENERAL = "general"


class IssueStatus(Enum):
    """Estados de un issue."""
    
    UNASSIGNED = "unassigned"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class AgentConfig:
    """Configuración de un sub-agente."""
    
    id: str
    type: AgentType
    specialization: str
    max_parallel_issues: int
    timeout_seconds: int
    capabilities: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "specialization": self.specialization,
            "max_parallel_issues": self.max_parallel_issues,
            "timeout_seconds": self.timeout_seconds,
            "capabilities": self.capabilities,
        }


@dataclass
class IssueAssignment:
    """Asignación de un issue a un agente."""
    
    issue_number: int
    agent_id: str
    status: IssueStatus
    assigned_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class SubAgentPool:
    """Pool de sub-agentes orquestados."""
    
    def __init__(self, loop_number: int = 1, agent_multiplier: float = 1.0):
        """Inicializar el pool de agentes.
        
        Args:
            loop_number: Número del loop iterativo (1, 2, 3)
            agent_multiplier: Multiplicador para escalar agentes (1.0, 1.5, 2.0)
        """
        self.loop_number = loop_number
        self.agent_multiplier = agent_multiplier
        self.agents: Dict[str, AgentConfig] = {}
        self.assignments: List[IssueAssignment] = []
        self.creation_time = datetime.utcnow().isoformat()
        
        self._create_agents()
    
    def _create_agents(self) -> None:
        """Crear agentes especializados con escalabilidad incremental."""
        base_agents = {
            "architect-1": AgentConfig(
                id="architect-1",
                type=AgentType.ARCHITECT,
                specialization="System Architecture & Design Patterns",
                max_parallel_issues=3,
                timeout_seconds=600,
                capabilities=[
                    "architecture-design",
                    "design-patterns",
                    "code-structure",
                    "refactoring",
                ],
            ),
            "security-1": AgentConfig(
                id="security-1",
                type=AgentType.SECURITY,
                specialization="Security & Compliance",
                max_parallel_issues=2,
                timeout_seconds=480,
                capabilities=[
                    "vulnerability-analysis",
                    "compliance-checking",
                    "policy-generation",
                    "threat-modeling",
                ],
            ),
            "testing-1": AgentConfig(
                id="testing-1",
                type=AgentType.TESTING,
                specialization="Testing & Quality Assurance",
                max_parallel_issues=4,
                timeout_seconds=540,
                capabilities=[
                    "test-generation",
                    "coverage-analysis",
                    "test-automation",
                    "test-orchestration",
                ],
            ),
            "optimization-1": AgentConfig(
                id="optimization-1",
                type=AgentType.OPTIMIZATION,
                specialization="Performance & Optimization",
                max_parallel_issues=3,
                timeout_seconds=600,
                capabilities=[
                    "performance-analysis",
                    "code-optimization",
                    "profiling",
                    "bottleneck-detection",
                ],
            ),
            "documentation-1": AgentConfig(
                id="documentation-1",
                type=AgentType.DOCUMENTATION,
                specialization="Documentation & DX",
                max_parallel_issues=5,
                timeout_seconds=360,
                capabilities=[
                    "documentation-generation",
                    "api-design",
                    "example-generation",
                    "tutorial-creation",
                ],
            ),
            "operations-1": AgentConfig(
                id="operations-1",
                type=AgentType.OPERATIONS,
                specialization="DevOps & Deployment",
                max_parallel_issues=3,
                timeout_seconds=540,
                capabilities=[
                    "deployment-automation",
                    "infrastructure-as-code",
                    "ci-cd-pipeline",
                    "monitoring-setup",
                ],
            ),
            "general-1": AgentConfig(
                id="general-1",
                type=AgentType.GENERAL,
                specialization="General Purpose Agent",
                max_parallel_issues=4,
                timeout_seconds=480,
                capabilities=[
                    "code-generation",
                    "bug-fixing",
                    "refactoring",
                    "implementation",
                ],
            ),
        }
        
        # En loops posteriores, crear agentes adicionales
        num_additional = int((self.loop_number - 1) * len(base_agents) * (self.agent_multiplier - 1.0))
        
        # Agregar agentes base
        self.agents.update(base_agents)
        
        # Crear agentes especializados adicionales basado en el loop
        for i in range(2, num_additional + 2):
            for base_id, base_config in base_agents.items():
                if base_id not in [f"{base_config.type.value}-{i}" for _ in range(1)]:
                    new_id = f"{base_config.type.value}-{i}"
                    self.agents[new_id] = AgentConfig(
                        id=new_id,
                        type=base_config.type,
                        specialization=base_config.specialization,
                        max_parallel_issues=base_config.max_parallel_issues,
                        timeout_seconds=base_config.timeout_seconds,
                        capabilities=base_config.capabilities,
                    )
    
    def get_available_agent(self, issue_labels: List[str]) -> Optional[AgentConfig]:
        """Obtener el agente más adecuado para un issue.
        
        Args:
            issue_labels: Labels del issue de GitHub
            
        Returns:
            AgentConfig del agente más adecuado o None
        """
        # Mapeo de labels a tipos de agentes
        label_to_type = {
            "architecture": AgentType.ARCHITECT,
            "design": AgentType.ARCHITECT,
            "security": AgentType.SECURITY,
            "compliance": AgentType.SECURITY,
            "testing": AgentType.TESTING,
            "test": AgentType.TESTING,
            "performance": AgentType.OPTIMIZATION,
            "optimization": AgentType.OPTIMIZATION,
            "documentation": AgentType.DOCUMENTATION,
            "dx": AgentType.DX,
            "devops": AgentType.OPERATIONS,
            "operations": AgentType.OPERATIONS,
        }
        
        # Encontrar tipo de agente más relevante
        preferred_type = None
        for label in issue_labels:
            if label.lower() in label_to_type:
                preferred_type = label_to_type[label.lower()]
                break
        
        # Si no hay match específico, usar general
        if not preferred_type:
            preferred_type = AgentType.GENERAL
        
        # Encontrar agente disponible del tipo preferido
        available = [
            agent for agent in self.agents.values()
            if agent.type == preferred_type
            and self._count_active_assignments(agent.id) < agent.max_parallel_issues
        ]
        
        if available:
            return available[0]
        
        # Fallback a cualquier agente disponible
        available = [
            agent for agent in self.agents.values()
            if self._count_active_assignments(agent.id) < agent.max_parallel_issues
        ]
        
        return available[0] if available else None
    
    def _count_active_assignments(self, agent_id: str) -> int:
        """Contar asignaciones activas de un agente."""
        return sum(
            1 for assignment in self.assignments
            if assignment.agent_id == agent_id
            and assignment.status in (IssueStatus.ASSIGNED, IssueStatus.IN_PROGRESS)
        )
    
    def assign_issue(
        self, issue_number: int, issue_labels: List[str]
    ) -> Optional[IssueAssignment]:
        """Asignar un issue a un agente disponible.
        
        Args:
            issue_number: Número del issue
            issue_labels: Labels del issue
            
        Returns:
            IssueAssignment si exitoso, None si no hay agentes disponibles
        """
        agent = self.get_available_agent(issue_labels)
        
        if not agent:
            return None
        
        assignment = IssueAssignment(
            issue_number=issue_number,
            agent_id=agent.id,
            status=IssueStatus.ASSIGNED,
            assigned_at=datetime.utcnow().isoformat(),
        )
        
        self.assignments.append(assignment)
        return assignment
    
    def mark_in_progress(self, issue_number: int) -> None:
        """Marcar un issue como en progreso."""
        for assignment in self.assignments:
            if assignment.issue_number == issue_number:
                assignment.status = IssueStatus.IN_PROGRESS
                assignment.started_at = datetime.utcnow().isoformat()
                break
    
    def mark_completed(
        self, issue_number: int, result: Optional[Dict] = None
    ) -> None:
        """Marcar un issue como completado."""
        for assignment in self.assignments:
            if assignment.issue_number == issue_number:
                assignment.status = IssueStatus.COMPLETED
                assignment.completed_at = datetime.utcnow().isoformat()
                assignment.result = result
                break
    
    def mark_failed(self, issue_number: int, error: str) -> None:
        """Marcar un issue como fallido."""
        for assignment in self.assignments:
            if assignment.issue_number == issue_number:
                assignment.status = IssueStatus.FAILED
                assignment.completed_at = datetime.utcnow().isoformat()
                assignment.error = error
                break
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtener resumen del estado del pool."""
        total = len(self.assignments)
        completed = sum(1 for a in self.assignments if a.status == IssueStatus.COMPLETED)
        in_progress = sum(1 for a in self.assignments if a.status == IssueStatus.IN_PROGRESS)
        failed = sum(1 for a in self.assignments if a.status == IssueStatus.FAILED)
        
        return {
            "loop_number": self.loop_number,
            "agent_multiplier": self.agent_multiplier,
            "total_agents": len(self.agents),
            "total_assignments": total,
            "completed": completed,
            "in_progress": in_progress,
            "failed": failed,
            "success_rate": (completed / total * 100) if total > 0 else 0,
            "creation_time": self.creation_time,
        }
    
    def to_dict(self) -> Dict:
        """Convertir a diccionario para persistencia."""
        return {
            "loop_number": self.loop_number,
            "agent_multiplier": self.agent_multiplier,
            "agents": {k: v.to_dict() for k, v in self.agents.items()},
            "assignments": [a.to_dict() for a in self.assignments],
            "summary": self.get_summary(),
        }


class Orchestrator:
    """Orquestador principal para múltiples loops."""
    
    def __init__(self, state_file: str = "orchestrator_state.json"):
        """Inicializar el orquestador.
        
        Args:
            state_file: Archivo para persistir estado
        """
        self.state_file = state_file
        self.pools: List[SubAgentPool] = []
        self.load_state()
    
    def create_loop(self, loop_number: int, agent_multiplier: float) -> SubAgentPool:
        """Crear un nuevo loop con pool de agentes.
        
        Args:
            loop_number: Número del loop
            agent_multiplier: Multiplicador de escalabilidad
            
        Returns:
            SubAgentPool creado
        """
        pool = SubAgentPool(loop_number, agent_multiplier)
        self.pools.append(pool)
        self.save_state()
        return pool
    
    def save_state(self) -> None:
        """Guardar estado a archivo."""
        data = {
            "created_at": datetime.utcnow().isoformat(),
            "pools": [pool.to_dict() for pool in self.pools],
        }
        
        with open(self.state_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def load_state(self) -> None:
        """Cargar estado desde archivo."""
        if Path(self.state_file).exists():
            with open(self.state_file, "r") as f:
                # En una implementación real, reconstruir los pools desde el estado
                pass
    
    def get_total_summary(self) -> Dict[str, Any]:
        """Obtener resumen total de todos los loops."""
        total_agents = sum(len(pool.agents) for pool in self.pools)
        total_assignments = sum(len(pool.assignments) for pool in self.pools)
        total_completed = sum(
            len([a for a in pool.assignments if a.status == IssueStatus.COMPLETED])
            for pool in self.pools
        )
        
        return {
            "total_loops": len(self.pools),
            "total_agents_across_all_loops": total_agents,
            "total_assignments": total_assignments,
            "total_completed": total_completed,
            "average_success_rate": (total_completed / total_assignments * 100) if total_assignments > 0 else 0,
            "pools": [pool.get_summary() for pool in self.pools],
        }


# CLI Commands

@click.group()
def cli():
    """Orchestrate sub-agents for parallel issue resolution."""
    pass


@cli.command()
@click.option(
    "--total-issues",
    type=int,
    default=120,
    help="Total number of issues to resolve",
)
@click.option(
    "--output",
    type=click.Path(),
    default="agent_orchestration.json",
    help="Output file for orchestration state",
)
def orchestrate_loops(total_issues: int, output: str) -> None:
    """Execute 3 loops of parallel issue resolution with incremental scaling."""
    
    orchestrator = Orchestrator(output)
    
    # Loop 1: Initial with base agents
    click.secho("\n🔄 LOOP 1: Base Agent Pool", fg="cyan", bold=True)
    pool1 = orchestrator.create_loop(loop_number=1, agent_multiplier=1.0)
    click.echo(f"   Agents created: {len(pool1.agents)}")
    click.echo(f"   Total capacity: {sum(a.max_parallel_issues for a in pool1.agents.values())} parallel issues")
    
    # Simular asignaciones
    issues_per_loop = total_issues // 3
    for i in range(issues_per_loop):
        pool1.assign_issue(i + 1, ["enhancement", "genesis"])
    
    summary1 = pool1.get_summary()
    click.echo(f"   Assigned: {summary1['total_assignments']} issues\n")
    
    # Loop 2: Scale to 1.5x agents
    click.secho("🔄 LOOP 2: Scaled Agent Pool (1.5x)", fg="cyan", bold=True)
    pool2 = orchestrator.create_loop(loop_number=2, agent_multiplier=1.5)
    click.echo(f"   Agents created: {len(pool2.agents)}")
    click.echo(f"   Total capacity: {sum(a.max_parallel_issues for a in pool2.agents.values())} parallel issues")
    
    for i in range(issues_per_loop):
        pool2.assign_issue(issues_per_loop + i + 1, ["enhancement", "genesis"])
    
    summary2 = pool2.get_summary()
    click.echo(f"   Assigned: {summary2['total_assignments']} issues\n")
    
    # Loop 3: Scale to 2x agents
    click.secho("🔄 LOOP 3: Maximum Agent Pool (2x)", fg="cyan", bold=True)
    pool3 = orchestrator.create_loop(loop_number=3, agent_multiplier=2.0)
    click.echo(f"   Agents created: {len(pool3.agents)}")
    click.echo(f"   Total capacity: {sum(a.max_parallel_issues for a in pool3.agents.values())} parallel issues")
    
    remaining = total_issues - (2 * issues_per_loop)
    for i in range(remaining):
        pool3.assign_issue(2 * issues_per_loop + i + 1, ["enhancement", "genesis"])
    
    summary3 = pool3.get_summary()
    click.echo(f"   Assigned: {summary3['total_assignments']} issues\n")
    
    # Total summary
    total = orchestrator.get_total_summary()
    
    click.secho("\n📊 ORCHESTRATION SUMMARY", fg="green", bold=True)
    click.echo(f"   Total Loops: {total['total_loops']}")
    click.echo(f"   Total Agents: {total['total_agents_across_all_loops']}")
    click.echo(f"   Total Issues Assigned: {total['total_assignments']}")
    click.echo(f"   Issues Completed: {total['total_completed']}")
    click.echo(f"   Success Rate: {total['average_success_rate']:.1f}%")
    
    click.secho(f"\n✓ Orchestration state saved to {output}", fg="green")
    orchestrator.save_state()


@cli.command()
@click.option(
    "--state-file",
    type=click.Path(exists=True),
    required=True,
    help="State file to analyze",
)
def analyze_state(state_file: str) -> None:
    """Analyze orchestration state."""
    with open(state_file, "r") as f:
        data = json.load(f)
    
    click.echo(json.dumps(data, indent=2))


if __name__ == "__main__":
    cli(prog_name="agent-orchestrator")
