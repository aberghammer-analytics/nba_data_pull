# NBA Data Pull

This repo has code to automatically pull nba data using `nbastatpy`. This will be containerized and run daily on AWS to update a database.

## Overview & Setup

To get started, you can run `uv sync` if you have uv installed to install the required dependencies and set up the virtual environment. If not, you can run `pip install .` to install dependincies from `pyproject.toml`.

This automated repo uses AWS S3 to store the data. You will need to set a bucket along with the correct security requirements, you will then want to add your AWS credentials to the `sample.env` file to ensure everything loads properly and works consistently.

This repo uses [typer](https://typer.tiangolo.com/) as the CLI tool to run each command manually, but airflow is used for automation and scheduling. Typer allows you to run commands using syntax such as `python src/get_data.py <command> <args>` to run the function. You can also use the `--help` flag to get more information on the function prior to running it.

## Workflow

### File Structure
To pull data using this repository, you should have the following path structure for storing data:

```plaintext
data/
├── logs/
│   ├── GAME/
│   ├── inventory_logs/
│   ├── PLAYER/
│   ├── SEASON/
├── meta/
│   ├── data_to_pull.yaml
│   ├── inventory.yaml
├── nba/
│   ├── SEASON/
│   │   ├── PER_GAME/
│   │   │   ├── PLAYOFFS/
│   │   │   │   ├── season_id/
│   │   │   ├── REGULAR_SEASON/
│   │   │       ├── season_id/
│   │   ├── PER_POSSESSION/
│   │   │   ├── PLAYOFFS/
│   │   │   │   ├── season_id/
│   │   │   ├── REGULAR_SEASON/
│   │   │       ├── season_id/
│   ├── GAME/
│   │   ├── PLAYOFFS/
│   │   │   ├── game_id/
│   │   ├── REGULAR_SEASON/
│   │       ├── game_id/
│   ├── PLAYER/
│       ├── player_id/
```

>[!NOTE]
> The ID folders (game_id, season_id, player_id) are folders containing data files for the respective data

### Automated Process

This repo uses the following workflow to track and ingest data from the nba api.

1. **Copy Data Inventory Files:** Run `python src/inventory/create_inventory.py copy-previous-meta` to copy the current inventory and data-to-pull files into a backup log folder.
2. **Get the Current Data Inventory:** Run `python src/inventory/create_inventory.py create-inventory` to build an inventory of the data currently stored in the file structure
3. **Get the Data that Needs to be Pulled:** Run `python src/inventory/create_inventory.py get-data-to-pull` to query the NBA API for any data that is currently missing.
4. **Get the Data Files:** You then run the 3 commands to get the season, game, and player data left in the `data_to_pull.yaml` file created in step 3. The commands are found in `src/get_data.py` and are `get-season-data`, `get-game-data`, and `get-player-data`




