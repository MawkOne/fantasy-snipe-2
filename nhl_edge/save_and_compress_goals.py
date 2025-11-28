import requests
import json
import os
import sys

def save_all_goals(game_id):
    # Setup directories
    raw_dir = f"nhl_edge/game_{game_id}/raw"
    comp_dir = f"nhl_edge/game_{game_id}/compressed"
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(comp_dir, exist_ok=True)
    
    # 1. Get Goal URLs
    pbp_url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"
    print(f"Fetching PBP: {pbp_url}")
    
    resp = requests.get(pbp_url)
    data = resp.json()
    
    goals = [p for p in data.get('plays', []) if p.get('typeDescKey') == 'goal']
    print(f"Found {len(goals)} goals.")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.nhl.com/"
    }
    
    results = []
    
    for g in goals:
        event_id = g.get('eventId')
        ppt_url = g.get('pptReplayUrl')
        
        if not ppt_url:
            print(f"Skipping Goal {event_id}: No animation URL")
            continue
            
        # 2. Fetch RAW Data
        print(f"Fetching Goal {event_id}...")
        anim_resp = requests.get(ppt_url, headers=headers)
        if anim_resp.status_code != 200:
            print(f"Failed to fetch {ppt_url}")
            continue
            
        raw_data = anim_resp.json()
        
        # Save RAW
        raw_path = os.path.join(raw_dir, f"goal_{event_id}_raw.json")
        with open(raw_path, 'w') as f:
            json.dump(raw_data, f) # No indent for fair size comparison (minified)
            
        # 3. Compress Data
        compressed_data = compress_tracking_data(raw_data)
        
        # Save COMPRESSED
        comp_path = os.path.join(comp_dir, f"goal_{event_id}_compressed.json")
        with open(comp_path, 'w') as f:
            json.dump(compressed_data, f) # Minified
            
        # Track stats
        raw_size = os.path.getsize(raw_path)
        comp_size = os.path.getsize(comp_path)
        results.append({
            "event_id": event_id,
            "raw_size": raw_size,
            "comp_size": comp_size,
            "reduction": (1 - (comp_size / raw_size)) * 100
        })

    # Summary
    print("\n--- Compression Results ---")
    print(f"{'Event ID':<10} | {'Raw (KB)':<10} | {'Comp (KB)':<10} | {'Savings':<10}")
    print("-" * 50)
    
    total_raw = 0
    total_comp = 0
    
    for r in results:
        print(f"{r['event_id']:<10} | {r['raw_size']/1024:<10.1f} | {r['comp_size']/1024:<10.1f} | {r['reduction']:.1f}%")
        total_raw += r['raw_size']
        total_comp += r['comp_size']
        
    print("-" * 50)
    print(f"TOTAL      | {total_raw/1024:<10.1f} | {total_comp/1024:<10.1f} | {(1-(total_comp/total_raw))*100:.1f}%")


def compress_tracking_data(raw_frames):
    """
    Transforms verbose dictionary list into compact columnar format.
    """
    if not raw_frames:
        return {}
        
    # 1. Extract Metadata (Players) from the first frame
    # We assume the player list is constant (or we take the union if not)
    first_frame = raw_frames[0]
    
    # Create a mapping of ID -> Index
    player_map = {} # {playerId: index}
    player_meta = [] # List of {id, team, number} to store in header
    
    # Always put Puck (ID 1) first for consistency
    # Check if puck exists in first frame (it usually does)
    # If not, we might need to scan frames, but let's assume standard structure
    
    # We need a stable list of ALL IDs that appear in the animation
    all_ids = set()
    for f in raw_frames:
        if 'onIce' in f:
            all_ids.update(f['onIce'].keys())
    
    # Sort IDs: Puck (1) first, then others
    sorted_ids = sorted(list(all_ids), key=lambda x: (0 if str(x)=='1' else 1, int(x) if str(x).isdigit() else 999))
    
    for idx, pid in enumerate(sorted_ids):
        player_map[pid] = idx
        
        # Find metadata for this player (scan frames until we find one instance)
        p_info = {}
        for f in raw_frames:
            if 'onIce' in f and pid in f['onIce']:
                obj = f['onIce'][pid]
                p_info = {
                    "id": pid,
                    "team": obj.get("teamAbbrev", ""),
                    "num": obj.get("sweaterNumber", "")
                }
                break
        player_meta.append(p_info)
        
    # 2. Build Frame Arrays
    # Format: [timestamp, x_p0, y_p0, x_p1, y_p1, ...]
    compressed_frames = []
    
    for f in raw_frames:
        ts = f.get('timeStamp')
        
        # Initialize frame array with timestamp
        # Use None or 0 for missing coords? None is safer, 0 saves space.
        # Let's use None (null in JSON) to indicate missing tracking
        row = [ts]
        
        # Add coords for every player in the sorted order
        for pid in sorted_ids:
            if 'onIce' in f and pid in f['onIce']:
                p = f['onIce'][pid]
                # Round to 2 decimals to save space (raw has ~4)
                row.append(round(p.get('x', 0), 2))
                row.append(round(p.get('y', 0), 2))
            else:
                row.append(None)
                row.append(None)
                
        compressed_frames.append(row)
        
    return {
        "meta": {
            "players": player_meta,
            "format": "ts, [x, y] per player in order"
        },
        "data": compressed_frames
    }

if __name__ == "__main__":
    save_all_goals(2025020360)

