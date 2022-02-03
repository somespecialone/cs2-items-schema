from pathlib import Path

from collectors.resource_collector import ResourceCollector

if __name__ == "__main__":
    import asyncio
    import platform
    from argparse import ArgumentParser

    from environs import Env

    env = Env()
    env.read_env()

    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # getting command line argument
    parser = ArgumentParser(description="Collect all resources")
    parser.add_argument("vpk_path", type=Path, help="Absolute path to pak01_dir.vpk file")

    args = parser.parse_args()

    RES_DIR = Path("./schemas").resolve()
    params = {
        "RES_DIR": RES_DIR,
        "ITEMS_GAME_URL": env.str(
            "ITEMS_GAME_URL",
            "https://raw.githubusercontent.com/SteamDatabase/GameTracking-CSGO/master/csgo/scripts/items/items_game.txt",
        ),
        "CSGO_ENGLISH_URL": env.str(
            "CSGO_ENGLISH_URL",
            "https://raw.githubusercontent.com/SteamDatabase/GameTracking-CSGO/master/csgo/resource/csgo_english.txt",
        ),
        "ITEMS_GAME_CDN_URL": env.str(
            "ITEMS_GAME_CDN_URL",
            "https://raw.githubusercontent.com/SteamDatabase/GameTracking-CSGO/master/csgo/scripts/items/items_game_cdn.txt",
        ),
        "ITEMS_SCHEMA_URL": env.str(
            "ITEMS_SCHEMA_URL",
            "https://api.steampowered.com/IEconItems_730/GetSchema/v2/?key=" + env.str("STEAM_API_KEY"),
        ),
        "vpk_path": args.vpk_path.resolve(),
        "categories_path": RES_DIR / "categories.json",
        "phases_mapping_path": RES_DIR / "_phases_mapping.json",
    }
    resource_collector = ResourceCollector(**params)
    asyncio.run(resource_collector.collect())
