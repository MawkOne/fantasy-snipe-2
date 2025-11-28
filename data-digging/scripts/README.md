# Scripts Directory Organization

This directory contains all data processing scripts organized by function.

📖 **See [INDEX_BY_SOURCE.md](./INDEX_BY_SOURCE.md) for a complete listing organized by data source (NHL API, BigQuery, CBS Sports, Yahoo, ESPN, etc.)**

## Directory Structure

### 📥 `ingestion/` (~50 scripts)
Core ETL scripts for importing NHL data into the database.

**Organized by data source:**
- `nhl_api/` - NHL API ingestion (games, play-by-play, players, stats, shifts)
- `bigquery/` - BigQuery exports and analytics
- `cbs_sports/` - CBS Sports API integration
- `yahoo/` - Yahoo Fantasy integration  
- `espn/` - ESPN scraping
- `eliteprospects/` - EliteProspects data
- `puckpedia/` - Contract/salary data
- `workers/` - Background jobs (RSS, sync workers)
- `other_sources/` - Misc imports and utilities

**Root orchestrators:**
- `populate_fantasy_database.py` - Full PostgreSQL ingestion
- `populate_bigquery.py` - Full BigQuery ingestion
- `init_db_tables.py` - Initialize database schema

See [INDEX_BY_SOURCE.md](./INDEX_BY_SOURCE.md) for complete details.

### 📊 `analysis/` (95 scripts)
Data analysis, modeling, and reporting scripts:
- **Player Analysis:** Age curves, elite player impact, on/off-ice metrics
- **Team Analysis:** Roster construction, forecasting, team dynamics
- **Foster Model:** Player tier segmentation and strength analysis
- **Goal Analysis:** Draisaitl xG, shot coordinates, offensive zone analysis
- **Metrics:** Advanced player metrics, shift metrics, clustering

### 🔧 `fixes/` (40 scripts)
Data quality, schema updates, and corrections:
- **Data Quality:** Duplicate fixes, data validation
- **Schema Updates:** Add columns, migrate tables
- **Corrections:** Position fixes, team mapping, calculation fixes

### 🧪 `testing/` (24 scripts)
Testing, validation, and QA scripts:
- **API Tests:** NHL API, CBS Sports, Yahoo integration tests
- **Data Checks:** Player details, contract validation, position distribution
- **Debug:** Debugging utilities for data issues

### 🗑️ `deprecated/` (2 scripts)
Obsolete scripts kept for reference

## Usage Examples

### Ingest 2025 Season Data
```bash
# 1. Populate games table
python3 ingestion/populate_games.py 2025

# 2. Populate play-by-play events
python3 ingestion/populate_play_by_play.py --all --season 20252026 --game-type 2

# 3. Populate player stats
python3 ingestion/populate_player_game_stats.py --season 20252026
```

### Run Analysis
```bash
# Analyze player impact
python3 analysis/analyze_player_impact_simple.py

# Generate forecasts
python3 analysis/forecast_season_2122_compare.py
```

### Fix Data Issues
```bash
# Fix duplicates
python3 fixes/fix_duplicate_players.py

# Update team assignments
python3 fixes/update_roster_team_assignments.py
```

## Notes
- Most ingestion scripts have both PostgreSQL (`populate_*`) and BigQuery (`bq_ingest_*`) versions
- Analysis scripts often output to markdown or generate reports
- Fix scripts should be run with caution as they modify existing data

