import json
from pathlib import Path
from time import sleep

import pandas as pd
from loguru import logger
from nbastatpy.game import Game
from nbastatpy.player import Player
from nbastatpy.season import Season
from tqdm import tqdm


class NBADataMappings:
    PLAY_TYPES = {
        "TRANSITION": "Transition",
        "ISOLATION": "Isolation",
        "ISO": "Isolation",
        "PRBALLHANDLER": "PRBallHandler",
        "PRROLLMAN": "PRRollman",
        "POSTUP": "Postup",
        "SPOTUP": "Spotup",
        "HANDOFF": "Handoff",
        "CUT": "Cut",
        "OFFSCREEN": "OffScreen",
        "PUTBACKS": "OffRebound",
        "OFFREBOUND": "OffRebound",
        "MISC": "Misc",
    }

    TRACKING_TYPES = {
        "SPEEDDISTANCE": "SpeedDistance",
        "SPEED": "SpeedDistance",
        "DISTANCE": "SpeedDistance",
        "POSSESSIONS": "Possessions",
        "CATCHSHOOT": "CatchShoot",
        "PULLUPSHOT": "PullUpShot",
        "PULLUP": "PullUpShot",
        "DEFENSE": "Defense",
        "DRIVES": "Drives",
        "DRIVE": "Drives",
        "PASSING": "Passing",
        "ELBOWTOUCH": "ElbowTouch",
        "ELBOW": "ElbowTouch",
        "POSTTOUCH": "PostTouch",
        "POST": "PostTouch",
        "PAINTTOUCH": "PaintTouch",
        "PAINT": "PaintTouch",
        "EFFICIENCY": "Efficiency",
    }


class PlayerIngest(Player):
    def __init__(
        self,
        player: str,
        save_folder: Path,
        season_year: str = None,
        playoffs: bool = False,
        permode: str = "PERGAME",
        verbose: bool = False,
    ):
        super().__init__(
            player=player, season_year=season_year, playoffs=playoffs, permode=permode
        )

        self.save_folder = Path(save_folder).joinpath(
            str(self.id).upper().replace(" ", "").replace("-", "")
        )

        if not Path(self.save_folder).exists():
            if verbose:
                logger.info(f"Creating folder: {str(self.save_folder)}")
            Path(self.save_folder).mkdir(parents=True, exist_ok=True)

    def save_combine_stats(self):
        df = self.get_combine_stats()[0]
        df.to_csv(
            self.save_folder.joinpath(f"{str(self.id)}_combine_stats.csv"), index=False
        )

    def save_common_info(self):
        df = pd.DataFrame(self.get_common_info(), index=[self.id])
        df.to_csv(
            self.save_folder.joinpath(f"{str(self.id)}_common_info.csv"), index=False
        )

    def save_all(self, verbose: bool = False):
        log_file = {}
        total_tasks = 2
        progress_bar = tqdm(total=total_tasks, desc="Progress", unit="task")
        try:
            progress_bar.set_description("Getting Common Info")
            self.save_common_info()
            progress_bar.update(1)
            sleep(1)
        except Exception as e:
            log_file["common_info"] = str(e)
            logger.error(f"common_info: {str(e)}")

        try:
            progress_bar.set_description("Getting Combine Stats")
            self.save_combine_stats()
            progress_bar.update(1)
        except Exception as e:
            log_file["combine"] = str(e)
            if verbose:
                logger.error(f"combine: {str(e)}")

        progress_bar.close()
        with open(self.save_folder.joinpath("log.json"), "w") as json_file:
            json.dump(log_file, json_file, indent=4)


