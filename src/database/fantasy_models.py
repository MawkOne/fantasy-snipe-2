"""
Fantasy Sports Database Models
Handles CBS Sports league data and integration with NHL metrics
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class FantasyLeague(Base):
    """Fantasy league information"""
    __tablename__ = 'fantasy_leagues'
    
    id = Column(Integer, primary_key=True)
    league_id = Column(String(50), unique=True, nullable=False)  # e.g., 'uhhp'
    sport = Column(String(20), nullable=False)  # 'hockey', 'football', etc.
    name = Column(String(200), nullable=False)
    platform = Column(String(50), nullable=False)  # 'cbs', 'espn', 'yahoo', etc.
    base_url = Column(String(500))
    
    # League settings
    scoring_system = Column(String(100))  # 'head-to-head', 'rotisserie', etc.
    draft_type = Column(String(50))  # 'snake', 'auction', etc.
    draft_rounds = Column(Integer)
    trade_deadline = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    teams = relationship("FantasyTeam", back_populates="league")
    league_settings = relationship("FantasyLeagueSettings", back_populates="league", uselist=False)
    scoring_rules = relationship("FantasyScoringRule", back_populates="league")

class FantasyLeagueSettings(Base):
    """Detailed league settings and rules"""
    __tablename__ = 'fantasy_league_settings'
    
    id = Column(Integer, primary_key=True)
    league_id = Column(Integer, ForeignKey('fantasy_leagues.id'), nullable=False)
    
    # Roster settings
    roster_positions = Column(JSON)  # {'C': 2, 'LW': 2, 'RW': 2, 'D': 4, 'G': 2, 'BN': 5}
    max_roster_size = Column(Integer)
    
    # Transaction settings
    waiver_period_days = Column(Integer)
    waiver_run_days = Column(String(100))  # 'Sunday, Friday, Saturday'
    trade_approval_required = Column(Boolean, default=True)
    
    # Playoff settings
    playoff_start_period = Column(Integer)
    playoff_weeks = Column(Integer)
    playoff_tiebreaker = Column(String(100))
    
    # Raw settings data
    raw_settings_json = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    league = relationship("FantasyLeague", back_populates="league_settings")

class FantasyScoringRule(Base):
    """Individual scoring rules"""
    __tablename__ = 'fantasy_scoring_rules'
    
    id = Column(Integer, primary_key=True)
    league_id = Column(Integer, ForeignKey('fantasy_leagues.id'), nullable=False)
    
    stat_name = Column(String(50), nullable=False)  # 'G', 'A', 'W', 'S', etc.
    stat_description = Column(String(200))  # 'Goals', 'Assists', 'Wins', etc.
    points = Column(Float, nullable=False)  # 3.0, 2.0, -1.25, etc.
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    league = relationship("FantasyLeague", back_populates="scoring_rules")

class FantasyTeam(Base):
    """Fantasy team information"""
    __tablename__ = 'fantasy_teams'
    
    id = Column(Integer, primary_key=True)
    league_id = Column(Integer, ForeignKey('fantasy_leagues.id'), nullable=False)
    
    # Team identification
    team_name = Column(String(200), nullable=False)
    owner_name = Column(String(200))
    team_id = Column(String(50))  # CBS team ID
    
    # Owner relationship
    owner_id = Column(Integer, ForeignKey('fantasy_users.id'))
    
    # Current status
    current_rank = Column(Integer)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    ties = Column(Integer, default=0)
    total_points = Column(Float, default=0.0)
    
    # Team metadata
    logo_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    league = relationship("FantasyLeague", back_populates="teams")
    roster = relationship("FantasyPlayer", back_populates="team")
    owner = relationship("FantasyUser", back_populates="owned_teams")

class FantasyPlayer(Base):
    """Fantasy player roster information"""
    __tablename__ = 'fantasy_players'
    
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('fantasy_teams.id'), nullable=False)
    
    # Player identification
    nhl_player_id = Column(Integer)  # Link to NHL database
    player_name = Column(String(200), nullable=False)
    position = Column(String(10))  # 'C', 'LW', 'RW', 'D', 'G'
    nhl_team = Column(String(10))  # 'EDM', 'TOR', etc.
    
    # Roster status
    roster_position = Column(String(20))  # 'C', 'LW', 'RW', 'D', 'G', 'BN', 'IR'
    is_active = Column(Boolean, default=True)
    is_injured = Column(Boolean, default=False)
    
    # Fantasy stats (current season)
    fantasy_points = Column(Float, default=0.0)
    games_played = Column(Integer, default=0)
    
    # Timestamps
    added_date = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    team = relationship("FantasyTeam", back_populates="roster")
    transactions = relationship("FantasyTransaction", back_populates="player")

class FantasyTransaction(Base):
    """Player transactions (adds, drops, trades)"""
    __tablename__ = 'fantasy_transactions'
    
    id = Column(Integer, primary_key=True)
    league_id = Column(Integer, ForeignKey('fantasy_leagues.id'), nullable=False)
    player_id = Column(Integer, ForeignKey('fantasy_players.id'), nullable=False)
    
    # Transaction details
    transaction_type = Column(String(20), nullable=False)  # 'add', 'drop', 'trade', 'waiver'
    from_team_id = Column(Integer, ForeignKey('fantasy_teams.id'))
    to_team_id = Column(Integer, ForeignKey('fantasy_teams.id'))
    
    # Transaction metadata
    transaction_date = Column(DateTime, nullable=False)
    processed_date = Column(DateTime)
    is_processed = Column(Boolean, default=False)
    
    # Additional details
    waiver_priority = Column(Integer)
    transaction_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    player = relationship("FantasyPlayer", back_populates="transactions")

class FantasyPlayerMetrics(Base):
    """Integrated NHL metrics for fantasy players"""
    __tablename__ = 'fantasy_player_metrics'
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('fantasy_players.id'), nullable=False)
    game_id = Column(Integer)  # NHL game ID
    
    # NHL advanced metrics (from your existing database)
    corsi_for = Column(Integer, default=0)
    corsi_against = Column(Integer, default=0)
    corsi_percentage = Column(Float)
    
    fenwick_for = Column(Integer, default=0)
    fenwick_against = Column(Integer, default=0)
    fenwick_percentage = Column(Float)
    
    shots_for = Column(Integer, default=0)
    shots_against = Column(Integer, default=0)
    shooting_percentage = Column(Float)
    save_percentage = Column(Float)
    pdo = Column(Float)
    
    # Fantasy-relevant metrics
    fantasy_points_earned = Column(Float, default=0.0)
    games_played = Column(Integer, default=0)
    
    # Danger tiers
    high_danger_shots = Column(Integer, default=0)
    medium_danger_shots = Column(Integer, default=0)
    low_danger_shots = Column(Integer, default=0)
    
    # Timestamps
    game_date = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    player = relationship("FantasyPlayer")

class FantasyPlayerValuation(Base):
    """Player valuation and trade analysis"""
    __tablename__ = 'fantasy_player_valuations'
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('fantasy_players.id'), nullable=False)
    
    # Valuation metrics
    fantasy_value = Column(Float)  # Calculated fantasy value
    trade_value = Column(Float)    # Trade market value
    keeper_value = Column(Float)   # Long-term keeper value
    
    # Performance projections
    projected_fantasy_points = Column(Float)
    projected_games_played = Column(Integer)
    
    # Risk assessment
    injury_risk = Column(Float)  # 0-1 scale
    consistency_score = Column(Float)  # 0-1 scale
    upside_potential = Column(Float)  # 0-1 scale
    
    # Analysis metadata
    analysis_date = Column(DateTime, default=func.now())
    analysis_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    player = relationship("FantasyPlayer") 

class FantasyUser(Base):
    """Fantasy sports user accounts"""
    __tablename__ = 'fantasy_users'
    
    id = Column(Integer, primary_key=True)
    
    # Authentication info (from external auth service)
    external_auth_id = Column(String(100), unique=True)  # Firebase/Auth0 user ID
    email = Column(String(200), unique=True, nullable=False)
    username = Column(String(100), unique=True)
    
    # User profile
    first_name = Column(String(100))
    last_name = Column(String(100))
    display_name = Column(String(200))
    avatar_url = Column(String(500))
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    
    # Permissions and roles
    role = Column(String(50), default='user')  # 'admin', 'commissioner', 'user'
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)
    
    # Relationships
    owned_teams = relationship("FantasyTeam", back_populates="owner")
    api_keys = relationship("FantasyAPIKey", back_populates="user")

class FantasyAPIKey(Base):
    """API keys for programmatic access"""
    __tablename__ = 'fantasy_api_keys'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('fantasy_users.id'), nullable=False)
    
    # API key details
    key_name = Column(String(100), nullable=False)  # e.g., "Fantasy Snipe Bot"
    api_key = Column(String(100), unique=True, nullable=False)
    api_secret = Column(String(200))  # Optional for additional security
    
    # Permissions
    permissions = Column(JSON)  # ['read:leagues', 'write:transactions', etc.]
    
    # Usage tracking
    last_used = Column(DateTime)
    usage_count = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)  # Optional expiration
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("FantasyUser", back_populates="api_keys")

class FantasyUserLeague(Base):
    """User participation in leagues"""
    __tablename__ = 'fantasy_user_leagues'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('fantasy_users.id'), nullable=False)
    league_id = Column(Integer, ForeignKey('fantasy_leagues.id'), nullable=False)
    
    # Role in this specific league
    role = Column(String(50), default='owner')  # 'commissioner', 'owner', 'viewer'
    
    # Permissions for this league
    can_view_rosters = Column(Boolean, default=True)
    can_make_transactions = Column(Boolean, default=True)
    can_trade = Column(Boolean, default=True)
    can_manage_league = Column(Boolean, default=False)
    
    # Timestamps
    joined_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("FantasyUser")
    league = relationship("FantasyLeague") 