from dataclasses import dataclass
from typing import Any

from . import typings


@dataclass(eq=False, repr=False)
class ItemsCollector:
    items_game: typings.ITEMS_GAME
    csgo_english: typings.CSGO_ENGLISH
    item_identities: typings.ITEM_IDENTITIES

    paints: dict[str, str]
    definitions: dict[str, dict[str, str]]
    containers: dict[str, dict[str, Any]]

    def _create_painted_item_name(self, defindex: str, paint_index: str) -> str:
        paint_codename = "_" + self.items_game["paint_kits"][paint_index]["name"]
        item_codename = self.items_game["items"][defindex]["name"]
        return item_codename + paint_codename

    def __call__(self) -> dict[str, dict[str, Any]]:
        items = {}

        for defindex in self.items_game["items"]:
            if defindex not in self.definitions:  # skip non-tradable and trash
                continue

            painted = False
            for paint_index in self.paints:
                item_name = self._create_painted_item_name(defindex, paint_index)
                if item_name not in self.item_identities:
                    continue

                items[f"[{paint_index}]{defindex}"] = {}
                painted = True

            if not painted:
                items[defindex] = {}

        # Explicit loot includes bare rewards and items without indexed images.
        for container_id, container in sorted(self.containers.items()):
            for item_id in container.get("items", []):
                items.setdefault(item_id, {}).setdefault("containers", []).append(container_id)

        return items
