from dataclasses import dataclass

from . import typings


@dataclass(eq=False, repr=False)
class ItemsCollector:
    items_game: typings.ITEMS_GAME
    csgo_english: typings.CSGO_ENGLISH
    items_cdn: typings.ITEMS_CDN

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

        return list(containers)

    def _check_paintable(self, item_data: dict) -> bool:
        return bool(next(filter(lambda k: item_data["name"] in k, self.items_cdn.keys()), None))

    def __call__(self) -> dict[str, dict]:
        items = {}

        for defindex, item_data in self.items_game["items"].items():
            if defindex not in self.definitions:  # skip non-tradable and trash
                continue

            if not self._check_paintable(item_data):  # non-paintable
                item = {
                    "type": defindex,
                }

                items[defindex] = item

            else:
                # find possible combination defindex + paintindex = item with paint
                for paint_index, paint_data in self.paints.items():
                    item_name = self._create_painted_item_name(defindex, paint_index)
                    if item_name in self.items_cdn:
                        item = {
                            "def": defindex,
                            "image": self.items_cdn[item_name],
                            "paint": paint_index,
                        }

                        if containers := self._find_containers(defindex, paint_index):
                            item["containers"] = containers

                        items[f"[{paint_index}]{defindex}"] = item

        return items
