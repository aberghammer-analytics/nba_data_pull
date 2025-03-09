import os
from datetime import date, datetime
from pathlib import Path
from time import sleep

import boto3
import typer
import yaml
from dotenv import load_dotenv
from loguru import logger
from rich.progress import track
from typing_extensions import Annotated, Dict, Literal

from nba_data_pull.data_pull.dataingest import GameIngest, PlayerIngest, SeasonIngest

app = typer.Typer()

load_dotenv()


class SeasonYear:
    current_datetime = datetime.now()
    current_season_year = current_datetime.year
    if current_datetime.month <= 9:
        current_season_year -= 1

    default = current_season_year


def load_yaml_s3(file_path: str, bucket_name: str, s3_client: boto3.client) -> dict:
    response = s3_client.get_object(Bucket=bucket_name, Key=str(file_path))
    yaml_content = response["Body"].read().decode("utf-8")
    return yaml.safe_load(yaml_content)


@app.command()
def get_player_data(
    data_to_pull_path: Annotated[
        Path,
        typer.Argument(
            help="Path to data to pull yaml file", file_okay=True, dir_okay=False
        ),
    ] = Path("data/meta/data_to_pull.yaml"),
    player_error_log_path: Annotated[
        str,
        typer.Argument(help="Path to save error log", file_okay=False, dir_okay=True),
    ] = "data/logs/PLAYER",
):
    bucket_name = os.getenv("BUCKET_NAME")
    logger.info(f"Loaded bucket name: {bucket_name}")

    logger.info("Connecting to S3")
    player_save_folder = f"s3://{bucket_name}/data/nba/PLAYER"
    player_error_log_path = f"{player_error_log_path}/{str(date.today())}.yaml"
    s3 = boto3.client("s3")

    logger.info("Loading data to pull yaml file")
    data_to_pull = load_yaml_s3(
        data_to_pull_path, bucket_name=bucket_name, s3_client=s3
    )

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

    player_error_content = yaml.dump(error_log, default_flow_style=False)
    s3.put_object(
        Bucket=bucket_name,
        Key=player_error_log_path,
        Body=player_error_content,
    )


@app.command()
def get_season_data(
    data_to_pull_path: Annotated[
        str,
        typer.Argument(help="Path to data to pull yaml file"),
    ] = "data/meta/data_to_pull.yaml",
    season_error_log_path: Annotated[
        Path,
        typer.Argument(help="Path to save error log", file_okay=False, dir_okay=True),
    ] = "data/logs/SEASON",
):
    bucket_name = os.getenv("BUCKET_NAME")
    logger.info(f"Loaded bucket name: {bucket_name}")

    logger.info("Setting up client")
    s3 = boto3.client("s3")

    logger.info("Loading data to pull yaml file")
    data_to_pull = load_yaml_s3(data_to_pull_path, bucket_name, s3_client=s3)

    season_error_log_path = f"{season_error_log_path}/{str(date.today())}.yaml"

    season_save_folder = f"s3://{bucket_name}/data/nba/SEASON"

    season_ids = data_to_pull.get("season")

    season_config = {
        "regular_season_pergame": {
            "season_id_list": season_ids.get("per_game").get("regular_season"),
            "out_path": f"{season_save_folder}/PER_GAME/REGULAR_SEASON",
            "playoffs": False,
            "permode": "PERGAME",
        },
        "playoffs_pergame": {
            "season_id_list": season_ids.get("per_game").get("playoffs"),
            "out_path": f"{season_save_folder}/PER_GAME/PLAYOFFS",
            "playoffs": True,
            "permode": "PERGAME",
        },
        "regular_season_perpossession": {
            "season_id_list": season_ids.get("per_possession").get("regular_season"),
            "out_path": f"{season_save_folder}/PER_POSSESSION/REGULAR_SEASON",
            "playoffs": False,
            "permode": "PER100POSSESSIONS",
        },
        "playoffs_perpossession": {
            "season_id_list": season_ids.get("per_possession").get("playoffs"),
            "out_path": f"{season_save_folder}/PER_POSSESSION/PLAYOFFS",
            "playoffs": True,
            "permode": "PER100POSSESSIONS",
        },
    }

    def save_season_data(
        season_key: Literal[
            "regular_season_pergame",
            "playoffs_pergame",
            "regular_season_perpossession",
            "playoffs_perpossession",
        ],
        game_ids: Dict,
        season_config: Dict = season_config,
    ) -> Dict:
        error_log = {}
        config = season_config[season_key]
        for season_id in config.get("season_id_list"):
            if not game_ids.get(season_id[0:4]):
                logger.info(f"Skipping {season_id}")
                continue
            try:
                season_ingest = SeasonIngest(
                    season_year=season_id[0:4],  # Expects season year not season id
                    save_folder=config.get("out_path"),
                    playoffs=config.get("playoffs"),
                    permode=config.get("permode"),
                )
                season_ingest.save_all_nonsynergy()
                season_ingest.save_all_synergy()
            except Exception as e:
                logger.error(f"Error for {season_id} - {e}")
                error_log[season_key][season_id] = e
                continue

            sleep(1)

        return error_log

    error_log = {}
    game_ids = data_to_pull.get("game")

    logger.info("Getting regular_season_pergame")
    error_log["regular_season_pergame"] = save_season_data(
        "regular_season_pergame", game_ids=game_ids.get("regular_season")
    )

    logger.info("Getting playoffs_pergame")
    error_log["playoffs_pergame"] = save_season_data(
        "playoffs_pergame", game_ids=game_ids.get("playoffs")
    )

    logger.info("Getting regular_season_perpossession")
    error_log["regular_season_perpossession"] = save_season_data(
        "regular_season_perpossession", game_ids=game_ids.get("regular_season")
    )

    logger.info("Getting playoffs perpossession")
    error_log["playoffs_perpossession"] = save_season_data(
        "playoffs_perpossession", game_ids=game_ids.get("playoffs")
    )

    logger.info("Saving error log")
    season_error_content = yaml.dump(error_log, default_flow_style=False)
    s3.put_object(
        Bucket=bucket_name,
        Key=season_error_log_path,
        Body=season_error_content,
    )


