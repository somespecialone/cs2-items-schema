import re
from dataclasses import dataclass
from typing import Any

from . import typings

_LOCALIZATION_PLACEHOLDER_RE = re.compile(r"%s([1-9][0-9]*)")


@dataclass(eq=False, repr=False)
class TradeUpCollector:
    """Collect source-defined trade-up recipes without evaluating their rules."""

    items_game: typings.ITEMS_GAME
    csgo_english: typings.CSGO_ENGLISH

    @staticmethod
    def _source_bool(value: Any) -> bool:
        if value == "0" or value is False:
            return False
        if value == "1" or value is True:
            return True
        raise ValueError(f"Expected source boolean, got {value!r}")

    def _localize_name(self, recipe: dict[str, Any]) -> str | None:
        name_key = recipe.get("name")
        if not isinstance(name_key, str) or not name_key.startswith("#"):
            return None

        template = self.csgo_english.get(name_key[1:])
        if not isinstance(template, str):
            return None

        placeholders = _LOCALIZATION_PLACEHOLDER_RE.findall(template)
        if not placeholders:
            return template

        arguments: dict[str, str] = {}
        for placeholder in placeholders:
            argument_key = f"n_{chr(ord('A') + int(placeholder) - 1)}"
            argument = recipe.get(argument_key)
            if not isinstance(argument, str) or not argument.startswith("#"):
                return None

            localized_argument = self.csgo_english.get(argument[1:])
            if not isinstance(localized_argument, str):
                return None
            arguments[placeholder] = localized_argument

        return _LOCALIZATION_PLACEHOLDER_RE.sub(lambda match: arguments[match.group(1)], template)

    def _parse_conditions(self, conditions: dict[str, dict[str, Any]]) -> list[dict[str, str | bool]]:
        return [
            {
                "field": condition["field"],
                "operator": condition["operator"],
                "value": condition["value"],
                "required": self._source_bool(condition["required"]),
            }
            for condition in conditions.values()
        ]

    def _parse_inputs(self, input_items: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "count": int(count),
                "conditions": self._parse_conditions(input_data["conditions"]),
            }
            for count, input_data in input_items.items()
        ]

    def _parse_outputs(self, output_items: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "key": key,
                "conditions": self._parse_conditions(output_data["conditions"]),
            }
            for key, output_data in output_items.items()
        ]

    def __call__(self) -> dict[str, dict[str, Any]]:
        recipes = {}
        for recipe_id, recipe_data in self.items_game["recipes"].items():
            recipe = {
                "disabled": self._source_bool(recipe_data["disabled"]),
                "all_same_class": self._source_bool(recipe_data["all_same_class"]),
                "premium_only": self._source_bool(recipe_data["premium_only"]),
                "inputs": self._parse_inputs(recipe_data["input_items"]),
                "outputs": self._parse_outputs(recipe_data["output_items"]),
            }
            if name := self._localize_name(recipe_data):
                recipe["name"] = name

            recipes[recipe_id] = recipe

        return recipes