class SeasonIngest(Season):
    def __init__(
        self,
        season_year: str,
        save_folder: Path,
        playoffs=False,
        permode: str = "PERGAME",
        verbose: bool = False,
    ):
        super().__init__(season_year=season_year, playoffs=playoffs, permode=permode)

        self.season_id = self.season.upper().replace(" ", "").replace("-", "")
        self.save_folder = Path(save_folder).joinpath(str(self.season_id))

        if not Path(self.save_folder).exists():
            if verbose:
                logger.info(f"Creating folder: {str(self.save_folder)}")
            Path(self.save_folder).mkdir(parents=True, exist_ok=True)

    def save_defense_player(self):
        df = self.get_defense_player()
        df.to_csv(
            self.save_folder.joinpath(f"{self.season_id}_player_defense.csv"),
            index=False,
        )

    def save_defense_team(self):
        df = self.get_defense_team()
        df.to_csv(
            self.save_folder.joinpath(f"{self.season_id}_team_defense.csv"), index=False
        )

    def save_lineup_details(self):
        df = self.get_lineup_details()
        df.to_csv(
            self.save_folder.joinpath(f"{self.season_id}_lineup_details.csv"),
            index=False,
        )

    def save_lineups(self):
        df = self.get_lineups()
        df.to_csv(
            self.save_folder.joinpath(f"{self.season_id}_lineups.csv"),
            index=False,
        )

    def save_opponent_shooting(self):
        df = self.get_opponent_shooting()
        df.to_csv(
            self.save_folder.joinpath(f"{self.season_id}_opponent_shooting.csv"),
            index=False,
        )

    def save_player_clutch(self):
        df = self.get_player_clutch()
        df.to_csv(
            self.save_folder.joinpath(f"{self.season_id}_player_clutch.csv"),
            index=False,
        )

    def save_player_games(self):
        df = self.get_player_games()
        df.to_csv(
            self.save_folder.joinpath(f"{self.season_id}_player_games.csv"),
            index=False,
        )

    def save_player_hustle(self):
        df = self.get_player_hustle()
        df.to_csv(
            self.save_folder.joinpath(f"{self.season_id}_player_hustle.csv"),
            index=False,
        )

    def save_player_matchups(self):
        df = self.get_player_matchups()
        df.to_csv(
            self.save_folder.joinpath(f"{self.season_id}_player_matchups.csv"),
            index=False,
        )

    def save_player_shot_locations(self):
        df = self.get_player_shot_locations()
        df.to_csv(
            self.save_folder.joinpath(f"{self.season_id}_player_shot_locations.csv"),
            index=False,
        )

    def save_player_shots(self):
        df = self.get_player_shots()
        df.to_csv(
            self.save_folder.joinpath(f"{self.season_id}_player_shots.csv"),
            index=False,
        )

    def save_player_stats(self):
        df = self.get_player_stats()
        df.to_csv(
            self.save_folder.joinpath(f"{self.season_id}_player_stats.csv"),
            index=False,
        )

    def save_salaries(self):
        df = self.get_salaries()
        df.to_csv(
            self.save_folder.joinpath(f"{self.season_id}_salaries.csv"),
            index=False,
        )

    def save_team_clutch(self):
        df = self.get_team_clutch()
        df.to_csv(
            self.save_folder.joinpath(f"{self.season_id}_team_clutch.csv"),
            index=False,
        )

    def save_team_games(self):
        df = self.get_team_games()
        df.to_csv(
            self.save_folder.joinpath(f"{self.season_id}_team_games.csv"),
            index=False,
        )

    def save_team_hustle(self):
        df = self.get_team_hustle()
        df.to_csv(
            self.save_folder.joinpath(f"{self.season_id}_team_hustle.csv"),
            index=False,
        )

    def save_team_shot_locations(self):
        df = self.get_team_shot_locations()
        df.to_csv(
            self.save_folder.joinpath(f"{self.season_id}_team_shot_locations.csv"),
            index=False,
        )

    def save_team_stats(self):
        df = self.get_team_stats()
        df.to_csv(
            self.save_folder.joinpath(f"{self.season_id}_team_stats.csv"),
            index=False,
        )

    def save_synergy_player(self, synergy_type: str):
        df = self.get_synergy_player(synergy_type)
        df.to_csv(
            self.save_folder.joinpath(f"{self.season_id}_{synergy_type}_player.csv"),
            index=False,
        )

    def save_tracking_player(self, tracking_type: str):
        df = self.get_tracking_player(tracking_type)
        df.to_csv(
            self.save_folder.joinpath(f"{self.season_id}_{tracking_type}_player.csv"),
            index=False,
        )

    def save_synergy_team(self, synergy_type: str):
        df = self.get_synergy_team(synergy_type)
        df.to_csv(
            self.save_folder.joinpath(f"{self.season_id}_{synergy_type}_team.csv"),
            index=False,
        )

    def save_tracking_team(self, tracking_type: str):
        df = self.get_tracking_team(tracking_type)
        df.to_csv(
            self.save_folder.joinpath(f"{self.season_id}_{tracking_type}_team.csv"),
            index=False,
        )

    def save_all_nonsynergy(self, verbose: bool = False):
        log_file = {}
        total_tasks = 18
        progress_bar = tqdm(total=total_tasks, desc="Progress", unit="task")

        steps = [
            ("Getting Player Defense", self.save_defense_player),
            ("Getting Team Defense", self.save_defense_team),
            ("Getting Lineup Details", self.save_lineup_details),
            ("Getting Lineups", self.save_lineups),
            ("Getting Opponent Shooting", self.save_opponent_shooting),
            ("Getting Player Clutch", self.save_player_clutch),
            ("Getting Player Games", self.save_player_games),
            ("Getting Player Hustle", self.save_player_hustle),
            ("Getting Player Matchups", self.save_player_matchups),
            ("Getting Player Shot Locations", self.save_player_shot_locations),
            ("Getting Player Shots", self.save_player_shots),
            ("Getting Player Stats", self.save_player_stats),
            ("Getting Salaries", self.save_salaries),
            ("Getting Team Clutch", self.save_team_clutch),
            ("Getting Team Games", self.save_team_games),
            ("Getting Team Hustle", self.save_team_hustle),
            ("Getting Team Shot Locations", self.save_team_shot_locations),
            ("Getting Team Stats", self.save_team_stats),
        ]

        for desc, func in steps:
            try:
                progress_bar.set_description(desc)
                func()  # Call the corresponding save function
                progress_bar.update(1)
                sleep(1)
            except Exception as e:
                if verbose:
                    logger.error(f"An error occurred in {desc}: {e}")
                log_file[str(desc)] = str(e)
                # Optionally, handle the error differently if needed

        progress_bar.close()
        with open(self.save_folder.joinpath("log_nonsynergy.json"), "w") as json_file:
            json.dump(log_file, json_file, indent=4)

    def save_all_synergy(self, verbose: bool = False):
        log_file = {}
        tracking_types = set(NBADataMappings.TRACKING_TYPES.values())
        play_types = set(NBADataMappings.PLAY_TYPES.values())

        total_tasks = len(play_types)
        progress_bar = tqdm(total=total_tasks, desc="Progress", unit="task")

        for play_type in play_types:
            try:
                progress_bar.set_description(f"Getting Player {play_type}")
                self.save_synergy_player(play_type)
                sleep(1)
            except Exception as e:
                log_file[str(play_type) + "_player"] = str(e)
                if verbose:
                    logger.error(f"{play_type}_PLAYER: {str(e)}")

            try:
                progress_bar.set_description(f"Getting Team {play_type}")
                self.save_synergy_team(play_type)
                progress_bar.update(1)
                sleep(1)
            except Exception as e:
                log_file[str(play_type) + "_team"] = str(e)
                if verbose:
                    logger.error(f"{play_type}_TEAM: {str(e)}")

        progress_bar.close()

        total_tasks = len(tracking_types)
        progress_bar = tqdm(total=total_tasks, desc="Progress", unit="task")

        for tracking_type in tracking_types:
            try:
                progress_bar.set_description(f"Getting Player {tracking_type}")
                self.save_tracking_player(tracking_type)
                sleep(1)
            except Exception as e:
                log_file[str(tracking_type) + "_player"] = str(e)
                if verbose:
                    logger.error(f"{tracking_type}: {str(e)}")

            try:
                progress_bar.set_description(f"Getting Team {tracking_type}")
                self.save_tracking_team(tracking_type)
                progress_bar.update(1)
                sleep(1)
            except Exception as e:
                log_file[str(tracking_type) + "_team"] = str(e)
                if verbose:
                    logger.error(f"{tracking_type}: {str(e)}")

        progress_bar.close()
        with open(self.save_folder.joinpath("log_synergy.json"), "w") as json_file:
            json.dump(log_file, json_file, indent=4)


