#!/bin/bash
set -e

# Configuración
PROJECT_NUMBER=2
OWNER="riptz5"
REPO="cookiecutter-hypermodern-python"

echo "🚀 Agregando issues al proyecto..."
echo ""

# Verificar autenticación
if ! gh auth status > /dev/null 2>&1; then
    echo "❌ No estás autenticado en GitHub CLI"
    echo "   Ejecuta: gh auth login"
    exit 1
fi

# Obtener ID del proyecto
echo "📋 Obteniendo ID del proyecto..."
PROJECT_ID=$(gh api graphql -f query="
{
  user(login: \"$OWNER\") {
    projectV2(number: $PROJECT_NUMBER) {
      id
      title
    }
  }
}" --jq '.data.user.projectV2.id' 2>&1)

if [ -z "$PROJECT_ID" ] || [[ "$PROJECT_ID" == *"error"* ]]; then
    echo ""
    echo "❌ Error: No se pudo obtener el ID del proyecto"
    echo ""
    echo "Esto puede ser porque:"
    echo "  1. El token no tiene permisos 'read:project'"
    echo "  2. El número del proyecto es incorrecto"
    echo ""
    echo "Solución:"
    echo "  1. Ejecuta: gh auth refresh -s read:project,write:project"
    echo "  2. O agrega los issues manualmente desde la web"
    echo ""
    echo "Ver instrucciones en: ADD_ISSUES_TO_PROJECT.md"
    exit 1
fi

echo "✓ Project ID: $PROJECT_ID"
echo ""

# Contador
SUCCESS=0
FAILED=0

# Agregar cada issue
for issue_num in {17..38}; do
    echo -n "Agregando issue #$issue_num... "
    
    # Obtener ID del issue
    ISSUE_ID=$(gh api graphql -f query="
    {
      repository(owner: \"$OWNER\", name: \"$REPO\") {
        issue(number: $issue_num) {
          id
          title
        }
      }
    }" --jq '.data.repository.issue.id' 2>&1)
    
    if [ -z "$ISSUE_ID" ] || [[ "$ISSUE_ID" == *"error"* ]]; then
        echo "❌ FAILED (issue no encontrado)"
        ((FAILED++))
        continue
    fi
    
    # Agregar al proyecto
    RESULT=$(gh api graphql -f query="
    mutation {
      addProjectV2ItemById(input: {
        projectId: \"$PROJECT_ID\"
        contentId: \"$ISSUE_ID\"
      }) {
        item {
          id
        }
      }
    }" 2>&1)
    
    if [[ "$RESULT" == *"error"* ]]; then
        echo "❌ FAILED"
        ((FAILED++))
    else
        echo "✓ OK"
        ((SUCCESS++))
    fi
    
    # Pequeña pausa para no saturar la API
    sleep 0.5
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Resumen:"
echo "   ✓ Exitosos: $SUCCESS"
echo "   ✗ Fallidos:  $FAILED"
echo "   📋 Total:     22"
echo ""
echo "✅ Proceso completado!"
echo ""
echo "Ver proyecto en:"
echo "https://github.com/users/$OWNER/projects/$PROJECT_NUMBER"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
