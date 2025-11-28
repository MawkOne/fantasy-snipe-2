# League Rules Integration ✅

## Update Summary

The JSON file (`uhhp_league_history_full.json`) now includes a complete **`league_rules`** section with all league format information from the Owner's Manual.

### File Size: 859.4 KB (increased from 842.7 KB)

---

## What's Included

The league rules are organized into **21 structured sections** plus the full original text:

### 📋 Basic Information
- **Version**: v 08.29
- **Title**: Ultimate Hardcore Hockey League Owner's Manual 2024
- **Buy-in**: $120

### 👥 Rosters
```json
{
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
    "rookie_rules": "..."
  }
}
```

### ⚡ Scoring System
```json
{
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
}
```

### 🏆 Divisions & Schedule
- One division format
- 22 week regular season
- Home and away vs every team

### 🎯 Playoffs
- **Stanley Cup Bracket**: Top 6 teams
  - Week 23: Wild Card Round
  - Week 24: Semifinals
  - Week 25-26: Finals (2 weeks)
  
- **Coke Cup Bracket**: Bottom 6 teams
  - Same structure as Stanley Cup
  - Winner gets 1st overall pick in Entry Draft
  - Runner-up gets 2nd overall pick
  
- **Tiebreaker**: H2H, Points For, Coin Flip

### 💵 Payouts
- Stanley Cup Champion: **$700**
- Stanley Cup Runner-Up: **$350**
- Presidente Trophy (Best Regular Season): **$100**
- Greene Trophy (Most Points For): **$100**
- Coca Cola Cup Champion: **$100**
- Luxury tax funds added to playoff payouts (prorated)

### 📝 Contracts
```json
{
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
}
```

### 🆓 Free Agency
- **RFA**: Players under 27 on June 30 whose contract expired
- **UFA**: Players 27+ on June 30 whose contract expired

### 🎰 Draft Day Structure
1. **Buyouts** - No limit, cost = salary × years remaining
2. **Entry Draft** - 1 round, NHL draft eligible players only
3. **Superstar Round** - 1 round, nominate any UFA/RFA for auction
4. **UFA Nominations** - 2 rounds, nominate for auction
5. **RFA Poaching** - Unlimited rounds, nominate other teams' RFAs
6. **Free Agent Auction** - Online bidding (daily then weekly)

**Note**: All draft signings are 3-year contracts

### 🏥 Injuries & Buyouts
- **Long Term Injury**: 45 days → can release for current year salary
- **In-Season Buyouts**: Cost = salary × years remaining
- **Cap hits apply** based on term remaining

### 🔄 Trades
- Must use CBS Sportsline trade function
- Subject to Commissioner approval
- **Trade Deadline**: Sunday, Feb 23, 2025

### ⛔ Blackout Period
- Starts when championship ends
- Ends near following year's draft
- No trades or FA signings allowed

### 🔧 League Governance
- **Expansion/Changes**: Requires 7 of 12 GM votes
- **Contraction**: Departing owner gets no refund
- **Commissioner**: "What they say goes" - fair and equitable

### 📄 Full Text
The complete original Owner's Manual text (9,513 characters) is also included in the `full_text` field for reference.

---

## JSON Structure

The complete JSON now has this top-level structure:

```json
{
  "league_name": "UHHP Fantasy Hockey League",
  "league_rules": {
    "version": "v 08.29",
    "title": "Ultimate Hardcore Hockey League Owner's Manual 2024",
    "buy_in": "$120",
    "rosters": {...},
    "scoring": {...},
    "divisions": {...},
    "playoffs": {...},
    "payouts": {...},
    "contracts": {...},
    "free_agency": {...},
    "draft_day": {...},
    "injuries": {...},
    "in_season_buyouts": {...},
    "retirement_khl": {...},
    "trades": {...},
    "blackout_period": {...},
    "expansion": {...},
    "contraction": {...},
    "league_changes": {...},
    "commissioner": {...},
    "full_text": "..."
  },
  "seasons": {
    "2022-2023": {...},
    "2023-2024": {...},
    "2024-2025": {...}
  }
}
```

