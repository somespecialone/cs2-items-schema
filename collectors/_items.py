import re
from dataclasses import dataclass, field

from . import _typings


@dataclass(eq=False, repr=False)
class ItemsCollector:
    items_game: _typings.ITEMS_GAME
    csgo_english: _typings.CSGO_ENGLISH
    items_schema: _typings.ITEMS_SCHEMA
    items_cdn: _typings.ITEMS_CDN

    paints: _typings.PAINTS
    types: _typings.TYPES
    categories: _typings.CATEGORIES
    cases: _typings.CASES

    _WITH_PAINTS_SET: set[str] = field(
        default_factory=lambda: {"knife", "pistol", "rifle", "smg", "sniper rifle", "shotgun", "machinegun", "gloves"}
    )

    def _create_painted_item_name(self, defindex: str, paint_index: str) -> str:
        paint_codename = "_" + self.items_game["paint_kits"][paint_index]["name"]
        item_codename = self.items_game["items"][defindex]["name"]
        return item_codename + paint_codename

    def _find_cases(self, defindex: str, paintindex: str) -> list[str]:
        cases = set()
        for case_index, case in self.cases.items():
            if "[" + paintindex + "]" + defindex in case["items"]:
                cases.add(case_index)

        return list(cases)

    def _check_paintable(self, item: dict[str, str | dict]) -> bool:
        # return self.categories[self.types[item["defindex"]]["category"]] in self._WITH_PAINTS_SET
        return item.get("capabilities", {}).get("paintable", False)

    def _find_rarity_paintable(self, paint_index: str) -> str:
        paint_codename: str = self.items_game["paint_kits"][paint_index]["name"]
        rarity_codename = self.items_game["paint_kits_rarity"][paint_codename]

        return self.items_game["rarities"][rarity_codename]["value"]

    @staticmethod
    def _fix_prefab_key(key: str) -> str:
        """Fixes prefab key `valve csgo_tool` -> `csgo_tool`"""
        if "valve " in key:
            key = key.replace("valve ", "")
        elif "_prefab" in key:
            key = re.search(r"^(.+_prefab)", key)[0]

        return key

    def _find_rarity_recursive(self, prefab_codename: str) -> str:
        prefab: dict[str, str | dict[str, str]] = self.items_game["prefabs"][self._fix_prefab_key(prefab_codename)]
        rarity_codename: str = prefab.get("item_rarity")
        if not rarity_codename:
            return self._find_rarity_recursive(prefab["prefab"])

        return self.items_game["rarities"][rarity_codename]["value"]

    def _find_rarity_nonpaintable(self, defindex: str) -> str:
        item_data: dict[str, str | int] = self.items_game["items"][defindex]
        return self._find_rarity_recursive(item_data["prefab"])

    def __call__(self) -> dict[str, dict]:
        items = {}

        item_data: dict[str, str | int]
        for item_data in self.items_schema["items"]:
            defindex: str = str(item_data["defindex"])

            if defindex not in self.types:  # skip some trash
                continue

            if not self._check_paintable(item_data):
                if image := (item_data["image_url"] or item_data["image_url_large"]):
                    items.update(
                        {
                            defindex: {
                                "type": defindex,
                                "image": image,
                                "rarity": self._find_rarity_nonpaintable(defindex),
                            }
                        }
                    )

            else:
                # find possible combination defindex + paintindex = item with paint
                for paint_index, paint_data in self.paints.items():
                    painted_item_name = self._create_painted_item_name(defindex, paint_index)
                    if painted_item_name in self.items_cdn:
                        painted_item = {
                            "type": defindex,
                            "image": self.items_cdn[painted_item_name],
                            "paint": paint_index,
                            "rarity": self._find_rarity_paintable(paint_index),
                        }

                        if cases := self._find_cases(defindex, paint_index):
                            painted_item["cases"] = cases

                        items.update({"[" + paint_index + "]" + defindex: painted_item})

        return items
