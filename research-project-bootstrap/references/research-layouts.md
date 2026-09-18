# Research Project Layouts

Choose one profile and remove directories that do not serve the project. Names may be adapted to an existing convention.

## Analysis-Only Profile

Use for a focused study whose main artifacts are notebooks, scripts, figures, tables, and a report.

```text
project/
|-- README.md
|-- AGENTS.md
|-- .gitignore
|-- environment.yml or requirements.txt
|-- configs/
|-- data/
|   |-- raw/
|   |-- interim/
|   |-- processed/
|   `-- external/
|-- notebooks/
|-- scripts/
|-- results/
|   |-- figures/
|   |-- tables/
|   `-- reports/
|-- docs/
`-- tests/
```

Prefer numbered notebook names such as `01-data-qc.ipynb` only when execution order matters. Move reusable logic from notebooks into `scripts/` or a package as it stabilizes.

## Reusable Python Package Profile

Use for a library, service, command-line tool, or analysis framework intended for reuse.

```text
project/
|-- README.md
|-- AGENTS.md
|-- .gitignore
|-- pyproject.toml
|-- src/
|   `-- package_name/
|       `-- __init__.py
|-- tests/
|-- docs/
|-- examples/
`-- scripts/
```

Use the `src/` layout, keep public APIs explicit, and mirror important package areas under `tests/`. Add `configs/`, `data/`, or `results/` only when the package also owns analysis workflows.

## Hybrid Research Package Profile

Use when a research project contains both reusable Python code and study-specific analyses. This is the default for multi-stage bioinformatics and computational research projects.

```text
project/
|-- README.md
|-- AGENTS.md
|-- .gitignore
|-- pyproject.toml
|-- src/
|   `-- package_name/
|-- tests/
|-- configs/
|-- data/
|   |-- raw/
|   |-- interim/
|   |-- processed/
|   `-- external/
|-- notebooks/
|-- workflows/
|-- results/
|   |-- figures/
|   |-- tables/
|   `-- reports/
|-- scripts/
`-- docs/
```

Put reusable transformations and statistical methods in `src/`. Put orchestration in `workflows/`, thin entry points in `scripts/`, exploration in `notebooks/`, and generated deliverables in `results/`.

## Data Lifecycle Rules

- `data/raw/`: immutable source data; record origin, retrieval date, checksum, and access restrictions.
- `data/external/`: third-party reference data that is not a primary study input.
- `data/interim/`: restartable intermediate products.
- `data/processed/`: analysis-ready datasets with stable schemas.
- `results/`: figures, tables, reports, model outputs, and other final or reviewable artifacts.
- Keep large or sensitive data outside Git. Track manifests, schemas, download instructions, and small synthetic fixtures instead.

## Minimum Documentation Content

- `README.md`: what the project does, current maturity, prerequisites, setup, minimal run path, inputs, outputs, tests, and contacts or ownership when known.
- `AGENTS.md`: supported commands, validation expectations, sensitive paths, generated-file rules, and project-specific conventions.
- `docs/project-structure.md`: path, purpose, allowed content, and ownership for non-obvious directories.
- `docs/data-management.md`: provenance, identifiers, schemas, retention, privacy, and movement between lifecycle stages.
- `docs/reproducibility.md`: environment lock, configuration, execution order, random seeds, external versions, and how to regenerate results.

## Naming And Portability

- Use lowercase, descriptive, stable directory names unless the existing project uses another convention.
- Keep source-controlled paths relative and avoid machine-specific absolute paths.
- Separate configuration from code and separate generated outputs from source inputs.
- Do not encode dates or versions into every directory name; use them only when they carry domain meaning.
- Prefer one authoritative document for each rule and link to it instead of duplicating instructions.