@app.command()
def get_game_data(
    meta_path: Annotated[
        str,
        typer.Argument(
            help="Path to folder containing inventory and data file",
        ),
    ] = "data/meta",
    game_error_path: Annotated[
        str, typer.Argument(help="Path to save error log")
    ] = "data/logs/GAME/",
    season_year: Annotated[str, typer.Argument(help="Season to pull data for")] = None,
):
    bucket_name = os.getenv("BUCKET_NAME")
    logger.info(f"Loaded bucket name: {bucket_name}")

    if not season_year:
        # this is default and shouldn't need to be changed unless
        # getting historical data
        logger.info("Setting season year to current")
        season_year = str(SeasonYear.default)

    season_year = str(season_year)

    logger.info("Setting up paths")
    game_save_folder = f"s3://{bucket_name}/data/nba/GAME"
    game_error_path = f"{game_error_path}/{str(date.today())}.yaml"

    data_to_pull_path = f"{meta_path}/data_to_pull.yaml"
    inventory_path = f"{meta_path}/inventory.yaml"
    regular_season_path = f"{game_save_folder}/REGULAR_SEASON"
    playoffs_path = f"{game_save_folder}/PLAYOFFS"

    logger.info("Setting up s3 client")
    s3 = boto3.client("s3")

    logger.info("Loading data to pull yaml file")
    data_to_pull = load_yaml_s3(data_to_pull_path, bucket_name, s3_client=s3)

    game_ids_regular_season = data_to_pull.get("game").get("regular_season")
    game_ids_playoffs = data_to_pull.get("game").get("playoffs")

    inventory = load_yaml_s3(inventory_path, bucket_name, s3_client=s3)

    inventory_game_ids_regular_season = inventory.get("GAME").get("REGULAR_SEASON")
    inventory_game_ids_playoffs = inventory.get("GAME").get("PLAYOFFS")

    logger.info("Getting data that needs to be pulled")
    game_ids_regular_season_topull = [
        game_id
        for game_id in game_ids_regular_season[season_year]
        if game_id not in inventory_game_ids_regular_season
    ]
    game_ids_playoffs_topull = [
        game_id
        for game_id in game_ids_playoffs[season_year]
        if game_id not in inventory_game_ids_playoffs
    ]

    error_log = {}

    game_ids_regular_season = data_to_pull.get("game").get("regular_season")
    game_ids_playoffs = data_to_pull.get("game").get("playoffs")

    error_log = {}

    error_log["regular_season"] = {}
    for game_id in game_ids_regular_season_topull:
        logger.info(f"Game ID: {game_id}")
        try:
            game_ingest = GameIngest(
                game_id=game_id,
                save_folder=regular_season_path,
                verbose=True,
            )
            game_ingest.save_all()

        except Exception as e:
            logger.error(f"Error for {game_id} - {e}")
            error_log["regular_season"][game_id] = e
            continue
        sleep(1)

    error_log["playoffs"] = {}
    for game_id in game_ids_playoffs_topull:
        logger.info(f"Game ID: {game_id}")
        try:
            game_ingest = GameIngest(
                game_id=game_id,
                save_folder=playoffs_path,
                verbose=True,
            )
            game_ingest.save_all()
        except Exception as e:
            logger.info(f"Error for {game_id} - {e}")
            error_log["playoffs"][game_id] = e
            continue
        sleep(1)

    logger.info("Saving error log")
    game_error_content = yaml.dump(error_log, default_flow_style=False)
    s3.put_object(
        Bucket=bucket_name,
        Key=game_error_path,
        Body=game_error_content,
    )


if __name__ == "__main__":
    app()
