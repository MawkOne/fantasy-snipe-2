import requests
import json
import os
import sys
import psycopg2
import math
from psycopg2.extras import RealDictCursor

# --- CONFIG ---
# Calibrated Physics Constants
FPS = 16.94  # Empirically derived from Draisaitl Top Speed (Game 2025020360)
SMOOTHING_WINDOW = 2 # +/- frames for central difference

DB_URL = os.getenv("FANTASY_DATABASE_URL", "postgresql://postgres:123-new-password@34.47.23.137:5432/postgres?sslmode=require")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.nhl.com/"
}

class NHLEdgePipeline:
    def __init__(self, game_id):
        self.game_id = str(game_id)
        self.dirs = {
            "raw": f"nhl_edge/game_{game_id}/raw",
            "final": f"nhl_edge/game_{game_id}/final"
        }
        for d in self.dirs.values():
            os.makedirs(d, exist_ok=True)
            
        self.pbp_data = None
        self.player_db_cache = {}

    def run(self):
        print(f"--- Starting Pipeline for Game {self.game_id} ---")
        print(f"Config: {FPS} FPS | Window: +/-{SMOOTHING_WINDOW}")
        
        # 1. Fetch Game Context (PBP)
        self.fetch_pbp()
        
        # 2. Identify Goals
        goals = self.extract_goals()
        print(f"Found {len(goals)} goals.")
        
        # 3. Process Each Goal and Insert to DB
        for goal in goals:
            try:
                final_json = self.process_goal(goal)
                if final_json:
                    self.insert_to_db(goal, final_json)
            except Exception as e:
                print(f"Error processing Goal {goal['id']}: {e}")

    def fetch_pbp(self):
        url = f"https://api-web.nhle.com/v1/gamecenter/{self.game_id}/play-by-play"
        print(f"Fetching PBP: {url}")
        resp = requests.get(url)
        if resp.status_code != 200:
            raise Exception(f"Failed to fetch PBP: {resp.status_code}")
        self.pbp_data = resp.json()

    def extract_goals(self):
        goals = []
        for play in self.pbp_data.get('plays', []):
            if play.get('typeDescKey') == 'goal':
                goals.append({
                    "id": play.get('eventId'),
                    "period": play.get('periodDescriptor', {}).get('number'),
                    "time": play.get('timeInPeriod'),
                    "score_home": play.get('details', {}).get('homeScore'),
                    "score_away": play.get('details', {}).get('awayScore'),
                    "strength": play.get('situationCode', '????'),
                    "scorer_id": play.get('details', {}).get('scoringPlayerId'),
                    "assist_ids": play.get('details', {}).get('assist1PlayerId', []), # Could be list or int
                    "url": play.get('pptReplayUrl')
                })
        return goals

    def process_goal(self, goal_meta):
        event_id = goal_meta['id']
        ppt_url = goal_meta['url']
        
        if not ppt_url:
            print(f"Skipping Goal {event_id}: No Animation URL")
            return

        # A. Get RAW Data (Local or Download)
        raw_path = os.path.join(self.dirs['raw'], f"goal_{event_id}_raw.json")
        raw_data = {}
        
        if os.path.exists(raw_path):
            with open(raw_path, 'r') as f:
                raw_data = json.load(f)
        else:
            print(f"Downloading raw for Goal {event_id}...")
            resp = requests.get(ppt_url, headers=HEADERS)
            if resp.status_code != 200:
                print(f"Failed download: {resp.status_code}")
                return
            raw_data = resp.json()
            with open(raw_path, 'w') as f:
                json.dump(raw_data, f)

        # B. Transform & Enrich (Now with Velocity!)
        final_json = self.transform(raw_data, goal_meta)
        
        # C. Save Final
        final_path = os.path.join(self.dirs['final'], f"goal_{event_id}_complete.json")
        with open(final_path, 'w') as f:
            json.dump(final_json, f)
        
        print(f"Saved Goal {event_id} -> {final_path} ({os.path.getsize(final_path)/1024:.1f} KB)")
        
        return final_json

    def get_player_details_from_db(self, player_ids):
        # Filter cached
        needed = [pid for pid in player_ids if pid not in self.player_db_cache]
        
        if not needed:
            return
            
        # Batch Query DB
        try:
            conn = psycopg2.connect(DB_URL)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            safe_ids = [int(x) for x in needed if str(x).isdigit()]
            if not safe_ids: return

            fmt = ','.join(['%s'] * len(safe_ids))
            query = f"SELECT id, full_name, position_code, headshot_url, sweater_number FROM players WHERE id IN ({fmt})"
            
            cur.execute(query, tuple(safe_ids))
            rows = cur.fetchall()
            
            for r in rows:
                self.player_db_cache[r['id']] = r
                
            conn.close()
        except Exception as e:
            print(f"DB Error: {e}")

    def calculate_velocity(self, frames_data, player_idx, current_frame_idx):
        """
        Calculates smooth MPH for a player at a specific frame.
        Uses central difference with window K.
        frames_data: List of coordinate lists [[x, y], [x, y]...] for one player
        """
        K = SMOOTHING_WINDOW
        
        # Boundary checks
        if current_frame_idx < K or current_frame_idx >= len(frames_data) - K:
            return 0.0
            
        p0 = frames_data[current_frame_idx - K]
        p1 = frames_data[current_frame_idx + K]
        
        if p0 is None or p1 is None:
            return 0.0
            
        # Distance in inches
        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]
        dist_inches = math.sqrt(dx*dx + dy*dy)
        
        # Time delta for window
        dt = (2 * K) / FPS
        
        # Speed
        feet_per_sec = (dist_inches / 12.0) / dt
        mph = feet_per_sec * 0.681818
        
        if mph > 35: return 0.0 # Glitch
        return round(mph, 2)

    def transform(self, raw_frames, goal_meta):
        if not raw_frames: return {}
        
        # 1. Extract all Player IDs
        id_map = {} # internal -> real
        
        for f in raw_frames:
            if 'onIce' in f:
                for iid, p in f['onIce'].items():
                    rid = p.get('playerId')
                    if rid: id_map[iid] = rid
                    elif iid == '1': id_map['1'] = 1
        
        # 2. Update DB Cache
        real_ids = [rid for rid in id_map.values() if rid != 1]
        self.get_player_details_from_db(real_ids)
        
        # 3. Build Header
        sorted_iids = sorted(list(id_map.keys()), key=lambda x: (0 if str(x)=='1' else 1, int(x) if str(x).isdigit() else 999))
        
        players_meta = []
        for iid in sorted_iids:
            rid = id_map.get(iid)
            raw_fb = {}
            for f in raw_frames:
                if 'onIce' in f and iid in f['onIce']:
                    raw_fb = f['onIce'][iid]
                    break
            
            if rid == 1:
                p_obj = {"id": 1, "name": "Puck", "team": "", "pos": "", "num": "", "img": ""}
            else:
                db_p = self.player_db_cache.get(rid, {})
                p_obj = {
                    "id": rid,
                    "name": db_p.get('full_name') or f"Player {rid}",
                    "team": raw_fb.get('teamAbbrev') or "",
                    "pos": db_p.get('position_code') or "",
                    "num": db_p.get('sweater_number') or raw_fb.get('sweaterNumber') or "",
                    "img": db_p.get('headshot_url') or ""
                }
            players_meta.append(p_obj)

        # 4. First Pass: Extract Coords per Player for Speed Calc
        # player_coords[internal_id] = [ [x,y], [x,y], ... ]
        player_coords = {iid: [] for iid in sorted_iids}
        timestamps = []
        
        for f in raw_frames:
            timestamps.append(f.get('timeStamp'))
            for iid in sorted_iids:
                if 'onIce' in f and iid in f['onIce']:
                    p = f['onIce'][iid]
                    player_coords[iid].append([p.get('x', 0), p.get('y', 0)])
                else:
                    player_coords[iid].append(None)

        # 5. Second Pass: Build Rows with [ts, x, y, v, x, y, v...]
        data_rows = []
        num_frames = len(timestamps)
        
        # Pre-calculate puck index for special logic
        puck_iid = None
        for iid in sorted_iids:
            if id_map.get(iid) == 1:
                puck_iid = iid
                break

        for i in range(num_frames):
            row = [timestamps[i]]
            
            for iid in sorted_iids:
                coords = player_coords[iid][i]
                
                if coords:
                    x, y = coords
                    mph = self.calculate_velocity(player_coords[iid], 0, i)
                    
                    # Special Puck Logic: Calculate Angle to Net (Center of Net: x=89, y=0 ?? No, y=0 is center ice?)
                    # NHL Coords: (0,0) is center ice. 
                    # Rink is 200x85. 
                    # Net is at X = +/- 89 ft = +/- 1068 inches? No, let's verify coordinates.
                    # Standard NHL: X goes -100 to +100 ft. Y goes -42.5 to +42.5 ft.
                    # In our data (raw): X seems to be 0-2400 ?? 
                    # Let's look at the raw data again.
                    # Frame 1 Puck: x=2066.64, y=79.31
                    # Frame 1 Player: x=1599.57 (This is huge). 
                    # Ah, the units seem to be 0-200ft scaled to inches? 200ft = 2400 inches.
                    # So Net is likely at X=11ft (132in) and X=189ft (2268in).
                    # Let's stick to saving raw X/Y/V for now to be safe.
                    
                    row.append(round(x, 2))
                    row.append(round(y, 2))
                    row.append(mph)
                else:
                    row.append(None)
                    row.append(None)
                    row.append(None)
            
            data_rows.append(row)
            
        # 6. Construct Final
        return {
            "event": goal_meta,
            "game": {
                "id": self.pbp_data.get('id'),
                "date": self.pbp_data.get('gameDate'),
                "home_team": self.pbp_data.get('homeTeam', {}).get('abbrev'),
                "away_team": self.pbp_data.get('awayTeam', {}).get('abbrev')
            },
            "config": {
                "fps": FPS,
                "units": "inches",
                "generated_speed": True
            },
            "players": players_meta,
            "data": data_rows
        }

    def insert_to_db(self, goal_meta, final_json):
        """Insert the tracking data into Cloud SQL"""
        try:
            conn = psycopg2.connect(DB_URL)
            cur = conn.cursor()
            
            query = """
                INSERT INTO tracking_goals 
                (game_id, event_id, game_date, period, time_in_period, scorer_player_id, fps, tracking_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (game_id, event_id) 
                DO UPDATE SET tracking_data = EXCLUDED.tracking_data, fps = EXCLUDED.fps;
            """
            
            cur.execute(query, (
                self.game_id,
                goal_meta['id'],
                self.pbp_data.get('gameDate'),
                goal_meta.get('period'),
                goal_meta.get('time'),
                goal_meta.get('scorer_id'),
                FPS,
                json.dumps(final_json)
            ))
            
            conn.commit()
            conn.close()
            print(f"✅ Inserted Goal {goal_meta['id']} to database")
            
        except Exception as e:
            print(f"❌ DB Insert Error: {e}")

    # Overriding for single player list usage
    def calculate_velocity(self, player_frames, _, current_idx):
        K = SMOOTHING_WINDOW
        if current_idx < K or current_idx >= len(player_frames) - K:
            return 0.0
        p0 = player_frames[current_idx - K]
        p1 = player_frames[current_idx + K]
        if p0 is None or p1 is None:
            return 0.0
        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]
        dist = math.sqrt(dx*dx + dy*dy)
        dt = (2 * K) / FPS
        mph = (dist / 12.0 / dt) * 0.681818
        return round(mph, 2)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python etl_pipeline.py <GAME_ID>")
    else:
        pipeline = NHLEdgePipeline(sys.argv[1])
        pipeline.run()
