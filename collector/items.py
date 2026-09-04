from dataclasses import dataclass

from . import typings


@dataclass(eq=False, repr=False)
class ItemsCollector:
    items_game: typings.ITEMS_GAME
    csgo_english: typings.CSGO_ENGLISH
    item_identities: typings.ITEM_IDENTITIES

    paints: dict[str, str]
    definitions: dict[str, dict[str, str]]
    containers: dict[str, dict[str | list[str]]]

    def _create_painted_item_name(self, defindex: str, paint_index: str) -> str:
        paint_codename = "_" + self.items_game["paint_kits"][paint_index]["name"]
        item_codename = self.items_game["items"][defindex]["name"]
        return item_codename + paint_codename

    def _find_containers(self, defindex: str, paintindex: str) -> list[str]:
        containers = set()
        for cont_index, cont in self.containers.items():
            if "[" + paintindex + "]" + defindex in cont["items"]:
                containers.add(cont_index)

        return sorted(containers)

    def __call__(self) -> dict[str, dict]:
        items = {}

        for defindex in self.items_game["items"]:
            if defindex not in self.definitions:  # skip non-tradable and trash
                continue

            painted = False
            for paint_index in self.paints:
                item_name = self._create_painted_item_name(defindex, paint_index)
                if item_name not in self.item_identities:
                    continue

                item = {}
                if containers := self._find_containers(defindex, paint_index):
                    item["containers"] = containers

                items[f"[{paint_index}]{defindex}"] = item
                painted = True

            if not painted:
                items[defindex] = {}

        return items

