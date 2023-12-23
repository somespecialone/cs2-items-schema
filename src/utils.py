import hashlib
from typing import IO


def invert_dict(mapping: dict[str, ...], key: str = None) -> dict[str, ...]:
    return {(v if key is None else v[key]): k for k, v in mapping.items()}


# https://stackoverflow.com/a/22058673
# Mega rare function that make hashsum used in steam static items url
# https://steamcdn-a.akamaihd.net/apps/730/icons/econ/{dir}/{image_path}.{hash}.png
def make_steam_static_item_hash(f: IO, buf_size=65536) -> str:
    sha1 = hashlib.sha1()
    while True:
        data = f.read(buf_size)
        if not data:
            break
        sha1.update(data)

    return sha1.hexdigest()
