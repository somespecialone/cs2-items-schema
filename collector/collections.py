from dataclasses import dataclass, field
from typing import Any

from . import typings


@dataclass(repr=False, eq=False)
class CollectionsCollector:
    """Collect source item sets with normalized item identifiers."""

    items_game: typings.ITEMS_GAME
    csgo_english: typings.CSGO_ENGLISH
    definitions: dict[str, dict[str, str]]
    paints: dict[str, dict[str, Any]]

    unresolved_members: list[tuple[str, str]] = field(default_factory=list, init=False)
    unresolved_unusuals: list[tuple[str, str]] = field(default_factory=list, init=False)

    @staticmethod
    def _unique_ids_by_name(entries: dict[str, dict[str, Any]], allowed_ids: set[str] | None = None) -> dict[str, str]:
        ids_by_name: dict[str, set[str]] = {}
        for identifier, entry in entries.items():
            if allowed_ids is not None and identifier not in allowed_ids:
                continue
            if name := entry.get("name"):
                ids_by_name.setdefault(name, set()).add(identifier)

        return {name: next(iter(identifiers)) for name, identifiers in ids_by_name.items() if len(identifiers) == 1}

    def _resolve_member(
        self,
        member: str,
        definition_ids: dict[str, str],
        bare_item_ids: dict[str, str],
        paint_ids: dict[str, str],
    ) -> str | None:
        if not member.startswith("["):
            return bare_item_ids.get(member)

        try:
            paint_name, item_name = member[1:].split("]", maxsplit=1)
        except ValueError:
            return None

        paint_id = paint_ids.get(paint_name)
        definition_id = definition_ids.get(item_name)
        if paint_id is None or definition_id is None:
            return None

        return f"[{paint_id}]{definition_id}"

    def __call__(self) -> dict[str, dict[str, Any]]:
        """Parse source item sets without resolving their loot-list rewards."""
        definition_ids = self._unique_ids_by_name(self.items_game["items"], set(self.definitions))
        bare_item_ids = self._unique_ids_by_name(self.items_game["items"])
        paint_ids = self._unique_ids_by_name(self.items_game["paint_kits"], set(self.paints))
        collections = {}
        self.unresolved_members.clear()
        self.unresolved_unusuals.clear()

        for set_key, set_data in self.items_game["item_sets"].items():
            collection = {}
            if (name_key := set_data.get("name")) and (name := self.csgo_english.get(name_key.removeprefix("#"))):
                collection["name"] = name
            if "is_hidden_set" in set_data:
                collection["hidden"] = set_data["is_hidden_set"] == "1"

            items = set()
            for member in set_data.get("items", {}):
                item = self._resolve_member(member, definition_ids, bare_item_ids, paint_ids)
                if item is None:
                    self.unresolved_members.append((set_key, member))
                else:
                    items.add(item)
            collection["items"] = sorted(items)

            unusuals = {}
            for quality_key, loot_list_name in set_data.get("unusuals", {}).items():
                try:
                    self.items_game["qualities"][quality_key]
                except KeyError:
                    self.unresolved_unusuals.append((set_key, quality_key))
                else:
                    unusuals[quality_key] = loot_list_name
            if unusuals:
                collection["unusuals"] = dict(sorted(unusuals.items()))

            collections[set_key] = collection

        return collections
