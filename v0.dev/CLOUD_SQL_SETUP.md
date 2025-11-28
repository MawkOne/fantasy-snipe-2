# Google Cloud SQL Integration Guide

## Overview
Your Google Cloud SQL instance contains historical fantasy hockey data. This guide explains how to integrate it with the Next.js frontend.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Next.js App    │────▶│  FastAPI Backend │────▶│ Google Cloud SQL    │
│  (Frontend)     │     │  (Railway)       │     │ (fantasy-snipe-ai)  │
└─────────────────┘     └──────────────────┘     └─────────────────────┘
```

**Recommended Approach:** Access Cloud SQL through your FastAPI backend for security and performance.

## Google Cloud SQL Instance

**Project:** `fantasy-snipe-ai`  
**Console:** https://console.cloud.google.com/sql/instances?project=fantasy-snipe-ai

### Your Connection Details ✅

**Instance Connection Name:** `fantasy-snipe-ai:northamerica-northeast1:nhl-api-db-montreal`  
**Region:** `northamerica-northeast1` (Montreal)  
**Private IP:** `10.112.0.3` (VPC only)  
**Public IP:** `34.47.23.137` (Internet accessible)  
**Port:** `5432` (PostgreSQL)  
**Database:** `nhl_api` (update if different)

## Option 1: Access via FastAPI Backend (Recommended)

### Step 1: Update FastAPI Backend

Add Cloud SQL connection to your FastAPI app on Railway:

```python
# main.py or database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Cloud SQL connection
CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME")
CLOUD_SQL_USER = os.getenv("CLOUD_SQL_USER")
CLOUD_SQL_PASSWORD = os.getenv("CLOUD_SQL_PASSWORD")
CLOUD_SQL_DATABASE = os.getenv("CLOUD_SQL_DATABASE")

# For Cloud SQL Proxy or public IP
DATABASE_URL = f"postgresql://{CLOUD_SQL_USER}:{CLOUD_SQL_PASSWORD}@127.0.0.1:5432/{CLOUD_SQL_DATABASE}"

# Or use unix socket (when deployed in GCP)
# DATABASE_URL = f"postgresql://{CLOUD_SQL_USER}:{CLOUD_SQL_PASSWORD}@/{CLOUD_SQL_DATABASE}?host=/cloudsql/{CLOUD_SQL_CONNECTION_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# API Endpoints
@app.get("/api/leagues")
async def get_leagues():
    """Get all leagues from Cloud SQL"""
    db = SessionLocal()
    try:
        # Query your leagues table
        result = db.execute("SELECT * FROM leagues")
        return result.fetchall()
    finally:
        db.close()

@app.get("/api/leagues/{league_id}/history/{season}")
async def get_league_history(league_id: str, season: str):
    """Get historical data for a specific league and season"""
    db = SessionLocal()
    try:
        # Query historical data
        result = db.execute(
            "SELECT * FROM league_history WHERE league_id = :league_id AND season = :season",
            {"league_id": league_id, "season": season}
        )
        return result.fetchall()
    finally:
        db.close()

@app.get("/api/teams/{team_id}/roster")
async def get_team_roster(team_id: str):
    """Get current roster for a team"""
    db = SessionLocal()
    try:
        result = db.execute(
            "SELECT * FROM team_rosters WHERE team_id = :team_id",
            {"team_id": team_id}
        )
        return result.fetchall()
    finally:
        db.close()

@app.get("/api/players/{player_id}/stats/{season}")
async def get_player_stats(player_id: str, season: str):
    """Get player stats for a season"""
    db = SessionLocal()
    try:
        result = db.execute(
            "SELECT * FROM player_stats WHERE player_id = :player_id AND season = :season",
            {"player_id": player_id, "season": season}
        )
        return result.fetchall()
    finally:
        db.close()
```

### Step 2: Set Environment Variables on Railway

In your Railway FastAPI project, add these environment variables:

```bash
CLOUD_SQL_CONNECTION_NAME=fantasy-snipe-ai:us-central1:your-instance-name
CLOUD_SQL_USER=your_username
CLOUD_SQL_PASSWORD=your_password
CLOUD_SQL_DATABASE=fantasy_hockey
```

### Step 3: Use Hooks in Next.js

```typescript
import { useLeagueHistory } from '@/hooks/use-cloud-sql-data';

