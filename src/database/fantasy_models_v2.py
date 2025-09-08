"""
Fantasy Sports Database Models v2 - Multi-User Support
Enhanced schema for proper multi-user fantasy sports management
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, JSON, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class FantasyUser(Base):
    """Fantasy sports user accounts"""
    __tablename__ = 'fantasy_users'
    
    id = Column(Integer, primary_key=True)
    
    # Authentication info (from external auth service)
    external_auth_id = Column(String(100), unique=True)  # Kinde user ID
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
    owned_leagues = relationship("FantasyLeague", back_populates="owner", foreign_keys="FantasyLeague.owner_id")
    league_memberships = relationship("FantasyUserLeague", back_populates="user", foreign_keys="FantasyUserLeague.user_id")
    owned_teams = relationship("FantasyTeam", back_populates="owner", foreign_keys="FantasyTeam.owner_id")
    api_keys = relationship("FantasyAPIKey", back_populates="user")

class FantasyLeague(Base):
    """Fantasy league information"""
    __tablename__ = 'fantasy_leagues'
    
    id = Column(Integer, primary_key=True)
    
    # League identification
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
    
    # Ownership and access control
    owner_id = Column(Integer, ForeignKey('fantasy_users.id'), nullable=False)  # Who imported this league
    is_public = Column(Boolean, default=False)  # Can other users discover/join
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_sync = Column(DateTime)  # When data was last updated from CBS
    
    # Relationships
    owner = relationship("FantasyUser", back_populates="owned_leagues", foreign_keys=[owner_id])
    teams = relationship("FantasyTeam", back_populates="league")
    league_settings = relationship("FantasyLeagueSettings", back_populates="league", uselist=False)
    scoring_rules = relationship("FantasyScoringRule", back_populates="league")
    user_memberships = relationship("FantasyUserLeague", back_populates="league", foreign_keys="FantasyUserLeague.league_id")

class FantasyUserLeague(Base):
    """User participation in leagues"""
    __tablename__ = 'fantasy_user_leagues'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('fantasy_users.id'), nullable=False)
    league_id = Column(Integer, ForeignKey('fantasy_leagues.id'), nullable=False)
    
    # Role in this specific league
    role = Column(String(50), default='member')  # 'owner', 'commissioner', 'member', 'viewer'
    
    # Permissions for this league
    can_view_rosters = Column(Boolean, default=True)
    can_make_transactions = Column(Boolean, default=False)
    can_trade = Column(Boolean, default=False)
    can_manage_league = Column(Boolean, default=False)
    can_invite_users = Column(Boolean, default=False)
    
    # Timestamps
    joined_at = Column(DateTime, default=func.now())
    invited_by = Column(Integer, ForeignKey('fantasy_users.id'))
    
    # Relationships
    user = relationship("FantasyUser", back_populates="league_memberships", foreign_keys=[user_id])
    league = relationship("FantasyLeague", back_populates="user_memberships", foreign_keys=[league_id])
    
    # Ensure unique user-league combinations
    __table_args__ = (UniqueConstraint('user_id', 'league_id', name='unique_user_league'),)

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
    owner_name = Column(String(200))  # Display name from CBS
    team_id = Column(String(50))  # CBS team ID
    
    # Owner relationship (who manages this team in our system)
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
    owner = relationship("FantasyUser", back_populates="owned_teams", foreign_keys=[owner_id])

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

class FantasyLeagueInvitation(Base):
    """League invitations for multi-user support"""
    __tablename__ = 'fantasy_league_invitations'
    
    id = Column(Integer, primary_key=True)
    league_id = Column(Integer, ForeignKey('fantasy_leagues.id'), nullable=False)
    invited_email = Column(String(200), nullable=False)
    
    # Invitation details
    role = Column(String(50), default='member')  # Role they'll have when they join
    permissions = Column(JSON)  # Specific permissions
    
    # Status
    is_accepted = Column(Boolean, default=False)
    is_expired = Column(Boolean, default=False)
    expires_at = Column(DateTime)
    
    # Invitation metadata
    invited_by = Column(Integer, ForeignKey('fantasy_users.id'), nullable=False)
    invitation_code = Column(String(100), unique=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    accepted_at = Column(DateTime)
    
    # Relationships
    league = relationship("FantasyLeague")
    inviter = relationship("FantasyUser") 


class FantasySeasonRanking(Base):
    """Cached season rankings for fast reads by the frontend"""
    __tablename__ = 'fantasy_season_rankings'

    id = Column(Integer, primary_key=True)

    # Season and identity
    season = Column(Integer, nullable=False, index=True)  # e.g., 2024
    nhl_player_id = Column(Integer, nullable=False)
    player_name = Column(String(200), nullable=False)
    position = Column(String(10))
    team = Column(String(10))

    # Totals
    gp = Column(Integer, default=0)
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    points = Column(Integer, default=0)
    shots = Column(Integer, default=0)
    pim = Column(Integer, default=0)
    plus_minus = Column(Integer, default=0)

    # Display
    rank = Column(Integer, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('season', 'nhl_player_id', name='uq_rankings_season_player'),
        Index('idx_rankings_season_rank', 'season', 'rank'),
    )