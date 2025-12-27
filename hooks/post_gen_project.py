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

    return options


def replace_block(text: str, start_marker: str, end_marker: str, content: str) -> str:
    """Replace the text between start and end markers with new content.
    
    If content is empty, removes the entire block including markers.
    Otherwise, replaces content between markers.
    """
    if start_marker not in text or end_marker not in text:
        return text
    
    before, rest = text.split(start_marker, 1)
    block, after = rest.split(end_marker, 1)
    
    if content:
        # Replace with content between markers
        return before + start_marker + "\n" + content + "\n" + end_marker + after
    else:
        # Remove entire block including markers
        return before + after


def update_dependency_blocks(options: dict[str, str]) -> None:
    """Populate optional dependency blocks in pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    text = pyproject_path.read_text()

    langgraph_content = ""
    if options.get("use_langgraph", "n") == "y":
        langgraph_content = "\n".join(
            [
                'langgraph = ">=1.0.0"',
                'langchain-core = ">=0.3.0"',
                'langchain-google-genai = ">=2.0.0"',
            ]
        )

    gadk_content = ""
    if options.get("use_google_adk", "n") == "y":
        gadk_content = 'google-genai = ">=1.0.0"'

    gcloud_content = ""
    if options.get("use_google_cloud", "n") == "y":
        gcloud_content = "\n".join(
            [
                'google-cloud-aiplatform = ">=1.70.0"',
                'google-cloud-storage = ">=2.10.0"',
                'google-cloud-service-usage = ">=1.10.0"',
                'google-cloud-secret-manager = ">=2.20.0"',
                'google-cloud-firestore = ">=2.16.0"',
                'google-cloud-bigquery = ">=3.25.0"',
                'google-auth = ">=2.30.0"',
            ]
        )

    text = replace_block(text, "# LANGGRAPH_DEPENDENCIES_START", "# LANGGRAPH_DEPENDENCIES_END", langgraph_content)
    text = replace_block(text, "# GADK_DEPENDENCIES_START", "# GADK_DEPENDENCIES_END", gadk_content)
    text = replace_block(text, "# GCLOUD_DEPENDENCIES_START", "# GCLOUD_DEPENDENCIES_END", gcloud_content)

    pyproject_path.write_text(text)


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
    options = remove_optional_files()
    update_dependency_blocks(options)
    remove_empty_directories()
