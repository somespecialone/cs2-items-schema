from dataclasses import dataclass

from . import _types

from ._vpk_extractor import VpkExtractor


STICKER_FIX_NAMES: tuple[tuple[str, str]] = (("dignitas", "teamdignitas"),)


@dataclass(eq=False, repr=False)
class StickerPatchCollector:
    """Collect sticker kits :)"""

    pak: VpkExtractor

    items_game: _types.ITEMS_GAME
    csgo_english: _types.CSGO_ENGLISH

    @staticmethod
    def _fix_sticker_name(sticker_name: str) -> str:
        """Fix sticker name inconstancy. Valve's 'good' work..."""
        for sticker_names in STICKER_FIX_NAMES:
            if sticker_names[0] in sticker_name:
                return sticker_name.replace(sticker_names[0], sticker_names[1])

    def _parse_item(self, sticker_kit: dict[str, str], item_types: str, material_key: str) -> dict:
        item = {}
        try:
            item["name"] = self.csgo_english[sticker_kit["item_name"][1:].lower()]
        except KeyError:
            item["name"] = self.csgo_english[self._fix_sticker_name(sticker_kit["item_name"][1:].lower())]

        item["image"] = self.pak.get_image_url(item_types, sticker_kit[material_key + "_material"])
        # image_url_large = self._get_image_url(sticker_kit['sticker_material'], large=True)

        return item

    def __call__(self) -> tuple:
        stickers = {}
        patches = {}
        graffities = {}

        del self.items_game["sticker_kits"]["0"]  # delete unused sticker kit
        sticker_kit: dict[str, str]
        for sticker_index, sticker_kit in self.items_game["sticker_kits"].items():
            try:
                if "patch_" in sticker_kit["name"]:
                    patches.update({sticker_index: self._parse_item(sticker_kit, "patches", "patch")})
                elif "_graffiti" in sticker_kit["name"]:
                    graffities.update({sticker_index: self._parse_item(sticker_kit, "stickers", "sticker")})
                else:
                    stickers.update({sticker_index: self._parse_item(sticker_kit, "stickers", "sticker")})
            except KeyError:
                continue

        return stickers, patches, graffities
