from dataclasses import dataclass, field

from . import typings
from .utils import invert_dict


@dataclass(repr=False, eq=False)
class FieldsCollector:
    """Collect origins, qualities, types, paints and rarities from game data."""

    items_game: typings.ITEMS_GAME
    csgo_english: typings.CSGO_ENGLISH
    phases_mapping: dict[str, str]

    _types_mapping: dict[str, str] = None
    _qualities_mapping: dict[str, str] = field(default_factory=dict)
    _rarities_mapping: dict[str, str] = field(default_factory=dict)

    def _parse_qualities(self) -> dict[str, dict[str, str]]:
        qualities = {}
        for quality_key, quality_data in self.items_game["qualities"].items():
            try:
                # in csgo_english titled as rarities :)
                # qualities[quality_data["value"]] = {
                #     "name": self.csgo_english[quality_key],
                #     "key": quality_key,
                # }
                qualities[quality_data["value"]] = self.csgo_english[quality_key]
                self._qualities_mapping[quality_key] = quality_data["value"]
            except KeyError:  # skip qualities that don't have name
                pass

        return qualities

    def _find_item_name(self, item_data: dict[str, str]) -> str | None:
        prefab = self._find_top_level_prefab(item_data, "item_name")
        return self.csgo_english[prefab["item_name"][1:]]

    def _find_top_level_prefab(self, data: dict[str, str], attr: str):
        # KeyError excepted on upper level of the stack
        if data.get(attr):
            return data
        else:
            # normalize special key
            if "valve" in data["prefab"]:
                prefab_key = data["prefab"].split(" ")[1]
            elif " " in data["prefab"]:  # ex. 'berlin2019_tournament_pass_prefab berlin2019_tournament_steamtv_items'
                prefab_key = data["prefab"].split(" ")[0]
            else:
                prefab_key = data["prefab"]

            return self._find_top_level_prefab(self.items_game["prefabs"][prefab_key], attr)

    def _find_type(self, item_data: dict[str, str]) -> str:
        # find top level prefab with 'item_type_name'
        prefab = self._find_top_level_prefab(item_data, "item_type_name")
        return self._types_mapping[self.csgo_english[prefab["item_type_name"][1:]]]

    def _parse_definitions(self) -> dict[str, dict[str, str]]:
        definitions = {}
        for defindex, item_data in self.items_game["items"].items():
            try:
                definition = {
                    # "key": item_data["name"],
                    "name": self._find_item_name(item_data),
                    "type": self._find_type(item_data),
                }

                # we have quality on inspected item
                if quality_key := item_data.get("item_quality"):
                    definition["quality"] = self._qualities_mapping[quality_key]

                if rarity_key := item_data.get("item_rarity"):
                    definition["rarity"] = self._rarities_mapping[rarity_key]

                definitions[defindex] = definition

                # there can be base_weapons image for definition
            except KeyError:
                pass

        return definitions

    def _parse_paints(self):
        paints = {}
        for paintindex, paint_data in self.items_game["paint_kits"].items():
            try:
                paint = {
                    # "key": paint_data["name"],
                    "name": self.csgo_english[paint_data["description_tag"][1:]],
                    "wear_min": float(paint_data.get("wear_remap_min", 0.06)),
                    "wear_max": float(paint_data.get("wear_remap_max", 0.8)),
                }

                if "doppler" in paint["name"].lower() and (phase := self.phases_mapping.get(paintindex)):
                    paint["phase"] = phase

                # we have rarity on inspected item
                if rarity_key := self.items_game["paint_kits_rarity"].get(paint_data["name"]):
                    paint["rarity"] = self._rarities_mapping[rarity_key]

                paints[paintindex] = paint
            except KeyError:
                pass

        return paints

    def _parse_rarities(self) -> dict[str, dict[str, str]]:
        rarities = {}
        for rarity_key, rarity_data in self.items_game["rarities"].items():
            try:
                rarity = {
                    "weapon": self.csgo_english[rarity_data["loc_key_weapon"]],
                    "nonweapon": self.csgo_english[rarity_data["loc_key"]],
                    "color": self.items_game["colors"][rarity_data["color"]]["hex_color"],
                    # "key": rarity_key,
                }
                if character_rarity := self.csgo_english.get(rarity_data["loc_key_character"]):
                    rarity["character"] = character_rarity

                rarities[rarity_data["value"]] = rarity
                self._rarities_mapping[rarity_key] = rarity_data["value"]

            except KeyError:  # skip rarities that does not have name in csgo_english
                pass

        return rarities

    def _parse_types(self) -> dict[str, str]:
        types = set()
        # prefabs does not contain all types so iterate over items
        for item_data in self.items_game["items"].values():
            try:
                top_prefab = self._find_top_level_prefab(item_data, "item_type_name")
                types.add(self.csgo_english[top_prefab["item_type_name"][1:]])
            except KeyError:
                pass

        return {str(i): t for i, t in enumerate(types)}

    def _parse_tints(self):
        tints = {}
        for tint_data in self.items_game["graffiti_tints"].values():
            tints[tint_data["id"]] = self.csgo_english["Attrib_SprayTintValue_" + tint_data["id"]]

        return tints

    def _parse_music_defs(self) -> dict[str, str]:
        music_defs = {}
        for music_index, music_kit_data in self.items_game["music_definitions"].items():
            try:
                music_defs[music_index] = self.csgo_english[music_kit_data["loc_name"][1:]]
            except KeyError:
                pass

        return music_defs

    def __call__(self) -> tuple[dict, ...]:
        """Parse all data to indexed format"""

        # separate fields
        types = self._parse_types()
        self._types_mapping = invert_dict(types)

        qualities = self._parse_qualities()
        rarities = self._parse_rarities()

        definitions = self._parse_definitions()
        paints = self._parse_paints()
        musics = self._parse_music_defs()
        tints = self._parse_tints()

        return types, qualities, definitions, paints, rarities, musics, tints
