#!/usr/bin/env python3
"""
Authenticated CBS Sports Fantasy Hockey Integration
This script handles authentication and session management for CBS Sports.
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
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    # Prefer Selenium Manager (built-in) over webdriver_manager to avoid path issues
except ImportError as e:
    print(f"Missing required packages: {e}")
    print("Install with: pip install beautifulsoup4 selenium")
    sys.exit(1)

# Import credentials manager
try:
    from cbs_credentials import CBSCredentials
except ImportError:
    print("Credentials manager not found. Make sure cbs_credentials.py is in the same directory.")
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

class CBSSportsAuthenticated:
    """Authenticated CBS Sports fantasy hockey integration"""
    
    def __init__(self, league_id: str, sport: str = "hockey", headless: bool = True):
        self.league_id = league_id
        self.sport = sport
        self.base_url = f"https://{league_id}.{sport}.cbssports.com"
        self.headless = headless
        self.driver = None
        self.session = requests.Session()
        self.credentials_manager = CBSCredentials()
        
        # Configure session headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def setup_driver(self):
        """Initialize Selenium WebDriver"""
        chrome_options = Options()
        if self.headless:
            # Use new headless where supported
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        # Use Selenium Manager (no external driver path needed)
        self.driver = webdriver.Chrome(options=chrome_options)
        return self.driver
    
    def login(self, username: str = None, password: str = None) -> bool:
        """Login to CBS Sports"""
        if not self.driver:
            self.setup_driver()
        
        # Get credentials if not provided
        if not username or not password:
            username, password = self.credentials_manager.get_credentials_interactive()
            if not username or not password:
                logger.error("No credentials provided")
                return False
        
        try:
            logger.info("Attempting to login to CBS Sports...")
            
            # Navigate to the league URL (will redirect to login if needed)
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Check if we need to login
            current_url = self.driver.current_url
            if 'login' in current_url.lower() or 'signin' in current_url.lower():
                logger.info("Login required, proceeding with authentication...")
                
                # Find and fill username field
                try:
                    username_field = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.NAME, "email"))
                    )
                    username_field.clear()
                    username_field.send_keys(username)
                except TimeoutException:
                    # Try alternative selectors
                    username_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='email'], input[name='username']")
                    username_field.clear()
                    username_field.send_keys(username)
                
                # Find and fill password field
                password_field = self.driver.find_element(By.NAME, "password")
                password_field.clear()
                password_field.send_keys(password)
                
                # Submit form
                submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
                submit_button.click()
                
                # Wait for redirect
                time.sleep(5)
                
                # Check if login was successful
                current_url = self.driver.current_url
                if 'login' not in current_url.lower() and 'signin' not in current_url.lower():
                    logger.info("Login appears successful")
                    
                    # Transfer cookies to requests session
                    self._transfer_cookies()
                    return True
                else:
                    logger.warning("Login may have failed")
                    return False
            else:
                logger.info("Already logged in or no login required")
                self._transfer_cookies()
                return True
                
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def _transfer_cookies(self):
        """Transfer cookies from Selenium to requests session"""
        if self.driver:
            for cookie in self.driver.get_cookies():
                self.session.cookies.set(cookie['name'], cookie['value'])
    
    def get_teams(self) -> List[CBSTeam]:
        """Get all teams in the league using authenticated session"""
        teams = []
        
        try:
            # Navigate to teams page
            teams_url = f"{self.base_url}/teams"
            logger.info(f"Navigating to teams page: {teams_url}")
            
            if self.driver:
                self.driver.get(teams_url)
                time.sleep(3)
                
                # Parse teams from the page
                teams = self._parse_teams_from_driver()
            else:
                # Use requests session
                response = self.session.get(teams_url)
                response.raise_for_status()
                teams = self._parse_teams_from_html(response.text)
                
        except Exception as e:
            logger.error(f"Error fetching teams: {e}")
        
        return teams
    
    def _parse_teams_from_driver(self) -> List[CBSTeam]:
        """Parse teams from Selenium WebDriver"""
        teams = []
        
        try:
            # Look for team elements with various selectors
            team_selectors = [
                ".team", ".team-name", ".team-info", ".roster-team",
                "[data-team-id]", ".fantasy-team", ".league-team",
                ".team-container", ".team-item"
            ]
            
            for selector in team_selectors:
                try:
                    team_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if team_elements:
                        logger.info(f"Found {len(team_elements)} teams using selector: {selector}")
                        break
                except:
                    continue
            
            # If no specific selectors work, try a broader approach
            if not team_elements:
                # Look for elements containing team-like text
                team_elements = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'team') or contains(@class, 'roster')]")
            
            for element in team_elements:
                try:
                    # Extract team name
                    team_name = element.text.strip()
                    if not team_name:
                        # Look for nested elements
                        name_elements = element.find_elements(By.CSS_SELECTOR, "h2, h3, h4, .name, .title")
                        if name_elements:
                            team_name = name_elements[0].text.strip()
                    
                    # Extract team ID
                    team_id = element.get_attribute('data-team-id') or element.get_attribute('id') or ''
                    
                    # Extract logo
                    logo = None
                    try:
                        img = element.find_element(By.TAG_NAME, "img")
                        logo = img.get_attribute('src')
                    except:
                        pass
                    
                    # Filter out non-team elements
                    if (team_name and 
                        len(team_name) > 2 and 
                        len(team_name) < 50 and
                        team_name.lower() not in ['login', 'sign', 'menu', 'nav', 'header', 'footer', 'team', 'teams']):
                        
                        team = CBSTeam(
                            id=team_id or f"team_{len(teams) + 1}",
                            name=team_name,
                            logo=logo
                        )
                        teams.append(team)
                        
                except Exception as e:
                    logger.debug(f"Error parsing team element: {e}")
                    continue
            
            # If still no teams found, try to extract from page text
            if not teams:
                page_text = self.driver.page_source
                teams = self._extract_teams_from_text(page_text)
        
        except Exception as e:
            logger.error(f"Error parsing teams from driver: {e}")
        
        return teams
    
    def _parse_teams_from_html(self, html: str) -> List[CBSTeam]:
        """Parse teams from HTML using BeautifulSoup"""
        soup = BeautifulSoup(html, 'html.parser')
        teams = []
        
        # Look for team elements
        team_selectors = [
            '.team', '.team-name', '.team-info', '.roster-team',
            '[data-team-id]', '.fantasy-team', '.league-team'
        ]
        
        for selector in team_selectors:
            team_elements = soup.select(selector)
            if team_elements:
                logger.info(f"Found {len(team_elements)} teams using selector: {selector}")
                break
        
        for element in team_elements:
            # Extract team name
            team_name = element.get_text(strip=True)
            if not team_name:
                name_elem = element.find(['h2', 'h3', 'h4', 'span', 'div'], class_=re.compile(r'name|title', re.I))
                if name_elem:
                    team_name = name_elem.get_text(strip=True)
            
            # Extract team ID
            team_id = element.get('data-team-id') or element.get('id') or ''
            
            # Extract logo
            logo = None
            img = element.find('img')
            if img:
                logo = img.get('src')
            
            if (team_name and 
                len(team_name) > 2 and 
                len(team_name) < 50 and
                team_name.lower() not in ['login', 'sign', 'menu', 'nav', 'header', 'footer', 'team', 'teams']):
                
                team = CBSTeam(
                    id=team_id or f"team_{len(teams) + 1}",
                    name=team_name,
                    logo=logo
                )
                teams.append(team)
        
        return teams
    
    def _extract_teams_from_text(self, text: str) -> List[CBSTeam]:
        """Extract team names from page text using heuristics"""
        teams = []
        
        # Look for patterns that might indicate team names
        # This is a fallback method and may have false positives
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if (len(line) > 3 and 
                len(line) < 50 and 
                line[0].isupper() and
                not line.isdigit() and
                not any(word in line.lower() for word in ['login', 'sign', 'menu', 'nav', 'header', 'footer', 'team', 'teams', 'roster'])):
                
                # Simple heuristic to identify potential team names
                if re.match(r'^[A-Z][a-zA-Z\s]+$', line):
                    team = CBSTeam(
                        id=f"team_{len(teams) + 1}",
                        name=line
                    )
                    teams.append(team)
        
        return teams
    
    def get_standings(self) -> Dict[str, Any]:
        """Get league standings"""
        try:
            standings_url = f"{self.base_url}/standings"
            logger.info(f"Fetching standings from: {standings_url}")
            
            if self.driver:
                self.driver.get(standings_url)
                time.sleep(3)
                return self._parse_standings_from_driver()
            else:
                response = self.session.get(standings_url)
                response.raise_for_status()
                return self._parse_standings_from_html(response.text)
                
        except Exception as e:
            logger.error(f"Error fetching standings: {e}")
            return {}
    
    def _parse_standings_from_driver(self) -> Dict[str, Any]:
        """Parse standings from WebDriver"""
        standings = {
            "teams": [],
            "parsed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            # Look for standings table
            table = self.driver.find_element(By.TAG_NAME, "table")
            rows = table.find_elements(By.TAG_NAME, "tr")
            
            for row in rows[1:]:  # Skip header
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 3:
                    team_data = {
                        "rank": cells[0].text.strip() if len(cells) > 0 else "",
                        "team": cells[1].text.strip() if len(cells) > 1 else "",
                        "record": cells[2].text.strip() if len(cells) > 2 else "",
                    }
                    standings["teams"].append(team_data)
        
        except Exception as e:
            logger.error(f"Error parsing standings from driver: {e}")
        
        return standings
    
    def _parse_standings_from_html(self, html: str) -> Dict[str, Any]:
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
    
    def export_league_data(self, output_file: str = None) -> Dict[str, Any]:
        """Export all available league data"""
        logger.info(f"Exporting data for league: {self.league_id}")
        
        data = {
            "league_id": self.league_id,
            "sport": self.sport,
            "base_url": self.base_url,
            "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "teams": [],
            "standings": {},
            "errors": []
        }
        
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
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Data exported to: {output_file}")
        
        return data
    
    def close(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
        self.session.close()

def main():
    parser = argparse.ArgumentParser(description="Authenticated CBS Sports Fantasy Hockey Integration")
    parser.add_argument("--league-id", required=True, help="CBS Sports league ID (subdomain)")
    parser.add_argument("--sport", default="hockey", choices=["hockey", "football", "baseball", "basketball"], 
                       help="Sport type")
    parser.add_argument("--username", help="CBS Sports username/email")
    parser.add_argument("--password", help="CBS Sports password")
    parser.add_argument("--output", help="Output file for exported data")
    parser.add_argument("--teams-only", action="store_true", help="Only fetch teams data")
    parser.add_argument("--no-headless", action="store_true", help="Run browser in visible mode")
    parser.add_argument("--use-saved-creds", action="store_true", help="Use saved credentials")
    
    args = parser.parse_args()
    
    # Initialize CBS Sports integration
    cbs = CBSSportsAuthenticated(args.league_id, args.sport, headless=not args.no_headless)
    
    try:
        # Handle credentials
        username = args.username
        password = args.password
        
        if args.use_saved_creds:
            # Use saved credentials
            username, password = cbs.credentials_manager.load_credentials()
            if not username or not password:
                print("No saved credentials found. Please save credentials first.")
                return
        
        # Login if credentials provided or use saved ones
        if username and password:
            if not cbs.login(username, password):
                print("Login failed. Cannot proceed.")
                return
        else:
            # Interactive login
            if not cbs.login():
                print("Login failed. Cannot proceed.")
                return
        
        if args.teams_only:
            teams = cbs.get_teams()
            print(f"Found {len(teams)} teams:")
            for team in teams:
                print(f"  {team.id}: {team.name} ({len(team.players)} players)")
        
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
    
    finally:
        cbs.close()

if __name__ == "__main__":
    main() 