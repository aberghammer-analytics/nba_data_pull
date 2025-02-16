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
    ],
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


# TODO:
# -- Pull in data_to_pull yaml file
# -- For each ID, use the data_ingest process from dataingest and check save_historical.py

if __name__ == "__main__":
    app()
