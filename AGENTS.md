# Repository Guidelines

## Project Overview

`cs2-items-schema` is a storage repository for an understandable, deliberately simple CS2 item schema. It checks in generated JSON in `schemas/` and SQL in `sql/`.

## Architecture & Data Flow

`collect.py` runs `collector.main.ResourceCollector`.

```text
game source files borrowed from `csfloat/cs-files`
  → concurrent fetch and parsing
  → collectors normalize fields, containers, items, and kits
  → JSON schemas/ and SQL sql/
```

`ResourceCollector` owns orchestration and output paths. `collector/sql.py` produces SQL for PostgreSQL, MySQL, SQLite, MSSQL, and Oracle. The root `manifest` records the borrowed source repository's version; `.github/workflows/schema.yml` compares it upstream and regenerates only when it changes.

## Key Directories

- `collector/` — collection and SQL-generation code.
- `schemas/` — checked-in JSON; `phases.json`, `origins.json`, `wears.json`, and `_phases_mapping.json` are collector inputs.
- `sql/` — generated schema and population scripts.
- `.github/workflows/` — scheduled and manual regeneration.

## Development Commands

Run generation from the repository root:

```sh
uv run collect.py
```

No repository build, test, type-check, or lint command is declared.

## Code Conventions & Common Patterns

- Use `snake_case` and descriptive collector classes such as `FieldsCollector`.
- Keep collection logic in its owning collector stage; later stages consume earlier normalized data.
- Preserve asynchronous concurrent fetching in `ResourceCollector`.
- Match existing parsed-data shapes from `collector/typings.py`; do not add a model layer for isolated changes.
- Missing optional game data is commonly skipped through `KeyError` handling. Preserve that behavior within the affected extraction path.
- There is no dependency-injection container or application state layer.
- Change collection logic or collector inputs, then regenerate. Do not hand-edit generated JSON or SQL.

## Important Files

- `collect.py` — collector entry point.
- `collector/main.py` — pipeline orchestration.
- `pyproject.toml` and `uv.lock` — runtime and dependency definitions.
- `.github/workflows/schema.yml` — automated regeneration.
- `README.md` — project scope and data limitations.

## Runtime/Tooling Preferences

- Use Python 3.14+ and `uv`.
- Run from the repository root: output paths default to `schemas/` and `sql/`.

## Testing & QA

No repository-owned automated tests, test configuration, or coverage threshold are declared.

For generation changes, run `uv run collect.py` and review the resulting `schemas/` and `sql/` changes. GitHub Actions compares the upstream source manifest daily at 01:19 UTC, regenerates only after an update, and supports manual dispatch.
