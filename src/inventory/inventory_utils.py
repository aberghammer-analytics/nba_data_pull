from datetime import datetime
from time import sleep

import boto3
import yaml
from nbastatpy.season import Season
from tqdm import tqdm
from typing_extensions import Dict, List, Tuple


def load_yaml_s3(file_path: str, bucket_name: str, s3_client: boto3.client) -> dict:
    response = s3_client.get_object(Bucket=bucket_name, Key=str(file_path))
    yaml_content = response["Body"].read().decode("utf-8")
    return yaml.safe_load(yaml_content)


class InventoryMeta:
    empty_inventory = {
        "GAME": {
            "PLAYOFFS": [],
            "REGULAR_SEASON": [],
        },
        "PLAYER": [],
        "SEASON": {
            "PER_GAME": {
                "PLAYOFFS": [],
                "REGULAR_SEASON": [],
            },
            "PER_POSSESSION": {"PLAYOFFS": [], "REGULAR_SEASON": []},
        },
    }

    data_folders = {
        "GAME": {
            "PLAYOFFS": "data/nba/GAME/PLAYOFFS/",
            "REGULAR": "data/nba/GAME/REGULAR/",
        },
        "PLAYER": "data/nba/PLAYER/",
        "SEASON": {
            "PER_GAME": {
                "PLAYOFFS": "data/nba/SEASON/PER_GAME/PLAYOFFS/",
                "REGULAR_SEASON": "data/nba/SEASON/PER_GAME/REGULAR_SEASON/",
            },
            "PER_POSSESSION": {
                "PLAYOFFS": "data/nba/SEASON/PER_POSSESSION/PLAYOFFS/",
                "REGULAR_SEASON": "data/nba/SEASON/PER_POSSESSION/REGULAR_SEASON/",
            },
        },
    }


def list_all_common_prefixes(bucket: str, prefix: str, s3_client=None) -> list:
    """
    Uses a paginator to list all common prefixes (subdirectories) under the given S3 prefix.

    :param bucket: Name of the S3 bucket.
    :param prefix: The prefix for the folder path (must end with a slash, e.g., "GAME/").
    :param s3_client: Optional boto3 S3 client.
    :return: A list of common prefixes.
    """
    if s3_client is None:
        s3_client = boto3.client("s3")

    paginator = s3_client.get_paginator("list_objects_v2")
    prefixes = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter="/"):
        if "CommonPrefixes" in page:
            for cp in page["CommonPrefixes"]:
                prefixes.append(cp["Prefix"])
    return prefixes


def update_s3_inventory(
    inventory: dict, bucket: str, prefix: str = "data/nba/", s3_client=None
) -> dict:
    """
    Recursively updates a nested inventory dictionary (mirroring your S3 folder hierarchy)
    by replacing each leaf (empty list) with a list of folder names from S3 at that prefix.
    """
    if s3_client is None:
        s3_client = boto3.client("s3")

    for key, value in inventory.items():
        current_prefix = f"{prefix}{key}/"  # Construct S3 path

        if isinstance(value, list):
            # Retrieve all common prefixes (i.e., subdirectories) using paginator
            common_prefixes = list_all_common_prefixes(
                bucket, current_prefix, s3_client
            )
            if common_prefixes:
                # Extract the subdirectory names from the S3 prefixes
                folders = [cp.rstrip("/").split("/")[-1] for cp in common_prefixes]
                inventory[key] = folders
            else:
                inventory[key] = []
        elif isinstance(value, dict):
            # Recursively update nested dictionaries
            update_s3_inventory(value, bucket, current_prefix, s3_client)

    return inventory


class SeasonYear:
    current_datetime = datetime.now()
    current_season_year = current_datetime.year
    if current_datetime.month <= 9:
        current_season_year -= 1

    default = current_season_year


def process_seasons(seasons: List, playoffs: bool) -> Tuple[Dict[str, List], List[str]]:
    """
    Processes a list of seasons and returns game IDs per season and a consolidated list of player IDs.

    :param seasons: List of season identifiers.
    :param playoffs: Boolean indicating if the seasons are playoffs.
    :param permode: The performance mode parameter for Season.
    :return: A tuple containing:
             - A dictionary mapping season (as string) to a list of game IDs.
             - A list of player IDs (as strings) from all seasons.
    """
    game_ids: Dict[str, List] = {}
    player_ids: List[str] = []
    progress_bar = tqdm(total=len(seasons), desc="Progress", unit="task")

    for season in seasons:
        progress_bar.set_description(f"Getting {season}")
        season_ingest = Season(season, playoffs=playoffs, permode="PerGame")
        df = season_ingest.get_player_games()
        game_ids[str(season)] = df["GAME_ID"].unique().tolist()
        player_ids.extend(df["PLAYER_ID"].astype(str).unique().tolist())
        progress_bar.update(1)
        sleep(1)

    progress_bar.close()
    return game_ids, player_ids


def get_season_list(earliest_season_year: int, inventory: dict, playoffs: bool = False):
    # Determine current season
    season_grain = "REGULAR_SEASON"

    season_year = SeasonYear.default
    seasons = list(range(earliest_season_year, season_year + 1))
    if playoffs:
        season_grain = "PLAYOFFS"

    seasons = [f"{str(season)}{str(season + 1)[-2:]}" for season in seasons]
    seasons = [
        season[0:4]
        for season in seasons
        if season not in inventory["SEASON"]["PER_GAME"][season_grain]
    ]
    if not seasons:
        seasons = [f"{str(season_year)}"]

    return seasons
