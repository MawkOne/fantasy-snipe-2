#!/usr/bin/env python3
"""
Map CBS players to NHL player IDs using the external NHL DB, and write nhl_player_id into cbs_players.

Logic:
- Join by normalized full_name against NHL players table; where ambiguous, prefer exact match.
- Also attempt lookup via player_info_tmp if available.

Env:
- FANTASY_DATABASE_URL: Postgres for cbs_* tables (Railway)
- NHL_DATABASE_URL: External Postgres with tables players, player_details, and player_info_tmp
"""
import os
import sys
import unicodedata
from typing import Dict
import psycopg2
from psycopg2.extras import execute_batch


def norm_name(s: str) -> str:
    return unicodedata.normalize('NFKD', (s or '')).encode('ascii', 'ignore').decode('ascii').strip().lower()


def main():
    local_url = os.getenv('FANTASY_DATABASE_URL') or os.getenv('DATABASE_URL')
    ext_url = os.getenv('NHL_DATABASE_URL')
    if not local_url or not ext_url:
        print('FANTASY_DATABASE_URL and NHL_DATABASE_URL must be set')
        sys.exit(1)

    local = psycopg2.connect(local_url)
    ext = psycopg2.connect(ext_url)
    local.autocommit = False
    try:
        lc = local.cursor()
        ec = ext.cursor()

        # Load NHL name->id map (players)
        ec.execute("SELECT id, full_name FROM players")
        name_to_id: Dict[str, int] = {}
        for pid, full_name in ec.fetchall():
            key = norm_name(full_name)
            if key and pid:
                name_to_id[key] = int(pid)

        # Augment with player_info_tmp if present (name and id columns may vary)
        try:
            ec.execute("SELECT player_id, firstname, lastname FROM player_info_tmp")
            for pid, firstname, lastname in ec.fetchall():
                full_name = f"{firstname} {lastname}".strip()
                key = norm_name(full_name)
                if key and pid and key not in name_to_id:
                    name_to_id[key] = int(pid)
        except Exception:
            pass

        # Read CBS players without mapped nhl_player_id
        lc.execute("SELECT cbs_player_id, full_name FROM cbs_players WHERE nhl_player_id IS NULL")
        rows = lc.fetchall()
        updates = []
        updates_split = []
        for cid, fullname in rows:
            key = norm_name(fullname)
            pid = name_to_id.get(key)
            if pid:
                updates.append((int(pid), str(cid)))
                continue
            # Fallback: split to first/last and do last-name exact, first-name fuzzy (prefix or levenshtein <= 2)
            parts = [p for p in fullname.replace("' ", "'").replace(" ’ ", "'").replace("`", "'").split() if p]
            if len(parts) >= 2:
                first = norm_name(" ".join(parts[:-1]))
                last = norm_name(parts[-1])
                # Build candidate set from player_info_tmp by last name
                try:
                    ec.execute("SELECT player_id, firstname, lastname FROM player_info_tmp WHERE lower(lastname)=%s", (last,))
                    cands = ec.fetchall()
                except Exception:
                    cands = []
                # simple fuzzy on first name (prefix or edit distance <=2)
                def ed(a, b):
                    dp = [[i+j if i*j==0 else 0 for j in range(len(b)+1)] for i in range(len(a)+1)]
                    for i in range(1, len(a)+1):
                        for j in range(1, len(b)+1):
                            dp[i][j] = min(
                                dp[i-1][j] + 1,
                                dp[i][j-1] + 1,
                                dp[i-1][j-1] + (0 if a[i-1]==b[j-1] else 1)
                            )
                    return dp[-1][-1]
                best_pid = None
                best_score = 99
                for pid2, fn, ln in cands:
                    fnk = norm_name(fn)
                    if fnk.startswith(first) or first.startswith(fnk):
                        best_pid = int(pid2)
                        best_score = 0
                        break
                    d = ed(first, fnk)
                    if d < best_score:
                        best_score = d
                        best_pid = int(pid2)
                if best_pid is not None and best_score <= 2:
                    updates_split.append((best_pid, str(cid), first, last))

        if updates:
            execute_batch(
                lc,
                "UPDATE cbs_players SET nhl_player_id = %s WHERE cbs_player_id = %s",
                updates,
                page_size=1000,
            )
            print(f"Updated {len(updates)} cbs_players rows with nhl_player_id")
        if updates_split:
            execute_batch(
                lc,
                "UPDATE cbs_players SET nhl_player_id = %s, first_name = COALESCE(first_name, %s), last_name = COALESCE(last_name, %s) WHERE cbs_player_id = %s",
                [(pid, fn, ln, cid) for (pid, cid, fn, ln) in updates_split],
                page_size=1000,
            )
            print(f"Updated {len(updates_split)} cbs_players rows via last-name match + fuzzy first-name")

        # Also backfill cbs_player_map with NHL names for debugging/joins
        try:
            # Build map of id -> names from NHL DB
            ec.execute("SELECT p.id, p.full_name, i.firstname, i.lastname FROM players p LEFT JOIN player_info_tmp i ON i.player_id=p.id")
            id_to_names = {int(pid): (fn, (first or None), (last or None)) for pid, fn, first, last in ec.fetchall()}
            # Load mapped entries
            lc.execute("SELECT cbs_player_id, nhl_player_id FROM cbs_player_map WHERE nhl_player_id IS NOT NULL")
            rows_map = lc.fetchall()
            payload = []
            for cid, pid in rows_map:
                if pid in id_to_names:
                    full, first, last = id_to_names[pid]
                    payload.append((full, first, last, cid))
            if payload:
                execute_batch(
                    lc,
                    "UPDATE cbs_player_map SET nhl_full_name = %s, nhl_first_name = %s, nhl_last_name = %s WHERE cbs_player_id = %s",
                    payload,
                    page_size=1000,
                )
                print(f"Backfilled NHL names into cbs_player_map for {len(payload)} rows")
        except Exception as e:
            print("Backfill into cbs_player_map failed:", e)
        else:
            print("No cbs_players updates needed")

        local.commit()
    except Exception as e:
        local.rollback()
        print("Error mapping cbs players:", e)
        sys.exit(1)
    finally:
        try:
            local.close()
        except Exception:
            pass
        try:
            ext.close()
        except Exception:
            pass


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
import os
import sys
import re
import argparse
import json
from typing import Dict, Any, Tuple, Optional

