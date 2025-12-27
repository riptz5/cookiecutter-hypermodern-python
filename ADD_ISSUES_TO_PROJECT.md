# Cómo Agregar Issues al Project Board

## 🎯 Problema

Los issues están creados en el repositorio (#17-#38), pero **NO aparecen automáticamente** en el Project Board.

GitHub Projects (v2) requiere agregar los issues manualmente al proyecto.

---

## ✅ Solución 1: Agregar Manualmente (Más Rápido)

### Paso 1: Ir al Project Board
https://github.com/users/riptz5/projects/2/views/1

### Paso 2: Agregar Issues

1. Click en el botón **"+ Add item"** (abajo del proyecto)
2. Buscar por número: `#17`, `#18`, `#19`, etc.
3. Seleccionar cada issue y agregarlo

**Repetir para los issues #17-#38** (22 issues en total)

---

## ✅ Solución 2: Usar GitHub CLI (Requiere Permisos)

### Paso 1: Actualizar Token

```bash
# Salir de la sesión actual
unset GITHUB_TOKEN

# Re-autenticar con permisos adicionales
gh auth login

# Cuando pregunte por scopes, seleccionar:
# - repo (ya lo tienes)
# - workflow (ya lo tienes)
# - project (NUEVO - necesario)
```

### Paso 2: Obtener ID del Proyecto

```bash
gh project list --owner riptz5
```

Esto mostrará algo como:
```
NUMBER  TITLE                           ID
2       Cookiecutter Development        PVT_kwDOABCD1234
```

### Paso 3: Agregar Issues al Proyecto

```bash
# Obtener el ID del proyecto (ejemplo: PVT_kwDOABCD1234)
PROJECT_ID="TU_PROJECT_ID_AQUI"

# Agregar issues #17-#38
for i in {17..38}; do
  gh project item-add $PROJECT_ID --owner riptz5 --url "https://github.com/riptz5/cookiecutter-hypermodern-python/issues/$i"
  echo "✓ Added issue #$i"
done
```

---

## ✅ Solución 3: Usar la Web UI (Bulk Add)

### Opción A: Desde el Proyecto

1. Ve a: https://github.com/users/riptz5/projects/2
2. Click en "⋮" (tres puntos) → "Settings"
3. En "Manage access" → "Workflows"
4. Habilitar "Auto-add items"
5. Seleccionar el repositorio `cookiecutter-hypermodern-python`
6. Configurar: "Add items when they match: is:issue is:open"

Esto agregará automáticamente futuros issues, pero **no los existentes**.

### Opción B: Agregar Existentes

1. Ve al repositorio: https://github.com/riptz5/cookiecutter-hypermodern-python/issues
2. Selecciona múltiples issues (checkbox a la izquierda)
3. Click en "Projects" (arriba)
4. Selecciona tu proyecto
5. Click "Add selected items"

---

## 🚀 Script Automatizado (Cuando tengas permisos)

He creado un script que puedes ejecutar cuando tengas los permisos correctos:

```bash
#!/bin/bash
# add_issues_to_project.sh

# Configuración
PROJECT_NUMBER=2
OWNER="riptz5"
REPO="cookiecutter-hypermodern-python"

echo "🚀 Agregando issues al proyecto..."

# Obtener ID del proyecto
PROJECT_ID=$(gh api graphql -f query="
{
  user(login: \"$OWNER\") {
    projectV2(number: $PROJECT_NUMBER) {
      id
    }
  }
}" --jq '.data.user.projectV2.id')

echo "Project ID: $PROJECT_ID"

# Agregar cada issue
for issue_num in {17..38}; do
  echo "Agregando issue #$issue_num..."
  
  # Obtener ID del issue
  ISSUE_ID=$(gh api graphql -f query="
  {
    repository(owner: \"$OWNER\", name: \"$REPO\") {
      issue(number: $issue_num) {
        id
      }
    }
  }" --jq '.data.repository.issue.id')
  
  # Agregar al proyecto
  gh api graphql -f query="
  mutation {
    addProjectV2ItemById(input: {
      projectId: \"$PROJECT_ID\"
      contentId: \"$ISSUE_ID\"
    }) {
      item {
        id
      }
    }
  }" > /dev/null
  
  echo "✓ Issue #$issue_num agregado"
done

echo ""
echo "✅ Todos los issues agregados al proyecto!"
echo "Ver en: https://github.com/users/$OWNER/projects/$PROJECT_NUMBER"
```

---

## 📋 Lista de Issues a Agregar

Estos son los issues que necesitas agregar al proyecto:

### M0: Foundation
- [x] #38 - ✅ COMPLETADO: Agent Orchestration System

### M1: Google ADK (4 issues)
- [ ] #17 - Add Google ADK cookiecutter option
- [ ] #18 - Implement Google ADK agent scaffolding
- [ ] #19 - Add tests for Google ADK integration
- [ ] #20 - Document Google ADK usage

### M2: MCP Integration (5 issues)
- [ ] #21 - Add MCP cookiecutter option
- [ ] #22 - Implement MCP server scaffolding
- [ ] #23 - Implement MCP client scaffolding
- [ ] #24 - Add tests for MCP integration
- [ ] #25 - Document MCP usage

### M3: Bridge & Adapters (4 issues)
- [ ] #26 - Implement agent bridge pattern
- [ ] #27 - Create adapter infrastructure
- [ ] #28 - Add tests for bridge and adapters
- [ ] #29 - Document bridge and adapter patterns

### M4: Advanced Features (8 issues)
- [ ] #30 - Add agent observability
- [ ] #31 - Add agent testing utilities
- [ ] #32 - Improve agent configuration
- [ ] #33 - Add agent CLI commands
- [ ] #34 - Create comprehensive examples
- [ ] #35 - Performance optimization
- [ ] #36 - Security hardening
- [ ] #37 - Final documentation pass

**Total: 22 issues**

---

## 🎯 Recomendación

**La forma más rápida** es usar la **Solución 1** (manual desde la web):

1. Ve a: https://github.com/users/riptz5/projects/2/views/1
2. Click "+ Add item"
3. Escribe `#17` y presiona Enter
4. Repite para #18, #19, ... #38

Toma ~2-3 minutos agregar todos los issues.

---

## ❓ Por Qué No Se Agregan Automáticamente

GitHub Projects (v2) son independientes de los repositorios. Los issues se crean en el repo, pero **no se agregan automáticamente** al proyecto a menos que:

1. Configures "Auto-add" en el proyecto (solo para futuros issues)
2. Los agregues manualmente
3. Uses la API/CLI con permisos de `project`

---

## 📞 Necesitas Ayuda?

Si tienes problemas:
1. Verifica que los issues existen: https://github.com/riptz5/cookiecutter-hypermodern-python/issues
2. Verifica que tienes acceso al proyecto: https://github.com/users/riptz5/projects/2
3. Si usas CLI, asegúrate de tener permisos `read:project` y `write:project`

---

**Última actualización**: Diciembre 26, 2025
