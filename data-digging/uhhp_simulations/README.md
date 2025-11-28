# UHHP Fantasy Hockey League - Complete History Dataset

## 📊 Overview

This directory contains a comprehensive JSON dataset of the UHHP Fantasy Hockey League, covering **3 complete seasons** (2022-2025) with detailed action-by-action history for all 13 teams.

---

## 📁 Main Data File

### `uhhp_league_history_full.json` (859.4 KB)

Complete league history with:
- **League rules** (v 08.29) - Complete Owner's Manual structured data
- **3 seasons**: 2022-2023, 2023-2024, 2024-2025
- **13 teams** tracked across all seasons
- **1,599 total actions** recorded
- **87 rookies** identified and tracked
- **114 auction wins** with full bid data

---

## 📈 Data Coverage

### Season Statistics:

| Season | Total Actions | Auctions | Signings | Trades | Drops | Weekly Results | Rookies |
|--------|--------------|----------|----------|--------|-------|----------------|---------|
| **2022-2023** | 472 | 0 | 113 | 23 | 18 | 312 | 28 |
| **2023-2024** | 582 | 57 | 130 | 61 | 22 | 312 | 28 |
| **2024-2025** | 545 | 57 | 129 | 32 | 14 | 312 | 31 |

---

## 🎯 What's Included

### ✅ League Rules & Format
Complete Owner's Manual (v 08.29) structured into 21 sections:
- **Rosters**: Active, reserve, rookie requirements
- **Scoring**: Points for goals, assists, saves, wins, etc.
- **Playoffs**: Stanley Cup & Coke Cup brackets
- **Contracts**: Salary cap ($100), luxury tax rules
- **Draft**: Entry draft, auctions, RFA poaching
- **Payouts**: Prize money distribution
- **Full original text** included (9,513 characters)

### ✅ Complete Action History
Every action is timestamped and categorized:

1. **Auction Data** (2023-2024, 2024-2025)
   - Player nominated
   - Winner and winning bid
   - All team bids recorded
   - 57 auctions per season

2. **Transaction History**
   - Player signings with salary/term
   - Trades with full details
   - Player drops
   - Activations/roster moves

3. **Weekly Matchup Results**
   - All 26 weeks per season
   - Scores for both teams
   - Running win/loss records
   - Opponent information

4. **Final Rosters**
   - Active roster (15 players)
   - Reserve roster (unlimited)
   - Injured/Rookie roster
   - Salary cap totals

5. **Rookie Status** ✨
   - Entry draft picks identified
   - Rookie flag on players
   - Tracked across seasons

---

## 📝 Data Structure

```json
{
  "league_name": "UHHP Fantasy Hockey League",
  "league_rules": {
    "version": "v 08.29",
    "title": "Ultimate Hardcore Hockey League Owner's Manual 2024",
    "buy_in": "$120",
    "rosters": {...},
    "scoring": {...},
    "playoffs": {...},
    "contracts": {...},
    "draft_day": {...},
    "payouts": {...},
    "full_text": "..."
  },
  "seasons": {
    "2022-2023": {
      "teams": {
        "Team Name": {
          "gm": "GM Name",
          "actions": [
            {
              "timestamp": "2023-10-10T00:00:00Z",
              "type": "weekly_result",
              "opponent": "Opponent",
              "result": "W",
              "score_for": 85.2,
              "score_against": 79.8,
              "record": {"wins": 1, "losses": 0, "ties": 0}
            },
            {
              "timestamp": "2023-09-01T00:00:00Z",
              "type": "auction",
              "player": "Connor McDavid C",
              "nhl_team": "EDM",
              "winning_bid": 30,
              "bids": {"Team A": 25, "Team B": 28, ...}
            }
          ],
          "final_roster": {
            "active": [...],
            "reserve": [...],
            "injured": [
              {
                "name": "Rookie Name",
                "position": "C",
                "nhl_team": "TOR",
                "is_rookie": true
              }
            ],
            "totals": {
              "active_salary": 115,
              "total_salary": 123
            }
          }
        }
      }
    }
  }
}
```

---

## 🔍 Action Types

| Type | Description | Fields |
|------|-------------|--------|
| `auction` | Draft auction win | player, winner, winning_bid, bids, nominator |
| `auction_nomination` | Nominated player in auction | player, winner, winning_bid |
| `signing` | Free agent signing | player, position, nhl_team, salary, years |
| `trade` | Player trade | description, players involved |
| `drop` | Player dropped | player, position, nhl_team |
| `weekly_result` | Weekly matchup outcome | opponent, result, score_for, score_against, record |
| `activation` | Player activated to roster | player |
| `benched` | Player moved to bench | player |

---

## 🏆 League Teams (13)

