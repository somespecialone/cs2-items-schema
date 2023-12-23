import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import aiohttp
from multidict import CIMultiDict
import vdf

from . import typings

from .fields import FieldsCollector
from .items import ItemsCollector
from .sticker_kits import StickerKitsCollector
from .containers import ContainersCollector


@dataclass(eq=False, repr=False)
class ResourceCollector:
    RES_DIR: Path = ""

    ITEMS_GAME_URL: str = ""
    CSGO_ENGLISH_URL: str = ""
    ITEMS_GAME_CDN_URL: str = ""

    async def _fetch_data_files(self) -> list[dict | list]:
        async with aiohttp.ClientSession() as session:
            tasks = (
                session.get(self.ITEMS_GAME_URL),
                session.get(self.CSGO_ENGLISH_URL),
                session.get(self.ITEMS_GAME_CDN_URL),
            )

            resps = await asyncio.gather(*tasks)
            return [await resp.text() for resp in resps]

    @classmethod
    def _parse_data_files(cls) -> tuple:
        with Path("items_game.txt").open("r", encoding="utf8") as f:
            items_game_raw = vdf.load(f)

        with Path("csgo_english.txt").open("r", encoding="utf8") as f:
            csgo_english_raw = vdf.load(f)

        with Path("items_game_cdn.txt").open("r", encoding="utf8") as f:
            items_game_cdn_raw = f.read()

        items_game: typings.ITEMS_GAME = items_game_raw["items_game"]
        csgo_english: typings.CSGO_ENGLISH = CIMultiDict(csgo_english_raw["lang"]["Tokens"])
        items_cdn: typings.ITEMS_CDN = {k: v for k, v in (l.split("=") for l in items_game_cdn_raw.splitlines()[3:])}

        return items_game, csgo_english, items_cdn

    def dump_files(self, *files: tuple[str | Path, Any]):
        for file_name, file in files:
            with (Path("schemas") / file_name).open("w") as f:
                json.dump(file, f, sort_keys=True, indent=2)

    def collect(self):
        with Path("schemas/_phases_mapping.json").open("r") as p:
            phases_mapping: dict[str, str] = json.load(p)

        # texts = await self._fetch_data_files()
        items_game, csgo_english, items_cdn = self._parse_data_files()

        fields_collector = FieldsCollector(items_game, csgo_english, phases_mapping)
        types, qualities, definitions, paints, rarities, musics, tints = fields_collector()

        containers_collector = ContainersCollector(items_game, csgo_english)
        weapon_cases, souvenir_cases, sticker_capsules, patch_capsules, music_kits = containers_collector()
        containers = {**weapon_cases, **souvenir_cases}
        sticker_kit_containers = {**sticker_capsules, **patch_capsules}

        items_collector = ItemsCollector(
            items_game,
            csgo_english,
            items_cdn,
            paints,
            definitions,
            containers,
        )
        items = items_collector()

        sticker_kit_collector = StickerKitsCollector(items_game, csgo_english, sticker_kit_containers)
        stickers, patches, graffities = sticker_kit_collector()
        sticker_kits = {**stickers, **patches, **graffities}

        to_dump = (
            ("types.json", types),
            ("qualities.json", qualities),
            ("definitions.json", definitions),
            ("paints.json", paints),
            ("musics.json", musics),
            ("rarities.json", rarities),
            ("containers.json", containers),
            ("sticker_kit_containers.json", sticker_kit_containers),
            ("items.json", items),
            ("sticker_kits.json", sticker_kits),
            ("music_kits.json", music_kits),
            ("tints.json", tints),
        )
        self.dump_files(*to_dump)