class GameIngest(Game):
    def __init__(self, game_id: str, save_folder: Path, verbose: bool = False):
        super().__init__(game_id=game_id)
        self.game_id = game_id

        self.save_folder = (
            Path(save_folder).joinpath("GAME").joinpath(str(self.game_id))
        )

        if not Path(self.save_folder).exists():
            if verbose:
                logger.info(f"Creating folder: {str(self.save_folder)}")
            Path(self.save_folder).mkdir(parents=True, exist_ok=True)

    def save_advanced(self):
        df = self.get_advanced()[0]
        df.to_csv(
            self.save_folder.joinpath(f"{self.game_id}_advanced.csv"),
            index=False,
        )

    def save_defense(self):
        df = self.get_defense()[0]
        df.to_csv(
            self.save_folder.joinpath(f"{self.game_id}_defense.csv"),
            index=False,
        )

    def save_hustle(self):
        df = self.get_hustle()[0]
        df.to_csv(
            self.save_folder.joinpath(f"{self.game_id}_hustle.csv"),
            index=False,
        )

    def save_matchups(self):
        df = self.get_matchups()[0]
        df.to_csv(
            self.save_folder.joinpath(f"{self.game_id}_matchups.csv"),
            index=False,
        )

    def save_playbyplay(self):
        df = self.get_playbyplay()
        df.to_csv(
            self.save_folder.joinpath(f"{self.game_id}_playbyplay.csv"),
            index=False,
        )

    def save_tracking(self):
        df = self.get_playertrack()[0]
        df.to_csv(
            self.save_folder.joinpath(f"{self.game_id}_tracking.csv"),
            index=False,
        )

    def save_rotations(self):
        df = self.get_rotations()
        df.to_csv(
            self.save_folder.joinpath(f"{self.game_id}_rotations.csv"),
            index=False,
        )

    def save_scoring(self):
        df = self.get_scoring()[0]
        df.to_csv(
            self.save_folder.joinpath(f"{self.game_id}_scoring.csv"),
            index=False,
        )

    def save_usage(self):
        df = self.get_usage()[0]
        df.to_csv(
            self.save_folder.joinpath(f"{self.game_id}_usage.csv"),
            index=False,
        )

    def save_all(self, verbose: bool = False):
        log_file = {}
        total_tasks = 9
        progress_bar = tqdm(total=total_tasks, desc="Progress", unit="task")

        steps = [
            ("Getting Advanced", self.save_advanced),
            ("Getting Defense", self.save_defense),
            ("Getting Hustle", self.save_hustle),
            ("Getting Matchups", self.save_matchups),
            ("Getting Play by Play", self.save_playbyplay),
            ("Getting Tracking", self.save_tracking),
            ("Getting Rotations", self.save_rotations),
            ("Getting Scoring", self.save_scoring),
            ("Getting Usage", self.save_usage),
        ]

        for desc, func in steps:
            try:
                progress_bar.set_description(desc)
                func()  # Call the corresponding save function
                progress_bar.update(1)
                sleep(1)
            except Exception as e:
                if verbose:
                    logger.error(f"An error occurred in {desc}: {e}")
                log_file[str(desc)] = str(e)
                # Optionally, you can handle specific exceptions or log them differently

        progress_bar.close()
        with open(self.save_folder.joinpath("log.json"), "w") as json_file:
            json.dump(log_file, json_file, indent=4)
