#!/usr/bin/env python3
"""
Populate Fantasy Database with CBS Sports Data
Integrates CBS Sports league data with NHL metrics database
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.fantasy_connection import init_fantasy_database, get_fantasy_session
from src.database.fantasy_models_v2 import (
    FantasyLeague, FantasyLeagueSettings, FantasyScoringRule,
    FantasyTeam, FantasyPlayer, FantasyTransaction, FantasyPlayerMetrics
)
# NHL database connection (optional for now)
try:
    from src.database.connection import connect_with_connector
    from src.database.models import Player
    NHL_DB_AVAILABLE = True
except ImportError:
    NHL_DB_AVAILABLE = False
    print("Warning: NHL database not available - player matching will be limited")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FantasyDataPopulator:
    """Populates fantasy database with CBS Sports data"""
    
    def __init__(self):
        self.fantasy_session = None
        self.nhl_session = None
    
    def load_cbs_data(self, cbs_data_file: str) -> Dict[str, Any]:
        """Load CBS Sports data from JSON file"""
        try:
            with open(cbs_data_file, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded CBS data from {cbs_data_file}")
            return data
        except Exception as e:
            logger.error(f"Failed to load CBS data: {e}")
            raise
    
    def parse_scoring_rules(self, raw_rules_text: List[str]) -> List[Dict[str, Any]]:
        """Parse scoring rules from raw rules text"""
        scoring_rules = []
        
        # Define scoring rule patterns
        rule_patterns = {
            'G': {'description': 'Goals', 'points': 3.0},
            'A': {'description': 'Assists', 'points': 2.0},
            'DG': {'description': 'Defenseman Goals', 'points': 2.0},
            'SHG': {'description': 'Short Handed Goals', 'points': 2.0},
            'W': {'description': 'Wins', 'points': 2.0},
            '+/-': {'description': 'Plus Minus', 'points': 0.25},
            'GA': {'description': 'Goals Against', 'points': -1.25},
            'S': {'description': 'Saves', 'points': 0.2},
            'PIM': {'description': 'Penalty Minutes', 'points': 0.0}
        }
        
        for rule_text in raw_rules_text:
            for stat_code, rule_info in rule_patterns.items():
                if stat_code in rule_text:
                    scoring_rules.append({
                        'stat_name': stat_code,
                        'stat_description': rule_info['description'],
                        'points': rule_info['points']
                    })
        
        return scoring_rules
    
    def parse_league_settings(self, raw_rules_text: List[str]) -> Dict[str, Any]:
        """Parse league settings from raw rules text"""
        settings = {
            'roster_positions': {},
            'waiver_period_days': 1,
            'waiver_run_days': 'Sunday, Friday, Saturday',
            'trade_approval_required': True,
            'playoff_start_period': 23,
            'playoff_weeks': 4,
            'playoff_tiebreaker': 'Goals (G)',
            'raw_settings_json': {'raw_rules': raw_rules_text}
        }
        
        for rule_text in raw_rules_text:
            if 'Draft Rounds' in rule_text:
                try:
                    rounds = int(rule_text.split()[-1].replace('.', ''))
                    settings['draft_rounds'] = rounds
                except:
                    pass
            
            if 'Trade Deadline' in rule_text:
                try:
                    # Parse date from "11:59 pm et 3/1/25"
                    date_part = rule_text.split('3/1/25')[0].split()[-1]
                    settings['trade_deadline'] = datetime(2025, 3, 1, 23, 59)
                except:
                    pass
        
        return settings
    
    def find_nhl_player_id(self, player_name: str, nhl_team: str = None) -> int:
        """Find NHL player ID by name and team"""
        try:
            query = self.nhl_session.query(Player).filter(
                Player.full_name.ilike(f"%{player_name}%")
            )
            
            if nhl_team:
                query = query.filter(Player.team_abbreviation == nhl_team)
            
            player = query.first()
            return player.id if player else None
            
        except Exception as e:
            logger.debug(f"Error finding NHL player {player_name}: {e}")
            return None
    
    def populate_league(self, cbs_data: Dict[str, Any], owner_id: int) -> FantasyLeague:
        """Populate fantasy league data"""
        try:
            # Check if league already exists
            existing_league = self.fantasy_session.query(FantasyLeague).filter(
                FantasyLeague.league_id == cbs_data['league_id']
            ).first()
            
            if existing_league:
                logger.info(f"League {cbs_data['league_id']} already exists, updating...")
                league = existing_league
            else:
                league = FantasyLeague()
            
            # Update league data
            league.league_id = cbs_data['league_id']
            league.sport = cbs_data['sport']
            league.name = "Ultimate Hardcore Hockey Pool"  # From CBS data
            league.platform = 'cbs'
            league.base_url = cbs_data['base_url']
            league.scoring_system = 'head-to-head'
            league.draft_type = 'snake'
            league.draft_rounds = 15
            league.owner_id = owner_id  # Set the owner
            league.is_public = False
            league.is_active = True
            
            # Parse trade deadline
            if 'league_settings' in cbs_data and 'raw_rules_text' in cbs_data['league_settings']:
                settings = self.parse_league_settings(cbs_data['league_settings']['raw_rules_text'])
                league.trade_deadline = settings.get('trade_deadline')
            
            self.fantasy_session.add(league)
            self.fantasy_session.flush()  # Get the ID
            
            logger.info(f"League {league.league_id} populated/updated")
            return league
            
        except Exception as e:
            logger.error(f"Error populating league: {e}")
            raise
    
    def populate_league_settings(self, league: FantasyLeague, cbs_data: Dict[str, Any]):
        """Populate league settings"""
        try:
            if 'league_settings' not in cbs_data:
                return
            
            # Check if settings already exist
            existing_settings = self.fantasy_session.query(FantasyLeagueSettings).filter(
                FantasyLeagueSettings.league_id == league.id
            ).first()
            
            if existing_settings:
                settings = existing_settings
            else:
                settings = FantasyLeagueSettings()
                settings.league_id = league.id
            
            # Parse settings from raw rules
            if 'raw_rules_text' in cbs_data['league_settings']:
                parsed_settings = self.parse_league_settings(cbs_data['league_settings']['raw_rules_text'])
                
                settings.waiver_period_days = parsed_settings['waiver_period_days']
                settings.waiver_run_days = parsed_settings['waiver_run_days']
                settings.trade_approval_required = parsed_settings['trade_approval_required']
                settings.playoff_start_period = parsed_settings['playoff_start_period']
                settings.playoff_weeks = parsed_settings['playoff_weeks']
                settings.playoff_tiebreaker = parsed_settings['playoff_tiebreaker']
                settings.raw_settings_json = parsed_settings['raw_settings_json']
            
            self.fantasy_session.add(settings)
            logger.info(f"League settings populated for {league.league_id}")
            
        except Exception as e:
            logger.error(f"Error populating league settings: {e}")
    
    def populate_scoring_rules(self, league: FantasyLeague, cbs_data: Dict[str, Any]):
        """Populate scoring rules"""
        try:
            if 'league_settings' not in cbs_data or 'raw_rules_text' not in cbs_data['league_settings']:
                return
            
            # Clear existing rules
            self.fantasy_session.query(FantasyScoringRule).filter(
                FantasyScoringRule.league_id == league.id
            ).delete()
            
            # Parse and add new rules
            raw_rules = cbs_data['league_settings']['raw_rules_text']
            scoring_rules = self.parse_scoring_rules(raw_rules)
            
            for rule_data in scoring_rules:
                rule = FantasyScoringRule()
                rule.league_id = league.id
                rule.stat_name = rule_data['stat_name']
                rule.stat_description = rule_data['stat_description']
                rule.points = rule_data['points']
                
                self.fantasy_session.add(rule)
            
            logger.info(f"Added {len(scoring_rules)} scoring rules for {league.league_id}")
            
        except Exception as e:
            logger.error(f"Error populating scoring rules: {e}")
    
    def populate_teams(self, league: FantasyLeague, cbs_data: Dict[str, Any]) -> List[FantasyTeam]:
        """Populate fantasy teams"""
        teams = []
        
        try:
            if 'standings' not in cbs_data or 'teams' not in cbs_data['standings']:
                logger.warning("No standings data found")
                return teams
            
            for team_data in cbs_data['standings']['teams']:
                team_name = team_data.get('rank', '')  # rank field contains team name
                if not team_name:
                    continue
                
                # Check if team already exists
                existing_team = self.fantasy_session.query(FantasyTeam).filter(
                    FantasyTeam.league_id == league.id,
                    FantasyTeam.team_name == team_name
                ).first()
                
                if existing_team:
                    team = existing_team
                    logger.debug(f"Team {team_name} already exists, updating...")
                else:
                    team = FantasyTeam()
                    team.league_id = league.id
                    team.team_name = team_name
                
                # Update team data
                team.current_rank = int(team_data.get('team', 0))
                team.wins = int(team_data.get('record', '0').split('-')[0]) if '-' in team_data.get('record', '0') else 0
                team.losses = int(team_data.get('record', '0').split('-')[1]) if '-' in team_data.get('record', '0') else 0
                
                self.fantasy_session.add(team)
                teams.append(team)
            
            logger.info(f"Populated {len(teams)} teams for {league.league_id}")
            return teams
            
        except Exception as e:
            logger.error(f"Error populating teams: {e}")
            return teams
    
    def populate_players(self, teams: List[FantasyTeam], cbs_data: Dict[str, Any]):
        """Populate fantasy players (placeholder for now)"""
        try:
            # This will be implemented when we successfully extract player rosters
            # For now, this is a placeholder
            logger.info("Player roster population not yet implemented - requires successful roster extraction")
            
        except Exception as e:
            logger.error(f"Error populating players: {e}")
    
    def populate_all(self, cbs_data_file: str, user_email: str = "default@example.com"):
        """Populate all fantasy database tables"""
        try:
            # Initialize fantasy session using context manager
            with get_fantasy_session() as self.fantasy_session:
                # Initialize NHL session if available
                if NHL_DB_AVAILABLE:
                    nhl_engine = connect_with_connector()
                    from sqlalchemy.orm import sessionmaker
                    NHLSession = sessionmaker(bind=nhl_engine)
                    self.nhl_session = NHLSession()
                else:
                    self.nhl_session = None
                
                # Create or get user
                user = self.create_or_get_user(user_email)
                
                # Load CBS data
                cbs_data = self.load_cbs_data(cbs_data_file)
                
                # Populate league (owned by the user)
                league = self.populate_league(cbs_data, user.id)
                
                # Populate league settings
                self.populate_league_settings(league, cbs_data)
                
                # Populate scoring rules
                self.populate_scoring_rules(league, cbs_data)
                
                # Populate teams
                teams = self.populate_teams(league, cbs_data)
                
                # Populate players (placeholder)
                self.populate_players(teams, cbs_data)
                
                logger.info("Fantasy database population completed successfully")
                
                # Close NHL session if it exists
                if self.nhl_session:
                    self.nhl_session.close()
            
        except Exception as e:
            logger.error(f"Error populating fantasy database: {e}")
            raise
    
    def create_or_get_user(self, email: str):
        """Create or get a user for the fantasy data"""
        from src.database.fantasy_models_v2 import FantasyUser
        
        # Check if user exists
        user = self.fantasy_session.query(FantasyUser).filter(FantasyUser.email == email).first()
        
        if not user:
            # Create new user
            user = FantasyUser(
                email=email,
                username=email.split('@')[0],
                display_name=email.split('@')[0].title(),
                is_active=True,
                role='user'
            )
            self.fantasy_session.add(user)
            self.fantasy_session.commit()
            logger.info(f"Created new user: {email}")
        else:
            logger.info(f"Using existing user: {email}")
        
        return user

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Populate Fantasy Database with CBS Sports Data')
    parser.add_argument('--cbs-data', required=False, help='Path to CBS Sports JSON data file')
    parser.add_argument('--init-db', action='store_true', help='Initialize fantasy database tables')
    parser.add_argument('--test-connection', action='store_true', help='Test database connections')
    
    args = parser.parse_args()
    
    try:
        # Initialize fantasy database if requested
        if args.init_db:
            logger.info("Initializing fantasy database...")
            init_fantasy_database()
        
        # Test connections if requested
        if args.test_connection:
            logger.info("Testing database connections...")
            from src.database.fantasy_connection import fantasy_db
            
            fantasy_ok = fantasy_db.test_connection()
            nhl_ok = NHL_DB_AVAILABLE
            
            print(f"Fantasy DB: {'✅' if fantasy_ok else '❌'}")
            print(f"NHL DB: {'✅' if nhl_ok else '❌'}")
            
            if not fantasy_ok:
                print("❌ Fantasy database connection failed")
                return
        
        # Populate database if CBS data provided
        if args.cbs_data:
            populator = FantasyDataPopulator()
            populator.populate_all(args.cbs_data)
        elif not args.test_connection and not args.init_db:
            print("❌ Please provide --cbs-data or use --test-connection or --init-db")
            sys.exit(1)
        
        print("✅ Fantasy database population completed successfully!")
        
    except Exception as e:
        logger.error(f"Failed to populate fantasy database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 