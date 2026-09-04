# Repository Guidelines

## Project Overview

This repository generates and stores a normalized Counter-Strike 2 item schema from upstream game files. Consumers use the checked-in JSON resources in `schemas/` or relational DDL/data in `sql/`. The dataset comes only from game files and is intentionally not guaranteed to contain every market item.

## Architecture & Data Flow

`collect.py` is the only executable entry point. It creates `collector.main.ResourceCollector` and runs the asynchronous pipeline with `asyncio.run()`:

1. Concurrently download `items_game.txt`, `csgo_english.txt`, and `pak01_dir.vpk` with `aiohttp`.
2. Parse VDF/localization data and derive VPK item-image identities.
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
- `.github/workflows/`: daily/manual schema regeneration automation.

## Development Commands

Use `uv` from the repository root:

```bash
uv sync --dev
uv run collect.py
uv run ruff check .
```

`uv run collect.py` is the end-to-end generation/smoke path used by CI. It requires network access, downloads upstream assets, and rewrites outputs under `schemas/` and `sql/`; CI updates `manifest` separately after collection. There is no package build, application server, type-check command, or test command. `.vscode/tasks.json` also defines **Run collector** using `.venv/bin/python collect.py`.

## Code Conventions & Common Patterns

- Python `>=3.14`; four-space indentation, `snake_case` functions/variables, `PascalCase` classes, and type annotations.
- Ruff is the sole configured QA tool; line length is 120 (`pyproject.toml`).
- Collector classes use `@dataclass(eq=False, repr=False)` and expose `__call__` for transformation steps.
- Prefer plain dictionaries, sets, and aliases from `collector/typings.py`; keep transformations local and explicit.
- Async work is concentrated in `ResourceCollector`: use `aiohttp` and concurrent gathering for independent downloads, then synchronous deterministic transforms.
- Recursive prefab and loot-list traversal is established in `collector/fields.py` and `collector/containers.py`.
- Missing/incomplete upstream records are commonly skipped with narrow `KeyError` handling. Invalid whole-input invariants, such as an empty VPK identity set, raise an explicit error. Do not broadly swallow failures.
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
- `pyproject.toml`: Python version, dependencies, dev tools, and Ruff configuration.
- `uv.lock`: reproducible dependency lock; keep it consistent with `pyproject.toml` despite the broad `*.lock` ignore rule.
- `.github/workflows/schema.yml`: scheduled/manual generation and automated schema commit.
- `README.md`: public data-model diagrams, scope limitations, and project purpose.
- `manifest`: current upstream manifest identifier used to decide whether CI regenerates data.

## Runtime/Tooling Preferences

- Required runtime: Python 3.14 or newer, as declared by `pyproject.toml` and `uv.lock`.
- Package/environment manager: `uv`; CI uses `astral-sh/setup-uv` with caching.
- Runtime dependencies: `aiohttp`, `vdf`, `vpk`, and SQLAlchemy 2.x.
- Do not assume Node.js, Bun, Docker, a build backend, or an installed console script.
- `pak01_dir.vpk`, `.vscode/`, and lockfiles match ignore patterns even though examples may be present locally/tracked; avoid adding unrelated local artifacts.
- Output directories must already exist; generation opens output paths directly.

## Testing & QA

No test framework, test directory, fixtures, snapshots, coverage configuration, type checker, or coverage threshold is currently defined. Do not invent pytest commands or conventions.

For collector changes:

1. Run `uv run ruff check .`.
2. Run `uv run collect.py` as the integration smoke test.
3. Inspect the affected generated JSON/SQL semantically and keep output deterministic.
4. Confirm only intended generated files changed; the workflow normally commits schema outputs with a `chore(schema): manifest ...` message.

The collector smoke test depends on live upstream resources and can produce large generated diffs. For isolated transformation bugs, add focused tests only when they protect a stable observable rule; follow existing repository simplicity rather than introducing test infrastructure for plumbing assertions.
