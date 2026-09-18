---
name: research-project-bootstrap
description: Plan, create, or improve reproducible research, data-science, bioinformatics, and Python project structures with appropriate source, notebook, data, result, test, configuration, and documentation directories. Use when starting a new project directory, reorganizing an early-stage research project, defining file-placement conventions, or generating core project documentation such as README.md, AGENTS.md, data-management notes, and reproducibility instructions.
---

# Research Project Bootstrap

Create a project structure that matches the work being done. Preserve the user's language in generated documentation and keep existing files intact unless the user explicitly requests replacement.

## Workflow

1. Establish the target.
   - Determine the project root, project name, primary language, and whether the work is analysis-only, a reusable package, or a hybrid.
   - Infer obvious details from existing files. Ask only when an unresolved choice would materially change the result.

2. Inspect before writing.
   - List the target directory and identify existing code, notebooks, data, configuration, documentation, and version-control state.
   - Treat a non-empty directory as an existing project. Create missing pieces without replacing user files.

3. Select a layout.
   - Read `references/research-layouts.md` completely.
   - Use the smallest suitable profile. Do not add directories that have no current or near-term purpose.
   - Adapt names to established project conventions when they already exist.

4. Scaffold the project.
   - Create only the selected directories and core files.
   - Add `.gitkeep` only where an intentionally empty directory must be tracked.
   - For Python projects, create or update `pyproject.toml` only when packaging or dependency configuration is in scope.
   - Create `.env.example` only when environment variables are actually needed; never put real credentials in it.

5. Write useful documentation.
   - `README.md`: purpose, status, setup, inputs, primary workflow, outputs, tests, and reproducibility.
   - `AGENTS.md`: project-specific operating rules for coding agents when ongoing Codex work is expected.
   - `docs/project-structure.md`: directory purposes and file-placement rules when the layout is not self-evident.
   - `docs/data-management.md`: data origin, lifecycle, identifiers, storage rules, and sensitive-data constraints when data is in scope.
   - `docs/reproducibility.md`: environment, configuration, execution order, seeds, and output regeneration when analyses are in scope.
   - Keep documentation factual. Mark genuinely unknown values as explicit TODOs rather than inventing commands, paths, or dependencies.

6. Validate the scaffold.
   - Print or summarize the resulting directory tree.
   - Check that documented commands and paths exist or are clearly marked as planned.
   - Check that raw data, secrets, caches, environments, and large generated artifacts are excluded from version control as appropriate.
   - If the directory is a Git repository, inspect status and distinguish newly created files from pre-existing changes.

7. Report the result.
   - State the selected profile, assumptions, files created, files intentionally left untouched, and any remaining TODOs.

## Integration With Other Skills

- Use `python-project-structure` when detailed Python package boundaries, imports, public APIs, or test placement are required.
- Use `folder-structure-blueprint-generator` when documenting or evaluating a substantial existing repository.
- Use `create-readme` for a final README pass after the actual structure and commands are known.
- Use `jupyter-notebook` when the scaffold includes a new experiment or tutorial notebook and that skill is available.

The workflow must remain functional when any of these optional companion skills are unavailable.

## Safety And Scope

- Never delete, move, rename, or overwrite existing project content without explicit approval.
- Treat `data/raw/` as immutable source material. Derived files belong in `data/interim/`, `data/processed/`, or `results/`.
- Do not inspect data contents, credentials, or unrelated files merely to create a directory structure.
- Do not initialize Git, install dependencies, download datasets, or run analyses unless the user requested that additional action.
- Prefer relative paths in documentation so the project remains portable.