1. **3sheets Sports Entertainment** - Michael Wong
2. **CinStars** - Sean Innes
3. **Doomsday Machine** - Ken Cor
4. **G' Stars** - Greg Dowell
5. **HawtSawwce** - Jeff Matsumiya
6. **LIP's Lasers** - Lorne Pearl
7. **New Oilers Nation** - Mark Henderson
8. **Shazam!!!** - David Foster
9. **South Calgary Oilers** - Ryan Bielefeld
10. **The Dook of Sook** - Nathan Krentz
11. **The Inglorious Basteeerds** - Chris Bache
12. **The Pylons** - Jeremy Greene
13. **re-degeneration X 2.0** - Ken and DK

---

## 📚 Analysis Scripts

### `analyze_competitive_balance.py`
Analyzes league competitive balance:
- Can you buy a championship?
- Can you buy to compete?
- Does transaction volume matter?
- Salary cap vs success correlation

### `analyze_rookie_draft.py`
Analyzes rookie draft strategy:
- Rookie holdings vs team success
- 3-year pipeline analysis
- Rebuild strategy effectiveness

### `build_league_json.py`
Main data processing script:
- Parses all source files (MD, CSV)
- Generates the JSON structure
- Validates data integrity

---

## 📖 Documentation

### `LEAGUE_RULES_INTEGRATION.md`
Complete guide to league rules structure in JSON (NEW!)

### `ROOKIE_ANALYSIS_SUMMARY.md`
Complete analysis of rookie draft strategies and outcomes

### `AUCTION_DATA_SUMMARY.md`
Detailed breakdown of auction spending and bidding patterns

### `League_format.md`
Official league rules and format (source document)

---

## 🎯 Key Findings

### Competitive Balance
- **3 different champions** in 3 seasons (no dynasty!)
- **9 of 13 teams** made playoffs all 3 seasons
- **Money helps but doesn't guarantee success**: Top 4 spenders average +5.5 wins in some seasons, but only +0.2 in others

### Rookie Strategy
- **Long-term investment**: Rookie-heavy teams underperform early, then catch up
- **3-year average**: Rookie-heavy teams +3.2 wins vs rookie-light teams
- **The Pylons**: 7.3 avg rookies/season, still made playoffs every year

### Transaction Activity
- **Less is often more**: Most active teams actually averaged FEWER wins in 2 of 3 seasons
- **2024-25 shift**: Transaction volume started correlating positively with success

### Auction Spending
- **$412 total** spent per season (57 players)
- **$7.20 average** per player
- **Strategies vary**: Volume buyers (8-9 players), Premium buyers (4-5 players), Value buyers (3-5 players)

---

## 🚀 Usage

### Loading the Data

```python
import json

with open('uhhp_league_history_full.json', 'r') as f:
    data = json.load(f)

# Access league rules
rules = data['league_rules']
print(f"League version: {rules['version']}")
print(f"Salary cap: ${rules['contracts']['salary_cap']['season_start_max']}")
print(f"Goals worth: {rules['scoring']['skaters']['goals']} points")

# Access specific team's data
team = data['seasons']['2023-2024']['teams']['CinStars']
print(f"GM: {team['gm']}")
print(f"Total actions: {len(team['actions'])}")

# Find all auctions
auctions = [a for a in team['actions'] if a['type'] == 'auction']
print(f"Auction wins: {len(auctions)}")

# Find rookies
rookies = [p for p in team['final_roster']['injured'] 
           if p.get('is_rookie', False)]
print(f"Rookies: {len(rookies)}")
```

---

## 📦 Source Files

### Transaction Data
- `2022_transactions.md`
- `2023_transactions.md`
- `2024_transactions.md`

### Weekly Results
- `2022_weekly.md`
- `2023_weekly.md`
- `2024_weekly.md`

### Final Rosters
- `2022_rosters.md`
- `2023_rosters.md`
- `2024_rosters.md`

### Auction Data
- `23_24 UHHP AUCTION TRACKER - Bids.csv`
- `24_25 UHHP AUCTION TRACKER - Bids.csv`
- `25_26 UHHP AUCTION TRACKER - Bids.csv` (for future use)

### Additional Files
- `2024_auction_results.md`
- `League_format.md`

---

## ✨ Status

### ✅ Complete Features
- [x] **League rules integrated** (v 08.29 Owner's Manual)
- [x] All transaction data parsed
- [x] Weekly matchup results
- [x] Final rosters with salary cap
- [x] Rookie status tracking
- [x] Auction bid data with full details
- [x] Comprehensive analysis scripts

### 🔜 Future Enhancements
- [ ] 2025-2026 season data (when available)
- [ ] Entry draft results (rookie draft picks)
- [ ] Playoff bracket outcomes
- [ ] Player performance statistics
- [ ] ROI analysis (auction value vs. performance)

---

## 📞 Contact

Generated for: **Mark Henderson** (New Oilers Nation)  
Date: November 2025  
Version: 1.0

---

**This dataset represents the most comprehensive history of the UHHP Fantasy Hockey League ever compiled!** 🏒🎉

