import asyncio
import json
import logging
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import aiohttp
import vdf
import vpk
from multidict import CIMultiDict

from . import typings
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

    items_game_url: str = "https://raw.githubusercontent.com/csfloat/cs-files/master/static/items_game.txt"
    csgo_english_url: str = "https://raw.githubusercontent.com/csfloat/cs-files/master/static/csgo_english.txt"
    items_vpk_url: str = "https://raw.githubusercontent.com/csfloat/cs-files/master/static/pak01_dir.vpk"

    # predefined schemas
    phases: dict[str, str] = None
    origins: dict[str, str] = None
    wears: list[dict[str, ...]] = None

    _phases_mapping: dict[str, str] = None

    def __post_init__(self):
        logger.info("Loading predefined schemas from %s", self.resource_dir)

        with (self.resource_dir / "_phases_mapping.json").open("r") as p:
            self._phases_mapping = json.load(p)

        with (self.resource_dir / "phases.json").open("r") as p:
            self.phases = json.load(p)

        with (self.resource_dir / "origins.json").open("r") as p:
            self.origins = json.load(p)

        with (self.resource_dir / "wears.json").open("r") as p:
            self.wears = json.load(p)

    async def fetch_data(self) -> tuple[typings.ITEMS_GAME, typings.CSGO_ENGLISH, typings.ITEM_IDENTITIES]:
        logger.info("Fetching upstream game data")

        async with aiohttp.ClientSession() as session:
            tasks = (
                session.get(self.items_game_url),
                session.get(self.csgo_english_url),
                session.get(self.items_vpk_url),
            )

            resps = await asyncio.gather(*tasks)
            items_game_raw, csgo_english_raw = [await resp.text() for resp in resps[:2]]
            items_vpk_raw = await resps[2].read()

        items_game = vdf.loads(items_game_raw)["items_game"]
        csgo_english = CIMultiDict(vdf.loads(csgo_english_raw)["lang"]["Tokens"])
        with tempfile.NamedTemporaryFile() as items_vpk:
            items_vpk.write(items_vpk_raw)
            items_vpk.flush()
            item_identities = {
                path.removeprefix(ITEM_IMAGE_PATH_PREFIX).removesuffix(ITEM_IMAGE_PATH_SUFFIX)
                for path in vpk.open(items_vpk.name)
                if path.startswith(ITEM_IMAGE_PATH_PREFIX) and path.endswith(ITEM_IMAGE_PATH_SUFFIX)
            }
        if not item_identities:
            raise ValueError("VPK index contains no item identities")


        logger.info(
            "Fetched %d items, %d localized tokens, and %d item identities",
            len(items_game["items"]),
            len(csgo_english),
            len(item_identities),
        )

        return items_game, csgo_english, item_identities

    @staticmethod
    def dump_json_files(*files: tuple[str | Path, dict | list], dir: Path):
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

        fields_collector = FieldsCollector(items_game, csgo_english, self._phases_mapping)
        types, qualities, definitions, paints, rarities, musics, tints = fields_collector()

        containers_collector = ContainersCollector(items_game, csgo_english)
        weapon_cases, souvenir_cases, sticker_capsules, patch_capsules, music_kits = containers_collector()
        item_containers = {**weapon_cases, **souvenir_cases}
        sticker_kit_containers = {**sticker_capsules, **patch_capsules}
        containers = {**item_containers, **sticker_kit_containers}

        items_collector = ItemsCollector(
            items_game,
            csgo_english,
            item_identities,
            paints,
            definitions,
            item_containers,
        )
        items = items_collector()

        for defindex, container in sticker_kit_containers.items():
            items[defindex]["kits"] = container["kits"]
        for defindex, music_kit in music_kits.items():
            items[defindex]["musics"] = music_kit["musics"]

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
        ]

        sql_creator = SQLCreator(
            types=types,
            qualities=qualities,
            definitions=definitions,
            paints=paints,
            musics=musics,
            rarities=rarities,
            containers=item_containers,
            sticker_kit_containers=sticker_kit_containers,
            items=items,
            sticker_kits=sticker_kits,
            music_kits=music_kits,
            tints=tints,
            phases=self.phases,
            wears=self.wears,
            origins=self.origins,
        )
        sql_dumps = sql_creator.create()

        logger.info("Writing %d JSON schemas and %d SQL scripts", len(to_json_dump), len(sql_dumps))

        self.dump_json_files(*to_json_dump, dir=self.resource_dir)
        for file_name in ("sticker_kit_containers.json", "music_kits.json"):
            (self.resource_dir / file_name).unlink(missing_ok=True)

        self.dump_files(*sql_dumps, dir=self.sql_dir)
        logger.info("Schema collection completed")
