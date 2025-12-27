#!/usr/bin/env python3
"""Add issues to GitHub Project using GraphQL API."""
import os
import subprocess
import json
import time
import sys

# Configuration
PROJECT_NUMBER = 2
OWNER = "riptz5"
REPO = "cookiecutter-hypermodern-python"
ISSUES_TO_ADD = list(range(17, 39))  # Issues #17-#38

def run_gh_api(query):
    """Run GitHub CLI API command."""
    try:
        result = subprocess.run(
            ["gh", "api", "graphql", "-f", f"query={query}"],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e.stderr}")
        return None
    except json.JSONDecodeError:
        print(f"❌ Error parsing JSON response")
        return None

def get_project_id():
    """Get the Project ID."""
    query = f"""
    {{
      user(login: "{OWNER}") {{
        projectV2(number: {PROJECT_NUMBER}) {{
          id
          title
        }}
      }}
    }}
    """
    
    print("📋 Obteniendo ID del proyecto...")
    result = run_gh_api(query)
    
    if not result or "errors" in result:
        print("\n❌ Error: No se pudo obtener el ID del proyecto")
        print("\nPosibles causas:")
        print("  1. El token no tiene permisos 'read:project'")
        print("  2. El proyecto no existe o es inaccesible")
        print("\nSolución:")
        print("  Ejecuta: gh auth refresh -s read:project,write:project")
        print("  O agrega los issues manualmente desde la web")
        return None
    
    try:
        project_id = result["data"]["user"]["projectV2"]["id"]
        project_title = result["data"]["user"]["projectV2"]["title"]
        print(f"✓ Proyecto encontrado: {project_title}")
        print(f"✓ Project ID: {project_id}\n")
        return project_id
    except (KeyError, TypeError):
        print("❌ Error: Respuesta inesperada de la API")
        return None

def get_issue_id(issue_number):
    """Get the Issue ID."""
    query = f"""
    {{
      repository(owner: "{OWNER}", name: "{REPO}") {{
        issue(number: {issue_number}) {{
          id
          title
        }}
      }}
    }}
    """
    
    result = run_gh_api(query)
    
    if not result or "errors" in result:
        return None, None
    
    try:
        issue_id = result["data"]["repository"]["issue"]["id"]
        issue_title = result["data"]["repository"]["issue"]["title"]
        return issue_id, issue_title
    except (KeyError, TypeError):
        return None, None

def add_issue_to_project(project_id, issue_id):
    """Add an issue to the project."""
    mutation = f"""
    mutation {{
      addProjectV2ItemById(input: {{
        projectId: "{project_id}"
        contentId: "{issue_id}"
      }}) {{
        item {{
          id
        }}
      }}
    }}
    """
    
    result = run_gh_api(mutation)
    
    if not result or "errors" in result:
        return False
    
    return True

def main():
    """Main function."""
    print("🚀 Agregando issues al proyecto GitHub...")
    print(f"   Proyecto: {OWNER}/projects/{PROJECT_NUMBER}")
    print(f"   Repositorio: {OWNER}/{REPO}")
    print(f"   Issues: #{ISSUES_TO_ADD[0]}-#{ISSUES_TO_ADD[-1]}")
    print("=" * 70)
    print()
    
    # Get project ID
    project_id = get_project_id()
    if not project_id:
        sys.exit(1)
    
    # Add each issue
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    for issue_num in ISSUES_TO_ADD:
        print(f"Procesando issue #{issue_num}...", end=" ", flush=True)
        
        # Get issue ID
        issue_id, issue_title = get_issue_id(issue_num)
        
        if not issue_id:
            print("❌ SKIP (no encontrado)")
            skipped_count += 1
            continue
        
        # Add to project
        if add_issue_to_project(project_id, issue_id):
            print(f"✓ OK - {issue_title[:50]}...")
            success_count += 1
        else:
            print("❌ FAILED")
            failed_count += 1
        
        # Rate limiting
        time.sleep(0.5)
    
    # Summary
    print()
    print("=" * 70)
    print("📊 Resumen:")
    print(f"   ✓ Exitosos: {success_count}")
    print(f"   ✗ Fallidos:  {failed_count}")
    print(f"   ⊘ Omitidos:  {skipped_count}")
    print(f"   📋 Total:     {len(ISSUES_TO_ADD)}")
    print()
    
    if success_count > 0:
        print("✅ Proceso completado!")
        print()
        print("Ver proyecto en:")
        print(f"https://github.com/users/{OWNER}/projects/{PROJECT_NUMBER}")
    else:
        print("❌ No se pudo agregar ningún issue")
        print()
        print("Verifica:")
        print("  1. Que tengas permisos 'read:project' y 'write:project'")
        print("  2. Que el proyecto exista y sea accesible")
        print("  3. Que los issues existan en el repositorio")
        sys.exit(1)
    
    print("=" * 70)

if __name__ == "__main__":
    main()
