# Repository Guidelines

## Project Overview

This repository generates and stores an understandable, deliberately simple & normalized Counter-Strike 2 item schema from upstream game files. Consumers use the checked-in JSON resources in `schemas/` or relational DDL/data in `sql/`. The dataset comes only from game files and is intentionally not guaranteed to contain every item.

## Architecture & Data Flow

`collect.py` is the only executable entry point. It creates `collector.main.ResourceCollector` and runs the asynchronous pipeline with `asyncio.run()`:

1. Concurrently download `items_game.txt`, `csgo_english.txt`, and the `pak01_dir.txt` file index with `aiohttp`.
2. Parse VDF/localization data and derive item-image identities from the plain-text index.
3. `FieldsCollector` builds types, qualities, definitions, paints, rarities, music kits, and tints.
4. `ContainersCollector` recursively resolves item sets and nested loot lists.
5. `ItemsCollector` creates base/painted item records and container relationships.
6. `StickerKitsCollector` partitions localized sticker, patch, and graffiti records.
7. `SQLCreator` maps the same model to SQLAlchemy metadata, five dialect-specific DDL files, and `populate.sql`.
8. `ResourceCollector` writes sorted, indented JSON and generated SQL in place.

Collectors are callable dataclasses (`collector(...)`) coordinated explicitly by `ResourceCollector`; there is no dependency-injection framework or persistent application state. Preserve this direct pipeline rather than introducing a second orchestration pattern.

## Key Directories

- `collector/`: collection, normalization, relationship-building, and SQL generation code.
- `schemas/`: checked-in generated JSON outputs; edit generator logic rather than hand-editing these files.
- `sql/`: checked-in generated PostgreSQL, MySQL, SQLite, MSSQL, and Oracle DDL plus population SQL.
- `.github/workflows/`: two-hourly/manual schema regeneration automation.

## Development Commands

Use `uv` from the repository root:

```bash
uv run collect.py
```

`uv run collect.py` is the end-to-end generation/smoke path used by CI. It requires network access, downloads upstream assets, and rewrites outputs under `schemas/` and `sql/`; CI updates `source_hash` separately after collection. There is no package build, application server, type-check command, or test command. `.vscode/tasks.json` also defines **Run collector** using `.venv/bin/python collect.py`.

## Code Conventions & Common Patterns

- Python `>=3.14`; four-space indentation, `snake_case` functions/variables, `PascalCase` classes, and type annotations.
- Ruff is the sole configured QA tool; line length is 120 (`pyproject.toml`).
- Collector classes use `@dataclass(eq=False, repr=False)` and expose `__call__` for transformation steps.
- Prefer plain dictionaries, sets, and aliases from `collector/typings.py`; keep transformations local and explicit.
- Async work is concentrated in `ResourceCollector`: use `aiohttp` and concurrent gathering for independent downloads, then synchronous deterministic transforms.
- Recursive prefab and loot-list traversal is established in `collector/fields.py` and `collector/containers.py`.
- Missing/incomplete upstream records are commonly skipped with narrow `KeyError` handling. Invalid whole-input invariants, such as an empty item identity set, raise an explicit error. Do not broadly swallow failures.
- Generated collections and relationship lists are sorted where stable output matters. Preserve deterministic JSON/SQL generation.
- Logging is module-level and uses concise `INFO` progress messages; no custom error hierarchy exists.

## Important Files

- `collect.py`: executable entry point; no CLI arguments.
- `collector/main.py`: upstream URLs, async fetching, pipeline orchestration, and output writes.
- `collector/fields.py`: prefab inheritance, localization, and indexed field maps.
- `collector/containers.py`: container discovery and recursive loot resolution.
- `collector/items.py`: item identity and paint/container relationship generation.
- `collector/sticker_kits.py`: sticker, patch, and graffiti normalization.
- `collector/sql.py`: SQLAlchemy schema and dialect-specific SQL generation.
- `.github/workflows/schema.yml`: scheduled/manual generation and automated schema commit.
- `README.md`: public data-model diagrams, scope limitations, and project purpose.
- `source_hash`: SHA-256 fingerprint of the three upstream source-file blob IDs used to decide whether CI regenerates data.

## Testing & QA

No test framework, test directory, fixtures, snapshots, coverage configuration, type checker, or coverage threshold is currently defined. Do not invent pytest commands or conventions.

For collector changes:

1. Run `uv run ruff check .`.
2. Run `uv run collect.py` as the integration smoke test.
3. Inspect the affected generated JSON/SQL semantically and keep output deterministic.
4. Confirm only intended generated files changed; the workflow normally commits schema outputs with a `chore(schema): source ...` message.

The collector smoke test depends on live upstream resources and can produce large generated diffs. For isolated transformation bugs, add focused tests only when they protect a stable observable rule; follow existing repository simplicity rather than introducing test infrastructure for plumbing assertions.
