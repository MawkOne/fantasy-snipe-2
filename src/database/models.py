from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, DateTime, Time, Float, JSON, UniqueConstraint, Index
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from src.database.connection import connect_with_connector

Base = declarative_base()

class Team(Base):
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True, autoincrement=False)
    franchise_id = Column(Integer)
    full_name = Column(String, nullable=False)
    league_id = Column(Integer)
    raw_tricode = Column(String(3))
    tri_code = Column(String(3))

    players = relationship("Player", back_populates="team")
    home_games = relationship("Game", foreign_keys="[Game.home_team_id]", back_populates="home_team")
    away_games = relationship("Game", foreign_keys="[Game.away_team_id]", back_populates="away_team")
    game_stats = relationship("PlayerGameStats", back_populates="team")

    def __repr__(self):
        return f"<Team(id={self.id}, full_name='{self.full_name}')>"

class Player(Base):
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True, autoincrement=False)
    full_name = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    sweater_number = Column(Integer)
    position_code = Column(String(1))
    headshot_url = Column(String)
    is_active = Column(Boolean, default=True)

    team_id = Column(Integer, ForeignKey('teams.id'))
    team = relationship("Team", back_populates="players")
    game_stats = relationship("PlayerGameStats", back_populates="player")

    def __repr__(self):
        return f"<Player(id={self.id}, full_name='{self.full_name}')>"

class Game(Base):
    __tablename__ = 'games'

    id = Column(Integer, primary_key=True, autoincrement=False)
    season = Column(Integer, nullable=False)
    game_type = Column(Integer)
    game_date = Column(DateTime, nullable=False)
    game_state = Column(String)

    home_team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    away_team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    
    home_score = Column(Integer)
    away_score = Column(Integer)

    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_games")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_games")
    player_stats = relationship("PlayerGameStats", back_populates="game")

    def __repr__(self):
        return f"<Game(id={self.id}, date='{self.game_date}', home_team={self.home_team_id}, away_team={self.away_team_id})>"

class PlayerGameStats(Base):
    __tablename__ = 'player_game_stats'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    game_id = Column(Integer, ForeignKey('games.id'), nullable=False)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)

    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    points = Column(Integer, default=0)
    plus_minus = Column(Integer, default=0)
    power_play_goals = Column(Integer, default=0)
    power_play_points = Column(Integer, default=0)
    game_winning_goals = Column(Integer, default=0)
    ot_goals = Column(Integer, default=0)
    shots = Column(Integer, default=0)
    shifts = Column(Integer, default=0)
    shorthanded_goals = Column(Integer, default=0)
    shorthanded_points = Column(Integer, default=0)
    pim = Column(Integer, default=0)
    toi = Column(String) # Time on Ice, e.g., "18:10"

    player = relationship("Player", back_populates="game_stats")
    game = relationship("Game", back_populates="player_stats")
    team = relationship("Team", back_populates="game_stats")

    def __repr__(self):
        return f"<PlayerGameStats(player_id={self.player_id}, game_id={self.game_id}, points={self.points})>"


class GoalieGameStats(Base):
    __tablename__ = 'goalie_game_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    game_id = Column(Integer, ForeignKey('games.id'), nullable=False)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)

    shots_against = Column(Integer, default=0)
    saves = Column(Integer, default=0)
    save_pct = Column(Float)  # e.g., 0.923
    goals_against = Column(Integer, default=0)
    shutout = Column(Boolean, default=False)
    decision = Column(String)  # 'W', 'L', 'OT', or None
    games_started = Column(Integer, default=0)
    toi = Column(String)  # "59:58"

    player = relationship("Player")
    game = relationship("Game")
    team = relationship("Team")

    def __repr__(self):
        return (
            f"<GoalieGameStats(player_id={self.player_id}, game_id={self.game_id}, "
            f"saves={self.saves}, shots_against={self.shots_against}, save_pct={self.save_pct})>"
        )


class PlayerCareerStats(Base):
    __tablename__ = 'player_career_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    # 2 = Regular Season, 3 = Playoffs (aligns with games.game_type)
    game_type = Column(Integer, nullable=False)

    games_played = Column(Integer, default=0)
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    points = Column(Integer, default=0)
    plus_minus = Column(Integer, default=0)
    pim = Column(Integer, default=0)
    shots = Column(Integer, default=0)
    power_play_goals = Column(Integer, default=0)
    power_play_points = Column(Integer, default=0)
    shorthanded_goals = Column(Integer, default=0)
    shorthanded_points = Column(Integer, default=0)
    game_winning_goals = Column(Integer, default=0)
    ot_goals = Column(Integer, default=0)

    player = relationship("Player")

    def __repr__(self):
        return (
            f"<PlayerCareerStats(player_id={self.player_id}, game_type={self.game_type}, "
            f"gp={self.games_played}, points={self.points})>"
        )


class PlayerShift(Base):
    __tablename__ = 'player_shifts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    game_id = Column(Integer, ForeignKey('games.id'), nullable=False)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)

    shift_number = Column(Integer, nullable=True)
    period = Column(Integer, nullable=True)
    start_time = Column(String)  # "MM:SS"
    end_time = Column(String)    # "MM:SS"
    duration = Column(String)    # "MM:SS"

    player = relationship("Player")
    game = relationship("Game")
    team = relationship("Team")

    def __repr__(self):
        return (
            f"<PlayerShift(player_id={self.player_id}, game_id={self.game_id}, "
            f"shift_number={self.shift_number}, period={self.period})>"
        )


