import os
import json


def build_auction_input(base_dir: str) -> str:
    s1_path = os.path.join(base_dir, 'stage1', 'stage1_rollforward.json')
    s3_path = os.path.join(base_dir, 'stage3', 'stage3_rookie_draft.json')
    out_path = os.path.join(base_dir, 'stage4', 'auction_input.json')

    with open(s1_path, 'r') as f:
        stage1 = json.load(f)
    try:
        with open(s3_path, 'r') as f:
            stage3 = json.load(f)
    except Exception:
        stage3 = {}

    # Capture current rosters (teams) and free agents (post Stage 2 updates)
    payload = {
        "teams": stage1.get('teams', []),
        "caps": stage1.get('caps', {}),
        "free_agents": stage1.get('free_agents', []),
        "rookie_draft": stage3,
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(payload, f, indent=2)
    return out_path


def main():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    p = build_auction_input(base)
    print(p)


if __name__ == '__main__':
    main()


