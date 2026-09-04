from typing import Any, TypeAlias

from multidict import CIMultiDict

ITEMS_GAME: TypeAlias = "dict[str, dict[str, Any]]"
CSGO_ENGLISH: TypeAlias = "CIMultiDict[str, str]"
ITEM_IDENTITIES: TypeAlias = set[str]
