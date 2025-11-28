# FastAPI + Google Cloud SQL Setup

## Your Cloud SQL Instance Details

**Connection Name:** `fantasy-snipe-ai:northamerica-northeast1:nhl-api-db-montreal`  
**Region:** `northamerica-northeast1` (Montreal)  
**Private IP:** `10.112.0.3`  
**Public IP:** `34.47.23.137`  
**Port:** `5432` (PostgreSQL)

## Option 1: Connect from Railway using Public IP (Recommended)

Since your FastAPI is hosted on Railway (external to GCP), use the **public IP** connection.

### Step 1: Update FastAPI Backend

```python
# database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Cloud SQL connection using public IP
CLOUD_SQL_HOST = os.getenv("CLOUD_SQL_HOST", "34.47.23.137")
CLOUD_SQL_PORT = os.getenv("CLOUD_SQL_PORT", "5432")
CLOUD_SQL_USER = os.getenv("CLOUD_SQL_USER", "postgres")
CLOUD_SQL_PASSWORD = os.getenv("CLOUD_SQL_PASSWORD")
CLOUD_SQL_DATABASE = os.getenv("CLOUD_SQL_DATABASE", "nhl_api")

# Connection string
DATABASE_URL = f"postgresql://{CLOUD_SQL_USER}:{CLOUD_SQL_PASSWORD}@{CLOUD_SQL_HOST}:{CLOUD_SQL_PORT}/{CLOUD_SQL_DATABASE}"

# SSL configuration (recommended for public IP connections)
# Add ?sslmode=require to the connection string for security
DATABASE_URL_SSL = f"{DATABASE_URL}?sslmode=require"

engine = create_engine(DATABASE_URL_SSL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Step 2: Add Environment Variables to Railway

Go to your Railway FastAPI project settings and add:

```bash
CLOUD_SQL_HOST=34.47.23.137
CLOUD_SQL_PORT=5432
CLOUD_SQL_USER=postgres
CLOUD_SQL_PASSWORD=your_password_here
CLOUD_SQL_DATABASE=nhl_api
```

### Step 3: Whitelist Railway IP in Cloud SQL

1. Go to https://console.cloud.google.com/sql/instances/nhl-api-db-montreal/connections/networking?project=fantasy-snipe-ai
2. Click **"Add Network"** under **Authorized Networks**
3. Add Railway's outgoing IP addresses:
   - You can find Railway's IPs or add `0.0.0.0/0` for testing (⚠️ not recommended for production)

### Step 4: Create API Endpoints

```python
# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import database
import models
import schemas

app = FastAPI(title="Fantasy Hockey API")

# Models (models.py)
class League(Base):
    __tablename__ = "leagues"
    
    id = Column(String, primary_key=True)
    name = Column(String)
    season = Column(String)
    created_at = Column(DateTime)
    settings = Column(JSON)

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(String, primary_key=True)
    league_id = Column(String, ForeignKey("leagues.id"))
    team_name = Column(String)
    gm_name = Column(String)
    strategy = Column(String)

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True)
    league_id = Column(String)
    season = Column(String)
    team_id = Column(String)
    action_type = Column(String)
    player_name = Column(String)
    timestamp = Column(DateTime)

class WeeklyResult(Base):
    __tablename__ = "weekly_results"
    
    id = Column(String, primary_key=True)
    league_id = Column(String)
    season = Column(String)
    week = Column(Integer)
    team_id = Column(String)
    wins = Column(Integer)
    losses = Column(Integer)
    ties = Column(Integer)
    points = Column(Float)
    rank = Column(Integer)

# API Endpoints

@app.get("/")
async def root():
    return {"message": "Fantasy Hockey API", "status": "running"}

@app.get("/api/leagues", response_model=List[schemas.League])
async def get_leagues(db: Session = Depends(get_db)):
    """Get all leagues"""
    leagues = db.query(models.League).all()
    return leagues

