"""Validate cookiecutter template generation."""
import subprocess
import sys
from pathlib import Path


def validate_template():
    """Run full template validation."""
    errors = []
    
    # Step 1: Generate project
    print("Step 1: Generating test project...")
    try:
        subprocess.run(
            ["cookiecutter", ".", "--no-input", "--overwrite-if-exists"],
            check=True,
            capture_output=True,
        )
        print("  ✓ Project generated")
    except subprocess.CalledProcessError as e:
        errors.append(f"Failed to generate project: {e.stderr.decode()}")
        return errors
    
    project_path = Path("hypermodern-python")
    if not project_path.exists():
        errors.append("Generated project directory not found")
        return errors
    
    # Step 2: Verify TOML is valid
    print("Step 2: Verifying TOML...")
    pyproject = project_path / "pyproject.toml"
    if pyproject.exists():
        try:
            # Try tomllib first (Python 3.11+)
            try:
                import tomllib
                with open(pyproject, "rb") as f:
                    tomllib.load(f)
            except ImportError:
                # Fallback to tomli
                import tomli
                with open(pyproject, "rb") as f:
                    tomli.load(f)
            print("  ✓ TOML is valid")
        except Exception as e:
            errors.append(f"Invalid TOML: {e}")
    else:
        errors.append("pyproject.toml not found")
    
    # Step 3: Verify Python syntax
    print("Step 3: Verifying Python syntax...")
    src_path = project_path / "src"
    if src_path.exists():
        python_files = list(src_path.rglob("*.py"))
        for py_file in python_files:
            try:
                compile(py_file.read_text(), str(py_file), "exec")
            except SyntaxError as e:
                errors.append(f"Syntax error in {py_file}: {e}")
        print(f"  ✓ {len(python_files)} Python files validated")
    else:
        errors.append("src directory not found")
    
    # Step 4: Check for unrendered Jinja
    print("Step 4: Checking for Jinja artifacts...")
    try:
        result = subprocess.run(
            ["grep", "-r", "{{cookiecutter", str(project_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            errors.append("Found unrendered Jinja template artifacts")
        else:
            print("  ✓ No Jinja artifacts found")
    except FileNotFoundError:
        # grep not available, use Python
        jinja_found = False
        for file_path in project_path.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith("."):
                try:
                    content = file_path.read_text()
                    if "{{cookiecutter" in content:
                        errors.append(f"Jinja artifact in {file_path}")
                        jinja_found = True
                except (UnicodeDecodeError, PermissionError):
                    pass
        if not jinja_found:
            print("  ✓ No Jinja artifacts found")
    
    # Step 5: Clean up
    print("Step 5: Cleaning up...")
    # Don't clean up automatically - let user decide
    
    return errors


if __name__ == "__main__":
    errors = validate_template()
    if errors:
        print("\n❌ Validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("\n✅ All validation checks passed!")
        sys.exit(0)
