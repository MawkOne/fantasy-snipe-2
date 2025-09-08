#!/usr/bin/env python3
"""
CBS Sports API Client - Optimized for production use without browser automation
"""

import json
import time
import logging
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class CBSLeague:
    """CBS Sports League Configuration"""
    league_id: str
    sport: str
    base_url: str
    session_cookies: Optional[Dict[str, str]] = None
    api_endpoints: Optional[Dict[str, str]] = None

class CBSSportsAPIClient:
    """CBS Sports API Client for production use"""
    
    def __init__(self, league_id: str, sport: str = "hockey"):
        self.league_id = league_id
        self.sport = sport
        self.base_url = f"http://{league_id}.{sport}.cbssports.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': self.base_url,
            'Origin': self.base_url
        })
        
        # Initialize session data
        self.session_cookies = {}
        self.api_endpoints = {}
        
        # Load saved session data
        self._load_session_data()
    
    def _get_session_file_path(self) -> Path:
        """Get path to session data file"""
        home_dir = Path.home()
        session_dir = home_dir / ".nhl_api"
        session_dir.mkdir(exist_ok=True)
        return session_dir / f"cbs_session_{self.league_id}.json"
    
    def _load_session_data(self):
        """Load saved session cookies and API endpoints"""
        session_file = self._get_session_file_path()
        if session_file.exists():
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                    self.session_cookies = data.get('cookies', {})
                    self.api_endpoints = data.get('endpoints', {})
                    
                    # Apply cookies to session
                    for cookie_name, cookie_value in self.session_cookies.items():
                        self.session.cookies.set(cookie_name, cookie_value)
                    
                    logger.info(f"Loaded session data for league {self.league_id}")
            except Exception as e:
                logger.warning(f"Failed to load session data: {e}")
    
    def _save_session_data(self):
        """Save current session cookies and discovered endpoints"""
        session_file = self._get_session_file_path()
        try:
            data = {
                'cookies': dict(self.session.cookies),
                'endpoints': self.api_endpoints or {},
                'updated_at': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(session_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved session data to {session_file}")
        except Exception as e:
            logger.error(f"Failed to save session data: {e}")
    
    def is_authenticated(self) -> bool:
        """Check if we have valid authentication"""
        try:
            # Try to access a protected endpoint
            response = self.session.get(f"{self.base_url}/standings", timeout=10)
            return response.status_code == 200 and "login" not in response.url.lower()
        except Exception as e:
            logger.debug(f"Authentication check failed: {e}")
            return False
    
    def get_league_info(self) -> Dict[str, Any]:
        """Get basic league information"""
        try:
            response = self.session.get(f"{self.base_url}/home", timeout=10)
            if response.status_code == 200:
                return {
                    "league_id": self.league_id,
                    "sport": self.sport,
                    "base_url": self.base_url,
                    "authenticated": self.is_authenticated(),
                    "last_check": time.strftime("%Y-%m-%d %H:%M:%S")
                }
        except Exception as e:
            logger.error(f"Error getting league info: {e}")
        
        return {}
    
    def get_standings(self) -> Dict[str, Any]:
        """Get league standings via API"""
        try:
            response = self.session.get(f"{self.base_url}/standings", timeout=10)
            if response.status_code == 200:
                # Try to extract standings from HTML or JSON response
                return self._parse_standings_response(response)
        except Exception as e:
            logger.error(f"Error getting standings: {e}")
        
        return {"teams": [], "error": "Failed to fetch standings"}
    
    def _parse_standings_response(self, response) -> Dict[str, Any]:
        """Parse standings from response"""
        try:
            # Check if response is JSON
            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
                return self._extract_standings_from_json(data)
            else:
                # Parse HTML response
                return self._extract_standings_from_html(response.text)
        except Exception as e:
            logger.error(f"Error parsing standings response: {e}")
            return {"teams": [], "error": f"Parse error: {e}"}
    
    def _extract_standings_from_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract standings from JSON response"""
        teams = []
        
        # Common JSON structures for standings
        if 'teams' in data:
            for team in data['teams']:
                teams.append({
                    "rank": team.get('name', team.get('team_name', '')),
                    "record": team.get('record', team.get('wins', '')),
                    "points": team.get('points', team.get('total_points', ''))
                })
        elif 'standings' in data:
            for team in data['standings']:
                teams.append({
                    "rank": team.get('name', team.get('team_name', '')),
                    "record": team.get('record', team.get('wins', '')),
                    "points": team.get('points', team.get('total_points', ''))
                })
        
        return {"teams": teams}
    
    def _extract_standings_from_html(self, html_content: str) -> Dict[str, Any]:
        """Extract standings from HTML response"""
        # This would need to be implemented based on CBS Sports HTML structure
        # For now, return empty teams list
        return {"teams": [], "note": "HTML parsing not implemented"}
    
    def get_waiver_status(self) -> Dict[str, Any]:
        """Get waiver status using discovered API endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/league/transactions/waiver-status", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Error getting waiver status: {e}")
        
        return {}
    
    def get_recent_transactions(self) -> List[Dict[str, Any]]:
        """Get recent league transactions"""
        try:
            # Try common transaction endpoints
            endpoints = [
                "/league/transactions",
                "/transactions",
                "/league/transactions/recent"
            ]
            
            for endpoint in endpoints:
                try:
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        return self._parse_transactions(data)
                except Exception as e:
                    logger.debug(f"Endpoint {endpoint} failed: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error getting transactions: {e}")
        
        return []
    
    def _parse_transactions(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse transaction data"""
        transactions = []
        
        # Common transaction structures
        if 'transactions' in data:
            for tx in data['transactions']:
                transactions.append({
                    "type": tx.get('type', ''),
                    "player": tx.get('player_name', ''),
                    "team": tx.get('team_name', ''),
                    "date": tx.get('date', ''),
                    "description": tx.get('description', '')
                })
        
        return transactions
    
    def update_session_from_browser(self, cookies: Dict[str, str], endpoints: Dict[str, str] = None):
        """Update session with data from browser automation"""
        # Apply cookies
        for cookie_name, cookie_value in cookies.items():
            self.session.cookies.set(cookie_name, cookie_value)
        
        # Store discovered endpoints
        if endpoints:
            self.api_endpoints = endpoints
        
        # Save updated session data
        self._save_session_data()
        
        logger.info("Session updated from browser data")
    
    def export_league_data(self) -> Dict[str, Any]:
        """Export all available league data"""
        data = {
            "league_id": self.league_id,
            "sport": self.sport,
            "base_url": self.base_url,
            "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "authenticated": self.is_authenticated(),
            "league_info": self.get_league_info(),
            "standings": self.get_standings(),
            "waiver_status": self.get_waiver_status(),
            "recent_transactions": self.get_recent_transactions(),
            "api_endpoints": self.api_endpoints or {},
            "session_info": {
                "cookies_count": len(self.session.cookies),
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        
        return data

def main():
    """Main function for testing the API client"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CBS Sports API Client')
    parser.add_argument('--league-id', required=True, help='CBS Sports League ID')
    parser.add_argument('--sport', default='hockey', help='Sport (default: hockey)')
    parser.add_argument('--output', help='Output file for exported data')
    parser.add_argument('--check-auth', action='store_true', help='Check authentication status')
    
    args = parser.parse_args()
    
    # Create client
    client = CBSSportsAPIClient(args.league_id, args.sport)
    
    if args.check_auth:
        print(f"Authentication Status: {client.is_authenticated()}")
        return
    
    # Export data
    data = client.export_league_data()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Data exported to: {args.output}")
    else:
        print(json.dumps(data, indent=2))
    
    # Print summary
    print(f"\nCBS Sports API Export Summary:")
    print(f"League ID: {args.league_id}")
    print(f"Sport: {args.sport}")
    print(f"Authenticated: {data.get('authenticated', False)}")
    print(f"Teams Found: {len(data.get('standings', {}).get('teams', []))}")
    print(f"Transactions Found: {len(data.get('recent_transactions', []))}")

if __name__ == "__main__":
    main() 