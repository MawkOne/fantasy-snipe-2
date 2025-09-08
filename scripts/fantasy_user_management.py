#!/usr/bin/env python3
"""
Fantasy User Management System
Handles user accounts, authentication, API keys, and league permissions
"""

import os
import sys
import json
import logging
import argparse
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.fantasy_connection import get_fantasy_session
from src.database.fantasy_models import (
    FantasyUser, FantasyAPIKey, FantasyUserLeague, 
    FantasyLeague, FantasyTeam
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class UserRegistrationData:
    """User registration data structure"""
    email: str
    username: str
    first_name: str
    last_name: str
    display_name: Optional[str] = None
    external_auth_id: Optional[str] = None
    role: str = 'user'

class FantasyUserManager:
    """Manages fantasy sports user accounts and permissions"""
    
    def __init__(self):
        self.session = None
    
    def __enter__(self):
        self.session_context = get_fantasy_session()
        self.session = self.session_context.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'session_context'):
            self.session_context.__exit__(exc_type, exc_val, exc_tb)
    
    def create_user(self, user_data: UserRegistrationData) -> FantasyUser:
        """Create a new fantasy user account"""
        try:
            # Check if user already exists
            existing_user = self.session.query(FantasyUser).filter(
                FantasyUser.email == user_data.email
            ).first()
            
            if existing_user:
                logger.warning(f"User with email {user_data.email} already exists")
                return existing_user
            
            # Create new user
            user = FantasyUser(
                email=user_data.email,
                username=user_data.username,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                display_name=user_data.display_name or f"{user_data.first_name} {user_data.last_name}",
                external_auth_id=user_data.external_auth_id,
                role=user_data.role,
                is_active=True,
                is_verified=False,
                email_verified=False,
                created_at=datetime.now()
            )
            
            self.session.add(user)
            self.session.flush()  # Get the ID
            
            logger.info(f"Created user: {user.email} (ID: {user.id})")
            return user
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            self.session.rollback()
            raise
    
    def get_user_by_email(self, email: str) -> Optional[FantasyUser]:
        """Get user by email address"""
        try:
            return self.session.query(FantasyUser).filter(
                FantasyUser.email == email
            ).first()
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[FantasyUser]:
        """Get user by ID"""
        try:
            return self.session.query(FantasyUser).filter(
                FantasyUser.id == user_id
            ).first()
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    def update_user_profile(self, user_id: int, profile_data: Dict[str, Any]) -> bool:
        """Update user profile information"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return False
            
            # Update allowed fields
            allowed_fields = ['first_name', 'last_name', 'display_name', 'avatar_url']
            for field, value in profile_data.items():
                if field in allowed_fields and hasattr(user, field):
                    setattr(user, field, value)
            
            user.updated_at = datetime.now()
            self.session.commit()
            
            logger.info(f"Updated profile for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            self.session.rollback()
            return False
    
    def create_api_key(self, user_id: int, key_name: str, permissions: List[str] = None) -> Optional[FantasyAPIKey]:
        """Create a new API key for a user"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return None
            
            # Generate API key
            api_key = secrets.token_urlsafe(32)
            api_secret = secrets.token_urlsafe(32)
            
            # Create API key record
            key_record = FantasyAPIKey(
                user_id=user_id,
                key_name=key_name,
                api_key=api_key,
                api_secret=api_secret,
                permissions=permissions or ['read:leagues', 'read:teams'],
                is_active=True,
                created_at=datetime.now()
            )
            
            self.session.add(key_record)
            self.session.flush()
            
            logger.info(f"Created API key '{key_name}' for user {user_id}")
            return key_record
            
        except Exception as e:
            logger.error(f"Error creating API key: {e}")
            self.session.rollback()
            return None
    
    def validate_api_key(self, api_key: str) -> Optional[FantasyAPIKey]:
        """Validate an API key and return the key record"""
        try:
            key_record = self.session.query(FantasyAPIKey).filter(
                FantasyAPIKey.api_key == api_key,
                FantasyAPIKey.is_active == True
            ).first()
            
            if key_record:
                # Update usage stats
                key_record.last_used = datetime.now()
                key_record.usage_count += 1
                self.session.commit()
                
                return key_record
            
            return None
            
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return None
    
    def revoke_api_key(self, user_id: int, key_id: int) -> bool:
        """Revoke an API key"""
        try:
            key_record = self.session.query(FantasyAPIKey).filter(
                FantasyAPIKey.id == key_id,
                FantasyAPIKey.user_id == user_id
            ).first()
            
            if key_record:
                key_record.is_active = False
                self.session.commit()
                logger.info(f"Revoked API key {key_id} for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error revoking API key: {e}")
            self.session.rollback()
            return False
    
    def add_user_to_league(self, user_id: int, league_id: int, role: str = 'owner', 
                          permissions: Dict[str, bool] = None) -> bool:
        """Add a user to a league with specific permissions"""
        try:
            # Check if user already in league
            existing = self.session.query(FantasyUserLeague).filter(
                FantasyUserLeague.user_id == user_id,
                FantasyUserLeague.league_id == league_id
            ).first()
            
            if existing:
                logger.warning(f"User {user_id} already in league {league_id}")
                return True
            
            # Set default permissions based on role
            if permissions is None:
                if role == 'commissioner':
                    permissions = {
                        'can_view_rosters': True,
                        'can_make_transactions': True,
                        'can_trade': True,
                        'can_manage_league': True
                    }
                elif role == 'owner':
                    permissions = {
                        'can_view_rosters': True,
                        'can_make_transactions': True,
                        'can_trade': True,
                        'can_manage_league': False
                    }
                else:  # viewer
                    permissions = {
                        'can_view_rosters': True,
                        'can_make_transactions': False,
                        'can_trade': False,
                        'can_manage_league': False
                    }
            
            # Create league membership
            membership = FantasyUserLeague(
                user_id=user_id,
                league_id=league_id,
                role=role,
                can_view_rosters=permissions.get('can_view_rosters', True),
                can_make_transactions=permissions.get('can_make_transactions', False),
                can_trade=permissions.get('can_trade', False),
                can_manage_league=permissions.get('can_manage_league', False),
                joined_at=datetime.now()
            )
            
            self.session.add(membership)
            self.session.commit()
            
            logger.info(f"Added user {user_id} to league {league_id} as {role}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding user to league: {e}")
            self.session.rollback()
            return False
    
    def get_user_leagues(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all leagues a user is a member of"""
        try:
            memberships = self.session.query(FantasyUserLeague).filter(
                FantasyUserLeague.user_id == user_id
            ).all()
            
            leagues = []
            for membership in memberships:
                league = self.session.query(FantasyLeague).filter(
                    FantasyLeague.id == membership.league_id
                ).first()
                
                if league:
                    leagues.append({
                        'league_id': league.id,
                        'league_name': league.name,
                        'league_code': league.league_id,
                        'role': membership.role,
                        'permissions': {
                            'can_view_rosters': membership.can_view_rosters,
                            'can_make_transactions': membership.can_make_transactions,
                            'can_trade': membership.can_trade,
                            'can_manage_league': membership.can_manage_league
                        },
                        'joined_at': membership.joined_at.isoformat()
                    })
            
            return leagues
            
        except Exception as e:
            logger.error(f"Error getting user leagues: {e}")
            return []
    
    def get_league_members(self, league_id: int) -> List[Dict[str, Any]]:
        """Get all members of a league"""
        try:
            memberships = self.session.query(FantasyUserLeague).filter(
                FantasyUserLeague.league_id == league_id
            ).all()
            
            members = []
            for membership in memberships:
                user = self.get_user_by_id(membership.user_id)
                if user:
                    members.append({
                        'user_id': user.id,
                        'email': user.email,
                        'username': user.username,
                        'display_name': user.display_name,
                        'role': membership.role,
                        'permissions': {
                            'can_view_rosters': membership.can_view_rosters,
                            'can_make_transactions': membership.can_make_transactions,
                            'can_trade': membership.can_trade,
                            'can_manage_league': membership.can_manage_league
                        },
                        'joined_at': membership.joined_at.isoformat()
                    })
            
            return members
            
        except Exception as e:
            logger.error(f"Error getting league members: {e}")
            return []
    
    def update_league_permissions(self, user_id: int, league_id: int, 
                                permissions: Dict[str, bool]) -> bool:
        """Update a user's permissions in a league"""
        try:
            membership = self.session.query(FantasyUserLeague).filter(
                FantasyUserLeague.user_id == user_id,
                FantasyUserLeague.league_id == league_id
            ).first()
            
            if not membership:
                logger.error(f"User {user_id} not found in league {league_id}")
                return False
            
            # Update permissions
            membership.can_view_rosters = permissions.get('can_view_rosters', membership.can_view_rosters)
            membership.can_make_transactions = permissions.get('can_make_transactions', membership.can_make_transactions)
            membership.can_trade = permissions.get('can_trade', membership.can_trade)
            membership.can_manage_league = permissions.get('can_manage_league', membership.can_manage_league)
            
            self.session.commit()
            logger.info(f"Updated permissions for user {user_id} in league {league_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating league permissions: {e}")
            self.session.rollback()
            return False
    
    def remove_user_from_league(self, user_id: int, league_id: int) -> bool:
        """Remove a user from a league"""
        try:
            membership = self.session.query(FantasyUserLeague).filter(
                FantasyUserLeague.user_id == user_id,
                FantasyUserLeague.league_id == league_id
            ).first()
            
            if membership:
                self.session.delete(membership)
                self.session.commit()
                logger.info(f"Removed user {user_id} from league {league_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error removing user from league: {e}")
            self.session.rollback()
            return False
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return {}
            
            # Get league memberships
            league_count = self.session.query(FantasyUserLeague).filter(
                FantasyUserLeague.user_id == user_id
            ).count()
            
            # Get API keys
            api_key_count = self.session.query(FantasyAPIKey).filter(
                FantasyAPIKey.user_id == user_id,
                FantasyAPIKey.is_active == True
            ).count()
            
            # Get owned teams
            owned_teams = self.session.query(FantasyTeam).filter(
                FantasyTeam.owner_id == user_id
            ).all()
            
            return {
                'user_id': user.id,
                'email': user.email,
                'username': user.username,
                'display_name': user.display_name,
                'role': user.role,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'stats': {
                    'league_memberships': league_count,
                    'active_api_keys': api_key_count,
                    'owned_teams': len(owned_teams)
                },
                'owned_teams': [
                    {
                        'team_id': team.id,
                        'team_name': team.team_name,
                        'league_id': team.league_id
                    } for team in owned_teams
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {}

def create_sample_users():
    """Create sample users for testing"""
    sample_users = [
        UserRegistrationData(
            email="commissioner@fantasy.com",
            username="commissioner",
            first_name="League",
            last_name="Commissioner",
            display_name="League Commissioner",
            role="admin"
        ),
        UserRegistrationData(
            email="owner1@fantasy.com",
            username="owner1",
            first_name="John",
            last_name="Owner",
            display_name="John Owner",
            role="user"
        ),
        UserRegistrationData(
            email="owner2@fantasy.com",
            username="owner2",
            first_name="Jane",
            last_name="Manager",
            display_name="Jane Manager",
            role="user"
        )
    ]
    
    with FantasyUserManager() as manager:
        created_users = []
        for user_data in sample_users:
            user = manager.create_user(user_data)
            if user:
                created_users.append(user)
        
        logger.info(f"Created {len(created_users)} sample users")
        return created_users

def main():
    """Main function for user management CLI"""
    parser = argparse.ArgumentParser(description='Fantasy User Management System')
    parser.add_argument('--create-user', nargs=5, metavar=('EMAIL', 'USERNAME', 'FIRST', 'LAST', 'ROLE'),
                       help='Create a new user')
    parser.add_argument('--create-api-key', nargs=2, metavar=('USER_ID', 'KEY_NAME'),
                       help='Create API key for user')
    parser.add_argument('--add-to-league', nargs=3, metavar=('USER_ID', 'LEAGUE_ID', 'ROLE'),
                       help='Add user to league')
    parser.add_argument('--list-users', action='store_true', help='List all users')
    parser.add_argument('--user-stats', type=int, metavar='USER_ID', help='Get user statistics')
    parser.add_argument('--create-samples', action='store_true', help='Create sample users')
    
    args = parser.parse_args()
    
    try:
        with FantasyUserManager() as manager:
            if args.create_user:
                email, username, first, last, role = args.create_user
                user_data = UserRegistrationData(
                    email=email,
                    username=username,
                    first_name=first,
                    last_name=last,
                    role=role
                )
                user = manager.create_user(user_data)
                if user:
                    print(f"✅ Created user: {user.email} (ID: {user.id})")
            
            elif args.create_api_key:
                user_id, key_name = int(args.create_api_key[0]), args.create_api_key[1]
                key = manager.create_api_key(user_id, key_name)
                if key:
                    print(f"✅ Created API key: {key.api_key}")
                    print(f"   Secret: {key.api_secret}")
            
            elif args.add_to_league:
                user_id, league_id, role = int(args.add_to_league[0]), int(args.add_to_league[1]), args.add_to_league[2]
                success = manager.add_user_to_league(user_id, league_id, role)
                if success:
                    print(f"✅ Added user {user_id} to league {league_id} as {role}")
            
            elif args.list_users:
                # This would need to be implemented - for now just show sample
                print("📋 User listing not yet implemented")
            
            elif args.user_stats:
                stats = manager.get_user_stats(args.user_stats)
                if stats:
                    print(json.dumps(stats, indent=2))
                else:
                    print(f"❌ User {args.user_stats} not found")
            
            elif args.create_samples:
                users = create_sample_users()
                print(f"✅ Created {len(users)} sample users")
            
            else:
                parser.print_help()
    
    except Exception as e:
        logger.error(f"Error in user management: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 