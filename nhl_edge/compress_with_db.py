import json
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

# DB Connection String
DB_URL = "postgresql://postgres:123-new-password@34.47.23.137:5432/postgres?sslmode=require"

def get_player_details(player_ids):
    """
    Queries the database for a list of player IDs.
    Returns a dictionary: { id: { full_name, position_code, headshot_url, ... } }
    """
    if not player_ids:
        return {}
        
    # Convert IDs to ints for safety
    safe_ids = [int(pid) for pid in player_ids if str(pid).isdigit()]
    if not safe_ids:
        return {}

    conn = None
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query
        format_strings = ','.join(['%s'] * len(safe_ids))
        query = f"SELECT id, full_name, position_code, headshot_url, sweater_number FROM players WHERE id IN ({format_strings})"
        
        cur.execute(query, tuple(safe_ids))
        rows = cur.fetchall()
        
        mapping = {}
        for r in rows:
            mapping[str(r['id'])] = r
            
        return mapping
        
    except Exception as e:
        print(f"DB Error: {e}")
        return {}
    finally:
        if conn:
            conn.close()

def compress_with_db(raw_frames, output_path):
    """
    Compresses frames and enriches metadata with DB info.
    """
    if not raw_frames:
        return
        
    # 1. Identify all Player IDs (Map internal ID to real NHL PlayerID)
    # mapping: { internal_id: real_nhl_id }
    id_map = {} 
    
    for f in raw_frames:
        if 'onIce' in f:
            for internal_id, p_data in f['onIce'].items():
                # The real NHL ID is usually in 'playerId'
                real_id = p_data.get('playerId')
                if real_id:
                    id_map[internal_id] = real_id
                elif internal_id == '1': # Puck
                    id_map['1'] = 1
            
    # Sort internal IDs for column order: Puck (1) first, then numeric sort
    sorted_internal_ids = sorted(list(id_map.keys()), key=lambda x: (0 if str(x)=='1' else 1, int(x) if str(x).isdigit() else 999))
    
    # 2. Fetch details from DB using REAL NHL IDs
    real_ids = list(id_map.values())
    db_info = get_player_details(real_ids)
    
    # 3. Build Metadata Header
    player_meta = [] 
    
    for internal_id in sorted_internal_ids:
        real_id = id_map.get(internal_id)
        
        # Default / Fallback info from raw data
        raw_fallback = {}
        for f in raw_frames:
             if 'onIce' in f and internal_id in f['onIce']:
                raw_fallback = f['onIce'][internal_id]
                break
        
        # Merge DB info (DB uses real_id)
        p_db = db_info.get(str(real_id), {})
        
        meta_obj = {
            "id": real_id, # Use the Real NHL ID in metadata
            "internal_id": internal_id, # Keep internal ID reference
            "name": p_db.get("full_name") or f"Player {internal_id}",
            "pos": p_db.get("position_code") or "",
            "num": p_db.get("sweater_number") or raw_fallback.get("sweaterNumber", ""),
            "team": raw_fallback.get("teamAbbrev", ""),
            "img": p_db.get("headshot_url") or ""
        }
        
        # Special Case for Puck
        if str(internal_id) == "1":
            meta_obj = {"id": 1, "internal_id": 1, "name": "Puck", "pos": "", "num": "", "team": "", "img": ""}
            
        player_meta.append(meta_obj)
        
    # 4. Build Frame Arrays
    compressed_frames = []
    for f in raw_frames:
        ts = f.get('timeStamp')
        row = [ts]
        for internal_id in sorted_internal_ids:
            if 'onIce' in f and internal_id in f['onIce']:
                p = f['onIce'][internal_id]
                row.append(round(p.get('x', 0), 2))
                row.append(round(p.get('y', 0), 2))
            else:
                row.append(None)
                row.append(None)
        compressed_frames.append(row)
        
    # 5. Output
    final_json = {
        "meta": {
            "players": player_meta,
            "format": "ts, [x, y] per player in order",
            "source": "NHL Edge + Postgres DB"
        },
        "data": compressed_frames
    }
    
    with open(output_path, 'w') as f:
        json.dump(final_json, f)
    
    print(f"Saved enriched data to {output_path}")
    print(f"Metadata included for {len(player_meta)} entities.")

def process_game_files(game_id):
    # Look for RAW files
    raw_dir = f"nhl_edge/game_{game_id}/raw"
    comp_dir = f"nhl_edge/game_{game_id}/compressed_enriched"
    
    if not os.path.exists(raw_dir):
        print(f"No raw data found for game {game_id}")
        return
        
    os.makedirs(comp_dir, exist_ok=True)
    
    files = [f for f in os.listdir(raw_dir) if f.endswith('_raw.json')]
    print(f"Found {len(files)} raw files to process.")
    
    for fname in files:
        raw_path = os.path.join(raw_dir, fname)
        out_name = fname.replace('_raw.json', '_enriched.json')
        out_path = os.path.join(comp_dir, out_name)
        
        with open(raw_path, 'r') as f:
            raw_data = json.load(f)
            
        compress_with_db(raw_data, out_path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python compress_with_db.py <GAME_ID>")
    else:
        process_game_files(sys.argv[1])

