# NBA Data Pull

This repo has code to automatically pull nba data using `nbastatpy`. This will be containerized and run daily on AWS to update a database.

## WORKFLOW WIP

1. Build the initial historical database
   1. Some of this may already exist and can be copied
2. Save files every day (.csv)
3. Every day during the NBA season, the database will be updated
   1. Airflow for scheduling
   2. Duckdb for database
4. Open port to allow connection to database
   1. Will need authentication

## Current Data

- Regular season data for per-game level stats is good to go
- Playoff Game data is good to go
- NO per possession
  - Per Possession not available for tracking / play type data
- NO playoff level season stats

**Just need to get playoff season stats & per possession for stats where available (no tracking or playtype)**


>[!WARNING]
> Need to recreate the historical database, will be good to have here anyway. Will have a 'break in case of emergency' rebuild database script
> MUST INCLUDE TESTING

## Process for Building Get Data Process

1. Build Data Inventory (First build, then add to it) --keeps track of all data currently ingested
2. Check for any new data not in data inventory. SEE: `setup_historical.py`
   1. Saves a config to be replaced each time with new missing files, etc.
3. Data pull for anything in config

- Will want an inventory file to track what has already been pulled
  - Holds IDs:
    - Game ID: Only pull new games
      - Get new games found in setup_historical
    - Player ID: Only pull player data once a year for players not in list
    - Season: Only update current season (replace), if new season pull all data
      - Keep initial pull for posterity...?

- Player Data 
  - Updated once a year for current season
  - No possession / playoff difference
  - Tables
   - Combine data pulled for one year (one pull)
   - Common info pulled for each NEW player (check for previous pulls)
- Season Data
  - Updated once a day for current season

