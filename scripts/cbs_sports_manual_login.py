#!/usr/bin/env python3
"""
CBS Sports Manual Login Integration
This script opens a browser for manual login to handle reCAPTCHA, then extracts data.
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
except ImportError as e:
    print(f"Missing required packages: {e}")
    print("Install with: pip install beautifulsoup4 selenium")
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

class CBSSportsManualLogin:
    """CBS Sports integration with manual login support"""
    
    def __init__(self, league_id: str, sport: str = "hockey"):
        self.league_id = league_id
        self.sport = sport
        self.base_url = f"http://{league_id}.{sport}.cbssports.com"
        self.driver = None
        self.session = requests.Session()
        self.discovered_endpoints = {}
        
        # Configure session headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def setup_driver(self):
        """Initialize Selenium WebDriver with visible browser"""
        chrome_options = Options()
        # Always run in visible mode for manual intervention
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        return self.driver
    
    def manual_login(self) -> bool:
        """Open browser for manual login"""
        if not self.driver:
            self.setup_driver()
        
        try:
            logger.info("Opening CBS Sports for manual login...")
            logger.info(f"URL: {self.base_url}")
            
            # Navigate to the league URL
            self.driver.get(self.base_url)
            
            print("\n🔐 Manual Login Required")
            print("=" * 40)
            print("1. A browser window has opened")
            print("2. Please log in manually to CBS Sports")
            print("3. Navigate to your league's teams page")
            print("4. Once logged in, press Enter here to continue...")
            
            input("\nPress Enter when you're logged in and ready to extract data...")
            
            # Transfer cookies to requests session regardless of URL
            self._transfer_cookies()
            logger.info("Manual login completed - proceeding with data extraction")
            
            # Save session data for API client
            self._save_browser_session()
            
            return True
                
        except Exception as e:
            logger.error(f"Manual login failed: {e}")
            return False
    
    def _transfer_cookies(self):
        """Transfer cookies from Selenium to requests session"""
        if self.driver:
            for cookie in self.driver.get_cookies():
                self.session.cookies.set(cookie['name'], cookie['value'])
    
    def _save_browser_session(self):
        """Save browser session data for API client transfer"""
        try:
            from pathlib import Path
            
            # Create session directory
            home_dir = Path.home()
            session_dir = home_dir / ".nhl_api"
            session_dir.mkdir(exist_ok=True)
            
            # Save session data
            session_file = session_dir / f"cbs_browser_session_{self.league_id}.json"
            
            session_data = {
                "league_id": self.league_id,
                "sport": self.sport,
                "base_url": self.base_url,
                "cookies": dict(self.session.cookies),
                "endpoints": self.discovered_endpoints,
                "saved_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            logger.info(f"Browser session saved to {session_file}")
            
        except Exception as e:
            logger.error(f"Failed to save browser session: {e}")
    
    def get_teams(self) -> List[CBSTeam]:
        """Get all teams in the league"""
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
                ".team-container", ".team-item", ".team-link"
            ]
            
            team_elements = []
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
            
            # If still no teams, try to find any clickable elements that might be teams
            if not team_elements:
                team_elements = self.driver.find_elements(By.TAG_NAME, "a")
            
            for element in team_elements:
                try:
                    # Extract team name
                    team_name = element.text.strip()
                    if not team_name:
                        # Look for nested elements
                        name_elements = element.find_elements(By.CSS_SELECTOR, "h2, h3, h4, .name, .title, span, div")
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
                        team_name.lower() not in ['login', 'sign', 'menu', 'nav', 'header', 'footer', 'team', 'teams', 'roster', 'home', 'standings', 'schedule']):
                        
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
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if (len(line) > 3 and 
                len(line) < 50 and 
                line[0].isupper() and
                not line.isdigit() and
                not any(word in line.lower() for word in ['login', 'sign', 'menu', 'nav', 'header', 'footer', 'team', 'teams', 'roster', 'home', 'standings', 'schedule'])):
                
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
            "league_settings": {},
            "team_rosters": {},
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
        
        # Get league settings
        try:
            data["league_settings"] = self.get_league_settings()
        except Exception as e:
            data["errors"].append(f"League settings error: {e}")
        
        # Get team rosters
        try:
            data["team_rosters"] = self.get_team_rosters()
        except Exception as e:
            data["errors"].append(f"Team rosters error: {e}")
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Data exported to: {output_file}")
        
        return data
    
    def get_league_settings(self) -> Dict[str, Any]:
        """Get league settings and configuration"""
        settings = {
            "league_info": {},
            "scoring_rules": {},
            "roster_settings": {},
            "draft_settings": {},
            "trade_settings": {},
            "parsed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            # Specifically target the rules page first
            rules_url = f"{self.base_url}/rules"
            logger.info(f"Fetching league rules from: {rules_url}")
            
            if self.driver:
                self.driver.get(rules_url)
                time.sleep(5)  # Give more time for the page to load
                
                # Check if we're on the rules page or redirected to login
                current_url = self.driver.current_url
                if 'rules' in current_url.lower():
                    logger.info("Successfully accessed rules page")
                    settings.update(self._parse_rules_page())
                else:
                    logger.warning("Redirected from rules page - may need to navigate manually")
            
            # Also try other settings pages as fallback
            settings_urls = [
                f"{self.base_url}/settings",
                f"{self.base_url}/league/settings",
                f"{self.base_url}/league/rules"
            ]
            
            for url in settings_urls:
                try:
                    logger.info(f"Trying to fetch settings from: {url}")
                    if self.driver:
                        self.driver.get(url)
                        time.sleep(3)
                        settings.update(self._parse_settings_from_driver())
                        break
                    else:
                        response = self.session.get(url)
                        if response.status_code == 200:
                            settings.update(self._parse_settings_from_html(response.text))
                            break
                except Exception as e:
                    logger.debug(f"Failed to fetch settings from {url}: {e}")
                    continue
            
            # Also try to extract from the main page
            if self.driver:
                settings.update(self._extract_settings_from_main_page())
                
        except Exception as e:
            logger.error(f"Error fetching league settings: {e}")
        
        return settings
    
    def _parse_rules_page(self) -> Dict[str, Any]:
        """Parse the specific rules page for league configuration"""
        rules_data = {
            "scoring_rules": {},
            "roster_settings": {},
            "draft_settings": {},
            "trade_settings": {},
            "waiver_settings": {},
            "playoff_settings": {},
            "raw_rules_text": []
        }
        
        try:
            # Get the page source
            page_source = self.driver.page_source
            
            # Look for specific sections in the rules page
            sections_to_find = [
                "scoring", "roster", "draft", "trade", "waiver", "playoff", 
                "settings", "rules", "configuration", "points", "categories"
            ]
            
            # Extract all text content
            soup = BeautifulSoup(page_source, 'html.parser')
            text_content = soup.get_text()
            
            # Split into lines and look for relevant content
            lines = text_content.split('\n')
            for line in lines:
                line = line.strip()
                if line and len(line) > 5:
                    # Look for lines containing scoring or rules information
                    if any(keyword in line.lower() for keyword in sections_to_find):
                        rules_data["raw_rules_text"].append(line)
            
            # Look for specific scoring patterns
            scoring_patterns = [
                r'(\w+)\s*=\s*(\d+(?:\.\d+)?)\s*points?',
                r'(\w+)\s*:\s*(\d+(?:\.\d+)?)',
                r'(\w+)\s*\((\d+(?:\.\d+)?)\)'
            ]
            
            for pattern in scoring_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    category, points = match
                    if category.lower() not in ['page', 'div', 'span', 'class']:
                        rules_data["scoring_rules"][category] = points
            
            # Look for roster configuration
            roster_patterns = [
                r'roster\s*size\s*:\s*(\d+)',
                r'(\d+)\s*players?\s*per\s*team',
                r'positions?\s*:\s*([^,\n]+)'
            ]
            
            for pattern in roster_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    rules_data["roster_settings"][f"roster_{len(rules_data['roster_settings'])}"] = match
            
            # Look for draft information
            draft_patterns = [
                r'draft\s*type\s*:\s*([^,\n]+)',
                r'draft\s*date\s*:\s*([^,\n]+)',
                r'(\d+)\s*rounds?'
            ]
            
            for pattern in draft_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    rules_data["draft_settings"][f"draft_{len(rules_data['draft_settings'])}"] = match
            
            # Look for tables with rules data
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            for table in tables:
                try:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    table_data = []
                    for row in rows:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 2:
                            row_data = {
                                "key": cells[0].text.strip() if len(cells) > 0 else "",
                                "value": cells[1].text.strip() if len(cells) > 1 else ""
                            }
                            table_data.append(row_data)
                    
                    if table_data:
                        rules_data["table_rules"] = table_data
                except Exception as e:
                    logger.debug(f"Error parsing rules table: {e}")
            
            # Look for lists with rules
            lists = self.driver.find_elements(By.TAG_NAME, "ul")
            for list_elem in lists:
                try:
                    items = list_elem.find_elements(By.TAG_NAME, "li")
                    list_data = []
                    for item in items:
                        text = item.text.strip()
                        if text and len(text) > 3:
                            list_data.append(text)
                    
                    if list_data:
                        rules_data["list_rules"] = list_data
                except Exception as e:
                    logger.debug(f"Error parsing rules list: {e}")
            
            # Look for specific elements that might contain rules
            rule_elements = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'rule') or contains(@class, 'scoring') or contains(@class, 'setting')]")
            for element in rule_elements:
                try:
                    text = element.text.strip()
                    if text and len(text) > 5:
                        rules_data["raw_rules_text"].append(text)
                except Exception as e:
                    logger.debug(f"Error parsing rule element: {e}")
        
        except Exception as e:
            logger.error(f"Error parsing rules page: {e}")
        
        return rules_data
    
    def _parse_settings_from_driver(self) -> Dict[str, Any]:
        """Parse settings from WebDriver"""
        settings = {}
        
        try:
            # Look for settings sections
            settings_sections = [
                "scoring", "roster", "draft", "trade", "waiver", "playoff"
            ]
            
            for section in settings_sections:
                try:
                    # Look for section headers
                    section_elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{section}') or contains(@class, '{section}')]")
                    if section_elements:
                        section_data = {}
                        for element in section_elements:
                            text = element.text.strip()
                            if text and len(text) > 3:
                                section_data[element.tag_name] = text
                        
                        if section_data:
                            settings[f"{section}_settings"] = section_data
                except Exception as e:
                    logger.debug(f"Error parsing {section} settings: {e}")
            
            # Look for tables with settings data
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            for table in tables:
                try:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    table_data = []
                    for row in rows:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 2:
                            row_data = {
                                "key": cells[0].text.strip() if len(cells) > 0 else "",
                                "value": cells[1].text.strip() if len(cells) > 1 else ""
                            }
                            table_data.append(row_data)
                    
                    if table_data:
                        settings["table_settings"] = table_data
                except Exception as e:
                    logger.debug(f"Error parsing settings table: {e}")
            
            # Look for lists with settings
            lists = self.driver.find_elements(By.TAG_NAME, "ul")
            for list_elem in lists:
                try:
                    items = list_elem.find_elements(By.TAG_NAME, "li")
                    list_data = []
                    for item in items:
                        text = item.text.strip()
                        if text and len(text) > 3:
                            list_data.append(text)
                    
                    if list_data:
                        settings["list_settings"] = list_data
                except Exception as e:
                    logger.debug(f"Error parsing settings list: {e}")
        
        except Exception as e:
            logger.error(f"Error parsing settings from driver: {e}")
        
        return settings
    
    def _parse_settings_from_html(self, html: str) -> Dict[str, Any]:
        """Parse settings from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        settings = {}
        
        # Look for settings sections
        settings_sections = [
            "scoring", "roster", "draft", "trade", "waiver", "playoff"
        ]
        
        for section in settings_sections:
            section_elements = soup.find_all(['div', 'section', 'h2', 'h3'], 
                                           string=re.compile(section, re.I))
            if section_elements:
                section_data = {}
                for element in section_elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 3:
                        section_data[element.name] = text
                
                if section_data:
                    settings[f"{section}_settings"] = section_data
        
        # Look for tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            table_data = []
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    row_data = {
                        "key": cells[0].get_text(strip=True) if len(cells) > 0 else "",
                        "value": cells[1].get_text(strip=True) if len(cells) > 1 else ""
                    }
                    table_data.append(row_data)
            
            if table_data:
                settings["table_settings"] = table_data
        
        return settings
    
    def _extract_settings_from_main_page(self) -> Dict[str, Any]:
        """Extract settings information from the main league page"""
        settings = {}
        
        try:
            # Look for league information in the page
            page_text = self.driver.page_source
            
            # Extract league name
            league_name_match = re.search(r'<title[^>]*>([^<]+)</title>', page_text, re.I)
            if league_name_match:
                settings["league_name"] = league_name_match.group(1).strip()
            
            # Look for common settings patterns
            settings_patterns = {
                "scoring_type": r'scoring[^>]*>([^<]+)',
                "roster_size": r'roster[^>]*>([^<]+)',
                "draft_type": r'draft[^>]*>([^<]+)',
                "trade_deadline": r'trade[^>]*>([^<]+)',
                "playoff_teams": r'playoff[^>]*>([^<]+)'
            }
            
            for key, pattern in settings_patterns.items():
                match = re.search(pattern, page_text, re.I)
                if match:
                    settings[key] = match.group(1).strip()
            
            # Look for any text that might contain settings
            lines = page_text.split('\n')
            settings_lines = []
            for line in lines:
                line = line.strip()
                if any(keyword in line.lower() for keyword in ['scoring', 'roster', 'draft', 'trade', 'waiver', 'playoff', 'settings', 'rules']):
                    if len(line) > 5 and len(line) < 200:
                        settings_lines.append(line)
            
            if settings_lines:
                settings["settings_text"] = settings_lines
        
        except Exception as e:
            logger.error(f"Error extracting settings from main page: {e}")
        
        return settings
    
    def get_team_rosters(self) -> Dict[str, Any]:
        """Get detailed roster information for all teams"""
        rosters = {
            "teams": {},
            "parsed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            # Specifically target the teams/all page for complete rosters
            teams_all_url = f"{self.base_url}/teams/all"
            logger.info(f"Fetching all team rosters from: {teams_all_url}")
            
            if self.driver:
                self.driver.get(teams_all_url)
                time.sleep(5)  # Give more time for the page to load
                
                # Check if we're on the teams/all page
                current_url = self.driver.current_url
                if 'teams/all' in current_url.lower():
                    logger.info("Successfully accessed teams/all page")
                    rosters.update(self._parse_teams_all_page())
                else:
                    logger.warning("Redirected from teams/all page - may need to navigate manually")
            
            # Fallback to individual team rosters if teams/all doesn't work
            if not rosters["teams"]:
                logger.info("Falling back to individual team roster extraction")
                standings = self.get_standings()
                if standings and "teams" in standings:
                    for team_data in standings["teams"]:
                        team_name = team_data.get("rank", "")  # rank field contains team name
                        if team_name:
                            logger.info(f"Fetching roster for team: {team_name}")
                            team_roster = self._get_single_team_roster(team_name)
                            if team_roster:
                                rosters["teams"][team_name] = team_roster
                
        except Exception as e:
            logger.error(f"Error fetching team rosters: {e}")
        
        return rosters
    
    def _parse_teams_all_page(self) -> Dict[str, Any]:
        """Parse the teams/all page for complete roster information"""
        all_rosters = {
            "teams": {},
            "page_info": {}
        }
        
        try:
            # Get the page source
            page_source = self.driver.page_source
            
            # Look for team sections
            team_sections = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'team') or contains(@class, 'roster')]")
            
            # Also look for table structures that might contain roster data
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            
            # Look for any elements that might contain team names
            team_elements = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'team-name') or contains(@class, 'team-info')]")
            
            # Extract all text content for analysis
            soup = BeautifulSoup(page_source, 'html.parser')
            text_content = soup.get_text()
            
            # Look for patterns that indicate team rosters
            # Common patterns in fantasy sports sites
            team_patterns = [
                r'Team:\s*([^\n]+)',
                r'([A-Z][a-zA-Z\s]+)\s*Roster',
                r'([A-Z][a-zA-Z\s]+)\s*Players'
            ]
            
            found_teams = []
            for pattern in team_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    if match.strip() and len(match.strip()) > 3:
                        found_teams.append(match.strip())
            
            # Look for player patterns
            player_patterns = [
                r'([A-Z][a-z]+ [A-Z][a-z]+)\s*([A-Z]{1,3})\s*([A-Z]{2,3})',  # Name POS TEAM
                r'([A-Z][a-z]+ [A-Z][a-z]+)\s*([A-Z]{1,3})',  # Name POS
                r'([A-Z][a-z]+ [A-Z][a-z]+)'  # Just Name
            ]
            
            all_players = []
            for pattern in player_patterns:
                matches = re.findall(pattern, text_content)
                for match in matches:
                    if isinstance(match, tuple):
                        player_info = list(match)
                    else:
                        player_info = [match]
                    
                    if player_info[0] and len(player_info[0]) > 3:
                        all_players.append(player_info)
            
            # Try to organize players by team
            # This is a simplified approach - in practice, we'd need to understand the page structure better
            current_team = None
            team_rosters = {}
            
            lines = text_content.split('\n')
            for line in lines:
                line = line.strip()
                if line:
                    # Check if this line contains a team name
                    for team_name in found_teams:
                        if team_name.lower() in line.lower():
                            current_team = team_name
                            if current_team not in team_rosters:
                                team_rosters[current_team] = []
                    
                    # Check if this line contains a player
                    for player_info in all_players:
                        if player_info[0] in line:
                            if current_team:
                                if current_team not in team_rosters:
                                    team_rosters[current_team] = []
                                team_rosters[current_team].append({
                                    "name": player_info[0],
                                    "position": player_info[1] if len(player_info) > 1 else "",
                                    "team": player_info[2] if len(player_info) > 2 else "",
                                    "raw_line": line
                                })
            
            # Convert to the expected format
            for team_name, players in team_rosters.items():
                all_rosters["teams"][team_name] = {
                    "players": players,
                    "positions": {},
                    "stats": {}
                }
            
            # If we didn't find structured data, try to extract from HTML elements
            if not all_rosters["teams"]:
                logger.info("Attempting to extract roster data from HTML elements")
                
                # Look for any clickable elements that might be team links
                team_links = self.driver.find_elements(By.TAG_NAME, "a")
                for link in team_links:
                    try:
                        link_text = link.text.strip()
                        if link_text and len(link_text) > 3:
                            # Check if this looks like a team name
                            if any(team_name.lower() in link_text.lower() for team_name in found_teams):
                                # Click on the team link to get roster
                                link.click()
                                time.sleep(2)
                                
                                # Extract roster from this team page
                                team_roster = self._extract_roster_from_current_page()
                                if team_roster:
                                    all_rosters["teams"][link_text] = team_roster
                                
                                # Go back to teams/all page
                                self.driver.get(f"{self.base_url}/teams/all")
                                time.sleep(2)
                    except Exception as e:
                        logger.debug(f"Error processing team link: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Error parsing teams/all page: {e}")
        
        return all_rosters
    
    def _extract_roster_from_current_page(self) -> Dict[str, Any]:
        """Extract roster information from the current page"""
        roster = {
            "players": [],
            "positions": {},
            "stats": {}
        }
        
        try:
            # Look for player elements
            player_elements = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'player') or contains(@class, 'roster')]")
            
            for element in player_elements:
                try:
                    text = element.text.strip()
                    if text and len(text) > 3:
                        # Simple parsing - this would need to be enhanced based on actual page structure
                        roster["players"].append({
                            "name": text,
                            "raw_text": text
                        })
                except Exception as e:
                    logger.debug(f"Error parsing player element: {e}")
        
        except Exception as e:
            logger.error(f"Error extracting roster from current page: {e}")
        
        return roster
    
    def _get_single_team_roster(self, team_name: str) -> Dict[str, Any]:
        """Get roster for a single team"""
        roster = {
            "players": [],
            "positions": {},
            "stats": {}
        }
        
        try:
            # Try to navigate to the team's roster page
            # CBS Sports typically has URLs like: /teams/{team_id}/roster
            # We'll try to find the team link first
            
            if self.driver:
                # Look for team links
                team_links = self.driver.find_elements(By.XPATH, f"//a[contains(text(), '{team_name}')]")
                if team_links:
                    # Click on the team link
                    team_links[0].click()
                    time.sleep(3)
                    
                    # Look for roster tab or roster information
                    roster_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'roster') or contains(@class, 'roster')]")
                    
                    for element in roster_elements:
                        try:
                            # Extract player information
                            player_text = element.text.strip()
                            if player_text and len(player_text) > 3:
                                # Simple parsing - this would need to be enhanced based on actual page structure
                                roster["players"].append({
                                    "name": player_text,
                                    "raw_text": player_text
                                })
                        except Exception as e:
                            logger.debug(f"Error parsing roster element: {e}")
                
        except Exception as e:
            logger.error(f"Error fetching roster for team {team_name}: {e}")
        
        return roster
    
    def close(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
        self.session.close()

def main():
    parser = argparse.ArgumentParser(description="CBS Sports Manual Login Integration")
    parser.add_argument("--league-id", required=True, help="CBS Sports league ID (subdomain)")
    parser.add_argument("--sport", default="hockey", choices=["hockey", "football", "baseball", "basketball"], 
                       help="Sport type")
    parser.add_argument("--output", help="Output file for exported data")
    parser.add_argument("--teams-only", action="store_true", help="Only fetch teams data")
    
    args = parser.parse_args()
    
    # Initialize CBS Sports integration
    cbs = CBSSportsManualLogin(args.league_id, args.sport)
    
    try:
        # Manual login
        if not cbs.manual_login():
            print("Manual login failed. Cannot proceed.")
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