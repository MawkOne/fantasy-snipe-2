#!/usr/bin/env python3
import os
import sys
import csv
from datetime import datetime
from typing import Dict

import pandas as pd
from sqlalchemy.orm import sessionmaker

# Add project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import connect_with_connector
from src.database.models import Team, Player, Game, PlayerGameStats, create_tables


REF_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs', 'Reference')


def norm(s: str) -> str:
    return (s or '').strip().lower().replace(' ', '_')


def ingest_teams(session, path: str) -> int:
    if not os.path.exists(path):
        return 0
    df = pd.read_csv(path)
    cols = {norm(c): c for c in df.columns}
    id_col = cols.get('team_id') or cols.get('id')
    name_col = cols.get('team_name') or cols.get('full_name') or cols.get('name')
    tri_col = cols.get('tri_code') or cols.get('abbreviation') or cols.get('raw_tricode')
    if not id_col or not name_col:
        return 0
    cnt = 0
    for _, r in df.iterrows():
        try:
            tid = int(r[id_col])
        except Exception:
            continue
        team = session.query(Team).filter(Team.id == tid).first()
        if team is None:
            team = Team(id=tid)
            session.add(team)
            cnt += 1
        team.full_name = str(r.get(name_col) or team.full_name)
        if tri_col:
            tc = str(r.get(tri_col) or '').upper()[:3]
            if tc:
                team.tri_code = tc
        session.flush()
    return cnt


def ingest_players(session, path: str) -> int:
    if not os.path.exists(path):
        return 0
    df = pd.read_csv(path)
    cols = {norm(c): c for c in df.columns}
    id_col = cols.get('player_id') or cols.get('id')
    fn_col = cols.get('first_name') or cols.get('firstname')
    ln_col = cols.get('last_name') or cols.get('lastname')
    full_col = cols.get('full_name') or cols.get('name')
    pos_col = cols.get('position_code') or cols.get('pos') or cols.get('position')
    team_col = cols.get('team_id')
    if not id_col:
        return 0
    cnt = 0
    for _, r in df.iterrows():
        try:
            pid = int(r[id_col])
        except Exception:
            continue
        player = session.query(Player).filter(Player.id == pid).first()
        if player is None:
            player = Player(id=pid)
            session.add(player)
            cnt += 1
        first = str(r.get(fn_col) or '') if fn_col else ''
        last = str(r.get(ln_col) or '') if ln_col else ''
        full = str(r.get(full_col) or '').strip()
        player.first_name = first or player.first_name
        player.last_name = last or player.last_name
        player.full_name = full or (f"{first} {last}".strip()) or player.full_name
        if pos_col:
            pc = str(r.get(pos_col) or '').upper()[:1]
            if pc:
                player.position_code = pc
        if team_col:
            try:
                player.team_id = int(r.get(team_col))
            except Exception:
                pass
        session.flush()
    return cnt


def parse_dt(s: str) -> datetime:
    # Try multiple formats
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(s), fmt)
        except Exception:
            continue
    return datetime.utcnow()


def ingest_games(session, path: str) -> int:
    if not os.path.exists(path):
        return 0
    df = pd.read_csv(path)
    cols = {norm(c): c for c in df.columns}
    gid_col = cols.get('game_id') or cols.get('id')
    season_col = cols.get('season')
    type_col = cols.get('type') or cols.get('game_type')
    dt_col = cols.get('date_time') or cols.get('game_date')
    home_id_col = cols.get('home_team_id')
    away_id_col = cols.get('away_team_id')
    home_goals_col = cols.get('home_goals') or cols.get('home_score')
    away_goals_col = cols.get('away_goals') or cols.get('away_score')
    if not gid_col or not season_col or not dt_col or not home_id_col or not away_id_col:
        return 0
    cnt = 0
    for _, r in df.iterrows():
        try:
            gid = int(r[gid_col])
        except Exception:
            continue
        g = session.query(Game).filter(Game.id == gid).first()
        if g is None:
            g = Game(id=gid)
            session.add(g)
            cnt += 1
        try:
            g.season = int(r.get(season_col))
        except Exception:
            pass
        # Map type: assume numeric if present, else try to convert R/P to 2/3
        t = r.get(type_col)
        if pd.notna(t):
            try:
                g.game_type = int(t)
            except Exception:
                ts = str(t).upper()[:1]
                g.game_type = 2 if ts == 'R' else (3 if ts == 'P' else None)
        g.game_date = parse_dt(r.get(dt_col))
        try:
            g.home_team_id = int(r.get(home_id_col))
            g.away_team_id = int(r.get(away_id_col))
        except Exception:
            pass
        try:
            g.home_score = int(r.get(home_goals_col)) if home_goals_col else g.home_score
            g.away_score = int(r.get(away_goals_col)) if away_goals_col else g.away_score
        except Exception:
            pass
        session.flush()
    return cnt


