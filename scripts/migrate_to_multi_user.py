#!/usr/bin/env python3
"""
Migration Script: Single-User to Multi-User Database Schema
Updates Railway database to support multiple users properly
"""

import os
import sys
import logging
from datetime import datetime
from sqlalchemy import text

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.fantasy_connection import get_fantasy_session
from src.database.fantasy_models_v2 import Base as NewBase
from src.database.fantasy_models_v2 import (
    FantasyUser, FantasyLeague, FantasyTeam, FantasyPlayer,
    FantasyUserLeague, FantasyAPIKey, FantasyLeagueSettings,
    FantasyScoringRule, FantasyTransaction, FantasyPlayerMetrics,
    FantasyPlayerValuation, FantasyLeagueInvitation
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def backup_existing_data():
    """Backup existing data before migration"""
    logger.info("Backing up existing data...")
    
    with get_fantasy_session() as session:
        # Get existing data using raw SQL
        users_result = session.execute(text("SELECT * FROM fantasy_users"))
        leagues_result = session.execute(text("SELECT * FROM fantasy_leagues"))
        teams_result = session.execute(text("SELECT * FROM fantasy_teams"))
        api_keys_result = session.execute(text("SELECT * FROM fantasy_api_keys"))
        user_leagues_result = session.execute(text("SELECT * FROM fantasy_user_leagues"))
        
        backup_data = {
            'users': [dict(row._mapping) for row in users_result],
            'leagues': [dict(row._mapping) for row in leagues_result],
            'teams': [dict(row._mapping) for row in teams_result],
            'api_keys': [dict(row._mapping) for row in api_keys_result],
            'user_leagues': [dict(row._mapping) for row in user_leagues_result]
        }
        
        logger.info(f"Backed up {len(backup_data['users'])} users, {len(backup_data['leagues'])} leagues")
        return backup_data

def drop_old_tables():
    """Drop old tables"""
    logger.info("Dropping old tables...")
    
    with get_fantasy_session() as session:
        # Drop old tables in correct order
        tables_to_drop = [
            'fantasy_player_valuations',
            'fantasy_player_metrics', 
            'fantasy_transactions',
            'fantasy_players',
            'fantasy_teams',
            'fantasy_scoring_rules',
            'fantasy_league_settings',
            'fantasy_user_leagues',
            'fantasy_api_keys',
            'fantasy_users',
            'fantasy_leagues'
        ]
        
        for table in tables_to_drop:
            try:
                session.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                logger.info(f"Dropped table: {table}")
            except Exception as e:
                logger.warning(f"Could not drop {table}: {e}")

def create_new_tables():
    """Create new tables with multi-user schema"""
    logger.info("Creating new multi-user tables...")
    
    with get_fantasy_session() as session:
        # Create all new tables
        NewBase.metadata.create_all(bind=session.bind)
        logger.info("New tables created successfully")

def migrate_users(backup_data):
    """Migrate users to new schema"""
    logger.info("Migrating users...")
    
    with get_fantasy_session() as session:
        for old_user_data in backup_data['users']:
            new_user = FantasyUser(
                id=old_user_data.get('id'),
                external_auth_id=old_user_data.get('external_auth_id'),
                email=old_user_data.get('email'),
                username=old_user_data.get('username'),
                first_name=old_user_data.get('first_name'),
                last_name=old_user_data.get('last_name'),
                display_name=old_user_data.get('display_name'),
                avatar_url=old_user_data.get('avatar_url'),
                is_active=old_user_data.get('is_active', True),
                is_verified=old_user_data.get('is_verified', False),
                email_verified=old_user_data.get('email_verified', False),
                role=old_user_data.get('role', 'user'),
                created_at=old_user_data.get('created_at', datetime.now()),
                updated_at=old_user_data.get('updated_at', datetime.now()),
                last_login=old_user_data.get('last_login')
            )
            
            session.add(new_user)
        
        session.commit()
        logger.info(f"Migrated {len(backup_data['users'])} users")

def migrate_leagues(backup_data):
    """Migrate leagues to new schema"""
    logger.info("Migrating leagues...")
    
    with get_fantasy_session() as session:
        for old_league_data in backup_data['leagues']:
            new_league = FantasyLeague(
                id=old_league_data.get('id'),
                league_id=old_league_data.get('league_id'),
                sport=old_league_data.get('sport'),
                name=old_league_data.get('name'),
                platform=old_league_data.get('platform'),
                base_url=old_league_data.get('base_url'),
                scoring_system=old_league_data.get('scoring_system'),
                draft_type=old_league_data.get('draft_type'),
                draft_rounds=old_league_data.get('draft_rounds'),
                trade_deadline=old_league_data.get('trade_deadline'),
                owner_id=1,  # Default to first user as owner
                is_public=False,
                is_active=old_league_data.get('is_active', True),
                created_at=old_league_data.get('created_at', datetime.now()),
                updated_at=old_league_data.get('updated_at', datetime.now()),
                last_sync=datetime.now()
            )
            
            session.add(new_league)
        
        session.commit()
        logger.info(f"Migrated {len(backup_data['leagues'])} leagues")

def migrate_teams(backup_data):
    """Migrate teams to new schema"""
    logger.info("Migrating teams...")
    
    with get_fantasy_session() as session:
        for old_team_data in backup_data['teams']:
            new_team = FantasyTeam(
                id=old_team_data.get('id'),
                league_id=old_team_data.get('league_id'),
                team_name=old_team_data.get('team_name'),
                owner_name=old_team_data.get('owner_name'),
                team_id=old_team_data.get('team_id'),
                owner_id=old_team_data.get('owner_id'),
                current_rank=old_team_data.get('current_rank'),
                wins=old_team_data.get('wins', 0),
                losses=old_team_data.get('losses', 0),
                ties=old_team_data.get('ties', 0),
                total_points=old_team_data.get('total_points', 0.0),
                logo_url=old_team_data.get('logo_url'),
                is_active=old_team_data.get('is_active', True),
                created_at=old_team_data.get('created_at', datetime.now()),
                updated_at=old_team_data.get('updated_at', datetime.now())
            )
            
            session.add(new_team)
        
        session.commit()
        logger.info(f"Migrated {len(backup_data['teams'])} teams")

def migrate_api_keys(backup_data):
    """Migrate API keys to new schema"""
    logger.info("Migrating API keys...")
    
    with get_fantasy_session() as session:
        for old_key_data in backup_data['api_keys']:
            new_key = FantasyAPIKey(
                id=old_key_data.get('id'),
                user_id=old_key_data.get('user_id'),
                key_name=old_key_data.get('key_name'),
                api_key=old_key_data.get('api_key'),
                api_secret=old_key_data.get('api_secret'),
                permissions=old_key_data.get('permissions'),
                last_used=old_key_data.get('last_used'),
                usage_count=old_key_data.get('usage_count', 0),
                is_active=old_key_data.get('is_active', True),
                expires_at=old_key_data.get('expires_at'),
                created_at=old_key_data.get('created_at', datetime.now())
            )
            
            session.add(new_key)
        
        session.commit()
        logger.info(f"Migrated {len(backup_data['api_keys'])} API keys")

def migrate_user_leagues(backup_data):
    """Migrate user league memberships to new schema"""
    logger.info("Migrating user league memberships...")
    
    with get_fantasy_session() as session:
        for old_membership_data in backup_data['user_leagues']:
            new_membership = FantasyUserLeague(
                id=old_membership_data.get('id'),
                user_id=old_membership_data.get('user_id'),
                league_id=old_membership_data.get('league_id'),
                role=old_membership_data.get('role', 'member'),
                can_view_rosters=old_membership_data.get('can_view_rosters', True),
                can_make_transactions=old_membership_data.get('can_make_transactions', False),
                can_trade=old_membership_data.get('can_trade', False),
                can_manage_league=old_membership_data.get('can_manage_league', False),
                can_invite_users=old_membership_data.get('can_invite_users', False),
                joined_at=old_membership_data.get('joined_at', datetime.now()),
                invited_by=old_membership_data.get('invited_by')
            )
            
            session.add(new_membership)
        
        session.commit()
        logger.info(f"Migrated {len(backup_data['user_leagues'])} user league memberships")

def main():
    """Main migration function"""
    logger.info("Starting migration to multi-user schema...")
    
    try:
        # Step 1: Backup existing data
        backup_data = backup_existing_data()
        
        # Step 2: Drop old tables
        drop_old_tables()
        
        # Step 3: Create new tables
        create_new_tables()
        
        # Step 4: Migrate data
        migrate_users(backup_data)
        migrate_leagues(backup_data)
        migrate_teams(backup_data)
        migrate_api_keys(backup_data)
        migrate_user_leagues(backup_data)
        
        logger.info("✅ Migration completed successfully!")
        logger.info("Database now supports multiple users with proper data isolation")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    main() 