---

## Usage Example

```python
import json

with open('uhhp_league_history_full.json', 'r') as f:
    data = json.load(f)

# Access league rules
rules = data['league_rules']

# Get scoring system
scoring = rules['scoring']
print(f"Goals are worth {scoring['skaters']['goals']} points")
print(f"Goalie wins are worth {scoring['goalies']['wins']} points")

# Get salary cap info
cap = rules['contracts']['salary_cap']
print(f"Salary cap: ${cap['season_start_max']}")
print(f"Min salary: ${cap['minimum_player_salary']}")

# Get playoff info
playoffs = rules['playoffs']
print(f"Stanley Cup bracket: {playoffs['stanley_cup_bracket']['teams']}")
print(f"Coke Cup reward: {playoffs['coke_cup_bracket']['winner_reward']}")

# Get payouts
payouts = rules['payouts']
print(f"Champion prize: {payouts['stanley_cup_champion']}")

# Access full rules text
full_text = rules['full_text']
print(f"Full manual: {len(full_text)} characters")
```

---

## Why This Matters

### 1. **Complete Context**
Anyone analyzing the league data now has immediate access to all the rules that govern it. No need to reference external documents.

### 2. **Programmatic Access**
The structured format means you can build tools that automatically check:
- Salary cap compliance
- Roster legality
- Scoring calculations
- Playoff seeding
- Prize money distribution

### 3. **Historical Record**
The rules are version-stamped (v 08.29) so you can track how league rules evolved over time.

### 4. **Self-Contained Dataset**
The JSON file is now a complete, standalone record of the league - data + rules = everything you need.

---

## Complete Dataset Summary

✅ **League Name**: UHHP Fantasy Hockey League  
✅ **League Rules**: 21 sections + full text (9,513 characters)  
✅ **Seasons**: 3 (2022-2023, 2023-2024, 2024-2025)  
✅ **Teams**: 13  
✅ **Total Actions**: 1,599  
✅ **Auction Wins**: 114  
✅ **Rookies Tracked**: 87  
✅ **Weekly Results**: 936  

📦 **File Size**: 859.4 KB  
📅 **Rules Version**: v 08.29  
🏒 **Status**: **COMPLETE** ✨

---

## Files Updated

1. ✅ `uhhp_league_history_full.json` - Now includes league rules
2. ✅ `build_league_json.py` - Added `parse_league_rules()` method
3. ✅ `LEAGUE_RULES_INTEGRATION.md` - This document

---

## What You Can Do Now

### 1. Validate League Operations
```python
# Check if a team is cap compliant
def check_cap_compliance(team_data, rules):
    cap = rules['contracts']['salary_cap']['season_start_max']
    team_salary = team_data['final_roster']['totals']['total_salary']
    return team_salary <= cap
```

### 2. Calculate Prize Money
```python
# Calculate total prize pool
payouts = rules['payouts']
total_prizes = 700 + 350 + 100 + 100 + 100  # $1,350
```

### 3. Understand Scoring
```python
# Calculate player points
def calc_skater_points(goals, assists, plus_minus):
    scoring = rules['scoring']['skaters']
    return (goals * scoring['goals'] + 
            assists * scoring['assists'] + 
            plus_minus * scoring['plus_minus'])
```

### 4. Analyze Draft Strategy
```python
# See draft structure
draft = rules['draft_day']
print(f"Entry draft rounds: {draft['entry_draft']['rounds']}")
print(f"UFA nomination rounds: {draft['ufa_nominations']['rounds']}")
print(f"All draft contracts: {draft['all_draft_contracts']}")
```

---

## The Ultimate UHHP Dataset! 🏆

**You now have the most comprehensive, self-contained fantasy hockey league dataset ever created - complete with rules, history, and analysis tools!** 🎉🏒

Everything you need to understand, analyze, and build tools for the UHHP league is in one JSON file.