function LeagueHistoryView() {
  const { history, loading, error } = useLeagueHistory('uhhp-league', '2024-2025');
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return (
    <div>
      {/* Display historical data */}
      {history.map(item => (
        <div key={item.id}>{item.name}</div>
      ))}
    </div>
  );
}
```

## Option 2: Cloud SQL Proxy (For Local Development)

### Install Cloud SQL Proxy

```bash
# macOS
brew install cloud-sql-proxy

# Or download from GitHub
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.11.4/cloud-sql-proxy.darwin.amd64
chmod +x cloud-sql-proxy
```

### Authenticate

```bash
gcloud auth application-default login
```

### Start Proxy

```bash
cloud-sql-proxy fantasy-snipe-ai:us-central1:your-instance-name
```

This will expose Cloud SQL on `localhost:5432`.

### Connect from FastAPI Locally

```bash
DATABASE_URL="postgresql://username:password@127.0.0.1:5432/fantasy_hockey"
```

## Database Schema (What's in Cloud SQL?)

Based on your `/uhhp_simulations/` JSON data, the Cloud SQL database likely contains:

```sql
-- Leagues
leagues (
  id, name, season, created_at, settings
)

-- Teams
teams (
  id, league_id, team_name, gm_name, strategy
)

-- Players
players (
  id, name, position, nhl_team, rookie_status
)

-- Rosters
team_rosters (
  id, team_id, player_id, season, contract_value, contract_years
)

-- Transactions
transactions (
  id, league_id, season, team_id, action_type, player_id, timestamp
)

-- Weekly Results
weekly_results (
  id, league_id, season, week, team_id, wins, losses, points, rank
)

-- Player Stats
player_stats (
  id, player_id, season, games, goals, assists, points
)
```

## Hybrid Approach: Firebase + Cloud SQL

**Firebase:** Real-time chat, user authentication, active sessions  
**Cloud SQL:** Historical data, analytics, complex queries

```typescript
import { useLeagues } from '@/hooks/use-leagues'; // Firebase
import { useLeagueHistory } from '@/hooks/use-cloud-sql-data'; // Cloud SQL

function LeagueView() {
  const { activeLeague } = useLeagues('user123'); // Current league state
  const { history } = useLeagueHistory(activeLeague?.id, '2024-2025'); // Historical data
  
  return (
    <div>
      <h1>{activeLeague?.name}</h1>
      <div>Current Season: {activeLeague?.settings.season}</div>
      <div>Historical Data: {history?.length} records</div>
    </div>
  );
}
```

## Data Migration: JSON → Cloud SQL

If you need to import your JSON data into Cloud SQL:

```python
import json
import psycopg2

# Connect to Cloud SQL
conn = psycopg2.connect(
    host="127.0.0.1",
    port=5432,
    database="fantasy_hockey",
    user="your_user",
    password="your_password"
)

# Load JSON
with open('/path/to/uhhp_league_history_full.json', 'r') as f:
    data = json.load(f)

# Insert into database
cursor = conn.cursor()

for season_name, season_data in data['seasons'].items():
    for stage_name, stage_data in season_data['stages'].items():
        for team_name, team_data in stage_data['teams'].items():
            for action in team_data['actions']:
                cursor.execute("""
                    INSERT INTO transactions 
                    (league_id, season, stage, team_name, action_type, player_name, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    'uhhp',
                    season_name,
                    stage_name,
                    team_name,
                    action['type'],
                    action.get('player'),
                    action.get('timestamp')
                ))

conn.commit()
cursor.close()
conn.close()
```

## Security Best Practices

1. ✅ **Never expose Cloud SQL credentials in frontend code**
2. ✅ **Always access through FastAPI backend**
3. ✅ **Use environment variables for sensitive data**
4. ✅ **Enable Cloud SQL SSL connections**
5. ✅ **Restrict Cloud SQL to authorized networks**
6. ✅ **Use IAM authentication when possible**

## Next Steps

1. Get your Cloud SQL instance connection details
2. Update FastAPI backend with Cloud SQL endpoints
3. Test API endpoints locally
4. Deploy FastAPI to Railway with environment variables
5. Use hooks in Next.js to fetch data

Let me know which tables/data you have in Cloud SQL and I'll create the specific API endpoints!

