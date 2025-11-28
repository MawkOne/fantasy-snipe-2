#!/usr/bin/env python3
"""
NHL API Data Ingestion Runner
Runs all NHL API ingestion scripts for a specified season
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime

# Script paths (relative to this file's directory)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NHL_API_DIR = os.path.join(SCRIPT_DIR, "ingestion", "nhl_api")

# Define the ingestion pipeline in order
INGESTION_PIPELINE = [
    {
        "name": "Games",
        "script": "populate_games.py",
        "args": lambda season: [str(season)],
        "description": "Populate games table with season schedule"
    },
    {
        "name": "Play-by-Play",
        "script": "populate_play_by_play.py",
        "args": lambda season: ["--all", "--season", f"{season}{season+1}", "--game-type", "2"],
        "description": "Populate game events (play-by-play data)"
    },
    {
        "name": "Player Game Stats",
        "script": "populate_player_game_stats.py",
        "args": lambda season: ["--season", f"{season}{season+1}"],
        "description": "Populate player statistics for each game"
    },
    {
        "name": "Shift Charts",
        "script": "populate_shift_charts.py",
        "args": lambda season: ["--season", f"{season}{season+1}"],
        "description": "Populate shift-by-shift data"
    }
]


def run_script(script_name: str, args: list, description: str) -> bool:
    """Run a single ingestion script"""
    script_path = os.path.join(NHL_API_DIR, script_name)
    
    if not os.path.exists(script_path):
        print(f"❌ Script not found: {script_path}")
        return False
    
    print(f"\n{'='*80}")
    print(f"🏒 {description}")
    print(f"{'='*80}")
    print(f"Running: {script_name} {' '.join(args)}\n")
    
    try:
        cmd = ["python3", script_path] + args
        result = subprocess.run(cmd, check=True, cwd=NHL_API_DIR)
        
        if result.returncode == 0:
            print(f"\n✅ {description} completed successfully")
            return True
        else:
            print(f"\n❌ {description} failed with exit code {result.returncode}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error running {script_name}: {e}")
        return False


def run_full_ingestion(season: int, skip_on_error: bool = False):
    """Run the full ingestion pipeline"""
    print(f"\n{'='*80}")
    print(f"🚀 NHL API DATA INGESTION - {season}-{season+1} SEASON")
    print(f"{'='*80}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    for step in INGESTION_PIPELINE:
        args = step["args"](season)
        success = run_script(step["script"], args, step["description"])
        results.append({
            "name": step["name"],
            "success": success
        })
        
        if not success and not skip_on_error:
            print(f"\n❌ Pipeline stopped due to error in: {step['name']}")
            break
    
    # Print summary
    print(f"\n{'='*80}")
    print("📊 INGESTION SUMMARY")
    print(f"{'='*80}")
    
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['name']}")
    
    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)
    
    print(f"\nCompleted: {success_count}/{total_count} steps")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    return success_count == total_count


def run_single_step(season: int, step_name: str):
    """Run a single ingestion step"""
    step = next((s for s in INGESTION_PIPELINE if s["name"].lower() == step_name.lower()), None)
    
    if not step:
        print(f"❌ Unknown step: {step_name}")
        print(f"\nAvailable steps:")
        for s in INGESTION_PIPELINE:
            print(f"  - {s['name']}")
        return False
    
    args = step["args"](season)
    return run_script(step["script"], args, step["description"])


def backfill_date_range(start_date: str, end_date: str):
    """Backfill data for a specific date range"""
    print(f"\n🔄 Backfilling data from {start_date} to {end_date}")
    
    # For play-by-play backfill
    script_path = os.path.join(NHL_API_DIR, "populate_play_by_play.py")
    
    if not os.path.exists(script_path):
        print(f"❌ Script not found: {script_path}")
        return False
    
    try:
        cmd = [
            "python3", script_path,
            "--start-date", start_date,
            "--end-date", end_date,
            "--game-type", "2"
        ]
        result = subprocess.run(cmd, check=True, cwd=NHL_API_DIR)
        
        if result.returncode == 0:
            print(f"\n✅ Backfill completed successfully")
            return True
        else:
            print(f"\n❌ Backfill failed")
            return False
            
    except Exception as e:
        print(f"\n❌ Backfill error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='NHL API Data Ingestion Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest full 2025 season
  python run_nhl_ingestion.py --season 2025
  
  # Ingest only play-by-play for 2025
  python run_nhl_ingestion.py --season 2025 --step "Play-by-Play"
  
  # Backfill data for October 2025
  python run_nhl_ingestion.py --backfill --start-date 2025-10-21 --end-date 2025-11-27
  
  # Continue on errors
  python run_nhl_ingestion.py --season 2025 --continue-on-error
        """
    )
    
    parser.add_argument(
        '--season',
        type=int,
        help='Season start year (e.g., 2025 for 2025-2026 season)'
    )
    
    parser.add_argument(
        '--step',
        type=str,
        help='Run only a specific step (Games, Play-by-Play, Player Game Stats, Shift Charts)'
    )
    
    parser.add_argument(
        '--backfill',
        action='store_true',
        help='Backfill data for a date range'
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date for backfill (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date for backfill (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--continue-on-error',
        action='store_true',
        help='Continue pipeline even if a step fails'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.backfill:
        if not args.start_date or not args.end_date:
            print("❌ --start-date and --end-date required for backfill")
            sys.exit(1)
        success = backfill_date_range(args.start_date, args.end_date)
    elif args.season:
        if args.step:
            success = run_single_step(args.season, args.step)
        else:
            success = run_full_ingestion(args.season, args.continue_on_error)
    else:
        print("❌ Either --season or --backfill is required")
        parser.print_help()
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()


