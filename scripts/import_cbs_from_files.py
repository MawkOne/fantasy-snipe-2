#!/usr/bin/env python3
import os
import re
import sys
import json
import argparse
from typing import Dict, List, Optional, Tuple, Any

import psycopg2
from psycopg2.extras import execute_batch

try:
    from bs4 import BeautifulSoup  # type: ignore
    from bs4 import element as bs4_element  # type: ignore
    HAS_BS4 = True
except Exception:
    HAS_BS4 = False


def read_text(path: str) -> str:
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


def extract_league_identity(header_html: str, schedule_html: str) -> Tuple[str, str, str]:
    # provider_slug
    m = re.search(r'"leagueId"\s*:\s*"([^"]+)"', schedule_html)
    provider_slug = m.group(1).strip() if m else 'unknown'
    # name
    m2 = re.search(r'<title>([^<]+)</title>', header_html, re.IGNORECASE)
    name = (m2.group(1).strip() if m2 else 'CBS League').replace(' - CBSSports.com', '').strip()
    # domain
    m3 = re.search(r'"httpHost"\s*:\s*"http[s]?:\/\/([^"]+)"', header_html)
    if not m3:
        m3 = re.search(r'"httpHost"\s*:\s*"http[s]?:\/\/([^"]+)"', schedule_html)
    domain = m3.group(1).strip() if m3 else f"{provider_slug}.hockey.cbssports.com"
    return provider_slug, name, domain


def extract_owners(schedule_html: str) -> List[Tuple[str, Optional[str], Optional[str]]]:
    owners: Dict[str, Tuple[str, str]] = {}
    # ownerlogo with id param
    for m in re.finditer(r'ownerlogo\?[^\s\"]*?id=([a-zA-Z0-9_\-]+)', schedule_html):
        oid = m.group(1)
        owners.setdefault(oid, ('', ''))
    # league-scoped email markers (optional)
    for m in re.finditer(r'"([a-zA-Z0-9_\-]+)@([a-z0-9_.\-]+)"', schedule_html):
        email = m.group(0)
        handle = m.group(1)
        if handle in owners:
            owners[handle] = (owners[handle][0], email)
    return [(oid, owners[oid][0] or None, owners[oid][1] or None) for oid in owners.keys()]


def extract_owner_team_links(schedule_html: str) -> List[Tuple[str, str]]:
    links: List[Tuple[str, str]] = []
    # ownerlogo?...&teamname=New_Oilers_Nation&id=markhend6789
    for m in re.finditer(r"ownerlogo\?[^\n\r\"']*teamname=([^&]+)&id=([a-zA-Z0-9_\-]+)", schedule_html):
        team_name_enc = m.group(1)
        owner_id = m.group(2)
        team_name = team_name_enc.replace('%20', ' ').replace('_', ' ').strip()
        links.append((owner_id, team_name))
    return links


def extract_teams(schedule_html: str) -> List[Tuple[str, str, Optional[str]]]:
    teams: Dict[str, Tuple[str, str]] = {}
    # anchor /teams/{id}
    for m in re.finditer(r"<a href='/teams/(\d+)'>([^<]+)</a>", schedule_html):
        tid = m.group(1)
        name = m.group(2).strip()
        teams[tid] = (name, '')
    # logo urls that include team_logo/{id-...}
    for m in re.finditer(r"https://[^\s'\"]+/team_logo/(\d+)-[a-zA-Z0-9_.]+", schedule_html):
        tid = m.group(1)
        url = m.group(0)
        if tid in teams:
            teams[tid] = (teams[tid][0], url)
    return [(tid, teams[tid][0], teams[tid][1] or None) for tid in sorted(teams.keys(), key=lambda x: int(x))]


