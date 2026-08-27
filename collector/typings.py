from typing import Any, TypeAlias

from multidict import CIMultiDict

_DEF_DICT: TypeAlias = "dict[str, str]"

ITEMS_GAME: TypeAlias = "dict[str, dict[str, Any]]"
CSGO_ENGLISH: TypeAlias = "CIMultiDict[str, str]"
ITEMS_CDN: TypeAlias = _DEF_DICT
