#!/usr/bin/env python3
"""
Test connection to Cloud SQL and explore available data
"""

import os
os.environ['NHL_DATABASE_URL'] = 'postgresql://postgres:your_password@127.0.0.1:5433/nhl_api'

import sys
sys.path.append('/Users/markhenderson/Cursor Projects/NHL-API/data-digging')

from sqlalchemy import create_engine, text
import pandas as pd

print("=" * 100)
print("  🔌 TESTING CLOUD SQL CONNECTION")
print("=" * 100)

# Try to connect
try:
    # Use localhost since proxy is running
    engine = create_engine('postgresql://postgres@127.0.0.1:5433/nhl_api', echo=False)
    
    print("\n✅ Attempting connection to Cloud SQL...")
    
    with engine.connect() as conn:
        print("✅ Connected successfully!\n")
        
        # Get all tables
        print("=" * 100)
        print("  📊 AVAILABLE TABLES")
        print("=" * 100)
        
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """))
        
        tables = [row[0] for row in result]
        
        print(f"\nFound {len(tables)} tables:\n")
        for i, table in enumerate(tables, 1):
            print(f"  {i:3}. {table}")
        
        # Show sample data from key tables
        print("\n" + "=" * 100)
        print("  🔍 SAMPLE DATA")
        print("=" * 100)
        
        # Check players table
        if 'players' in tables:
            print("\n📋 PLAYERS TABLE (first 5 rows):")
            print("-" * 100)
            players_df = pd.read_sql_query(text("SELECT * FROM players LIMIT 5"), conn)
            print(players_df.to_string())
            print(f"\nTotal players: {pd.read_sql_query(text('SELECT COUNT(*) FROM players'), conn).iloc[0, 0]}")
        
        # Check games table
        if 'games' in tables:
            print("\n🏒 GAMES TABLE (first 5 rows):")
            print("-" * 100)
            games_df = pd.read_sql_query(text("SELECT * FROM games LIMIT 5"), conn)
            print(games_df.to_string())
            print(f"\nTotal games: {pd.read_sql_query(text('SELECT COUNT(*) FROM games'), conn).iloc[0, 0]}")
        
        # Check if Darnell Nurse exists
        if 'players' in tables:
            print("\n" + "=" * 100)
            print("  🔎 SEARCHING FOR DARNELL NURSE")
            print("=" * 100)
            
            nurse_query = text("SELECT * FROM players WHERE LOWER(name) LIKE '%nurse%' OR id = 8477498")
            nurse_df = pd.read_sql_query(nurse_query, conn)
            
            if not nurse_df.empty:
                print("\n✅ Found Darnell Nurse:")
                print(nurse_df.to_string())
            else:
                print("\n❌ Darnell Nurse not found in players table")
        
        print("\n" + "=" * 100)
        print("  ✅ CONNECTION TEST COMPLETE")
        print("=" * 100)
        
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    print("\nTroubleshooting:")
    print("  1. Make sure Cloud SQL proxy is running")
    print("  2. Check if you need a password (might need to update connection string)")
    print("  3. Verify database name is 'nhl_api'")
    print(f"\n  Error details: {type(e).__name__}: {e}")

