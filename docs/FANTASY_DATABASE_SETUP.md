# Fantasy Sports Database Setup Guide

This guide covers setting up the fantasy sports database to integrate CBS Sports league data with your NHL metrics.

## 🗄️ Database Architecture

### **Two-Database Approach (Recommended)**

```
┌─────────────────┐    ┌──────────────────┐
│   NHL Database  │    │ Fantasy Database │
│   (Google Cloud)│    │ (Railway/Cloud)  │
│                 │    │                  │
│ • Player Data   │    │ • League Info    │
│ • Game Events   │    │ • Team Rosters   │
│ • Shift Metrics │    │ • Transactions   │
│ • Advanced Stats│    │ • Fantasy Rules  │
└─────────────────┘    └──────────────────┘
         │                       │
         └───────────────────────┘
                    │
         ┌─────────────────────┐
         │ Integration Layer   │
         │ • Player Matching   │
         │ • Metrics Mapping   │
         │ • Trade Analysis    │
         └─────────────────────┘
```

## 🚀 Deployment Options

### **Option 1: Railway (Recommended for Development)**

**Pros:**
- ✅ Easy setup and deployment
- ✅ Free tier available
- ✅ Automatic scaling
- ✅ Built-in PostgreSQL

**Setup Steps:**

1. **Create Railway Account**
   ```bash
   # Visit https://railway.app
   # Sign up with GitHub
   ```

2. **Create New Project**
   ```bash
   # Click "New Project"
   # Select "Provision PostgreSQL"
   ```

3. **Get Database URL**
   ```bash
   # Copy the DATABASE_URL from Railway dashboard
   # Format: postgresql://user:pass@host:port/database
   ```

4. **Set Environment Variables**
   ```bash
   export DATABASE_URL="postgresql://..."
   ```

### **Option 2: Google Cloud SQL**

**Pros:**
- ✅ Same platform as NHL database
- ✅ Advanced security features
- ✅ Better integration with existing infrastructure

**Setup Steps:**

1. **Create Cloud SQL Instance**
   ```bash
   gcloud sql instances create fantasy-sports-db \
     --database-version=POSTGRES_14 \
     --tier=db-f1-micro \
     --region=us-central1 \
     --storage-type=SSD \
     --storage-size=10GB
   ```

2. **Create Database**
   ```bash
   gcloud sql databases create fantasy_sports \
     --instance=fantasy-sports-db
   ```

3. **Create User**
   ```bash
   gcloud sql users create fantasy_user \
     --instance=fantasy-sports-db \
     --password=your_secure_password
   ```

4. **Set Environment Variables**
   ```bash
   export FANTASY_DB_HOST="your-instance-ip"
   export FANTASY_DB_PORT="5432"
   export FANTASY_DB_NAME="fantasy_sports"
   export FANTASY_DB_USER="fantasy_user"
   export FANTASY_DB_PASSWORD="your_secure_password"
   ```

### **Option 3: Local Development**

**For testing and development:**

```bash
# Install PostgreSQL locally
brew install postgresql  # macOS
sudo apt-get install postgresql  # Ubuntu

# Create database
createdb fantasy_sports

# Set environment variable
export DATABASE_URL="postgresql://localhost/fantasy_sports"
```

## 📊 Database Schema

### **Core Tables**

1. **`fantasy_leagues`** - League information
2. **`fantasy_league_settings`** - Rules and configuration
3. **`fantasy_scoring_rules`** - Individual scoring rules
4. **`fantasy_teams`** - Team information and owners
5. **`fantasy_players`** - Player rosters
6. **`fantasy_transactions`** - Add/drop/trade history
7. **`fantasy_player_metrics`** - Integrated NHL metrics
8. **`fantasy_player_valuations`** - Trade analysis

### **Key Relationships**

```
FantasyLeague (1) ←→ (Many) FantasyTeam
FantasyTeam (1) ←→ (Many) FantasyPlayer
FantasyPlayer (1) ←→ (Many) FantasyPlayerMetrics
FantasyPlayer (1) ←→ (Many) FantasyTransaction
```

## 🔧 Setup and Initialization

### **1. Initialize Database**

```bash
# Test connections and create tables
python3 scripts/populate_fantasy_database.py \
  --init-db \
  --test-connection
```

### **2. Populate with CBS Data**

```bash
# Populate database with CBS Sports data
python3 scripts/populate_fantasy_database.py \
  --cbs-data cbs_league_rosters.json
```

### **3. Verify Setup**

```bash
# Check database contents
python3 scripts/populate_fantasy_database.py \
  --test-connection
```

## 🔗 Integration with NHL Database

### **Player Matching Strategy**

1. **Exact Name Match** - Direct name comparison
2. **Fuzzy Name Match** - Handle spelling variations
3. **Team + Name Match** - Use team abbreviation as filter
4. **Manual Override** - Handle edge cases

### **Metrics Integration**

