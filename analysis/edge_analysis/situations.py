import json
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional


@dataclass
class FrameState:
    t: int
    puck: Tuple[float, float]
    puck_speed: float
    players: Dict[int, Tuple[float, float, float]]  # player_id -> (x, y, speed)


class SituationClassifier:
    """
    Classifies goal situations from NHL-style tracking goal_*_complete.json files.

    Outputs:
      - start_type: one of
          ['Breakaway', 'DZ Turnover', 'NZ Turnover', 'Rush Entry', 'In-Zone Start']
      - play_actions: dict of booleans
          {
            'is_rebound': bool,
            'is_netfront': bool,
            'is_east_west': bool,
            'is_cross_slot': bool,
            'is_low_to_high': bool,
          }
    """

    def __init__(self, rink_length: float = 2000.0):
        self.rink_length = rink_length  # same units as tracking (inches-ish)

    # ---------- basic utilities ----------

    @staticmethod
    def distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def load_goal(self, path: str) -> Dict:
        with open(path, "r") as f:
            return json.load(f)

    def parse_frames(self, goal: Dict) -> List[FrameState]:
        players = goal["players"]
        idx_to_player_id: Dict[int, int] = {}
        for i, p in enumerate(players):
            if i == 0:
                continue  # index 0 is puck
            idx_to_player_id[i] = p["id"]

        frames: List[FrameState] = []
        for row in goal["data"]:
            t = int(row[0])
            puck_x, puck_y, puck_speed = float(row[1]), float(row[2]), float(row[3])
            players_state: Dict[int, Tuple[float, float, float]] = {}
            base = 4
            for idx in range(1, len(players)):
                pid = idx_to_player_id[idx]
                col = base + (idx - 1) * 3
                x, y, s = row[col], row[col + 1], row[col + 2]
                if x is None or y is None:
                    continue
                players_state[pid] = (float(x), float(y), float(s))
            frames.append(FrameState(t=t, puck=(puck_x, puck_y),
                                     puck_speed=puck_speed, players=players_state))
        return frames

    def teams_map(self, goal: Dict) -> Dict[int, str]:
        """player_id -> team string"""
        return {p["id"]: p.get("team", "") for p in goal["players"] if p["id"] != 1}

    def infer_attack_direction(self, frames: List[FrameState]) -> int:
        """
        Returns +1 if attacking towards increasing x, -1 if towards decreasing x.
        Uses final puck x to infer which side is offensive zone.
        """
        last = frames[-1]
        center = self.rink_length / 2
        return +1 if last.puck[0] > center else -1

    def offensive_zone_time(self, frames: List[FrameState], goal: Dict) -> float:
        """Approximate OZ time as time since puck crossed the center line in attack direction."""
        fps = goal.get("config", {}).get("fps", 16.94)
        direction = self.infer_attack_direction(frames)
        center = self.rink_length / 2

        first_oz_idx = None
        for i, fr in enumerate(frames):
            x = fr.puck[0]
            if (direction == +1 and x >= center) or (direction == -1 and x <= center):
                first_oz_idx = i
                break

        if first_oz_idx is None:
            return 0.0
        return (len(frames) - first_oz_idx) / fps

    # ---------- possession / turnover detection ----------

    def closest_team_to_puck(self, fr: FrameState, team_by_player: Dict[int, str]) -> Optional[str]:
        best_team = None
        best_d = None
        for pid, (x, y, s) in fr.players.items():
            team = team_by_player.get(pid, "")
            if not team:
                continue
            d = self.distance(fr.puck, (x, y))
            if best_d is None or d < best_d:
                best_d = d
                best_team = team
        return best_team

    def detect_turnover_zone(self, goal: Dict, frames: List[FrameState]) -> Optional[str]:
        """
        Returns 'DZ', 'NZ', 'OZ' or None for the *first* turnover where scoring team gains possession.
        Zone is relative to scoring team's attack direction.
        """
        scorer_id = goal["event"]["scorer_id"]
        team_by_player = self.teams_map(goal)
        scoring_team = team_by_player.get(scorer_id, "")
        if not scoring_team:
            return None

        fps = goal.get("config", {}).get("fps", 16.94)
        direction = self.infer_attack_direction(frames)
        center = self.rink_length / 2
        # Use thirds of rink as DZ / NZ / OZ
        third = self.rink_length / 3

        def zone_of_x(x: float) -> str:
            if direction == +1:
                if x < third:       # left third
                    return "DZ"
                elif x < 2 * third: # middle third
                    return "NZ"
                else:
                    return "OZ"
            else:
                # attacking left, so flip
                if x > 2 * third:
                    return "DZ"
                elif x > third:
                    return "NZ"
                else:
                    return "OZ"

        # track team with possession over time
        prev_team = None
        for i, fr in enumerate(frames):
            team_now = self.closest_team_to_puck(fr, team_by_player)
            if prev_team is None:
                prev_team = team_now
                continue
            if team_now is None:
                prev_team = team_now
                continue
            # turnover moment: previous team != scoring team, now scoring team
            if prev_team != scoring_team and team_now == scoring_team:
                # turnover location
                z = zone_of_x(fr.puck[0])
                return z
            prev_team = team_now

        return None

    # ---------- start-type classifier ----------

    def classify_start_type(self, goal: Dict, frames: List[FrameState]) -> str:
        scorer_id = goal["event"]["scorer_id"]
        team_by_player = self.teams_map(goal)
        scoring_team = team_by_player.get(scorer_id, "")
        if not scoring_team:
            scoring_team = ""

        fps = goal.get("config", {}).get("fps", 16.94)
        last = frames[-1]
        direction = self.infer_attack_direction(frames)

        # shooter position at goal frame
        shooter_pos = last.players.get(scorer_id)
        if shooter_pos is None:
            # fallback: closest scoring-team player to puck
            best = None
            best_d = None
            for pid, (x, y, s) in last.players.items():
                if team_by_player.get(pid) != scoring_team:
                    continue
                d = self.distance(last.puck, (x, y))
                if best_d is None or d < best_d:
                    best_d = d
                    best = (x, y, s)
            shooter_pos = best

        # 1) Breakaway check
        if shooter_pos is not None and scoring_team:
            sh_x, sh_y, sh_s = shooter_pos
            gap_min = None
            ahead = True
            for pid, (x, y, s) in last.players.items():
                if team_by_player.get(pid) == scoring_team:
                    continue
                d = self.distance((sh_x, sh_y), (x, y))
                if gap_min is None or d < gap_min:
                    gap_min = d
                # if any defender is "ahead" of shooter, not a breakaway
                if (direction == +1 and x > sh_x) or (direction == -1 and x < sh_x):
                    ahead = False
            if ahead and gap_min is not None and gap_min > 180.0:
                return "Breakaway"

        # 2) Turnover zone (if any)
        turnover_zone = self.detect_turnover_zone(goal, frames)
        if turnover_zone == "DZ":
            return "DZ Turnover"
        if turnover_zone == "NZ":
            return "NZ Turnover"

        # 3) Rush vs In-Zone
        oz_time = self.offensive_zone_time(frames, goal)
        if oz_time < 7.0:
            return "Rush Entry"
        else:
            return "In-Zone Start"

    # ---------- play-action classifiers ----------

    def compute_play_actions(self, goal: Dict, frames: List[FrameState]) -> Dict[str, bool]:
        """
        Returns dict of:
          is_rebound, is_netfront, is_east_west, is_cross_slot, is_low_to_high
        """
        fps = goal.get("config", {}).get("fps", 16.94)
        last = frames[-1]
        center_y = 0.0  # assuming y=0 is center line; adjust if needed

        # last ~2 sec window
        tail_2s = frames[-int(fps*2):] if len(frames) > fps*2 else frames
        tail_1s = frames[-int(fps*1):] if len(frames) > fps else frames

        # --- rebound ---
        speeds = [fr.puck_speed for fr in tail_2s]
        is_rebound = False
        if len(speeds) >= 3:
            # simple heuristic: prior speeds show big drop then big increase
            prev = speeds[:-1]
            if min(prev) < 5.0 and max(prev) > 10.0:
                is_rebound = True

        # --- netfront / crease battle ---
        # find goalie position (deepest in its own end)
        team_by_player = self.teams_map(goal)
        scorer_id = goal["event"]["scorer_id"]
        scoring_team = team_by_player.get(scorer_id, "")
        goalie_team = None
        for p in goal["players"]:
            if p.get("pos") == "G" and p.get("team") != scoring_team:
                goalie_team = p["team"]
                break

        goalie_pos_xy = None
        if goalie_team is not None:
            deep = None
            for pid, (x, y, s) in last.players.items():
                if team_by_player.get(pid) != goalie_team:
                    continue
                if deep is None:
                    deep = (x, y, s)
                else:
                    # goalie is the one furthest back in its own zone
                    if abs(x - self.rink_length/2) > abs(deep[0] - self.rink_length/2):
                        deep = (x, y, s)
            if deep is not None:
                goalie_pos_xy = (deep[0], deep[1])

        is_netfront = False
        if goalie_pos_xy is not None:
            # puck close to goalie AND several players close
            puck_d = self.distance(last.puck, goalie_pos_xy)
            close_players = 0
            for pid, (x, y, s) in last.players.items():
                if self.distance((x, y), goalie_pos_xy) < 300.0:
                    close_players += 1
            if puck_d < 300.0 and close_players >= 3:
                is_netfront = True

        # --- east-west / royal road & cross-slot ---
        is_east_west = False
        is_cross_slot = False
        if len(tail_1s) >= 2:
            start = tail_1s[0]
            dy = last.puck[1] - start.puck[1]
            # sign change across center: royal road
            crosses_center = (start.puck[1] - center_y) * (last.puck[1] - center_y) < 0
            if abs(dy) > 200.0 and crosses_center:
                is_east_west = True
            elif abs(dy) > 200.0 and not crosses_center:
                is_cross_slot = True

        # --- low-to-high ---
        # look back ~2 seconds: low y magnitude -> high |y| magnitude OR low x near goal line -> higher x
        # here we use x as "depth": smaller |x - goal_line| => low, larger => high, but with your coords
        # a simpler heuristic: in offensive zone, early frame near goalie in x then moves toward blue line
        direction = self.infer_attack_direction(frames)
        center_x = self.rink_length / 2
        # pick first frame in last 2s where puck is clearly "low"
        low_frame = None
        high_frame = None
        for fr in reversed(tail_2s):
            # we scan backwards: mark the earliest "low" and latest "high"
            x = fr.puck[0]
            # low in OZ: close to end boards in attack direction
            if direction == +1 and x > center_x and (self.rink_length - x) < 300:
                low_frame = fr
                break
            if direction == -1 and x < center_x and (x) < 300:
                low_frame = fr
                break
        if low_frame is not None:
            # now find a later frame (closer to goal frame) where puck is further from boards (toward point)
            for fr in tail_2s:
                if fr.t <= low_frame.t:
                    continue
                x = fr.puck[0]
                if direction == +1 and x > center_x and (self.rink_length - x) > 400:
                    high_frame = fr
                    break
                if direction == -1 and x < center_x and x > 400:
                    high_frame = fr
                    break

        is_low_to_high = high_frame is not None

        return {
            "is_rebound": is_rebound,
            "is_netfront": is_netfront,
            "is_east_west": is_east_west,
            "is_cross_slot": is_cross_slot,
            "is_low_to_high": is_low_to_high,
        }

    # ---------- full API ----------

    def classify_goal(self, goal: Dict) -> Dict[str, object]:
        frames = self.parse_frames(goal)
        start_type = self.classify_start_type(goal, frames)
        play_actions = self.compute_play_actions(goal, frames)
        return {
            "start_type": start_type,
            **play_actions,
        }


# Example usage:
if __name__ == "__main__":
    import os

    classifier = SituationClassifier()
    base = "/path/to/your/goals"  # <-- change to your directory

    files = [
        "goal_4_complete.json",
        "goal_585_complete.json",
        "goal_596_complete.json",
        "goal_857_complete.json",
        "goal_1018_complete.json",
        "goal_465_complete.json",
        "goal_489_complete.json",
        "goal_745_complete.json",
        "goal_763_complete.json",
        "goal_780_complete.json",
    ]

    for fn in files:
        path = os.path.join(base, fn)
        with open(path, "r") as f:
            goal = json.load(f)
        result = classifier.classify_goal(goal)
        print(fn, "→", result)
