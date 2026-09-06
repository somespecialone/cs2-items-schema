import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import aiohttp
import vdf
from multidict import CIMultiDict

from . import typings
from .catalog import CatalogCollector
from .collections import CollectionsCollector
from .containers import ContainersCollector
from .fields import FieldsCollector
from .items import ItemsCollector
from .sql import SQLCreator
from .sticker_kits import StickerKitsCollector

logger = logging.getLogger(__name__)
ITEM_IMAGE_PATH_PREFIX = "panorama/images/econ/default_generated/"
ITEM_IMAGE_PATH_SUFFIX = "_light_png.vtex_c"


@dataclass(eq=False, repr=False)
class ResourceCollector:
    resource_dir: Path = field(default_factory=lambda: Path("schemas"))
    sql_dir: Path = field(default_factory=lambda: Path("sql"))

    items_game_url: str = (
        "https://raw.githubusercontent.com/SteamTracking/GameTracking-CS2/master/"
        "game/csgo/pak01_dir/scripts/items/items_game.txt"
    )
    csgo_english_url: str = (
        "https://raw.githubusercontent.com/SteamTracking/GameTracking-CS2/master/"
        "game/csgo/pak01_dir/resource/csgo_english.txt"
    )
    items_index_url: str = (
        "https://raw.githubusercontent.com/SteamTracking/GameTracking-CS2/master/game/csgo/pak01_dir.txt"
    )

    async def fetch_data(self) -> tuple[typings.ITEMS_GAME, typings.CSGO_ENGLISH, typings.ITEM_IDENTITIES]:
        logger.info("Fetching upstream game data")

        async with aiohttp.ClientSession() as session:
            tasks = (
                session.get(self.items_game_url),
                session.get(self.csgo_english_url),
                session.get(self.items_index_url),
            )

            resps = await asyncio.gather(*tasks)
            items_game_raw, csgo_english_raw, items_index_raw = await asyncio.gather(*(resp.text() for resp in resps))

        items_game = vdf.loads(items_game_raw)["items_game"]
        csgo_english = CIMultiDict(vdf.loads(csgo_english_raw)["lang"]["Tokens"])
        item_identities = {
            path.removeprefix(ITEM_IMAGE_PATH_PREFIX).removesuffix(ITEM_IMAGE_PATH_SUFFIX)
            for line in items_index_raw.splitlines()
            if (path := line.partition(" ")[0]).startswith(ITEM_IMAGE_PATH_PREFIX)
            and path.endswith(ITEM_IMAGE_PATH_SUFFIX)
        }
        if not item_identities:
            raise ValueError("Item index contains no item identities")

        logger.info(
            "Fetched %d items, %d localized tokens, and %d item identities",
            len(items_game["items"]),
            len(csgo_english),
            len(item_identities),
        )

        return items_game, csgo_english, item_identities

    @staticmethod
    def dump_json_files(*files: tuple[str | Path, dict[str, Any] | list[Any]], dir: Path):
        for file_name, file in files:
            with (dir / file_name).open("w", encoding="utf8") as f:
                json.dump(file, f, ensure_ascii=False, sort_keys=True, indent=2)

    @staticmethod
    def dump_files(*files: tuple[str | Path, str], dir: Path):
        for file_name, file in files:
            with (dir / file_name).open("w", encoding="utf8") as f:
                f.write(file)

    async def collect(self):
        logger.info("Starting schema collection")

        items_game, csgo_english, item_identities = await self.fetch_data()

        fields_collector = FieldsCollector(items_game, csgo_english)
        types, qualities, definitions, paints, rarities, musics, tints = fields_collector()
        collections_collector = CollectionsCollector(items_game, csgo_english, definitions, paints)
        collections = collections_collector()
        if collections_collector.unresolved_members or collections_collector.unresolved_unusuals:
            raise ValueError(
                f"Unresolved collection references: {collections_collector.unresolved_members}, "
                f"{collections_collector.unresolved_unusuals}"
            )
        charms, highlights, tournament_events, tournament_teams, tournament_players, tournament_stages = (
            CatalogCollector(items_game, csgo_english)()
        )

        containers_collector = ContainersCollector(items_game, csgo_english)
        containers = containers_collector()
        sticker_kit_containers = {key: data for key, data in containers.items() if "kits" in data}

        items_collector = ItemsCollector(
            items_game,
            csgo_english,
            item_identities,
            paints,
            definitions,
            containers,
        )
        items = items_collector()

        # Collection membership is explicit source evidence even without an indexed image.
        for collection in collections.values():
            for item_id in collection["items"]:
                items.setdefault(item_id, {})
        for defindex, container in containers.items():
            items.setdefault(defindex, {})
            if associated := container.get("associated"):
                items.setdefault(associated, {})

        for defindex, container in containers.items():
            for reward_field in ("kits", "musics", "charms"):
                if reward_field in container:
                    items[defindex][reward_field] = container[reward_field]

        sticker_kit_collector = StickerKitsCollector(items_game, csgo_english, sticker_kit_containers)
        stickers, patches, graffities = sticker_kit_collector()
        sticker_kits = {**stickers, **patches, **graffities}

        logger.info(
            "Collected %d definitions, %d items, and %d containers",
            len(definitions),
            len(items),
            len(containers),
        )

        to_json_dump = [
            ("types.json", types),
            ("qualities.json", qualities),
            ("definitions.json", definitions),
            ("paints.json", paints),
            ("musics.json", musics),
            ("rarities.json", rarities),
            ("containers.json", containers),
            ("items.json", items),
            ("sticker_kits.json", sticker_kits),
            ("tints.json", tints),
            ("collections.json", collections),
            ("charms.json", charms),
            ("highlights.json", highlights),
            ("tournament_events.json", tournament_events),
            ("tournament_teams.json", tournament_teams),
            ("tournament_players.json", tournament_players),
            ("tournament_stages.json", tournament_stages),
        ]

        sql_creator = SQLCreator(
            types=types,
            qualities=qualities,
            definitions=definitions,
            paints=paints,
            musics=musics,
            rarities=rarities,
            containers=containers,
            items=items,
            sticker_kits=sticker_kits,
            tints=tints,
            collections=collections,
            charms=charms,
            highlights=highlights,
            tournament_events=tournament_events,
            tournament_teams=tournament_teams,
            tournament_players=tournament_players,
            tournament_stages=tournament_stages,
        )
        sql_dumps = sql_creator.create()

        logger.info("Writing %d JSON schemas and %d SQL scripts", len(to_json_dump), len(sql_dumps))

        self.dump_json_files(*to_json_dump, dir=self.resource_dir)
        for file_name in ("sticker_kit_containers.json", "music_kits.json"):
            (self.resource_dir / file_name).unlink(missing_ok=True)

        self.dump_files(*sql_dumps, dir=self.sql_dir)
        logger.info("Schema collection completed")
