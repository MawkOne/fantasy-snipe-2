import requests
import json

# Fetch Standings for Nov 26, 2025
date = "2025-11-26"
url = f"https://api-web.nhle.com/v1/standings/{date}"

print(f"Fetching standings for {date}...")
resp = requests.get(url)
data = resp.json()

total_goals_so_far = 0
total_games_played = 0
teams_count = 0

standings = data.get('standings', [])

for team in standings:
    # goalsFor includes all goals scored by the team
    gf = team.get('goalFor', 0)
    gp = team.get('gamesPlayed', 0)
    
    total_goals_so_far += gf
    total_games_played += gp
    teams_count += 1

# Since "Games Played" sums games for both teams, Total Games = Total Games Played / 2
real_total_games = total_games_played / 2

print(f"\n--- Season Stats (as of {date}) ---")
print(f"Total Teams: {teams_count}")
print(f"Total Games Played: {int(real_total_games)}")
print(f"Total Goals Scored: {total_goals_so_far}")
if real_total_games > 0:
    print(f"Avg Goals per Game: {total_goals_so_far / real_total_games:.2f}")

# Project for full season
# 1312 games in a standard 32-team schedule
total_season_games = 1312
projected_goals = total_season_games * (total_goals_so_far / real_total_games)
print(f"\n--- Full Season Projection ---")
print(f"Projected Total Goals (1312 games): {int(projected_goals)}")