@app.get("/api/leagues/{league_id}")
async def get_league(league_id: str, db: Session = Depends(get_db)):
    """Get league details"""
    league = db.query(models.League).filter(models.League.id == league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    return league

@app.get("/api/leagues/{league_id}/teams")
async def get_league_teams(league_id: str, db: Session = Depends(get_db)):
    """Get all teams in a league"""
    teams = db.query(models.Team).filter(models.Team.league_id == league_id).all()
    return teams

@app.get("/api/teams/{team_id}/roster")
async def get_team_roster(team_id: str, db: Session = Depends(get_db)):
    """Get team roster"""
    roster = db.query(models.Roster).filter(models.Roster.team_id == team_id).all()
    return roster

@app.get("/api/leagues/{league_id}/transactions/{season}")
async def get_transactions(league_id: str, season: str, db: Session = Depends(get_db)):
    """Get all transactions for a league and season"""
    transactions = db.query(models.Transaction).filter(
        models.Transaction.league_id == league_id,
        models.Transaction.season == season
    ).order_by(models.Transaction.timestamp).all()
    return transactions

@app.get("/api/leagues/{league_id}/weekly/{season}")
async def get_weekly_results(
    league_id: str, 
    season: str, 
    week: int = None,
    db: Session = Depends(get_db)
):
    """Get weekly results for a league"""
    query = db.query(models.WeeklyResult).filter(
        models.WeeklyResult.league_id == league_id,
        models.WeeklyResult.season == season
    )
    
    if week:
        query = query.filter(models.WeeklyResult.week == week)
    
    results = query.order_by(models.WeeklyResult.week, models.WeeklyResult.rank).all()
    return results

@app.get("/api/leagues/{league_id}/analytics")
async def get_league_analytics(league_id: str, db: Session = Depends(get_db)):
    """Get competitive balance and analytics"""
    # Query transactions, rosters, weekly results
    # Calculate analytics like:
    # - Can you buy a championship?
    # - Rebuild success rate
    # - Transaction volume impact
    
    transactions = db.query(models.Transaction).filter(
        models.Transaction.league_id == league_id
    ).all()
    
    weekly = db.query(models.WeeklyResult).filter(
        models.WeeklyResult.league_id == league_id
    ).all()
    
    # Calculate metrics
    return {
        "league_id": league_id,
        "total_transactions": len(transactions),
        "total_weeks": len(set([w.week for w in weekly])),
        # Add more analytics here
    }

@app.get("/api/players/{player_id}/stats/{season}")
async def get_player_stats(player_id: str, season: str, db: Session = Depends(get_db)):
    """Get player stats for a season"""
    stats = db.query(models.PlayerStats).filter(
        models.PlayerStats.player_id == player_id,
        models.PlayerStats.season == season
    ).first()
    
    if not stats:
        raise HTTPException(status_code=404, detail="Player stats not found")
    
    return stats

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db = database.SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## Option 2: Cloud SQL Auth Proxy (More Secure)

For better security, use Cloud SQL Auth Proxy:

### Install in Docker (Railway)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Cloud SQL Proxy
RUN apt-get update && apt-get install -y wget
RUN wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
RUN chmod +x cloud_sql_proxy

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Start script
CMD ./cloud_sql_proxy -instances=fantasy-snipe-ai:northamerica-northeast1:nhl-api-db-montreal=tcp:5432 & uvicorn main:app --host 0.0.0.0 --port $PORT
```

Then use `localhost:5432` as your database host.

## Test Connection

```bash
# Test from local machine
psql -h 34.47.23.137 -p 5432 -U postgres -d nhl_api

# Test from Python
python -c "import psycopg2; conn = psycopg2.connect(host='34.47.23.137', port=5432, database='nhl_api', user='postgres', password='YOUR_PASSWORD'); print('Connected!')"
```

## Security Checklist

✅ **Enable SSL:** Add `?sslmode=require` to connection string  
✅ **Whitelist IPs:** Only allow Railway and necessary IPs  
✅ **Use strong password:** Update default postgres password  
✅ **Create read-only user:** For analytics/reporting  
✅ **Enable Cloud SQL IAM:** Use IAM authentication instead of passwords  
✅ **Set up backups:** Enable automated backups in Cloud SQL  

## Next Steps

1. ✅ Connection details configured
2. 🔲 Set up Railway environment variables
3. 🔲 Create database tables/schema
4. 🔲 Import JSON data into Cloud SQL
5. 🔲 Deploy FastAPI endpoints
6. 🔲 Test API from Next.js frontend

Do you want me to:
1. Create the database schema SQL?
2. Write a script to import your JSON data?
3. Set up the complete FastAPI project structure?

