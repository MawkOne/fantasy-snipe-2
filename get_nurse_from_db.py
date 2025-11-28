#!/usr/bin/env python3
"""
Get Darnell Nurse data from Cloud SQL database
"""

from sqlalchemy import create_engine, text
import pandas as pd

DATABASE_URL = "postgresql://postgres:123-new-password@34.47.23.137:5432/postgres?sslmode=require"

print("=" * 100)
print("  🏒 DARNELL NURSE - DATABASE vs EDGE API COMPARISON")
print("=" * 100)

engine = create_engine(DATABASE_URL, echo=False)

with engine.connect() as conn:
    
    # Find Darnell Nurse
    print("\n[1] PLAYER INFO")
    print("-" * 100)
    
    nurse_player = pd.read_sql_query(
        text("SELECT * FROM players WHERE id = 8477498 OR full_name ILIKE '%nurse%'"),
        conn
    )
    
    if not nurse_player.empty:
        print(nurse_player.to_string())
        nurse_id = int(nurse_player.iloc[0]['id'])  # Convert to native Python int
    else:
        print("❌ Not found in players table")
        nurse_id = 8477498
    
    # Get game stats
    print("\n\n[2] GAME STATS (Recent games)")
    print("-" * 100)
    
    game_stats = pd.read_sql_query(
        text("""
            SELECT 
                game_id, 
                assists, 
                goals, 
                shots, 
                hits, 
                blocked, 
                time_on_ice
            FROM player_game_stats 
            WHERE player_id = :player_id 
            ORDER BY game_id DESC 
            LIMIT 10
        """),
        conn,
        params={"player_id": nurse_id}
    )
    
    if not game_stats.empty:
        print(game_stats.to_string())
        print(f"\nTotal game stats records: {pd.read_sql_query(text('SELECT COUNT(*) FROM player_game_stats WHERE player_id = :pid'), conn, params={'pid': nurse_id}).iloc[0, 0]}")
    else:
        print("❌ No game stats found")
    
    # Get advanced metrics
    print("\n\n[3] ADVANCED METRICS")
    print("-" * 100)
    
    adv_metrics = pd.read_sql_query(
        text("""
            SELECT * FROM player_game_advanced_metrics_flat 
            WHERE player_id = :player_id 
            ORDER BY game_id DESC 
            LIMIT 5
        """),
        conn,
        params={"player_id": nurse_id}
    )
    
    if not adv_metrics.empty:
        print(adv_metrics.to_string())
        print(f"\nColumns: {list(adv_metrics.columns)}")
    else:
        print("❌ No advanced metrics found")
    
    # Get shift metrics
    print("\n\n[4] SHIFT METRICS")
    print("-" * 100)
    
    shift_metrics = pd.read_sql_query(
        text("""
            SELECT * FROM player_shift_metrics 
            WHERE player_id = :player_id 
            ORDER BY game_id DESC 
            LIMIT 5
        """),
        conn,
        params={"player_id": nurse_id}
    )
    
    if not shift_metrics.empty:
        print(shift_metrics.to_string())
        print(f"\nTotal shift metrics records: {pd.read_sql_query(text('SELECT COUNT(*) FROM player_shift_metrics WHERE player_id = :pid'), conn, params={'pid': nurse_id}).iloc[0, 0]}")
    else:
        print("❌ No shift metrics found")
    
    # Summary
    print("\n" + "=" * 100)
    print("  📊 DATABASE SUMMARY FOR DARNELL NURSE")
    print("=" * 100)
    
    print(f"\n✅ Player ID: {nurse_id}")
    print(f"✅ Game stats records: {len(pd.read_sql_query(text('SELECT * FROM player_game_stats WHERE player_id = :pid'), conn, params={'pid': nurse_id}))}")
    print(f"✅ Advanced metrics records: {len(pd.read_sql_query(text('SELECT * FROM player_game_advanced_metrics_flat WHERE player_id = :pid'), conn, params={'pid': nurse_id}))}")
    print(f"✅ Shift metrics records: {len(pd.read_sql_query(text('SELECT * FROM player_shift_metrics WHERE player_id = :pid'), conn, params={'pid': nurse_id}))}")
    
    print("\n💡 Now you can combine this data with Edge API speed/shot velocity data!")
    
    print("\n" + "=" * 100)