def extract_players_from_skaters(skaters_html: str) -> List[Tuple[str, str, Optional[str], Optional[str], Optional[str]]]:
    # Prefer BeautifulSoup + aria-label for reliable parsing
    results: Dict[str, Tuple[str, Optional[str], Optional[str], Optional[str]]] = {}
    if HAS_BS4:
        soup = BeautifulSoup(skaters_html, 'html.parser')
        for a in soup.find_all('a', class_='playerLink'):
            href = a.get('href') or ''
            m = re.search(r"players?/playerpage/(\d+)", href)
            if not m:
                continue
            pid = m.group(1)
            label = (a.get('aria-label') or '').strip()
            # Skip non-player entries
            if label.lower().startswith('injury report'):
                continue
            full_name: str = ''
            pos: Optional[str] = None
            team: Optional[str] = None
            if label:
                toks = label.split()
                if len(toks) >= 3:
                    pos = toks[-2]
                    team = toks[-1]
                    full_name = ' '.join(toks[:-2]).strip()
            if not full_name:
                # Fallback to anchor text
                full_name = (a.get_text() or '').strip()
            # Guard again
            if full_name.lower().startswith('injury report'):
                continue
            if (not pos) or (not team):
                # Fallback to sibling span with class playerPositionAndTeam
                span = a.find_next('span', class_='playerPositionAndTeam')
                if span:
                    p, t = parse_position_team(span.get_text())
                    pos = pos or p
                    team = team or t
            if not full_name:
                full_name = f'Player {pid}'
            results[pid] = (full_name, pos, team, None)
    else:
        # Regex fallback
        for m in re.finditer(r"/players/playerpage/(\d+)", skaters_html):
            pid = m.group(1)
            start = max(0, m.start() - 200)
            end = min(len(skaters_html), m.end() + 200)
            ctx = skaters_html[start:end]
            name_m = re.search(r"aria-label='\s*([^'<]+)\s*'", ctx)
            full_name = ''
            pos = None
            team = None
            if name_m:
                label = name_m.group(1).strip()
                if label.lower().startswith('injury report'):
                    continue
                toks = label.split()
                if len(toks) >= 3:
                    pos = toks[-2]
                    team = toks[-1]
                    full_name = ' '.join(toks[:-2]).strip()
            if not full_name:
                txt_m = re.search(r">\s*([^<]{3,100}?)\s*<", ctx)
                full_name = txt_m.group(1).strip() if txt_m else f"Player {pid}"
            if full_name.lower().startswith('injury report'):
                continue
            results[pid] = (full_name, pos, team, None)
    return [(pid, results[pid][0], results[pid][1], results[pid][2], results[pid][3]) for pid in results.keys()]


