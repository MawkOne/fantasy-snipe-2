import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.nhl.com/"
}

def check_season(season_year):
    # Try a random game from that season (approximate ID logic)
    # Standard Game ID: YYYY02xxxx (02 = Regular Season)
    # Let's try game 0001 (First game of season)
    game_id = f"{season_year}020001"
    
    print(f"\nChecking Season {season_year}-{season_year+1} (Game {game_id})...")
    
    # 1. Get PBP
    pbp_url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"
    try:
        resp = requests.get(pbp_url)
        if resp.status_code != 200:
            print(f"  -> PBP Not Found (Status {resp.status_code})")
            return False
            
        data = resp.json()
        
        # 2. Find a Goal
        goal = next((p for p in data.get('plays', []) if p.get('typeDescKey') == 'goal'), None)
        
        if not goal:
            print("  -> No goals found in first game (0-0 tie? unlikely)")
            return False
            
        # 3. Check for pptReplayUrl
        ppt_url = goal.get('pptReplayUrl')
        if ppt_url:
            print(f"  -> SUCCESS! Found Animation URL: {ppt_url}")
            
            # 4. Verify we can download it
            anim_resp = requests.get(ppt_url, headers=headers)
            if anim_resp.status_code == 200:
                print("  -> Verified: Can download JSON.")
                return True
            else:
                print(f"  -> Failed to download JSON (Status {anim_resp.status_code})")
                return False
        else:
            print("  -> No 'pptReplayUrl' found in Goal object.")
            return False
            
    except Exception as e:
        print(f"  -> Error: {e}")
        return False

# Check backwards from current
seasons_to_check = [2024, 2023, 2022, 2021, 2020, 2019]

for s in seasons_to_check:
    has_data = check_season(s)
    if not has_data:
        print(f"\nLikely Cutoff: Season {s} does not seem to have Edge data available.")
        break

