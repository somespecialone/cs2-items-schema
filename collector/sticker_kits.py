from dataclasses import dataclass

from . import typings


@dataclass(eq=False, repr=False)
class StickerKitsCollector:
    """Collect stickers, tints, patches, graffities"""

    items_game: typings.ITEMS_GAME
    csgo_english: typings.CSGO_ENGLISH

    containers: dict[str, dict]

    def _find_containers(self, sticker_kit_index: str) -> list[str]:
        containers = set()
        for cont_index, cont in self.containers.items():
            if sticker_kit_index in cont["kits"]:
                containers.add(cont_index)

        return list(containers)

    def __call__(self) -> tuple:
        stickers = {}
        patches = {}
        graffities = {}

        sticker_kit_data: dict[str, str]
        for sticker_kit_index, sticker_kit_data in self.items_game["sticker_kits"].items():
            try:
                sticker_kit = {
                    "name": self.csgo_english[sticker_kit_data["item_name"][1:]],
                }

            except KeyError:
                continue

            if containers := self._find_containers(sticker_kit_index):
                sticker_kit["containers"] = containers

            if rarity_key := sticker_kit_data.get("item_rarity"):
                sticker_kit["rarity"] = self.items_game["rarities"][rarity_key]["value"]

            # there can be image

            if "patch" in sticker_kit_data["name"]:
                patches[sticker_kit_index] = sticker_kit
            elif "graffiti" in sticker_kit_data["name"]:
                graffities[sticker_kit_index] = sticker_kit
            else:
                stickers[sticker_kit_index] = sticker_kit

        return stickers, patches, graffities
