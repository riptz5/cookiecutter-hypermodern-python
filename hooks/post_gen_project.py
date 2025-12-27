#!/usr/bin/env python
"""Post-generation hook for cookiecutter."""
import json
import shutil
from pathlib import Path


def reindent_cookiecutter_json():
    """Indent .cookiecutter.json using two spaces."""
    path = Path(".cookiecutter.json")
    with path.open() as io:
        data = json.load(io)
    with path.open(mode="w") as io:
        json.dump(data, io, sort_keys=True, indent=2)
        io.write("\n")


def remove_optional_files():
    """Remove optional files based on cookiecutter options."""
    with Path(".cookiecutter.json").open() as f:
        options = json.load(f)

    use_langgraph = options.get("use_langgraph", "n") == "y"
    use_google_adk = options.get("use_google_adk", "n") == "y"
    use_google_cloud = options.get("use_google_cloud", "n") == "y"

    paths_to_remove = []

    if not use_langgraph and not use_google_adk:
        paths_to_remove.extend(["src/*/agents", "tests/agents", "examples/orchestration_example.py"])

    if not use_langgraph:
        paths_to_remove.append("src/*/agents/langgraph")

    if not use_google_adk:
        paths_to_remove.extend(["src/*/agents/adk", "tests/agents/adk"])

    if not use_google_cloud and not use_google_adk:
        paths_to_remove.extend(["src/*/core", "tests/core", "examples/gcp_discovery_example.py", "examples/custom_gcp_plugin_example.py"])

    if not use_langgraph and not use_google_adk and not use_google_cloud:
        paths_to_remove.extend(["examples", "src/*/adapters", "src/*/mcp", "tests/adapters", "tests/mcp"])

    for pattern in paths_to_remove:
        for path in Path(".").glob(pattern):
            if path.exists():
                if path.is_dir():
                    print(f"Removing directory: {path}")
                    shutil.rmtree(path)
                else:
                    print(f"Removing file: {path}")
                    path.unlink()


def remove_empty_directories():
    """Remove empty directories recursively."""
    changed = True
    while changed:
        changed = False
        dirs = sorted([d for d in Path(".").rglob("*") if d.is_dir()], key=lambda p: len(p.parts), reverse=True)
        for d in dirs:
            if any(part.startswith(".") for part in d.parts):
                continue
            if d.exists() and not any(d.iterdir()):
                print(f"Removing empty directory: {d}")
                d.rmdir()
                changed = True


if __name__ == "__main__":
    reindent_cookiecutter_json()
    remove_optional_files()
    remove_empty_directories()
