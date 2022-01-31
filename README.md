## csgo-items-db

This is schema storage repo of CSGO items schema. Feel free to used it if you need 😊

To collect data you need `.env` file in project root dir with yours `STEAM_API_KEY` field. Just start `collect.py`
script with one argument - path to `pak01_dir.vpk` file which live in `CSGO/csgo` directory. Example:

```shell
python ./collect.py ".../Steam/steamapps/common/Counter-Strike Global Offensive/csgo/pak01_dir.vpk"
```
