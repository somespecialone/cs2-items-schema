from dataclasses import dataclass
from typing import Any

from . import typings


@dataclass(eq=False, repr=False)
class CatalogCollector:
    """Collect charms, highlight reels, and tournament lookup identities."""

    items_game: typings.ITEMS_GAME
    csgo_english: typings.CSGO_ENGLISH

    def _localized(self, key: str | None) -> str | None:
        if not key:
            return None
        return self.csgo_english.get(key.removeprefix("#"))

    def _charm_fields(
        self,
        charm: dict[str, Any],
        charms_by_name: dict[str, dict[str, Any]],
        seen: set[str] | None = None,
    ) -> dict[str, Any]:
        """Inherit classification metadata that source charm variants omit."""
        inherited = {field: charm[field] for field in ("item_rarity", "item_quality") if field in charm}
        base_name = charm.get("base")
        if not base_name or base_name in (seen or set()):
            return inherited

        base = charms_by_name.get(base_name)
        if base is None:
            return inherited

        base_fields = self._charm_fields(base, charms_by_name, (seen or set()) | {base_name})
        for field, value in base_fields.items():
            inherited.setdefault(field, value)
        return inherited

    def _collect_charms(self) -> dict[str, dict[str, str]]:
        charm_definitions = self.items_game["keychain_definitions"]
        charms_by_name = {data["name"]: data for data in charm_definitions.values() if "name" in data}
        charm_ids_by_name = {data["name"]: charm_id for charm_id, data in charm_definitions.items() if "name" in data}
        highlight_ids_by_key = {
            data["id"]: highlight_id
            for highlight_id, data in self.items_game["highlight_reels"].items()
            if "id" in data
        }
        rarities = self.items_game["rarities"]
        qualities = self.items_game["qualities"]
        charms: dict[str, dict[str, str]] = {}

        for charm_id, charm in charm_definitions.items():
            fields = self._charm_fields(charm, charms_by_name)
            catalog_charm = {}
            base_id = charm_ids_by_name.get(charm.get("base"))

            if name := self._localized(charm.get("loc_name")):
                catalog_charm["name"] = name
            if not base_id and (description := self._localized(charm.get("loc_description"))):
                catalog_charm["description"] = description

            rarity = fields.get("item_rarity")
            if rarity in rarities:
                catalog_charm["rarity"] = rarity
            quality = fields.get("item_quality")
            if quality in qualities:
                catalog_charm["quality"] = quality

            if base_id:
                catalog_charm["base"] = base_id
            if highlight_id := highlight_ids_by_key.get(charm.get("highlight_reel")):
                catalog_charm["highlight"] = highlight_id

            charms[charm_id] = catalog_charm

        return charms

    def _collect_highlights(self) -> dict[str, dict[str, str]]:
        return {
            highlight_id: {
                "key": highlight["id"],
                "event": highlight["tournament event id"],
                "stage": highlight["tournament event stage id"],
                "map": highlight["map"],
                "team0": highlight["tournament event team0 id"],
                "team1": highlight["tournament event team1 id"],
            }
            for highlight_id, highlight in self.items_game["highlight_reels"].items()
        }

    def _referenced_tournament_ids(self) -> tuple[set[str], set[str], set[str], set[str]]:
        events: set[str] = set()
        stages: set[str] = set()
        teams: set[str] = set()
        players: set[str] = set()

        for highlight in self.items_game["highlight_reels"].values():
            events.add(highlight["tournament event id"])
            stages.add(highlight["tournament event stage id"])
            teams.update((highlight["tournament event team0 id"], highlight["tournament event team1 id"]))

        for sticker_kit in self.items_game["sticker_kits"].values():
            event_id = sticker_kit.get("tournament_event_id")
            if event_id is not None:
                events.add(event_id)
            team_id = sticker_kit.get("tournament_team_id")
            if team_id is not None:
                teams.add(team_id)
            player_id = sticker_kit.get("tournament_player_id")
            if player_id is not None:
                players.add(player_id)

        for player in self.items_game["pro_players"].values():
            for event_id, event in player.get("events", {}).items():
                events.add(event_id)
                team_id = event.get("team")
                if team_id is not None:
                    teams.add(team_id)

        return events, stages, teams, players

    def _collect_events_and_stages(
        self, referenced_events: set[str], referenced_stages: set[str]
    ) -> tuple[dict[str, dict[str, str]], dict[str, str]]:
        events = set(referenced_events)
        stages = set(referenced_stages)
        event_names = "CSGO_Tournament_Event_Name_"
        event_short_names = "CSGO_Tournament_Event_NameShort_"
        stage_names = "CSGO_Tournament_Event_Stage_"

        for localization_key in self.csgo_english:
            for prefix, identities in (
                (event_names, events),
                (event_short_names, events),
                (stage_names, stages),
            ):
                if localization_key.startswith(prefix) and (identifier := localization_key[len(prefix) :]).isdigit():
                    identities.add(identifier)

        tournament_events: dict[str, dict[str, str]] = {}
        for event_id in events:
            event = {}
            if name := self.csgo_english.get(event_names + event_id):
                event["name"] = name
            if short_name := self.csgo_english.get(event_short_names + event_id):
                event["short_name"] = short_name
            tournament_events[event_id] = event

        tournament_stages = {stage_id: self.csgo_english[stage_names + stage_id] for stage_id in stages}

        return tournament_events, tournament_stages

    def _collect_teams_and_players(
        self, referenced_teams: set[str], referenced_players: set[str]
    ) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
        tournament_teams: dict[str, dict[str, str]] = {}
        for team_id in set(self.items_game["pro_teams"]) | referenced_teams:
            source_team = self.items_game["pro_teams"].get(team_id, {})
            team = {}
            if tag := source_team.get("tag"):
                team["tag"] = tag
            if source_team.get("geo"):
                team["geo"] = source_team["geo"]
            tournament_teams[team_id] = team

        tournament_players: dict[str, dict[str, str]] = {}
        for player_id in set(self.items_game["pro_players"]) | referenced_players:
            source_player = self.items_game["pro_players"].get(player_id, {})
            player = {}
            if name := source_player.get("name"):
                player["name"] = name
            if source_player.get("geo"):
                player["geo"] = source_player["geo"]
            tournament_players[player_id] = player

        return tournament_teams, tournament_players

    def __call__(
        self,
    ) -> tuple[
        dict[str, dict[str, str]],
        dict[str, dict[str, str]],
        dict[str, dict[str, str]],
        dict[str, dict[str, str]],
        dict[str, dict[str, str]],
        dict[str, str],
    ]:
        charms = self._collect_charms()
        highlights = self._collect_highlights()
        referenced_events, referenced_stages, referenced_teams, referenced_players = self._referenced_tournament_ids()
        tournament_events, tournament_stages = self._collect_events_and_stages(referenced_events, referenced_stages)
        tournament_teams, tournament_players = self._collect_teams_and_players(referenced_teams, referenced_players)
        return (
            charms,
            highlights,
            tournament_events,
            tournament_teams,
            tournament_players,
            tournament_stages,
        )
