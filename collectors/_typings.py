from typing import Any, TypeAlias

_DEF_DICT: TypeAlias = "dict[str, str]"

ITEMS_GAME: TypeAlias = "dict[str, dict[str, Any]]"
CSGO_ENGLISH: TypeAlias = _DEF_DICT
ITEMS_CDN: TypeAlias = _DEF_DICT
ITEMS_SCHEMA: TypeAlias = "dict[str, dict[str, Any] | list[dict]]"

PAINTS: TypeAlias = _DEF_DICT
TYPES: TypeAlias = "dict[str, _DEF_DICT]"
CATEGORIES: TypeAlias = _DEF_DICT
CASES: TypeAlias = "dict[str, dict[str | list[str]]]"
PHASES: TypeAlias = _DEF_DICT
PHASES_MAPPING: TypeAlias = _DEF_DICT