import psycopg2
from psycopg2.extras import execute_batch


def db_connect(db_url: str):
    return psycopg2.connect(db_url, sslmode='require') if 'rlwy.net' in db_url or 'railway' in db_url else psycopg2.connect(db_url)


def normalize_name(name: str) -> str:
    n = name.strip().lower()
    n = re.sub(r"[^a-z\s]", "", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


def fetch_cbs_players(cur) -> Dict[str, Tuple[str, str, str]]:
    # cbs_player_id -> (full_name, pos_primary, nhl_team_abbr)
    cur.execute("SELECT cbs_player_id, full_name, COALESCE(pos_primary,''), COALESCE(nhl_team_abbr,'') FROM cbs_players")
    out: Dict[str, Tuple[str, str, str]] = {}
    for row in cur.fetchall():
        out[row[0]] = (row[1], row[2], row[3])
    return out


def fetch_rankings(cur) -> Dict[str, Tuple[int, str, str]]:
    # normalized name -> (nhl_player_id, position, team)
    cur.execute("SELECT nhl_player_id, player_name, COALESCE(position,''), COALESCE(team,'') FROM fantasy_season_rankings")
    out: Dict[str, Tuple[int, str, str]] = {}
    for pid, name, pos, team in cur.fetchall():
        out[normalize_name(name)] = (int(pid), pos, team)
    return out


def load_yahoo_name_map(path: str) -> Dict[str, int]:
    """Build normalized name -> nhl_player_id from Yahoo JSON file."""
    try:
        with open(path, 'r') as f:
            arr = json.load(f)
        name_to_id: Dict[str, int] = {}
        for it in arr:
            nhl_id = it.get('nhl_player_id')
            name = it.get('nhl_player_name') or it.get('yahoo_player_name')
            if not name or not nhl_id:
                continue
            try:
                nhl_id_int = int(nhl_id)
            except Exception:
                continue
            key = normalize_name(str(name))
            name_to_id.setdefault(key, nhl_id_int)
        return name_to_id
    except Exception:
        return {}


def upsert_map(cur, rows):
    if not rows:
        return 0
    execute_batch(
        cur,
        """
        INSERT INTO cbs_player_map(cbs_player_id, nhl_player_id, confidence, match_method)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (cbs_player_id) DO UPDATE SET
          nhl_player_id=EXCLUDED.nhl_player_id,
          confidence=EXCLUDED.confidence,
          match_method=EXCLUDED.match_method,
          mapped_at=NOW()
        """,
        rows,
        page_size=1000,
    )
    return len(rows)


def main():
    ap = argparse.ArgumentParser(description='Map CBS players to NHL player_ids using rankings names (or Yahoo JSON fallback)')
    ap.add_argument('--db-url', default=os.getenv('CBS_DB_URL') or os.getenv('FANTASY_DATABASE_URL') or os.getenv('DATABASE_URL') or 'postgresql://postgres:WbUPvsoAtcwLhxCDMPOygaFHuALRTcWa@shuttle.proxy.rlwy.net:34371/railway')
    ap.add_argument('--yahoo-json', default='/Users/markhenderson/Cursor Projects/NHL-API/Player_sources/yahoo_NHL_players_map')
    args = ap.parse_args()

    conn = db_connect(args.db_url)
    conn.autocommit = True
    cur = conn.cursor()
    try:
        cbs = fetch_cbs_players(cur)
        ranks: Dict[str, Tuple[int, str, str]] = {}
        # Check if rankings table exists before querying
        cur.execute("SELECT to_regclass('public.fantasy_season_rankings')")
        has_rank = cur.fetchone()[0] is not None
        if has_rank:
            try:
                ranks = fetch_rankings(cur)
            except Exception:
                ranks = {}
        rows = []
        yahoo_map: Dict[str, int] = {}
        used_yahoo = False
        if not ranks:
            yahoo_map = load_yahoo_name_map(args.yahoo_json)
            used_yahoo = bool(yahoo_map)
        for cbs_id, (full_name, pos, team) in cbs.items():
            key = normalize_name(full_name)
            if ranks:
                hit = ranks.get(key)
                if hit:
                    nhl_id, rpos, rteam = hit
                    conf = 0.95
                    if pos and rpos and pos.upper()[:1] == rpos.upper()[:1]:
                        conf += 0.02
                    if team and rteam and team.upper() == rteam.upper():
                        conf += 0.02
                    rows.append((cbs_id, nhl_id, min(conf, 0.99), 'name_exact_norm'))
            else:
                nhl_id = yahoo_map.get(key)
                if nhl_id:
                    conf = 0.90
                    rows.append((cbs_id, nhl_id, conf, 'name_yahoo_norm'))
        count = upsert_map(cur, rows)
        source = 'rankings' if not used_yahoo else 'yahoo'
        print(f"Mapped {count} CBS players to NHL IDs (source={source})")
    except Exception as e:
        print('Mapping error:', e)
        sys.exit(1)
    finally:
        cur.close(); conn.close()


if __name__ == '__main__':
    main()
