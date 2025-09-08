#!/usr/bin/env python3
import os
import sys

# Scripts to remove (25 total)
scripts_to_remove = [
    # One-time enrichment scripts (COMPLETED)
    "run_enrich_for_games_2024.py",
    "backfill_game_events_enrich_for_game.py", 
    "backfill_sqlset_for_game.py",
    "test_backfill_sqlset.py",
    "backfill_game_events_from_raw.py",
    "alter_game_events_expand.py",
    
    # QA/Diagnostic scripts (One-time use)
    "qa_fields_for_games_list.py",
    "qa_enrich_progress.py", 
    "count_presence_across_games.py",
    "count_games_missing_fields.py",
    "find_games_with_fields.py",
    "list_raw_fields_for_game.py",
    "qa_game_events_for_game.py",
    
    # Zero records fix scripts (RESOLVED)
    "backfill_zero_shifts.py",
    "delete_zeros_for_game.py",
    "diagnose_game_zero_rows.py", 
    "delete_zero_rows.py",
    "start_backfill_zeros.sh",
    
    # Obsolete/Unused scripts
    "shift_metrics_background_worker.py",
    "debug_event_overlap.py",
    "verify_coords_coverage.py",
    "populate_pbp_for_player.py",
    "diagnose_shift.py",
    "scan_player_game_shifts.py",
    
    # Legacy population scripts (redundant)
    "populate_schedule_by_date.py",
    "populate_game_logs.py",
    "populate_player_details.py",
    "populate_player_career_stats_api.py",
    "populate_player_career_stats.py",
    "populate_goalies.py",
]

def main():
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    removed_count = 0
    
    print("Removing obsolete scripts...")
    print("=" * 50)
    
    for script in scripts_to_remove:
        script_path = os.path.join(scripts_dir, script)
        if os.path.exists(script_path):
            try:
                os.remove(script_path)
                print(f"✓ Removed: {script}")
                removed_count += 1
            except Exception as e:
                print(f"✗ Failed to remove {script}: {e}")
        else:
            print(f"- Not found: {script}")
    
    print("=" * 50)
    print(f"Removed {removed_count} scripts")
    
    # List remaining scripts
    remaining_scripts = []
    for file in os.listdir(scripts_dir):
        if file.endswith('.py') or file.endswith('.sh'):
            remaining_scripts.append(file)
    
    print(f"\nRemaining scripts ({len(remaining_scripts)}):")
    for script in sorted(remaining_scripts):
        print(f"  - {script}")

if __name__ == "__main__":
    main() 