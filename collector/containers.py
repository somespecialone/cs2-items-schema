from dataclasses import dataclass
from typing import Any

from . import typings


@dataclass(repr=False, eq=False)
class ContainersCollector:
    """Collect container kinds and direct source-defined rewards."""

    items_game: typings.ITEMS_GAME
    csgo_english: typings.CSGO_ENGLISH

    def _prefab_chain(self, data: dict[str, Any]) -> set[str]:
        prefabs = set()
        pending = data.get("prefab", "").split()
        while pending:
            key = pending.pop()
            if key in prefabs:
                continue
            prefabs.add(key)
            pending.extend(self.items_game["prefabs"].get(key, {}).get("prefab", "").split())
        return prefabs

    def _loot_list_names(self, item_data: dict[str, Any]) -> set[str]:
        client_loot_lists = self.items_game["client_loot_lists"]
        names = set()
        for name in (item_data.get("name"), item_data.get("loot_list_name")):
            if name in client_loot_lists:
                names.add(name)
        for tag in item_data.get("tags", {}).values():
            if tag.get("tag_value") in client_loot_lists:
                names.add(tag["tag_value"])
        series = item_data.get("attributes", {}).get("set supply crate series")
        if isinstance(series, dict):
            series = series.get("value")
        name = self.items_game["revolving_loot_lists"].get(series)
        if name in client_loot_lists:
            names.add(name)
        return names

    def _loot(self, names: set[str]) -> tuple[set[str], set[str]]:
        rewards = set()
        highlight_charms = set()
        seen = set()
        pending = list(names)
        while pending:
            name = pending.pop()
            if name in seen:
                continue
            seen.add(name)
            entry = self.items_game["client_loot_lists"][name]
            if charm := entry.get("match_highlight_reel_keychain"):
                highlight_charms.add(charm)
            for reward in entry:
                if reward in self.items_game["client_loot_lists"]:
                    pending.append(reward)
                else:
                    rewards.add(reward)
        return rewards, highlight_charms

    @staticmethod
    def _kind(item: dict[str, Any], prefabs: set[str], rewards: set[str]) -> str:
        tags = item.get("tags", {})
        if "coupon_prefab" in prefabs:
            return "coupon"
        if "weapon_case_souvenirpkg" in prefabs:
            return "souvenir_package"
        if "ItemSet" in tags or "weapon_case" in prefabs or "weapon_case_selfopening_collection" in prefabs:
            return "weapon_case"
        if "PatchCapsule" in tags or "patch_capsule" in prefabs:
            return "patch_capsule"
        if "SprayCapsule" in tags or "graffiti_box" in prefabs:
            return "graffiti_container"
        if "StickerCapsule" in tags or "sticker_capsule" in prefabs:
            return "sticker_capsule"
        reward_types = {reward.rsplit("]", 1)[-1] for reward in rewards if reward.startswith("[")}
        return {
            frozenset({"sticker"}): "sticker_capsule",
            frozenset({"patch"}): "patch_capsule",
            frozenset({"spray"}): "graffiti_container",
            frozenset({"musickit"}): "music_kit_container",
            frozenset({"keychain"}): "charm_container",
        }.get(frozenset(reward_types), "container")

    def __call__(self) -> dict[str, dict[str, Any]]:
        item_ids = {data["name"]: key for key, data in self.items_game["items"].items() if key.isdigit()}
        paint_ids = {data["name"]: key for key, data in self.items_game["paint_kits"].items()}
        kit_ids = {data["name"]: key for key, data in self.items_game["sticker_kits"].items()}
        music_ids = {data["name"]: key for key, data in self.items_game["music_definitions"].items()}
        charm_ids = {data["name"]: key for key, data in self.items_game["keychain_definitions"].items()}
        containers = {}

        for defindex, item in self.items_game["items"].items():
            prefabs = self._prefab_chain(item)
            if not defindex.isdigit() or "weapon_case_base" not in prefabs:
                continue
            names = self._loot_list_names(item)
            rewards, highlight_charms = self._loot(names)
            container: dict[str, Any] = {"kind": self._kind(item, prefabs, rewards)}
            if tag := item.get("tags", {}).get("ItemSet"):
                collection_id = tag["tag_value"]
                container["collection"] = collection_id
                rewards.update(self.items_game["item_sets"][collection_id]["items"])

            members: dict[str, set[str]] = {"items": set(), "kits": set(), "musics": set(), "charms": set()}
            for reward in rewards:
                if reward.startswith("["):
                    kit, definition = reward[1:].split("]", maxsplit=1)
                    if definition in {"sticker", "patch", "spray"}:
                        members["kits"].add(kit_ids[kit])
                    elif definition == "musickit":
                        members["musics"].add(music_ids[kit])
                    elif definition == "keychain":
                        members["charms"].add(charm_ids[kit])
                    else:
                        members["items"].add(f"[{paint_ids[kit]}]{item_ids[definition]}")
                elif reward in item_ids:
                    # A coupon can award another container; do not flatten that item's contents.
                    members["items"].add(item_ids[reward])
            for field, values in members.items():
                if values:
                    container[field] = sorted(values)

            if associated := item.get("associated_items"):
                if len(associated) != 1:
                    raise ValueError(f"Multiple associated items for container {defindex}: {associated}")
                container["associated"] = next(iter(associated))

            # Only the item or its explicitly selected root loot list establishes this flag.
            if "will_produce_stattrak" in item:
                flags = {item["will_produce_stattrak"]}
            else:
                flags = {
                    self.items_game["client_loot_lists"][name]["will_produce_stattrak"]
                    for name in names
                    if "will_produce_stattrak" in self.items_game["client_loot_lists"][name]
                }
            if flags:
                if len(flags) != 1 or not flags <= {"0", "1"}:
                    raise ValueError(f"Conflicting or unknown StatTrak reward flag for container {defindex}: {flags}")
                container["will_produce_stattrak"] = flags == {"1"}
            if highlight_charms:
                container["highlight_charms"] = sorted(charm_ids[name] for name in highlight_charms)
            containers[defindex] = container

        return containers
