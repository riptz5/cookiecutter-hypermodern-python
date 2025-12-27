#!/usr/bin/env python3
"""Complete validation pipeline: Tests + Template + Hooks.

Run this before committing to ensure everything passes.
"""
import subprocess
import sys
from pathlib import Path


class CompleteValidator:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.passed = []
        self.failed = []
    
    def run_command(self, name: str, command: list, cwd=None) -> bool:
        """Run a command and track result."""
        print(f"\n{'─'*70}")
        print(f"🔍 {name}...")
        print(f"{'─'*70}")
        
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print(result.stdout)
                print(f"✅ {name}: PASSED")
                self.passed.append(name)
                return True
            else:
                print(result.stderr or result.stdout)
                print(f"❌ {name}: FAILED")
                self.failed.append(name)
                return False
        except subprocess.TimeoutExpired:
            print(f"❌ {name}: TIMEOUT")
            self.failed.append(name)
            return False
        except Exception as e:
            print(f"❌ {name}: ERROR - {e}")
            self.failed.append(name)
            return False
    
    def run_all(self) -> bool:
        """Run all validation steps."""
        print("\n" + "="*70)
        print("COMPLETE VALIDATION PIPELINE")
        print("="*70)
        print(f"Project: {self.project_root}")
        print(f"Steps: 4 (tests, template, hooks, linting)")
        
        # Step 1: Run tests
        tests_ok = self.run_command(
            "1. Unit Tests",
            ["python3", "-m", "pytest", "tests/", "-v", "--tb=short"]
        )
        
        # Step 2: Validate template
        template_ok = self.run_command(
            "2. Template Validation",
            ["python3", "tools/validate_template.py"]
        )
        
        # Step 3: Check hooks
        hooks_ok = self.run_command(
            "3. Hook Status",
            ["python3", "tools/hook_monitor.py"]
        )
        
        # Step 4: Linting (if possible)
        print(f"\n{'─'*70}")
        print(f"🔍 4. Linting...")
        print(f"{'─'*70}")
        try:
            result = subprocess.run(
                ["python3", "-m", "ruff", "check", "."],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                print("✅ 4. Linting: PASSED")
                self.passed.append("Linting")
            else:
                print(result.stdout)
                print("⚠️  4. Linting: WARNINGS (non-blocking)")
        except FileNotFoundError:
            print("⚠️  4. Linting: ruff not installed (skipping)")
        except Exception as e:
            print(f"⚠️  4. Linting: {e} (non-blocking)")
        
        # Summary
        self.print_summary()
        
        # Return success if critical steps passed
        return tests_ok and template_ok and hooks_ok
    
    def print_summary(self):
        """Print summary report."""
        print("\n" + "="*70)
        print("VALIDATION SUMMARY")
        print("="*70)
        
        print(f"\n✅ PASSED ({len(self.passed)}):")
        for item in self.passed:
            print(f"   ✓ {item}")
        
        if self.failed:
            print(f"\n❌ FAILED ({len(self.failed)}):")
            for item in self.failed:
                print(f"   ✗ {item}")
        
        total = len(self.passed) + len(self.failed)
        rate = (len(self.passed) / total * 100) if total > 0 else 0
        
        print(f"\n{'─'*70}")
        print(f"Success Rate: {len(self.passed)}/{total} ({rate:.0f}%)")
        
        if not self.failed:
            print("\n🎉 ALL VALIDATIONS PASSED!")
            print("   You're ready to commit and push.")
        else:
            print("\n⚠️  SOME VALIDATIONS FAILED")
            print("   Fix the issues and run this script again.")
        
        print("="*70 + "\n")


def main():
    validator = CompleteValidator()
    success = validator.run_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