class PlayerDetails(Base):
    __tablename__ = 'player_details'

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False, unique=True)

    birth_date = Column(String)  # e.g., "1997-02-14"
    height_in_inches = Column(Integer)
    weight_in_pounds = Column(Integer)
    shoots_catches = Column(String)
    nationality = Column(String)
    birth_city = Column(String)
    birth_state_province = Column(String)
    birth_country = Column(String)
    rookie = Column(Boolean)

    current_team_id = Column(Integer)
    current_team_tricode = Column(String(3))

    player = relationship("Player")

    def __repr__(self):
        return f"<PlayerDetails(player_id={self.player_id}, shoots_catches={self.shoots_catches})>"


class GameEvent(Base):
    __tablename__ = 'game_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey('games.id'), nullable=False, index=True)
    event_idx = Column(Integer)  # sequential index if provided by API
    period = Column(Integer)
    period_time = Column(String)  # e.g., "12:34"
    period_time_remaining = Column(String)
    event_type = Column(String)
    description = Column(String)
    team_id = Column(Integer, ForeignKey('teams.id'))
    # Primary actor for the event (e.g., Scorer, Shooter, Hitter, Taker, Giver, Winner, PenaltyOn)
    primary_player_id = Column(Integer)
    secondary_type = Column(String)
    coordinates_x = Column(Float)
    coordinates_y = Column(Float)
    raw = Column(JSON)  # raw event payload for completeness

    def __repr__(self):
        return (
            f"<GameEvent(game_id={self.game_id}, idx={self.event_idx}, period={self.period}, "
            f"type={self.event_type}, time={self.period_time})>"
        )


class PlayerShiftMetrics(Base):
    __tablename__ = 'player_shift_metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    game_id = Column(Integer, ForeignKey('games.id'), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    shift_number = Column(Integer, nullable=True)
    period = Column(Integer, nullable=True)
    start_time = Column(String)  # MM:SS
    end_time = Column(String)    # MM:SS
    duration = Column(String)    # MM:SS

    attempts_for = Column(Integer, default=0)
    attempts_against = Column(Integer, default=0)
    unblocked_for = Column(Integer, default=0)
    unblocked_against = Column(Integer, default=0)
    shots_for = Column(Integer, default=0)
    shots_against = Column(Integer, default=0)
    goals_for = Column(Integer, default=0)
    goals_against = Column(Integer, default=0)
    hits_for = Column(Integer, default=0)
    hits_against = Column(Integer, default=0)
    takeaways_for = Column(Integer, default=0)
    takeaways_against = Column(Integer, default=0)
    giveaways_for = Column(Integer, default=0)
    giveaways_against = Column(Integer, default=0)
    blocks_for = Column(Integer, default=0)
    blocks_against = Column(Integer, default=0)

    zone_start = Column(String)  # 'O','D','N' or None
    faceoff_won = Column(Boolean)
    strength_state = Column(String)  # 'EV','PP','SH' (approximate)
    teammates_on_ice = Column(Integer)
    opponents_on_ice = Column(Integer)
    teammates_on_ice_ids = Column(JSON)
    opponents_on_ice_ids = Column(JSON)

    __table_args__ = (
        UniqueConstraint('player_id', 'game_id', 'shift_number', name='uq_player_shift_metrics_key'),
    )


class PlayerGameAdvancedMetrics(Base):
    __tablename__ = 'player_game_advanced_metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    game_id = Column(Integer, ForeignKey('games.id'), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey('teams.id'))
    season = Column(Integer)
    game_type = Column(Integer)
    # Entire metrics payload as produced by scripts/player_metrics_report.py
    summary = Column(JSON, nullable=False)

    __table_args__ = (
        UniqueConstraint('player_id', 'game_id', name='uq_player_game_adv_metrics_key'),
        Index('idx_pg_adv_player', 'player_id'),
        Index('idx_pg_adv_game', 'game_id'),
    )

class PlayerGameAdvancedMetricsFlat(Base):
    __tablename__ = 'player_game_advanced_metrics_flat'

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    game_id = Column(Integer, ForeignKey('games.id'), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey('teams.id'))
    season = Column(Integer)
    game_type = Column(Integer)

    # Core totals
    CF = Column(Integer, default=0)
    CA = Column(Integer, default=0)
    FF = Column(Integer, default=0)
    FA = Column(Integer, default=0)
    SF = Column(Integer, default=0)
    SA = Column(Integer, default=0)
    GF = Column(Integer, default=0)
    GA = Column(Integer, default=0)

    # Rates and percentages
    CF_pct = Column(Float)
    FF_pct = Column(Float)
    SF_pct = Column(Float)
    GF_pct = Column(Float)
    CF60 = Column(Float)
    FF60 = Column(Float)
    SF60 = Column(Float)
    GF60 = Column(Float)
    PDO = Column(Float)

    # Time on ice and shifts
    TOI_seconds = Column(Integer, default=0)
    shifts = Column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint('player_id', 'game_id', name='uq_player_game_adv_flat_key'),
        Index('idx_pg_adv_flat_player', 'player_id'),
        Index('idx_pg_adv_flat_game', 'game_id'),
    )

def create_tables():
    """
    Creates all tables defined in this model in the database.
    """
    engine = connect_with_connector()
    print("Creating tables...")
    Base.metadata.create_all(engine)
    print("Tables created successfully.")

if __name__ == '__main__':
    create_tables()
