import os
from datetime import date
from pathlib import Path

import boto3
import typer
import yaml
from dotenv import load_dotenv
from loguru import logger
from typing_extensions import Annotated

from nba_data_pull.inventory.inventory_utils import (
    InventoryMeta,
    SeasonYear,
    get_season_list,
    load_yaml_s3,
    process_seasons,
    update_s3_inventory,
)

load_dotenv()

app = typer.Typer()


@app.command()
def copy_previous_meta(
    root_folder: Annotated[
        Path,
        typer.Argument(
            help="Root folder with metadata", file_okay=False, dir_okay=True
        ),
    ] = Path("data/meta/"),
    out_folder: Annotated[
        Path,
        typer.Argument(
            help="Output folder to save archive", file_okay=False, dir_okay=True
        ),
    ] = Path("data/logs/inventory_logs/"),
):
    if isinstance(root_folder, str):
        root_folder = Path(root_folder)
    if isinstance(out_folder, str):
        out_folder = Path(out_folder)

    bucket_name = os.getenv("BUCKET_NAME")
    logger.info(f"Loaded bucket name: {bucket_name}")

    logger.info("Connecting to S3")
    s3 = boto3.client("s3")

    # Create output folder for today
    out_folder = out_folder.joinpath(str(date.today()))

    logger.info("Reading data")
    inventory = load_yaml_s3(
        root_folder.joinpath("inventory.yaml"), bucket_name=bucket_name, s3_client=s3
    )
    data_to_pull = load_yaml_s3(
        root_folder.joinpath("data_to_pull.yaml"), bucket_name=bucket_name, s3_client=s3
    )

    logger.info("Saving data to S3")
    # Convert Python dictionary to YAML format
    inventory_yaml_content = yaml.dump(inventory, default_flow_style=False)
    data_to_pull_yaml_content = yaml.dump(data_to_pull, default_flow_style=False)

    # Upload to S3
    s3.put_object(
        Bucket=bucket_name,
        Key=str(out_folder.joinpath("inventory.yaml")),
        Body=inventory_yaml_content,
    )
    s3.put_object(
        Bucket=bucket_name,
        Key=str(out_folder.joinpath("data_to_pull.yaml")),
        Body=data_to_pull_yaml_content,
    )


@app.command()
def create_inventory(
    output_path: Annotated[
        Path,
        typer.Argument(
            help="Path to save data inventory", file_okay=True, dir_okay=False
        ),
    ] = Path("data/meta/inventory.yaml"),
):
    bucket_name = os.getenv("BUCKET_NAME")
    logger.info(f"Loaded bucket name: {bucket_name}")

    inventory_meta = InventoryMeta().empty_inventory

    logger.info("Setting up Client")
    s3 = boto3.client("s3")

    logger.info("Getting inventory")
    updated_inventory = update_s3_inventory(
        inventory=inventory_meta,
        bucket=bucket_name,
        prefix="data/nba/",
        s3_client=s3,
    )

    inventory_yaml_content = yaml.dump(updated_inventory, default_flow_style=False)

    logger.info("Saving inventory to S3")
    s3.put_object(
        Bucket=bucket_name,
        Key=str(output_path),
        Body=inventory_yaml_content,
    )


@app.command()
def get_data_to_pull(
    inventory_path: Annotated[
        Path,
        typer.Argument(help="Path to inventory file", file_okay=True, dir_okay=False),
    ] = Path("data/meta/inventory.yaml"),
    output_path: Annotated[
        Path,
        typer.Argument(
            help="Path to save data inventory", file_okay=True, dir_okay=False
        ),
    ] = Path("data/meta/data_to_pull.yaml"),
    earliest_season_year: Annotated[
        int, typer.Argument(help="Earliest season year")
    ] = 1990,
):
    bucket_name = os.getenv("BUCKET_NAME")
    logger.info(f"Loaded bucket name: {bucket_name}")

    logger.info("Connecting to S3")
    s3 = boto3.client("s3")

    logger.info("Reading data")
    inventory = load_yaml_s3(str(inventory_path), bucket_name=bucket_name, s3_client=s3)

    expected_season_list = [
        f"{str(season)}{str(season + 1)[-2:]}"
        for season in range(earliest_season_year, SeasonYear.default + 1)
    ]

    seasons_regular_season = get_season_list(earliest_season_year, inventory)
    seasons_playoffs = get_season_list(earliest_season_year, inventory, playoffs=True)

    logger.info("Going through regular season")
    game_ids_regular, player_ids_regular = process_seasons(
        seasons=seasons_regular_season,
        playoffs=False,
    )

    logger.info("Going through playoffs")
    game_ids_playoffs, player_ids_playoffs = process_seasons(
        seasons=seasons_playoffs, playoffs=True
    )

    data_to_pull = {
        "game": {
            "regular_season": game_ids_regular,
            "playoffs": game_ids_playoffs,
        },
        "player": [
            str(player_id)
            for player_id in player_ids_regular
            if str(player_id) not in inventory["PLAYER"]
        ],
        "season": {
            "per_game": {
                "regular_season": [
                    season
                    for season in expected_season_list
                    if season not in inventory["SEASON"]["PER_GAME"]["REGULAR_SEASON"]
                ],
                "playoffs": [
                    season
                    for season in expected_season_list
                    if season not in inventory["SEASON"]["PER_GAME"]["PLAYOFFS"]
                ],
            },
            "per_possession": {
                "regular_season": [
                    season
                    for season in expected_season_list
                    if season
                    not in inventory["SEASON"]["PER_POSSESSION"]["REGULAR_SEASON"]
                ],
                "playoffs": [
                    season
                    for season in expected_season_list
                    if season not in inventory["SEASON"]["PER_POSSESSION"]["PLAYOFFS"]
                ],
            },
        },
    }

    if not data_to_pull["season"]["per_game"]["regular_season"]:
        data_to_pull["season"]["per_game"]["regular_season"] = [
            f"{str(SeasonYear.default)}{str(SeasonYear.default + 1)[-2:]}"
        ]

    if not data_to_pull["season"]["per_game"]["playoffs"]:
        data_to_pull["season"]["per_game"]["playoffs"] = [
            f"{str(SeasonYear.default)}{str(SeasonYear.default + 1)[-2:]}"
        ]

    if not data_to_pull["season"]["per_possession"]["regular_season"]:
        data_to_pull["season"]["per_possession"]["regular_season"] = [
            f"{str(SeasonYear.default)}{str(SeasonYear.default + 1)[-2:]}"
        ]

    if not data_to_pull["season"]["per_possession"]["playoffs"]:
        data_to_pull["season"]["per_possession"]["playoffs"] = [
            f"{str(SeasonYear.default)}{str(SeasonYear.default + 1)[-2:]}"
        ]

    logger.info("Saving Data")
    data_to_pull_yaml_content = yaml.dump(data_to_pull, default_flow_style=False)

    logger.info("Saving inventory to S3")
    s3.put_object(
        Bucket=bucket_name,
        Key=str(output_path),
        Body=data_to_pull_yaml_content,
    )


if __name__ == "__main__":
    app()
