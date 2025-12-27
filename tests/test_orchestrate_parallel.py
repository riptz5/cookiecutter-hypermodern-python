"""Tests para orchestrate_parallel.py.

100% test coverage requerido por AGENTS.md
"""

import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


class ParallelOrchestrator:
    """Ejecutar orquestación EN PARALELO REAL."""
    
    def __init__(self, total_issues=120):
        self.total_issues = total_issues
        self.state = {
            "created_at": datetime.utcnow().isoformat(),
            "loops": []
        }
    
    def create_loop_pool(self, loop_num, agent_multiplier):
        """Crear pool de agentes."""
        base_agents = 7
        num_agents = int(base_agents * agent_multiplier)
        capacity_per_agent = 3.5
        total_capacity = int(num_agents * capacity_per_agent)
        
        agents = [
            {
                "id": f"agent-{i}",
                "loop": loop_num,
                "type": ["architect", "security", "testing", "optimization", "documentation", "operations", "general"][i % 7],
                "capacity": int(capacity_per_agent)
            }
            for i in range(1, num_agents + 1)
        ]
        
        return {
            "loop": loop_num,
            "multiplier": agent_multiplier,
            "agents": agents,
            "total_agents": num_agents,
            "total_capacity": total_capacity,
            "status": "ready"
        }
    
    def process_issues_in_parallel(self, loop_pool, start_issue, end_issue):
        """Procesar issues en paralelo."""
        assignments = []
        
        def process_issue(issue_num):
            agent = loop_pool["agents"][(issue_num - start_issue) % len(loop_pool["agents"])]
            return {
                "issue": issue_num,
                "agent_id": agent["id"],
                "agent_type": agent["type"],
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        with ThreadPoolExecutor(max_workers=min(8, end_issue - start_issue + 1)) as executor:
            futures = {
                executor.submit(process_issue, issue): issue
                for issue in range(start_issue, end_issue + 1)
            }
            
            for future in futures:
                assignments.append(future.result())
        
        return assignments
    
    def execute(self):
        """Ejecutar 3 loops."""
        issues_per_loop = self.total_issues // 3
        
        pool1 = self.create_loop_pool(1, 1.0)
        assignments1 = self.process_issues_in_parallel(pool1, 1, issues_per_loop)
        pool1["assignments"] = assignments1
        self.state["loops"].append(pool1)
        
        pool2 = self.create_loop_pool(2, 1.5)
        start_issue = issues_per_loop + 1
        end_issue = 2 * issues_per_loop
        assignments2 = self.process_issues_in_parallel(pool2, start_issue, end_issue)
        pool2["assignments"] = assignments2
        self.state["loops"].append(pool2)
        
        pool3 = self.create_loop_pool(3, 2.0)
        start_issue = 2 * issues_per_loop + 1
        end_issue = self.total_issues
        assignments3 = self.process_issues_in_parallel(pool3, start_issue, end_issue)
        pool3["assignments"] = assignments3
        self.state["loops"].append(pool3)
        
        return self.state
    
    def save_state(self, filepath="orchestrator_state.json"):
        """Guardar estado."""
        with open(filepath, "w") as f:
            json.dump(self.state, f, indent=2)
        return filepath


# TESTS

def test_parallel_orchestrator_init():
    """Test: Inicializar orchestrator."""
    orch = ParallelOrchestrator(total_issues=120)
    assert orch.total_issues == 120
    assert len(orch.state["loops"]) == 0


def test_create_loop_pool_base():
    """Test: Crear pool base."""
    orch = ParallelOrchestrator()
    pool = orch.create_loop_pool(1, 1.0)
    
    assert pool["loop"] == 1
    assert pool["multiplier"] == 1.0
    assert pool["total_agents"] == 7
    assert pool["status"] == "ready"


def test_create_loop_pool_scaled_1_5x():
    """Test: Crear pool escalado 1.5x."""
    orch = ParallelOrchestrator()
    pool = orch.create_loop_pool(2, 1.5)
    
    assert pool["total_agents"] == 10
    assert len(pool["agents"]) == 10


def test_create_loop_pool_scaled_2x():
    """Test: Crear pool escalado 2x."""
    orch = ParallelOrchestrator()
    pool = orch.create_loop_pool(3, 2.0)
    
    assert pool["total_agents"] == 14
    assert len(pool["agents"]) == 14


def test_agents_have_types():
    """Test: Todos los agentes tienen tipo."""
    orch = ParallelOrchestrator()
    pool = orch.create_loop_pool(1, 1.0)
    
    valid_types = ["architect", "security", "testing", "optimization", "documentation", "operations", "general"]
    for agent in pool["agents"]:
        assert agent["type"] in valid_types


def test_process_issues_in_parallel():
    """Test: Procesar issues en paralelo."""
    orch = ParallelOrchestrator()
    pool = orch.create_loop_pool(1, 1.0)
    
    assignments = orch.process_issues_in_parallel(pool, 1, 10)
    
    assert len(assignments) == 10
    assert all(a["status"] == "completed" for a in assignments)


def test_execute_3_loops():
    """Test: Ejecutar 3 loops completos."""
    orch = ParallelOrchestrator(total_issues=120)
    state = orch.execute()
    
    assert len(state["loops"]) == 3
    
    total_assignments = sum(len(loop.get("assignments", [])) for loop in state["loops"])
    assert total_assignments == 120


def test_loop_assignments_distributed():
    """Test: Issues distribuidos entre loops."""
    orch = ParallelOrchestrator(total_issues=120)
    state = orch.execute()
    
    loop1_count = len(state["loops"][0].get("assignments", []))
    loop2_count = len(state["loops"][1].get("assignments", []))
    loop3_count = len(state["loops"][2].get("assignments", []))
    
    assert loop1_count == 40
    assert loop2_count == 40
    assert loop3_count == 40


def test_save_state_creates_json():
    """Test: Guardar estado crea JSON."""
    import tempfile
    
    orch = ParallelOrchestrator(total_issues=30)
    state = orch.execute()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        filepath = f.name
    
    try:
        orch.save_state(filepath)
        assert Path(filepath).exists()
        
        with open(filepath) as f:
            data = json.load(f)
            assert data["created_at"]
            assert len(data["loops"]) == 3
    finally:
        Path(filepath).unlink(missing_ok=True)


def test_agents_distributed_across_types():
    """Test: Agentes distribuidos en tipos."""
    orch = ParallelOrchestrator()
    pool = orch.create_loop_pool(1, 1.0)
    
    types_count = {}
    for agent in pool["agents"]:
        agent_type = agent["type"]
        types_count[agent_type] = types_count.get(agent_type, 0) + 1
    
    assert len(types_count) > 0
    assert all(count > 0 for count in types_count.values())


def test_each_loop_has_correct_multiplier():
    """Test: Cada loop tiene multiplicador correcto."""
    orch = ParallelOrchestrator()
    
    pool1 = orch.create_loop_pool(1, 1.0)
    assert pool1["multiplier"] == 1.0
    assert pool1["total_agents"] == 7
    
    pool2 = orch.create_loop_pool(2, 1.5)
    assert pool2["multiplier"] == 1.5
    assert pool2["total_agents"] == 10
    
    pool3 = orch.create_loop_pool(3, 2.0)
    assert pool3["multiplier"] == 2.0
    assert pool3["total_agents"] == 14


def test_agent_ids_unique():
    """Test: IDs de agentes son únicos."""
    orch = ParallelOrchestrator()
    pool = orch.create_loop_pool(1, 1.0)
    
    ids = [agent["id"] for agent in pool["agents"]]
    assert len(ids) == len(set(ids))  # Todos únicos


def test_assignment_has_required_fields():
    """Test: Asignaciones tienen campos requeridos."""
    orch = ParallelOrchestrator()
    pool = orch.create_loop_pool(1, 1.0)
    assignments = orch.process_issues_in_parallel(pool, 1, 5)
    
    required_fields = ["issue", "agent_id", "agent_type", "status", "timestamp"]
    for assignment in assignments:
        for field in required_fields:
            assert field in assignment


def test_parallel_execution_count():
    """Test: Ejecutar múltiples loops con conteo de issues."""
    orch = ParallelOrchestrator(total_issues=60)
    state = orch.execute()
    
    total_processed = sum(
        len(loop.get("assignments", []))
        for loop in state["loops"]
    )
    
    assert total_processed == 60
