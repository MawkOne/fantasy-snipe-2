#!/usr/bin/env python3
"""
Research script for CBS Sports fantasy hockey data extraction.
This script analyzes page structure and network traffic to understand
how to extract fantasy league data from CBS Sports.

Usage:
    python research_cbs_sports.py --url "https://uhhp.hockey.cbssports.com/home" --mode analyze
    python research_cbs_sports.py --url "https://uhhp.hockey.cbssports.com/home" --mode scrape --username "user" --password "pass"
"""

import os
import sys
import json
import time
import argparse
import requests
from urllib.parse import urljoin, urlparse
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
except ImportError as e:
    print(f"Missing required packages: {e}")
    print("Install with: pip install beautifulsoup4 selenium requests")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class CBSLeagueInfo:
    """Structure to hold CBS Sports league information"""
    league_id: Optional[str] = None
    league_name: Optional[str] = None
    teams: List[Dict[str, Any]] = None
    players: List[Dict[str, Any]] = None
    settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.teams is None:
            self.teams = []
        if self.players is None:
            self.players = []
        if self.settings is None:
            self.settings = {}

class CBSSportsResearch:
    """Research and scraping class for CBS Sports fantasy hockey"""
    
    def __init__(self, headless: bool = True):
        self.session = requests.Session()
        self.headless = headless
        self.driver = None
        self.base_url = "https://www.cbssports.com"
        
        # Configure session headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def setup_driver(self):
        """Initialize Selenium WebDriver"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        return self.driver
    
    def analyze_page_structure(self, url: str) -> Dict[str, Any]:
        """Analyze the structure of a CBS Sports page without authentication"""
        logger.info(f"Analyzing page structure for: {url}")
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            analysis = {
                'url': url,
                'status_code': response.status_code,
                'title': soup.title.string if soup.title else None,
                'forms': self._extract_forms(soup),
                'links': self._extract_links(soup, url),
                'scripts': self._extract_scripts(soup),
                'data_attributes': self._extract_data_attributes(soup),
                'potential_selectors': self._identify_selectors(soup),
                'requires_auth': self._check_auth_required(response, soup),
            }
            
            return analysis
            
        except requests.RequestException as e:
            logger.error(f"Error analyzing page: {e}")
            return {'error': str(e), 'url': url}
    
    def _extract_forms(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract form information"""
        forms = []
        for form in soup.find_all('form'):
            form_info = {
                'action': form.get('action'),
                'method': form.get('method', 'GET'),
                'inputs': []
            }
            
            for input_tag in form.find_all(['input', 'select', 'textarea']):
                input_info = {
                    'type': input_tag.get('type'),
                    'name': input_tag.get('name'),
                    'id': input_tag.get('id'),
                    'placeholder': input_tag.get('placeholder'),
                }
                form_info['inputs'].append(input_info)
            
            forms.append(form_info)
        
        return forms
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract relevant links"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href:
                full_url = urljoin(base_url, href)
                links.append({
                    'text': link.get_text(strip=True),
                    'href': href,
                    'full_url': full_url,
                    'class': link.get('class', []),
                })
        
        return links
    
    def _extract_scripts(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract script information"""
        scripts = []
        for script in soup.find_all('script'):
            script_info = {
                'src': script.get('src'),
                'type': script.get('type'),
                'content_length': len(script.get_text()) if script.string else 0,
            }
            scripts.append(script_info)
        
        return scripts
    
    def _extract_data_attributes(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract data attributes that might contain useful information"""
        data_attrs = {}
        
        # Look for common data attributes
        for attr in ['data-league-id', 'data-team-id', 'data-player-id', 'data-user-id']:
            elements = soup.find_all(attrs={attr: True})
            if elements:
                data_attrs[attr] = [elem.get(attr) for elem in elements]
        
        return data_attrs
    
    def _identify_selectors(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Identify potential CSS selectors for data extraction"""
        selectors = {
            'tables': [],
            'lists': [],
            'divs_with_classes': [],
            'spans_with_classes': [],
        }
        
        # Find tables
        for table in soup.find_all('table'):
            classes = table.get('class', [])
            if classes:
                selectors['tables'].append(f"table.{'.'.join(classes)}")
        
        # Find lists
        for ul in soup.find_all(['ul', 'ol']):
            classes = ul.get('class', [])
            if classes:
                selectors['lists'].append(f"{ul.name}.{'.'.join(classes)}")
        
        # Find divs with classes
        for div in soup.find_all('div', class_=True):
            classes = div.get('class', [])
            if classes:
                selectors['divs_with_classes'].append(f"div.{'.'.join(classes)}")
        
        # Find spans with classes
        for span in soup.find_all('span', class_=True):
            classes = span.get('class', [])
            if classes:
                selectors['spans_with_classes'].append(f"span.{'.'.join(classes)}")
        
        return selectors
    
    def _check_auth_required(self, response: requests.Response, soup: BeautifulSoup) -> bool:
        """Check if the page requires authentication"""
        auth_indicators = [
            'login' in response.url.lower(),
            'signin' in response.url.lower(),
            soup.find('input', {'name': 'username'}) is not None,
            soup.find('input', {'name': 'email'}) is not None,
            soup.find('input', {'type': 'password'}) is not None,
            'login' in soup.get_text().lower(),
            'sign in' in soup.get_text().lower(),
        ]
        
        return any(auth_indicators)
    
    def login(self, username: str, password: str) -> bool:
        """Attempt to login to CBS Sports"""
        if not self.driver:
            self.setup_driver()
        
        try:
            logger.info("Attempting to login to CBS Sports...")
            
            # Navigate to login page
            self.driver.get("https://www.cbssports.com/login")
            time.sleep(2)
            
            # Find and fill username field
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            username_field.send_keys(username)
            
            # Find and fill password field
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.send_keys(password)
            
            # Submit form
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()
            
            # Wait for redirect
            time.sleep(5)
            
            # Check if login was successful
            current_url = self.driver.current_url
            if 'login' not in current_url.lower():
                logger.info("Login appears successful")
                return True
            else:
                logger.warning("Login may have failed")
                return False
                
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def extract_league_data(self, league_url: str) -> CBSLeagueInfo:
        """Extract league data from CBS Sports"""
        if not self.driver:
            logger.error("WebDriver not initialized. Call login() first.")
            return CBSLeagueInfo()
        
        try:
            logger.info(f"Navigating to league URL: {league_url}")
            self.driver.get(league_url)
            time.sleep(3)
            
            league_info = CBSLeagueInfo()
            
            # Extract league name
            try:
                league_name_elem = self.driver.find_element(By.CSS_SELECTOR, "h1, .league-name, .league-title")
                league_info.league_name = league_name_elem.text.strip()
            except NoSuchElementException:
                logger.warning("Could not find league name")
            
            # Extract teams
            league_info.teams = self._extract_teams()
            
            # Extract players
            league_info.players = self._extract_players()
            
            # Extract settings
            league_info.settings = self._extract_settings()
            
            return league_info
            
        except Exception as e:
            logger.error(f"Error extracting league data: {e}")
            return CBSLeagueInfo()
    
    def _extract_teams(self) -> List[Dict[str, Any]]:
        """Extract team information"""
        teams = []
        
        try:
            # Look for team elements
            team_selectors = [
                ".team-name", ".team", ".roster-team", 
                "[data-team-id]", ".fantasy-team"
            ]
            
            for selector in team_selectors:
                team_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if team_elements:
                    logger.info(f"Found {len(team_elements)} teams using selector: {selector}")
                    break
            
            for team_elem in team_elements:
                team_info = {
                    'name': team_elem.text.strip(),
                    'id': team_elem.get_attribute('data-team-id'),
                    'owner': None,
                    'record': None,
                }
                
                # Try to find owner and record
                try:
                    parent = team_elem.find_element(By.XPATH, "./..")
                    owner_elem = parent.find_element(By.CSS_SELECTOR, ".owner, .team-owner")
                    team_info['owner'] = owner_elem.text.strip()
                except NoSuchElementException:
                    pass
                
                teams.append(team_info)
        
        except Exception as e:
            logger.error(f"Error extracting teams: {e}")
        
        return teams
    
    def _extract_players(self) -> List[Dict[str, Any]]:
        """Extract player information"""
        players = []
        
        try:
            # Look for player elements
            player_selectors = [
                ".player-name", ".player", ".roster-player",
                "[data-player-id]", ".fantasy-player"
            ]
            
            for selector in player_selectors:
                player_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if player_elements:
                    logger.info(f"Found {len(player_elements)} players using selector: {selector}")
                    break
            
            for player_elem in player_elements:
                player_info = {
                    'name': player_elem.text.strip(),
                    'id': player_elem.get_attribute('data-player-id'),
                    'position': None,
                    'team': None,
                    'stats': {},
                }
                
                # Try to find position and team
                try:
                    parent = player_elem.find_element(By.XPATH, "./..")
                    pos_elem = parent.find_element(By.CSS_SELECTOR, ".position, .pos")
                    player_info['position'] = pos_elem.text.strip()
                except NoSuchElementException:
                    pass
                
                players.append(player_info)
        
        except Exception as e:
            logger.error(f"Error extracting players: {e}")
        
        return players
    
    def _extract_settings(self) -> Dict[str, Any]:
        """Extract league settings"""
        settings = {}
        
        try:
            # Look for settings elements
            settings_selectors = [
                ".league-settings", ".settings", ".league-info",
                ".scoring-rules", ".roster-positions"
            ]
            
            for selector in settings_selectors:
                settings_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if settings_elements:
                    logger.info(f"Found settings using selector: {selector}")
                    for elem in settings_elements:
                        settings[elem.get_attribute('class') or 'unknown'] = elem.text.strip()
                    break
        
        except Exception as e:
            logger.error(f"Error extracting settings: {e}")
        
        return settings
    
    def save_analysis(self, analysis: Dict[str, Any], filename: str):
        """Save analysis results to file"""
        with open(filename, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        logger.info(f"Analysis saved to: {filename}")
    
    def close(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
        self.session.close()

def main():
    parser = argparse.ArgumentParser(description="Research CBS Sports fantasy hockey data extraction")
    parser.add_argument("--url", required=True, help="CBS Sports league URL")
    parser.add_argument("--mode", choices=["analyze", "scrape"], default="analyze", 
                       help="Mode: analyze (no auth) or scrape (with auth)")
    parser.add_argument("--username", help="CBS Sports username/email")
    parser.add_argument("--password", help="CBS Sports password")
    parser.add_argument("--output", default="cbs_analysis.json", help="Output file for analysis")
    parser.add_argument("--headless", action="store_true", default=True, help="Run browser in headless mode")
    
    args = parser.parse_args()
    
    researcher = CBSSportsResearch(headless=args.headless)
    
    try:
        if args.mode == "analyze":
            # Analyze page structure without authentication
            analysis = researcher.analyze_page_structure(args.url)
            researcher.save_analysis(analysis, args.output)
            
            print(f"\nAnalysis Results:")
            print(f"Title: {analysis.get('title', 'N/A')}")
            print(f"Requires Auth: {analysis.get('requires_auth', 'Unknown')}")
            print(f"Forms Found: {len(analysis.get('forms', []))}")
            print(f"Links Found: {len(analysis.get('links', []))}")
            print(f"Scripts Found: {len(analysis.get('scripts', []))}")
            print(f"Data Attributes: {analysis.get('data_attributes', {})}")
            
        elif args.mode == "scrape":
            if not args.username or not args.password:
                print("Error: Username and password required for scrape mode")
                return
            
            # Login and extract data
            if researcher.login(args.username, args.password):
                league_data = researcher.extract_league_data(args.url)
                
                # Save extracted data
                with open(args.output, 'w') as f:
                    json.dump(league_data.__dict__, f, indent=2, default=str)
                
                print(f"\nExtracted Data:")
                print(f"League Name: {league_data.league_name}")
                print(f"Teams Found: {len(league_data.teams)}")
                print(f"Players Found: {len(league_data.players)}")
                print(f"Settings Found: {len(league_data.settings)}")
            else:
                print("Login failed. Cannot extract data.")
    
    finally:
        researcher.close()

if __name__ == "__main__":
    main() 