```python
# Example: Get player's advanced metrics
def get_player_fantasy_metrics(player_id: int, game_id: int):
    """Get integrated NHL metrics for fantasy player"""
    
    # Get fantasy player info
    fantasy_player = session.query(FantasyPlayer).filter(
        FantasyPlayer.id == player_id
    ).first()
    
    # Get NHL metrics
    nhl_metrics = session.query(PlayerGameAdvancedMetricsFlat).filter(
        PlayerGameAdvancedMetricsFlat.player_id == fantasy_player.nhl_player_id,
        PlayerGameAdvancedMetricsFlat.game_id == game_id
    ).first()
    
    # Calculate fantasy points based on league rules
    fantasy_points = calculate_fantasy_points(nhl_metrics, league_scoring_rules)
    
    return {
        'player': fantasy_player,
        'nhl_metrics': nhl_metrics,
        'fantasy_points': fantasy_points
    }
```

## 📈 Data Flow

### **Daily Update Process**

```mermaid
graph TD
    A[CBS Sports API] --> B[Extract League Data]
    B --> C[Update Fantasy Database]
    C --> D[NHL Metrics Database]
    D --> E[Calculate Fantasy Points]
    E --> F[Update Player Valuations]
    F --> G[Generate Trade Analysis]
```

### **Weekly Deep Dive**

```mermaid
graph TD
    A[Browser Automation] --> B[Extract Full Rosters]
    B --> C[Update Player Lists]
    C --> D[Match NHL Players]
    D --> E[Calculate Advanced Metrics]
    E --> F[Generate Trade Recommendations]
```

## 🛠️ Usage Examples

### **Get League Information**

```python
from src.database.fantasy_connection import get_fantasy_session
from src.database.fantasy_models import FantasyLeague

with get_fantasy_session() as session:
    league = session.query(FantasyLeague).filter(
        FantasyLeague.league_id == 'uhhp'
    ).first()
    
    print(f"League: {league.name}")
    print(f"Teams: {len(league.teams)}")
    print(f"Scoring System: {league.scoring_system}")
```

### **Get Team Roster**

```python
from src.database.fantasy_models import FantasyTeam, FantasyPlayer

with get_fantasy_session() as session:
    team = session.query(FantasyTeam).filter(
        FantasyTeam.team_name == "The Inglorious Basteeerds"
    ).first()
    
    players = session.query(FantasyPlayer).filter(
        FantasyPlayer.team_id == team.id
    ).all()
    
    for player in players:
        print(f"{player.player_name} ({player.position}) - {player.nhl_team}")
```

### **Calculate Player Value**

```python
def calculate_player_value(player_id: int):
    """Calculate fantasy value based on NHL metrics"""
    
    # Get player's recent metrics
    recent_metrics = session.query(FantasyPlayerMetrics).filter(
        FantasyPlayerMetrics.player_id == player_id
    ).order_by(FantasyPlayerMetrics.game_date.desc()).limit(10).all()
    
    # Calculate average fantasy points
    avg_points = sum(m.fantasy_points_earned for m in recent_metrics) / len(recent_metrics)
    
    # Factor in consistency and injury risk
    consistency = calculate_consistency_score(recent_metrics)
    injury_risk = calculate_injury_risk(player_id)
    
    return {
        'fantasy_value': avg_points * consistency * (1 - injury_risk),
        'consistency': consistency,
        'injury_risk': injury_risk
    }
```

## 🔒 Security Considerations

### **Environment Variables**

```bash
# Never commit these to version control
export DATABASE_URL="postgresql://..."
export FANTASY_DB_PASSWORD="..."

# Use .env file for local development
echo "DATABASE_URL=postgresql://..." > .env
```

### **Database Permissions**

```sql
-- Create read-only user for analytics
CREATE USER fantasy_analytics WITH PASSWORD 'secure_password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO fantasy_analytics;

-- Create write user for updates
CREATE USER fantasy_updater WITH PASSWORD 'secure_password';
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO fantasy_updater;
```

## 📊 Monitoring and Maintenance

### **Database Health Checks**

```python
def check_database_health():
    """Monitor database performance and data quality"""
    
    with get_fantasy_session() as session:
        # Check table sizes
        league_count = session.query(FantasyLeague).count()
        team_count = session.query(FantasyTeam).count()
        player_count = session.query(FantasyPlayer).count()
        
        # Check data freshness
        latest_update = session.query(FantasyPlayer).order_by(
            FantasyPlayer.updated_at.desc()
        ).first().updated_at
        
        return {
            'leagues': league_count,
            'teams': team_count,
            'players': player_count,
            'last_update': latest_update
        }
```

### **Backup Strategy**

```bash
# Daily backups
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Automated backups with Railway
# Railway provides automatic backups every 24 hours
```

## 🚀 Next Steps

1. **Deploy Database** - Choose Railway or Google Cloud
2. **Initialize Schema** - Run the setup script
3. **Populate Data** - Import CBS Sports league data
4. **Test Integration** - Verify NHL metrics connection
5. **Build Analytics** - Create trade analysis tools
6. **Automate Updates** - Set up daily/weekly sync

## 📞 Support

For issues with:
- **Database Setup**: Check connection strings and permissions
- **Data Population**: Verify CBS Sports data format
- **Integration**: Ensure NHL database is accessible
- **Performance**: Monitor query execution times 