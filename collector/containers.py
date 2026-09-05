import re
from dataclasses import dataclass
from typing import Any

from . import typings

ITEM_NAME_RE = re.compile(r"\[(.+)](.+)")


@dataclass(repr=False, eq=False)
class ContainersCollector:
    """Collect containers"""

    items_game: typings.ITEMS_GAME
    csgo_english: typings.CSGO_ENGLISH

    def _find_item_indexes(self, item_name: str) -> str:
        # performance? No, thanks
        paint_name, def_name = ITEM_NAME_RE.findall(item_name)[0]
        for defindex, type_data in self.items_game["items"].items():
            if type_data["name"] == def_name:
                for paint_index, paint_data in self.items_game["paint_kits"].items():
                    if paint_data["name"] == paint_name:
                        return "[" + paint_index + "]" + defindex

        raise ValueError(f"Unknown item index: {item_name}")

    def _check_case_prefab(self, data: dict[str, Any]) -> bool:
        # look for weapon_case_base prefab walking to top
        if "prefab" in data:
            if data["prefab"] == "weapon_case_base":
                return True
            else:
                return self._check_case_prefab(self.items_game["prefabs"].get(data["prefab"], {}))
        else:
            return False

    def _find_sticker_kit_index(self, item_name: str) -> str:
        sticker_kit_name, _ = ITEM_NAME_RE.findall(item_name)[0]
        for sticker_id, sticker_kit_data in self.items_game["sticker_kits"].items():
            if sticker_kit_data["name"] == sticker_kit_name:
                return sticker_id

        raise ValueError(f"Unknown sticker kit: {item_name}")

    def _find_music_kit_index(self, item_name: str) -> str:
        music_kit_name, _ = ITEM_NAME_RE.findall(item_name)[0]
        for music_id, music_kit_data in self.items_game["music_definitions"].items():
            if music_kit_data["name"] == music_kit_name:
                return music_id

        raise ValueError(f"Unknown music kit: {item_name}")

    def _get_loot_recursive(self, entry: dict[str, Any] | None) -> list[str]:
        if entry is None:
            return []

        loot = []
        for loot_name in entry:
            if "[" in loot_name:
                loot.append(loot_name)
            else:
                loot.extend(self._get_loot_recursive(self.items_game["client_loot_lists"].get(loot_name, {})))

        return loot

    def __call__(self) -> tuple[dict[str, Any], ...]:
        souvenir_cases = {}
        sticker_capsules = {}
        weapon_cases = {}
        music_kits = {}
        patch_capsules = {}

        for defindex, item_data in self.items_game["items"].items():
            if not self._check_case_prefab(item_data):
                continue

            container = {}
            supply_crate_series = item_data.get("attributes", {}).get("set supply crate series")
            if isinstance(supply_crate_series, dict):
                supply_crate_series = supply_crate_series.get("value")
            if not isinstance(supply_crate_series, str):
                supply_crate_series = None
            revolving_loot_list = (
                self.items_game["revolving_loot_lists"].get(supply_crate_series) if supply_crate_series else None
            )


            # there can be image pointer for containers a la 'econ/weapon_cases/...'

            if item_set_tag := item_data.get("tags", {}).get("ItemSet"):
                # if item set in tags we can bypass lookup and get items directly from set
                item_set = self.items_game["item_sets"][item_set_tag["tag_value"]]
                # container["set"] = self.csgo_english[item_set["name"][1:]]

                loot_list = list(item_set["items"].keys())  # no need to extract here
                container["items"] = [self._find_item_indexes(i) for i in loot_list]

                if "associated_items" in item_data:
                    container["associated"] = next(iter(item_data["associated_items"]))

                if item_data["prefab"] == "weapon_case_souvenirpkg":
                    containers_to_add = souvenir_cases
                else:
                    containers_to_add = weapon_cases

            elif sticker_caps_tag := item_data.get("tags", {}).get("StickerCapsule"):
                loot_dict: dict[str, Any] | None = None

                if sticker_caps_tag["tag_value"] in self.items_game["client_loot_lists"]:
                    loot_dict = self.items_game["client_loot_lists"][sticker_caps_tag["tag_value"]]

                elif item_data["name"] in self.items_game["client_loot_lists"]:
                    loot_dict = self.items_game["client_loot_lists"][item_data["name"]]

                elif (
                    isinstance(revolving_loot_list, str)
                    and revolving_loot_list in self.items_game["client_loot_lists"]
                ):
                    loot_dict = self.items_game["client_loot_lists"][revolving_loot_list]

                loot_list = self._get_loot_recursive(loot_dict)
                container["kits"] = [self._find_sticker_kit_index(i) for i in loot_list]

                containers_to_add = sticker_capsules

            elif patch_caps_tag := item_data.get("tags", {}).get("PatchCapsule"):
                loot_dict: dict[str, Any] | None = None

                if patch_caps_tag["tag_value"] in self.items_game["client_loot_lists"]:
                    loot_dict = self.items_game["client_loot_lists"][patch_caps_tag["tag_value"]]

                elif item_data["name"] in self.items_game["client_loot_lists"]:
                    loot_dict = self.items_game["client_loot_lists"][item_data["name"]]

                loot_list = self._get_loot_recursive(loot_dict)
                container["kits"] = [self._find_sticker_kit_index(i) for i in loot_list]

                containers_to_add = patch_capsules

            elif (
                isinstance(revolving_loot_list, str)
                and revolving_loot_list in self.items_game["client_loot_lists"]
            ):
                loot_dict = self.items_game["client_loot_lists"][revolving_loot_list]
                loot_list = self._get_loot_recursive(loot_dict)

                if "musickit" in item_data["name"]:
                    container["musics"] = [self._find_music_kit_index(i) for i in loot_list]
                    containers_to_add = music_kits

                else:
                    container["kits"] = [self._find_sticker_kit_index(i) for i in loot_list]
                    containers_to_add = sticker_capsules

            elif "loot_list_name" in item_data:
                try:
                    loot_dict = self.items_game["client_loot_lists"][item_data["loot_list_name"]]
                except KeyError:
                    continue

                loot_list = self._get_loot_recursive(loot_dict)

                if "musickit" in item_data["name"] or "music_kits" in item_data.get("image_inventory", ""):
                    container["musics"] = [self._find_music_kit_index(i) for i in loot_list]
                    containers_to_add = music_kits

                elif "coupon" in item_data["name"]:
                    container["kits"] = [self._find_sticker_kit_index(i) for i in loot_list]
                    containers_to_add = sticker_capsules

                else:
                    container["kits"] = [self._find_sticker_kit_index(i) for i in loot_list]
                    containers_to_add = sticker_capsules

            else:  # skip containers without loot lists
                continue

            if container.get("items") or container.get("kits") or container.get("musics"):
                containers_to_add[defindex] = container

        return weapon_cases, souvenir_cases, sticker_capsules, patch_capsules, music_kits
