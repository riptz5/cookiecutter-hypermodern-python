---
description: Test the cookiecutter template by generating a project and running its tests
---

1. Generate the project (overwrite if exists)
// turbo
cookiecutter --no-input . --overwrite-if-exists

2. Enter the generated directory
// turbo
cd hypermodern-python

3. Run the generated project's tests using Nox
// turbo
nox