def ingest_skater_stats(session, path: str) -> int:
    if not os.path.exists(path):
        return 0
    df = pd.read_csv(path)
    cols = {norm(c): c for c in df.columns}
    pid_col = cols.get('player_id') or cols.get('skater_id') or cols.get('id')
    gid_col = cols.get('game_id') or cols.get('gameid')
    team_col = cols.get('team_id') or cols.get('teamid')
    g_col = cols.get('goals') or cols.get('g')
    a_col = cols.get('assists') or cols.get('a')
    pts_col = cols.get('points') or cols.get('pts')
    shots_col = cols.get('shots') or cols.get('s')
    pm_col = cols.get('plus_minus') or cols.get('plusminus') or cols.get('pm')
    pp_g_col = cols.get('power_play_goals') or cols.get('ppg')
    pp_pts_col = cols.get('power_play_points') or cols.get('ppp')
    sh_g_col = cols.get('shorthanded_goals') or cols.get('shg')
    sh_pts_col = cols.get('shorthanded_points') or cols.get('shp')
    pim_col = cols.get('pim') or cols.get('penalty_minutes')
    shifts_col = cols.get('shifts')
    toi_col = cols.get('time_on_ice') or cols.get('toi') or cols.get('timeonice')
    if not pid_col or not gid_col:
        return 0
    cnt = 0
    for _, r in df.iterrows():
        try:
            pid = int(r.get(pid_col))
            gid = int(r.get(gid_col))
        except Exception:
            continue
        row = session.query(PlayerGameStats).filter(
            PlayerGameStats.player_id == pid,
            PlayerGameStats.game_id == gid,
        ).first()
        if row is None:
            row = PlayerGameStats(player_id=pid, game_id=gid, team_id=None)
            session.add(row)
            cnt += 1
        # Team if present
        try:
            if team_col:
                row.team_id = int(r.get(team_col))
        except Exception:
            pass
        def iv(col, default=0):
            try:
                return int(r.get(col)) if col else default
            except Exception:
                try:
                    return int(float(r.get(col)))
                except Exception:
                    return default
        row.goals = iv(g_col, row.goals or 0)
        row.assists = iv(a_col, row.assists or 0)
        row.points = iv(pts_col, (row.goals or 0) + (row.assists or 0))
        row.shots = iv(shots_col, row.shots or 0)
        row.plus_minus = iv(pm_col, row.plus_minus or 0)
        row.power_play_goals = iv(pp_g_col, row.power_play_goals or 0)
        row.power_play_points = iv(pp_pts_col, row.power_play_points or 0)
        row.shorthanded_goals = iv(sh_g_col, row.shorthanded_goals or 0)
        row.shorthanded_points = iv(sh_pts_col, row.shorthanded_points or 0)
        row.pim = iv(pim_col, row.pim or 0)
        row.shifts = iv(shifts_col, row.shifts or 0)
        toi_val = str(r.get(toi_col) or '') if toi_col else ''
        row.toi = toi_val if ':' in toi_val else row.toi
        session.flush()
    return cnt


def main():
    # Connect
    engine = connect_with_connector()
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        create_tables()
    except Exception:
        pass
    try:
        t_new = ingest_teams(session, os.path.join(REF_DIR, 'team_info.csv'))
        p_new = ingest_players(session, os.path.join(REF_DIR, 'player_info.csv'))
        g_new = ingest_games(session, os.path.join(REF_DIR, 'game.csv'))
        s_new = ingest_skater_stats(session, os.path.join(REF_DIR, 'game_skater_stats.csv'))
        session.commit()
        print(f"Ingested: teams+{t_new}, players+{p_new}, games+{g_new}, skater_stats+{s_new}")
    except Exception as e:
        print("Ingestion error:", e)
        session.rollback()
    finally:
        session.close()


if __name__ == '__main__':
    main()


