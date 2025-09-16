"""
Fantasy Sports Database Connection Manager
Handles connections to the fantasy sports database (separate from NHL database)
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)

class FantasyDatabaseManager:
    """Manages connections to the fantasy sports database"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the fantasy database manager
        
        Args:
            database_url: Database connection URL. If not provided, will use environment variables.
        """
        self.database_url = database_url or self._get_database_url()
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()
    
    def _get_database_url(self) -> str:
        """Get database URL from environment variables"""
        def _sanitize_db_url(raw: str | None) -> str | None:
            if not raw:
                return None
            value = raw.strip().strip('\"').strip("'")
            # Handle mistaken 'KEY=postgresql://...' values (e.g., 'NHL_DATABASE_URL=postgresql://...')
            if '://' not in value and '=' in value:
                maybe = value.split('=')[-1].strip()
                if '://' in maybe:
                    value = maybe
            # Normalize deprecated scheme
            if value.startswith('postgres://'):
                value = 'postgresql://' + value[len('postgres://'):]
            # Trim whitespace/newlines again after normalization
            value = value.strip()
            return value if '://' in value else None

        # Prefer DATABASE_URL when valid (Railway sets this)
        db_url = _sanitize_db_url(os.getenv('DATABASE_URL'))
        if db_url:
            return db_url

        # Accept FANTASY_DATABASE_URL if present and valid
        db_url = _sanitize_db_url(os.getenv('FANTASY_DATABASE_URL'))
        if db_url:
            return db_url

        # Compose from PG* envs if available (Railway exposes these too)
        pg_host = os.getenv('PGHOST')
        pg_port = os.getenv('PGPORT', '5432')
        pg_db = os.getenv('PGDATABASE') or os.getenv('POSTGRES_DB')
        pg_user = os.getenv('PGUSER') or os.getenv('POSTGRES_USER')
        pg_pass = os.getenv('PGPASSWORD') or os.getenv('POSTGRES_PASSWORD')
        if pg_host and pg_user and pg_pass and pg_db:
            base = f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
            sslmode = os.getenv('PGSSLMODE') or os.getenv('SSL_MODE')
            if sslmode and 'sslmode=' not in base:
                return f"{base}?sslmode={sslmode}"
            return base
        
        # Check for Google Cloud SQL
        if os.getenv('FANTASY_DB_HOST'):
            host = os.getenv('FANTASY_DB_HOST')
            port = os.getenv('FANTASY_DB_PORT', '5432')
            database = os.getenv('FANTASY_DB_NAME', 'fantasy_sports')
            user = os.getenv('FANTASY_DB_USER')
            password = os.getenv('FANTASY_DB_PASSWORD')
            
            if all([host, user, password]):
                return f"postgresql://{user}:{password}@{host}:{port}/{database}"
        
        # Default to local development
        return "postgresql://localhost/fantasy_sports"
    
    def _initialize_engine(self):
        """Initialize the SQLAlchemy engine"""
        try:
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False  # Set to True for SQL debugging
            )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info(f"Fantasy database engine initialized: {self.database_url.split('@')[0]}@***")
            
        except Exception as e:
            logger.error(f"Failed to initialize fantasy database engine: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Session:
        """Get a database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """Create all fantasy database tables"""
        try:
            from .fantasy_models import Base
            Base.metadata.create_all(bind=self.engine)
            logger.info("Fantasy database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create fantasy database tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all fantasy database tables (use with caution!)"""
        try:
            from .fantasy_models import Base
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("Fantasy database tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop fantasy database tables: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_session() as session:
                from sqlalchemy import text
                session.execute(text("SELECT 1"))
                logger.info("Fantasy database connection test successful")
                return True
        except Exception as e:
            logger.error(f"Fantasy database connection test failed: {e}")
            return False
    
    def get_database_info(self) -> dict:
        """Get database information"""
        try:
            with self.get_session() as session:
                # Get table counts
                from .fantasy_models import (
                    FantasyLeague, FantasyTeam, FantasyPlayer, 
                    FantasyTransaction, FantasyPlayerMetrics
                )
                
                info = {
                    "database_url": self.database_url.split('@')[0] + "@***",
                    "tables": {
                        "fantasy_leagues": session.query(FantasyLeague).count(),
                        "fantasy_teams": session.query(FantasyTeam).count(),
                        "fantasy_players": session.query(FantasyPlayer).count(),
                        "fantasy_transactions": session.query(FantasyTransaction).count(),
                        "fantasy_player_metrics": session.query(FantasyPlayerMetrics).count(),
                    }
                }
                
                return info
                
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {"error": str(e)}

# Global instance
fantasy_db = FantasyDatabaseManager()

def get_fantasy_session() -> Session:
    """Get a fantasy database session"""
    return fantasy_db.get_session()

def init_fantasy_database():
    """Initialize the fantasy database"""
    fantasy_db.create_tables()
    return fantasy_db.test_connection() 