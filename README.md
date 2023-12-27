# CS2 Items Schema

[![license](https://img.shields.io/github/license/somespecialone/cs2-items-schema)](https://github.com/somespecialone/cs2-items-schema/blob/master/LICENSE)
[![Schema](https://github.com/somespecialone/cs2-items-schema/actions/workflows/schema.yml/badge.svg)](https://github.com/somespecialone/cs2-items-schema/actions/workflows/schema.yml)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![steam](https://shields.io/badge/steam-1b2838?logo=steam)](https://store.steampowered.com/)

This is storage repo of CS2 (ex. CSGO) items schema with attempt to create more understandable format
of Steam Economy CS2 items and their relations.

Feel free to use it if you need 😊

> [!NOTE]
> Contains data extracted from game files only.
> Includes not all items, **but almost all tradable items - must be inside** 📦

> [!TIP]
> If you are looking for an `itemnameid` of items for Steam Market,
> check out this repo [somespecialone/steam-item-name-ids](https://github.com/somespecialone/steam-item-name-ids)

## Integrity schema 🧾

Reflects `json` schemas and relationships between entities

![integrity](integrity.png)

## Diagram 📅

Diagram for SQL database

![diagram](diagram.png)

## TODO

- [x] Sticker capsules
- [x] Souvenir packages
- [x] Item sets
- [x] ~~Graffiti with tints~~
- [x] SQL scripts and schema

## Credits

* [csfloat/cs-files](https://github.com/csfloat/cs-files)
* [draw.io](https://draw.io)
* [dbdiagram.io](https://dbdiagram.io/)
