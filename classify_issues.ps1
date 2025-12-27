# Classify all issues by priority

# P0 - CRITICAL: Foundation that blocks everything
$p0_issues = @(
    53,  # Base Agent Interface - Foundation for all agents
    52,  # Centralized Configuration - Required for everything
    51,  # CLI - User interface
    2,   # Create agent structure
    3,   # Create .agent/config.yaml
    1    # Unify AGENTS.md
)

# P1 - HIGH: Core systems from forensic analysis
$p1_issues = @(
    41,  # Genesis System - Core autopoietic system
    40,  # Autopoietic Multi-Agent System
    42,  # A2A Protocol - Agent communication
    43,  # Meta Agents System - Self-improving agents
    44,  # Supervisor Agent - LangGraph coordination
    45,  # Worker Agents - ADK workers
    48,  # ADK-LangGraph Bridge - Integration
    49,  # Production Orchestrator - Core orchestration
    54,  # LangGraph Graph Builder
    55,  # LangGraph Nodes
    56,  # LangGraph State Schema
    6,   # Create LangGraph template base
    7,   # Add LangGraph cookiecutter option
    8,   # Create ADK template base
    17,  # Add Google ADK cookiecutter option
    18,  # Implement Google ADK agent scaffolding
    19,  # Add tests for Google ADK
    20,  # Document Google ADK usage
    16,  # Fix: Add missing variable
    14   # Add template validation
)

# P2 - MEDIUM: Important support systems
$p2_issues = @(
    46,  # Cloud Integration - Firestore, Pub/Sub, Cloud Run
    47,  # Agent Factory Pattern
    50,  # Integration Tests
    60,  # Individual Test Suites
    21,  # Add MCP cookiecutter option
    22,  # Implement MCP server scaffolding
    23,  # Implement MCP client scaffolding
    24,  # Add tests for MCP integration
    25,  # Document MCP usage
    26,  # Implement agent bridge pattern
    27,  # Create adapter infrastructure
    28,  # Add tests for bridge and adapters
    29,  # Document bridge and adapters
    30,  # Add agent observability
    31,  # Add agent testing utilities
    32,  # Improve agent configuration
    33,  # Add agent CLI commands
    34,  # Create comprehensive examples
    35,  # Performance optimization
    36,  # Security hardening
    37,  # Final documentation pass
    58,  # Update Dependencies
    57,  # Update Post-Generation Hook
    59,  # Update GCP Discovery Example
    4,   # Update Python to 3.12
    5,   # Add LangGraph cookiecutter option
    9,   # Bridge design RFC
    10,  # Implement bridge.py
    11,  # Create deployment workflow
    12  # Create MCP Server deployment
)

# P3 - LOW: Future innovations and nice-to-have
$p3_issues = @(
    61,  # Agent-Based Testing Framework
    62,  # Self-Healing Infrastructure
    63,  # Multiverse Testing
    64,  # Evolutionary Testing
    65,  # AI-Powered Debugging
    66,  # Temporal Code Analysis
    67,  # Proactive Security Scanning
    68,  # Dynamic Documentation Generation
    69,  # Quantum Problem Solving
    70,  # Cross-Project Learning
    71,  # Plugin Architecture Evolution
    72,  # Graph-Based Dependency Resolution
    73,  # Distributed Agent Execution
    74,  # Zero-Trust Protocol
    75,  # Blue-Green Deployment
    76,  # AI Code Completion
    77,  # Contextual Code Suggestions
    78,  # Refactoring Assistant
    79,  # Code Smell Detection
    80  # API Design Validation
)

Write-Output "Classifying issues by priority..."
Write-Output "P0 (CRITICAL): $($p0_issues.Count) issues"
Write-Output "P1 (HIGH): $($p1_issues.Count) issues"
Write-Output "P2 (MEDIUM): $($p2_issues.Count) issues"
Write-Output "P3 (LOW): $($p3_issues.Count) issues"
Write-Output ""

# Add P0 labels
foreach ($issue in $p0_issues) {
    gh issue edit $issue --add-label "priority:p0" 2>&1 | Out-Null
    Write-Output "P0: #$issue"
}

# Add P1 labels
foreach ($issue in $p1_issues) {
    gh issue edit $issue --add-label "priority:p1" 2>&1 | Out-Null
    Write-Output "P1: #$issue"
}

# Add P2 labels
foreach ($issue in $p2_issues) {
    gh issue edit $issue --add-label "priority:p2" 2>&1 | Out-Null
    Write-Output "P2: #$issue"
}

# Add P3 labels
foreach ($issue in $p3_issues) {
    gh issue edit $issue --add-label "priority:p3" 2>&1 | Out-Null
    Write-Output "P3: #$issue"
}

Write-Output ""
Write-Output "=== CLASSIFICATION COMPLETE ==="
