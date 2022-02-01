from dataclasses import dataclass

from . import _typings


@dataclass(repr=False, eq=False)
class FieldsCollector:
    """Collect origins, qualities, types, paints and rarities from game data."""

    items_game: _typings.ITEMS_GAME
    csgo_english: _typings.CSGO_ENGLISH
    items_schema: _typings.ITEMS_SCHEMA
    categories: dict[str, str]

    # key to identify rarity
    _weapon_key: str = "weapon"
    _non_weapon_key: str = "nonweapon"
    _character_key: str = "character"

    def _parse_qualities(self) -> dict[str, str]:
        qualities = {}
        for quality_key, quality_data in self.items_game["qualities"].items():
            try:
                qualities |= {quality_data["value"]: self.csgo_english[quality_key.lower()]}
            except KeyError:
                pass
        return qualities

    def _find_item_name(self, defindex: str) -> str | None:
        item_data: dict[str, str] = self.items_game["items"][defindex]
        if "item_name" in item_data:
            weapon_hud: str = item_data["item_name"][1:]

        else:
            prefab_val: str = item_data["prefab"]
            weapon_hud: str = self.items_game["prefabs"][prefab_val]["item_name"][1:]

        return self.csgo_english.get(weapon_hud.lower())

    @staticmethod
    def _invert_dict(mapping: dict[str, str]) -> dict[str, str]:
        return {v: k for k, v in mapping.items()}

    def _find_category(self, defindex: str) -> str:
        categories_mapping = self._invert_dict(self.categories)

        for item_data in self.items_schema["items"]:
            if str(item_data["defindex"]) == defindex:
                return categories_mapping[self.csgo_english[item_data["item_type_name"][1:].lower()].lower()]

    def _parse_types(self) -> dict[str, str]:
        types = {}

        del self.items_game["items"]["default"]
        for defindex in self.items_game["items"].keys():
            try:
                types |= {
                    defindex: {
                        "name": self._find_item_name(defindex),
                        "category": self._find_category(defindex),
                    }
                }
            except KeyError:
                pass
        return {k: v for k, v in types.items() if v is not None}  # filter from None values

    def _define_paints(self, paintindex: str) -> str:
        code_name: str = self.items_game["paint_kits"][paintindex]["description_tag"][1:]
        return self.csgo_english[code_name.lower()]

    def _parse_paints(self):
        paints = {}
        for paintindex in self.items_game["paint_kits"].keys():
            try:
                paints |= {paintindex: self._define_paints(paintindex)}
            except KeyError:
                pass
        # TODO: wear min/max
        return paints

    def _parse_rarities(self) -> dict[str, dict[str, str]]:
        del self.items_game["rarities"]["unusual"]  # remove useless rarity
        return {
            v["value"]: {
                self._weapon_key: self.csgo_english[v["loc_key_weapon"].lower()],
                self._non_weapon_key: self.csgo_english[v["loc_key"].lower()],
                self._character_key: self.csgo_english[v["loc_key_character"].lower()],
                "color": self.items_game["colors"][v["color"]]["hex_color"],
            }
            for v in self.items_game["rarities"].values()
        }

    def _parse_origins(self) -> dict[str, str]:
        return {str(origin_data["origin"]): origin_data["name"] for origin_data in self.items_schema["originNames"]}

    def __call__(self) -> tuple:
        """Parse all data to indexed format"""
        qualities = self._parse_qualities()
        types = self._parse_types()
        paints = self._parse_paints()

        rarities = self._parse_rarities()
        origins = self._parse_origins()

        return qualities, types, paints, rarities, origins