def _extract_json_object(js_text: str, marker: str) -> Optional[str]:
    """Extract a JSON object assigned to a JS var marker like 'var FantasyGlobalChatJson =' from raw text.
    Returns the JSON string or None if not found.
    """
    idx = js_text.find(marker)
    if idx == -1:
        return None
    # Find the first '{' after marker
    start = js_text.find('{', idx)
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(js_text)):
        ch = js_text[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end = i
                return js_text[start:end+1]
    return None


def extract_team_meta_from_teams_html(teams_html: str) -> Dict[str, Dict[str, Any]]:
    """Parse team metadata from embedded FantasyGlobalChatJson in teams HTML.
    Returns map of team_id -> meta dict.
    """
    out: Dict[str, Dict[str, Any]] = {}
    js = _extract_json_object(teams_html, 'var FantasyGlobalChatJson')
    if not js:
        return out
    try:
        data = json.loads(js)
    except Exception:
        # Attempt to sanitize trailing commas if any (basic)
        js2 = re.sub(r",\s*([}\]])", r"\1", js)
        try:
            data = json.loads(js2)
        except Exception:
            return out
    try:
        users = (((data or {}).get('chat_data') or {}).get('roster') or {}).get('allUsers') or []
        for u in users:
            attrib = (u or {}).get('attrib') or {}
            team = attrib.get('team') or {}
            auth = (u or {}).get('auth') or {}
            team_id = str(team.get('id') or '').strip()
            if not team_id:
                continue
            out[team_id] = {
                'team_name': team.get('name') or None,
                'abbrev': team.get('abbr') or None,
                'long_abbr': team.get('long_abbr') or None,
                'short_name': team.get('short_name') or None,
                'division': team.get('division') or None,
                'logo_url': team.get('logo') or None,
                'owner_id': auth.get('id') or None,
            }
    except Exception:
        return out
    return out


def update_teams_with_chat_meta(cur, league_id: int, team_meta: Dict[str, Dict[str, Any]]):
    if not team_meta:
        return
    rows = []
    for team_id, meta in team_meta.items():
        rows.append((
            league_id,
            team_id,
            meta.get('team_name'),
            meta.get('abbrev'),
            meta.get('long_abbr'),
            meta.get('logo_url'),
            meta.get('owner_id'),
            meta.get('short_name'),
            meta.get('division'),
        ))
    execute_batch(
        cur,
        """
        INSERT INTO cbs_teams(league_id, team_id, team_name, abbrev, long_abbr, logo_url, owner_id, short_name, division)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (league_id, team_id) DO UPDATE SET
          team_name=COALESCE(EXCLUDED.team_name, cbs_teams.team_name),
          abbrev=COALESCE(EXCLUDED.abbrev, cbs_teams.abbrev),
          long_abbr=COALESCE(EXCLUDED.long_abbr, cbs_teams.long_abbr),
          logo_url=COALESCE(EXCLUDED.logo_url, cbs_teams.logo_url),
          owner_id=COALESCE(EXCLUDED.owner_id, cbs_teams.owner_id),
          short_name=COALESCE(EXCLUDED.short_name, cbs_teams.short_name),
          division=COALESCE(EXCLUDED.division, cbs_teams.division)
        """,
        rows,
        page_size=200,
    )


def upsert_owners_from_chat_meta(cur, team_meta: Dict[str, Dict[str, Any]]):
    """Ensure any owner_id references from chat meta exist in cbs_owners."""
    if not team_meta:
        return
    owners: List[Tuple[str, Optional[str], Optional[str]]] = []
    seen: set[str] = set()
    for meta in team_meta.values():
        oid = meta.get('owner_id')
        if not oid:
            continue
        if oid in seen:
            continue
        seen.add(oid)
        display_name = None  # chat json has only owner handle; display names come from schedule users sometimes
        owners.append((oid, display_name, None))
    if not owners:
        return
    execute_batch(
        cur,
        """
        INSERT INTO cbs_owners(owner_id, display_name, email)
        VALUES (%s, %s, %s)
        ON CONFLICT (owner_id) DO NOTHING
        """,
        owners,
        page_size=200,
    )


def extract_scoring_rules(rules_html: str) -> Tuple[str, List[Tuple[str, str, float, Optional[str]]]]:
    # Scoring mode
    mode = 'Head-to-Head, Points' if 'Head-to-Head, Points' in rules_html else 'Points'
    # Table rows with stat codes
    rules: List[Tuple[str, str, float, Optional[str]]] = []
    for m in re.finditer(r"<tr[^>]*>\s*<td[^>]*>\s*([^<]{1,6})\s*</td>\s*<td[^>]*>\s*([^<]{1,64})\s*</td>\s*<td[^>]*>\s*([\-\+\d\.]+)\s*points", rules_html, re.IGNORECASE):
        code = m.group(1).strip()
        name = m.group(2).strip()
        pts = float(m.group(3))
        cat = 'goalie' if code in {'W','S','GA','SO','SHOL','OL'} else 'skater'
        rules.append((code, name, pts, cat))
    return mode, rules


def extract_roster_positions(rules_html: str) -> Dict[str, Any]:
    """Parse roster position requirements from the Rules HTML.
    Returns a JSON-serializable dict like:
      {
        "positions": {
          "C": {"active_min": 2, "active_max": 2, "roster_total": None},
          "W": {"active_min": 3, "active_max": 3, "roster_total": None},
          ...
        },
        "status_limits": {
          "Active Players": {"min": 15, "max": 15},
          "Reserve Players": {"min": 0, "max": None},
          ...
        }
      }
    """
    out: Dict[str, Any] = {"positions": {}, "status_limits": {}}
    try:
        # Status limits table (Active/Reserve/Injured/Total)
        # Rows like: <td align="left">Active Players</td><td align="right">15</td><td align="right">15</td>
        for m in re.finditer(r"<tr[^>]*>\s*<td[^>]*>\s*(Active Players|Reserve Players|Injured Players|Total Players)\s*</td>\s*<td[^>]*>\s*([^<]+?)\s*</td>\s*<td[^>]*>\s*([^<]+?)\s*</td>", rules_html, re.IGNORECASE):
            label = m.group(1).strip()
            min_txt = m.group(2).strip()
            max_txt = m.group(3).strip()
            def parse_limit(s: str) -> Optional[int]:
                s2 = s.replace(',', '').strip()
                if re.match(r"^No Limit$", s2, re.IGNORECASE):
                    return None
                try:
                    return int(s2)
                except Exception:
                    return None
            out["status_limits"][label] = {
                "min": parse_limit(min_txt),
                "max": parse_limit(max_txt),
            }
        # Position limits table
        # Rows like: <td align="left">C</td><td align="right">2</td><td align="right">2</td><td align="right">No Limit</td>
        for m in re.finditer(r"<tr[^>]*>\s*<td[^>]*>\s*([A-Z]{1,2})\s*</td>\s*<td[^>]*>\s*([^<]+?)\s*</td>\s*<td[^>]*>\s*([^<]+?)\s*</td>\s*<td[^>]*>\s*([^<]+?)\s*</td>", rules_html):
            pos = m.group(1).strip()
            min_txt = m.group(2).strip()
            max_txt = m.group(3).strip()
            total_txt = m.group(4).strip()
            # Only consider typical fantasy positions (C,W,F,D,G)
            if pos not in {"C","W","F","D","G"}:
                continue
            def parse_num(s: str) -> Optional[int]:
                s2 = s.replace(',', '').strip()
                if re.match(r"^No Limit$", s2, re.IGNORECASE):
                    return None
                try:
                    return int(s2)
                except Exception:
                    return None
            out["positions"][pos] = {
                "active_min": parse_num(min_txt),
                "active_max": parse_num(max_txt),
                "roster_total": parse_num(total_txt),
            }
    except Exception:
        pass
    return out


def db_connect(db_url: str):
    return psycopg2.connect(db_url, sslmode='require') if 'rlwy.net' in db_url else psycopg2.connect(db_url)


def upsert_league(cur, provider_slug: str, name: str, domain: str) -> int:
    cur.execute(
        """
        INSERT INTO cbs_leagues(provider_slug, name, domain)
        VALUES (%s, %s, %s)
        ON CONFLICT (provider_slug) DO UPDATE SET name=EXCLUDED.name, domain=EXCLUDED.domain
        RETURNING id
        """,
        (provider_slug, name, domain),
    )
    league_id = cur.fetchone()[0]
    return league_id


def upsert_rules(cur, league_id: int, mode: str, roster_positions: Optional[Dict[str, Any]] = None):
    cur.execute(
        """
        INSERT INTO cbs_league_rules(league_id, scoring_mode, roster_positions)
        VALUES (%s, %s, %s)
        ON CONFLICT (league_id) DO UPDATE SET
          scoring_mode=EXCLUDED.scoring_mode,
          roster_positions=COALESCE(EXCLUDED.roster_positions, cbs_league_rules.roster_positions)
        """,
        (league_id, mode, json.dumps(roster_positions) if roster_positions else None),
    )


def upsert_scoring_rules(cur, league_id: int, rules: List[Tuple[str, str, float, Optional[str]]]):
    if not rules:
        return
    execute_batch(
        cur,
        """
        INSERT INTO cbs_scoring_rules(league_id, stat_code, stat_name, points, category)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (league_id, stat_code) DO UPDATE SET stat_name=EXCLUDED.stat_name, points=EXCLUDED.points, category=EXCLUDED.category
        """,
        [(league_id, code, name, pts, cat) for code, name, pts, cat in rules],
        page_size=200,
    )


def upsert_owners(cur, owners: List[Tuple[str, Optional[str], Optional[str]]]):
    if not owners:
        return
    execute_batch(
        cur,
        """
        INSERT INTO cbs_owners(owner_id, display_name, email)
        VALUES (%s, %s, %s)
        ON CONFLICT (owner_id) DO UPDATE SET display_name=COALESCE(EXCLUDED.display_name, cbs_owners.display_name), email=COALESCE(EXCLUDED.email, cbs_owners.email)
        """,
        owners,
        page_size=200,
    )


def upsert_teams(cur, league_id: int, teams: List[Tuple[str, str, Optional[str]]]):
    if not teams:
        return
    execute_batch(
        cur,
        """
        INSERT INTO cbs_teams(league_id, team_id, team_name, logo_url)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (league_id, team_id) DO UPDATE SET team_name=EXCLUDED.team_name, logo_url=EXCLUDED.logo_url
        """,
        [(league_id, tid, name, logo) for (tid, name, logo) in teams],
        page_size=200,
    )


def link_owners_to_teams(cur, league_id: int, owner_team_links: List[Tuple[str, str]]):
    if not owner_team_links:
        return
    # update team.owner_id by team_name match, and ensure league-owner membership exists
    for owner_id, team_name in owner_team_links:
        # set owner_id on team (best-effort by name)
        cur.execute(
            """
            UPDATE cbs_teams SET owner_id=%s
            WHERE league_id=%s AND team_name=%s
            """,
            (owner_id, league_id, team_name),
        )
        # add league-owner
        cur.execute(
            """
            INSERT INTO cbs_league_owners(league_id, owner_id, role)
            VALUES (%s, %s, %s)
            ON CONFLICT (league_id, owner_id) DO NOTHING
            """,
            (league_id, owner_id, 'owner'),
        )


def upsert_players(cur, players: List[Tuple[str, str, Optional[str], Optional[str], Optional[str]]]):
    if not players:
        return
    execute_batch(
        cur,
        """
        INSERT INTO cbs_players(cbs_player_id, full_name, pos_primary, nhl_team_abbr, shoots)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (cbs_player_id) DO UPDATE SET full_name=EXCLUDED.full_name, pos_primary=COALESCE(EXCLUDED.pos_primary, cbs_players.pos_primary), nhl_team_abbr=COALESCE(EXCLUDED.nhl_team_abbr, cbs_players.nhl_team_abbr)
        """,
        players,
        page_size=500,
    )


# --- New: BeautifulSoup parsing for teams page (rosters and summaries) ---

def parse_position_team(text: str) -> Tuple[Optional[str], Optional[str]]:
    # expects like "C •COL" or "G •MIN"
    if not text:
        return None, None
    parts = re.split(r"\s+•\s+", text.strip())
    if len(parts) == 2:
        pos = parts[0].strip()
        team = parts[1].strip()
        if pos in {"C","W","D","G"}:
            return pos, team
    return None, None


def parse_team_footer_summary(text: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if not text:
        return out
    m = re.search(r"Active:\s*(\d+)", text)
    if m:
        out["active_count"] = int(m.group(1))
    m = re.search(r"Reserve:\s*(\d+)", text)
    if m:
        out["reserve_count"] = int(m.group(1))
    m = re.search(r"Injured:\s*(\d+)", text)
    if m:
        out["injured_count"] = int(m.group(1))
    m = re.search(r"Active salary:\s*([\d\.]+)", text)
    if m:
        out["active_salary"] = float(m.group(1))
    m = re.search(r"Total salary:\s*([\d\.]+)", text)
    if m:
        out["total_salary"] = float(m.group(1))
    return out


def extract_rosters_from_teams_html(teams_html: str) -> Dict[str, Dict[str, Any]]:
    if not HAS_BS4:
        return {}
    soup = BeautifulSoup(teams_html, 'html.parser')
    results: Dict[str, Dict[str, Any]] = {}
    # Stream through document, maintain current team_id based on last seen team_logo image
    current_team_id: Optional[str] = None
    for el in soup.descendants:
        if not isinstance(el, bs4_element.Tag):
            continue
        if el.name == 'img':
            src = el.get('src') or ''
            m = re.search(r"team_logo/(\d+)-", src)
            if m:
                current_team_id = m.group(1)
                results.setdefault(current_team_id, {"players": [], "summary": {}, "raw_meta": {}})
                continue
        if el.name == 'a' and 'playerLink' in (el.get('class') or []):
            href = el.get('href') or ''
            m = re.search(r"playerpage/(\d+)", href)
            if not m or not current_team_id:
                continue
            cbs_player_id = m.group(1)
            name = (el.get_text() or '').strip()
            # row context
            tr = el.find_parent('tr')
            pos, nhl_abbr = (None, None)
            salary_val: Optional[float] = None
            years_val: Optional[int] = None
            if tr:
                pos_span = tr.find('span', class_='playerPositionAndTeam')
                pos, nhl_abbr = parse_position_team(pos_span.get_text() if pos_span else '')
                # try parse salary/years from numeric cells in row
                tds = tr.find_all('td')
                nums: List[str] = []
                for td in tds:
                    txt = (td.get_text() or '').strip().replace('$','')
                    if re.fullmatch(r"\d{1,2}", txt) or re.fullmatch(r"\d+\.\d+", txt):
                        nums.append(txt)
                # Heuristic: years is a small int <= 10; salary is decimal with dot
                for n in nums:
                    if re.fullmatch(r"\d+\.\d+", n):
                        try:
                            salary_val = float(n)
                        except:
                            pass
                for n in nums:
                    if re.fullmatch(r"\d{1,2}", n):
                        try:
                            val = int(n)
                            if 0 <= val <= 12:
                                years_val = val
                        except:
                            pass
            t = results.setdefault(current_team_id, {"players": [], "summary": {}, "raw_meta": {}})
            t["players"].append({
                "cbs_player_id": cbs_player_id,
                "full_name": name,
                "pos_primary": pos,
                "nhl_team_abbr": nhl_abbr,
                "salary": salary_val,
                "years": years_val,
            })
        if el.name == 'tr' and 'footer' in (el.get('class') or []):
            td = el.find('td')
            if not td or not current_team_id:
                continue
            text = td.get_text(strip=True)
            summary = parse_team_footer_summary(text)
            t = results.setdefault(current_team_id, {"players": [], "summary": {}, "raw_meta": {}})
            t["summary"].update(summary)
    return results


def extract_rosters_by_headers(teams_html: str, teamname_to_id: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
    if not HAS_BS4:
        return {}
    soup = BeautifulSoup(teams_html, 'html.parser')
    results: Dict[str, Dict[str, Any]] = {}
    # Find all header cells like "<td colspan="13">{Team Name} Skaters</td>"
    headers = soup.find_all('td', attrs={'colspan': re.compile(r'^13$')})
    for hd in headers:
        header_text = (hd.get_text() or '').strip()
        if not header_text:
            continue
        if not (header_text.endswith('Skaters') or header_text.endswith('Goalies')):
            continue
        team_name = header_text.replace(' Skaters', '').replace(' Goalies', '').strip()
        team_id = teamname_to_id.get(team_name)
        if not team_id:
            # try relaxed matching without spaces/underscores
            key = re.sub(r"\s+", ' ', team_name).strip().lower()
            for tn, tid in teamname_to_id.items():
                if re.sub(r"\s+", ' ', tn).strip().lower() == key:
                    team_id = tid
                    break
        if not team_id:
            continue
        # Collect rows until next header or end
        container_tr = hd.find_parent('tr')
        if not container_tr:
            continue
        section_players: List[Dict[str, Any]] = []
        footer_summary: Dict[str, Any] = {}
        node = container_tr.next_sibling
        while node:
            if isinstance(node, bs4_element.Tag):
                # stop if another header cell encountered
                td_col = node.find('td', attrs={'colspan': re.compile(r'^13$')})
                if td_col and (td_col.get_text() or '').strip() and td_col is not hd:
                    break
                # parse player rows
                for a in node.find_all('a', class_='playerLink'):
                    href = a.get('href') or ''
                    m = re.search(r"playerpage/(\d+)", href)
                    if not m:
                        continue
                    cbs_player_id = m.group(1)
                    name = (a.get_text() or '').strip()
                    tr = a.find_parent('tr')
                    pos, nhl_abbr = (None, None)
                    salary_val: Optional[float] = None
                    years_val: Optional[int] = None
                    if tr:
                        pos_span = tr.find('span', class_='playerPositionAndTeam')
                        pos, nhl_abbr = parse_position_team(pos_span.get_text() if pos_span else '')
                        tds = tr.find_all('td')
                        # Salary and years often in trailing numeric columns; parse smartly
                        for td in reversed(tds):
                            txt = (td.get_text() or '').strip().replace('$','')
                            if not txt:
                                continue
                            if years_val is None and re.fullmatch(r"\d{1,2}", txt):
                                try:
                                    ival = int(txt)
                                    if 0 <= ival <= 12:
                                        years_val = ival
                                        continue
                                except:
                                    pass
                            if salary_val is None and re.fullmatch(r"\d+\.\d+", txt):
                                try:
                                    salary_val = float(txt)
                                except:
                                    pass
                        # fallback: if salary_val not found but a number like 79.00 exists anywhere
                        if salary_val is None:
                            for td in tds:
                                txt = (td.get_text() or '').strip().replace('$','')
                                if re.fullmatch(r"\d+\.\d+", txt):
                                    try:
                                        salary_val = float(txt)
                                        break
                                    except:
                                        pass
                    section_players.append({
                        'cbs_player_id': cbs_player_id,
                        'full_name': name,
                        'pos_primary': pos,
                        'nhl_team_abbr': nhl_abbr,
                        'salary': salary_val,
                        'years': years_val,
                    })
                # parse footer summary if present
                if 'footer' in (node.get('class') or []):
                    td = node.find('td')
                    if td:
                        footer_summary.update(parse_team_footer_summary(td.get_text(strip=True)))
            node = node.next_sibling
        # assign collected
        if section_players or footer_summary:
            t = results.setdefault(team_id, {"players": [], "summary": {}, "raw_meta": {}})
            t["players"].extend(section_players)
            t["summary"].update(footer_summary)
    return results


def update_team_summaries(cur, league_id: int, team_id: str, summary: Dict[str, Any]):
    # columns removed; keep as no-op for compatibility
    return


def ensure_roster_players_exist(cur, roster_players: List[Dict[str, Any]]):
    if not roster_players:
        return
    rows = []
    for p in roster_players:
        pid = p.get('cbs_player_id')
        if not pid:
            continue
        rows.append((pid, p.get('full_name') or f'Player {pid}', p.get('pos_primary'), p.get('nhl_team_abbr'), None))
    if not rows:
        return
    execute_batch(
        cur,
        """
        INSERT INTO cbs_players(cbs_player_id, full_name, pos_primary, nhl_team_abbr, shoots)
        VALUES (%s,%s,%s,%s,%s)
        ON CONFLICT (cbs_player_id) DO NOTHING
        """,
        rows,
        page_size=500,
    )


def upsert_rosters(cur, league_id: int, team_id: str, players: List[Dict[str, Any]], season: Optional[int] = None):
    if not players:
        return
    # Ensure all roster players exist in cbs_players (covers draft pick placeholders)
    ensure_roster_players_exist(cur, players)
    # simple strategy: delete existing rows for team+season=None to avoid duplicates, then insert
    cur.execute(
        "DELETE FROM cbs_rosters WHERE league_id=%s AND team_id=%s AND (season IS NULL OR season=%s)",
        (league_id, team_id, season),
    )
    rows = []
    for idx, p in enumerate(players):
        rows.append(
            (
                league_id,
                team_id,
                season,
                p.get('cbs_player_id'),
                'roster',  # slot_type placeholder
                None,  # status
                None,  # acquired_via
                p.get('salary'),  # salary
                p.get('years'),   # years
                None,  # effective_from
                None,  # effective_to
                None,  # source_url
                None,  # future_fa
                idx,   # roster_order
            )
        )
    execute_batch(
        cur,
        """
        INSERT INTO cbs_rosters(
            league_id, team_id, season, cbs_player_id, slot_type, status, acquired_via, salary, years,
            effective_from, effective_to, source_url, future_fa, roster_order
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        rows,
        page_size=500,
    )


def main():
    ap = argparse.ArgumentParser(description='Import CBS league data from saved HTML files into Postgres')
    ap.add_argument('--db-url', default=os.getenv('CBS_DB_URL') or 'postgresql://postgres:WbUPvsoAtcwLhxCDMPOygaFHuALRTcWa@shuttle.proxy.rlwy.net:34371/railway')
    ap.add_argument('--base-dir', default='docs/CBS')
    ap.add_argument('--league-header', default='Header')
    ap.add_argument('--league-schedule', default='schedule')
    ap.add_argument('--league-rules', default='rules')
    ap.add_argument('--league-teams', default='teams')
    ap.add_argument('--league-skaters', default='skaters')
    ap.add_argument('--league-goalies', default='goalies')
    args = ap.parse_args()

    header_html = read_text(os.path.join(args.base_dir, args.league_header))
    schedule_html = read_text(os.path.join(args.base_dir, args.league_schedule))
    rules_html = read_text(os.path.join(args.base_dir, args.league_rules))
    teams_html = read_text(os.path.join(args.base_dir, args.league_teams))
    skaters_html = read_text(os.path.join(args.base_dir, args.league_skaters))
    goalies_html = read_text(os.path.join(args.base_dir, args.league_goalies)) if os.path.exists(os.path.join(args.base_dir, args.league_goalies)) else ''

    provider_slug, league_name, domain = extract_league_identity(header_html, schedule_html)
    owners = extract_owners(schedule_html)
    teams = extract_teams(schedule_html)
    owner_team_links = extract_owner_team_links(schedule_html)
    scoring_mode, scoring = extract_scoring_rules(rules_html)
    roster_positions = extract_roster_positions(rules_html)
    players = extract_players_from_skaters(skaters_html)
    # Also include goalies list if provided
    if goalies_html:
        players_goalies = extract_players_from_skaters(goalies_html)
        # Merge, prefer skaters data but add missing
        seen = {p[0] for p in players}
        for row in players_goalies:
            if row[0] not in seen:
                players.append(row)
    # New: parse team metadata from embedded chat JSON within teams page
    team_meta = extract_team_meta_from_teams_html(teams_html)

    # Parse rosters and team summaries from teams.html (BeautifulSoup)
    team_rosters = extract_rosters_from_teams_html(teams_html) if HAS_BS4 else {}

    conn = db_connect(args.db_url)
    cur = conn.cursor()
    try:
        cur.execute('BEGIN')
        league_id = upsert_league(cur, provider_slug, league_name, domain)
        upsert_rules(cur, league_id, scoring_mode, roster_positions)
        upsert_scoring_rules(cur, league_id, scoring)
        upsert_owners(cur, owners)
        upsert_teams(cur, league_id, teams)
        link_owners_to_teams(cur, league_id, owner_team_links)
        # Ensure owners from chat meta exist before setting owner_id on teams
        upsert_owners_from_chat_meta(cur, team_meta)
        # Apply team metadata for abbrev/short_name/division/logo/owner_id
        update_teams_with_chat_meta(cur, league_id, team_meta)
        upsert_players(cur, players)
        # Apply team summaries and rosters
        for team_id, data in team_rosters.items():
            update_team_summaries(cur, league_id, team_id, data.get('summary', {}))
            upsert_rosters(cur, league_id, team_id, data.get('players', []), season=None)
        conn.commit()
        print(f"Imported league={provider_slug} name='{league_name}' owners={len(owners)} teams={len(teams)} players={len(players)} rosters={len(team_rosters)}")
    except Exception as e:
        conn.rollback()
        print('Import error:', e)
        sys.exit(1)
    finally:
        cur.close(); conn.close()


if __name__ == '__main__':
    main()


