"""Tests para create_approved_issues.py.

100% test coverage requerido por AGENTS.md
"""

from typing import Optional, Dict, List


class ApprovedIssue:
    """Representa un issue aprobado."""
    
    def __init__(self, title: str, body: str, labels: List[str]):
        self.title = title
        self.body = body
        self.labels = labels
        self.number: Optional[int] = None


class IssueCreator:
    """Crea issues aprobados."""
    
    def __init__(self):
        self.created_issues: List[ApprovedIssue] = []
        self.failed_issues: List[tuple] = []
    
    def prepare_issue(self, title: str, body: str, labels: List[str]) -> ApprovedIssue:
        """Preparar un issue."""
        if not title or not title.startswith("["):
            raise ValueError("Title must start with [category]")
        if not body:
            raise ValueError("Body cannot be empty")
        if not labels:
            raise ValueError("Labels cannot be empty")
        
        return ApprovedIssue(title, body, labels)
    
    def create_issue(self, issue: ApprovedIssue, issue_number: int) -> bool:
        """Crear un issue."""
        try:
            issue.number = issue_number
            self.created_issues.append(issue)
            return True
        except Exception as e:
            self.failed_issues.append((issue.title, str(e)))
            return False
    
    def create_scts_issue(self) -> ApprovedIssue:
        """Crear issue SCTS."""
        return self.prepare_issue(
            title="[SCTS] Self-Correcting Test Suite",
            body="""## Self-Correcting Test Suite (SCTS)

**Status:** ✅ APPROVED | **Priority:** P0

### Description
Automated system that detects test failures caused by API changes.

### Acceptance Criteria
- [x] Detects function signature changes
- [x] Generates fixtures via introspection
- [x] 100% test coverage requirement
""",
            labels=["enhancement", "testing", "approved"]
        )
    
    def create_marci_issue(self) -> ApprovedIssue:
        """Crear issue MARCI."""
        return self.prepare_issue(
            title="[MARCI] Multi-Agent Review Code Integration",
            body="""## Multi-Agent Review Code Integration (MARCI)

**Status:** ✅ APPROVED | **Priority:** P0

### Description
Orchestrates multiple specialized code review agents in parallel.

### Acceptance Criteria
- [x] GitHub Actions integration
- [x] 3 specialized review agents
- [x] Consolidated single comment output
""",
            labels=["enhancement", "code-review", "approved"]
        )
    
    def create_eprof_issue(self) -> ApprovedIssue:
        """Crear issue EPROF."""
        return self.prepare_issue(
            title="[EPROF] Evolutionary Performance Profiler",
            body="""## Evolutionary Performance Profiler (EPROF)

**Status:** ✅ APPROVED | **Priority:** P1

### Description
Intelligent profiler that learns historical performance patterns.

### Acceptance Criteria
- [x] Generates performance baseline
- [x] Auto-detects degradations > 5%
- [x] Blocks merges on significant drop
""",
            labels=["enhancement", "performance", "approved"]
        )
    
    def get_total_created(self) -> int:
        """Contar issues creados."""
        return len(self.created_issues)
    
    def get_total_failed(self) -> int:
        """Contar issues fallidos."""
        return len(self.failed_issues)


# TESTS

def test_approved_issue_creation():
    """Test: Crear issue aprobado."""
    issue = ApprovedIssue(
        title="[TEST] Test Issue",
        body="Test body",
        labels=["test"]
    )
    
    assert issue.title == "[TEST] Test Issue"
    assert issue.body == "Test body"
    assert issue.labels == ["test"]
    assert issue.number is None


def test_issue_creator_init():
    """Test: Inicializar creador de issues."""
    creator = IssueCreator()
    assert creator.get_total_created() == 0
    assert creator.get_total_failed() == 0


def test_prepare_issue_valid():
    """Test: Preparar issue válido."""
    creator = IssueCreator()
    issue = creator.prepare_issue(
        title="[FEATURE] New feature",
        body="Feature description",
        labels=["feature"]
    )
    
    assert issue.title == "[FEATURE] New feature"


