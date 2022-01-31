from dataclasses import dataclass

from . import _types

_WITH_PAINTS_SET: set[str] = {"knife", "pistol", "rifle", "smg", "sniper rifle", "shotgun", "machinegun", "gloves"}


@dataclass(eq=False, repr=False)
class ItemsCollector:
    items_game: _types.ITEMS_GAME
    csgo_english: _types.CSGO_ENGLISH
    items_schema: _types.ITEMS_SCHEMA
    items_cdn: _types.ITEMS_CDN

    paints: dict[str, str]
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

    @staticmethod
    def _invert_dict(mapping: dict[str, str]) -> dict[str, str]:
        return {v: k for k, v in mapping.items()}

    def _find_cases(self, defindex: str, paintindex: str) -> list[str]:
        cases = set()
        for case_index, case in self.cases.items():
            if "[" + paintindex + "]" + defindex in case["items"]:
                cases.add(case_index)

        return list(cases)

    def __call__(self) -> dict[str, dict]:
        items = {}
        categories_mapping = self._invert_dict(self.categories)

        item_data: dict[str, str | int]
        for item_data in self.items_schema["items"]:
            try:
                item = {
                    "category": categories_mapping[self.csgo_english[item_data["item_type_name"][1:].lower()].lower()],
                    "defindex": str(item_data["defindex"]),
                }
            except KeyError:
                continue

            if self.categories[item["category"]] not in _WITH_PAINTS_SET:
                if image := (item_data["image_url"] or item_data["image_url_large"]):
                    item["image"] = image
                    items.update({item["defindex"]: item})

            else:
                # find possible combination defindex + paintindex = item with paint
                for paint_index, paint_name in self.paints.items():
                    item_name = self._create_item_name(item["defindex"], paint_index)
                    if item_name in self.items_cdn:
                        painted_item = {
                            **item,
                            "image": self.items_cdn[item_name],
                            "paintindex": paint_index,
                            "cases": self._find_cases(item["defindex"], paint_index),
                        }
                        items.update({"[" + paint_index + "]" + item["defindex"]: painted_item})

        return items
