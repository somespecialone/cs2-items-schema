import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path

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
    resource_dir: Path = field(default_factory=lambda: Path("schemas"))

    items_game_url: str = "https://raw.githubusercontent.com/csfloat/cs-files/master/static/items_game.txt"
    csgo_english_url: str = "https://raw.githubusercontent.com/csfloat/cs-files/master/static/csgo_english.txt"
    items_game_cdn_url: str = "https://raw.githubusercontent.com/csfloat/cs-files/master/static/items_game_cdn.txt"

    _phases_mapping: dict[str, str] = None

    def __post_init__(self):
        with (self.resource_dir / "_phases_mapping.json").open("r") as p:
            self._phases_mapping: dict[str, str] = json.load(p)

    async def fetch_data(self) -> tuple[typings.ITEMS_GAME, typings.CSGO_ENGLISH, typings.ITEMS_CDN]:
        async with aiohttp.ClientSession() as session:
            tasks = (
                session.get(self.items_game_url),
                session.get(self.csgo_english_url),
                session.get(self.items_game_cdn_url),
            )

            resps = await asyncio.gather(*tasks)
            items_game_raw, csgo_english_raw, items_game_cdn_raw = [await resp.text() for resp in resps]

        items_game = vdf.loads(items_game_raw)["items_game"]
        csgo_english = CIMultiDict(vdf.loads(csgo_english_raw)["lang"]["Tokens"])
        items_cdn = {k: v for k, v in (l.split("=") for l in items_game_cdn_raw.splitlines()[3:])}

        return items_game, csgo_english, items_cdn

    def dump_files(self, *files: tuple[str | Path, ...]):
        for file_name, file in files:
            with (self.resource_dir / file_name).open("w") as f:
                json.dump(file, f, sort_keys=True, indent=2)

    async def collect(self):
        items_game, csgo_english, items_cdn = await self.fetch_data()

        fields_collector = FieldsCollector(items_game, csgo_english, self._phases_mapping)
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
