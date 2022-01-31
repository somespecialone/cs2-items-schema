from dataclasses import dataclass
import hashlib

from vpk import VPK, VPKFile


@dataclass(eq=False, repr=False)
class VpkExtractor:
    vpk_source: VPK

    # https://stackoverflow.com/a/22058673
    @staticmethod
    def _make_hash(vpk_file: VPKFile, buf_size=65536):
        sha1 = hashlib.sha1()
        while True:
            data = vpk_file.read(buf_size)
            if not data:
                break
            sha1.update(data)

        return sha1.hexdigest()

    def get_image_url(self, dir_name: str, material: str, large=False) -> str:
        postfix = "_large.png" if large else ".png"
        image_path = "/" + material.lower() + postfix
        image_file = self.vpk_source.get_file('resource/flash/econ/' + dir_name + image_path)
        image_hash = self._make_hash(image_file)
        image_url = image_path.replace('.png', f'.{image_hash}.png')
        return 'https://steamcdn-a.akamaihd.net/apps/730/icons/econ/' + dir_name + image_url
