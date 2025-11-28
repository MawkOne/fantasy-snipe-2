# Scripts Index - Organized by Data Source

## 🏒 NHL API (Primary Source)

### Games & Schedule
- `ingestion/nhl_api/populate_games.py` - Populate games table from NHL API
- `ingestion/nhl_api/populate_teams.py` - Populate teams table
- `ingestion/nhl_api/populate_schedule_statsapi.py` - Schedule from Stats REST API
- `ingestion/nhl_api/populate_team_season_schedule.py` - Team-specific schedules

### Play-by-Play Events
- `ingestion/nhl_api/populate_play_by_play.py` - **Main PBP ingestion to PostgreSQL**
  - Usage: `python populate_play_by_play.py --all --season 20252026 --game-type 2`

### Players
- `ingestion/nhl_api/populate_players.py` - Core player roster
- `ingestion/nhl_api/populate_player_details_from_nhl.py` - Extended player details
- `ingestion/nhl_api/nhl_api_roster_comprehensive.py` - Comprehensive roster data

### Stats & Performance
- `ingestion/nhl_api/populate_player_game_stats.py` - Player game-level statistics
- `ingestion/nhl_api/populate_shift_charts.py` - Shift-by-shift data

### Full Database Population
- `ingestion/nhl_api/populate_fantasy_database.py` - **Master script for full NHL data ingestion**

---

## ☁️ BigQuery (Cloud Analytics)

### Data Ingestion
- `ingestion/bigquery/bq_ingest_games.py` - Games to BigQuery
- `ingestion/bigquery/bq_ingest_pbp.py` - Play-by-play events to BigQuery
- `ingestion/bigquery/bq_ingest_player_details*.py` - Player details (3 versions)
- `ingestion/bigquery/bq_ingest_player_stats.py` - Player statistics
- `ingestion/bigquery/bq_ingest_shifts.py` - Shift data
- `ingestion/bigquery/populate_bigquery.py` - Full BigQuery population
- `ingestion/bigquery/save_rosters_to_bigquery.py` - Roster exports

### Analytics
- `analysis/bq_compute_player_shift_metrics.py` - Shift metrics computation
- `analysis/bq_compute_player_game_advanced_metrics*.py` - Advanced metrics
- `analysis/bq_age_curves*.py` - Age curve analysis
- `analysis/bq_forwards_*.py` - Forward-specific analysis
- `analysis/bq_pts60_*.py` - Points per 60 analysis
- `analysis/bq_elite_*.py` - Elite player analysis
- `analysis/bq_season_adjusted_analysis.py` - Season adjustments

---

## 📊 CBS Sports

### Integration
- `ingestion/cbs_sports/cbs_credentials.py` - Credentials management
- `ingestion/cbs_sports/cbs_session_bridge.py` - Session handling
- `ingestion/cbs_sports/cbs_sports_api_client.py` - API client
- `ingestion/cbs_sports/cbs_sports_authenticated.py` - Authentication
- `ingestion/cbs_sports/cbs_sports_integration.py` - Main integration
- `ingestion/cbs_sports/cbs_sports_manual_login.py` - Manual login helper
- `ingestion/cbs_sports/setup_cbs_integration.py` - Setup script

### Data Collection
- `ingestion/cbs_sports/scrape_cbs_team_rosters.py` - Team rosters
- `ingestion/cbs_sports/scrape_cbs_teams.py` - Team data
- `ingestion/cbs_sports/scrape_cbs_transactions.py` - Transactions
- `ingestion/cbs_sports/map_cbs_players.py` - Player ID mapping

---

## 🟣 Yahoo Fantasy

- `ingestion/yahoo/yahoo_api_test.py` - Yahoo API integration test
- `ingestion/other_sources/import_yahoo_player_map.py` - Player ID mapping

---

## 📰 ESPN

- `ingestion/espn/espn_roster_scraper.py` - ESPN roster scraping (v1)
- `ingestion/espn/espn_roster_scraper_v2.py` - ESPN roster scraping (v2)

---

## 🎓 EliteProspects

- `ingestion/eliteprospects/ep_ingest_player.py` - Player data from EliteProspects

---

## 💰 PuckPedia (Contract Data)

- `ingestion/puckpedia/puckpedia_ingest_player.py` - Contract and salary data

---

## 🔄 Workers & Background Jobs

- `ingestion/workers/provider_sync_worker.py` - Background provider sync
- `ingestion/workers/rss_ingestion_worker.py` - RSS feed ingestion
- `ingestion/workers/playht_worker.py` - Audio generation worker

---

## 🛠️ Other Data Sources

- `ingestion/other_sources/import_projections_rosters.py` - Projection imports
- `ingestion/other_sources/import_rosters_salaries.py` - Roster/salary imports
- `ingestion/other_sources/ingest_projections.py` - External projections
- `ingestion/other_sources/ingest_reference_csvs.py` - CSV imports
- `ingestion/other_sources/ingest_roster_data.py` - Roster data
- `ingestion/other_sources/backfill_pg_adv_flat.py` - Advanced metrics backfill
- `ingestion/other_sources/persist_all_player_game_metrics.py` - Metrics persistence
- `ingestion/other_sources/cache_rankings_to_fantasy.py` - Rankings cache

---

## 📝 Quick Reference

### Ingest 2025 Season (PostgreSQL)
```bash
# Step 1: Games
python ingestion/nhl_api/populate_games.py 2025

# Step 2: Play-by-Play
python ingestion/nhl_api/populate_play_by_play.py --all --season 20252026 --game-type 2

# Step 3: Player Stats
python ingestion/nhl_api/populate_player_game_stats.py --season 20252026
```

### Ingest to BigQuery
```bash
python ingestion/bigquery/bq_ingest_games.py --season 20252026 --game-type 2
python ingestion/bigquery/bq_ingest_pbp.py --season 20252026 --game-type 2
```

### Full Database Setup
```bash
python ingestion/init_db_tables.py
python ingestion/populate_fantasy_database.py
```

