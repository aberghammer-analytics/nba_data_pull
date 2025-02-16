from datetime import datetime
from pathlib import Path
from time import sleep

from nbastatpy.season import Season
from tqdm import tqdm
from typing_extensions import Dict, List, Tuple


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
        seasons = [f"{str(seasons)}{str(seasons + 1)[-2:]}"]

    return seasons


def build_directory_tree(root: Path):
    # Get all immediate subdirectories
    subdirs = [p for p in root.iterdir() if p.is_dir()]

    # If there are no subdirectories, return an empty list (empty directory)
    if not subdirs:
        return []

    # Build the structure for each subdirectory
    tree = {sub.name: build_directory_tree(sub) for sub in subdirs}

    # If every subdirectory is a leaf (i.e. its value is an empty list),
    # then return a list of the subdirectory names.
    if all(value == [] for value in tree.values()):
        return list(tree.keys())
    else:
        return tree
