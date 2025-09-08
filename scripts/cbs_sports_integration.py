#!/usr/bin/env python3
"""
CBS Sports Fantasy Hockey Integration
Based on FantasyPros integration data structure discovered.

This script can extract league data from CBS Sports fantasy hockey leagues
using the API structure revealed by FantasyPros integration.
"""

import os
import sys
import json
import time
import requests
import argparse
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("BeautifulSoup not found. Install with: pip install beautifulsoup4")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class CBSTeam:
    """CBS Sports team information"""
    id: str
    name: str
    logo: Optional[str] = None
    players: List[int] = None
    
    def __post_init__(self):
        if self.players is None:
            self.players = []

@dataclass
class CBSLeague:
    """CBS Sports league information"""
    league_id: str
    name: str
    sport: str = "nhl"
    teams: List[CBSTeam] = None
    team_count: int = 0
    has_drafted: bool = False
    
    def __post_init__(self):
        if self.teams is None:
            self.teams = []

class CBSSportsIntegration:
    """CBS Sports fantasy hockey integration"""
    
    def __init__(self, league_id: str, sport: str = "hockey"):
        self.league_id = league_id
        self.sport = sport
        self.base_url = f"https://{league_id}.{sport}.cbssports.com"
        self.session = requests.Session()
        
        # Configure session headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Referer': self.base_url,
        })
    
    def get_league_info(self) -> Optional[CBSLeague]:
        """Get basic league information"""
        try:
            # Try to get league info from teams page
            url = f"{self.base_url}/teams"
            logger.info(f"Fetching league info from: {url}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse the response (might be HTML or JSON)
            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
                return self._parse_league_json(data)
            else:
                # Parse HTML for league info
                return self._parse_league_html(response.text)
                
        except requests.RequestException as e:
            logger.error(f"Error fetching league info: {e}")
            return None
    
    def get_teams(self) -> List[CBSTeam]:
        """Get all teams in the league"""
        try:
            # Try API endpoint first
            url = f"{self.base_url}/api/teams"
            logger.info(f"Fetching teams from: {url}")
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return self._parse_teams_json(data)
            
            # Fallback to HTML parsing
            url = f"{self.base_url}/teams"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            return self._parse_teams_html(response.text)
            
        except requests.RequestException as e:
            logger.error(f"Error fetching teams: {e}")
            return []
    
    def get_standings(self) -> Dict[str, Any]:
        """Get league standings"""
        try:
            url = f"{self.base_url}/standings"
            logger.info(f"Fetching standings from: {url}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            if response.headers.get('content-type', '').startswith('application/json'):
                return response.json()
            else:
                return self._parse_standings_html(response.text)
                
        except requests.RequestException as e:
            logger.error(f"Error fetching standings: {e}")
            return {}
    
    def get_schedule(self) -> Dict[str, Any]:
        """Get league schedule"""
        try:
            url = f"{self.base_url}/schedule"
            logger.info(f"Fetching schedule from: {url}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            if response.headers.get('content-type', '').startswith('application/json'):
                return response.json()
            else:
                return self._parse_schedule_html(response.text)
                
        except requests.RequestException as e:
            logger.error(f"Error fetching schedule: {e}")
            return {}
    
    def get_team_roster(self, team_id: str) -> Dict[str, Any]:
        """Get specific team roster"""
        try:
            url = f"{self.base_url}/teams/{team_id}/roster"
            logger.info(f"Fetching roster for team {team_id} from: {url}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            if response.headers.get('content-type', '').startswith('application/json'):
                return response.json()
            else:
                return self._parse_roster_html(response.text)
                
        except requests.RequestException as e:
            logger.error(f"Error fetching roster for team {team_id}: {e}")
            return {}
    
    def get_player_stats(self, player_id: int) -> Dict[str, Any]:
        """Get player statistics"""
        try:
            url = f"{self.base_url}/players/{player_id}/stats"
            logger.info(f"Fetching stats for player {player_id} from: {url}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            if response.headers.get('content-type', '').startswith('application/json'):
                return response.json()
            else:
                return self._parse_player_stats_html(response.text)
                
        except requests.RequestException as e:
            logger.error(f"Error fetching stats for player {player_id}: {e}")
            return {}
    
    def _parse_league_json(self, data: Dict[str, Any]) -> CBSLeague:
        """Parse league data from JSON response"""
        league = CBSLeague(
            league_id=self.league_id,
            name=data.get('name', 'Unknown League'),
            sport=self.sport,
            has_drafted=data.get('hasDrafted', False)
        )
        
        # Parse teams if available
        teams_data = data.get('teams', [])
        for team_data in teams_data:
            team = CBSTeam(
                id=team_data.get('id', ''),
                name=team_data.get('name', ''),
                logo=team_data.get('logo'),
                players=team_data.get('players', [])
            )
            league.teams.append(team)
        
        league.team_count = len(league.teams)
        return league
    
    def _parse_league_html(self, html: str) -> CBSLeague:
        """Parse league data from HTML response"""
        soup = BeautifulSoup(html, 'html.parser')
        
        league = CBSLeague(
            league_id=self.league_id,
            name=f"{self.league_id} League",
            sport=self.sport
        )
        
        # Try to extract league name from title or headings
        title = soup.find('title')
        if title:
            league.name = title.get_text().strip()
        
        # Look for league name in headings
        h1 = soup.find('h1')
        if h1:
            league.name = h1.get_text().strip()
        
        # Extract basic info from HTML
        if 'teams' in html.lower():
            # Try to extract team count
            team_matches = re.findall(r'team', html, re.IGNORECASE)
            league.team_count = len(team_matches) // 2  # Rough estimate
        
        return league
    
    def _parse_teams_json(self, data: Dict[str, Any]) -> List[CBSTeam]:
        """Parse teams data from JSON response"""
        teams = []
        teams_data = data.get('teams', [])
        
        for team_data in teams_data:
            team = CBSTeam(
                id=team_data.get('id', ''),
                name=team_data.get('name', ''),
                logo=team_data.get('logo'),
                players=team_data.get('players', [])
            )
            teams.append(team)
        
        return teams
    
    def _parse_teams_html(self, html: str) -> List[CBSTeam]:
        """Parse teams data from HTML response"""
        soup = BeautifulSoup(html, 'html.parser')
        teams = []
        
        # Look for team elements - common patterns in fantasy sports sites
        team_selectors = [
            '.team', '.team-name', '.team-info', '.roster-team',
            '[data-team-id]', '.fantasy-team', '.league-team'
        ]
        
        for selector in team_selectors:
            team_elements = soup.select(selector)
            if team_elements:
                logger.info(f"Found {len(team_elements)} teams using selector: {selector}")
                break
        
        # If no specific selectors work, look for common patterns
        if not team_elements:
            # Look for elements containing team-like text
            team_elements = soup.find_all(['div', 'span', 'a'], class_=re.compile(r'team|roster', re.I))
        
        for element in team_elements:
            # Extract team ID
            team_id = element.get('data-team-id') or element.get('id') or ''
            
            # Extract team name
            team_name = element.get_text(strip=True)
            if not team_name:
                # Look for nested elements with team name
                name_elem = element.find(['h2', 'h3', 'h4', 'span', 'div'], class_=re.compile(r'name|title', re.I))
                if name_elem:
                    team_name = name_elem.get_text(strip=True)
            
            # Extract logo URL
            logo = None
            img = element.find('img')
            if img:
                logo = img.get('src')
            
            if team_name and team_name not in ['Team', 'Teams', 'Roster']:
                team = CBSTeam(
                    id=team_id,
                    name=team_name,
                    logo=logo
                )
                teams.append(team)
        
        # If still no teams found, try a more aggressive approach
        if not teams:
            # Look for any text that might be team names
            # This is a fallback and might catch false positives
            text_elements = soup.find_all(['div', 'span', 'a'], string=re.compile(r'[A-Z][a-z]+', re.I))
            for elem in text_elements:
                text = elem.get_text(strip=True)
                if len(text) > 3 and len(text) < 50 and not text.isdigit():
                    # Simple heuristic to identify potential team names
                    if not any(word in text.lower() for word in ['login', 'sign', 'menu', 'nav', 'header', 'footer']):
                        team = CBSTeam(
                            id=f"team_{len(teams) + 1}",
                            name=text
                        )
                        teams.append(team)
        
        return teams
    
    def _parse_standings_html(self, html: str) -> Dict[str, Any]:
        """Parse standings from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        standings = {
            "teams": [],
            "parsed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Look for standings table
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')
            for row in rows[1:]:  # Skip header row
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:
                    team_data = {
                        "rank": cells[0].get_text(strip=True) if len(cells) > 0 else "",
                        "team": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                        "record": cells[2].get_text(strip=True) if len(cells) > 2 else "",
                    }
                    standings["teams"].append(team_data)
        
        return standings
    
    def _parse_schedule_html(self, html: str) -> Dict[str, Any]:
        """Parse schedule from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        schedule = {
            "matchups": [],
            "parsed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Look for schedule/matchup elements
        matchup_elements = soup.find_all(['div', 'tr'], class_=re.compile(r'matchup|game|schedule', re.I))
        
        for element in matchup_elements:
            matchup_data = {
                "teams": element.get_text(strip=True),
                "raw_html": str(element)[:200]  # First 200 chars for debugging
            }
            schedule["matchups"].append(matchup_data)
        
        return schedule
    
    def _parse_roster_html(self, html: str) -> Dict[str, Any]:
        """Parse roster from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        roster = {
            "players": [],
            "parsed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Look for player elements
        player_elements = soup.find_all(['div', 'tr', 'li'], class_=re.compile(r'player|roster', re.I))
        
        for element in player_elements:
            player_data = {
                "name": element.get_text(strip=True),
                "raw_html": str(element)[:200]  # First 200 chars for debugging
            }
            roster["players"].append(player_data)
        
        return roster
    
    def _parse_player_stats_html(self, html: str) -> Dict[str, Any]:
        """Parse player stats from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        stats = {
            "player_info": {},
            "stats": {},
            "parsed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Look for stats table
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    stats["stats"][key] = value
        
        return stats
    
    def export_league_data(self, output_file: str = None) -> Dict[str, Any]:
        """Export all available league data"""
        logger.info(f"Exporting data for league: {self.league_id}")
        
        data = {
            "league_id": self.league_id,
            "sport": self.sport,
            "base_url": self.base_url,
            "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "league_info": None,
            "teams": [],
            "standings": {},
            "schedule": {},
            "errors": []
        }
        
        # Get league info
        try:
            league_info = self.get_league_info()
            if league_info:
                data["league_info"] = {
                    "name": league_info.name,
                    "team_count": league_info.team_count,
                    "has_drafted": league_info.has_drafted
                }
        except Exception as e:
            data["errors"].append(f"League info error: {e}")
        
        # Get teams
        try:
            teams = self.get_teams()
            for team in teams:
                data["teams"].append({
                    "id": team.id,
                    "name": team.name,
                    "logo": team.logo,
                    "player_count": len(team.players)
                })
        except Exception as e:
            data["errors"].append(f"Teams error: {e}")
        
        # Get standings
        try:
            data["standings"] = self.get_standings()
        except Exception as e:
            data["errors"].append(f"Standings error: {e}")
        
        # Get schedule
        try:
            data["schedule"] = self.get_schedule()
        except Exception as e:
            data["errors"].append(f"Schedule error: {e}")
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Data exported to: {output_file}")
        
        return data

def main():
    parser = argparse.ArgumentParser(description="CBS Sports Fantasy Hockey Integration")
    parser.add_argument("--league-id", required=True, help="CBS Sports league ID (subdomain)")
    parser.add_argument("--sport", default="hockey", choices=["hockey", "football", "baseball", "basketball"], 
                       help="Sport type")
    parser.add_argument("--output", help="Output file for exported data")
    parser.add_argument("--teams-only", action="store_true", help="Only fetch teams data")
    parser.add_argument("--standings-only", action="store_true", help="Only fetch standings")
    
    args = parser.parse_args()
    
    # Initialize CBS Sports integration
    cbs = CBSSportsIntegration(args.league_id, args.sport)
    
    if args.teams_only:
        teams = cbs.get_teams()
        print(f"Found {len(teams)} teams:")
        for team in teams:
            print(f"  {team.id}: {team.name} ({len(team.players)} players)")
    
    elif args.standings_only:
        standings = cbs.get_standings()
        print(json.dumps(standings, indent=2))
    
    else:
        # Export all data
        data = cbs.export_league_data(args.output)
        
        # Print summary
        print(f"\nCBS Sports League Export Summary:")
        print(f"League ID: {data['league_id']}")
        print(f"Sport: {data['sport']}")
        print(f"Teams Found: {len(data['teams'])}")
        print(f"Errors: {len(data['errors'])}")
        
        if data['errors']:
            print(f"\nErrors encountered:")
            for error in data['errors']:
                print(f"  - {error}")

if __name__ == "__main__":
    main() 