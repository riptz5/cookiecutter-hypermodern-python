#!/usr/bin/env python3
"""Agent Onboarding: Learn the rules before you work.

This script helps agents understand:
1. AGENTS.md rules
2. Hook system
3. Code location rules
4. Validation checklist
5. Thinking process
"""
import json
from pathlib import Path


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}\n")


def main():
    project_root = Path(__file__).parent.parent
    
    print_section("🎓 AGENT ONBOARDING")
    print("Welcome! Before you work on this repository, you MUST understand:")
    print("1. Code location rules")
    print("2. Test requirements")
    print("3. Validation hooks")
    print("4. Thinking process")
    
    # Section 1: Code Rules
    print_section("📍 CODE LOCATION RULES (MANDATORY)")
    print("""
RULE 1: Code in tools/ → Tests in tests/
  Example: tools/my_tool.py → tests/test_my_tool.py
  
RULE 2: Code in {{cookiecutter.project_name}}/src/ → Tests in template/tests/
  Example: {{cookiecutter.project_name}}/src/mypackage/file.py → {{cookiecutter.project_name}}/tests/test_file.py
  
RULE 3: Tests MUST be written in SAME session as code
  Definition: Same conversation thread, no separate "testing" threads
  Enforcement: Manual verification (automated enforcement coming)
""")
    
    # Section 2: Test Requirements
    print_section("🧪 TEST REQUIREMENTS (MANDATORY)")
    print("""
REQUIREMENT 1: All external dependencies MUST be mocked
  ✓ GitHub API calls → Mock github3/requests
  ✓ Git commands → Mock subprocess.run
  ✓ File system → Mock Path operations if needed
  ✓ Environment variables → Mock os.getenv
  
REQUIREMENT 2: Tests MUST pass before code is complete
  Command: python3 -m pytest tests/
  Result: ALL tests pass, NO failures
  
REQUIREMENT 3: 100% code coverage for new code
  Command: Check coverage with pytest-cov
  Result: NO uncovered lines in new code
""")
    
    # Section 3: 7-Step Process
    print_section("🔄 SEVEN-STEP THINKING PROCESS (MANDATORY)")
    print("""
You MUST follow these steps IN ORDER. Skipping any step = violation.

1. UNDERSTAND
   → Read AGENTS.md COMPLETELY
   → Read all related files
   → Understand the FULL scope
   
2. PLAN
   → Draft change in thinking block
   → Document ALL steps you'll take
   → Get user approval if needed
   
3. IMPLEMENT + TEST
   → Write code AND tests TOGETHER
   → SAME session, not separate
   → NO code without tests
   → NO tests after code
   
4. VERIFY
   → Execute tests
   → Verify code works
   → Fix ALL failures BEFORE proceeding
   
5. VALIDATE
   → Run validation checklist (see below)
   → ALL checks MUST pass
   
6. REFINE
   → If ANY check fails, fix it
   → Repeat validation
   → DO NOT proceed until ALL pass
   
7. PRESENT
   → Only present to user AFTER steps 1-6 complete
   → ALL checks must pass
""")
    
    # Section 4: Validation Checklist
    print_section("✅ PRE-PRESENTATION VALIDATION CHECKLIST")
    print("""
You MUST complete EVERY checkbox before presenting:

- [ ] Code implemented
- [ ] Tests written (100% coverage for new code)
- [ ] Tests pass (python3 -m pytest tests/)
- [ ] Template generates successfully (cookiecutter . --no-input --overwrite-if-exists)
- [ ] TOML is valid (no parse errors)
- [ ] Python syntax is valid (no compilation errors)
- [ ] No Jinja artifacts in generated project
- [ ] Code actually works (manual test if applicable)
- [ ] All linter checks pass
- [ ] Documentation updated if needed
- [ ] Validation checklist (above) completed and ALL steps passed

RULE: If ANY checkbox is unchecked, DO NOT present.
      Fix issues. Re-validate. Present only when ALL checked.
""")
    
    # Section 5: Hook System
    print_section("🔒 AUTOMATED HOOK SYSTEM")
    print("""
This repository has automated validation hooks that BLOCK changes:

PRE-COMMIT HOOK (.git/hooks/pre-commit)
  Runs on: git commit
  Blocks if: Template invalid, TOML invalid, Python syntax bad, Jinja artifacts found
  
PRE-PUSH HOOK (.git/hooks/pre-push)
  Runs on: git push
  Blocks if: Validation incomplete, coverage <100%, compliance failed

IF A HOOK BLOCKS YOU:
  1. Run: python3 tools/hook_monitor.py
  2. Read: .hook_status.json
  3. Fix the issues (code, tests, or validation)
  4. Re-run: python3 tools/validate_template.py
  5. Try again
  
⛔ DO NOT bypass hooks with --no-verify (this violates the process)
""")
    
    # Section 6: Prohibited Actions
    print_section("⛔ PROHIBITED ACTIONS")
    print("""
DO NOT:
  ⛔ Run release commands interactively (nox -s publish-release)
  ⛔ Modify .github/workflows without explicit user approval
  ⛔ Simplify {{cookiecutter.*}} expressions (they're template variables!)
  ⛔ Present code without pre-presentation checklist
  ⛔ Skip validation steps
  ⛔ Write code without tests (same session)
  ⛔ Bypass git hooks with --no-verify
  ⛔ Create unnecessary documents
""")
    
    # Section 7: Verification Commands
    print_section("🔍 VERIFICATION COMMANDS")
    print("""
Before presenting work, run these commands:

# 1. Validate template
python3 tools/validate_template.py

# 2. Run tests
python3 -m pytest tests/

# 3. Check hooks
python3 tools/hook_monitor.py

# 4. Generate project
cookiecutter . --no-input --overwrite-if-exists

# All of the above at once:
python3 tools/validate_template.py && python3 -m pytest tests/ && python3 tools/hook_monitor.py
""")
    
    # Load agent reminder
    reminder_path = project_root / ".agent_reminder.json"
    if reminder_path.exists():
        reminder = json.loads(reminder_path.read_text())
        print_section("📋 AGENT REMINDER (FROM .agent_reminder.json)")
        print(f"Created: {reminder.get('timestamp', 'Unknown')}")
        print("\nMandatory Rules:")
        for rule in reminder.get("mandatory_rules", []):
            print(f"  • {rule}")
    
    # Final checklist
    print_section("✨ BEFORE YOU START CODING")
    print("""
Verify you have:
  ✓ Read AGENTS.md COMPLETELY
  ✓ Read .agent_reminder.json
  ✓ Read .HOOKS_README.md
  ✓ Understood the 7-step process
  ✓ Understood code location rules
  ✓ Understood test requirements
  ✓ Verified hooks are operational (python3 tools/hook_monitor.py)

Ready? Then:
  1. Read the issue/request carefully
  2. Follow the 7-step process
  3. Run validation checklist
  4. Present only when complete
  
Questions? Read AGENTS.md (it's the source of truth).
""")
    
    print("\n" + "="*70)
    print("🎓 ONBOARDING COMPLETE")
    print("="*70)
    print("\nYou're ready to work!")
    print("Remember: 7 steps, mandatory rules, 100% coverage, then present.")


if __name__ == "__main__":
    main()
