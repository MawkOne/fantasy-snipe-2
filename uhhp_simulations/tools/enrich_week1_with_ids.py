import os
import json
import re
import unicodedata
from typing import Dict, List, Optional, Tuple

from sqlalchemy import create_engine, text


EXT_DB = "postgresql://postgres:new-password-123@34.47.23.137:5432/postgres"


def normalize_ascii_lower(s: str) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii").strip().lower()


def parse_roster_display_to_full_name(display: str) -> Tuple[str, Optional[str]]:
    """
    Convert roster display formats like:
    - "McDavid, Connor C EDM" -> ("Connor McDavid", "C")
    - "Connor McDavid" -> ("Connor McDavid", None)
    - "Frost, Morgan C CGY" -> ("Morgan Frost", "C")
    - Handles bullets, extra spaces, unicode bullets, and leaves z-CAPHIT/Draft as-is
    Returns (full_name_like, position_or_none)
    """
    if not display:
        return "", None

    s = (display or "").strip()
    # Remove unicode bullets and weird separators
    s = re.sub(r"[\u2022\u00B7]", " ", s)
    s = re.sub(r"\s+", " ", s)

    # z-CAPHIT and Draft: return as-is
    if normalize_ascii_lower(s).startswith("z-caphit"):
        return s, None
    if normalize_ascii_lower(s) == "draft":
        return s, None

    # Split tokens and strip trailing team/pos combos like "C EDM" or "RW TOR"
    tokens = s.split()
    pos = None
    if len(tokens) >= 2:
        last = tokens[-1]
        prev = tokens[-2]
        if re.fullmatch(r"[A-Z]{2,3}", last) and re.fullmatch(r"[A-Z]{1,2}W|[CDG]", prev):
            pos = prev
            tokens = tokens[:-2]

    # Rejoin and flip Last, First
    joined = " ".join(tokens)
    if "," in joined:
        last, first = [p.strip() for p in joined.split(",", 1)]
        full = f"{first} {last}"
    else:
        full = joined

    full = re.sub(r"\s+", " ", full).strip()
    return full, pos


def build_player_key(engine) -> Dict[str, Dict[str, Optional[str]]]:
    """
    Build a normalized name -> {id, full_name, position_code} mapping from external DB players table.
    Includes variants: "first last" and "last first" forms, all lowercased/ascii-normalized.
    """
    key: Dict[str, Dict[str, Optional[str]]] = {}
    with engine.connect() as conn:
        rows = conn.execute(text(
            """
            SELECT id, full_name, position_code
            FROM players
            WHERE full_name IS NOT NULL
            """
        )).fetchall()
    for r in rows:
        pid = int(r[0])
        full = (r[1] or "").strip()
        pos = (r[2] or "").strip() or None
        if not full:
            continue
        norm = normalize_ascii_lower(full)
        key[norm] = {"id": pid, "full_name": full, "position_code": pos}
        # Add flipped variant if looks like "First Last"
        parts = full.split()
        if len(parts) >= 2:
            first = parts[0]
            last = parts[-1]
            flipped = normalize_ascii_lower(f"{last} {first}")
            key.setdefault(flipped, {"id": pid, "full_name": full, "position_code": pos})
    return key


def best_match(player_key: Dict[str, Dict[str, Optional[str]]], name: str, pos_hint: Optional[str]) -> Tuple[Optional[int], Optional[str]]:
    norm = normalize_ascii_lower(name)
    hit = player_key.get(norm)
    if hit:
        return int(hit["id"]), str(hit["full_name"]) if hit.get("full_name") else name

    # Try coarse fuzzy using simple subsequence/startswith heuristics
    # Gather candidates sharing last token
    parts = norm.split()
    if parts:
        last = parts[-1]
        cand = [v for k, v in player_key.items() if k.endswith(" " + last) or k.startswith(last + " ")]
        # If pos_hint provided, try to prefer position matches
        if pos_hint:
            cand_pos = [c for c in cand if (c.get("position_code") or "").upper().startswith(pos_hint[0])]
            if cand_pos:
                cand = cand_pos
        if cand:
            # Pick the one with longest common subsequence approximation via overlap length
            def score(c):
                nm = normalize_ascii_lower(c.get("full_name") or "")
                return len(set(nm.split()) & set(parts))
            cand.sort(key=score, reverse=True)
            top = cand[0]
            return int(top["id"]), str(top.get("full_name") or name)
    return None, None


def enrich_week1(input_path: str, output_path: str, engine) -> None:
    try:
        with open(input_path, "r") as f:
            data = json.load(f)
    except Exception:
        data = {}

    if not isinstance(data, dict) or not data:
        # write empty enriched structure for consistency
        with open(output_path, "w") as f:
            json.dump({}, f, indent=2)
        return

    player_key = build_player_key(engine)

    enriched: Dict[str, List[Dict]] = {}
    for team, roster in data.items():
        out: List[Dict] = []
        if not isinstance(roster, list):
            enriched[team] = out
            continue
        for raw in roster:
            if not isinstance(raw, str):
                continue
            full, pos = parse_roster_display_to_full_name(raw)
            # Skip cap hits and Draft entries; keep as metadata
            if normalize_ascii_lower(full).startswith("z-caphit") or normalize_ascii_lower(full) == "draft":
                out.append({
                    "display_name": raw,
                    "parsed_name": full,
                    "position_hint": pos,
                    "player_id": None,
                    "player_full_name": None,
                    "note": "non-player-entry"
                })
                continue

            pid, resolved_name = best_match(player_key, full, pos)
            out.append({
                "display_name": raw,
                "parsed_name": full,
                "position_hint": pos,
                "player_id": pid,
                "player_full_name": resolved_name if resolved_name else None,
            })
        enriched[team] = out

    with open(output_path, "w") as f:
        json.dump(enriched, f, indent=2)


def main():
    engine_ext = create_engine(EXT_DB)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uhhp_simulations", "outputs"))
    # Fallback: if running from tools/, derive outputs directory relative to project
    if not os.path.isdir(base_dir):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs"))

    targets = [
        (os.path.join(base_dir, "week1_rosters_2022.json"), os.path.join(base_dir, "week1_rosters_2022_enriched.json")),
        (os.path.join(base_dir, "week1_rosters_2023.json"), os.path.join(base_dir, "week1_rosters_2023_enriched.json")),
        (os.path.join(base_dir, "week1_rosters_2024.json"), os.path.join(base_dir, "week1_rosters_2024_enriched.json")),
    ]

    for src, dst in targets:
        enrich_week1(src, dst, engine_ext)


if __name__ == "__main__":
    main()


