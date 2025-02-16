from datetime import date
from pathlib import Path
from time import sleep

import typer
import yaml
from dataingest import GameIngest, PlayerIngest, SeasonIngest
from loguru import logger
from rich.progress import track
from typing_extensions import Annotated

app = typer.Typer()


@app.command()
def get_player_data(
    data_to_pull_path: Annotated[
        Path,
        typer.Argument(
            help="Path to data to pull yaml file", file_okay=True, dir_okay=False
        ),
    ] = Path("data/meta/data_to_pull.yaml"),
    player_save_folder: Annotated[
        Path,
        typer.Argument(help="Path to save player data", file_okay=False, dir_okay=True),
    ] = Path("data/nba/PLAYER/"),
    player_error_log_path: Annotated[
        Path,
        typer.Argument(help="Path to save error log", file_okay=False, dir_okay=True),
    ] = Path("data/logs/PLAYER/"),
):
    logger.info("Loading data to pull yaml file")
    with open(data_to_pull_path, "r") as file:
        data_to_pull = yaml.safe_load(file)

    player_ids = data_to_pull.get("player")

    error_log = {}

    logger.info("Pulling player data")
    for player_id in track(player_ids):
        try:
            player_ingest = PlayerIngest(
                player=player_id, save_folder=player_save_folder
            )
        except ValueError as e:
            logger.error(f"Error for {player_id} - {e}")
            error_log[player_id] = e
            continue

        player_ingest.save_all()
        sleep(1)

    logger.info("Saving error log")
    with open(player_error_log_path.joinpath(str(date.today())), "w") as file:
        yaml.dump(error_log, file)


@app.command()
def get_season_data(
    data_to_pull_path: Annotated[
        Path,
        typer.Argument(
            help="Path to data to pull yaml file", file_okay=True, dir_okay=False
        ),
    ] = Path("data/meta/data_to_pull.yaml"),
    season_save_folder: Annotated[
        Path,
        typer.Argument(help="Path to save season data", file_okay=False, dir_okay=True),
    ] = Path("data/nba/SEASON/"),
    season_error_log_path: Annotated[
        Path,
        typer.Argument(help="Path to save error log", file_okay=False, dir_okay=True),
    ] = Path("data/logs/SEASON/"),
):
    logger.info("Loading data to pull yaml file")
    with open(data_to_pull_path, "r") as file:
        data_to_pull = yaml.safe_load(file)

    error_log = {}

    season_ids = data_to_pull.get("season")

    logger.info("Getting data for per game - regular season")
    season_ids_regular_season_pergame = season_ids["per_game"]["regular_season"]
    season_ids_regular_season_pergame_outpath = season_save_folder.joinpath(
        "PER_GAME"
    ).joinpath("REGULAR_SEASON")

    # Get regular season per game data
    error_log["regular_season_pergame"] = {}
    for season_id in track(season_ids_regular_season_pergame):
        try:
            season_ingest = SeasonIngest(
                season_year=season_id[0:4],  # Expects season year not season id
                save_folder=season_ids_regular_season_pergame_outpath,
                playoffs=False,
                permode="PERGAME",
            )
        except Exception as e:
            logger.error(f"Error for {season_id} - {e}")
            error_log["regular_season_pergame"][season_id] = e
            continue

        season_ingest.save_all_nonsynergy()
        season_ingest.save_all_synergy()
        sleep(1)

    # Get playoffs per game data
    logger.info("Getting data for per game - playoffs")
    season_ids_playoffs_pergame = season_ids["per_game"]["playoffs"]
    season_ids_playoffs_pergame_outpath = season_save_folder.joinpath(
        "PER_GAME"
    ).joinpath("PLAYOFFS")

    error_log["playoffs_pergame"] = {}
    for season_id in track(season_ids_playoffs_pergame):
        try:
            season_ingest = SeasonIngest(
                season_year=season_id[0:4],  # Expects season year not season id
                save_folder=season_ids_playoffs_pergame_outpath,
                playoffs=True,
                permode="PERGAME",
            )
        except Exception as e:
            logger.error(f"Error for {season_id} - {e}")
            error_log["playoffs_pergame"][season_id] = e
            continue

        season_ingest.save_all_nonsynergy()
        season_ingest.save_all_synergy()
        sleep(1)

    # Get regular season per possession data
    logger.info("Getting data for per possession - regular season")
    season_ids_regular_season_perpossession = season_ids["per_possession"][
        "regular_season"
    ]
    season_ids_regular_season_perpossession_outpath = season_save_folder.joinpath(
        "PER_POSSESSION"
    ).joinpath("REGULAR_SEASON")

    error_log["regular_season_perpossession"] = {}
    for season_id in track(season_ids_regular_season_perpossession):
        try:
            season_ingest = SeasonIngest(
                season_year=season_id[0:4],  # Expects season year not season id
                save_folder=season_ids_regular_season_perpossession_outpath,
                playoffs=False,
                permode="PER100POSSESSIONS",
            )
        except Exception as e:
            logger.error(f"Error for {season_id} - {e}")
            error_log["regular_season_perpossession"][season_id] = e
            continue

        season_ingest.save_all_nonsynergy()
        season_ingest.save_all_synergy()
        sleep(1)

    # Get playoffs per possession data
    logger.info("Getting data for per possession - playoffs")
    season_ids_playoffs_perpossession = season_ids["per_possession"]["playoffs"]
    season_ids_playoffs_perpossession_outpath = season_save_folder.joinpath(
        "PER_POSSESSION"
    ).joinpath("PLAYOFFS")

    error_log["playoffs_perpossession"] = {}
    for season_id in track(season_ids_playoffs_perpossession):
        try:
            season_ingest = SeasonIngest(
                season_year=season_id[0:4],  # Expects season year not season id
                save_folder=season_ids_playoffs_perpossession_outpath,
                playoffs=True,
                permode="PER100POSSESSIONS",
            )
        except Exception as e:
            logger.error(f"Error for {season_id} - {e}")
            error_log["playoffs_perpossession"][season_id] = e
            continue

        season_ingest.save_all_nonsynergy()
        season_ingest.save_all_synergy()
        sleep(1)

    logger.info("Saving error log")
    with open(season_error_log_path.joinpath(str(date.today())), "w") as file:
        yaml.dump(error_log, file)


# TODO:
# -- Pull in data_to_pull yaml file
# -- For each ID, use the data_ingest process from dataingest and check save_historical.py

if __name__ == "__main__":
    app()
