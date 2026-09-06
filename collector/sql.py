from dataclasses import dataclass, field
from graphlib import TopologicalSorter
from typing import Any

from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    MetaData,
    Table,
    UniqueConstraint,
    create_mock_engine,
)
from sqlalchemy.dialects import mssql, mysql, oracle, postgresql, sqlite
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.types import BigInteger, Float, SmallInteger, String, Text, TypeEngine

metadata = MetaData()

Types = Table(
    "types",
    metadata,
    Column("id", String(60), primary_key=True),
    Column("name", String(16)),
)


Qualities = Table(
    "qualities",
    metadata,
    Column("id", String(60), primary_key=True),
    Column("name", String(16)),
)


Tints = Table(
    "tints",
    metadata,
    Column("id", SmallInteger, primary_key=True, autoincrement=False),
    Column("name", String(16)),
)

Musics = Table(
    "musics",
    metadata,
    Column("id", SmallInteger, primary_key=True, autoincrement=False),
    Column("name", String(255)),
)

Rarities = Table(
    "rarities",
    metadata,
    Column("id", String(60), primary_key=True),
    Column("character", String(16)),
    Column("color", String(16), nullable=False),
    Column("nonweapon", String(16), nullable=False),
    Column("weapon", String(16), nullable=False),
)


Definitions = Table(
    "definitions",
    metadata,
    Column("defindex", SmallInteger, primary_key=True, autoincrement=False),
    Column("name", String(255), nullable=False),
    Column("type", String(60), ForeignKey(Types.c.id)),
    Column("quality", String(60), ForeignKey(Qualities.c.id)),
    Column("rarity", String(60), ForeignKey(Rarities.c.id)),
)

Paints = Table(
    "paints",
    metadata,
    Column("paintindex", SmallInteger, primary_key=True, autoincrement=False),
    Column("name", String(60), nullable=False),
    Column("wear_min", Float, nullable=False),
    Column("wear_max", Float, nullable=False),
    Column("rarity", String(60), ForeignKey(Rarities.c.id), nullable=False),
)

Items = Table(
    "items",
    metadata,
    Column("id", String(16), primary_key=True),
    Column("def", SmallInteger, ForeignKey(Definitions.c.defindex), nullable=False),
    Column("paint", SmallInteger, ForeignKey(Paints.c.paintindex)),
    UniqueConstraint("def", "paint", name="uniq_paint_def"),
    Index("ix_paint_def", "def", "paint", unique=True),
)

TournamentEvents = Table(
    "tournament_events",
    metadata,
    Column("id", SmallInteger, primary_key=True, autoincrement=False),
    Column("name", String(255)),
    Column("short_name", String(255)),
)

TournamentTeams = Table(
    "tournament_teams",
    metadata,
    Column("id", SmallInteger, primary_key=True, autoincrement=False),
    Column("tag", String(60)),
    Column("geo", String(16)),
)

TournamentPlayers = Table(
    "tournament_players",
    metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=False),
    Column("name", String(255)),
    Column("geo", String(16)),
)

TournamentStages = Table(
    "tournament_stages",
    metadata,
    Column("id", SmallInteger, primary_key=True, autoincrement=False),
    Column("name", String(255)),
)

Highlights = Table(
    "highlights",
    metadata,
    Column("id", SmallInteger, primary_key=True, autoincrement=False),
    Column("key", String(255), nullable=False, unique=True),
    Column("event", SmallInteger, ForeignKey(TournamentEvents.c.id), nullable=False),
    Column("stage", SmallInteger, ForeignKey(TournamentStages.c.id), nullable=False),
    Column("map", String(60), nullable=False),
    Column("team0", SmallInteger, ForeignKey(TournamentTeams.c.id), nullable=False),
    Column("team1", SmallInteger, ForeignKey(TournamentTeams.c.id), nullable=False),
)

Charms = Table(
    "charms",
    metadata,
    Column("id", SmallInteger, primary_key=True, autoincrement=False),
    Column("name", String(255)),
    Column("description", Text),
    Column("rarity", String(60), ForeignKey(Rarities.c.id)),
    Column("quality", String(60), ForeignKey(Qualities.c.id)),
    Column("base", SmallInteger, ForeignKey("charms.id")),
    Column("highlight", SmallInteger, ForeignKey(Highlights.c.id)),
)

