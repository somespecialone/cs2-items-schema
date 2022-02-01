from dataclasses import dataclass

from . import _typings

_WITH_PAINTS_SET: set[str] = {"knife", "pistol", "rifle", "smg", "sniper rifle", "shotgun", "machinegun", "gloves"}


@dataclass(eq=False, repr=False)
class ItemsCollector:
    items_game: _typings.ITEMS_GAME
    csgo_english: _typings.CSGO_ENGLISH
    items_schema: _typings.ITEMS_SCHEMA
    items_cdn: _typings.ITEMS_CDN

    paints: dict[str, str]
    types: dict[str, dict[str, str]]
    categories: dict[str, str]
    cases: dict[str, dict[str | list[str]]]

    def _create_item_name(self, defindex: str, paint_index: str) -> str:
        skin_name = "_" + self.items_game["paint_kits"][paint_index]["name"]
        if skin_name == "_default":
            skin_name = ""

        weapon_name = self.items_game["items"][defindex]["name"]
        return weapon_name + skin_name

    # def _clean_items(self, items: dict[str, dict]) -> dict[str, dict]:
    #     """Return new item's dict without item's not represented in csgo english"""
    #     return {key: item for key, item in items.items() if item["item_name"].lower() in self.csgo_english}

    def _find_cases(self, defindex: str, paintindex: str) -> list[str]:
        cases = set()
        for case_index, case in self.cases.items():
            if "[" + paintindex + "]" + defindex in case["items"]:
                cases.add(case_index)

        return list(cases)

    def _check_paintable(self, item: dict[str, str | dict]) -> bool:
        # return self.categories[self.types[item["defindex"]]["category"]] in _WITH_PAINTS_SET
        return item.get("capabilities", {}).get("paintable", False)

    def __call__(self) -> dict[str, dict]:
        items = {}

        item_data: dict[str, str | int]
        for item_data in self.items_schema["items"]:
            item = {"type": str(item_data["defindex"])}

            if item["type"] not in self.types:  # skip some trash
                continue

            if not self._check_paintable(item_data):
                if image := (item_data["image_url"] or item_data["image_url_large"]):
                    item["image"] = image
                    items.update({item["type"]: item})

            else:
                # find possible combination defindex + paintindex = item with paint
                for paint_index, paint_name in self.paints.items():
                    item_name = self._create_item_name(item["type"], paint_index)
                    if item_name in self.items_cdn:
                        painted_item = {
                            **item,
                            "image": self.items_cdn[item_name],
                            "paint": paint_index,
                            "cases": self._find_cases(item["type"], paint_index),
                        }
                        items.update({"[" + paint_index + "]" + item["type"]: painted_item})

        # TODO: rarity
        return items
