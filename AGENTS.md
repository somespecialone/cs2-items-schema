# Repository Guidelines

## Project Overview

This repository generates and stores an understandable, deliberately simple & normalized Counter-Strike 2 item schema from upstream game files. Consumers use the checked-in JSON resources in `schemas/` or relational DDL/data in `sql/`. The dataset comes only from game files and is intentionally not guaranteed to contain every item.

## Architecture & Data Flow

`collect.py` is the only executable entry point. It creates `collector.main.ResourceCollector` and runs the asynchronous pipeline with `asyncio.run()`:

1. Concurrently download `items_game.txt`, `csgo_english.txt`, and the `pak01_dir.txt` file index with `aiohttp`.
2. Parse VDF/localization data and derive item-image identities from the plain-text index.
3. `FieldsCollector` builds types, qualities, definitions, paints, rarities, music kits, and tints, resolving inherited definition quality/rarity.
4. `CollectionsCollector` normalizes item-set membership and preserves unresolved unusual-reward list references.
5. `CatalogCollector` builds charms, highlights, and tournament event/team/player/stage lookup records.
6. `ContainersCollector` resolves nested loot lists into one container map with explicit kinds and direct reward relationships.
7. `ItemsCollector` creates base/painted items and reverse container links; `ResourceCollector` also retains explicit collection members, containers, and associated items without requiring indexed images.
8. `StickerKitsCollector` partitions stickers, patches, and graffiti, preserving kind and tournament references when merged into one catalog.
9. `SQLCreator` maps the same model to SQLAlchemy metadata, five dialect-specific DDL files, and `populate.sql`.
10. `ResourceCollector` writes sorted, indented JSON and generated SQL in place.

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
- Recursive prefab and loot-list traversal is established in `collector/fields.py` and `collector/containers.py`. Definition lookup examines all existing prefab branches, skips missing tokens such as `valve`, and rejects conflicting inherited values rather than guessing precedence.
- Localization uses case-insensitive `CIMultiDict`; source tokens may include or omit `#`. Do not audit localization with case-sensitive plain-dictionary lookups.
- Preserve source-backed identities when optional names or metadata are unavailable; omit unavailable fields rather than inventing labels. Some legacy field collectors still skip records with narrow `KeyError` handling.
- Invalid whole-input invariants, conflicting inherited values, and unresolved collection references raise explicit errors. Do not broadly swallow failures.
- Generated collections and relationship lists are sorted where stable output matters. Preserve deterministic JSON/SQL generation.
- Logging is module-level and uses concise `INFO` progress messages; no custom error hierarchy exists.

## Schema Contracts

- Expose consumer-facing metadata and relationships, not prefab structures, textures, or rendering configuration. Do not infer inventory origin, drop odds, or complete variant eligibility from display names.
- JSON IDs and references are strings. `types`, `qualities`, and `rarities` use stable source keys; their localized values are display text only. Optional fields are omitted; an absent boolean is not `false`. Preserve deterministic relationship lists and the distinction between definition rarity and paint rarity.
- Definition quality precedence is direct `item_quality`, then the inherited `craft_class = "unusual"` normalization to quality `"unusual"` (`★`), then inherited `item_quality`. Direct rarity overrides inherited rarity. Do not assign `★` to all knives/gloves by type.
- `collections` uses source set keys and normalized bare/painted item IDs. Its `containers` lists the inverse of `containers.collection`; `unusuals` keys are source quality keys and values are unresolved source loot-list names, not enumerated rare rewards or probabilities.
- Keep all container kinds in one JSON catalog and SQL table. Preserve `kind`, collection/key associations, and separate `items`, `kits`, `musics`, `charms`, and `highlight_charms` relationships. Use the generic `container` kind when a more specific classification is not established.
- Source coupons retain `kind = "coupon"`. A coupon awarding another container links to that item; never flatten the awarded container's contents into the coupon.
- `will_produce_stattrak` comes only from an explicit item or selected root-loot-list flag. A conditional nested reward does not establish a guarantee. Missing contents do not require dropping a known container's metadata.
- Stickers, patches, and graffiti share `sticker_kits` with an explicit `kind`. Preserve source `event`, `team`, and `player` IDs instead of parsing them from names.
- Charms and highlights are separate catalogs. Resolve explicit charm base/highlight references; do not infer highlight players from reel keys. Tournament lookup records may contain only a source-backed ID, including team ID `0`. Preserve raw `geo` tags such as `WORLD`; they are not necessarily country codes.
- SQL uses unified `containers` and separate reward junctions, including `musics_containers`. Do not reintroduce the obsolete `sticker_kit_containers`, `music_kits`, or `musics_music_kits` tables. `containers.collection` references the collections table.
- SQL flags use integer `0`/`1` for portable population scripts. Insert referenced records before dependents, including base charms before variants. Keep SQL nullability, numeric ranges, and string widths compatible with emitted JSON data.
- Update `README.md` when public fields or SQL contracts change. Generated DDL/population files recreate a schema; they are not in-place database migrations.

## Important Files

- `collect.py`: executable entry point; no CLI arguments.
- `collector/main.py`: upstream URLs, async fetching, pipeline orchestration, and output writes.
- `collector/fields.py`: multi-prefab inheritance, localization, and source-keyed field maps.
- `collector/collections.py`: collection membership, source set identities, and unusual-reward references.
- `collector/catalog.py`: charms, highlights, and tournament lookup identities.
- `collector/containers.py`: container kinds, direct rewards, coupon links, and explicit reward metadata.
- `collector/items.py`: image/source-backed item identities and reverse item/container relationships.
- `collector/sticker_kits.py`: sticker/patch/graffiti kinds, localization, and tournament references.
- `collector/sql.py`: SQLAlchemy tables, unified container reward junctions, and dialect-specific SQL generation.
- `.github/workflows/schema.yml`: scheduled/manual generation and automated schema commit.
- `README.md`: public data-model diagrams, scope limitations, and project purpose.
- `source_hash`: SHA-256 fingerprint of the three upstream source-file blob IDs used to decide whether CI regenerates data.

## Testing & QA

No test framework, test directory, fixtures, snapshots, coverage configuration, type checker, or coverage threshold is currently defined. Do not invent pytest commands or conventions.

For collector changes:

1. Run `uv run ruff check .`.
2. Run `uv run collect.py` as the integration smoke test.
3. Inspect affected JSON/SQL semantically: source identities, inherited-value precedence, kind preservation, direct coupon rewards, and reference integrity. Do not substitute hard-coded live dataset counts for source comparisons.
4. For SQL changes, load `create_sqlite.sql` and `populate.sql` into a temporary SQLite database with `PRAGMA foreign_keys=ON`; require an empty `PRAGMA foreign_key_check` result. Compare catalog/junction coverage and check declared string lengths against emitted values, since SQLite does not enforce `VARCHAR` lengths.
5. Exercise uncertain boundaries with focused smoke checks, especially multi-prefab conflicts, missing localization, and conditional versus guaranteed rewards. Generating five dialects is not proof that all five database engines were exercised.
6. Confirm only intended generated files changed and keep output deterministic; the workflow normally commits schema outputs with a `chore(schema): source ...` message.

The collector smoke test depends on live upstream resources and can produce large generated diffs. For isolated transformation bugs, add focused tests only when they protect a stable observable rule; follow existing repository simplicity rather than introducing test infrastructure for plumbing assertions.