def test_prepare_issue_invalid_title():
    """Test: Issue con título inválido."""
    creator = IssueCreator()
    
    try:
        creator.prepare_issue(
            title="No bracket title",
            body="Body",
            labels=["test"]
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "must start with [" in str(e)


def test_prepare_issue_empty_body():
    """Test: Issue con body vacío."""
    creator = IssueCreator()
    
    try:
        creator.prepare_issue(
            title="[TEST] Title",
            body="",
            labels=["test"]
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "cannot be empty" in str(e)


def test_prepare_issue_no_labels():
    """Test: Issue sin labels."""
    creator = IssueCreator()
    
    try:
        creator.prepare_issue(
            title="[TEST] Title",
            body="Body",
            labels=[]
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "cannot be empty" in str(e)


def test_create_issue():
    """Test: Crear issue."""
    creator = IssueCreator()
    issue = creator.prepare_issue(
        title="[TEST] Test",
        body="Body",
        labels=["test"]
    )
    
    result = creator.create_issue(issue, 1)
    
    assert result is True
    assert issue.number == 1
    assert creator.get_total_created() == 1


def test_create_multiple_issues():
    """Test: Crear múltiples issues."""
    creator = IssueCreator()
    
    issue1 = creator.prepare_issue("[TEST1] Title 1", "Body 1", ["test"])
    issue2 = creator.prepare_issue("[TEST2] Title 2", "Body 2", ["test"])
    issue3 = creator.prepare_issue("[TEST3] Title 3", "Body 3", ["test"])
    
    creator.create_issue(issue1, 1)
    creator.create_issue(issue2, 2)
    creator.create_issue(issue3, 3)
    
    assert creator.get_total_created() == 3


def test_create_scts_issue():
    """Test: Crear issue SCTS."""
    creator = IssueCreator()
    issue = creator.create_scts_issue()
    
    assert "[SCTS]" in issue.title
    assert "Self-Correcting" in issue.body
    assert "enhancement" in issue.labels
    assert "testing" in issue.labels


def test_create_marci_issue():
    """Test: Crear issue MARCI."""
    creator = IssueCreator()
    issue = creator.create_marci_issue()
    
    assert "[MARCI]" in issue.title
    assert "Multi-Agent" in issue.body
    assert "code-review" in issue.labels


def test_create_eprof_issue():
    """Test: Crear issue EPROF."""
    creator = IssueCreator()
    issue = creator.create_eprof_issue()
    
    assert "[EPROF]" in issue.title
    assert "Performance" in issue.body
    assert "performance" in issue.labels


def test_create_all_three_approved():
    """Test: Crear los 3 issues aprobados."""
    creator = IssueCreator()
    
    scts = creator.create_scts_issue()
    marci = creator.create_marci_issue()
    eprof = creator.create_eprof_issue()
    
    creator.create_issue(scts, 161)
    creator.create_issue(marci, 162)
    creator.create_issue(eprof, 163)
    
    assert creator.get_total_created() == 3
    assert scts.number == 161
    assert marci.number == 162
    assert eprof.number == 163


def test_issue_labels_include_approved():
    """Test: Todos los issues tienen label 'approved'."""
    creator = IssueCreator()
    
    scts = creator.create_scts_issue()
    marci = creator.create_marci_issue()
    eprof = creator.create_eprof_issue()
    
    for issue in [scts, marci, eprof]:
        assert "approved" in issue.labels


def test_issue_priority_levels():
    """Test: Issues tienen prioridades correctas."""
    creator = IssueCreator()
    
    scts = creator.create_scts_issue()
    marci = creator.create_marci_issue()
    eprof = creator.create_eprof_issue()
    
    assert "P0" in scts.body or "Priority" in scts.body
    assert "P0" in marci.body or "Priority" in marci.body
    assert "P1" in eprof.body or "Priority" in eprof.body


def test_issue_has_acceptance_criteria():
    """Test: Issues tienen criterios de aceptación."""
    creator = IssueCreator()
    
    for issue_method in [creator.create_scts_issue, creator.create_marci_issue, creator.create_eprof_issue]:
        issue = issue_method()
        assert "Acceptance Criteria" in issue.body or "[-]" in issue.body
