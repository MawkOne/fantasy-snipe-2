# FastAPI NHL Data Endpoints

## Endpoints to Create

Based on your Cloud SQL database, here are the API endpoints you should add to your FastAPI backend:

### Player Endpoints

```python
@app.get("/api/players/search")
async def search_players(q: str, db: Session = Depends(get_db)):
    """Search players by name"""
    players = db.query(models.Player).filter(
        models.Player.full_name.ilike(f"%{q}%")
    ).limit(20).all()
    return players

@app.get("/api/players/{player_id}")
async def get_player(player_id: int, db: Session = Depends(get_db)):
    """Get player details"""
    player = db.query(models.Player).filter(
        models.Player.id == player_id
    ).first()
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    return player

@app.get("/api/players/{player_id}/season-stats")
async def get_player_season_stats(
    player_id: int, 
    season: str = "20242025",
    db: Session = Depends(get_db)
):
    """Get player stats for a season"""
    stats = db.query(models.PlayerCareerStats).filter(
        models.PlayerCareerStats.player_id == player_id,
        models.PlayerCareerStats.season == season
    ).first()
    
    return stats

@app.get("/api/players/{player_id}/game-log")
async def get_player_game_log(
    player_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get player's recent games"""
    game_stats = db.query(models.PlayerGameStats).filter(
        models.PlayerGameStats.player_id == player_id
    ).order_by(
        models.PlayerGameStats.game_id.desc()
    ).limit(limit).all()
    
    return game_stats
```

### Game Endpoints

```python
@app.get("/api/games/upcoming")
async def get_upcoming_games(
    team_id: int = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get upcoming games"""
    query = db.query(models.Game).filter(
        models.Game.game_state == "SCHEDULED"
    )
    
    if team_id:
        query = query.filter(
            or_(
                models.Game.home_team_id == team_id,
                models.Game.away_team_id == team_id
            )
        )
    
    games = query.order_by(models.Game.game_date).limit(limit).all()
    return games

@app.get("/api/games/{game_id}")
async def get_game(game_id: int, db: Session = Depends(get_db)):
    """Get game details"""
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game

@app.get("/api/games/{game_id}/events")
async def get_game_events(game_id: int, db: Session = Depends(get_db)):
    """Get all events for a game (goals, penalties, etc.)"""
    events = db.query(models.GameEvent).filter(
        models.GameEvent.game_id == game_id
    ).order_by(models.GameEvent.period, models.GameEvent.time_in_period).all()
    return events
```

### Team Endpoints

```python
@app.get("/api/teams")
async def get_teams(db: Session = Depends(get_db)):
    """Get all NHL teams"""
    teams = db.query(models.Team).all()
    return teams

@app.get("/api/teams/{team_id}")
async def get_team(team_id: int, db: Session = Depends(get_db)):
    """Get team details"""
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@app.get("/api/teams/{team_id}/roster")
async def get_team_roster(team_id: int, db: Session = Depends(get_db)):
    """Get team's current roster"""
    players = db.query(models.Player).filter(
        models.Player.team_id == team_id,
        models.Player.is_active == True
    ).all()
    return players
```

### Stats Endpoints

```python
@app.get("/api/stats/leaders")
async def get_stat_leaders(
    stat: str = "points",
    season: str = "20242025",
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get league leaders for a specific stat"""
    # Query based on stat type
    if stat == "points":
        leaders = db.query(
            models.PlayerCareerStats
        ).filter(
            models.PlayerCareerStats.season == season
        ).order_by(
            (models.PlayerCareerStats.goals + models.PlayerCareerStats.assists).desc()
        ).limit(limit).all()
    
    return leaders
```

## Full Example FastAPI File

```python
# main.py
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from typing import List, Optional
import os
from database import get_db, engine
import models

app = FastAPI(
    title="NHL Fantasy API",
    description="API for NHL player stats and fantasy league data",
    version="1.0.0"
)

# Health check
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# ... (add all the endpoints above)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

## Models (models.py)

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Player(Base):
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    sweater_number = Column(Integer)
    position_code = Column(String(1))
    headshot_url = Column(String)
    is_active = Column(Boolean)
    team_id = Column(Integer, ForeignKey("teams.id"))

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True)
    # Add other team fields based on your schema

class Game(Base):
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True)
    # Add game fields

class PlayerGameStats(Base):
    __tablename__ = "player_game_stats"
    
    player_id = Column(Integer, ForeignKey("players.id"), primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id"), primary_key=True)
    goals = Column(Integer)
    assists = Column(Integer)
    # Add other stat fields

class PlayerCareerStats(Base):
    __tablename__ = "player_career_stats"
    
    player_id = Column(Integer, ForeignKey("players.id"), primary_key=True)
    season = Column(String, primary_key=True)
    games_played = Column(Integer)
    goals = Column(Integer)
    assists = Column(Integer)
    # Add other career stat fields
```

## Testing

```bash
# Search for players
curl "https://fastapi-production-45ce.up.railway.app/api/players/search?q=Caufield"

# Get player details
curl "https://fastapi-production-45ce.up.railway.app/api/players/8481540"

# Get player stats
curl "https://fastapi-production-45ce.up.railway.app/api/players/8481540/season-stats?season=20242025"

# Get teams
curl "https://fastapi-production-45ce.up.railway.app/api/teams"
```

## Next Steps

1. Copy the endpoint code to your FastAPI project
2. Create the models based on your database schema
3. Deploy to Railway
4. Test endpoints
5. Use in Next.js with the React hooks I created

