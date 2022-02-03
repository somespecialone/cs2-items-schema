import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import aiohttp
import vdf
import vpk

from . import _typings

from ._vpk_extractor import VpkExtractor
from ._fields import FieldsCollector
from ._items import ItemsCollector
from ._sticker_kits import StickerPatchCollector
from ._cases import CasesCollector


# https://stackoverflow.com/a/287944
class BCOLORS:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


@dataclass(eq=False, repr=False)
class ResourceCollector:
    RES_DIR: Path

    ITEMS_GAME_URL: str
    CSGO_ENGLISH_URL: str
    ITEMS_GAME_CDN_URL: str
    ITEMS_SCHEMA_URL: str

    vpk_path: Path
    categories_path: Path
    phases_mapping_path: Path

    def __post_init__(self):
        assert self.vpk_path.exists(), "No vpk file on this path"  # some validation

    @staticmethod
    def _keys_to_lowercase(target: dict[str, Any]) -> dict[str, Any]:
        return {k.lower(): v for k, v in target.items()}

    async def _fetch_data_files(self) -> list[dict | list]:
        async with aiohttp.ClientSession() as session:
            tasks = (
                session.get(self.ITEMS_GAME_URL),
                session.get(self.CSGO_ENGLISH_URL),
                session.get(self.ITEMS_GAME_CDN_URL),
                session.get(self.ITEMS_SCHEMA_URL),
            )

            resps = await asyncio.gather(*tasks)
            return [await resp.text() for resp in resps]

    @classmethod
    def _parse_data_files(cls, *texts: str) -> tuple:
        items_game_text, csgo_english_text, items_game_cdn_text, items_schema_text = texts

        items_game: _typings.ITEMS_GAME = vdf.loads(items_game_text)["items_game"]
        csgo_english: _typings.CSGO_ENGLISH = cls._keys_to_lowercase(vdf.loads(csgo_english_text)["lang"]["Tokens"])
        items_cdn: _typings.ITEMS_CDN = {
            line.split("=")[0]: line.split("=")[1] for line in items_game_cdn_text.splitlines()[3:]
        }
        items_schema: _typings.ITEMS_SCHEMA = json.loads(items_schema_text)["result"]

        return items_game, csgo_english, items_cdn, items_schema

    def _dump_files(self, *files: tuple[str | Path, Any]):
        for file_name, file in files:
            with (self.RES_DIR / file_name).open("w") as f:
                json.dump(file, f, sort_keys=True, indent=2)

    async def collect(self):
        print(f"{BCOLORS.OKCYAN}[{datetime.now()}] Start parsing data...")

        with self.categories_path.open("r") as c:
            categories: dict[str, str] = json.load(c)

        with self.phases_mapping_path.open("r") as p:
            phases_mapping: dict[str, str] = json.load(p)

        texts = await self._fetch_data_files()
        items_game, csgo_english, items_cdn, items_schema = self._parse_data_files(*texts)
        pak = VpkExtractor(vpk.open(str(self.vpk_path)))

        fields_collector = FieldsCollector(items_game, csgo_english, items_schema, categories, phases_mapping)
        qualities, types, paints, rarities, origins = fields_collector()

        cases_collector = CasesCollector(items_game, csgo_english, items_schema)
        cases = cases_collector()

        items_collector = ItemsCollector(
            items_game, csgo_english, items_schema, items_cdn, paints, types, categories, cases
        )
        items = items_collector()

        sticker_collector = StickerPatchCollector(pak, items_game, csgo_english)
        stickers, patches, graffities, tints = sticker_collector()
        sticker_kits = {**stickers, **patches, **graffities}

        # test(pak, items_cdn, csgo_english)

        to_dump = (
            ("qualities.json", qualities),
            ("types.json", types),
            ("paints.json", paints),
            ("rarities.json", rarities),
            ("origins.json", origins),
            ("cases.json", cases),
            ("items.json", items),
            ("sticker_kits.json", sticker_kits),
            ("tints.json", tints),
        )
        self._dump_files(*to_dump)

        print(f"{BCOLORS.OKCYAN}[{datetime.now()}] All data parsed and saved!")
