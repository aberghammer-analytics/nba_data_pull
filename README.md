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
- NO playoff level season stats

>[!WARNING]
> Need to recreate the historical database, will be good to have here anyway. Will have a 'break in case of emergency' rebuild database script
> MUST INCLUDE TESTING
