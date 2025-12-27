# Propuesta de Cambios a AGENTS.md

## Análisis: ¿Qué fue diferente del proceso requerido?

### ❌ Lo que NO seguí correctamente:

1. **"Implement + Test" juntos**: 
   - ❌ Escribí el código primero (`tools/resolve-issues.py`)
   - ❌ Escribí los tests DESPUÉS (`tests/test_resolve_issues.py`)
   - ✅ Debería haberlos escrito juntos

2. **Validación antes de presentar**:
   - ❌ No validé el template antes de mostrar al usuario
   - ❌ No ejecuté los checks de validación
   - ✅ Debería haber validado ANTES de presentar

3. **Verificación funcional**:
   - ❌ No probé que el código realmente funcionara
   - ❌ No ejecuté los tests
   - ✅ Debería haber verificado que funciona

4. **Proceso completo**:
   - ❌ Me detuve en "implementar" sin completar "validate" y "refine"
   - ✅ Debería haber seguido todos los pasos: Understand → Plan → Implement+Test → Validate → Refine

### ✅ Lo que SÍ seguí:

1. ✅ Leí AGENTS.md completamente
2. ✅ Creé el código
3. ✅ Creé los tests (aunque tarde)
4. ✅ Validé el template (aunque tarde)

## Cambios Propuestos a AGENTS.md

### 1. Agregar sección sobre tests para tools/

**Problema**: AGENTS.md menciona tests pero no especifica dónde van los tests para código en `tools/` (nivel raíz del template).

**Propuesta**: Agregar después de la sección "Testing & Verification":

```markdown
### Testing Tools and Scripts

Tools and scripts in the root `tools/` directory should have corresponding tests in `tests/`:

- `tools/resolve-issues.py` → `tests/test_resolve_issues.py`
- `tools/prepare-github-release.py` → `tests/test_prepare_github_release.py`
- etc.

These tests follow the same 100% coverage requirement and should mock external dependencies (GitHub API, git commands, etc.).
```

### 2. Clarificar el proceso de validación

**Problema**: La sección "Validating Templates" asume Python 3.11+ (tomllib) pero el proyecto soporta Python 3.7+.

**Propuesta**: Actualizar la sección "Validating Templates":

```markdown
## Validating Templates

Before committing changes to template files, validate locally:

```bash
# Step 1: Generate a test project (overwrite if exists)
cookiecutter . --no-input --overwrite-if-exists

# Step 2: Verify TOML is valid
# For Python 3.11+: use tomllib
python3 -c "import tomllib; tomllib.load(open('hypermodern-python/pyproject.toml', 'rb'))"
# For Python <3.11: use tomli (install with: pip install tomli)
python3 -c "import tomli; tomli.load(open('hypermodern-python/pyproject.toml', 'rb'))"

# Step 3: Verify Python syntax
find hypermodern-python/src -name "*.py" -exec python3 -m py_compile {} \;

# Step 4: Check for unrendered Jinja
grep -r "{{cookiecutter" hypermodern-python/ && echo "ERROR" || echo "OK"

# Step 5: Clean up (optional)
rm -rf hypermodern-python
```

**Alternative**: Use the validation script:
```bash
python3 tools/validate_template.py
```
```

### 3. Agregar paso explícito de "Verificar que funciona"

**Problema**: El proceso "Thinking Process" no menciona explícitamente verificar que el código funciona.

**Propuesta**: Actualizar "Thinking Process":

```markdown
### Thinking Process
1. **Understand**: Read `AGENTS.md` and related file context.
2. **Plan**: Draft a change in your scratchpad or `<thinking>` block.
3. **Implement + Test**: Write code AND tests together (see `.agent/procedures/TESTING_PROCEDURE.md`).
4. **Verify**: Run tests and verify the code actually works:
   - Execute tests: `python3 -m pytest tests/` (or equivalent)
   - Run the code manually if applicable
   - Verify no syntax errors or import issues
5. **Validate**: Run the validation checklist BEFORE committing:
   - Generate template project
   - Verify TOML/Python syntax
   - Check for Jinja artifacts
6. **Refine**: If tests fail or validation fails, fix *before* presenting to the user.
7. **Present**: Only present to user after ALL checks pass.
```

### 4. Agregar checklist explícito antes de presentar

**Propuesta**: Agregar nueva sección:

```markdown
## Pre-Presentation Checklist

Before presenting work to the user, verify:

- [ ] Code implemented
- [ ] Tests written (100% coverage)
- [ ] Tests pass (`python3 -m pytest tests/` or equivalent)
- [ ] Template generates successfully (`cookiecutter . --no-input`)
- [ ] TOML is valid (no parse errors)
- [ ] Python syntax is valid (no compilation errors)
- [ ] No Jinja artifacts in generated project
- [ ] Code actually works (manual test if applicable)
- [ ] All linter checks pass
- [ ] Documentation updated if needed

**If ANY check fails, FIX IT before presenting.**
```

### 5. Clarificar diferencia entre "template code" y "tools code"

**Propuesta**: Agregar después de "Two Levels: Template vs Generated Project":

```markdown
### Code Locations

This repository has three types of code:

1. **Template code** (`{{cookiecutter.project_name}}/`): Jinja2 templates that become the generated project
   - Tests go in: `{{cookiecutter.project_name}}/tests/`
   - Validation: Must generate valid project

2. **Tools code** (`tools/`): Python scripts for template development
   - Tests go in: `tests/` (root level)
   - Validation: Must work in template repository context

3. **Template repository code** (root level): Configuration, workflows, etc.
   - Usually no tests needed (configuration files)
   - Validation: Must not break template generation
```

## Resumen de Cambios

1. ✅ Agregar sección sobre tests para `tools/`
2. ✅ Clarificar validación de templates (soporte Python 3.7+)
3. ✅ Agregar paso explícito de "Verificar que funciona"
4. ✅ Agregar checklist pre-presentación
5. ✅ Clarificar diferencia entre tipos de código

Estos cambios harán el proceso más claro y evitarán que los agentes se salten pasos.