Collections = Table(
    "collections",
    metadata,
    Column("id", String(60), primary_key=True),
    Column("name", String(255)),
    Column("hidden", SmallInteger),
)

ItemsCollectionsJunction = Table(
    "items_collections",
    metadata,
    Column("item", String(16), ForeignKey(Items.c.id), primary_key=True),
    Column("collection", String(60), ForeignKey(Collections.c.id), primary_key=True),
)

CollectionUnusualSources = Table(
    "collection_unusual_sources",
    metadata,
    Column("collection", String(60), ForeignKey(Collections.c.id), primary_key=True),
    Column("quality", String(60), ForeignKey(Qualities.c.id), primary_key=True),
    Column("loot_list", String(255), nullable=False),
)

StickerKits = Table(
    "sticker_kits",
    metadata,
    Column("id", SmallInteger, primary_key=True, autoincrement=False),
    Column("name", String(60)),
    Column("rarity", String(60), ForeignKey(Rarities.c.id)),
    Column("kind", String(16), nullable=False),
    Column("event", SmallInteger, ForeignKey(TournamentEvents.c.id)),
    Column("team", SmallInteger, ForeignKey(TournamentTeams.c.id)),
    Column("player", BigInteger, ForeignKey(TournamentPlayers.c.id)),
)

Containers = Table(
    "containers",
    metadata,
    Column("defindex", String(16), ForeignKey(Items.c.id), primary_key=True),
    Column("associated", String(16), ForeignKey(Items.c.id)),
    Column("kind", String(32), nullable=False),
    Column("collection", String(60), ForeignKey(Collections.c.id)),
    Column("will_produce_stattrak", SmallInteger),
)

ItemsContainersJunction = Table(
    "items_containers",
    metadata,
    Column("item", String(16), ForeignKey(Items.c.id), primary_key=True, nullable=False),
    Column("container", String(16), ForeignKey(Containers.c.defindex), primary_key=True, nullable=False),
    UniqueConstraint("item", "container", name="uniq_item_container"),
    Index("idx_item_container", "item", "container", unique=True),
)

MusicsContainersJunction = Table(
    "musics_containers",
    metadata,
    Column("music", SmallInteger, ForeignKey(Musics.c.id), primary_key=True, nullable=False),
    Column("container", String(16), ForeignKey(Containers.c.defindex), primary_key=True, nullable=False),
    UniqueConstraint("music", "container", name="uniq_music_container"),
    Index("idx_music_container", "music", "container", unique=True),
)

StickerKitsContainersJunction = Table(
    "sticker_kits_containers",
    metadata,
    Column("kit", SmallInteger, ForeignKey(StickerKits.c.id), primary_key=True, nullable=False),
    Column("container", String(16), ForeignKey(Containers.c.defindex), primary_key=True, nullable=False),
    UniqueConstraint("kit", "container", name="uniq_kit_container"),
    Index("idx_kit_container", "kit", "container", unique=True),
)

CharmsContainersJunction = Table(
    "charms_containers",
    metadata,
    Column("container", String(16), ForeignKey(Containers.c.defindex), primary_key=True),
    Column("charm", SmallInteger, ForeignKey(Charms.c.id), primary_key=True),
)

ContainerHighlightCharms = Table(
    "container_highlight_charms",
    metadata,
    Column("container", String(16), ForeignKey(Containers.c.defindex), primary_key=True),
    Column("charm", SmallInteger, ForeignKey(Charms.c.id), primary_key=True),
)



