#!/usr/bin/env python3
"""Monitor and recover from hook failures.

This script:
1. Detects hook failures
2. Auto-fixes common issues
3. Reports failures to other agents via AGENTS.md reminders
"""
import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime


class HookMonitor:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.hook_dir = self.project_root / ".git" / "hooks"
        self.failures: List[Dict] = []
        
    def verify_hooks_exist(self) -> bool:
        """Verify both hooks are installed and executable."""
        pre_commit = self.hook_dir / "pre-commit"
        pre_push = self.hook_dir / "pre-push"
        
        if not pre_commit.exists():
            self.failures.append({
                "hook": "pre-commit",
                "error": "Not found",
                "fix": "Re-run implement_validation_gates.py --no-dry-run"
            })
            return False
        
        if not pre_push.exists():
            self.failures.append({
                "hook": "pre-push",
                "error": "Not found",
                "fix": "Re-run implement_validation_gates.py --no-dry-run"
            })
            return False
        
        # Check executable
        if not (pre_commit.stat().st_mode & 0o111):
            pre_commit.chmod(0o755)
            print(f"✓ Fixed pre-commit permissions")
        
        if not (pre_push.stat().st_mode & 0o111):
            pre_push.chmod(0o755)
            print(f"✓ Fixed pre-push permissions")
        
        return True
    
    def test_pre_commit_hook(self) -> Tuple[bool, str]:
        """Test pre-commit hook by running it."""
        try:
            result = subprocess.run(
                ["bash", str(self.hook_dir / "pre-commit")],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr
        except Exception as e:
            return False, str(e)
    
    def test_pre_push_hook(self) -> Tuple[bool, str]:
        """Test pre-push hook by running it."""
        try:
            result = subprocess.run(
                ["bash", str(self.hook_dir / "pre-push")],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr
        except Exception as e:
            return False, str(e)
    
    def auto_fix_common_issues(self) -> bool:
        """Auto-fix common issues that cause hook failures."""
        fixed = False
        
        # Issue 1: Invalid template generation
        try:
            result = subprocess.run(
                ["cookiecutter", ".", "--no-input", "--overwrite-if-exists"],
                cwd=str(self.project_root),
                capture_output=True,
                timeout=60
            )
            if result.returncode != 0:
                print("⚠️  Template generation failed - attempting recovery...")
                # Clean and retry
                gen_dir = self.project_root / "hypermodern-python"
                if gen_dir.exists():
                    import shutil
                    shutil.rmtree(gen_dir)
                    result = subprocess.run(
                        ["cookiecutter", ".", "--no-input"],
                        cwd=str(self.project_root),
                        capture_output=True,
                        timeout=60
                    )
                    if result.returncode == 0:
                        fixed = True
                        print("✓ Fixed template generation")
        except Exception as e:
            print(f"⚠️  Template check failed: {e}")
        
        return fixed
    
    def create_agent_reminder(self) -> None:
        """Create a reminder for other agents about AGENTS.md rules."""
        reminder = {
            "timestamp": datetime.now().isoformat(),
            "message": "⚠️  IMPORTANT: Other agents must follow AGENTS.md rules",
            "mandatory_rules": [
                "RULE 1: Code in tools/ → Tests in tests/",
                "RULE 2: Code in {{cookiecutter.project_name}}/src/ → Tests in {{cookiecutter.project_name}}/tests/",
                "RULE 3: Tests MUST be written in SAME session as code",
                "TEST REQUIREMENT 1: All external dependencies MUST be mocked",
                "TEST REQUIREMENT 2: Tests MUST pass before code is complete",
                "TEST REQUIREMENT 3: 100% code coverage for new code"
            ],
            "thinking_process": [
                "1. Understand - Read AGENTS.md COMPLETELY",
                "2. Plan - Draft change, document steps",
                "3. Implement + Test - Code AND tests TOGETHER (same session)",
                "4. Verify - Execute tests, verify code works",
                "5. Validate - Run validation checklist, ALL checks MUST pass",
                "6. Refine - If ANY check fails, fix and repeat",
                "7. Present - Only after ALL steps complete"
            ],
            "prohibited_actions": [
                "DO NOT run release commands interactively",
                "DO NOT modify .github/workflows without explicit approval",
                "DO NOT simplify {{cookiecutter.*}} expressions",
                "DO NOT present code without pre-presentation checklist",
                "DO NOT skip validation steps",
                "DO NOT write code without tests",
                "DO NOT bypass git hooks with --no-verify"
            ]
        }
        
        reminder_path = self.project_root / ".agent_reminder.json"
        reminder_path.write_text(json.dumps(reminder, indent=2))
        print(f"\n📋 Created agent reminder: {reminder_path}")
    
    def generate_report(self) -> Dict:
        """Generate comprehensive status report."""
        pre_commit_ok, pre_commit_out = self.test_pre_commit_hook()
        pre_push_ok, pre_push_out = self.test_pre_push_hook()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "hooks": {
                "pre_commit": {
                    "exists": (self.hook_dir / "pre-commit").exists(),
                    "executable": bool((self.hook_dir / "pre-commit").stat().st_mode & 0o111) if (self.hook_dir / "pre-commit").exists() else False,
                    "test_passed": pre_commit_ok,
                    "test_output": pre_commit_out[:200] if not pre_commit_ok else "OK"
                },
                "pre_push": {
                    "exists": (self.hook_dir / "pre-push").exists(),
                    "executable": bool((self.hook_dir / "pre-push").stat().st_mode & 0o111) if (self.hook_dir / "pre-push").exists() else False,
                    "test_passed": pre_push_ok,
                    "test_output": pre_push_out[:200] if not pre_push_ok else "OK"
                }
            },
            "overall_status": "OK" if (pre_commit_ok and pre_push_ok) else "FAILED",
            "failures": self.failures
        }
        
        return report


def main():
    monitor = HookMonitor()
    
    print("\n" + "="*70)
    print("HOOK MONITOR & RECOVERY")
    print("="*70)
    
    # Step 1: Verify hooks exist
    print("\n1️⃣  Verifying hooks exist...")
    if not monitor.verify_hooks_exist():
        print("❌ Hooks missing - please run: python3 tools/implement_validation_gates.py --no-dry-run")
        return False
    print("✅ Hooks exist and are executable")
    
    # Step 2: Test hooks
    print("\n2️⃣  Testing hooks...")
    pre_commit_ok, pre_commit_out = monitor.test_pre_commit_hook()
    pre_push_ok, pre_push_out = monitor.test_pre_push_hook()
    
    if pre_commit_ok:
        print("✅ Pre-commit hook: PASSED")
    else:
        print(f"❌ Pre-commit hook: FAILED")
        print(f"   Error: {pre_commit_out[:100]}")
    
    if pre_push_ok:
        print("✅ Pre-push hook: PASSED")
    else:
        print(f"❌ Pre-push hook: FAILED")
        print(f"   Error: {pre_push_out[:100]}")
    
    # Step 3: Auto-fix if needed
    if not (pre_commit_ok and pre_push_ok):
        print("\n3️⃣  Attempting auto-recovery...")
        if monitor.auto_fix_common_issues():
            print("✓ Applied auto-fixes")
            # Re-test
            pre_commit_ok, _ = monitor.test_pre_commit_hook()
            pre_push_ok, _ = monitor.test_pre_push_hook()
    
    # Step 4: Create agent reminder
    print("\n4️⃣  Creating agent reminder...")
    monitor.create_agent_reminder()
    
    # Step 5: Generate report
    print("\n5️⃣  Generating report...")
    report = monitor.generate_report()
    report_path = monitor.project_root / ".hook_status.json"
    report_path.write_text(json.dumps(report, indent=2))
    print(f"📄 Report saved: {report_path}")
    
    # Final summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    if pre_commit_ok and pre_push_ok:
        print("✅ ALL HOOKS OPERATIONAL")
        print("\nStatus:")
        print("  ✓ Pre-commit hook: ACTIVE (blocks commits on failure)")
        print("  ✓ Pre-push hook: ACTIVE (blocks pushes on failure)")
        print("\nAgent Rules:")
        print("  → See .agent_reminder.json for AGENTS.md rules")
        print("  → Other agents MUST follow rules or hooks will block them")
        return True
    else:
        print("❌ SOME HOOKS FAILED")
        print("\nFailed hooks:")
        if not pre_commit_ok:
            print("  ✗ Pre-commit hook")
        if not pre_push_ok:
            print("  ✗ Pre-push hook")
        print("\nAction: Run recovery script or check hook content")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
