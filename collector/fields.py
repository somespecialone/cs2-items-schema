from dataclasses import dataclass, field
from typing import Any

from . import typings


@dataclass(repr=False, eq=False)
class FieldsCollector:
    """Collect qualities, types, paints and rarities from game data."""

    items_game: typings.ITEMS_GAME
    csgo_english: typings.CSGO_ENGLISH

    _types: set[str] = field(default_factory=set)
    _qualities_mapping: dict[str, str] = field(default_factory=dict)
    _rarities_mapping: dict[str, str] = field(default_factory=dict)

    def _parse_qualities(self) -> dict[str, str]:
        qualities = {}
        for quality_key in self.items_game["qualities"]:
            try:
                qualities[quality_key] = self.csgo_english[quality_key]
                self._qualities_mapping[quality_key] = quality_key
            except KeyError:  # skip qualities that don't have name
                pass

        return qualities

    def _find_item_name(self, item_data: dict[str, str]) -> str | None:
        prefab = self._find_top_level_prefab(item_data, "item_name")
        item_name = prefab["item_name"]
        return self.csgo_english[item_name.removeprefix("#")]

    def _find_top_level_prefab(self, data: dict[str, str], attr: str) -> dict[str, str]:
        # Direct fields override every prefab branch.
        if data.get(attr):
            return data

        matches = self._find_prefab_matches(data, attr, set())
        if not matches:
            raise KeyError(attr)

        values = {match[attr] for match in matches}
        if len(values) != 1:
            raise ValueError(f"conflicting inherited {attr!r} values: {values!r}")

        return matches[0]

    def _find_prefab_matches(self, data: dict[str, str], attr: str, visited: set[str]) -> list[dict[str, str]]:
        matches = []
        for prefab_key in data.get("prefab", "").split():
            if prefab_key in visited:
                continue

            prefab = self.items_game["prefabs"].get(prefab_key)
            if prefab is None:
                continue

            if prefab.get(attr):
                matches.append(prefab)
                continue

            matches.extend(self._find_prefab_matches(prefab, attr, visited | {prefab_key}))

        return matches

    def _find_type(self, item_data: dict[str, str]) -> str:
        prefab = self._find_top_level_prefab(item_data, "item_type_name")
        type_key = prefab["item_type_name"].removeprefix("#")
        if type_key not in self._types:
            raise KeyError(type_key)
        return type_key

    def _parse_definitions(self) -> dict[str, dict[str, str]]:
        definitions = {}

        for defindex, item_data in self.items_game["items"].items():
            if not defindex.isdigit():
                continue

            try:
                definition = {
                    "name": self._find_item_name(item_data),
                }
                try:
                    definition["type"] = self._find_type(item_data)
                except KeyError:
                    pass

                if quality_key := item_data.get("item_quality"):
                    definition["quality"] = self._qualities_mapping[quality_key]
                else:
                    try:
                        craft_class = self._find_top_level_prefab(item_data, "craft_class")["craft_class"]
                    except KeyError:
                        craft_class = None

                    if craft_class == "unusual":
                        definition["quality"] = self._qualities_mapping["unusual"]
                    else:
                        try:
                            quality_key = self._find_top_level_prefab(item_data, "item_quality")["item_quality"]
                        except KeyError:
                            pass
                        else:
                            definition["quality"] = self._qualities_mapping[quality_key]

                if rarity_key := item_data.get("item_rarity"):
                    definition["rarity"] = self._rarities_mapping[rarity_key]
                else:
                    try:
                        rarity_key = self._find_top_level_prefab(item_data, "item_rarity")["item_rarity"]
                    except KeyError:
                        pass
                    else:
                        definition["rarity"] = self._rarities_mapping[rarity_key]

                definitions[defindex] = definition

                # there can be base_weapons image for definition
            except KeyError:
                pass

        return definitions

    def _parse_paints(self):
        paints = {}
        for paintindex, paint_data in self.items_game["paint_kits"].items():
            if description_tag := paint_data.get("description_tag"):
                paint = {
                    # "key": paint_data["name"],
                    "name": self.csgo_english.get(description_tag.removeprefix("#")),
                    "wear_min": float(paint_data.get("wear_remap_min", 0.06)),
                    "wear_max": float(paint_data.get("wear_remap_max", 0.8)),
                }

                # we have rarity on inspected item
                if rarity_key := self.items_game["paint_kits_rarity"].get(paint_data["name"]):
                    paint["rarity"] = self._rarities_mapping[rarity_key]

                paints[paintindex] = paint

        del paints["0"]  # remove unused

        return paints

    def _parse_rarities(self) -> dict[str, dict[str, str]]:
        rarities = {}
        for rarity_key, rarity_data in self.items_game["rarities"].items():
            try:
                rarity = {
                    "weapon": self.csgo_english[rarity_data["loc_key_weapon"]],
                    "nonweapon": self.csgo_english[rarity_data["loc_key"]],
                    "color": self.items_game["colors"][rarity_data["color"]]["hex_color"],
                }
                if character_rarity := self.csgo_english.get(rarity_data["loc_key_character"]):
                    rarity["character"] = character_rarity

                rarities[rarity_key] = rarity
                self._rarities_mapping[rarity_key] = rarity_key

            except KeyError:  # skip rarities that do not have required localized names
                pass

        return rarities

    def _parse_types(self) -> dict[str, str]:
        types = {}
        # Prefabs do not contain every used type, so inspect all items.
        for item_data in self.items_game["items"].values():
            try:
                prefab = self._find_top_level_prefab(item_data, "item_type_name")
                type_key = prefab["item_type_name"].removeprefix("#")
                types[type_key] = self.csgo_english[type_key]
            except KeyError:
                pass

        return types

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

    def __call__(self) -> tuple[dict[str, Any], ...]:
        """Parse all data to indexed format"""

        # separate fields
        types = self._parse_types()
        self._types = set(types)

        qualities = self._parse_qualities()
        rarities = self._parse_rarities()

        definitions = self._parse_definitions()
        paints = self._parse_paints()
        musics = self._parse_music_defs()
        tints = self._parse_tints()

        return types, qualities, definitions, paints, rarities, musics, tints
