#!/usr/bin/env python3
"""
Script to build comprehensive UHHP League History JSON from source files
"""

import json
import re
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class LeagueHistoryBuilder:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.league_data = {
            "league_name": "UHHP Fantasy Hockey League",
            "league_rules": {},
            "seasons": {}
        }
        
        # Team name to GM mapping
        # Note: "Doomsday Machine" was renamed to "re-degeneration X 2.0" after 2023-2024 season
        self.team_gms = {
            "3sheets Sports Entertainment": "Michael Wong",
            "CinStars": "Sean Innes",
            "G' Stars": "Greg Dowell",
            "HawtSawwce": "Jeff Matsumiya",
            "LIP's Lasers": "Lorne Pearl",
            "New Oilers Nation": "Mark Henderson",
            "re-degeneration X 2.0": "Ken and DK",  # Formerly "Doomsday Machine" (Ken Cor)
            "Shazam!!!": "David Foster",
            "South Calgary Oilers": "ryan bielefeld",
            "The Dook of Sook": "Nathan Krentz",
            "The Inglorious Basteeerds": "Chris Bache",
            "The Pylons": "Jeremy Greene"
        }
    
    def parse_date(self, date_str: str) -> str:
        """Convert date string to ISO format"""
        try:
            # Handle various date formats
            if "ET" in date_str:
                date_str = date_str.split(" ET")[0]
            
            # Try parsing
            for fmt in ["%m/%d/%y %I:%M %p", "%m/%d/%y %I:%M:%S %p", "%m/%d/%y"]:
                try:
                    dt = datetime.strptime(date_str.strip(), fmt)
                    return dt.isoformat() + "Z"
                except ValueError:
                    continue
            
            return date_str
        except Exception as e:
            print(f"Error parsing date {date_str}: {e}")
            return date_str
    
    def parse_transactions(self, year: str) -> Dict[str, List[Dict]]:
        """Parse transaction file for a given year"""
        filename = f"{year}_transactions.md"
        filepath = self.base_path / filename
        
        transactions_by_team = {}
        
        if not filepath.exists():
            print(f"Warning: {filename} not found")
            return transactions_by_team
        
        # Use csv.reader to handle multi-line quoted fields
        with open(filepath, 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                if len(row) < 3:
                    continue
                
                # Skip header rows
                if row[0].strip().startswith('Date') or row[0].strip().startswith('|'):
                    continue
                
                timestamp_raw = row[0].strip()
                if not timestamp_raw:
                    continue
                    
                team_name = self._normalize_team_name(row[1].strip())
                action_text = row[2].strip() if len(row) > 2 else ""
                
                if not action_text:
                    continue
                
                # Parse timestamp
                timestamp = self.parse_date(timestamp_raw)
                
                # Determine action type and parse accordingly
                transaction = self.parse_transaction_line(
                    timestamp, team_name, action_text
                )
                
                if transaction and team_name in self.team_gms:
                    if team_name not in transactions_by_team:
                        transactions_by_team[team_name] = []
                    
                    # Handle multiple actions
                    if "_multi" in transaction:
                        transactions_by_team[team_name].extend(transaction["_multi"])
                    else:
                        transactions_by_team[team_name].append(transaction)
        
        return transactions_by_team
    
    def parse_transaction_line(self, timestamp: str, team: str, text: str) -> Dict:
        """Parse individual transaction line - can return multiple actions"""
        
        # Handle multi-line actions (CSV reader removes quotes, but preserves newlines)
        if '\n' in text:
            # Multiple actions in one entry - return a special marker
            actions = []
            lines = text.split('\n')
            for line in lines:
                if line.strip():
                    action = self.parse_single_action(timestamp, team, line.strip())
                    if action:
                        actions.append(action)
            # Return marker for multiple actions
            if actions:
                return {"_multi": actions}
        
        # Single line action
        return self.parse_single_action(timestamp, team, text)
    
    def parse_single_action(self, timestamp: str, team: str, text: str) -> Dict:
        """Parse a single action line"""
        
        # Signing pattern
        if "Signed for" in text:
            # Try both • and | formats
            match = re.search(r"(.+?)\s+([CWDGF])\s+[•|]\s+(\w+).*Signed for \$(\d+)", text)
            if match:
                return {
                    "timestamp": timestamp,
                    "type": "signing",
                    "player": match.group(1).strip(),
                    "position": match.group(2),
                    "nhl_team": match.group(3),
                    "details": {
                        "salary": int(match.group(4)),
                        "years": 1
                    }
                }
        
        # Drop pattern (both formats)
        elif "Dropped" in text:
            # Special case for draft pick drops: "2025 Draft Pick TeamName C | - Dropped"
            if "Draft Pick" in text:
                match = re.search(r"(.+?)\s+([CWDGF])\s+\|", text)
                if match:
                    return {
                        "timestamp": timestamp,
                        "type": "drop",
                        "player": match.group(1).strip(),
                        "position": match.group(2),
                        "nhl_team": ""
                    }
            
            # Try pipe format first (2025+)
            match = re.search(r"(.+?)\s+([CWDGF])\s+\|\s+(\w+)", text)
            if not match:
                # Try bullet format (older)
                match = re.search(r"(.+?)\s+([CWDGF])\s+•\s+(\w+)", text)
            if match:
                return {
                    "timestamp": timestamp,
                    "type": "drop",
                    "player": match.group(1).strip(),
                    "position": match.group(2),
                    "nhl_team": match.group(3)
                }
        
        # Moved to IR pattern (2025+ format)
        elif "Moved to IR" in text and "Moved to" not in text.replace("Moved to IR", ""):
            match = re.search(r"(.+?)\s+([CWDGF])\s+\|\s+(\w+)", text)
            if match:
                return {
                    "timestamp": timestamp,
                    "type": "moved_to_ir",
                    "player": match.group(1).strip(),
                    "position": match.group(2),
                    "nhl_team": match.group(3)
                }
        
        # Trade pattern
        elif "Traded from" in text or "Traded to" in text:
            return {
                "timestamp": timestamp,
                "type": "trade",
                "description": text.strip()
            }
        
        # Activation/Benching (both formats)
        elif "Activated" in text or "Benched" in text:
            action_type = "activation" if "Activated" in text else "benched"
            # Try pipe format first
            match = re.search(r"(.+?)\s+([CWDGF])\s+\|\s+(\w+)", text)
            if not match:
                # Try bullet format
                match = re.search(r"(.+?)\s+([CWDGF])\s+•\s+(\w+)", text)
            if match:
                return {
                    "timestamp": timestamp,
                    "type": action_type,
                    "player": match.group(1).strip(),
                    "position": match.group(2),
                    "nhl_team": match.group(3)
                }
        
        return None
    
    def parse_weekly_results(self, year: str) -> Dict[str, List[Dict]]:
        """Parse weekly matchup results"""
        filename = f"{year}_weekly.md"
        filepath = self.base_path / filename
        
        results_by_team = {}
        
        if not filepath.exists():
            print(f"Warning: {filename} not found")
            return results_by_team
        
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        # Track current period and dates
        current_period = None
        current_dates = None
        current_standings = {}  # Track cumulative records
        parsing_standings_table = False  # Track when we're in the standings section
        standings_rank = 0  # Track rank position in standings table
        
        for line in lines:
            line = line.strip()
            
            # Check for period header
            if line.startswith('Period '):
                match = re.search(r'Period (\d+): (.+?) Matchups', line)
                if match:
                    current_period = int(match.group(1))
                    current_dates = match.group(2)
                    parsing_standings_table = False
                    standings_rank = 0
                    continue
            
            # Check for standings table header (after matchups)
            if line.startswith('W\t') and 'L\t' in line and 'T\t' in line and 'FPTS' in line:
                parsing_standings_table = True
                standings_rank = 0
                continue
            
            # Parse standings table entries
            if parsing_standings_table and '\t' in line and current_period:
                parts = line.split('\t')
                # Format: Team Name	W	L	T	FPTS
                if len(parts) >= 5:
                    team_name = parts[0].strip()
                    # Skip if it looks like a header or empty
                    if team_name and not team_name.startswith('W') and team_name in current_standings:
                        standings_rank += 1
                        # Update the standings for this team with rank
                        current_standings[team_name]["rank"] = standings_rank
                        
                        # Also update the most recent weekly result for this team with the rank
                        if team_name in results_by_team and results_by_team[team_name]:
                            # Find the most recent result for this period
                            for result in reversed(results_by_team[team_name]):
                                if result.get("period") == current_period:
                                    result["record"]["rank"] = standings_rank
                                    break
                continue
            
            # Check for matchup line (contains tab-separated data with scores)
            if '\t' in line and current_period:
                parts = line.split('\t')
                # Skip header lines and standings lines
                if len(parts) >= 3 and parts[0] and '(' in parts[0] and '-' in parts[2]:
                    teams_str = parts[0] + '\t' + parts[1]  # Combine first two parts
                    results_str = parts[2]
                    
                    # Extract teams and results - pattern: "Team1 (W)" and "Team2 (L)"
                    team_match = re.findall(r'(.+?)\s+\(([WL])\)', teams_str)
                    score_match = re.search(r'([\d.]+)\s*-\s*([\d.]+)', results_str)
                    
                    if len(team_match) == 2 and score_match:
                        team1, result1 = team_match[0]
                        team2, result2 = team_match[1]
                        team1 = team1.strip()
                        team2 = team2.strip()
                        score1 = float(score_match.group(1))
                        score2 = float(score_match.group(2))
                        
                        # Update standings
                        for team, result in [(team1, result1), (team2, result2)]:
                            if team not in current_standings:
                                current_standings[team] = {"wins": 0, "losses": 0, "ties": 0}
                            if result == 'W':
                                current_standings[team]["wins"] += 1
                            elif result == 'L':
                                current_standings[team]["losses"] += 1
                        
                        # Create timestamp from dates and period
                        # Format is like "10/7/22 - 10/16/22"
                        date_parts = current_dates.split(' - ')
                        if date_parts:
                            timestamp = self.parse_date(date_parts[0])
                        else:
                            timestamp = f"{year}-{current_period:02d}-01T00:00:00Z"
                        
                        # Add result for team1
                        if team1 not in results_by_team:
                            results_by_team[team1] = []
                        
                        results_by_team[team1].append({
                            "timestamp": timestamp,
                            "type": "weekly_result",
                            "period": current_period,
                            "dates": current_dates,
                            "opponent": team2,
                            "result": result1,
                            "score_for": score1,
                            "score_against": score2,
                            "record": dict(current_standings[team1])
                        })
                        
                        # Add result for team2
                        if team2 not in results_by_team:
                            results_by_team[team2] = []
                        
                        results_by_team[team2].append({
                            "timestamp": timestamp,
                            "type": "weekly_result",
                            "period": current_period,
                            "dates": current_dates,
                            "opponent": team1,
                            "result": result2,
                            "score_for": score2,
                            "score_against": score1,
                            "record": dict(current_standings[team2])
                        })
        
        return results_by_team
    
    def _normalize_team_name(self, team_name: str) -> str:
        """Normalize fantasy team name variations (from auction files, transactions, etc)"""
        # Strip and handle common variations
        team_name = team_name.strip()
        
        normalizations = {
            # 3sheets Sports Entertainment variations
            '3sSE': '3sheets Sports Entertainment',
            '3sheets': '3sheets Sports Entertainment',
            
            # CinStars variations
            'Cin': 'CinStars',
            
            # G' Stars variations
            'G': "G' Stars",
            
            # HawtSawwce variations
            'Hawt': 'HawtSawwce',
            
            # LIP's Lasers variations
            'LIP': "LIP's Lasers",
            
            # New Oilers Nation variations
            'NON': 'New Oilers Nation',
            
            # Shazam!!! variations
            'Shax': 'Shazam!!!',
            
            # South Calgary Oilers variations
            'SoCal': 'South Calgary Oilers',
            
            # The Dook of Sook variations
            'Dook': 'The Dook of Sook',
            
            # The Inglorious Basteeerds variations
            'Basteeerds': 'The Inglorious Basteeerds',
            
            # The Pylons variations
            'Pylons': 'The Pylons',
            
            # re-degeneration X 2.0 variations (formerly "Doomsday Machine")
            'Doomsday Machine': 're-degeneration X 2.0',
            'Dooms': 're-degeneration X 2.0',
            'Re-DeGen': 're-degeneration X 2.0',
            're-degeneration X': 're-degeneration X 2.0',
            'ReDeGen': 're-degeneration X 2.0',
            'DeGen': 're-degeneration X 2.0',
        }
        
        return normalizations.get(team_name, team_name)
    
    def _normalize_nhl_team(self, team_abbr: str) -> str:
        """Normalize NHL team abbreviations for relocated franchises"""
        normalizations = {
            'ARI': 'UTA',  # Arizona Coyotes -> Utah Hockey Club
        }
        return normalizations.get(team_abbr, team_abbr)
    
    def _parse_roster_section(self, roster_text: str) -> Dict:
        """Helper to parse a roster section"""
        import csv
        import io
        
        roster = {
            "active": [],
            "reserve": [],
            "injured": [],
            "totals": {}
        }
        
        # Use csv.reader to handle multi-line quoted fields properly
        reader = csv.reader(io.StringIO(roster_text), delimiter='\t')
        current_section = "active"
        
        for row in reader:
            if not row or len(row) < 2:
                continue
            
            # Skip header lines
            if 'Pos' in str(row) and ('Status' in str(row) or 'Players' in str(row)):
                continue
            
            # Check for section markers
            first_cell = row[0].strip() if row else ""
            if first_cell in ['Reserves', 'Reserve']:
                current_section = "reserve"
                continue
            elif first_cell in ['Injured', 'IR']:
                current_section = "injured"
                continue
            
            # Parse totals line
            if 'Active:' in ' '.join(row):
                match = re.search(r'Active:\s*(\d+)\s+Reserve:\s*(\d+)\s+Injured:\s*(\d+)\s+Active salary:\s*([\d.]+)\s+Total salary:\s*([\d.]+)', ' '.join(row), re.IGNORECASE)
                if match:
                    roster["totals"] = {
                        "active_count": int(match.group(1)),
                        "reserve_count": int(match.group(2)),
                        "injured_count": int(match.group(3)),
                        "active_salary": float(match.group(4)),
                        "total_salary": float(match.group(5))
                    }
                break
            
            # Try to parse player line - handle both old and new formats
            # New format (2025): 0=Pos, 1=Player, 8=salary, 9=Years, 10=Rookie
            # Old format (2022-2024): 0=player_info, 1=salary, 2=years, 3=rookie, 6=status, 7=pos
            
            if len(row) >= 11:
                # New format (2025)
                pos = row[0].strip()
                player_text = row[1].strip()
                salary = row[8].strip() if len(row) > 8 else ""
                years = row[9].strip() if len(row) > 9 else ""
                rookie = row[10].strip() if len(row) > 10 else ""
                
                # Parse player: "Name Pos | NHLTeam"
                if '|' in player_text and pos in ['C', 'W', 'F', 'D', 'G', 'LW', 'RW']:
                    parts = player_text.split('|')
                    name_and_pos = parts[0].strip()
                    nhl_team_part = parts[1].strip() if len(parts) > 1 else ""
                    nhl_team = nhl_team_part.split()[0] if nhl_team_part and nhl_team_part.split() else ""
                    
                    # Remove position suffix from name
                    name = re.sub(r'\s+(C|W|F|D|G|LW|RW)\s*$', '', name_and_pos).strip()
                    
                    player = {
                        "name": name,
                        "position": pos,
                        "nhl_team": nhl_team
                    }
                    
                    # Add salary and years if present
                    try:
                        if salary and float(salary) > 0:
                            player["salary"] = int(float(salary))
                    except:
                        pass
                    
                    try:
                        if years and int(float(years)) > 0:
                            player["years"] = int(float(years))
                    except:
                        pass
                    
                    # Add rookie status
                    if rookie == '1' or rookie == '2':
                        player["is_rookie"] = True
                    
                    roster[current_section].append(player)
            
            elif len(row) >= 8:
                # Old format (2022-2024)
                player_info = row[0].strip()
                salary = row[1].strip()
                years = row[2].strip()
                rookie = row[3].strip()
                status = row[6].strip()
                pos = row[7].strip()
                
                # Skip if empty or header
                if not player_info or player_info == 'Player':
                    continue
                
                # Determine section based on status
                if status == 'A':
                    current_section = "active"
                elif status == 'RS':
                    current_section = "reserve"
                elif status == 'I':
                    current_section = "injured"
                
                # Parse player name: "Name POS NHLTeam"
                name_match = re.match(r'(.+?)\s+(LW|RW|C|D|G|F)\s+(\w+)', player_info)
                if name_match:
                    player = {
                        "name": name_match.group(1).strip(),
                        "position": pos,
                        "nhl_team": name_match.group(3)
                    }
                    
                    if salary and salary.isdigit():
                        player["salary"] = int(salary)
                    if years.isdigit():
                        player["years"] = int(years)
                    if rookie == '1':
                        player["is_rookie"] = True
                    
                    roster[current_section].append(player)
        
        return roster if (roster["active"] or roster["reserve"] or roster["injured"]) else None
    
    def parse_rosters(self, year: str) -> Dict[str, Dict]:
        """Parse final roster file"""
        filename = f"{year}_rosters.md"
        filepath = self.base_path / filename
        
        rosters_by_team = {}
        
        if not filepath.exists():
            print(f"Warning: {filename} not found")
            return rosters_by_team
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Try format 1: "Team Name - GM Name" (older files)
        team_sections = re.split(r'^([^|].+?)\s+-\s+(.+?)$', content, flags=re.MULTILINE)
        
        if len(team_sections) <= 1:
            # Format 1 didn't work, try format 2: "Team Name Skaters" (2025 format)
            team_sections = re.split(r'^(.+?)\s+Skaters', content, flags=re.MULTILINE)
            # In this format: sections[0]=preamble, sections[1]=team1_name, sections[2]=team1_content, sections[3]=team2_name, etc.
            # Process pairs starting at index 1
            for i in range(1, len(team_sections), 2):
                team_name = self._normalize_team_name(team_sections[i].strip())
                roster_text = team_sections[i+1] if i+1 < len(team_sections) else ""
                
                if team_name not in self.team_gms:
                    continue
                
                roster = self._parse_roster_section(roster_text)
                if roster:
                    rosters_by_team[team_name] = roster
            
            return rosters_by_team
        
        # Process format 1 (Team - GM format)
        for i in range(1, len(team_sections), 3):
            team_name = self._normalize_team_name(team_sections[i].strip())
            gm_name = team_sections[i+1].strip() if i+1 < len(team_sections) else ""
            roster_text = team_sections[i+2] if i+2 < len(team_sections) else ""
            
            if team_name not in self.team_gms:
                continue
            
            roster = self._parse_roster_section(roster_text)
            if roster:
                rosters_by_team[team_name] = roster
        
        return rosters_by_team
    
    def parse_league_rules(self) -> Dict:
        """Parse league rules from League_format.md"""
        rules_file = self.base_path / "League_format.md"
        if not rules_file.exists():
            print("Warning: League_format.md not found")
            return {}
        
        with open(rules_file, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        rules = {
            "version": lines[0].strip() if lines else "Unknown",
            "title": lines[1].strip() if len(lines) > 1 else "Unknown",
            "buy_in": "$120",
            "rosters": {
                "active_roster": {
                    "goalies": 2,
                    "centres": 2,
                    "wingers": 3,
                    "forwards": 4,
                    "defense": 4,
                    "description": "These are the minimum requirements to qualify for play"
                },
                "reserve_roster": "No limit",
                "injury_roster": {
                    "description": "Houses rookies, future draft picks, and cap hits",
                    "rookie_rules": "No limit on rookie players. Only rookies from entry draft can be classified as rookies. Players on Rookie Contract cannot be dressed/accumulate points. Can be moved to active roster at $2 min salary for 3 year max term. Can be left as rookie for 3 years max. Once moved to active roster, cannot be sent down. Auto becomes UFA if unsigned after 3 years."
                }
            },
            "scoring": {
                "skaters": {
                    "goals": 3,
                    "assists": 2,
                    "plus_minus": 0.25,
                    "short_handed_goals": 2,
                    "shootout_goals": 1,
                    "penalty_minutes": 0,
                    "defenseman_assists_bonus": 1,
                    "defenseman_goals_bonus": 2
                },
                "goalies": {
                    "wins": 2,
                    "goals_against": -1.25,
                    "saves": 0.2,
                    "overtime_losses": 1,
                    "shootout_losses": 1,
                    "shutouts_bonus": 1
                }
            },
            "divisions": {
                "format": "All teams in one division",
                "regular_season_weeks": 22,
                "schedule": "Home and away game against every other team"
            },
            "playoffs": {
                "stanley_cup_bracket": {
                    "teams": "Top 6 teams",
                    "week_23_wildcard": "#3 v #6, #4 v #5",
                    "week_24_semifinals": "#1 v. Worst seed remaining; #2 v. Other",
                    "week_25_26_final": "Final 2 teams over 2 weeks"
                },
                "coke_cup_bracket": {
                    "teams": "Bottom 6 teams",
                    "week_23": "#9 v #12, #10 v #11",
                    "week_24_semifinals": "#7 v. Worst seed remaining; #8 v. Other",
                    "week_25_26_final": "Final 2 teams over 2 weeks",
                    "winner_reward": "1st overall pick in following year's entry draft",
                    "runner_up_reward": "2nd overall pick",
                    "bronze_winner": "3rd overall pick",
                    "bronze_runner_up": "4th overall pick"
                },
                "tiebreaker": "H2H, Points For, Coin Flip (in all tie break cases)",
                "draft_order": "Remaining picks based on reverse regular season standings"
            },
            "payouts": {
                "stanley_cup_champion": "$700",
                "stanley_cup_runner_up": "$350",
                "presidente_trophy": "$100 (Best Regular Season Record)",
                "greene_trophy": "$100 (Most Points For in Regular Season)",
                "coca_cola_cup_champion": "$100",
                "luxury_tax_note": "Commissioner takes luxury tax funds and adds to playoff payouts (not Presidente or Greene) on prorated basis"
            },
            "contracts": {
                "salary_cap": {
                    "season_start_max": 100,
                    "minimum_player_salary": 2,
                    "salary_format": "Whole numbers only",
                    "maximum_player_salary": "No maximum",
                    "luxury_tax": {
                        "1_5_over": "2x overage",
                        "6_25_over": "3x overage",
                        "26_50_over": "4x overage",
                        "over_50": "5x overage",
                        "note": "Applied if over 100 at playoff start date"
                    }
                },
                "term": {
                    "minimum": "1 year",
                    "maximum": "3 years"
                }
            },
            "free_agency": {
                "rfa": "Any player under age 27 on June 30 whose contract expired",
                "ufa": "Any player at or above age 27 on June 30 whose contract expired"
            },
            "draft_day": {
                "buyouts": {
                    "limit": "No limit on number of players",
                    "cost": "Annual salary × years remaining (real cash)",
                    "cap_hit_1yr": "No cap hit",
                    "cap_hit_2yr": "Half player's annual salary (rounded up) for 1 year",
                    "tradeable": "Whole cap hits are tradeable"
                },
                "entry_draft": {
                    "rounds": 1,
                    "eligible_players": "Only players drafted in NHL Entry Draft that year"
                },
                "superstar_round": {
                    "rounds": 1,
                    "format": "Owner nominates any available player (UFA or RFA) for auction"
                },
                "ufa_nominations": {
                    "rounds": 2,
                    "format": "Owner nominates available player for auction"
                },
                "rfa_poaching": {
                    "rounds": "Unlimited (until all owners tap out or RFAs exhausted)",
                    "format": "Nominate RFA from another owner's team for auction",
                    "matching_rights": "Original owner can match highest bid"
                },
                "all_draft_contracts": "All players signed during draft are on 3 year contracts",
                "free_agent_auction_online": {
                    "frequency": "Daily for first few days, then weekly after season starts",
                    "term": "One year deals ONLY",
                    "budget": "Based on remaining salary cap space"
                }
            },
            "injuries": {
                "long_term_injury": {
                    "eligibility": "Injured for 45 days",
                    "cost_to_release": "Current year salary (real cash)",
                    "cap_hit": "No cap hit",
                    "blackout": "Dropping owner cannot pick up player for 45 days",
                    "offseason_note": "If injured during offseason, 45 days begins at start of regular season"
                }
            },
            "in_season_buyouts": {
                "limit": "No limit",
                "cost": "Annual salary × years remaining (real cash)",
                "cap_hit_1yr": "Half player's annual salary (rounded up) for rest of current year",
                "cap_hit_2_3yr": "Half player's annual salary (rounded up) for rest of current year + 1 more year"
            },
            "retirement_khl": {
                "rule": "Can freely release player if they retire from NHL or go overseas (AHL not included)",
                "option": "Can keep player at contracted rate and term if desired"
            },
            "trades": {
                "process": "Must use CBS Sportsline trade function, subject to Commissioner approval",
                "trade_deadline": "Sunday, Feb 23, 2025",
                "pending_trades": "Trades pending on/before deadline will be processed",
                "post_deadline": "Offered but not accepted trades cancelled, no new trades allowed"
            },
            "blackout_period": {
                "start": "When championship game is over",
                "end": "Near following year's draft",
                "restrictions": "No trades or free agent signings permitted"
            },
            "expansion": {
                "approval": "Must be agreed upon by GMs, majority rules (7 of 12 minimum)"
            },
            "contraction": {
                "rule": "Departing owner receives no refund",
                "process": "Commissioner attempts to find new owner to take over team wholesale"
            },
            "league_changes": {
                "process": "Ideas proposed to League Competition Committee → discussed and analyzed → high graded ideas brought to League of GMs → GMs discuss and vote"
            },
            "commissioner": {
                "authority": "Commissioners rule the league. What they say goes.",
                "commitment": "Will endeavour to be fair and equitable to all owners"
            },
            "full_text": content
        }
        
        return rules
    
    def parse_auction_bids(self, season_label: str) -> Dict[str, List[Dict]]:
        """Parse auction bid data from CSV files"""
        # Map season labels to CSV filenames
        csv_mapping = {
            "2022-2023": None,  # No auction data for 2022-2023
            "2023-2024": "23_24 UHHP AUCTION TRACKER - Bids.csv",
            "2024-2025": "24_25 UHHP AUCTION TRACKER - Bids.csv",
            "2025-2026": "25_26 UHHP AUCTION TRACKER - Bids.csv"
        }
        
        filename = csv_mapping.get(season_label)
        if not filename:
            return {}
        
        filepath = self.base_path / filename
        if not filepath.exists():
            print(f"Warning: {filename} not found")
            return {}
        
        auction_by_team = {}
        
        with open(filepath, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        # Find the header row with "Pick,Player,Nominator,Winner" OR "OWNER,Winner"
        header_row_idx = None
        team_columns = {}
        
        for idx, row in enumerate(rows):
            # Check for both header formats
            if len(row) > 3:
                # Format 1: "Pick,Player,Nominator,Winner,..."
                if row[0] == 'Pick' and 'Player' in row[1]:
                    header_row_idx = idx
                    # Map team names to column indices
                    for col_idx, header in enumerate(row):
                        normalized_team = self._normalize_team_name(header.strip())
                        # Only store if it's actually a team name (not Pick, Player, etc)
                        if normalized_team != header.strip() or normalized_team in self.team_gms:
                            team_columns[col_idx] = normalized_team
                    break
                # Format 2: ",,OWNER,Winner,..." (23_24 format)
                elif 'OWNER' in row and 'Winner' in row:
                    header_row_idx = idx
                    # Map team names to column indices (starting from column 5)
                    for col_idx in range(5, len(row)):
                        header = row[col_idx].strip()
                        normalized_team = self._normalize_team_name(header)
                        # Only store if it's a valid team name
                        if normalized_team != header or normalized_team in self.team_gms:
                            team_columns[col_idx] = normalized_team
                    break
        
        if header_row_idx is None:
            print(f"Warning: Could not find header row in {filename}")
            return {}
        
        # Parse auction data
        for row in rows[header_row_idx + 1:]:
            if len(row) < 4:
                continue
            
            pick = row[0].strip()
            if not pick or not re.match(r'\d+\.\d+', pick):
                continue
            
            player_info = row[1].strip()
            nominator = row[2].strip() if len(row) > 2 else ""
            winner_field = row[3].strip() if len(row) > 3 else ""
            
            # Parse player name and position
            if ' | ' in player_info:
                player_name, nhl_team = player_info.split(' | ')
            else:
                player_name = player_info
                nhl_team = ""
            
            # Determine winner and winning bid based on format
            # Format 1: Winner field contains team name and bid (e.g., "3sheets,$14")
            # Format 2: Winner field is just bid (e.g., "$14") and nominator is winner
            winning_bid = 0
            winner_normalized = None
            
            if ',' in winner_field:
                # Format 1: "TeamName,$Amount"
                parts = winner_field.split(',')
                winner = parts[0].strip()
                if len(parts) > 1:
                    bid_match = re.search(r'\$?(\d+)', parts[1])
                    if bid_match:
                        winning_bid = int(bid_match.group(1))
                # Normalize winner name
                winner_normalized = self._normalize_team_name(winner)
            else:
                # Format 2: Winner field is just the bid, nominator is the winner
                bid_match = re.search(r'\$?(\d+)', winner_field)
                if bid_match:
                    winning_bid = int(bid_match.group(1))
                # Nominator is the winner (default assumption for 23_24 format)
                winner_normalized = self._normalize_team_name(nominator)
            
            # Normalize nominator name
            nominator_normalized = self._normalize_team_name(nominator)
            
            # Don't create artificial timestamps - auction CSV doesn't have dates
            # Create auction action
            auction_action = {
                "type": "auction",
                "pick": pick,
                "player": player_name,
                "nhl_team": nhl_team,
                "nominator": nominator_normalized,
                "winner": winner_normalized,
                "winning_bid": winning_bid,
                "bids": {}
            }
            
            # Collect all team bids
            for col_idx, team_name in team_columns.items():
                if col_idx < len(row):
                    bid_value = row[col_idx].strip()
                    # Parse bid (could be number, $X, or text)
                    if bid_value and bid_value not in ['', 'cannot bid', '0', 'NO', ':(', 'Mashy', 'lollzzz', 'fuck u', 'washed', 'costco', 'Machine learning']:
                        bid_match = re.search(r'[-]?\$?(\d+)', bid_value)
                        if bid_match:
                            auction_action["bids"][team_name] = int(bid_match.group(1))
            
            # Add action to winner's team
            if winner_normalized and winner_normalized in self.team_gms:
                if winner_normalized not in auction_by_team:
                    auction_by_team[winner_normalized] = []
                auction_by_team[winner_normalized].append(auction_action)
            
            # Also add as "nomination" action to nominator if different
            if nominator_normalized and nominator_normalized != winner_normalized and nominator_normalized in self.team_gms:
                nomination_action = {
                    "type": "auction_nomination",
                    "pick": pick,
                    "player": player_name,
                    "nhl_team": nhl_team,
                    "winner": winner_normalized,
                    "winning_bid": winning_bid
                }
                if nominator_normalized not in auction_by_team:
                    auction_by_team[nominator_normalized] = []
                auction_by_team[nominator_normalized].append(nomination_action)
        
        return auction_by_team
    
    def build_season(self, year: str, season_label: str):
        """Build complete season data"""
        print(f"Building {season_label}...")
        
        # Parse all data sources
        transactions = self.parse_transactions(year)
        weekly_results = self.parse_weekly_results(year)
        rosters = self.parse_rosters(year)
        auction_data = self.parse_auction_bids(season_label)
        
        # Determine draft date and commissioner processing period based on season
        if season_label == "2025-2026":
            draft_date = "2025-09-08"
            comm_start = "2025-09-08T16:32:00Z"
            comm_end = "2025-09-16T23:00:00Z"
            waiver_start = "2025-09-16T23:00:00Z"
            season_start = "2025-10-07"
        elif season_label == "2024-2025":
            # Week 1: 10/4/24 - Waivers on 10/4-5 at 7:55 AM (pre-game)
            draft_date = f"{year}-09-01"
            comm_start = f"{year}-09-01T12:00:00Z"
            comm_end = f"{year}-09-15T23:00:00Z"
            waiver_start = f"{year}-09-15T23:00:00Z"
            season_start = f"{year}-10-05T12:00:00Z"  # After 10/5 7:55 AM waivers
        elif season_label == "2023-2024":
            # Week 1: 10/10/23 - Waivers on 10/15 at 4:02 AM (pre-Week 1)
            draft_date = f"{year}-09-01"
            comm_start = f"{year}-09-01T12:00:00Z"
            comm_end = f"{year}-09-15T23:00:00Z"
            waiver_start = f"{year}-09-15T23:00:00Z"
            season_start = f"{year}-10-15T12:00:00Z"  # After 10/15 4:02 AM waivers
        elif season_label == "2022-2023":
            # Week 1: 10/7/22 - Waivers on 10/8-9 at 3:40 AM (pre-game)
            draft_date = f"{year}-09-01"
            comm_start = f"{year}-09-01T12:00:00Z"
            comm_end = f"{year}-09-15T23:00:00Z"
            waiver_start = f"{year}-09-15T23:00:00Z"
            season_start = f"{year}-10-09T12:00:00Z"  # After 10/9 3:40 AM waivers
        else:
            # Default dates for older seasons (approximate)
            draft_date = f"{year}-09-01"
            comm_start = f"{year}-09-01T12:00:00Z"
            comm_end = f"{year}-09-15T23:00:00Z"
            waiver_start = f"{year}-09-15T23:00:00Z"
            season_start = f"{year}-10-07"
        
        # Build season structure with stage metadata aligned to league rules
        season_data = {
            "stages": {
                "0_buyout_window": {
                    "name": "Post-Entry Draft Cleanup",
                    "description": "Commissioner maintenance period after entry draft and before auction. Rosters are adjusted for cap compliance and rookie assignments.",
                    "period": {"start": f"{year}-08-15", "end": draft_date},
                    "contract_term": "n/a",
                    "decision_maker": "commissioner",
                    "teams": {}
                },
                "1_entry_draft": {
                    "name": "Entry Draft (Rookies)",
                    "description": "1 round draft of players from current year's NHL Entry Draft",
                    "date": draft_date,
                    "rounds": 1,
                    "contract_term": "3 years",
                    "decision_maker": "gm",
                    "teams": {}
                },
                "2_free_agent_auction": {
                    "name": "Free Agent Auction",
                    "description": "Offline auction: Superstar Round (1), UFA Nominations (2 rounds), RFA Poaching (unlimited rounds)",
                    "date": draft_date,
                    "rounds": "3+ (1 Superstar, 2 UFA, unlimited RFA)",
                    "contract_term": "3 years",
                    "decision_maker": "gm",
                    "teams": {}
                },
                "3_commissioner_processing": {
                    "name": "Commissioner Processing",
                    "description": "Commissioner processes drops for cap compliance, IR moves, and post-draft cleanup",
                    "period": {"start": comm_start, "end": comm_end},
                    "decision_maker": "commissioner",
                    "teams": {}
                },
                "4_free_agent_auction_online": {
                    "name": "Free Agent Auction Online",
                    "description": "Daily waivers for pre-season free agent signings (1 year deals only)",
                    "period": {"start": waiver_start, "end": f"{year}-10-06T23:59:59Z"},
                    "contract_term": "1 year only",
                    "decision_maker": "gm",
                    "teams": {}
                },
                "5_regular_season": {
                    "name": "Regular Season",
                    "description": "22 weeks of head-to-head matchups with weekly free agent auctions",
                    "period": {"start": season_start, "end": f"{int(year)+1}-03-31"},
                    "weeks": 22,
                    "decision_maker": "mixed",
                    "teams": {}
                },
                "6_playoffs": {
                    "name": "Playoffs",
                    "description": "Dual-bracket elimination tournament. Top 6 teams compete for Championship (seeds 1-2 get bye). Bottom 6 teams play Consolation bracket.",
                    "period": {"start": f"{int(year)+1}-03-24", "end": f"{int(year)+1}-04-18"},
                    "weeks": 4,
                    "structure": {
                        "championship_bracket": {
                            "teams": "Top 6 finishers (seeds 1-6)",
                            "prize": "League Championship",
                            "rounds": {
                                "week_23": "Wildcard Round - Seeds 3-6 play (seeds 1-2 get bye)",
                                "week_24": "Semifinals - Seeds 1-2 play wildcard winners",
                                "weeks_25_26": "Finals - 2-week championship (best of 2)"
                            }
                        },
                        "consolation_bracket": {
                            "teams": "Bottom 6 finishers (seeds 7-12)",
                            "prize": "Consolation bracket winner",
                            "rounds": {
                                "week_23": "Wildcard Round - Seeds 9-12 play (seeds 7-8 get bye)",
                                "week_24": "Semifinals - Seeds 7-8 play wildcard winners",
                                "weeks_25_26": "Finals - 2-week consolation final"
                            }
                        }
                    },
                    "decision_maker": "mixed",
                    "teams": {}
                }
            }
        }
        
        # Helper function to categorize actions by stage and add decision_maker
        def get_stage_and_annotate(action):
            timestamp = action.get("timestamp", "9999-99-99T99:99:99Z")
            action_type = action.get("type", "")
            
            # Add decision_maker field to action
            if action_type == "auction" or action_type == "auction_nomination":
                action["decision_maker"] = "gm"
                # All auction actions go to stage 2 (Free Agent Auction)
                return "2_free_agent_auction"
            elif action_type in ["drop", "activation", "moved_to_ir", "benched"]:
                # Pre-auction (before draft_date) = Commissioner maintenance/post-entry-draft cleanup
                if timestamp < draft_date:
                    action["decision_maker"] = "commissioner"
                    if action_type == "drop":
                        action["reason"] = "post_entry_draft_cleanup"
                        action["note"] = "Commissioner maintenance: roster cleanup after entry draft, before auction"
                    elif action_type in ["activation", "moved_to_ir", "signing"]:
                        action["reason"] = "post_entry_draft_adjustment"
                        action["note"] = "Commissioner maintenance: roster adjustments after entry draft"
                    return "0_buyout_window"
                # Post-auction, pre-waiver = Commissioner Processing
                elif timestamp < waiver_start:
                    action["decision_maker"] = "commissioner"
                    # Add reason for commissioner drops
                    if action_type == "drop":
                        action["reason"] = "cap_compliance"
                        action["note"] = "Post-draft cleanup"
                    elif action_type == "activation":
                        action["note"] = "Moving from IR to active roster"
                    return "3_commissioner_processing"
                # Post-waiver = Regular Season
                else:
                    action["decision_maker"] = "commissioner"
                    if action_type == "drop":
                        action["reason"] = "qualified_injury"
                        action["note"] = "Qualified injury drop per league rules"
                    return "5_regular_season"
            elif action_type == "trade":
                action["decision_maker"] = "gm"
                if timestamp < waiver_start:
                    action["note"] = "Pre-season trade"
                    return "3_commissioner_processing"
                else:
                    action["note"] = "In-season trade"
                    return "5_regular_season"
            elif action_type == "signing":
                action["decision_maker"] = "gm"
                if timestamp < season_start:
                    action["note"] = "Pre-season waiver signing (1 year deal)"
                    return "4_free_agent_auction_online"
                else:
                    action["note"] = "In-season waiver pickup (1 year deal)"
                    return "5_regular_season"
            elif action_type == "weekly_result":
                action["decision_maker"] = None
                # Playoff weeks (23-26) go to playoffs stage
                period = action.get("period", 0)
                if period > 22:
                    return "6_playoffs"
                else:
                    return "5_regular_season"
            else:
                action["decision_maker"] = "gm"
                return "5_regular_season"
        
        # Process all teams
        all_teams = set(self.team_gms.keys())
        
        for team_name in all_teams:
            # Initialize team data for each stage
            for stage_name in season_data["stages"].keys():
                season_data["stages"][stage_name]["teams"][team_name] = {
                    "gm": self.team_gms[team_name],
                    "actions": []
                }
            
            # Collect all actions for this team
            all_actions = []
            
            if team_name in auction_data:
                all_actions.extend(auction_data[team_name])
            if team_name in transactions:
                all_actions.extend(transactions[team_name])
            if team_name in weekly_results:
                all_actions.extend(weekly_results[team_name])
            
            # Distribute actions to appropriate stages and annotate
            for action in all_actions:
                stage = get_stage_and_annotate(action)
                season_data["stages"][stage]["teams"][team_name]["actions"].append(action)
            
            # Sort actions within each stage
            for stage_name in season_data["stages"].keys():
                stage_actions = season_data["stages"][stage_name]["teams"][team_name]["actions"]
                
                if stage_name == "0_buyout_window":
                    # Sort by timestamp
                    stage_actions.sort(key=lambda a: a.get("timestamp", "9999-99-99"))
                elif stage_name == "1_entry_draft":
                    # Entry draft - would sort by pick number if we had that data
                    stage_actions.sort(key=lambda a: a.get("pick", "99.99"))
                elif stage_name == "2_free_agent_auction":
                    # Sort by pick number for auctions
                    stage_actions.sort(key=lambda a: a.get("pick", "99.99"))
                elif stage_name == "5_regular_season":
                    # Sort by period for weekly results, then timestamp
                    def season_sort(a):
                        if a.get("type") == "weekly_result" and "period" in a:
                            return f"0-{a['period']:03d}"
                        return f"1-{a.get('timestamp', '9999')}"
                    stage_actions.sort(key=season_sort)
                elif stage_name == "6_playoffs":
                    # Sort by period for playoff weeks
                    stage_actions.sort(key=lambda a: a.get("period", 99))
                else:
                    # Sort by timestamp
                    stage_actions.sort(key=lambda a: a.get("timestamp", "9999-99-99"))
                
                # Calculate stage summaries
                stage_summary = {}
                
                if stage_name == "0_buyout_window":
                    # Post-entry draft cleanup summary
                    drops = [a for a in stage_actions if a.get("type") == "drop"]
                    moves_to_ir = [a for a in stage_actions if a.get("type") == "moved_to_ir"]
                    activations = [a for a in stage_actions if a.get("type") == "activation"]
                    
                    stage_summary["drops"] = len(drops)
                    stage_summary["moved_to_ir"] = len(moves_to_ir)
                    stage_summary["activations"] = len(activations)
                
                elif stage_name == "1_entry_draft":
                    # Entry draft summary
                    rookies = [a for a in stage_actions if a.get("type") == "draft"]
                    stage_summary["rookies_drafted"] = len(rookies)
                
                elif stage_name == "2_free_agent_auction":
                    auctions = [a for a in stage_actions if a.get("type") == "auction"]
                    stage_summary["players_acquired"] = len(auctions)
                    stage_summary["total_spent"] = sum(a.get("winning_bid", 0) for a in auctions)
                
                elif stage_name == "3_commissioner_processing":
                    drops = [a for a in stage_actions if a.get("type") == "drop"]
                    activations = [a for a in stage_actions if a.get("type") == "activation"]
                    trades = [a for a in stage_actions if a.get("type") == "trade"]
                    commissioner_actions = [a for a in stage_actions if a.get("decision_maker") == "commissioner"]
                    gm_decisions = [a for a in stage_actions if a.get("decision_maker") == "gm"]
                    
                    stage_summary["drops"] = len(drops)
                    stage_summary["activations"] = len(activations)
                    stage_summary["trades"] = len(trades)
                    stage_summary["commissioner_actions"] = len(commissioner_actions)
                    stage_summary["gm_decisions"] = len(gm_decisions)
                
                elif stage_name == "4_free_agent_auction_online":
                    signings = [a for a in stage_actions if a.get("type") == "signing"]
                    stage_summary["signings"] = len(signings)
                    stage_summary["total_spent"] = sum(a.get("salary", 0) for a in signings)
                
                elif stage_name == "5_regular_season":
                    weekly = [a for a in stage_actions if a.get("type") == "weekly_result"]
                    wins = len([w for w in weekly if w.get("result") == "W"])
                    losses = len([w for w in weekly if w.get("result") == "L"])
                    signings = [a for a in stage_actions if a.get("type") == "signing"]
                    drops = [a for a in stage_actions if a.get("type") == "drop"]
                    
                    stage_summary["wins"] = wins
                    stage_summary["losses"] = losses
                    stage_summary["waiver_pickups"] = len(signings)
                    stage_summary["commissioner_drops"] = len(drops)
                    
                    # Try to get points_for from weekly results
                    points_for = 0
                    for w in weekly:
                        score = w.get("score", "")
                        if " - " in score:
                            try:
                                points_for += float(score.split(" - ")[0])
                            except:
                                pass
                    if points_for > 0:
                        stage_summary["points_for"] = round(points_for, 1)
                
                elif stage_name == "6_playoffs":
                    weekly = [a for a in stage_actions if a.get("type") == "weekly_result"]
                    
                    # Filter for REAL games only (not TBA, must have real opponent and score)
                    real_games = [w for w in weekly if w.get('opponent') != 'TBA' and w.get('score_against', 0) > 0]
                    real_wins = len([w for w in real_games if w.get("result") == "W"])
                    real_losses = len([w for w in real_games if w.get("result") == "L"])
                    
                    stage_summary["playoff_wins"] = real_wins
                    stage_summary["playoff_losses"] = real_losses
                    stage_summary["real_games_played"] = len(real_games)
                    stage_summary["total_rounds"] = len(weekly)
                    
                    # Determine bracket based on final regular season standing
                    # Get final regular season rank for this team
                    reg_team_data = season_data["stages"]["5_regular_season"]["teams"].get(team_name, {})
                    reg_actions = reg_team_data.get("actions", [])
                    final_weekly = [a for a in reg_actions if a.get("type") == "weekly_result"]
                    
                    final_rank = None
                    if final_weekly:
                        last_week = final_weekly[-1]
                        final_rank = last_week.get("record", {}).get("rank", 0)
                    
                    # Determine bracket: Top 6 = Championship, Bottom 6 = Consolation
                    if final_rank and final_rank <= 6:
                        stage_summary["bracket"] = "Championship"
                        stage_summary["seed"] = final_rank
                        
                        # Check if team made it to finals (weeks 25-26)
                        finals_games = [w for w in real_games if w.get('period') in [25, 26]]
                        
                        # Championship bracket results
                        if len(real_games) == 0:
                            # Eliminated before playing any real games
                            if len(weekly) >= 2:
                                stage_summary["result"] = "Championship Semifinals (eliminated)"
                            elif len(weekly) >= 1:
                                stage_summary["result"] = "Championship Wildcard (eliminated)"
                            else:
                                stage_summary["result"] = "Did not compete"
                        elif len(finals_games) >= 2:
                            # Made it to finals - determine winner by aggregate score
                            total_for = sum(w.get('score_for', 0) for w in finals_games)
                            total_against = sum(w.get('score_against', 0) for w in finals_games)
                            
                            stage_summary["finals_aggregate_for"] = round(total_for, 1)
                            stage_summary["finals_aggregate_against"] = round(total_against, 1)
                            
                            if total_for > total_against:
                                stage_summary["result"] = "League Champion"
                            elif total_against > total_for:
                                stage_summary["result"] = "Championship Finals (Runner-up)"
                            else:
                                # Tie - shouldn't happen but handle it
                                stage_summary["result"] = "Championship Finals (Tied)"
                        elif len(finals_games) == 1:
                            # Only played one finals game (odd scenario)
                            if finals_games[0].get('result') == 'W':
                                stage_summary["result"] = "League Champion"
                            else:
                                stage_summary["result"] = "Championship Finals (Runner-up)"
                        elif real_losses == 0:
                            # Won all games but didn't reach finals (shouldn't happen)
                            stage_summary["result"] = "Championship Semifinals (eliminated)"
                        else:
                            # Lost before finals
                            if len(real_games) >= 2:
                                stage_summary["result"] = "Championship Semifinals (eliminated)"
                            elif len(real_games) >= 1:
                                stage_summary["result"] = "Championship Wildcard (eliminated)"
                            else:
                                stage_summary["result"] = "Did not compete"
                            
                    elif final_rank and final_rank <= 12:
                        stage_summary["bracket"] = "Consolation"
                        stage_summary["seed"] = final_rank
                        
                        # Check if team made it to finals (weeks 25-26)
                        finals_games = [w for w in real_games if w.get('period') in [25, 26]]
                        
                        # Consolation bracket results
                        if len(real_games) == 0:
                            # Eliminated before playing any real games
                            if len(weekly) >= 2:
                                stage_summary["result"] = "Consolation Semifinals (eliminated)"
                            elif len(weekly) >= 1:
                                stage_summary["result"] = "Consolation Wildcard (eliminated)"
                            else:
                                stage_summary["result"] = "Did not compete"
                        elif len(finals_games) >= 2:
                            # Made it to finals - determine winner by aggregate score
                            total_for = sum(w.get('score_for', 0) for w in finals_games)
                            total_against = sum(w.get('score_against', 0) for w in finals_games)
                            
                            stage_summary["finals_aggregate_for"] = round(total_for, 1)
                            stage_summary["finals_aggregate_against"] = round(total_against, 1)
                            
                            if total_for > total_against:
                                stage_summary["result"] = "Consolation Champion"
                            elif total_against > total_for:
                                stage_summary["result"] = "Consolation Finals (Runner-up)"
                            else:
                                # Tie - shouldn't happen but handle it
                                stage_summary["result"] = "Consolation Finals (Tied)"
                        elif len(finals_games) == 1:
                            # Only played one finals game (odd scenario)
                            if finals_games[0].get('result') == 'W':
                                stage_summary["result"] = "Consolation Champion"
                            else:
                                stage_summary["result"] = "Consolation Finals (Runner-up)"
                        elif real_losses == 0:
                            # Won all games but didn't reach finals
                            stage_summary["result"] = "Consolation Semifinals (eliminated)"
                        else:
                            # Lost before finals
                            if len(real_games) >= 2:
                                stage_summary["result"] = "Consolation Semifinals (eliminated)"
                            elif len(real_games) >= 1:
                                stage_summary["result"] = "Consolation Wildcard (eliminated)"
                            else:
                                stage_summary["result"] = "Did not compete"
                    else:
                        stage_summary["bracket"] = "Unknown"
                        stage_summary["result"] = "Did not qualify"
                
                if stage_summary:
                    season_data["stages"][stage_name]["teams"][team_name]["stage_summary"] = stage_summary
            
            # Add final roster to regular season stage
            if team_name in rosters:
                season_data["stages"]["5_regular_season"]["teams"][team_name]["final_roster"] = rosters[team_name]
        
        # Extract NEW rookies (years_remaining = 3) from final rosters and add to entry draft stage
        # Also check for draft pick drops (e.g., "2025 Draft Pick TeamName" being dropped)
        pick_number = 1
        draft_year = season_label.split('-')[0]  # e.g., "2025" from "2025-2026"
        
        for team_name in all_teams:
            if team_name not in rosters:
                continue
            
            roster = rosters[team_name]
            team_rookies = []
            
            # Check all roster categories for NEW rookies (3 years remaining = just drafted)
            for category in ['active', 'reserve', 'injured']:
                for player in roster.get(category, []):
                    if player.get('is_rookie') and player.get('years') == 3:
                        team_rookies.append({
                            "type": "entry_draft_pick",
                            "pick": pick_number,
                            "player": player.get('name'),
                            "position": player.get('position'),
                            "nhl_team": player.get('nhl_team'),
                            "years_remaining": player.get('years'),
                            "status": category,
                            "decision_maker": "gm"
                        })
                        pick_number += 1
            
            # Also check for draft pick asset drops (e.g., "2025 Draft Pick TeamName" dropped = pick used)
            # Draft picks can be traded, so the team that DROPS the pick is the team that USED it
            # Example: If "The Dook of Sook" drops "2025 Draft Pick NON", 
            #          The Dook made the pick (using a pick they traded for from NON)
            if team_name in transactions:
                draft_picks_found = []
                for txn in transactions[team_name]:
                    if txn.get('type') == 'drop':
                        player_name = txn.get('player', '')
                        # Check if this is a draft pick asset for the current draft year
                        if f"{draft_year} Draft Pick" in player_name and player_name not in draft_picks_found:
                            draft_picks_found.append(player_name)
                
                # Each draft pick drop represents one selection in the entry draft
                # We need to account for picks beyond the rookies on roster
                picks_needed = max(0, len(draft_picks_found) - len(team_rookies))
                
                for i in range(picks_needed):
                    # Get the draft pick that corresponds to this additional pick
                    pick_index = len(team_rookies) + i
                    if pick_index < len(draft_picks_found):
                        draft_pick_name = draft_picks_found[pick_index]
                        team_rookies.append({
                            "type": "entry_draft_pick",
                            "pick": pick_number,
                            "player": f"Draft Pick Used",
                            "position": "Unknown",
                            "nhl_team": "",
                            "years_remaining": 3,
                            "status": "pick_used",
                            "decision_maker": "gm",
                            "note": f"Draft pick asset dropped: {draft_pick_name}. Player may have been immediately activated to non-rookie contract, traded, or dropped."
                        })
                        pick_number += 1
            
            # Add to entry draft stage
            season_data["stages"]["1_entry_draft"]["teams"][team_name]["actions"].extend(team_rookies)
            
            # Update entry draft summary
            season_data["stages"]["1_entry_draft"]["teams"][team_name]["stage_summary"]["rookies_drafted"] = len(team_rookies)
        
        self.league_data["seasons"][season_label] = season_data
    
    def build(self):
        """Build complete league history"""
        print("Parsing league rules...")
        self.league_data["league_rules"] = self.parse_league_rules()
        
        self.build_season("2022", "2022-2023")
        self.build_season("2023", "2023-2024")
        self.build_season("2024", "2024-2025")
        self.build_season("2025", "2025-2026")
    
    def save(self, output_file: str = "uhhp_league_history_full.json"):
        """Save to JSON file"""
        output_path = self.base_path / output_file
        with open(output_path, 'w') as f:
            json.dump(self.league_data, f, indent=2)
        print(f"Saved to {output_path}")
        print(f"File size: {output_path.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    builder = LeagueHistoryBuilder()
    builder.build()
    builder.save()
    print("Done!")

