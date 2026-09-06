from dataclasses import dataclass
from typing import Any

from . import typings


@dataclass(eq=False, repr=False)
class StickerKitsCollector:
    """Collect stickers, tints, patches, graffities"""

    items_game: typings.ITEMS_GAME
    csgo_english: typings.CSGO_ENGLISH

    containers: dict[str, dict[str, Any]]

    def _find_containers(self, sticker_kit_index: str) -> list[str]:
        containers = set()
        for cont_index, cont in self.containers.items():
            if sticker_kit_index in cont.get("kits", []):
                containers.add(cont_index)

        return sorted(containers)

    def __call__(self) -> tuple[dict[str, dict[str, Any]], ...]:
        stickers: dict[str, dict[str, Any]] = {}
        patches: dict[str, dict[str, Any]] = {}
        graffities: dict[str, dict[str, Any]] = {}

        for sticker_kit_index, sticker_kit_data in self.items_game["sticker_kits"].items():
            sticker_kit: dict[str, Any] = {}
            item_name = sticker_kit_data.get("item_name")
            if item_name and (name := self.csgo_english.get(item_name.removeprefix("#"))):
                sticker_kit["name"] = name

            if containers := self._find_containers(sticker_kit_index):
                sticker_kit["containers"] = containers

            if (rarity_key := sticker_kit_data.get("item_rarity")) and rarity_key in self.items_game["rarities"]:
                sticker_kit["rarity"] = rarity_key

            for source_key, output_key in (
                ("tournament_event_id", "event"),
                ("tournament_team_id", "team"),
                ("tournament_player_id", "player"),
            ):
                if source_id := sticker_kit_data.get(source_key):
                    sticker_kit[output_key] = source_id

            if "patch_material" in sticker_kit_data:
                sticker_kit["kind"] = "patch"
                patches[sticker_kit_index] = sticker_kit
            elif "graffiti" in sticker_kit_data.get("sticker_material", ""):
                sticker_kit["kind"] = "graffiti"
                graffities[sticker_kit_index] = sticker_kit
            else:
                sticker_kit["kind"] = "sticker"
                stickers[sticker_kit_index] = sticker_kit

        return stickers, patches, graffities
