from datetime import date
from pathlib import Path

import typer
import yaml
from inventory_utils import (
    SeasonYear,
    build_directory_tree,
    get_season_list,
    process_seasons,
)
from loguru import logger
from typing_extensions import Annotated

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
    logger.info("Reading data")
    with open(root_folder.joinpath("inventory.yaml"), "r") as file:
        inventory = yaml.safe_load(file)

    with open(root_folder.joinpath("data_to_pull.yaml"), "r") as file:
        data_to_pull = yaml.safe_load(file)

    logger.info("Saving data to archive")
    out_folder.joinpath(str(date.today())).mkdir(parents=True, exist_ok=True)
    with open(
        out_folder.joinpath(str(date.today())).joinpath("inventory.yaml"), "w"
    ) as file:
        yaml.safe_dump(inventory, file)

    with open(
        out_folder.joinpath(str(date.today())).joinpath("data_to_pull.yaml"), "w"
    ) as file:
        yaml.safe_dump(data_to_pull, file)


@app.command()
def create_inventory(
    root_folder: Annotated[
        Path,
        typer.Argument(help="Root folder with data", file_okay=False, dir_okay=True),
    ] = Path("data/nba/"),
    output_path: Annotated[
        Path,
        typer.Argument(
            help="Path to save data inventory", file_okay=True, dir_okay=False
        ),
    ] = Path("data/meta/inventory.yaml"),
):
    directory_tree = build_directory_tree(root_folder)

    logger.info("Saving file tree to output path")
    with open(output_path, "w") as file:
        yaml.safe_dump(directory_tree, file)


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
    with open(inventory_path, "r") as file:
        inventory = yaml.safe_load(file)

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

    logger.info("Saving Data")
    with open(output_path, "w") as json_file:
        yaml.safe_dump(data_to_pull, json_file, indent=4)


if __name__ == "__main__":
    app()