@dataclass(eq=False, repr=False)
class SQLCreator:
    types: dict[str, str]
    qualities: dict[str, str]
    definitions: dict[str, dict[str, Any]]
    paints: dict[str, dict[str, Any]]
    musics: dict[str, str]
    rarities: dict[str, dict[str, Any]]
    containers: dict[str, dict[str, Any]]
    items: dict[str, dict[str, Any]]
    sticker_kits: dict[str, dict[str, Any]]
    tints: dict[str, str]
    collections: dict[str, dict[str, Any]]
    charms: dict[str, dict[str, Any]]
    highlights: dict[str, dict[str, Any]]
    tournament_events: dict[str, dict[str, Any]]
    tournament_teams: dict[str, dict[str, Any]]
    tournament_players: dict[str, dict[str, Any]]
    tournament_stages: dict[str, str]

    dialect: Dialect = field(default_factory=sqlite.dialect)

    def _create_expression(self) -> list[tuple[str, str]]:
        # create 'create' scripts

        scripts = []
        for dialect, file_suffix in [
            (postgresql.dialect(), "postgre"),
            (mysql.dialect(), "mysql"),
            (sqlite.dialect(), "sqlite"),
            (mssql.dialect(), "mssql"),
            (oracle.dialect(), "oracle"),
        ]:
            file = f"create_{file_suffix}.sql"

            script_arr = []

            def dump(sql: TypeEngine[Any], *multiparams, dialect=dialect, script_arr=script_arr, **params):
                exp = sql.compile(dialect=dialect)
                script_arr.append(str(exp))

            engine = create_mock_engine("sqlite:///:memory:", dump)
            metadata.create_all(engine, checkfirst=False)

            script_arr.append("\n")

            script_joined = ";".join(script_arr)
            scripts.append((file, script_joined))

        return scripts

    def _base_field(self, table: Table, source: dict[str, str]):
        numeric_ids = isinstance(table.c.id.type, SmallInteger)
        return [
            table.insert()
            .values(id=int(source_id) if numeric_ids else source_id, name=name)
            .compile(dialect=self.dialect, compile_kwargs={"literal_binds": True})
            .string
            for source_id, name in source.items()
        ]

    def _populate_base_fields(self):
        types = self._base_field(Types, self.types)
        musics = self._base_field(Musics, self.musics)
        qualities = self._base_field(Qualities, self.qualities)
        tints = self._base_field(Tints, self.tints)

        return types, musics, qualities, tints

    def _populate_rarities(self):
        rarities = []
        for rarity_id, rarity_data in self.rarities.items():
            rarities.append(
                Rarities.insert()
                .values(id=rarity_id, **rarity_data)
                .compile(dialect=self.dialect, compile_kwargs={"literal_binds": True})
                .string
            )

        return rarities

    def _populate_defs(self):
        defs = []
        for defindex, def_data in self.definitions.items():
            defs.append(
                Definitions.insert()
                .values(
                    defindex=int(defindex),
                    type=def_data.get("type"),
                    quality=def_data.get("quality"),
                    rarity=def_data.get("rarity"),
                    name=def_data["name"],
                )
                .compile(dialect=self.dialect, compile_kwargs={"literal_binds": True})
                .string
            )

        return defs

    def _populate_paints(self):
        paints = []
        for paintindex, paint_data in self.paints.items():
            paints.append(
                Paints.insert()
                .values(
                    paintindex=int(paintindex),
                    rarity=paint_data["rarity"],
                    name=paint_data["name"],
                    wear_min=paint_data["wear_min"],
                    wear_max=paint_data["wear_max"],
                )
                .compile(dialect=self.dialect, compile_kwargs={"literal_binds": True})
                .string
            )

        return paints

    @staticmethod
    def _item_indexes(item_id: str) -> tuple[int, int | None]:
        if item_id.startswith("["):
            paint_index, defindex = item_id[1:].split("]", maxsplit=1)
            return int(defindex), int(paint_index)

        return int(item_id), None

    def _populate_items(self):
        items = []
        for item_id in self.items:
            defindex, paint_index = self._item_indexes(item_id)
            items.append(
                Items.insert()
                .values(
                    id=item_id,
                    **{"def": defindex},
                    paint=paint_index,
                )
                .compile(dialect=self.dialect, compile_kwargs={"literal_binds": True})
                .string
            )

        return items

    def _populate_sticker_kits(self):
        sticker_kits = []
        for sticker_kits_id, sticker_kits_data in self.sticker_kits.items():
            sticker_kits.append(
                StickerKits.insert()
                .values(
                    id=int(sticker_kits_id),
                    rarity=sticker_kits_data.get("rarity"),
                    name=sticker_kits_data.get("name"),
                    kind=sticker_kits_data["kind"],
                    event=int(sticker_kits_data["event"]) if "event" in sticker_kits_data else None,
                    team=int(sticker_kits_data["team"]) if "team" in sticker_kits_data else None,
                    player=int(sticker_kits_data["player"]) if "player" in sticker_kits_data else None,
                )
                .compile(dialect=self.dialect, compile_kwargs={"literal_binds": True})
                .string
            )

        return sticker_kits

    def _insert(self, table: Table, **values: Any) -> str:
        # Normalize numeric source IDs and encode flags as portable SQL 0/1 values.
        values = {
            key: int(value)
            if value is not None and isinstance(table.c[key].type, (SmallInteger, BigInteger))
            else value
            for key, value in values.items()
        }
        return (
            table.insert().values(**values).compile(dialect=self.dialect, compile_kwargs={"literal_binds": True}).string
        )

    def _populate_catalogs(self) -> list[str]:
        statements = []
        for table, source in (
            (TournamentEvents, self.tournament_events),
            (TournamentTeams, self.tournament_teams),
            (TournamentPlayers, self.tournament_players),
        ):
            for source_id, data in sorted(source.items()):
                statements.append(self._insert(table, id=source_id, **data))
        for stage_id, name in sorted(self.tournament_stages.items()):
            statements.append(self._insert(TournamentStages, id=stage_id, name=name))
        for highlight_id, data in sorted(self.highlights.items()):
            statements.append(self._insert(Highlights, id=highlight_id, **data))

        # Insert base charms before derivatives so self-references work with FK checks enabled.
        dependencies = {
            charm_id: [data["base"]] if "base" in data else [] for charm_id, data in sorted(self.charms.items())
        }
        for charm_id in TopologicalSorter(dependencies).static_order():
            statements.append(self._insert(Charms, id=charm_id, **self.charms[charm_id]))
        return statements

    def _populate_collections(self) -> list[str]:
        statements = []
        for collection_id, data in sorted(self.collections.items()):
            statements.append(
                self._insert(Collections, id=collection_id, name=data.get("name"), hidden=data.get("hidden"))
            )
            for item_id in data["items"]:
                statements.append(self._insert(ItemsCollectionsJunction, item=item_id, collection=collection_id))
            for quality, loot_list in sorted(data.get("unusuals", {}).items()):
                statements.append(
                    self._insert(
                        CollectionUnusualSources, collection=collection_id, quality=quality, loot_list=loot_list
                    )
                )
        return statements

    def _populate_containers(self) -> list[str]:
        statements = []
        for defindex, data in sorted(self.containers.items()):
            statements.append(
                self._insert(
                    Containers,
                    defindex=defindex,
                    kind=data["kind"],
                    collection=data.get("collection"),
                    associated=data.get("associated"),
                    will_produce_stattrak=data.get("will_produce_stattrak"),
                )
            )
            for key, table, column in (
                ("items", ItemsContainersJunction, "item"),
                ("kits", StickerKitsContainersJunction, "kit"),
                ("musics", MusicsContainersJunction, "music"),
                ("charms", CharmsContainersJunction, "charm"),
                ("highlight_charms", ContainerHighlightCharms, "charm"),
            ):
                for member in data.get(key, []):
                    statements.append(self._insert(table, container=defindex, **{column: member}))
        return statements


    def create(self) -> list[tuple[str, str]]:
        create_scripts = self._create_expression()

        types, musics, qualities, tints = self._populate_base_fields()

        rarities = self._populate_rarities()
        defs = self._populate_defs()
        paints = self._populate_paints()

        items = self._populate_items()
        sticker_kits = self._populate_sticker_kits()

        catalogs = self._populate_catalogs()
        collections = self._populate_collections()
        containers = self._populate_containers()

        populate = ";\n".join(
            [
                *types,
                *musics,
                *qualities,
                *tints,
                *rarities,
                *defs,
                *paints,
                *items,
                *catalogs,
                *collections,
                *sticker_kits,
                *containers,
            ]
        )

        return [*create_scripts, ("populate.sql", populate + ";\n")]
